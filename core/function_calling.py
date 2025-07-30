#!/usr/bin/env python3
"""
基于输出解析的Function Calling系统

Function Calling System Based on Output Parsing
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None


@dataclass
class ToolResult:
    """工具调用结果"""
    call_id: str
    success: bool
    result: Any
    error: Optional[str] = None


class ToolCallParser:
    """工具调用输出解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_tool_calls(self, llm_output: str) -> List[ToolCall]:
        """从LLM输出中解析工具调用请求"""
        tool_calls = []
        
        # 方法1: JSON格式解析
        json_calls = self._parse_json_format(llm_output)
        tool_calls.extend(json_calls)
        
        # 方法2: XML格式解析
        xml_calls = self._parse_xml_format(llm_output)
        tool_calls.extend(xml_calls)
        
        # 方法3: 自定义标记格式解析
        marker_calls = self._parse_marker_format(llm_output)
        tool_calls.extend(marker_calls)
        
        self.logger.info(f"🔧 解析到 {len(tool_calls)} 个工具调用")
        return tool_calls
    
    def _parse_json_format(self, output: str) -> List[ToolCall]:
        """解析JSON格式的工具调用"""
        calls = []
        
        # 方法1: 查找```json代码块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, output, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if self._is_tool_call(data):
                    call = ToolCall(
                        tool_name=data['tool_name'],
                        parameters=data.get('parameters', {}),
                        call_id=data.get('call_id', f"call_{len(calls)}")
                    )
                    calls.append(call)
            except json.JSONDecodeError:
                continue
        
        # 方法2: 如果没有找到代码块，尝试解析整个输出为JSON
        if not calls:
            try:
                # 清理输出
                cleaned_output = output.strip()
                if cleaned_output.startswith('{') and cleaned_output.endswith('}'):
                    data = json.loads(cleaned_output)
                    
                    # 检查是否包含tool_calls数组
                    if 'tool_calls' in data and isinstance(data['tool_calls'], list):
                        for tool_call_data in data['tool_calls']:
                            if isinstance(tool_call_data, dict) and 'tool_name' in tool_call_data:
                                call = ToolCall(
                                    tool_name=tool_call_data['tool_name'],
                                    parameters=tool_call_data.get('parameters', {}),
                                    call_id=tool_call_data.get('call_id', f"call_{len(calls)}")
                                )
                                calls.append(call)
                    
                    # 检查是否直接是一个工具调用
                    elif self._is_tool_call(data):
                        call = ToolCall(
                            tool_name=data['tool_name'],
                            parameters=data.get('parameters', {}),
                            call_id=data.get('call_id', f"call_{len(calls)}")
                        )
                        calls.append(call)
                        
            except json.JSONDecodeError:
                pass
        
        return calls
    
    def _parse_xml_format(self, output: str) -> List[ToolCall]:
        """解析XML格式的工具调用"""
        calls = []
        
        # 查找XML格式的工具调用
        xml_pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(xml_pattern, output, re.DOTALL)
        
        for match in matches:
            try:
                # 提取工具名
                tool_name_match = re.search(r'<tool_name>(.*?)</tool_name>', match)
                if not tool_name_match:
                    continue
                
                tool_name = tool_name_match.group(1).strip()
                
                # 提取参数
                params = {}
                param_matches = re.findall(r'<param name="([^"]+)">(.*?)</param>', match, re.DOTALL)
                for param_name, param_value in param_matches:
                    params[param_name] = param_value.strip()
                
                call = ToolCall(
                    tool_name=tool_name,
                    parameters=params,
                    call_id=f"call_{len(calls)}"
                )
                calls.append(call)
                
            except Exception as e:
                self.logger.debug(f"XML解析失败: {e}")
                continue
        
        return calls
    
    def _parse_marker_format(self, output: str) -> List[ToolCall]:
        """解析自定义标记格式的工具调用"""
        calls = []
        
        # 查找TOOL_CALL标记格式
        marker_pattern = r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)'
        matches = re.findall(marker_pattern, output, re.DOTALL)
        
        for tool_name, params_str in matches:
            try:
                # 解析参数字符串
                params = {}
                if params_str.strip():
                    # 简单的键值对解析
                    param_pairs = params_str.split(',')
                    for pair in param_pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            params[key.strip()] = value.strip().strip('"\'')
                
                call = ToolCall(
                    tool_name=tool_name,
                    parameters=params,
                    call_id=f"call_{len(calls)}"
                )
                calls.append(call)
                
            except Exception as e:
                self.logger.debug(f"标记格式解析失败: {e}")
                continue
        
        return calls
    
    def _is_tool_call(self, data: Dict[str, Any]) -> bool:
        """判断JSON数据是否为工具调用"""
        return (isinstance(data, dict) and 
                'tool_name' in data and 
                isinstance(data['tool_name'], str))


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_descriptions: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_tool(self, name: str, func: Callable, description: str, 
                     parameters: Dict[str, Any] = None):
        """注册工具函数"""
        self.tools[name] = func
        self.tool_descriptions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {}
        }
        self.logger.info(f"🔧 注册工具: {name}")
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有注册的工具"""
        return self.tool_descriptions.copy()
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        return self.tools.get(name)
    
    def get_tools_prompt(self) -> str:
        """生成工具使用说明的prompt"""
        if not self.tools:
            return "当前没有可用的工具。"
        
        prompt = """
## 🛠️ 可用工具

你可以通过以下三种格式调用工具：

### 格式1: JSON格式 (推荐)
```json
{
    "tool_name": "工具名称",
    "parameters": {
        "参数名": "参数值"
    },
    "call_id": "可选的调用ID"
}
```

### 格式2: XML格式
<tool_call>
    <tool_name>工具名称</tool_name>
    <param name="参数名">参数值</param>
</tool_call>

### 格式3: 标记格式
TOOL_CALL: 工具名称(参数名="参数值", 参数名2="参数值2")

### 可用工具列表:
"""
        
        for tool_name, desc in self.tool_descriptions.items():
            prompt += f"\n**{tool_name}**: {desc['description']}\n"
            
            if desc['parameters']:
                prompt += "参数:\n"
                for param_name, param_info in desc['parameters'].items():
                    param_desc = param_info.get('description', '无描述')
                    param_type = param_info.get('type', 'string')
                    required = "必需" if param_info.get('required', False) else "可选"
                    prompt += f"  - {param_name} ({param_type}): {param_desc} [{required}]\n"
            prompt += "\n"
        
        prompt += """
### 工具调用规则:
1. 每次只调用一个工具
2. 调用工具后等待结果再继续
3. 如果工具调用失败，分析错误原因并重试或调整策略
4. 根据工具结果做出下一步决策

### 示例:
如果要生成测试台，使用：
```json
{
    "tool_name": "generate_testbench",
    "parameters": {
        "module_code": "完整的Verilog模块代码",
        "test_cases": ["test1", "test2"]
    }
}
```
"""
        return prompt
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        if tool_call.tool_name not in self.tools:
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                result=None,
                error=f"工具 '{tool_call.tool_name}' 不存在"
            )
        
        try:
            tool_func = self.tools[tool_call.tool_name]
            
            # 执行工具函数
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_call.parameters)
            else:
                result = tool_func(**tool_call.parameters)
            
            return ToolResult(
                call_id=tool_call.call_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            self.logger.error(f"❌ 工具调用失败 {tool_call.tool_name}: {str(e)}")
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                result=None,
                error=str(e)
            )


class FunctionCallingAgent(ABC):
    """支持Function Calling的智能体基类"""
    
    def __init__(self):
        self.tool_parser = ToolCallParser()
        self.tool_registry = ToolRegistry()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 注册工具
        self._register_tools()
    
    @abstractmethod
    def _register_tools(self):
        """子类实现：注册可用的工具"""
        pass
    
    async def process_with_function_calling(self, user_request: str, 
                                          max_iterations: int = 5) -> str:
        """使用Function Calling处理请求"""
        
        # 构建包含工具说明的system prompt
        system_prompt = self._build_system_prompt()
        
        # 初始对话
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request}
        ]
        
        for iteration in range(max_iterations):
            self.logger.info(f"🔄 Function Calling 迭代 {iteration + 1}/{max_iterations}")
            
            # 调用LLM
            llm_response = await self._call_llm(conversation)
            
            # 解析工具调用
            tool_calls = self.tool_parser.parse_tool_calls(llm_response)
            
            if not tool_calls:
                # 没有工具调用，返回最终结果
                self.logger.info("✅ 任务完成，无需调用工具")
                return llm_response
            
            # 执行工具调用
            conversation.append({"role": "assistant", "content": llm_response})
            
            for tool_call in tool_calls:
                self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name}")
                
                tool_result = await self.tool_registry.execute_tool(tool_call)
                
                # 构建工具结果消息
                result_message = self._format_tool_result(tool_call, tool_result)
                conversation.append({"role": "user", "content": result_message})
        
        # 达到最大迭代次数
        final_response = await self._call_llm(conversation)
        return final_response
    
    def _build_system_prompt(self) -> str:
        """构建包含工具说明的system prompt"""
        base_prompt = self._get_base_system_prompt()
        tools_prompt = self.tool_registry.get_tools_prompt()
        
        return f"{base_prompt}\n\n{tools_prompt}"
    
    @abstractmethod
    def _get_base_system_prompt(self) -> str:
        """子类实现：获取基础system prompt"""
        pass
    
    @abstractmethod
    async def _call_llm(self, conversation: List[Dict[str, str]]) -> str:
        """子类实现：调用LLM"""
        pass
    
    def _format_tool_result(self, tool_call: ToolCall, tool_result: ToolResult) -> str:
        """格式化工具调用结果"""
        if tool_result.success:
            return f"""
## 工具调用结果

**工具**: {tool_call.tool_name}
**状态**: ✅ 成功
**结果**: 
{tool_result.result}

请基于此结果继续处理任务。
"""
        else:
            return f"""
## 工具调用结果

**工具**: {tool_call.tool_name}
**状态**: ❌ 失败
**错误**: {tool_result.error}

请分析错误原因并调整策略。
"""


# 导入异步支持
import asyncio