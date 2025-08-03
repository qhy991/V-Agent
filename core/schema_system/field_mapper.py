"""
字段映射器 - 处理AI Agent与工具Schema之间的字段名不匹配问题
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FieldMapper:
    """智能字段映射器"""
    
    def __init__(self):
        # 全局字段映射规则
        self.global_mappings = {
            # 常见字段名变化
            'verilog_code': 'code',
            'module_code': 'code',
            'design_files': 'verilog_files', 
            'testbench_files': 'testbench_files',
            'target_platform': 'platform',
            'optimization_level': 'optimization',
            'coding_standard': 'standard',
            'analysis_scope': 'scope',
            'test_scenarios': 'scenarios',
            'simulation_time': 'sim_time',
            'clock_period': 'period'
        }
        
        # 工具特定的字段映射
        self.tool_specific_mappings = {
            'generate_verilog_code': {
                'code': 'verilog_code',  # 反向映射，因为这个工具期望verilog_code
                'ports': 'input_ports',  # 如果只提供了ports而没有区分输入输出
                'module_description': 'requirements'
            },
            'analyze_code_quality': {
                'code': 'verilog_code',
                'source': 'verilog_code',
                'content': 'verilog_code',
                'scope': 'analysis_scope'
            },
            'generate_testbench': {
                'code': 'verilog_code',
                'module_code': 'verilog_code',
                'test_cases': 'test_scenarios',
                'scenarios': 'test_scenarios'
            },
            'run_simulation': {
                'design_files': 'verilog_files',
                'tb_files': 'testbench_files',
                'testbench': 'testbench_files',
                'testbench_file': 'testbench_file',  # 保持原字段名
                'module_file': 'module_file'  # 保持原字段名
            }
        }
        
        # 双向映射缓存
        self._reverse_mappings = {}
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        """构建反向映射缓存"""
        # 全局反向映射
        self._reverse_mappings['global'] = {v: k for k, v in self.global_mappings.items()}
        
        # 工具特定反向映射
        for tool_name, mappings in self.tool_specific_mappings.items():
            self._reverse_mappings[tool_name] = {v: k for k, v in mappings.items()}
    
    def map_fields(self, data: Dict[str, Any], tool_name: str, 
                   target_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能映射字段名
        
        Args:
            data: 原始数据
            tool_name: 工具名称
            target_schema: 目标Schema
            
        Returns:
            映射后的数据
        """
        mapped_data = data.copy()
        schema_properties = target_schema.get('properties', {})
        
        # 1. 应用工具特定映射
        if tool_name in self.tool_specific_mappings:
            tool_mappings = self.tool_specific_mappings[tool_name]
            mapped_data = self._apply_mappings(mapped_data, tool_mappings)
        
        # 2. 应用全局映射
        mapped_data = self._apply_mappings(mapped_data, self.global_mappings)
        
        # 3. 智能字段匹配（处理部分匹配的字段名）
        mapped_data = self._smart_field_matching(mapped_data, schema_properties)
        
        # 4. 处理缺失的必需字段（尝试从相似字段推断）
        mapped_data = self._infer_missing_fields(mapped_data, target_schema)
        
        return mapped_data
    
    def _apply_mappings(self, data: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """应用字段映射规则"""
        mapped_data = data.copy()
        
        for old_name, new_name in mappings.items():
            if old_name in mapped_data and new_name not in mapped_data:
                mapped_data[new_name] = mapped_data[old_name]
                # 保留原字段以避免破坏兼容性，除非Schema明确不允许
                logger.debug(f"字段映射: {old_name} -> {new_name}")
        
        return mapped_data
    
    def _smart_field_matching(self, data: Dict[str, Any], 
                            schema_properties: Dict[str, Any]) -> Dict[str, Any]:
        """智能字段匹配 - 处理部分匹配的字段名"""
        mapped_data = data.copy()
        
        # 寻找相似的字段名
        for data_field in list(data.keys()):
            if data_field not in schema_properties:
                # 尝试找到最相似的Schema字段
                best_match = self._find_best_field_match(data_field, schema_properties.keys())
                if best_match and best_match not in mapped_data:
                    mapped_data[best_match] = mapped_data[data_field]
                    logger.info(f"智能字段匹配: {data_field} -> {best_match}")
        
        return mapped_data
    
    def _find_best_field_match(self, field_name: str, 
                              schema_fields: List[str], threshold: float = 0.7) -> Optional[str]:
        """找到最佳字段匹配"""
        field_lower = field_name.lower()
        best_score = 0
        best_match = None
        
        for schema_field in schema_fields:
            schema_lower = schema_field.lower()
            
            # 计算相似度
            score = self._calculate_field_similarity(field_lower, schema_lower)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = schema_field
        
        return best_match
    
    def _calculate_field_similarity(self, field1: str, field2: str) -> float:
        """计算字段名相似度"""
        # 完全匹配
        if field1 == field2:
            return 1.0
        
        # 包含关系
        if field1 in field2 or field2 in field1:
            return 0.8
        
        # 关键词匹配
        field1_words = set(field1.split('_'))
        field2_words = set(field2.split('_'))
        
        if field1_words & field2_words:  # 有交集
            intersection = len(field1_words & field2_words)
            union = len(field1_words | field2_words)
            return intersection / union
        
        # Levenshtein距离（简化版）
        return self._simple_string_similarity(field1, field2)
    
    def _simple_string_similarity(self, s1: str, s2: str) -> float:
        """简单字符串相似度计算"""
        if not s1 or not s2:
            return 0.0
        
        # 基于共同字符的相似度
        common_chars = len(set(s1) & set(s2))
        total_chars = len(set(s1) | set(s2))
        
        return common_chars / total_chars if total_chars > 0 else 0.0
    
    def _infer_missing_fields(self, data: Dict[str, Any], 
                            schema: Dict[str, Any]) -> Dict[str, Any]:
        """推断缺失的必需字段"""
        mapped_data = data.copy()
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})
        
        for field in required_fields:
            if field not in mapped_data:
                # 尝试从现有数据推断
                inferred_value = self._infer_field_value(field, data, properties.get(field, {}))
                if inferred_value is not None:
                    mapped_data[field] = inferred_value
                    logger.info(f"推断缺失字段: {field} = {inferred_value}")
        
        return mapped_data
    
    def _infer_field_value(self, field_name: str, existing_data: Dict[str, Any], 
                          field_schema: Dict[str, Any]) -> Any:
        """推断字段值"""
        # 基于字段名的推断规则
        inference_rules = {
            'module_name': self._infer_module_name,
            'requirements': self._infer_requirements,
            'verilog_code': self._infer_verilog_code,
            'code': self._infer_code,
            'input_ports': self._infer_input_ports,
            'output_ports': self._infer_output_ports
        }
        
        if field_name in inference_rules:
            return inference_rules[field_name](existing_data, field_schema)
        
        # 提供类型默认值
        field_type = field_schema.get('type')
        if field_type == 'string':
            return ""
        elif field_type == 'array':
            return []
        elif field_type == 'object':
            return {}
        elif field_type == 'integer':
            return 0
        elif field_type == 'number':
            return 0.0
        elif field_type == 'boolean':
            return False
        
        return None
    
    def _infer_module_name(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """推断模块名称"""
        # 从requirements或代码中提取模块名
        for key in ['requirements', 'description', 'task', 'verilog_code', 'code']:
            if key in data:
                content = str(data[key])
                # 查找模块声明
                import re
                match = re.search(r'module\s+([a-zA-Z][a-zA-Z0-9_]*)', content)
                if match:
                    return match.group(1)
        
        # 提供默认值
        return "top_module"
    
    def _infer_requirements(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """推断需求描述"""
        # 从相关字段组合需求
        req_parts = []
        
        for key in ['description', 'task', 'module_name', 'functionality']:
            if key in data:
                req_parts.append(str(data[key]))
        
        if req_parts:
            return " ".join(req_parts)
        
        return "Design requirements not specified"
    
    def _infer_verilog_code(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """推断Verilog代码"""
        # 从相关字段查找代码
        for key in ['code', 'module_code', 'source', 'content']:
            if key in data and isinstance(data[key], str):
                return data[key]
        
        return None
    
    def _infer_code(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """推断代码内容"""
        # 从相关字段查找代码
        for key in ['verilog_code', 'module_code', 'source', 'content']:
            if key in data and isinstance(data[key], str):
                return data[key]
        
        return None
    
    def _infer_input_ports(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """推断输入端口"""
        # 从ports字段或代码中推断
        if 'ports' in data and isinstance(data['ports'], list):
            # 假设前面的是输入端口
            ports = data['ports']
            if len(ports) > 1:
                return ports[:-1]  # 除了最后一个端口
        
        return []
    
    def _infer_output_ports(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """推断输出端口"""
        # 从ports字段或代码中推断
        if 'ports' in data and isinstance(data['ports'], list):
            # 假设最后的是输出端口
            ports = data['ports']
            if ports:
                return [ports[-1]]  # 最后一个端口
        
        return []