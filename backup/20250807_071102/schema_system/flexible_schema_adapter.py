"""
灵活Schema适配器 - 解决AI Agent与工具Schema不匹配问题
处理常见的格式转换，如字符串端口定义转对象数组等
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .field_mapper import FieldMapper

logger = logging.getLogger(__name__)

@dataclass
class SchemaAdaptationResult:
    """Schema适配结果"""
    success: bool
    adapted_data: Optional[Dict[str, Any]] = None
    transformations: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.transformations is None:
            self.transformations = []
        if self.warnings is None:
            self.warnings = []

class FlexibleSchemaAdapter:
    """灵活的Schema适配器 - 智能转换AI Agent输出格式"""
    
    def __init__(self):
        self.field_mapper = FieldMapper()
        
        self.port_patterns = [
            # 匹配 "a [7:0]", "b [3:0]", "cin" 等格式
            r'^([a-zA-Z][a-zA-Z0-9_]*)\s*\[(\d+):0\]$',  # 带宽度的端口
            r'^([a-zA-Z][a-zA-Z0-9_]*)\s*\[(\d+):(\d+)\]$',  # 带范围的端口  
            r'^([a-zA-Z][a-zA-Z0-9_]*)\s*$'  # 单bit端口
        ]
    
    def adapt_parameters(self, data: Dict[str, Any], schema: Dict[str, Any], 
                        tool_name: str) -> SchemaAdaptationResult:
        """
        智能适配参数格式以匹配Schema要求
        
        Args:
            data: 原始参数数据
            schema: 目标Schema定义
            tool_name: 工具名称（用于特定适配规则）
            
        Returns:
            SchemaAdaptationResult: 适配结果
        """
        result = SchemaAdaptationResult(success=True)
        adapted_data = data.copy()
        
        try:
            # 1. 智能字段映射（首要步骤）
            adapted_data = self.field_mapper.map_fields(adapted_data, tool_name, schema)
            result.transformations.append("应用智能字段映射")
            
            # 2. 处理端口定义转换 (针对generate_verilog_code)
            if tool_name == "generate_verilog_code":
                adapted_data = self._adapt_verilog_code_parameters(adapted_data, result)
            
            # 3. 处理测试场景转换 (针对generate_testbench)
            elif tool_name == "generate_testbench":
                adapted_data = self._adapt_testbench_parameters(adapted_data, result)
            
            # 4. 处理代码分析参数 (针对analyze_code_quality)
            elif tool_name == "analyze_code_quality":
                adapted_data = self._adapt_code_analysis_parameters(adapted_data, result)
            
            # 5. 移除Schema不允许的额外字段 (如果additionalProperties=False)
            if not schema.get("additionalProperties", True):
                adapted_data = self._remove_extra_fields(adapted_data, schema, result)
            
            # 6. 添加缺失的必需字段默认值（字段映射器已经处理了大部分）
            adapted_data = self._add_missing_required_fields(adapted_data, schema, result)
            
            result.adapted_data = adapted_data
            
        except Exception as e:
            logger.error(f"Schema适配失败: {str(e)}")
            result.success = False
            result.warnings.append(f"适配过程异常: {str(e)}")
            result.adapted_data = data  # 返回原数据
        
        return result
    
    def _adapt_verilog_code_parameters(self, data: Dict[str, Any], 
                                     result: SchemaAdaptationResult) -> Dict[str, Any]:
        """适配Verilog代码生成工具的参数"""
        adapted = data.copy()
        
        # 转换input_ports字符串数组为对象数组
        if "input_ports" in adapted and isinstance(adapted["input_ports"], list):
            if adapted["input_ports"] and isinstance(adapted["input_ports"][0], str):
                port_objects = self._convert_port_strings_to_objects(adapted["input_ports"])
                if port_objects is not None:
                    adapted["input_ports"] = port_objects
                    result.transformations.append("将input_ports从字符串数组转换为对象数组")
        
        # 转换output_ports字符串数组为对象数组  
        if "output_ports" in adapted and isinstance(adapted["output_ports"], list):
            if adapted["output_ports"] and isinstance(adapted["output_ports"][0], str):
                port_objects = self._convert_port_strings_to_objects(adapted["output_ports"])
                if port_objects is not None:
                    adapted["output_ports"] = port_objects
                    result.transformations.append("将output_ports从字符串数组转换为对象数组")
        
        # 如果没有提供端口定义，从requirements中推断
        if "input_ports" not in adapted and "output_ports" not in adapted:
            requirements = adapted.get("requirements", "")
            inferred_ports = self._infer_ports_from_requirements(requirements)
            if inferred_ports:
                adapted.update(inferred_ports)
                result.transformations.append("从requirements推断端口定义")
        
        return adapted
    
    def _adapt_testbench_parameters(self, data: Dict[str, Any], 
                                  result: SchemaAdaptationResult) -> Dict[str, Any]:
        """适配测试台生成工具的参数"""
        adapted = data.copy()
        
        # 转换test_scenarios字符串数组为对象数组（如果Schema要求对象）
        if "test_scenarios" in adapted and isinstance(adapted["test_scenarios"], list):
            if adapted["test_scenarios"] and isinstance(adapted["test_scenarios"][0], str):
                # 保持字符串格式，因为Schema确实支持字符串数组
                result.transformations.append("保持test_scenarios字符串数组格式")
        
        return adapted
    
    def _adapt_code_analysis_parameters(self, data: Dict[str, Any], 
                                      result: SchemaAdaptationResult) -> Dict[str, Any]:
        """适配代码分析工具的参数"""
        adapted = data.copy()
        
        # 处理代码字段名变化
        if "code" in adapted and "verilog_code" not in adapted:
            adapted["verilog_code"] = adapted["code"]
            result.transformations.append("将code字段映射为verilog_code")
        
        return adapted
    
    def _convert_port_strings_to_objects(self, port_strings: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        将端口字符串数组转换为对象数组
        
        Examples:
            ["a [7:0]", "b [7:0]", "cin"] -> 
            [{"name": "a", "width": 8}, {"name": "b", "width": 8}, {"name": "cin", "width": 1}]
        """
        try:
            port_objects = []
            
            for port_str in port_strings:
                # 清理字符串
                port_str = port_str.strip().strip('"').strip("'")
                if not port_str:
                    continue
                
                port_obj = self._parse_single_port_string(port_str)
                if port_obj:
                    port_objects.append(port_obj)
            
            return port_objects if port_objects else None
            
        except Exception as e:
            logger.warning(f"端口字符串转换失败: {str(e)}")
            return None
    
    def _parse_single_port_string(self, port_str: str) -> Optional[Dict[str, Any]]:
        """解析单个端口字符串"""
        for pattern in self.port_patterns:
            match = re.match(pattern, port_str.strip())
            if match:
                if len(match.groups()) >= 2:
                    # 带宽度的端口 "a [7:0]"
                    name = match.group(1)
                    if len(match.groups()) == 2:
                        # [7:0] 格式
                        width = int(match.group(2)) + 1
                    else:
                        # [7:3] 格式
                        high = int(match.group(2))
                        low = int(match.group(3))
                        width = abs(high - low) + 1
                else:
                    # 单bit端口 "cin"
                    name = match.group(1)
                    width = 1
                
                # 验证名称有效性
                if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                    return {
                        "name": name,
                        "width": width,
                        "description": f"{width}-bit port"
                    }
        
        return None
    
    def _infer_ports_from_requirements(self, requirements: str) -> Dict[str, List[Dict[str, Any]]]:
        """从需求描述中推断端口定义"""
        inferred = {}
        
        # 查找模块声明
        module_pattern = r'module\s+\w+\s*\((.*?)\)'
        match = re.search(module_pattern, requirements, re.DOTALL)
        
        if match:
            port_list = match.group(1)
            # 简单解析端口列表
            ports = [p.strip() for p in port_list.split(',') if p.strip()]
            
            input_ports = []
            output_ports = []
            
            for port in ports:
                # 简单的输入/输出识别
                if 'input' in port:
                    port_clean = re.sub(r'input\s*', '', port).strip()
                    port_obj = self._parse_single_port_string(port_clean)
                    if port_obj:
                        input_ports.append(port_obj)
                elif 'output' in port:
                    port_clean = re.sub(r'output\s*', '', port).strip()  
                    port_obj = self._parse_single_port_string(port_clean)
                    if port_obj:
                        output_ports.append(port_obj)
            
            if input_ports:
                inferred["input_ports"] = input_ports
            if output_ports:
                inferred["output_ports"] = output_ports
        
        return inferred
    
    def _remove_extra_fields(self, data: Dict[str, Any], schema: Dict[str, Any],
                           result: SchemaAdaptationResult) -> Dict[str, Any]:
        """移除Schema不允许的额外字段"""
        if schema.get("additionalProperties", True):
            return data
        
        properties = schema.get("properties", {})
        adapted = {}
        
        for key, value in data.items():
            if key in properties:
                adapted[key] = value
            else:
                result.warnings.append(f"移除额外字段: {key}")
        
        return adapted
    
    def _add_missing_required_fields(self, data: Dict[str, Any], schema: Dict[str, Any],
                                   result: SchemaAdaptationResult) -> Dict[str, Any]:
        """添加缺失的必需字段默认值"""
        adapted = data.copy()
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for field in required:
            if field not in adapted:
                # 尝试提供默认值
                field_schema = properties.get(field, {})
                default_value = self._get_default_value_for_type(field_schema)
                
                if default_value is not None:
                    adapted[field] = default_value
                    result.transformations.append(f"添加缺失字段 {field} 默认值: {default_value}")
        
        return adapted
    
    def _get_default_value_for_type(self, field_schema: Dict[str, Any]) -> Any:
        """根据字段Schema获取默认值"""
        if "default" in field_schema:
            return field_schema["default"]
        
        field_type = field_schema.get("type")
        if field_type == "string":
            return ""
        elif field_type == "integer":
            return 0
        elif field_type == "number":
            return 0.0
        elif field_type == "boolean":
            return False
        elif field_type == "array":
            return []
        elif field_type == "object":
            return {}
        
        return None
    
    def create_flexible_schema(self, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """创建更灵活的Schema版本"""
        flexible_schema = original_schema.copy()
        
        # 1. 允许额外属性（但发出警告）
        flexible_schema["additionalProperties"] = True
        
        # 2. 对于端口数组，支持字符串和对象两种格式
        properties = flexible_schema.get("properties", {})
        
        for port_field in ["input_ports", "output_ports"]:
            if port_field in properties:
                original_port_schema = properties[port_field]
                flexible_port_schema = {
                    "anyOf": [
                        # 原始对象数组格式
                        original_port_schema,
                        # 字符串数组格式 (AI Agent喜欢的格式)
                        {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*(\s*\[\d+:\d*\])?$"
                            },
                            "maxItems": original_port_schema.get("maxItems", 100)
                        }
                    ],
                    "description": f"{original_port_schema.get('description', '')} (支持字符串或对象格式)"
                }
                properties[port_field] = flexible_port_schema
        
        # 3. 对测试场景也支持多种格式
        if "test_scenarios" in properties:
            original_scenarios = properties["test_scenarios"]
            properties["test_scenarios"] = {
                "anyOf": [
                    # 原始格式
                    original_scenarios,
                    # 对象格式
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "inputs": {"type": "object"},
                                "expected_outputs": {"type": "object"}
                            }
                        }
                    }
                ]
            }
        
        return flexible_schema