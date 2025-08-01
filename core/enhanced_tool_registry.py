"""
增强的工具注册系统 - 支持JSON Schema验证
"""
import json
import re
import time
import asyncio
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import jsonschema
from jsonschema import Draft7Validator
import logging

from .function_calling import ToolCall, ToolResult

logger = logging.getLogger(__name__)

@dataclass
class ToolSchema:
    """工具Schema定义"""
    name: str
    description: str
    schema: Dict[str, Any]
    validator: Draft7Validator
    category: str = "general"
    security_level: str = "normal"  # low, normal, high
    resource_limits: Dict[str, Any] = None

class EnhancedToolRegistry:
    """增强的工具注册器 - 支持JSON Schema验证"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: Dict[str, ToolSchema] = {}
        self.execution_stats: Dict[str, Dict] = {}
        
        # 安全配置
        self.max_execution_time = 300  # 5分钟
        self.max_string_length = 1000000  # 1MB
        self.dangerous_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
    
    def register_tool(self, 
                     name: str, 
                     func: Callable, 
                     description: str,
                     schema: Dict[str, Any],
                     category: str = "general",
                     security_level: str = "normal") -> None:
        """
        注册工具并验证Schema
        
        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            schema: JSON Schema定义
            category: 工具分类
            security_level: 安全级别 (low/normal/high)
        """
        try:
            # 验证Schema本身的有效性
            Draft7Validator.check_schema(schema)
            validator = Draft7Validator(schema)
            
            # 创建工具Schema对象
            tool_schema = ToolSchema(
                name=name,
                description=description,
                schema=schema,
                validator=validator,
                category=category,
                security_level=security_level
            )
            
            # 注册工具
            self.tools[name] = func
            self.schemas[name] = tool_schema
            self.execution_stats[name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_execution_time": 0.0,
                "last_called": None
            }
            
            logger.info(f"✅ 工具注册成功: {name} (类别: {category}, 安全级别: {security_level})")
            
        except jsonschema.SchemaError as e:
            raise ValueError(f"❌ 工具 {name} 的Schema无效: {e}")
        except Exception as e:
            raise ValueError(f"❌ 工具注册失败 {name}: {e}")
    
    def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证工具参数
        
        Returns:
            (is_valid, error_message)
        """
        if tool_name not in self.schemas:
            return False, f"未知工具: {tool_name}"
        
        tool_schema = self.schemas[tool_name]
        
        try:
            # JSON Schema验证
            tool_schema.validator.validate(parameters)
            
            # 安全检查
            security_check, security_error = self._security_check(parameters, tool_schema.security_level)
            if not security_check:
                return False, f"安全检查失败: {security_error}"
            
            return True, None
            
        except jsonschema.ValidationError as e:
            error_msg = f"参数验证失败: {e.message}"
            if e.path:
                error_msg += f" (路径: {'.'.join(map(str, e.path))})"
            return False, error_msg
    
    def _security_check(self, parameters: Dict[str, Any], security_level: str) -> tuple[bool, Optional[str]]:
        """安全检查"""
        for key, value in parameters.items():
            if isinstance(value, str):
                # 检查字符串长度
                if len(value) > self.max_string_length:
                    return False, f"参数 {key} 超过最大长度限制"
                
                # 高安全级别下检查危险模式
                if security_level == "high":
                    for pattern in self.dangerous_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            return False, f"参数 {key} 包含潜在危险内容"
            
            elif isinstance(value, dict):
                # 递归检查嵌套对象
                nested_check, nested_error = self._security_check(value, security_level)
                if not nested_check:
                    return False, nested_error
        
        return True, None
    
    def sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """清理参数"""
        def sanitize_value(value):
            if isinstance(value, str):
                # 移除潜在危险字符
                value = re.sub(r'[<>\"\'&\x00-\x1f\x7f-\x9f]', '', value)
                # 限制长度
                if len(value) > self.max_string_length:
                    value = value[:self.max_string_length]
                return value
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value
        
        return sanitize_value(parameters)
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        执行工具调用（带验证和监控）
        """
        start_time = time.time()
        tool_name = tool_call.tool_name
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(tool_name, tool_call.parameters)
            if not is_valid:
                self._update_stats(tool_name, False, 0)
                return ToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=error_msg,
                    result=None
                )
            
            # 清理参数
            sanitized_params = self.sanitize_parameters(tool_call.parameters)
            
            # 获取工具函数
            if tool_name not in self.tools:
                self._update_stats(tool_name, False, 0)
                return ToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"工具 {tool_name} 未注册",
                    result=None
                )
            
            tool_func = self.tools[tool_name]
            
            # 执行工具（带超时）
            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await asyncio.wait_for(
                        tool_func(**sanitized_params),
                        timeout=self.max_execution_time
                    )
                else:
                    # 在线程池中执行同步函数
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: tool_func(**sanitized_params)),
                        timeout=self.max_execution_time
                    )
                
                execution_time = time.time() - start_time
                self._update_stats(tool_name, True, execution_time)
                
                return ToolResult(
                    call_id=tool_call.call_id,
                    success=True,
                    error=None,
                    result=result
                )
                
            except asyncio.TimeoutError:
                self._update_stats(tool_name, False, time.time() - start_time)
                return ToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"工具执行超时 (>{self.max_execution_time}s)",
                    result=None
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(tool_name, False, execution_time)
            logger.error(f"工具执行异常 {tool_name}: {str(e)}")
            
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"工具执行异常: {str(e)}",
                result=None
            )
    
    def _update_stats(self, tool_name: str, success: bool, execution_time: float):
        """更新执行统计"""
        if tool_name not in self.execution_stats:
            return
        
        stats = self.execution_stats[tool_name]
        stats["total_calls"] += 1
        stats["last_called"] = time.time()
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        # 更新平均执行时间
        if stats["total_calls"] > 1:
            stats["avg_execution_time"] = (
                (stats["avg_execution_time"] * (stats["total_calls"] - 1) + execution_time) 
                / stats["total_calls"]
            )
        else:
            stats["avg_execution_time"] = execution_time
    
    def get_tool_documentation(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具文档"""
        if tool_name not in self.schemas:
            return None
        
        tool_schema = self.schemas[tool_name]
        return {
            "name": tool_schema.name,
            "description": tool_schema.description,
            "category": tool_schema.category,
            "security_level": tool_schema.security_level,
            "parameters": tool_schema.schema,
            "stats": self.execution_stats.get(tool_name, {})
        }
    
    def list_tools(self, category: str = None) -> List[Dict[str, Any]]:
        """列出工具"""
        tools = []
        for name, schema in self.schemas.items():
            if category is None or schema.category == category:
                tools.append({
                    "name": name,
                    "description": schema.description,
                    "category": schema.category,
                    "security_level": schema.security_level
                })
        return tools
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        total_calls = sum(stats["total_calls"] for stats in self.execution_stats.values())
        successful_calls = sum(stats["successful_calls"] for stats in self.execution_stats.values())
        
        return {
            "total_tools": len(self.tools),
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "tools_stats": self.execution_stats
        }