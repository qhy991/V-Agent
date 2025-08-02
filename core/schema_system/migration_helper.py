"""
迁移辅助工具 - 帮助将现有工具迁移到Schema系统
"""
import json
import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import ast
import inspect
import logging

logger = logging.getLogger(__name__)

class MigrationHelper:
    """迁移辅助工具"""
    
    def __init__(self):
        self.type_mapping = {
            'str': 'string',
            'int': 'integer', 
            'float': 'number',
            'bool': 'boolean',
            'list': 'array',
            'dict': 'object'
        }
        
        self.common_patterns = {
            'filename': r'^[a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'version': r'^\d+\.\d+\.\d+$',
            'identifier': r'^[a-zA-Z][a-zA-Z0-9_]*$',
            'path': r'^[a-zA-Z0-9_./\\-]+$'
        }
    
    def analyze_existing_tool(self, tool_func: Callable, tool_name: str,
                             existing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析现有工具并生成Schema建议
        
        Args:
            tool_func: 工具函数
            tool_name: 工具名称
            existing_params: 现有参数定义
            
        Returns:
            Schema建议
        """
        logger.info(f"🔍 分析工具: {tool_name}")
        
        # 1. 分析函数签名
        signature_info = self._analyze_function_signature(tool_func)
        
        # 2. 分析现有参数定义
        existing_info = self._analyze_existing_parameters(existing_params or {})
        
        # 3. 分析函数文档
        doc_info = self._analyze_function_docstring(tool_func)
        
        # 4. 生成Schema建议
        schema_suggestion = self._generate_schema_suggestion(
            signature_info, existing_info, doc_info, tool_name
        )
        
        return {
            "tool_name": tool_name,
            "analysis": {
                "signature": signature_info,
                "existing_params": existing_info,
                "documentation": doc_info
            },
            "suggested_schema": schema_suggestion,
            "migration_notes": self._generate_migration_notes(signature_info, existing_info)
        }
    
    def _analyze_function_signature(self, func: Callable) -> Dict[str, Any]:
        """分析函数签名"""
        try:
            sig = inspect.signature(func)
            parameters = {}
            
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "has_default": param.default != inspect.Parameter.empty,
                    "default_value": param.default if param.default != inspect.Parameter.empty else None
                }
                
                # 尝试获取类型注解
                if param.annotation != inspect.Parameter.empty:
                    param_info["annotation"] = str(param.annotation)
                    param_info["suggested_type"] = self._convert_python_type_to_json_type(
                        param.annotation
                    )
                
                parameters[param_name] = param_info
            
            return {
                "parameters": parameters,
                "return_annotation": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 无法分析函数签名: {str(e)}")
            return {"parameters": {}, "error": str(e)}
    
    def _analyze_existing_parameters(self, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """分析现有参数定义"""
        analyzed = {}
        
        for param_name, param_def in existing_params.items():
            if isinstance(param_def, dict):
                analyzed[param_name] = {
                    "type": param_def.get("type", "string"),
                    "description": param_def.get("description", ""),
                    "required": param_def.get("required", False)
                }
        
        return analyzed
    
    def _analyze_function_docstring(self, func: Callable) -> Dict[str, Any]:
        """分析函数文档字符串"""
        doc = inspect.getdoc(func)
        if not doc:
            return {"has_docstring": False}
        
        # 尝试解析Google风格或Sphinx风格的文档
        doc_info = {
            "has_docstring": True,
            "raw_docstring": doc,
            "parameters": {},
            "description": ""
        }
        
        # 简单的参数提取（Google风格）
        lines = doc.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Args:') or line.startswith('Arguments:'):
                current_section = 'args'
                continue
            elif line.startswith('Returns:'):
                current_section = 'returns'
                continue
            elif line.startswith('Raises:'):
                current_section = 'raises'
                continue
            
            if current_section == 'args' and ':' in line:
                # 解析参数行，格式如: param_name (type): description
                match = re.match(r'\s*(\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.+)', line)
                if match:
                    param_name, param_type, description = match.groups()
                    doc_info["parameters"][param_name] = {
                        "description": description.strip(),
                        "type_hint": param_type.strip() if param_type else None
                    }
        
        # 提取主要描述（第一段）
        first_paragraph = doc.split('\n\n')[0].replace('\n', ' ').strip()
        doc_info["description"] = first_paragraph
        
        return doc_info
    
    def _generate_schema_suggestion(self, signature_info: Dict[str, Any],
                                   existing_info: Dict[str, Any], 
                                   doc_info: Dict[str, Any],
                                   tool_name: str) -> Dict[str, Any]:
        """生成Schema建议"""
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        # 合并所有参数信息
        all_params = {}
        
        # 从函数签名获取参数
        for param_name, param_info in signature_info.get("parameters", {}).items():
            all_params[param_name] = {
                "source": "signature",
                "info": param_info
            }
        
        # 更新现有参数信息
        for param_name, param_info in existing_info.items():
            if param_name in all_params:
                all_params[param_name]["existing"] = param_info
            else:
                all_params[param_name] = {
                    "source": "existing",
                    "info": param_info
                }
        
        # 更新文档信息
        for param_name, param_doc in doc_info.get("parameters", {}).items():
            if param_name in all_params:
                all_params[param_name]["documentation"] = param_doc
            else:
                all_params[param_name] = {
                    "source": "documentation",
                    "documentation": param_doc
                }
        
        # 为每个参数生成Schema
        for param_name, param_data in all_params.items():
            param_schema = self._generate_parameter_schema(param_name, param_data, tool_name)
            if param_schema:
                schema["properties"][param_name] = param_schema
                
                # 确定是否为必需参数
                is_required = self._determine_if_required(param_data)
                if is_required:
                    schema["required"].append(param_name)
        
        return schema
    
    def _generate_parameter_schema(self, param_name: str, param_data: Dict[str, Any],
                                  tool_name: str) -> Dict[str, Any]:
        """为单个参数生成Schema"""
        param_schema = {}
        
        # 确定类型
        param_type = self._determine_parameter_type(param_data)
        param_schema["type"] = param_type
        
        # 添加描述
        description = self._get_parameter_description(param_data)
        if description:
            param_schema["description"] = description
        
        # 添加默认值
        default_value = self._get_parameter_default(param_data)
        if default_value is not None:
            param_schema["default"] = default_value
        
        # 根据参数名和类型添加约束
        constraints = self._suggest_parameter_constraints(param_name, param_type, tool_name)
        param_schema.update(constraints)
        
        return param_schema
    
    def _determine_parameter_type(self, param_data: Dict[str, Any]) -> str:
        """确定参数类型"""
        # 优先级：现有定义 > 类型注解 > 文档提示 > 默认推断
        
        # 1. 检查现有定义
        existing = param_data.get("existing", {})
        if existing.get("type"):
            return existing["type"]
        
        # 2. 检查类型注解
        signature_info = param_data.get("info", {})
        if signature_info.get("suggested_type"):
            return signature_info["suggested_type"]
        
        # 3. 检查文档类型提示
        doc_info = param_data.get("documentation", {})
        if doc_info.get("type_hint"):
            return self._convert_python_type_to_json_type(doc_info["type_hint"])
        
        # 4. 根据默认值推断
        default_value = signature_info.get("default_value")
        if default_value is not None:
            return self._infer_type_from_value(default_value)
        
        # 5. 默认为字符串
        return "string"
    
    def _get_parameter_description(self, param_data: Dict[str, Any]) -> str:
        """获取参数描述"""
        # 优先级：文档描述 > 现有描述
        doc_info = param_data.get("documentation", {})
        if doc_info.get("description"):
            return doc_info["description"]
        
        existing = param_data.get("existing", {})
        return existing.get("description", "")
    
    def _get_parameter_default(self, param_data: Dict[str, Any]) -> Any:
        """获取参数默认值"""
        signature_info = param_data.get("info", {})
        return signature_info.get("default_value")
    
    def _determine_if_required(self, param_data: Dict[str, Any]) -> bool:
        """确定参数是否必需"""
        # 如果有默认值，则不是必需的
        signature_info = param_data.get("info", {})
        if signature_info.get("has_default", False):
            return False
        
        # 检查现有定义
        existing = param_data.get("existing", {})
        return existing.get("required", True)  # 默认为必需
    
    def _suggest_parameter_constraints(self, param_name: str, param_type: str,
                                      tool_name: str) -> Dict[str, Any]:
        """建议参数约束"""
        constraints = {}
        
        # 根据参数名建议约束
        param_name_lower = param_name.lower()
        
        if 'filename' in param_name_lower or 'file' in param_name_lower:
            if param_type == "string":
                constraints.update({
                    "pattern": self.common_patterns["filename"],
                    "maxLength": 255,
                    "minLength": 1
                })
        
        elif 'email' in param_name_lower:
            if param_type == "string":
                constraints.update({
                    "pattern": self.common_patterns["email"],
                    "maxLength": 254
                })
        
        elif 'url' in param_name_lower or 'link' in param_name_lower:
            if param_type == "string":
                constraints.update({
                    "pattern": self.common_patterns["url"],
                    "maxLength": 2048
                })
        
        elif 'version' in param_name_lower:
            if param_type == "string":
                constraints.update({
                    "pattern": self.common_patterns["version"]
                })
        
        elif 'count' in param_name_lower or 'limit' in param_name_lower or 'max' in param_name_lower:
            if param_type in ["integer", "number"]:
                constraints.update({
                    "minimum": 0,
                    "maximum": 1000  # 合理的默认上限
                })
        
        elif 'timeout' in param_name_lower or 'delay' in param_name_lower:
            if param_type in ["integer", "number"]:
                constraints.update({
                    "minimum": 0,
                    "maximum": 3600  # 1小时
                })
        
        # 根据工具类型添加安全约束
        if self._is_security_sensitive_tool(tool_name):
            if param_type == "string":
                constraints["maxLength"] = constraints.get("maxLength", 1000)
        
        return constraints
    
    def _convert_python_type_to_json_type(self, python_type) -> str:
        """将Python类型转换为JSON Schema类型"""
        if hasattr(python_type, '__name__'):
            type_name = python_type.__name__
        else:
            type_name = str(python_type)
        
        # 移除泛型标记
        type_name = re.sub(r'[<>].*', '', type_name)
        type_name = type_name.split('.')[-1]  # 获取类名
        
        return self.type_mapping.get(type_name.lower(), "string")
    
    def _infer_type_from_value(self, value: Any) -> str:
        """从值推断类型"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"
    
    def _is_security_sensitive_tool(self, tool_name: str) -> bool:
        """判断是否为安全敏感工具"""
        sensitive_keywords = [
            'file', 'write', 'read', 'execute', 'command', 'shell',
            'sql', 'database', 'network', 'http', 'request'
        ]
        
        tool_name_lower = tool_name.lower()
        return any(keyword in tool_name_lower for keyword in sensitive_keywords)
    
    def _generate_migration_notes(self, signature_info: Dict[str, Any],
                                 existing_info: Dict[str, Any]) -> List[str]:
        """生成迁移注意事项"""
        notes = []
        
        # 检查类型不一致
        sig_params = signature_info.get("parameters", {})
        for param_name, existing_param in existing_info.items():
            if param_name in sig_params:
                sig_param = sig_params[param_name]
                existing_type = existing_param.get("type")
                suggested_type = sig_param.get("suggested_type")
                
                if existing_type and suggested_type and existing_type != suggested_type:
                    notes.append(
                        f"参数 '{param_name}' 类型不一致: "
                        f"现有({existing_type}) vs 推断({suggested_type})"
                    )
        
        # 检查缺失的参数
        existing_params = set(existing_info.keys())
        signature_params = set(sig_params.keys())
        
        missing_in_existing = signature_params - existing_params
        if missing_in_existing:
            notes.append(f"现有定义中缺少参数: {', '.join(missing_in_existing)}")
        
        extra_in_existing = existing_params - signature_params
        if extra_in_existing:
            notes.append(f"现有定义中多余参数: {', '.join(extra_in_existing)}")
        
        return notes
    
    def generate_migration_script(self, analysis_results: List[Dict[str, Any]],
                                 output_file: str = "migration_script.py") -> str:
        """生成迁移脚本"""
        script_lines = [
            '"""',
            '自动生成的工具迁移脚本',
            '"""',
            '',
            'from core.schema_system import EnhancedBaseAgent',
            '',
            'def migrate_tools(agent: EnhancedBaseAgent):',
            '    """迁移现有工具到Schema系统"""',
            ''
        ]
        
        for analysis in analysis_results:
            tool_name = analysis["tool_name"]
            schema = analysis["suggested_schema"]
            
            script_lines.extend([
                f'    # 迁移工具: {tool_name}',
                f'    agent.register_enhanced_tool(',
                f'        name="{tool_name}",',
                f'        func=agent.function_calling_registry["{tool_name}"],',
                f'        description="TODO: 添加工具描述",',
                f'        schema={json.dumps(schema, indent=8)[:-1]}    }}',
                f'    )',
                ''
            ])
        
        script_content = '\n'.join(script_lines)
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"✅ 迁移脚本已生成: {output_file}")
        return script_content
    
    def validate_migration(self, agent, tool_name: str, 
                          original_params: Dict[str, Any],
                          schema: Dict[str, Any]) -> Dict[str, Any]:
        """验证迁移结果"""
        from .schema_validator import SchemaValidator
        
        validator = SchemaValidator()
        validation_result = validator.validate(original_params, schema)
        
        return {
            "tool_name": tool_name,
            "validation_passed": validation_result.is_valid,
            "errors": [error.to_dict() for error in validation_result.errors],
            "warnings": [warning.to_dict() for warning in validation_result.warnings]
        }