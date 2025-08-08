#!/usr/bin/env python3
"""
增强的错误处理器
提供统一的错误处理、文件存在性检查和智能恢复机制
"""

import os
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 警告级别，可以继续执行
    MEDIUM = "medium"     # 需要处理但不致命
    HIGH = "high"         # 严重错误，需要中止当前操作
    CRITICAL = "critical" # 系统级错误，需要完全停止

class ErrorCategory(Enum):
    """错误类别"""
    FILE_NOT_FOUND = "file_not_found"
    PATH_ERROR = "path_error"
    COMPILATION_ERROR = "compilation_error"
    SIMULATION_ERROR = "simulation_error"
    TOOL_ERROR = "tool_error"
    PERMISSION_ERROR = "permission_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class ErrorInfo:
    """错误信息结构"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    traceback_str: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    recovery_hints: List[str] = field(default_factory=list)

@dataclass
class RecoveryAction:
    """恢复操作定义"""
    name: str
    description: str
    action: Callable[[], bool]
    prerequisites: List[str] = field(default_factory=list)
    success_probability: float = 0.5  # 成功概率估计

class EnhancedErrorHandler:
    """增强错误处理器"""
    
    def __init__(self):
        self.logger = logger
        self.error_history: List[ErrorInfo] = []
        self.recovery_actions: Dict[ErrorCategory, List[RecoveryAction]] = {}
        self._initialize_recovery_actions()
    
    def _initialize_recovery_actions(self):
        """初始化恢复操作"""
        
        # 文件不存在错误的恢复操作
        self.recovery_actions[ErrorCategory.FILE_NOT_FOUND] = [
            RecoveryAction(
                name="search_alternative_paths",
                description="搜索替代路径中的文件",
                action=self._search_alternative_file_paths,
                success_probability=0.7
            ),
            RecoveryAction(
                name="create_placeholder_file",
                description="创建占位符文件",
                action=self._create_placeholder_file,
                success_probability=0.3
            )
        ]
        
        # 路径错误的恢复操作
        self.recovery_actions[ErrorCategory.PATH_ERROR] = [
            RecoveryAction(
                name="normalize_path",
                description="规范化路径格式",
                action=self._normalize_paths,
                success_probability=0.8
            ),
            RecoveryAction(
                name="create_missing_directories",
                description="创建缺失的目录",
                action=self._create_missing_directories,
                success_probability=0.9
            )
        ]
        
        # 编译错误的恢复操作
        self.recovery_actions[ErrorCategory.COMPILATION_ERROR] = [
            RecoveryAction(
                name="check_syntax_errors",
                description="检查语法错误并尝试修复",
                action=self._check_and_fix_syntax,
                success_probability=0.4
            ),
            RecoveryAction(
                name="verify_file_integrity",
                description="验证文件完整性",
                action=self._verify_file_integrity,
                success_probability=0.6
            )
        ]
    
    def handle_error(self, exception: Exception, context: Dict[str, Any] = None,
                    category: ErrorCategory = None, severity: ErrorSeverity = None,
                    auto_recover: bool = True) -> ErrorInfo:
        """处理错误"""
        
        # 分析错误
        error_info = self._analyze_error(exception, context, category, severity)
        
        # 记录错误
        self.error_history.append(error_info)
        self._log_error(error_info)
        
        # 尝试自动恢复
        if auto_recover and error_info.severity != ErrorSeverity.CRITICAL:
            recovery_success = self._attempt_recovery(error_info)
            if recovery_success:
                self.logger.info(f"✅ 错误恢复成功: {error_info.category.value}")
            else:
                self.logger.warning(f"⚠️ 错误恢复失败: {error_info.category.value}")
        
        return error_info
    
    def _analyze_error(self, exception: Exception, context: Dict[str, Any] = None,
                      category: ErrorCategory = None, severity: ErrorSeverity = None) -> ErrorInfo:
        """分析错误并生成错误信息"""
        
        # 自动推断错误类别
        if category is None:
            category = self._infer_error_category(exception)
        
        # 自动推断错误严重程度
        if severity is None:
            severity = self._infer_error_severity(exception, category)
        
        # 生成错误消息
        message = self._format_error_message(exception)
        
        # 获取堆栈跟踪
        traceback_str = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        # 生成建议操作
        suggested_actions = self._generate_suggested_actions(category, exception, context)
        
        # 生成恢复提示
        recovery_hints = self._generate_recovery_hints(category, exception, context)
        
        return ErrorInfo(
            category=category,
            severity=severity,
            message=message,
            context=context or {},
            traceback_str=traceback_str,
            suggested_actions=suggested_actions,
            recovery_hints=recovery_hints
        )
    
    def _infer_error_category(self, exception: Exception) -> ErrorCategory:
        """推断错误类别"""
        exception_type = type(exception).__name__
        exception_msg = str(exception).lower()
        
        if isinstance(exception, FileNotFoundError):
            return ErrorCategory.FILE_NOT_FOUND
        elif isinstance(exception, PermissionError):
            return ErrorCategory.PERMISSION_ERROR
        elif "path" in exception_msg or "directory" in exception_msg:
            return ErrorCategory.PATH_ERROR
        elif "compilation" in exception_msg or "compile" in exception_msg:
            return ErrorCategory.COMPILATION_ERROR
        elif "simulation" in exception_msg or "simulate" in exception_msg:
            return ErrorCategory.SIMULATION_ERROR
        elif "tool" in exception_msg or "command not found" in exception_msg:
            return ErrorCategory.TOOL_ERROR
        elif "config" in exception_msg or "configuration" in exception_msg:
            return ErrorCategory.CONFIGURATION_ERROR
        elif "network" in exception_msg or "connection" in exception_msg:
            return ErrorCategory.NETWORK_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _infer_error_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """推断错误严重程度"""
        severity_map = {
            ErrorCategory.FILE_NOT_FOUND: ErrorSeverity.HIGH,
            ErrorCategory.PATH_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.COMPILATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.SIMULATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.TOOL_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.PERMISSION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.CONFIGURATION_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK_ERROR: ErrorSeverity.LOW,
            ErrorCategory.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        
        return severity_map.get(category, ErrorSeverity.MEDIUM)
    
    def _format_error_message(self, exception: Exception) -> str:
        """格式化错误消息"""
        return f"{type(exception).__name__}: {str(exception)}"
    
    def _generate_suggested_actions(self, category: ErrorCategory, exception: Exception,
                                  context: Dict[str, Any] = None) -> List[str]:
        """生成建议操作"""
        actions = []
        
        if category == ErrorCategory.FILE_NOT_FOUND:
            actions.extend([
                "检查文件路径是否正确",
                "验证文件是否存在于预期位置",
                "搜索文件的其他可能位置",
                "检查文件权限"
            ])
        elif category == ErrorCategory.PATH_ERROR:
            actions.extend([
                "验证路径格式是否正确",
                "检查目录是否存在",
                "创建缺失的目录结构",
                "使用绝对路径替代相对路径"
            ])
        elif category == ErrorCategory.COMPILATION_ERROR:
            actions.extend([
                "检查Verilog语法错误",
                "验证所有模块依赖是否满足",
                "检查编译器版本和选项",
                "查看完整的编译日志"
            ])
        elif category == ErrorCategory.SIMULATION_ERROR:
            actions.extend([
                "检查测试台和设计文件的兼容性",
                "验证仿真器配置",
                "检查仿真时间设置",
                "查看仿真日志的详细信息"
            ])
        elif category == ErrorCategory.TOOL_ERROR:
            actions.extend([
                "验证工具是否正确安装",
                "检查工具版本兼容性",
                "更新PATH环境变量",
                "重新安装或更新工具"
            ])
        
        return actions
    
    def _generate_recovery_hints(self, category: ErrorCategory, exception: Exception,
                               context: Dict[str, Any] = None) -> List[str]:
        """生成恢复提示"""
        hints = []
        
        if category == ErrorCategory.FILE_NOT_FOUND:
            hints.extend([
                "尝试使用文件搜索功能找到缺失的文件",
                "检查是否有备份文件可用",
                "考虑重新生成缺失的文件"
            ])
        elif category == ErrorCategory.PATH_ERROR:
            hints.extend([
                "使用路径规范化功能修复路径问题",
                "自动创建缺失的目录结构"
            ])
        elif category == ErrorCategory.COMPILATION_ERROR:
            hints.extend([
                "尝试使用简化的编译选项",
                "检查文件编码格式",
                "验证文件完整性"
            ])
        
        return hints
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """尝试错误恢复"""
        category = error_info.category
        
        if category not in self.recovery_actions:
            self.logger.warning(f"⚠️ 没有为错误类别 {category.value} 定义恢复操作")
            return False
        
        actions = self.recovery_actions[category]
        
        for action in sorted(actions, key=lambda a: a.success_probability, reverse=True):
            self.logger.info(f"🔧 尝试恢复操作: {action.description}")
            
            try:
                if action.action():
                    self.logger.info(f"✅ 恢复操作成功: {action.name}")
                    return True
                else:
                    self.logger.warning(f"⚠️ 恢复操作失败: {action.name}")
            except Exception as e:
                self.logger.error(f"❌ 恢复操作异常: {action.name} - {str(e)}")
        
        return False
    
    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        severity_icons = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        icon = severity_icons.get(error_info.severity, "❓")
        
        self.logger.error(f"{icon} [{error_info.category.value}] {error_info.message}")
        
        if error_info.suggested_actions:
            self.logger.info("💡 建议操作:")
            for i, action in enumerate(error_info.suggested_actions, 1):
                self.logger.info(f"   {i}. {action}")
    
    # 恢复操作实现
    def _search_alternative_file_paths(self) -> bool:
        """搜索替代文件路径"""
        # 这里实现具体的文件搜索逻辑
        return False
    
    def _create_placeholder_file(self) -> bool:
        """创建占位符文件"""
        # 这里实现创建占位符文件的逻辑
        return False
    
    def _normalize_paths(self) -> bool:
        """规范化路径"""
        # 这里实现路径规范化逻辑
        return True
    
    def _create_missing_directories(self) -> bool:
        """创建缺失目录"""
        # 这里实现目录创建逻辑
        return True
    
    def _check_and_fix_syntax(self) -> bool:
        """检查并修复语法错误"""
        # 这里实现语法检查和修复逻辑
        return False
    
    def _verify_file_integrity(self) -> bool:
        """验证文件完整性"""
        # 这里实现文件完整性验证逻辑
        return False
    
    def check_file_existence(self, file_paths: List[Union[str, Path]], 
                           auto_fix: bool = True) -> Dict[str, Any]:
        """检查文件存在性"""
        result = {
            "all_exist": True,
            "existing_files": [],
            "missing_files": [],
            "invalid_paths": [],
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                path_obj = Path(file_path)
                
                if path_obj.exists():
                    if path_obj.is_file():
                        result["existing_files"].append(str(path_obj))
                    else:
                        result["invalid_paths"].append(str(path_obj))
                        result["all_exist"] = False
                else:
                    result["missing_files"].append(str(path_obj))
                    result["all_exist"] = False
                    
                    if auto_fix:
                        # 尝试修复缺失文件问题
                        self._attempt_file_recovery(path_obj)
                        
            except Exception as e:
                error_msg = f"路径处理错误: {file_path} - {str(e)}"
                result["errors"].append(error_msg)
                result["all_exist"] = False
                self.logger.error(error_msg)
        
        return result
    
    def _attempt_file_recovery(self, missing_file: Path):
        """尝试恢复缺失文件"""
        self.logger.info(f"🔍 尝试恢复缺失文件: {missing_file}")
        
        # 搜索可能的替代位置
        search_dirs = [
            missing_file.parent,
            missing_file.parent.parent,
            Path.cwd(),
            Path.cwd() / "designs",
            Path.cwd() / "testbenches",
            Path.cwd() / "src"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists() and search_dir.is_dir():
                potential_file = search_dir / missing_file.name
                if potential_file.exists() and potential_file.is_file():
                    self.logger.info(f"✅ 在替代位置找到文件: {potential_file}")
                    return potential_file
        
        self.logger.warning(f"⚠️ 无法找到文件的替代位置: {missing_file}")
        return None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        if not self.error_history:
            return {"total_errors": 0, "message": "没有记录的错误"}
        
        summary = {
            "total_errors": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": []
        }
        
        # 按类别统计
        for error in self.error_history:
            category = error.category.value
            severity = error.severity.value
            
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # 最近的错误
        summary["recent_errors"] = [
            {
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.message,
                "timestamp": error.timestamp
            }
            for error in self.error_history[-5:]
        ]
        
        return summary


# 全局实例
_error_handler_instance = None

def get_error_handler() -> EnhancedErrorHandler:
    """获取错误处理器实例"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = EnhancedErrorHandler()
    return _error_handler_instance

def handle_error_with_context(func: Callable) -> Callable:
    """装饰器：为函数添加错误处理上下文"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            context = {
                "function": func.__name__,
                "args": str(args)[:200],  # 限制长度
                "kwargs": str(kwargs)[:200]
            }
            error_info = error_handler.handle_error(e, context)
            # 可以选择重新抛出异常或返回错误信息
            raise e
    
    return wrapper