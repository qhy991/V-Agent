#!/usr/bin/env python3
"""
Error Analyzer - 错误分析器
==========================

从BaseAgent中提取的错误分析和恢复功能，负责分析工具执行失败原因并提供修复建议。
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..function_calling.parser import ToolCall, ToolResult


@dataclass
class ErrorPattern:
    """错误模式"""
    pattern: str
    error_type: str
    description: str
    suggested_fix: str
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class FailureContext:
    """失败上下文"""
    tool_name: str
    parameters: Dict[str, Any]
    error_message: str
    error_type: str
    attempt_count: int
    max_attempts: int
    execution_time: float
    agent_id: str


class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # 预定义的错误模式
        self.error_patterns = self._initialize_error_patterns()
        
        # 工具特定的错误处理规则
        self.tool_specific_rules = self._initialize_tool_specific_rules()
        
        # 分析统计
        self.analysis_stats = {
            'total_analyses': 0,
            'successful_fixes': 0,
            'failed_fixes': 0,
            'common_errors': {}
        }
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """初始化错误模式"""
        return [
            # 文件相关错误
            ErrorPattern(
                pattern=r"文件.*不存在|File.*not found|No such file",
                error_type="file_not_found",
                description="文件不存在错误",
                suggested_fix="检查文件路径是否正确，确保文件存在",
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"权限.*拒绝|Permission.*denied|Access.*denied",
                error_type="permission_error",
                description="权限错误",
                suggested_fix="检查文件或目录的访问权限",
                severity="high"
            ),
            ErrorPattern(
                pattern=r"磁盘.*满|Disk.*full|No space.*device",
                error_type="disk_full",
                description="磁盘空间不足",
                suggested_fix="清理磁盘空间或选择其他存储位置",
                severity="critical"
            ),
            
            # 参数相关错误
            ErrorPattern(
                pattern=r"缺少.*参数|Missing.*parameter|Required.*parameter",
                error_type="missing_parameter",
                description="缺少必需参数",
                suggested_fix="检查并提供所有必需的参数",
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"参数.*类型.*错误|Parameter.*type.*error|Invalid.*type",
                error_type="parameter_type_error",
                description="参数类型错误",
                suggested_fix="检查参数类型，确保符合工具要求",
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"参数.*值.*无效|Invalid.*value|Value.*out.*range",
                error_type="parameter_value_error",
                description="参数值无效",
                suggested_fix="检查参数值是否在有效范围内",
                severity="medium"
            ),
            
            # 网络相关错误
            ErrorPattern(
                pattern=r"连接.*超时|Connection.*timeout|Timeout.*error",
                error_type="connection_timeout",
                description="连接超时",
                suggested_fix="检查网络连接，增加超时时间",
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"连接.*拒绝|Connection.*refused|Refused.*connection",
                error_type="connection_refused",
                description="连接被拒绝",
                suggested_fix="检查目标服务是否运行，端口是否正确",
                severity="high"
            ),
            
            # 内存相关错误
            ErrorPattern(
                pattern=r"内存.*不足|Out.*memory|Memory.*error",
                error_type="out_of_memory",
                description="内存不足",
                suggested_fix="减少数据量或增加系统内存",
                severity="critical"
            ),
            
            # 通用错误
            ErrorPattern(
                pattern=r"未知.*错误|Unknown.*error|Unexpected.*error",
                error_type="unknown_error",
                description="未知错误",
                suggested_fix="查看详细错误日志，联系技术支持",
                severity="medium"
            )
        ]
    
    def _initialize_tool_specific_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化工具特定规则"""
        return {
            "write_file": {
                "common_errors": {
                    "file_not_found": "检查目录是否存在，确保有写入权限",
                    "permission_error": "检查目录权限，确保可以创建文件",
                    "disk_full": "清理磁盘空间或选择其他目录"
                },
                "parameter_validation": {
                    "filename": "文件名不能为空，不能包含特殊字符",
                    "content": "内容不能为空",
                    "directory": "目录路径必须存在且可写"
                }
            },
            "read_file": {
                "common_errors": {
                    "file_not_found": "检查文件路径是否正确",
                    "permission_error": "检查文件读取权限"
                },
                "parameter_validation": {
                    "filepath": "文件路径不能为空，文件必须存在"
                }
            },
            "generate_verilog_code": {
                "common_errors": {
                    "invalid_requirements": "检查需求描述是否清晰完整",
                    "module_name_error": "模块名必须符合Verilog命名规范"
                },
                "parameter_validation": {
                    "module_name": "模块名必须以字母开头，只能包含字母、数字和下划线",
                    "requirements": "需求描述不能为空，必须包含功能说明"
                }
            }
        }
    
    def analyze_failure(self, failure_context: FailureContext) -> Dict[str, Any]:
        """分析失败原因"""
        self.analysis_stats['total_analyses'] += 1
        
        analysis_result = {
            'error_type': 'unknown',
            'description': '未知错误',
            'suggested_fixes': [],
            'severity': 'medium',
            'confidence': 0.0,
            'tool_specific_advice': [],
            'parameter_issues': [],
            'retry_recommended': True,
            'max_retry_attempts': 3
        }
        
        # 1. 模式匹配分析
        pattern_match = self._match_error_patterns(failure_context.error_message)
        if pattern_match:
            analysis_result.update(pattern_match)
        
        # 2. 工具特定分析
        tool_analysis = self._analyze_tool_specific_issues(failure_context)
        if tool_analysis:
            analysis_result['tool_specific_advice'].extend(tool_analysis)
        
        # 3. 参数验证
        parameter_issues = self._validate_parameters(failure_context)
        if parameter_issues:
            analysis_result['parameter_issues'] = parameter_issues
        
        # 4. 重试建议
        retry_advice = self._generate_retry_advice(failure_context, analysis_result)
        analysis_result['retry_recommended'] = retry_advice['recommended']
        analysis_result['max_retry_attempts'] = retry_advice['max_attempts']
        
        # 5. 更新统计
        self._update_analysis_stats(analysis_result)
        
        return analysis_result
    
    def _match_error_patterns(self, error_message: str) -> Optional[Dict[str, Any]]:
        """匹配错误模式"""
        error_lower = error_message.lower()
        
        for pattern in self.error_patterns:
            if re.search(pattern.pattern, error_lower, re.IGNORECASE):
                return {
                    'error_type': pattern.error_type,
                    'description': pattern.description,
                    'suggested_fixes': [pattern.suggested_fix],
                    'severity': pattern.severity,
                    'confidence': 0.8
                }
        
        return None
    
    def _analyze_tool_specific_issues(self, failure_context: FailureContext) -> List[str]:
        """分析工具特定问题"""
        tool_rules = self.tool_specific_rules.get(failure_context.tool_name, {})
        advice = []
        
        # 检查常见错误
        common_errors = tool_rules.get('common_errors', {})
        for error_type, fix in common_errors.items():
            if error_type in failure_context.error_type.lower():
                advice.append(fix)
        
        # 检查参数验证
        param_validation = tool_rules.get('parameter_validation', {})
        for param_name, validation_rule in param_validation.items():
            if param_name in failure_context.parameters:
                # 这里可以添加更详细的参数验证逻辑
                pass
        
        return advice
    
    def _validate_parameters(self, failure_context: FailureContext) -> List[Dict[str, Any]]:
        """验证参数"""
        issues = []
        tool_rules = self.tool_specific_rules.get(failure_context.tool_name, {})
        param_validation = tool_rules.get('parameter_validation', {})
        
        for param_name, validation_rule in param_validation.items():
            if param_name in failure_context.parameters:
                param_value = failure_context.parameters[param_name]
                
                # 基本验证
                if param_value is None or (isinstance(param_value, str) and not param_value.strip()):
                    issues.append({
                        'parameter': param_name,
                        'issue': '参数为空',
                        'suggestion': validation_rule
                    })
                elif isinstance(param_value, str) and len(param_value) > 1000:
                    issues.append({
                        'parameter': param_name,
                        'issue': '参数值过长',
                        'suggestion': '缩短参数值长度'
                    })
        
        return issues
    
    def _generate_retry_advice(self, failure_context: FailureContext, 
                             analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成重试建议"""
        severity = analysis_result.get('severity', 'medium')
        error_type = analysis_result.get('error_type', 'unknown')
        
        # 根据错误类型和严重程度决定是否重试
        retry_configs = {
            'critical': {'recommended': False, 'max_attempts': 1},
            'high': {'recommended': True, 'max_attempts': 2},
            'medium': {'recommended': True, 'max_attempts': 3},
            'low': {'recommended': True, 'max_attempts': 5}
        }
        
        # 特定错误类型的重试策略
        if error_type in ['disk_full', 'out_of_memory', 'permission_error']:
            return {'recommended': False, 'max_attempts': 1}
        elif error_type in ['connection_timeout', 'connection_refused']:
            return {'recommended': True, 'max_attempts': 5}
        elif error_type in ['missing_parameter', 'parameter_type_error']:
            return {'recommended': False, 'max_attempts': 1}
        
        return retry_configs.get(severity, {'recommended': True, 'max_attempts': 3})
    
    def _update_analysis_stats(self, analysis_result: Dict[str, Any]):
        """更新分析统计"""
        error_type = analysis_result.get('error_type', 'unknown')
        self.analysis_stats['common_errors'][error_type] = \
            self.analysis_stats['common_errors'].get(error_type, 0) + 1
    
    def generate_repair_suggestions(self, tool_calls: List[ToolCall], 
                                  tool_results: List[ToolResult]) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        for tool_call, tool_result in zip(tool_calls, tool_results):
            if not tool_result.success:
                # 创建失败上下文
                failure_context = FailureContext(
                    tool_name=tool_call.tool_name,
                    parameters=tool_call.parameters,
                    error_message=tool_result.error or "未知错误",
                    error_type="unknown",
                    attempt_count=1,
                    max_attempts=3,
                    execution_time=0.0,
                    agent_id="unknown"
                )
                
                # 分析失败
                analysis = self.analyze_failure(failure_context)
                
                # 生成建议
                if analysis['suggested_fixes']:
                    suggestions.append(f"工具 {tool_call.tool_name}: {analysis['suggested_fixes'][0]}")
                
                if analysis['tool_specific_advice']:
                    suggestions.extend(analysis['tool_specific_advice'])
        
        return suggestions
    
    def suggest_alternatives(self, tool_calls: List[ToolCall], 
                           tool_results: List[ToolResult]) -> List[str]:
        """建议替代方案"""
        alternatives = []
        
        for tool_call, tool_result in zip(tool_calls, tool_results):
            if not tool_result.success:
                # 根据工具类型建议替代方案
                if tool_call.tool_name == "write_file":
                    alternatives.append("尝试使用不同的文件路径或目录")
                elif tool_call.tool_name == "read_file":
                    alternatives.append("检查文件是否存在，尝试使用绝对路径")
                elif tool_call.tool_name == "generate_verilog_code":
                    alternatives.append("简化需求描述，分步骤生成代码")
        
        return alternatives
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计"""
        stats = self.analysis_stats.copy()
        
        # 计算成功率
        if stats['total_analyses'] > 0:
            stats['success_rate'] = stats['successful_fixes'] / stats['total_analyses']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def clear_stats(self):
        """清除统计"""
        self.analysis_stats = {
            'total_analyses': 0,
            'successful_fixes': 0,
            'failed_fixes': 0,
            'common_errors': {}
        }
    
    def add_error_pattern(self, pattern: ErrorPattern):
        """添加错误模式"""
        self.error_patterns.append(pattern)
        self.logger.debug(f"添加错误模式: {pattern.error_type}")
    
    def add_tool_specific_rule(self, tool_name: str, rule: Dict[str, Any]):
        """添加工具特定规则"""
        if tool_name not in self.tool_specific_rules:
            self.tool_specific_rules[tool_name] = {}
        
        self.tool_specific_rules[tool_name].update(rule)
        self.logger.debug(f"添加工具规则: {tool_name}")
    
    async def enhance_error_with_context(self, failure_context: Dict[str, Any], max_retry_attempts: int = 3) -> str:
        """增强错误信息，基于上下文生成详细分析"""
        try:
            tool_name = failure_context.get("tool_name", "unknown")
            error = failure_context.get("error", "unknown error")
            error_type = failure_context.get("error_type", "Exception")
            parameters = failure_context.get("parameters", {})
            attempt = failure_context.get("attempt", 1)
            
            # 分析错误类型和常见原因
            error_analysis = self._analyze_error_type(error, error_type, tool_name, parameters)
            
            # 构建增强的错误描述
            enhanced_error = f"""
=== 工具执行失败详细分析 ===
🔧 工具名称: {tool_name}
📝 错误类型: {error_type}
🔍 原始错误: {error}
📊 尝试次数: {attempt}/{max_retry_attempts}
⚙️ 调用参数: {parameters}

🎯 错误分析:
{error_analysis['category']}: {error_analysis['description']}

💡 可能原因:
{chr(10).join(f"• {cause}" for cause in error_analysis['possible_causes'])}

🔧 建议修复:
{chr(10).join(f"• {fix}" for fix in error_analysis['suggested_fixes'])}

⚠️ 影响评估: {error_analysis['impact']}
""".strip()
            
            return enhanced_error
            
        except Exception as e:
            self.logger.warning(f"⚠️ 错误增强失败: {str(e)}")
            return f"工具 {failure_context.get('tool_name', 'unknown')} 执行失败: {failure_context.get('error', 'unknown')}"
    
    def _analyze_error_type(self, error: str, error_type: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析错误类型并提供详细信息"""
        error_lower = error.lower()
        
        # 文件相关错误
        if "no such file or directory" in error_lower or "filenotfounderror" in error_type.lower():
            return {
                "category": "文件访问错误",
                "description": "指定的文件或目录不存在",
                "possible_causes": [
                    "文件路径不正确或文件未创建",
                    "相对路径解析错误",
                    "文件被删除或移动",
                    "权限不足无法访问文件"
                ],
                "suggested_fixes": [
                    "检查文件路径是否正确",
                    "使用绝对路径替代相对路径",
                    "先创建文件或目录再访问",
                    "检查文件权限设置"
                ],
                "impact": "中等 - 可通过修正路径或创建文件解决"
            }
        
        # 权限相关错误
        elif "permission denied" in error_lower or "permissionerror" in error_type.lower():
            return {
                "category": "权限访问错误", 
                "description": "没有足够权限执行操作",
                "possible_causes": [
                    "文件或目录权限设置不当",
                    "用户权限不足",
                    "文件被其他进程占用",
                    "目录为只读状态"
                ],
                "suggested_fixes": [
                    "检查并修改文件权限",
                    "使用具有足够权限的用户运行",
                    "确保文件未被其他进程占用",
                    "检查目录写入权限"
                ],
                "impact": "中等 - 需要调整权限设置"
            }
        
        # 参数相关错误
        elif "typeerror" in error_type.lower() or "missing" in error_lower or "required" in error_lower:
            return {
                "category": "参数错误",
                "description": "工具调用参数不正确或缺失",
                "possible_causes": [
                    "必需参数未提供",
                    "参数类型不匹配",
                    "参数值格式错误",
                    "参数名称拼写错误"
                ],
                "suggested_fixes": [
                    "检查所有必需参数是否提供",
                    "验证参数类型和格式",
                    "参考工具文档确认参数要求",
                    "使用正确的参数名称"
                ],
                "impact": "低 - 可通过修正参数解决"
            }
        
        # API相关错误
        elif "unexpected keyword argument" in error_lower or "got an unexpected keyword argument" in error_lower:
            return {
                "category": "API接口错误",
                "description": "工具API接口不匹配",
                "possible_causes": [
                    "工具方法签名已更改",
                    "传递了不支持的参数",
                    "组件集成不完整",
                    "版本兼容性问题"
                ],
                "suggested_fixes": [
                    "检查工具方法的最新签名",
                    "移除不支持的参数",
                    "更新组件集成代码",
                    "检查版本兼容性"
                ],
                "impact": "高 - 需要修复API调用"
            }
        
        # 属性相关错误
        elif "object has no attribute" in error_lower or "attributeerror" in error_type.lower():
            return {
                "category": "对象属性错误",
                "description": "对象缺少必需的属性或方法",
                "possible_causes": [
                    "对象类型不正确",
                    "方法未实现或已移除",
                    "组件集成不完整",
                    "初始化失败"
                ],
                "suggested_fixes": [
                    "检查对象类型和初始化",
                    "实现缺失的方法",
                    "完成组件集成",
                    "检查初始化过程"
                ],
                "impact": "高 - 需要修复对象结构"
            }
        
        # 网络相关错误
        elif "connection" in error_lower or "timeout" in error_lower:
            return {
                "category": "网络连接错误",
                "description": "网络连接失败或超时",
                "possible_causes": [
                    "网络连接不稳定",
                    "服务端响应超时",
                    "防火墙阻止连接",
                    "服务不可用"
                ],
                "suggested_fixes": [
                    "检查网络连接状态",
                    "增加超时时间设置",
                    "检查防火墙配置",
                    "验证服务可用性"
                ],
                "impact": "中等 - 网络问题通常可恢复"
            }
        
        # 默认错误处理
        else:
            return {
                "category": "未知错误",
                "description": f"未识别的错误类型: {error_type}",
                "possible_causes": [
                    "系统内部错误",
                    "未处理的异常情况",
                    "环境配置问题",
                    "代码逻辑错误"
                ],
                "suggested_fixes": [
                    "检查系统日志获取更多信息",
                    "验证环境配置",
                    "重启相关服务",
                    "联系技术支持"
                ],
                "impact": "未知 - 需要进一步分析"
            } 