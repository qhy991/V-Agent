"""
参数修复器 - 智能分析验证错误并生成修复建议
"""
import re
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .schema_validator import ValidationResult, ValidationError, ValidationErrorType
import logging

logger = logging.getLogger(__name__)

@dataclass
class RepairSuggestion:
    """修复建议"""
    field_path: str
    original_value: Any
    suggested_value: Any
    repair_type: str
    confidence: float  # 0.0 - 1.0
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_path": self.field_path,
            "original_value": self.original_value,
            "suggested_value": self.suggested_value,
            "repair_type": self.repair_type,
            "confidence": self.confidence,
            "explanation": self.explanation
        }

@dataclass
class RepairResult:
    """修复结果"""
    success: bool
    repaired_data: Optional[Dict[str, Any]] = None
    suggestions: List[RepairSuggestion] = None
    llm_prompt: Optional[str] = None  # 用于Agent的修复指令
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class ParameterRepairer:
    """智能参数修复器"""
    
    def __init__(self):
        self.common_patterns = {
            'filename': {
                'pattern': r'^[a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+$',
                'fix_chars': {
                    '<': '_',
                    '>': '_', 
                    ':': '_',
                    '"': '_',
                    '|': '_',
                    '?': '_',
                    '*': '_',
                    ' ': '_'
                }
            },
            'math_expression': {
                'pattern': r'^[0-9+\-*/().\s]+$',
                'allowed_chars': set('0123456789+-*/().')
            },
            'version': {
                'pattern': r'^\d+\.\d+\.\d+$'
            },
            'identifier': {
                'pattern': r'^[a-zA-Z][a-zA-Z0-9_]*$'
            }
        }
        
        self.type_converters = {
            'string': self._convert_to_string,
            'integer': self._convert_to_integer,
            'number': self._convert_to_number,
            'boolean': self._convert_to_boolean,
            'array': self._convert_to_array
        }
    
    def repair_parameters(self, data: Dict[str, Any], schema: Dict[str, Any], 
                         validation_result: ValidationResult) -> RepairResult:
        """
        基于验证结果修复参数
        
        Args:
            data: 原始数据
            schema: Schema定义
            validation_result: 验证结果
            
        Returns:
            RepairResult: 修复结果
        """
        if validation_result.is_valid:
            return RepairResult(success=True, repaired_data=data)
        
        repair_result = RepairResult(success=False)
        repaired_data = data.copy()
        
        # 处理每个错误
        for error in validation_result.errors:
            suggestion = self._generate_repair_suggestion(
                error, data, schema, repaired_data
            )
            
            if suggestion:
                repair_result.suggestions.append(suggestion)
                
                # 尝试自动修复
                if suggestion.confidence >= 0.8:  # 高置信度才自动修复
                    self._apply_repair(repaired_data, suggestion)
        
        # 生成LLM修复指令
        repair_result.llm_prompt = self._generate_llm_repair_prompt(
            validation_result, repair_result.suggestions, schema
        )
        
        # 如果有高置信度的修复，返回修复后的数据
        high_confidence_repairs = [s for s in repair_result.suggestions if s.confidence >= 0.8]
        if high_confidence_repairs:
            repair_result.success = True
            repair_result.repaired_data = repaired_data
        
        return repair_result
    
    def _generate_repair_suggestion(self, error: ValidationError, 
                                   original_data: Dict[str, Any],
                                   schema: Dict[str, Any],
                                   current_data: Dict[str, Any]) -> Optional[RepairSuggestion]:
        """生成单个错误的修复建议"""
        field_path = error.field_path
        
        # 获取原始值
        original_value = self._get_nested_value(original_data, field_path)
        
        # 根据错误类型生成建议
        if error.error_type == ValidationErrorType.TYPE_MISMATCH:
            return self._repair_type_mismatch(error, original_value, schema, field_path)
        
        elif error.error_type == ValidationErrorType.PATTERN_MISMATCH:
            return self._repair_pattern_mismatch(error, original_value, schema, field_path)
        
        elif error.error_type == ValidationErrorType.LENGTH_VIOLATION:
            return self._repair_length_violation(error, original_value, schema, field_path)
        
        elif error.error_type == ValidationErrorType.RANGE_VIOLATION:
            return self._repair_range_violation(error, original_value, schema, field_path)
        
        elif error.error_type == ValidationErrorType.ENUM_VIOLATION:
            return self._repair_enum_violation(error, original_value, schema, field_path)
        
        elif error.error_type == ValidationErrorType.MISSING_REQUIRED:
            return self._repair_missing_required(error, schema, field_path)
        
        elif error.error_type == ValidationErrorType.EXTRA_PROPERTY:
            return self._repair_extra_property(error, field_path)
        
        elif error.error_type == ValidationErrorType.SECURITY_VIOLATION:
            return self._repair_security_violation(error, original_value, field_path)
        
        return None
    
    def _repair_type_mismatch(self, error: ValidationError, value: Any, 
                             schema: Dict[str, Any], field_path: str) -> RepairSuggestion:
        """修复类型不匹配"""
        # 从schema中获取期望类型
        expected_type = self._get_expected_type_from_schema(schema, field_path)
        
        if expected_type in self.type_converters:
            converted_value, confidence = self.type_converters[expected_type](value)
            
            return RepairSuggestion(
                field_path=field_path,
                original_value=value,
                suggested_value=converted_value,
                repair_type="type_conversion",
                confidence=confidence,
                explanation=f"将 {type(value).__name__} 类型转换为 {expected_type} 类型"
            )
        
        # 针对特定情况提供更准确的修复建议
        if expected_type == "array" and isinstance(value, str):
            # 字符串转数组的特殊处理
            if value.startswith('[') and value.endswith(']'):
                # 尝试解析JSON数组
                try:
                    import json
                    parsed_array = json.loads(value)
                    return RepairSuggestion(
                        field_path=field_path,
                        original_value=value,
                        suggested_value=parsed_array,
                        repair_type="string_to_array",
                        confidence=0.9,
                        explanation=f"将JSON字符串解析为数组"
                    )
                except:
                    pass
            
            # 对于字符串数组到对象数组的转换（特别是端口定义）
            if isinstance(value, list) and value and isinstance(value[0], str):
                # 检查是否是端口定义数组
                field_name = field_path.split('.')[-1]
                if field_name in ['input_ports', 'output_ports']:
                    suggested_array = self._convert_string_array_to_port_objects(value)
                    if suggested_array:
                        return RepairSuggestion(
                            field_path=field_path,
                            original_value=value,
                            suggested_value=suggested_array,
                            repair_type="string_array_to_port_objects",
                            confidence=0.9,
                            explanation=f"将端口字符串数组转换为端口对象数组"
                        )
            
            # 对于单个字符串，尝试转换为对象数组
            schema_properties = self._get_nested_value(schema, f"properties.{field_path.split('.')[-1]}.items.properties")
            if schema_properties and ("name" in schema_properties or "width" in schema_properties):
                # 这是一个端口定义数组
                suggested_array = self._convert_string_to_port_array(value)
                if suggested_array:
                    return RepairSuggestion(
                        field_path=field_path,
                        original_value=value,
                        suggested_value=suggested_array,
                        repair_type="string_to_port_array",
                        confidence=0.8,
                        explanation=f"将端口字符串描述转换为端口对象数组"
                    )
        
        return RepairSuggestion(
            field_path=field_path,
            original_value=value,
            suggested_value=value,  # 保持原值而不是None
            repair_type="type_conversion",
            confidence=0.1,  # 低置信度，表示需要人工处理
            explanation=f"无法自动转换为 {expected_type} 类型，需要检查参数格式"
        )
    
    def _repair_pattern_mismatch(self, error: ValidationError, value: Any,
                                schema: Dict[str, Any], field_path: str) -> RepairSuggestion:
        """修复模式不匹配"""
        if not isinstance(value, str):
            return None
        
        # 获取模式
        pattern = self._get_pattern_from_schema(schema, field_path)
        
        # 尝试常见模式的修复
        for pattern_name, pattern_info in self.common_patterns.items():
            if pattern_info['pattern'] == pattern or (pattern_name == 'identifier' and 'a-zA-Z' in pattern):
                if pattern_name == 'filename':
                    fixed_value = self._fix_filename(value)
                    return RepairSuggestion(
                        field_path=field_path,
                        original_value=value,
                        suggested_value=fixed_value,
                        repair_type="pattern_fix",
                        confidence=0.9,
                        explanation="修复文件名中的非法字符"
                    )
                
                elif pattern_name == 'math_expression':
                    fixed_value = self._fix_math_expression(value)
                    confidence = 0.9 if fixed_value and len(fixed_value) > 0 else 0.3
                    return RepairSuggestion(
                        field_path=field_path,
                        original_value=value,
                        suggested_value=fixed_value,
                        repair_type="pattern_fix", 
                        confidence=confidence,
                        explanation="移除数学表达式中的非法字符"
                    )
                
                elif pattern_name == 'identifier':
                    fixed_value = self._fix_identifier(value)
                    return RepairSuggestion(
                        field_path=field_path,
                        original_value=value,
                        suggested_value=fixed_value,
                        repair_type="pattern_fix",
                        confidence=0.9,
                        explanation="修复标识符格式，确保以字母开头"
                    )
        
        return RepairSuggestion(
            field_path=field_path,
            original_value=value,
            suggested_value=None,
            repair_type="pattern_fix",
            confidence=0.3,
            explanation=f"需要匹配模式: {pattern}"
        )
    
    def _repair_length_violation(self, error: ValidationError, value: Any,
                                schema: Dict[str, Any], field_path: str) -> RepairSuggestion:
        """修复长度违规"""
        if not isinstance(value, str):
            return None
        
        min_length = self._get_min_length_from_schema(schema, field_path)
        max_length = self._get_max_length_from_schema(schema, field_path)
        
        if max_length and len(value) > max_length:
            # 截断字符串
            fixed_value = value[:max_length].rstrip()
            return RepairSuggestion(
                field_path=field_path,
                original_value=value,
                suggested_value=fixed_value,
                repair_type="length_fix",
                confidence=0.8,
                explanation=f"截断字符串至最大长度 {max_length}"
            )
        
        elif min_length and len(value) < min_length:
            # 这种情况需要用户手动补充内容
            return RepairSuggestion(
                field_path=field_path,
                original_value=value,
                suggested_value=None,
                repair_type="length_fix",
                confidence=0.2,
                explanation=f"字符串太短，需要至少 {min_length} 个字符"
            )
        
        return None
    
    def _repair_range_violation(self, error: ValidationError, value: Any,
                               schema: Dict[str, Any], field_path: str) -> RepairSuggestion:
        """修复范围违规"""
        if not isinstance(value, (int, float)):
            return None
        
        minimum = self._get_minimum_from_schema(schema, field_path)
        maximum = self._get_maximum_from_schema(schema, field_path)
        
        fixed_value = value
        if minimum is not None and value < minimum:
            fixed_value = minimum
        elif maximum is not None and value > maximum:
            fixed_value = maximum
        
        if fixed_value != value:
            return RepairSuggestion(
                field_path=field_path,
                original_value=value,
                suggested_value=fixed_value,
                repair_type="range_fix",
                confidence=0.9,
                explanation=f"将值调整到允许范围内: [{minimum}, {maximum}]"
            )
        
        return None
    
    def _repair_enum_violation(self, error: ValidationError, value: Any,
                              schema: Dict[str, Any], field_path: str) -> RepairSuggestion:
        """修复枚举违规"""
        enum_values = self._get_enum_from_schema(schema, field_path)
        if not enum_values:
            return None
        
        # 尝试找到最相似的值
        if isinstance(value, str):
            best_match = self._find_closest_string_match(value, enum_values)
            if best_match:
                return RepairSuggestion(
                    field_path=field_path,
                    original_value=value,
                    suggested_value=best_match,
                    repair_type="enum_fix",
                    confidence=0.7,
                    explanation=f"使用最相似的枚举值: {best_match}"
                )
        
        # 如果找不到相似的，建议第一个值
        return RepairSuggestion(
            field_path=field_path,
            original_value=value,
            suggested_value=enum_values[0],
            repair_type="enum_fix",
            confidence=0.5,
            explanation=f"建议使用: {enum_values[0]}，可选值: {enum_values}"
        )
    
    def _repair_missing_required(self, error: ValidationError, schema: Dict[str, Any],
                                field_path: str) -> RepairSuggestion:
        """修复缺失必需字段"""
        # 尝试提供默认值
        default_value = self._get_default_value_from_schema(schema, field_path)
        
        return RepairSuggestion(
            field_path=field_path,
            original_value=None,
            suggested_value=default_value,
            repair_type="add_required",
            confidence=0.6 if default_value is not None else 0.3,
            explanation=f"添加必需字段 '{field_path}'" + 
                       (f" 默认值: {default_value}" if default_value is not None else "")
        )
    
    def _repair_extra_property(self, error: ValidationError, field_path: str) -> RepairSuggestion:
        """修复额外属性"""
        return RepairSuggestion(
            field_path=field_path,
            original_value="<extra_property>",
            suggested_value=None,
            repair_type="remove_extra",
            confidence=0.9,
            explanation=f"移除不允许的额外字段 '{field_path}'"
        )
    
    def _repair_security_violation(self, error: ValidationError, value: Any,
                                  field_path: str) -> RepairSuggestion:
        """修复安全违规"""
        if isinstance(value, str):
            # 移除危险内容
            safe_value = self._sanitize_dangerous_content(value)
            
            return RepairSuggestion(
                field_path=field_path,
                original_value=value,
                suggested_value=safe_value,
                repair_type="security_fix",
                confidence=0.8,
                explanation="移除潜在的安全风险内容"
            )
        
        return RepairSuggestion(
            field_path=field_path,
            original_value=value,
            suggested_value=None,
            repair_type="security_fix",
            confidence=0.3,
            explanation="检测到安全风险，请手动检查"
        )
    
    def _generate_llm_repair_prompt(self, validation_result: ValidationResult,
                                   suggestions: List[RepairSuggestion],
                                   schema: Dict[str, Any]) -> str:
        """生成给LLM Agent的修复指令"""
        prompt = "参数验证失败，请根据以下信息修复参数:\n\n"
        
        # 错误摘要
        prompt += "🔍 验证错误:\n"
        for i, error in enumerate(validation_result.errors, 1):
            prompt += f"{i}. 字段 '{error.field_path}': {error.message}\n"
            prompt += f"   期望: {error.expected}\n"
            prompt += f"   实际: {error.actual}\n\n"
        
        # 修复建议
        if suggestions:
            prompt += "🔧 自动修复建议:\n"
            for i, suggestion in enumerate(suggestions, 1):
                prompt += f"{i}. 字段 '{suggestion.field_path}':\n"
                prompt += f"   修复类型: {suggestion.repair_type}\n"
                prompt += f"   建议值: {suggestion.suggested_value}\n"
                prompt += f"   置信度: {suggestion.confidence:.1%}\n"
                prompt += f"   说明: {suggestion.explanation}\n\n"
        
        # 修复指令
        prompt += "📋 修复指令:\n"
        prompt += "1. 请仔细检查上述错误信息\n"
        prompt += "2. 根据Schema要求修复参数格式\n"
        prompt += "3. 对于高置信度(>80%)的建议，可直接采用\n"
        prompt += "4. 对于低置信度的建议，请仔细考虑后调整\n"
        prompt += "5. 确保修复后的参数符合功能需求\n\n"
        
        # Schema信息
        prompt += "📚 相关Schema信息:\n"
        prompt += f"```json\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n```\n\n"
        
        prompt += "请重新调用工具，使用修复后的参数。"
        
        return prompt
    
    def _apply_repair(self, data: Dict[str, Any], suggestion: RepairSuggestion):
        """应用修复建议到数据"""
        if suggestion.repair_type == "remove_extra":
            self._remove_nested_key(data, suggestion.field_path)
        elif suggestion.suggested_value is not None:
            self._set_nested_value(data, suggestion.field_path, suggestion.suggested_value)
    
    # 辅助方法
    def _convert_to_string(self, value: Any) -> tuple[str, float]:
        """转换为字符串"""
        try:
            return str(value), 0.9
        except:
            return "", 0.3
    
    def _convert_to_integer(self, value: Any) -> tuple[int, float]:
        """转换为整数"""
        if isinstance(value, str):
            if value.isdigit():
                return int(value), 0.9
            try:
                return int(float(value)), 0.7
            except:
                return 0, 0.3
        elif isinstance(value, float):
            return int(value), 0.8
        elif isinstance(value, bool):
            return int(value), 0.6
        return 0, 0.3
    
    def _convert_to_number(self, value: Any) -> tuple[float, float]:
        """转换为数字"""
        if isinstance(value, str):
            try:
                return float(value), 0.9
            except:
                return 0.0, 0.3
        elif isinstance(value, (int, float)):
            return float(value), 0.9
        return 0.0, 0.3
    
    def _convert_to_boolean(self, value: Any) -> tuple[bool, float]:
        """转换为布尔值"""
        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val in ['true', '1', 'yes', 'on']:
                return True, 0.9
            elif lower_val in ['false', '0', 'no', 'off']:
                return False, 0.9
            return bool(value), 0.5
        return bool(value), 0.7
    
    def _convert_to_array(self, value: Any) -> tuple[list, float]:
        """转换为数组"""
        if isinstance(value, list):
            return value, 1.0
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed, 0.8
            except:
                pass
            # 尝试分割字符串
            return value.split(','), 0.6
        return [value], 0.5
    
    def _fix_filename(self, filename: str) -> str:
        """修复文件名"""
        fixed = filename
        for bad_char, good_char in self.common_patterns['filename']['fix_chars'].items():
            fixed = fixed.replace(bad_char, good_char)
        
        # 确保有扩展名
        if '.' not in fixed:
            fixed += '.txt'
        
        # 移除开头的非字母字符
        fixed = re.sub(r'^[^a-zA-Z]+', '', fixed)
        if not fixed:
            fixed = 'output.txt'
        
        return fixed
    
    def _convert_string_array_to_port_objects(self, value: List[str]) -> Optional[List[Dict[str, Any]]]:
        """将端口字符串数组转换为端口对象数组"""
        try:
            port_objects = []
            
            for port_str in value:
                port_obj = self._parse_single_port_string(port_str)
                if port_obj:
                    port_objects.append(port_obj)
            
            return port_objects if port_objects else None
            
        except Exception as e:
            logger.warning(f"端口字符串数组转换失败: {str(e)}")
            return None
    
    def _parse_single_port_string(self, port_str: str) -> Optional[Dict[str, Any]]:
        """解析单个端口字符串"""
        try:
            # 清理字符串
            port_str = port_str.strip().strip('"').strip("'")
            if not port_str:
                return None
            
            # 匹配不同的端口格式
            patterns = [
                # 匹配 "a [7:0]" 格式
                r'^([a-zA-Z][a-zA-Z0-9_]*)\s*\[(\d+):0\]$',
                # 匹配 "a [7:3]" 格式  
                r'^([a-zA-Z][a-zA-Z0-9_]*)\s*\[(\d+):(\d+)\]$',
                # 匹配 "cin" 单bit格式
                r'^([a-zA-Z][a-zA-Z0-9_]*)$'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, port_str)
                if match:
                    name = match.group(1)
                    
                    if len(match.groups()) >= 2:
                        # 有宽度信息
                        if len(match.groups()) == 2:
                            # [7:0] 格式
                            width = int(match.group(2)) + 1
                        else:
                            # [7:3] 格式
                            high = int(match.group(2))
                            low = int(match.group(3))
                            width = abs(high - low) + 1
                    else:
                        # 单bit端口
                        width = 1
                    
                    # 验证名称有效性
                    if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                        return {
                            "name": name,
                            "width": width,
                            "description": f"{width}-bit port"
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"解析端口字符串失败 '{port_str}': {str(e)}")
            return None
    
    def _convert_string_to_port_array(self, value: str) -> Optional[List[Dict[str, Any]]]:
        """将字符串转换为端口对象数组"""
        try:
            # 处理类似 "a [7:0]", "b [7:0]", "cin" 的格式
            if isinstance(value, str):
                # 移除方括号并分割
                parts = [part.strip().replace('"', '').replace("'", '') for part in value.split(',')]
                port_array = []
                
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # 解析端口定义，如 "a [7:0]" 或 "cin"
                    width_match = re.search(r'\[(\d+):0\]', part)
                    if width_match:
                        width = int(width_match.group(1)) + 1
                        name = part[:width_match.start()].strip()
                    else:
                        width = 1
                        name = part.strip()
                    
                    # 验证名称是否有效
                    if name and re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                        port_array.append({
                            "name": name,
                            "width": width,
                            "description": f"{width}-bit {'input' if 'in' in name.lower() else 'output'} port"
                        })
                
                return port_array if port_array else None
                
        except Exception as e:
            logger.warning(f"转换端口数组失败: {e}")
            return None
        
        return None
    
    def _fix_math_expression(self, expr: str) -> str:
        """修复数学表达式"""
        allowed_chars = self.common_patterns['math_expression']['allowed_chars']
        return ''.join(c for c in expr if c in allowed_chars or c.isspace())
    
    def _fix_identifier(self, identifier: str) -> str:
        """修复标识符格式"""
        # 移除所有非字母数字下划线字符
        fixed = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)
        
        # 确保以字母开头
        if fixed and not fixed[0].isalpha():
            fixed = 'id_' + fixed
        
        # 如果完全为空，提供默认值
        if not fixed:
            fixed = 'identifier'
        
        return fixed
    
    def _find_closest_string_match(self, value: str, candidates: List[str]) -> Optional[str]:
        """找到最相似的字符串"""
        value_lower = value.lower()
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # 简单的相似度计算
            if value_lower == candidate_lower:
                return candidate
            elif value_lower in candidate_lower or candidate_lower in value_lower:
                score = len(set(value_lower) & set(candidate_lower)) / len(set(value_lower) | set(candidate_lower))
                if score > best_score:
                    best_score = score
                    best_match = candidate
        
        return best_match if best_score > 0.5 else None
    
    def _sanitize_dangerous_content(self, content: str) -> str:
        """清理危险内容"""
        # 移除常见的危险模式
        dangerous_patterns = [
            r'<script.*?</script>',
            r'javascript:.*?',
            r'on\w+\s*=.*?',
            r'eval\s*\(.*?\)',
            r'exec\s*\(.*?\)',
            r'import\s+os.*?',
            r'subprocess.*?'
        ]
        
        clean_content = content
        for pattern in dangerous_patterns:
            clean_content = re.sub(pattern, '', clean_content, flags=re.IGNORECASE | re.DOTALL)
        
        return clean_content.strip()
    
    # Schema查询辅助方法
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套值"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """设置嵌套值"""
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def _remove_nested_key(self, data: Dict[str, Any], path: str):
        """移除嵌套键"""
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                return
        if keys[-1] in current:
            del current[keys[-1]]
    
    def _get_expected_type_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[str]:
        """从Schema获取期望类型"""
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("type") if field_schema else None
    
    def _get_pattern_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[str]:
        """从Schema获取模式"""
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("pattern") if field_schema else None
    
    def _get_field_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[Dict[str, Any]]:
        """获取字段的Schema定义"""
        keys = field_path.split('.')
        current_schema = schema
        
        for key in keys:
            if current_schema.get("type") == "object":
                properties = current_schema.get("properties", {})
                if key in properties:
                    current_schema = properties[key]
                else:
                    return None
            else:
                return None
        
        return current_schema
    
    def _get_min_length_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[int]:
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("minLength") if field_schema else None
    
    def _get_max_length_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[int]:
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("maxLength") if field_schema else None
    
    def _get_minimum_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[Union[int, float]]:
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("minimum") if field_schema else None
    
    def _get_maximum_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[Union[int, float]]:
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("maximum") if field_schema else None
    
    def _get_enum_from_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[List[Any]]:
        field_schema = self._get_field_schema(schema, field_path)
        return field_schema.get("enum") if field_schema else None
    
    def _get_default_value_from_schema(self, schema: Dict[str, Any], field_path: str) -> Any:
        field_schema = self._get_field_schema(schema, field_path)
        if field_schema:
            if "default" in field_schema:
                return field_schema["default"]
            
            # 根据类型提供默认值
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