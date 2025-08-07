"""
JSON Schema 验证器 - 支持详细错误报告和修复建议
"""
import re
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationErrorType(Enum):
    """验证错误类型"""
    TYPE_MISMATCH = "type_mismatch"
    MISSING_REQUIRED = "missing_required"
    EXTRA_PROPERTY = "extra_property"
    PATTERN_MISMATCH = "pattern_mismatch"
    LENGTH_VIOLATION = "length_violation"
    RANGE_VIOLATION = "range_violation"
    ENUM_VIOLATION = "enum_violation"
    ARRAY_SIZE_VIOLATION = "array_size_violation"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class ValidationError:
    """详细的验证错误信息"""
    error_type: ValidationErrorType
    field_path: str
    expected: str
    actual: str
    message: str
    suggestion: Optional[str] = None
    severity: str = "error"  # error, warning, info
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "field_path": self.field_path,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "suggestion": self.suggestion,
            "severity": self.severity
        }

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    sanitized_data: Optional[Dict[str, Any]] = None
    
    def add_error(self, error: ValidationError):
        """添加错误"""
        if error.severity == "error":
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == "warning":
            self.warnings.append(error)
    
    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if not self.errors:
            return "验证成功"
        
        summary = f"发现 {len(self.errors)} 个错误:\n"
        for i, error in enumerate(self.errors, 1):
            summary += f"{i}. [{error.field_path}] {error.message}\n"
            if error.suggestion:
                summary += f"   建议: {error.suggestion}\n"
        
        return summary
    
    def get_repair_instructions(self) -> str:
        """获取修复指令"""
        if not self.errors:
            return ""
        
        instructions = "参数修复指令:\n"
        for error in self.errors:
            instructions += f"• 字段 '{error.field_path}': {error.message}\n"
            if error.suggestion:
                instructions += f"  修复建议: {error.suggestion}\n"
            instructions += f"  期望格式: {error.expected}\n"
            instructions += f"  当前值: {error.actual}\n\n"
        
        return instructions

class SchemaValidator:
    """增强的Schema验证器"""
    
    def __init__(self):
        self.security_patterns = {
            'sql_injection': [
                r"(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
                r"(exec\s*\(|execute\s*\(|sp_executesql)"
            ],
            'code_injection': [
                r"(eval\s*\(|exec\s*\(|import\s+os|subprocess)",
                r"(__import__|getattr|setattr|delattr)"
            ],
            'path_traversal': [
                r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
                r"(/etc/passwd|/etc/shadow|C:\\Windows\\System32)"
            ],
            'xss': [
                r"(<script|javascript:|on\w+\s*=)",
                r"(<iframe|<object|<embed|<link)"
            ]
        }
    
    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """
        验证数据是否符合Schema
        
        Args:
            data: 要验证的数据
            schema: JSON Schema定义
            
        Returns:
            ValidationResult: 详细的验证结果
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # 1. 基础Schema验证
            self._validate_object(data, schema, "", result)
            
            # 2. 安全性检查
            self._security_check(data, "", result)
            
            # 3. 数据清理和标准化
            if result.is_valid:
                result.sanitized_data = self._sanitize_data(data, schema)
            
        except Exception as e:
            logger.error(f"Schema验证异常: {str(e)}")
            result.add_error(ValidationError(
                error_type=ValidationErrorType.TYPE_MISMATCH,
                field_path="root",
                expected="valid data",  
                actual=str(type(data)),
                message=f"验证过程发生异常: {str(e)}",
                suggestion="请检查数据格式是否正确"
            ))
        
        return result
    
    def _validate_object(self, data: Dict[str, Any], schema: Dict[str, Any], 
                        path: str, result: ValidationResult):
        """验证对象类型"""
        if schema.get("type") != "object":
            result.add_error(ValidationError(
                error_type=ValidationErrorType.TYPE_MISMATCH,
                field_path=path or "root",
                expected="object",
                actual=schema.get("type", "unknown"),
                message="Schema类型必须是object"
            ))
            return
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_properties = schema.get("additionalProperties", True)
        
        # 检查必需字段
        for field in required:
            if field not in data:
                field_path = f"{path}.{field}" if path else field
                result.add_error(ValidationError(
                    error_type=ValidationErrorType.MISSING_REQUIRED,
                    field_path=field_path,
                    expected=f"required field: {field}",
                    actual="missing",
                    message=f"缺少必需字段: {field}",
                    suggestion=f"请添加字段 '{field}'"
                ))
        
        # 检查额外字段
        if not additional_properties:
            for field in data:
                if field not in properties:
                    field_path = f"{path}.{field}" if path else field
                    result.add_error(ValidationError(
                        error_type=ValidationErrorType.EXTRA_PROPERTY,
                        field_path=field_path,
                        expected="allowed properties: " + ", ".join(properties.keys()),
                        actual=f"extra field: {field}",
                        message=f"不允许的额外字段: {field}",
                        suggestion=f"请移除字段 '{field}' 或检查拼写"
                    ))
        
        # 验证每个字段
        for field, value in data.items():
            if field in properties:
                field_path = f"{path}.{field}" if path else field
                self._validate_property(value, properties[field], field_path, result)
    
    def _validate_property(self, value: Any, prop_schema: Dict[str, Any], 
                          field_path: str, result: ValidationResult):
        """验证单个属性"""
        prop_type = prop_schema.get("type")
        
        # 类型检查
        if not self._check_type(value, prop_type):
            result.add_error(ValidationError(
                error_type=ValidationErrorType.TYPE_MISMATCH,
                field_path=field_path,
                expected=f"type: {prop_type}",
                actual=f"type: {type(value).__name__}",
                message=f"字段类型错误，期望 {prop_type}，实际 {type(value).__name__}",
                suggestion=self._get_type_conversion_suggestion(value, prop_type)
            ))
            return
        
        # 字符串特定验证
        if prop_type == "string" and isinstance(value, str):
            self._validate_string(value, prop_schema, field_path, result)
        
        # 数值特定验证
        elif prop_type in ["integer", "number"] and isinstance(value, (int, float)):
            self._validate_number(value, prop_schema, field_path, result)
        
        # 数组特定验证
        elif prop_type == "array" and isinstance(value, list):
            self._validate_array(value, prop_schema, field_path, result)
        
        # 对象特定验证
        elif prop_type == "object" and isinstance(value, dict):
            self._validate_object(value, prop_schema, field_path, result)
    
    def _validate_string(self, value: str, schema: Dict[str, Any], 
                        field_path: str, result: ValidationResult):
        """验证字符串"""
        # 长度检查
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        
        if min_length is not None and len(value) < min_length:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.LENGTH_VIOLATION,
                field_path=field_path,
                expected=f"length >= {min_length}",
                actual=f"length = {len(value)}",
                message=f"字符串长度不能少于 {min_length}",
                suggestion=f"请增加字符串长度至至少 {min_length} 个字符"
            ))
        
        if max_length is not None and len(value) > max_length:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.LENGTH_VIOLATION,
                field_path=field_path,
                expected=f"length <= {max_length}",
                actual=f"length = {len(value)}",
                message=f"字符串长度不能超过 {max_length}",
                suggestion=f"请缩短字符串长度至最多 {max_length} 个字符"
            ))
        
        # 模式匹配
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, value):
            result.add_error(ValidationError(
                error_type=ValidationErrorType.PATTERN_MISMATCH,
                field_path=field_path,
                expected=f"pattern: {pattern}",
                actual=f"value: {value}",
                message=f"字符串不符合要求的格式",
                suggestion=self._get_pattern_suggestion(pattern, value)
            ))
        
        # 枚举检查
        enum_values = schema.get("enum")
        if enum_values and value not in enum_values:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.ENUM_VIOLATION,
                field_path=field_path,
                expected=f"one of: {enum_values}",
                actual=f"value: {value}",
                message=f"值必须是以下选项之一: {enum_values}",
                suggestion=f"请选择: {', '.join(map(str, enum_values))}"
            ))
    
    def _validate_number(self, value: Union[int, float], schema: Dict[str, Any],
                        field_path: str, result: ValidationResult):
        """验证数值"""
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        
        if minimum is not None and value < minimum:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.RANGE_VIOLATION,
                field_path=field_path,
                expected=f"value >= {minimum}",
                actual=f"value = {value}",
                message=f"数值不能小于 {minimum}",
                suggestion=f"请输入大于等于 {minimum} 的值"
            ))
        
        if maximum is not None and value > maximum:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.RANGE_VIOLATION,
                field_path=field_path,
                expected=f"value <= {maximum}",
                actual=f"value = {value}",
                message=f"数值不能大于 {maximum}",
                suggestion=f"请输入小于等于 {maximum} 的值"
            ))
    
    def _validate_array(self, value: List[Any], schema: Dict[str, Any],
                       field_path: str, result: ValidationResult):
        """验证数组"""
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        
        if min_items is not None and len(value) < min_items:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.ARRAY_SIZE_VIOLATION,
                field_path=field_path,
                expected=f"at least {min_items} items",
                actual=f"{len(value)} items",
                message=f"数组至少需要 {min_items} 个元素",
                suggestion=f"请添加更多元素，至少需要 {min_items} 个"
            ))
        
        if max_items is not None and len(value) > max_items:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.ARRAY_SIZE_VIOLATION,
                field_path=field_path,
                expected=f"at most {max_items} items",
                actual=f"{len(value)} items",
                message=f"数组最多允许 {max_items} 个元素",
                suggestion=f"请减少元素数量，最多允许 {max_items} 个"
            ))
        
        # 验证数组元素
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(value):
                item_path = f"{field_path}[{i}]"
                self._validate_property(item, items_schema, item_path, result)
    
    def _security_check(self, data: Dict[str, Any], path: str, result: ValidationResult):
        """安全性检查"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, str):
                # 检查危险模式
                for category, patterns in self.security_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            result.add_error(ValidationError(
                                error_type=ValidationErrorType.SECURITY_VIOLATION,
                                field_path=current_path,
                                expected="safe content",
                                actual=f"potential {category}",
                                message=f"检测到潜在的安全风险: {category}",
                                suggestion="请移除可能的恶意代码或使用安全的替代方案"
                            ))
            
            elif isinstance(value, dict):
                self._security_check(value, current_path, result)
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型匹配"""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        return True
    
    def _get_type_conversion_suggestion(self, value: Any, expected_type: str) -> str:
        """获取类型转换建议"""
        if expected_type == "string":
            return f"请将值转换为字符串，例如: \"{value}\""
        elif expected_type == "integer":
            if isinstance(value, str) and value.isdigit():
                return f"请将字符串转换为整数: {value}"
            elif isinstance(value, float):
                return f"请将小数转换为整数: {int(value)}"
        elif expected_type == "boolean":
            return "请使用 true 或 false"
        elif expected_type == "array":
            return f"请使用数组格式，例如: [{value}]"
        
        return f"请提供 {expected_type} 类型的值"
    
    def _get_pattern_suggestion(self, pattern: str, value: str) -> str:
        """获取模式匹配建议"""
        pattern_suggestions = {
            r"^[a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+$": "文件名应包含扩展名，只允许字母、数字、下划线、点和横线",
            r"^[0-9+\-*/().\s]+$": "只允许数字和基本数学运算符 (+, -, *, /, (, ), .)",
            r"^\d+\.\d+\.\d+$": "版本号格式应为 x.y.z，例如: 1.2.3",
            r"^[a-zA-Z][a-zA-Z0-9_]*$": "标识符应以字母开头，只包含字母、数字和下划线"
        }
        
        return pattern_suggestions.get(pattern, f"请确保值匹配模式: {pattern}")
    
    def _sanitize_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """清理和标准化数据"""
        sanitized = {}
        properties = schema.get("properties", {})
        
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                sanitized_value = self._sanitize_value(value, prop_schema)
                sanitized[key] = sanitized_value
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_value(self, value: Any, schema: Dict[str, Any]) -> Any:
        """清理单个值"""
        if isinstance(value, str):
            # 移除潜在危险字符
            value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)  # 控制字符
            
            # 限制长度
            max_length = schema.get("maxLength")
            if max_length and len(value) > max_length:
                value = value[:max_length]
            
            return value.strip()
        
        elif isinstance(value, dict) and schema.get("type") == "object":
            return self._sanitize_data(value, schema)
        
        elif isinstance(value, list) and schema.get("type") == "array":
            items_schema = schema.get("items")
            if items_schema:
                return [self._sanitize_value(item, items_schema) for item in value]
        
        return value