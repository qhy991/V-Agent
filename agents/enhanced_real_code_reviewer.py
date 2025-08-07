#!/usr/bin/env python3
"""
重构后的代码审查智能体
使用统一的LLM通信模块，减少重复代码
"""

import os
import json
import asyncio
import subprocess
import tempfile
import re
import time
from typing import Dict, Any, Set, List, Tuple, Optional
from pathlib import Path

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from core.base_agent import TaskMessage
from core.response_format import StandardizedResponse, TaskStatus, ResponseType, QualityMetrics, IssueReport
from datetime import datetime
from core.llm_communication import UnifiedLLMClientManager, SystemPromptBuilder, CallType
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir
from tools.script_tools import ScriptManager

# 导入现有模块化组件
from core.error_analysis.analyzer import ErrorAnalyzer, FailureContext
from core.file_operations.manager import FileOperationManager, FileOperationConfig
from core.function_calling.executor import ToolExecutionEngine, ExecutionContext
from core.conversation.manager import ConversationManager


class EnhancedRealCodeReviewAgent(EnhancedBaseAgent):
    """重构后的代码审查智能体 - 使用统一LLM通信模块"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="enhanced_real_code_review_agent",
            role="code_reviewer",
            capabilities={
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ANALYSIS,
                AgentCapability.SPECIFICATION_ANALYSIS,
                AgentCapability.TEST_GENERATION,
                AgentCapability.VERIFICATION
            },
            config=config
        )
        
        # 初始化配置
        self.config = config or FrameworkConfig.from_env()
        
        # 使用统一的LLM通信管理器
        self.llm_manager = UnifiedLLMClientManager(
            agent_id=self.agent_id,
            role="code_reviewer",
            config=self.config
        )
        
        # 使用统一的System Prompt构建器
        self.prompt_builder = SystemPromptBuilder()
        
        # 🔧 向后兼容：保留llm_client属性（某些工具方法可能直接调用）
        from llm_integration.enhanced_llm_client import EnhancedLLMClient
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('EnhancedRealCodeReviewAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        # 初始化脚本管理器
        self.script_manager = ScriptManager(work_dir=self.artifacts_dir)
        
        # 🔧 新增：初始化模块化组件
        # 错误分析器 - 扩展Verilog专用错误模式
        self.error_analyzer = ErrorAnalyzer(logger=self.logger)
        self._extend_error_analyzer_for_verilog()
        
        # 文件操作管理器
        file_config = FileOperationConfig(
            default_artifacts_dir=self.artifacts_dir,
            enable_cache=True,
            max_file_size=10 * 1024 * 1024,  # 10MB
            backup_enabled=True
        )
        self.file_manager = FileOperationManager(config=file_config, logger=self.logger)
        
        # 工具执行引擎
        exec_context = ExecutionContext(
            agent_id=self.agent_id,
            max_retry_attempts=3,
            retry_delay=1.0,
            enable_logging=True
        )
        self.tool_executor = ToolExecutionEngine(context=exec_context, logger=self.logger)
        
        # 对话管理器
        self.conversation_manager = ConversationManager(agent_id=self.agent_id, logger=self.logger)
        
        # 注册增强工具
        self._register_enhanced_code_review_tools()
        
        self.logger.debug(f"🔍 重构后的代码审查智能体初始化完成（集成模块化组件）")
        
        # 错误处理相关属性（简化后）
        self.error_classification_cache = {}
        # 注：simulation_error_patterns已移至ErrorAnalyzer中统一管理
    
    def _extend_error_analyzer_for_verilog(self):
        """扩展ErrorAnalyzer以支持Verilog专用错误模式"""
        from core.error_analysis.analyzer import ErrorPattern
        
        # 添加Verilog专用错误模式
        verilog_patterns = [
            # Verilog编译语法错误
            ErrorPattern(
                pattern=r"syntax error|Syntax in assignment|Malformed statement|unexpected token|missing semicolon",
                error_type="verilog_compilation_syntax",
                description="Verilog语法错误",
                suggested_fix="检查Verilog语法、端口定义、信号声明",
                severity="high"
            ),
            # Verilog编译语义错误
            ErrorPattern(
                pattern=r"type mismatch|width mismatch|port connection|module not found|undefined variable",
                error_type="verilog_compilation_semantic", 
                description="Verilog语义错误",
                suggested_fix="检查模块连接、信号宽度、变量声明",
                severity="high"
            ),
            # Verilog仿真运行时错误
            ErrorPattern(
                pattern=r"simulation timeout|infinite loop|deadlock|assertion failure|testbench failure",
                error_type="verilog_simulation_runtime",
                description="Verilog仿真运行时错误",
                suggested_fix="检查仿真时间、时钟生成、复位逻辑",
                severity="medium"
            ),
            # Verilog测试台错误
            ErrorPattern(
                pattern=r"testbench error|assertion|coverage|test case|stimulus|monitor",
                error_type="verilog_testbench_logic",
                description="Verilog测试台逻辑错误",
                suggested_fix="检查测试台激励生成和断言检查",
                severity="medium"
            )
        ]
        
        # 扩展现有的错误模式
        self.error_analyzer.error_patterns.extend(verilog_patterns)
        
        self.logger.debug(f"✅ ErrorAnalyzer已扩展 {len(verilog_patterns)} 个Verilog专用错误模式")
    
    def _classify_simulation_error(self, error_message: str, error_context: Dict = None) -> Dict[str, Any]:
        """使用统一的ErrorAnalyzer进行错误分类（重构后）"""
        # 创建失败上下文
        failure_context = FailureContext(
            tool_name=error_context.get('tool_name', 'simulation') if error_context else 'simulation',
            parameters=error_context.get('parameters', {}) if error_context else {},
            error_message=error_message,
            error_type="unknown",
            attempt_count=error_context.get('attempt_count', 1) if error_context else 1,
            max_attempts=3,
            execution_time=error_context.get('execution_time', 0.0) if error_context else 0.0,
            agent_id=self.agent_id
        )
        
        # 使用统一的ErrorAnalyzer进行分析
        analysis_result = self.error_analyzer.analyze_failure(failure_context)
        
        # 转换为审查智能体期望的格式
        error_info = {
            "error_type": analysis_result.get('error_type', 'unknown'),
            "severity": analysis_result.get('severity', 'medium'),
            "category": self._map_error_type_to_category(analysis_result.get('error_type', 'unknown')),
            "suggested_actions": analysis_result.get('suggested_fixes', []),
            "fix_priority": analysis_result.get('severity', 'medium'),
            "detailed_analysis": {
                "issue": analysis_result.get('description', '未知错误'),
                "confidence": analysis_result.get('confidence', 0.0),
                "tool_specific_advice": analysis_result.get('tool_specific_advice', []),
                "parameter_issues": analysis_result.get('parameter_issues', [])
            }
        }
        
        # 记录到缓存
        cache_key = f"{hash(error_message)}_{failure_context.tool_name}"
        self.error_classification_cache[cache_key] = error_info
        
        return error_info
    
    def _map_error_type_to_category(self, error_type: str) -> str:
        """将错误类型映射到分类"""
        mapping = {
            'verilog_compilation_syntax': 'compilation',
            'verilog_compilation_semantic': 'compilation',
            'verilog_simulation_runtime': 'simulation',
            'verilog_testbench_logic': 'verification',
            'file_not_found': 'system',
            'permission_error': 'system',
            'parameter_type_error': 'parameter'
        }
        return mapping.get(error_type, 'general')
    
    def _enhance_error_information(self, error_message: str, error_context: Dict = None, 
                                 simulation_result: Dict = None) -> Dict[str, Any]:
        """向后兼容的错误信息增强方法（简化版，委托给ErrorAnalyzer）"""
        try:
            # 使用新的错误分析功能
            classification = self._classify_simulation_error(error_message, error_context)
            
            # 构建兼容的返回格式
            enhanced_error = {
                "original_error": error_message,
                "error_classification": {
                    "error_type": classification.get("error_type", "unknown"),
                    "severity": classification.get("severity", "medium"),
                    "category": classification.get("category", "general"),
                    "fix_priority": classification.get("fix_priority", "medium"),
                    "detailed_analysis": {
                        "issue": classification.get("detailed_analysis", {}).get("issue", "未知错误"),
                        "common_causes": classification.get("detailed_analysis", {}).get("common_causes", ["未知原因"]),
                        "fix_strategy": classification.get("detailed_analysis", {}).get("fix_strategy", "需要进一步分析")
                    }
                },
                "context_information": error_context or {},
                "technical_details": simulation_result or {},
                "recovery_suggestions": classification.get("suggested_actions", ["检查错误日志", "重试操作"]),
                "debug_information": {
                    "severity": classification.get("severity", "medium"),
                    "category": classification.get("category", "general"),
                    "confidence": classification.get("detailed_analysis", {}).get("confidence", 0.5),
                    "suggested_debug_steps": ["分析错误信息", "检查代码语法", "验证文件路径"]
                }
            }
            
            return enhanced_error
            
        except Exception as e:
            self.logger.warning(f"⚠️ 错误信息增强失败，返回基础信息: {e}")
            return {
                "original_error": error_message,
                "error_classification": {"error_type": "unknown", "severity": "medium"},
                "context_information": error_context or {},
                "technical_details": {},
                "recovery_suggestions": ["检查错误日志", "重试操作"],
                "debug_information": {"severity": "medium", "category": "general"}
            }
    
    def _generate_simulation_error_prompt(self, enhanced_error: Dict[str, Any], 
                                        design_code: str = None, testbench_code: str = None) -> str:
        """
        特殊Prompt设计：针对仿真错误设计专门的prompt
        
        Args:
            enhanced_error: 增强的错误信息
            design_code: 设计代码
            testbench_code: 测试台代码
            
        Returns:
            专门针对仿真错误的prompt
        """
        error_class = enhanced_error["error_classification"]
        context_info = enhanced_error["context_information"]
        tech_details = enhanced_error["technical_details"]
        
        prompt = f"""
🚨 **仿真错误诊断与修复专家模式**

## 📋 错误分类信息
- **错误类型**: {error_class.get('error_type', 'unknown')}
- **严重程度**: {error_class.get('severity', 'medium')}
- **错误类别**: {error_class.get('category', 'general')}
- **修复优先级**: {error_class.get('fix_priority', 'medium')}

## 🔍 错误详情
**原始错误信息**:
```
{enhanced_error['original_error']}
```

**错误分析**:
{error_class.get('detailed_analysis', {}).get('issue', '未知错误')}

**常见原因**:
{', '.join(error_class.get('detailed_analysis', {}).get('common_causes', ['未知原因']))}

**修复策略**:
{error_class.get('detailed_analysis', {}).get('fix_strategy', '需要进一步分析')}

## 📊 上下文信息
- **编译阶段**: {context_info.get('compilation_stage', 'unknown')}
- **仿真器**: {context_info.get('simulator_info', 'unknown')}
- **工作目录**: {context_info.get('working_directory', 'unknown')}
- **执行命令**: {context_info.get('command_executed', 'unknown')}

## 🛠️ 技术细节
- **执行状态**: {'成功' if tech_details.get('success') else '失败'}
- **返回码**: {tech_details.get('return_code', -1)}
- **错误输出**: {tech_details.get('error_output', '无')}

## 🎯 建议的修复行动
{chr(10).join(f"- {action}" for action in enhanced_error.get('recovery_suggestions', ['检查错误日志']))}

## 📝 调试指导
{chr(10).join(f"- {step}" for step in enhanced_error.get('debug_information', {}).get('suggested_debug_steps', ['分析错误信息']))}

## 🔧 你的任务
作为硬件验证专家，请：

1. **深入分析错误原因**：基于错误分类和上下文信息，准确识别问题的根本原因
2. **提供具体修复方案**：给出详细的代码修改建议，包括具体的语法修正
3. **验证修复效果**：确保修复后的代码能够通过编译和仿真
4. **预防类似问题**：提供最佳实践建议，避免类似错误再次发生

## 📋 可用工具
- `generate_testbench`: 重新生成测试台
- `run_simulation`: 重新运行仿真
- `analyze_test_failures`: 分析测试失败原因
- `write_file`: 保存修复后的代码

请开始分析和修复这个仿真错误。
"""
        
        # 如果有设计代码，添加到prompt中
        if design_code:
            prompt += f"\n## 📄 设计代码\n```verilog\n{design_code}\n```\n"
        
        # 如果有测试台代码，添加到prompt中
        if testbench_code:
            prompt += f"\n## 🧪 测试台代码\n```verilog\n{testbench_code}\n```\n"
        
        return prompt
    
    def _normalize_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """参数标准化方法 - 修复向后兼容问题"""
        normalized_params = parameters.copy()
        
        # 🔧 修复read_file参数不匹配问题
        if tool_name == "read_file":
            # 如果传入了file_path但缺少filepath，进行映射
            if "file_path" in normalized_params and "filepath" not in normalized_params:
                normalized_params["filepath"] = normalized_params["file_path"]
                self.logger.debug(f"🔧 参数映射: file_path -> filepath for {tool_name}")
            # 如果只有filepath，确保file_path也存在（为了兼容性）
            elif "filepath" in normalized_params and "file_path" not in normalized_params:
                normalized_params["file_path"] = normalized_params["filepath"]
                self.logger.debug(f"🔧 参数映射: filepath -> file_path for {tool_name}")
        
        # 🔧 修复write_file参数兼容性问题
        elif tool_name == "write_file":
            # 处理文件名参数兼容性
            if "file_name" in normalized_params and "filename" not in normalized_params:
                normalized_params["filename"] = normalized_params["file_name"]
                self.logger.debug(f"🔧 参数映射: file_name -> filename for {tool_name}")
        
        return normalized_params
    
    def _register_enhanced_code_review_tools(self):
        """注册带Schema验证的代码审查工具"""
        
        # 1. 测试台生成工具
        self.register_enhanced_tool(
            name="generate_testbench",
            func=self._tool_generate_testbench,
            description="为Verilog模块生成全面的测试台(testbench)",
            security_level="normal",
            category="verification",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "目标模块名称，必须以字母开头"
                    },
                    "module_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "完整的Verilog模块代码"
                    },
                    "test_scenarios": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 100,
                                    "description": "测试场景名称"
                                },
                                "description": {
                                    "type": "string",
                                    "minLength": 5,
                                    "maxLength": 1000,
                                    "description": "测试场景描述"
                                },
                                "inputs": {
                                    "type": "object",
                                    "description": "输入信号值"
                                },
                                "expected_outputs": {
                                    "type": "object",
                                    "description": "期望的输出值"
                                }
                            },
                            "required": ["name", "description"],
                            "additionalProperties": False
                        },
                        "maxItems": 50,
                        "description": "测试场景定义列表"
                    },
                    "clock_period": {
                        "type": "number",
                        "minimum": 0.1,
                        "maximum": 1000.0,
                        "default": 10.0,
                        "description": "时钟周期(ns)"
                    },
                    "simulation_time": {
                        "type": "integer",
                        "minimum": 100,
                        "maximum": 1000000,
                        "default": 10000,
                        "description": "仿真时间(时钟周期数)"
                    },
                    "coverage_options": {
                        "type": "object",
                        "properties": {
                            "enable_coverage": {
                                "type": "boolean",
                                "default": False,
                                "description": "是否启用覆盖率收集"
                            },
                            "coverage_type": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["line", "toggle", "branch", "condition"]
                                },
                                "default": ["line", "toggle"],
                                "description": "覆盖率类型"
                            }
                        },
                        "additionalProperties": False,
                        "description": "覆盖率选项配置"
                    }
                },
                "required": ["module_name", "module_code"],
                "additionalProperties": False
            }
        )
        
        # 2. 仿真执行工具
        self.register_enhanced_tool(
            name="run_simulation",
            func=self._tool_run_simulation,
            description="使用专业工具运行Verilog仿真和验证",
            security_level="high",
            category="verification",
            schema={
                "type": "object",
                "properties": {
                    "module_file": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-:\\\\]+\.v$",
                        "maxLength": 500,
                        "description": "模块文件路径，必须以.v结尾，支持Windows和Unix路径"
                    },
                    "testbench_file": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-:\\\\]+\.v$",
                        "maxLength": 500,
                        "description": "测试台文件路径，必须以.v结尾，支持Windows和Unix路径"
                    },
                    "module_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "模块代码内容(如果不提供文件路径)"
                    },
                    "testbench_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "测试台代码内容(如果不提供文件路径)"
                    },
                    "simulator": {
                        "type": "string",
                        "enum": ["iverilog", "modelsim", "vivado", "auto"],
                        "default": "iverilog",
                        "description": "仿真器选择"
                    },
                    "simulation_options": {
                        "type": "object",
                        "properties": {
                            "timescale": {
                                "type": "string",
                                "pattern": r"^\d+[a-z]+/\d+[a-z]+$",
                                "default": "1ns/1ps",
                                "description": "时间精度设置"
                            },
                            "dump_waves": {
                                "type": "boolean",
                                "default": True,
                                "description": "是否生成波形文件"
                            },
                            "max_sim_time": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 10000000,
                                "default": 100000,
                                "description": "最大仿真时间(时间单位)"
                            }
                        },
                        "additionalProperties": False,
                        "description": "仿真选项配置"
                    }
                },
                "anyOf": [
                    {"required": ["module_file", "testbench_file"]},
                    {"required": ["module_code", "testbench_code"]}
                ],
                "additionalProperties": False
            }
        )
        
        # 3. 外部testbench使用工具
        self.register_enhanced_tool(
            name="use_external_testbench",
            func=self._tool_use_external_testbench,
            description="使用外部提供的testbench文件进行测试验证",
            security_level="high",
            category="verification",
            schema={
                "type": "object",
                "properties": {
                    "design_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "需要测试的Verilog设计代码"
                    },
                    "external_testbench_path": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-:\\\\]+\.v$",
                        "maxLength": 500,
                        "description": "外部testbench文件路径，必须以.v结尾"
                    },
                    "design_module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "设计模块名称，必须以字母开头"
                    },
                    "simulator": {
                        "type": "string",
                        "enum": ["iverilog", "modelsim", "vivado", "auto"],
                        "default": "iverilog",
                        "description": "仿真器选择"
                    },
                    "simulation_options": {
                        "type": "object",
                        "properties": {
                            "timescale": {
                                "type": "string",
                                "pattern": r"^\d+[a-z]+/\d+[a-z]+$",
                                "default": "1ns/1ps",
                                "description": "时间精度设置"
                            },
                            "dump_waves": {
                                "type": "boolean",
                                "default": True,
                                "description": "是否生成波形文件"
                            },
                            "max_sim_time": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 10000000,
                                "default": 100000,
                                "description": "最大仿真时间(时间单位)"
                            }
                        },
                        "additionalProperties": False,
                        "description": "仿真选项配置"
                    }
                },
                "required": ["design_code", "external_testbench_path", "design_module_name"],
                "additionalProperties": False
            }
        )

        
        # 4. 构建脚本生成工具
        self.register_enhanced_tool(
            name="generate_build_script",
            func=self._tool_generate_build_script,
            description="生成专业的构建脚本(Makefile或shell脚本)",
            security_level="high",
            category="build_automation",
            schema={
                "type": "object",
                "properties": {
                    "verilog_files": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z0-9_./\-]+\.v$",
                            "maxLength": 500
                        },
                        "minItems": 1,
                        "maxItems": 100,
                        "description": "Verilog源文件列表"
                    },
                    "testbench_files": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z0-9_./\-]+\.v$",
                            "maxLength": 500
                        },
                        "minItems": 1,
                        "maxItems": 100,
                        "description": "测试台文件列表"
                    },
                    "script_type": {
                        "type": "string",
                        "enum": ["makefile", "bash", "tcl", "python"],
                        "default": "makefile",
                        "description": "脚本类型选择"
                    },
                    "target_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_\-]*$",
                        "minLength": 1,
                        "maxLength": 50,
                        "default": "simulation",
                        "description": "构建目标名称"
                    },
                    "build_options": {
                        "type": "object",
                        "properties": {
                            "simulator": {
                                "type": "string",
                                "enum": ["iverilog", "modelsim", "vivado", "verilator"],
                                "default": "iverilog",
                                "description": "目标仿真器"
                            },
                            "optimization_level": {
                                "type": "string",
                                "enum": ["none", "basic", "aggressive"],
                                "default": "basic",
                                "description": "优化级别"
                            },
                            "include_dirs": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "pattern": r"^[a-zA-Z0-9_./\-]+$",
                                    "maxLength": 500
                                },
                                "maxItems": 20,
                                "description": "包含目录列表"
                            },
                            "defines": {
                                "type": "object",
                                "patternProperties": {
                                    "^[A-Z][A-Z0-9_]*$": {
                                        "type": "string",
                                        "maxLength": 100
                                    }
                                },
                                "maxProperties": 50,
                                "description": "预定义宏"
                            }
                        },
                        "additionalProperties": False,
                        "description": "构建选项配置"
                    }
                },
                "required": ["verilog_files", "testbench_files"],
                "additionalProperties": False
            }
        )
        
        # 5. 脚本执行工具
        self.register_enhanced_tool(
            name="execute_build_script",
            func=self._tool_execute_build_script,
            description="安全执行构建脚本进行编译和仿真",
            security_level="high",
            category="build_automation",
            schema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_.\-]+$",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "脚本文件名，只允许安全字符"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["all", "compile", "simulate", "clean", "test", "lint"],
                        "default": "all",
                        "description": "执行的动作类型"
                    },
                    "arguments": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z0-9_=.\-/]+$",
                            "maxLength": 200
                        },
                        "maxItems": 20,
                        "description": "安全的命令行参数，过滤危险字符"
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 10,
                        "maximum": 3600,
                        "default": 300,
                        "description": "执行超时时间(秒)"
                    },
                    "working_directory": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-]+$",
                        "maxLength": 500,
                        "description": "工作目录路径"
                    }
                },
                "required": ["script_name"],
                "additionalProperties": False
            }
        )
        

        
        # 7. 测试失败分析工具 - 专门用于分析TDD循环中的失败模式
        self.register_enhanced_tool(
            name="analyze_test_failures",
            func=self._tool_analyze_test_failures,
            description="分析测试失败原因并提供具体修复建议",
            security_level="normal",
            category="debugging",
            schema={
                "type": "object",
                "properties": {
                    "compilation_errors": {
                        "type": "string",
                        "maxLength": 5000,
                        "description": "编译错误输出信息"
                    },
                    "simulation_errors": {
                        "type": "string",
                        "maxLength": 5000,
                        "description": "仿真错误输出信息"
                    },
                    "test_assertions": {
                        "type": "string",
                        "maxLength": 5000,
                        "description": "测试断言失败信息"
                    },
                    "design_code": {
                        "type": "string",
                        "maxLength": 10000,
                        "description": "需要分析的设计代码"
                    },
                    "testbench_code": {
                        "type": "string",
                        "maxLength": 10000,
                        "description": "测试台代码"
                    },
                    "testbench_file": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "测试台文件路径（用于自动修复）"
                    },
                    "iteration_number": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "当前TDD迭代次数"
                    },
                    "previous_fixes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "maxLength": 500
                        },
                        "maxItems": 10,
                        "description": "之前尝试的修复方法列表"
                    }
                },
                "required": ["design_code"],
                "additionalProperties": False
            }
        )
        
        # 7. 工具使用指导工具
        self.register_enhanced_tool(
            name="get_tool_usage_guide",
            func=self._tool_get_tool_usage_guide,
            description="获取EnhancedRealCodeReviewAgent的工具使用指导，包括可用工具、参数说明、调用示例和最佳实践。",
            security_level="normal",
            category="help",
            schema={
                "type": "object",
                "properties": {
                    "include_examples": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含调用示例"
                    },
                    "include_best_practices": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含最佳实践"
                    }
                },
                "additionalProperties": False
            }
        )
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """使用统一的LLM通信管理器进行Function Calling调用"""
        return await self.llm_manager.call_llm_for_function_calling(
            conversation, 
            system_prompt_builder=self._build_system_prompt
        )
    
    async def _call_llm_optimized_with_history(self, user_request: str, 
                                             conversation_history: List[Dict[str, str]], 
                                             is_first_call: bool = False) -> str:
        """重写父类方法，使用统一的LLM通信管理器"""
        try:
            # 构建对话历史
            conversation = []
            
            # 添加系统提示（仅在第一次调用时）
            if is_first_call:
                conversation.append({
                    "role": "system", 
                    "content": await self._build_system_prompt()
                })
            
            # 添加历史对话
            if conversation_history and not is_first_call:
                # 添加最近的对话历史作为上下文
                recent_history = conversation_history[-6:]  # 保留最近3轮对话
                for entry in recent_history:
                    if entry.get("role") in ["user", "assistant"]:
                        conversation.append({
                            "role": entry["role"],
                            "content": entry["content"]
                        })
            
            # 添加当前用户请求
            conversation.append({
                "role": "user",
                "content": user_request
            })
            
            # 使用统一的LLM管理器进行调用
            response = await self.llm_manager.call_llm_for_function_calling(
                conversation,
                system_prompt_builder=self._build_system_prompt
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ 优化LLM调用失败: {str(e)}")
            raise
    
    async def _build_system_prompt(self) -> str:
        """使用统一的System Prompt构建器"""
        return await self.prompt_builder.build_system_prompt(
            role="code_reviewer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id=self.agent_id,
            capabilities=self._capabilities
        )
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力"""
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.QUALITY_ANALYSIS,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.VERIFICATION
        }
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "集成Schema验证的增强代码审查智能体，提供严格参数验证和智能错误修复的专业代码审查服务"
    
    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """获取注册的工具列表"""
        return self.enhanced_tools
    
    def _extract_module_name_from_code(self, verilog_code: str) -> str:
        """从Verilog代码中提取模块名"""
        import re
        
        # 匹配module声明
        module_pattern = r'module\s+(\w+)\s*\('
        match = re.search(module_pattern, verilog_code, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # 如果没有找到，返回默认名称
        return "unknown_module"
    
    def _validate_and_fix_module_name(self, provided_name: str, verilog_code: str) -> str:
        """验证并修复模块名"""
        extracted_name = self._extract_module_name_from_code(verilog_code)
        
        if provided_name and provided_name != extracted_name:
            self.logger.warning(f"⚠️ 模块名不匹配: 提供={provided_name}, 提取={extracted_name}")
            return extracted_name
        
        return provided_name or extracted_name
    
    def _identify_top_module(self, files_to_compile: List[Path]) -> str:
        """识别顶层模块"""
        try:
            # 优先查找testbench文件作为顶层模块
            for file_path in files_to_compile:
                file_name = file_path.name.lower()
                if any(keyword in file_name for keyword in ['testbench', 'tb_', '_tb', 'test_']):
                    module_name = self._extract_module_name_from_file(file_path)
                    if module_name:
                        self.logger.info(f"🔍 识别到顶层模块（testbench）: {module_name}")
                        return module_name
            
            # 如果没有找到testbench，查找第一个有效的模块
            for file_path in files_to_compile:
                module_name = self._extract_module_name_from_file(file_path)
                if module_name:
                    self.logger.info(f"🔍 识别到顶层模块: {module_name}")
                    return module_name
            
            self.logger.warning("⚠️ 无法识别顶层模块")
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️ 顶层模块识别失败: {e}")
            return None
    
    def _extract_module_name_from_file(self, file_path: Path) -> str:
        """从文件中提取模块名"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return self._extract_module_name_from_code(content)
        except Exception as e:
            self.logger.warning(f"⚠️ 从文件 {file_path} 提取模块名失败: {e}")
            return None
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的System Prompt（向后兼容方法）"""
        # 为向后兼容而保留，直接调用统一的构建方法
        import asyncio
        try:
            return asyncio.run(self._build_system_prompt())
        except Exception as e:
            self.logger.warning(f"统一System Prompt构建失败，使用简化版本: {e}")
            return """你是一位专业的硬件验证和代码审查专家，专注于Verilog/SystemVerilog代码质量分析、测试台设计和仿真验证。
请使用提供的工具进行代码审查和功能验证，确保代码质量和功能正确性。"""
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强的代码审查和验证任务"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行增强代码审查任务: {task_id}")
        
        try:
            # 🔧 新增：检查并设置实验路径
            experiment_path = None
            
            # 1. 从任务上下文获取实验路径
            if hasattr(self, 'current_task_context') and self.current_task_context:
                if hasattr(self.current_task_context, 'experiment_path') and self.current_task_context.experiment_path:
                    experiment_path = self.current_task_context.experiment_path
                    self.logger.info(f"🧪 从任务上下文获取实验路径: {experiment_path}")
            
            # 2. 如果没有找到，尝试从实验管理器获取
            if not experiment_path:
                try:
                    from core.experiment_manager import get_experiment_manager
                    exp_manager = get_experiment_manager()
                    
                    if exp_manager and exp_manager.current_experiment_path:
                        experiment_path = exp_manager.current_experiment_path
                        self.logger.info(f"🧪 从实验管理器获取实验路径: {experiment_path}")
                except (ImportError, Exception) as e:
                    self.logger.debug(f"实验管理器不可用: {e}")
            
            # 3. 如果还是没有找到，使用默认路径
            if not experiment_path:
                experiment_path = "./file_workspace"
                self.logger.warning(f"⚠️ 没有找到实验路径，使用默认路径: {experiment_path}")
            
            # 设置实验路径到任务上下文
            if hasattr(self, 'current_task_context') and self.current_task_context:
                self.current_task_context.experiment_path = experiment_path
                self.logger.info(f"✅ 设置任务实验路径: {experiment_path}")
            
            # 🔧 新增：提取设计文件路径
            design_file_path = None
            
            # 1. 从任务上下文获取设计文件路径
            if hasattr(self, 'current_task_context') and self.current_task_context:
                if hasattr(self.current_task_context, 'design_file_path') and self.current_task_context.design_file_path:
                    design_file_path = self.current_task_context.design_file_path
                    self.logger.info(f"📁 从任务上下文获取设计文件路径: {design_file_path}")
            
            # 2. 如果没有找到，从任务描述中提取
            if not design_file_path:
                design_file_path = self._extract_design_file_path_from_task(enhanced_prompt)
                if design_file_path:
                    self.logger.info(f"📁 从任务描述中提取设计文件路径: {design_file_path}")
            
            # 3. 如果还是没有找到，尝试从文件内容中查找
            if not design_file_path and file_contents:
                for file_id, file_info in file_contents.items():
                    if file_info.get("file_type") == "verilog" or file_info.get("file_path", "").endswith(".v"):
                        design_file_path = file_info.get("file_path")
                        self.logger.info(f"📁 从文件内容中获取设计文件路径: {design_file_path}")
                        break
            
            # 设置设计文件路径到任务上下文
            if design_file_path and hasattr(self, 'current_task_context') and self.current_task_context:
                self.current_task_context.design_file_path = design_file_path
                self.logger.info(f"✅ 设置设计文件路径: {design_file_path}")
            
            # 使用增强验证处理流程
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=6
            )
            
            if result["success"]:
                self.logger.info(f"✅ 代码审查任务完成: {task_id}")
                
                # 提取生成的文件路径信息
                generated_files = self._extract_generated_files_from_tool_results(result.get("tool_results", []))
                
                # 🔧 新增：更新文件路径为实验路径
                for file_info in generated_files:
                    if file_info.get("file_path") and experiment_path:
                        # 如果文件路径是相对路径，更新为实验路径下的绝对路径
                        if not file_info["file_path"].startswith("/"):
                            file_info["file_path"] = f"{experiment_path}/{file_info['file_path']}"
                            self.logger.info(f"📁 更新文件路径: {file_info['file_path']}")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "response": result.get("response", ""),
                    "tool_results": result.get("tool_results", []),
                    "iterations": result.get("iterations", 1),
                    "generated_files": generated_files,
                    "experiment_path": experiment_path,  # 🔧 新增：返回实验路径
                    "design_file_path": design_file_path,  # 🔧 新增：返回设计文件路径
                    "quality_metrics": {
                        "schema_validation_passed": True,
                        "parameter_errors_fixed": result.get("iterations", 1) > 1,
                        "security_checks_passed": True,
                        "verification_type": result.get("verification_type", "unknown"),
                        "test_coverage_score": result.get("test_coverage_score", 0.0)
                    }
                }
            else:
                self.logger.error(f"❌ 代码审查任务失败: {task_id} - {result.get('error')}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "iterations": result.get("iterations", 1),
                    "last_error": result.get("last_error", ""),
                    "suggestions": result.get("suggestions", []),
                    "experiment_path": experiment_path,  # 🔧 新增：返回实验路径
                    "design_file_path": design_file_path  # 🔧 新增：返回设计文件路径
                }
                
        except Exception as e:
            self.logger.error(f"❌ 代码审查任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}",
                "suggestions": [
                    "检查输入参数格式是否正确",
                    "确认设计文件路径是否正确",
                    "验证工具配置是否正确"
                ],
                "experiment_path": experiment_path if 'experiment_path' in locals() else None,  # 🔧 新增：返回实验路径
                "design_file_path": design_file_path if 'design_file_path' in locals() else None  # 🔧 新增：返回设计文件路径
            }
    
    # =============================================================================
    # 新增：文件路径提取和管理
    # =============================================================================
    
    def _extract_generated_files_from_tool_results(self, tool_results: List[Dict]) -> List[Dict]:
        """从工具结果中提取生成的文件路径信息"""
        generated_files = []
        
        for tool_result in tool_results:
            if not isinstance(tool_result, dict):
                continue
                
            tool_name = tool_result.get("tool_name", "")
            result_data = tool_result.get("result", {})
            
            # 检查write_file工具的结果
            if tool_name == "write_file" and isinstance(result_data, dict):
                if result_data.get("success", False):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "testbench_code",
                        "description": result_data.get("description", ""),
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
            
            # 检查generate_testbench工具的结果
            elif tool_name == "generate_testbench" and isinstance(result_data, dict):
                if result_data.get("success", False) and result_data.get("file_path"):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "testbench",
                        "module_name": result_data.get("module_name", ""),
                        "description": f"Generated testbench for: {result_data.get('module_name', '')}",
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
            
            # 检查run_simulation工具的结果
            elif tool_name == "run_simulation" and isinstance(result_data, dict):
                if result_data.get("success", False):
                    # 仿真可能生成波形文件
                    waveform_file = result_data.get("waveform_file", "")
                    if waveform_file:
                        file_info = {
                            "file_path": waveform_file,
                            "file_type": "waveform",
                            "description": "Simulation waveform file",
                            "tool_name": tool_name
                        }
                        generated_files.append(file_info)
            
            # 检查generate_build_script工具的结果
            elif tool_name == "generate_build_script" and isinstance(result_data, dict):
                if result_data.get("success", False) and result_data.get("file_path"):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "build_script",
                        "script_type": result_data.get("script_type", ""),
                        "description": f"Build script: {result_data.get('script_type', '')}",
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
        
        self.logger.info(f"📁 提取到 {len(generated_files)} 个生成文件")
        for file_info in generated_files:
            self.logger.info(f"📄 生成文件: {file_info.get('file_path', '')} - {file_info.get('description', '')}")
        
        return generated_files
    
    # =============================================================================
    # 工具实现方法
    # =============================================================================
    
    async def _tool_generate_testbench(self, module_name: str = None, module_code: str = None, 
                                     code: str = None, verilog_code: str = None, 
                                     test_scenarios: List[Dict] = None,
                                     clock_period: float = 10.0,
                                     simulation_time: int = 10000,
                                     coverage_options: Dict = None, **kwargs) -> Dict[str, Any]:
        """生成测试台 - 增强版本，确保使用缓存的文件内容"""
        
        try:
            # 🧠 新增：优先使用缓存的文件内容
            cached_files = self.agent_state_cache.get("last_read_files", {})
            if not module_code and not code and not verilog_code:
                # 从缓存中查找Verilog文件
                for filepath, file_info in cached_files.items():
                    if file_info.get("file_type") in ["verilog", "systemverilog"]:
                        module_code = file_info["content"]
                        self.logger.info(f"🧠 使用缓存的文件内容生成测试台: {filepath} ({len(module_code)} 字符)")
                        break
            
            # 如果没有缓存内容，使用传入的参数
            if not module_code:
                module_code = code or verilog_code
            
            # 🔧 新增：从实例变量中获取 file_contents（如果存在）
            if not module_code:
                file_contents = getattr(self, '_current_file_contents', None)
                if file_contents and "design_file" in file_contents:
                    design_file_info = file_contents["design_file"]
                    if design_file_info.get("content"):
                        module_code = design_file_info["content"]
                        self.logger.info(f"📁 使用传递的设计文件内容，长度: {len(module_code)} 字符")
                    else:
                        self.logger.warning("⚠️ file_contents 中的 design_file 没有内容")
            
            # 如果没有模块代码，报错
            if not module_code:
                return {
                    "success": False,
                    "error": "缺少模块代码，无法生成测试台"
                }
            
            # 验证并修复模块名
            actual_module_name = self._validate_and_fix_module_name(module_name, module_code)
            if actual_module_name != module_name:
                self.logger.info(f"🔧 模块名已修正: {module_name} -> {actual_module_name}")
                module_name = actual_module_name
            
            self.logger.info(f"🧪 生成测试台: {module_name}")

            test_scenarios = test_scenarios or [
                {"name": "basic_test", "description": "基础功能测试"}
            ]
            coverage_options = coverage_options or {"enable_coverage": False}
            
            # 构建测试台生成提示
            scenarios_desc = "\n".join([
                f"- {s['name']}: {s['description']}" 
                for s in test_scenarios
            ])
            
            testbench_prompt = f"""
请为以下Verilog模块生成一个完整、专业的测试台：

目标模块: {module_name}
```verilog
{module_code}
```

测试要求:
- 时钟周期: {clock_period}ns
- 仿真时间: {simulation_time} 个时钟周期
- 覆盖率收集: {'启用' if coverage_options.get('enable_coverage') else '禁用'}

测试场景:
{scenarios_desc}

**重要要求**：
1. 使用标准Verilog语法，不要使用SystemVerilog特性
2. 避免使用task/function中的多语句结构
3. 使用标准的for循环语法
4. 确保所有语句都有正确的分号
5. 使用标准的begin/end块结构

**测试结果统计要求**：
1. 必须统计通过的测试用例数量（passed_count）
2. 必须统计失败的测试用例数量（failed_count）
3. 必须统计总测试用例数量（total_count）
4. 在每个测试用例执行后，输出明确的PASS/FAIL状态
5. 在测试结束时，输出详细的统计信息
6. 如果所有测试都通过（failed_count = 0），必须输出"All passed!"消息

请生成包含以下内容的专业测试台：
1. 完整的testbench模块声明
2. 所有必要的信号声明（包括计数器信号）
3. 时钟和复位生成逻辑
4. 被测模块的正确实例化
5. 系统化的测试激励生成
6. 结果检查和断言
7. 测试计数器变量声明（passed_count, failed_count, total_count）
8. 每个测试用例的状态输出格式：
   ```
   $display("Time=%0t: Test Case %0d - %s", $time, test_number, test_name);
   $display("Expected: %h, Got: %h, Status: %s", expected_value, actual_value, status);
   ```
9. 测试结束时的统计输出格式：
   ```
   $display("==================================================");
   $display("Test Summary:");
   $display("Total Tests: %0d", total_count);
   $display("Passed: %0d", passed_count);
   $display("Failed: %0d", failed_count);
   $display("==================================================");
   if (failed_count == 0) begin
       $display("All passed!");
   end
   $display("==================================================");
   ```
10. 适当的$display、$monitor和$finish语句
11. 波形转储设置（VCD文件）

确保测试台能够充分验证模块的所有功能，使用标准Verilog语法，并提供清晰的测试结果统计。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=testbench_prompt,
                system_prompt="你是专业的验证工程师，请生成高质量的Verilog测试台。",
                temperature=0.1
            )
            
            # 首先保存设计代码（如果提供了module_code）
            design_filename = f"{module_name}.v"
            design_saved = False
            
            if module_code and module_code.strip():
                design_write_result = await self._tool_write_file(
                    filename=design_filename,
                    content=module_code,
                    description=f"生成的{module_name}模块设计代码"
                )
                design_saved = design_write_result.get("success", False)
                if design_saved:
                    self.logger.info(f"✅ 设计代码已保存: {design_filename}")
                else:
                    self.logger.warning(f"⚠️ 设计代码保存失败: {design_write_result.get('error', 'Unknown error')}")
            
            # 使用Function Calling write_file工具保存测试台
            # 统一命名规范：testbench_{module_name}.v
            tb_filename = f"testbench_{module_name}.v"
            
            # 验证生成的测试台语法
            if not await self._validate_verilog_file_content(response):
                self.logger.warning(f"⚠️ 生成的测试台可能存在语法问题，尝试修复...")
                response = await self._fix_testbench_syntax(response, module_name)
            
            write_result = await self._tool_write_file(
                filename=tb_filename,
                content=response,
                description=f"生成的{module_name}模块测试台"
            )
            
            if not write_result.get("success", False):
                return {
                    "success": False,
                    "error": f"测试台保存失败: {write_result.get('error', 'Unknown error')}",
                    "testbench_code": response
                }
            
            # 返回成功结果
            return {
                "success": True,
                "message": f"✅ 成功生成测试台: {tb_filename}",
                "module_name": module_name,
                "file_path": str(self.artifacts_dir / tb_filename),
                "file_id": write_result.get("file_id", ""),
                "testbench_code": response,
                "design_saved": design_saved,
                "design_file_path": str(self.artifacts_dir / design_filename) if design_saved else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试台生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"测试台生成异常: {str(e)}",
                "testbench_code": ""
            }
    
    async def _tool_use_external_testbench(self, design_code: str, external_testbench_path: str,
                                          design_module_name: str, simulator: str = "iverilog",
                                          simulation_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用外部testbench进行测试验证"""
        try:
            self.logger.info(f"🔍 使用外部testbench验证设计: {design_module_name}")
            
            # 设置默认仿真选项
            if simulation_options is None:
                simulation_options = {
                    "timescale": "1ns/1ps",
                    "dump_waves": True,
                    "max_sim_time": 100000
                }
            
            # 检查外部testbench文件是否存在
            testbench_path = Path(external_testbench_path)
            if not testbench_path.exists():
                return {
                    "success": False,
                    "error": f"外部testbench文件不存在: {external_testbench_path}",
                    "stage": "validation"
                }
            
            # 读取外部testbench内容
            try:
                with open(testbench_path, 'r', encoding='utf-8') as f:
                    testbench_code = f.read()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"读取外部testbench失败: {str(e)}",
                    "stage": "file_reading"
                }
            
            # 创建临时设计文件
            design_filename = f"{design_module_name}.v"
            design_file_path = self.artifacts_dir / design_filename
            
            try:
                with open(design_file_path, 'w', encoding='utf-8') as f:
                    f.write(design_code)
                
                self.logger.info(f"✅ 设计文件已创建: {design_file_path}")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"创建设计文件失败: {str(e)}",
                    "stage": "file_creation"
                }
            
            # 使用run_simulation工具进行仿真
            result = await self._tool_run_simulation(
                module_file=str(design_file_path),
                testbench_file=external_testbench_path,
                simulator=simulator,
                simulation_options=simulation_options
            )
            
            # 增强结果信息
            if result.get("success"):
                result["external_testbench_used"] = external_testbench_path
                result["message"] = f"✅ 使用外部testbench成功验证设计模块 {design_module_name}"
                self.logger.info(f"✅ 外部testbench验证成功: {design_module_name}")
            else:
                result["external_testbench_used"] = external_testbench_path
                result["message"] = f"❌ 使用外部testbench验证失败: {result.get('error', '未知错误')}"
                self.logger.warning(f"❌ 外部testbench验证失败: {design_module_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 外部testbench使用异常: {str(e)}")
            return {
                "success": False,
                "error": f"外部testbench使用异常: {str(e)}",
                "stage": "exception"
            }

    async def _tool_run_simulation(self, module_file: str = None, testbench_file: str = None,
                                 module_code: str = None, testbench_code: str = None,
                                 simulator: str = "iverilog",
                                 simulation_options: Dict = None,
                                 files: List = None, command: str = None,
                                 **kwargs) -> Dict[str, Any]:
        """运行仿真工具实现 - 集成智能依赖分析和参数处理"""
        self.logger.info(f"🔍 运行仿真: {module_file} {testbench_file} {module_code} {testbench_code} {simulator} {simulation_options}")
        try:
            self.logger.info(f"🔬 运行仿真: {simulator}")
            simulation_options = simulation_options or {}
            
            # 🧠 智能参数处理策略
            # 1. 优先使用文件路径参数
            # 2. 如果文件路径失败，自动切换到代码内容参数
            # 3. 如果代码内容也没有，尝试从文件管理器获取
            
            files_to_compile = []
            use_file_paths = True
            
            # 检查文件路径参数是否有效
            if module_file and testbench_file:
                # 验证文件路径格式（支持Windows和Unix路径）
                import re
                path_pattern = r'^[a-zA-Z0-9_./\-:\\\\]+\.v$'
                
                if not re.match(path_pattern, module_file) or not re.match(path_pattern, testbench_file):
                    self.logger.warning(f"⚠️ 文件路径格式不符合要求，切换到代码内容模式")
                    self.logger.warning(f"   模块文件路径: {module_file}")
                    self.logger.warning(f"   测试台文件路径: {testbench_file}")
                    use_file_paths = False
                    
                    # 尝试从文件管理器获取代码内容
                    if not module_code or not testbench_code:
                        try:
                            from core.file_manager import get_file_manager
                            file_manager = get_file_manager()
                            
                            # 尝试获取模块代码
                            if not module_code:
                                design_files = file_manager.get_files_by_type("design")
                                for file_ref in design_files:
                                    if "alu" in file_ref.file_path.lower():
                                        module_code = file_ref.content
                                        self.logger.info(f"📄 从文件管理器获取模块代码: {file_ref.file_path}")
                                        break
                            
                            # 尝试获取测试台代码
                            if not testbench_code:
                                testbench_files = file_manager.get_files_by_type("testbench")
                                for file_ref in testbench_files:
                                    if "alu" in file_ref.file_path.lower():
                                        testbench_code = file_ref.content
                                        self.logger.info(f"📄 从文件管理器获取测试台代码: {file_ref.file_path}")
                                        break
                                        
                        except Exception as e:
                            self.logger.warning(f"⚠️ 从文件管理器获取代码失败: {str(e)}")
            
            if use_file_paths and module_file and testbench_file:
                mod_file = Path(module_file)
                tb_file = Path(testbench_file)
                
                # 智能文件搜索和验证
                # 首先尝试直接路径
                if not mod_file.exists():
                    # 搜索多个可能的路径
                    search_paths = [
                        Path(module_file),
                        Path("file_workspace/designs") / module_file,
                        Path("file_workspace") / module_file,
                        Path.cwd() / "file_workspace/designs" / module_file,
                        Path.cwd() / "file_workspace" / module_file,
                    ]
                    
                    mod_file_found = False
                    for path in search_paths:
                        if path.exists():
                            mod_file = path
                            mod_file_found = True
                            self.logger.info(f"📁 找到模块文件: {mod_file}")
                            break
                    
                    if not mod_file_found:
                        return {
                            "success": False,
                            "error": f"模块文件不存在: {module_file}，已搜索路径: {[str(p) for p in search_paths]}",
                            "stage": "file_validation"
                        }
                
                if not tb_file.exists():
                    # 智能文件搜索 - 支持多种命名格式，优先新格式
                    module_name = Path(module_file).stem  # 获取模块名（不含扩展名）
                    
                    # 生成可能的测试台文件名（按优先级排序）
                    possible_tb_names = [
                        f"testbench_{module_name}.v",  # 新格式：testbench_module.v（最高优先级）
                        f"{module_name}_tb.v",  # 标准格式：module_tb.v
                        f"{module_name}_testbench.v",  # 后缀格式：module_testbench.v
                        f"tb_{module_name}.v",  # 短前缀格式：tb_module.v
                        testbench_file,  # 原始文件名（最低优先级）
                    ]
                    
                    # 搜索多个可能的路径
                    search_paths = []
                    for tb_name in possible_tb_names:
                        search_paths.extend([
                            Path(tb_name),
                            Path("file_workspace/testbenches") / tb_name,
                            Path("file_workspace") / tb_name,
                            Path.cwd() / "file_workspace/testbenches" / tb_name,
                            Path.cwd() / "file_workspace" / tb_name,
                        ])
                    
                    tb_file_found = False
                    for path in search_paths:
                        if path.exists():
                            # 验证文件语法（简单检查）
                            if await self._validate_verilog_file(path):
                                tb_file = path
                                tb_file_found = True
                                self.logger.info(f"📁 找到有效测试台文件: {tb_file}")
                                break
                            else:
                                self.logger.warning(f"⚠️ 跳过语法错误的文件: {path}")
                    
                    if not tb_file_found:
                        # 如果找不到文件，尝试从文件管理器获取最新生成的文件
                        try:
                            from core.file_manager import get_file_manager
                            file_manager = get_file_manager()
                            testbench_files = file_manager.get_files_by_type("testbench")
                            
                            # 查找匹配模块名的测试台文件
                            for file_ref in testbench_files:
                                filename = Path(file_ref.file_path).stem
                                if module_name.lower() in filename.lower():
                                    if await self._validate_verilog_file(Path(file_ref.file_path)):
                                        tb_file = Path(file_ref.file_path)
                                        tb_file_found = True
                                        self.logger.info(f"📁 从文件管理器找到测试台文件: {tb_file}")
                                        break
                        except Exception as e:
                            self.logger.warning(f"⚠️ 从文件管理器查找文件失败: {str(e)}")
                    
                    if not tb_file_found:
                        return {
                            "success": False,
                            "error": f"测试台文件不存在或语法错误: {testbench_file}，已搜索路径: {[str(p) for p in search_paths[:10]]}...",
                            "stage": "file_validation"
                        }
                
                # 🔍 应用智能依赖分析
                try:
                    from extensions.verilog_dependency_analyzer import VerilogDependencyAnalyzer
                    dep_analyzer = VerilogDependencyAnalyzer()
                    
                    # 分析依赖关系
                    dep_analyzer.analyze_file(str(mod_file))
                    dep_analyzer.analyze_file(str(tb_file))
                    
                    # 从文件管理器查找缺失依赖
                    missing_deps = []
                    for module in dep_analyzer.modules.values():
                        for dep in module.dependencies:
                            if dep not in dep_analyzer.modules:
                                missing_deps.append(dep)
                    
                    if missing_deps:
                        self.logger.info(f"🔍 发现缺失依赖: {missing_deps}")
                        additional_files = await self._find_missing_dependencies(missing_deps)
                        
                        for add_file in additional_files:
                            dep_analyzer.analyze_file(add_file)
                            files_to_compile.append(Path(add_file))
                            self.logger.info(f"✅ 添加依赖文件: {Path(add_file).name}")
                    
                    # 生成编译顺序
                    target_modules = [m.name for m in dep_analyzer.modules.values() if m.is_testbench]
                    if target_modules:
                        ordered_files, missing = dep_analyzer.resolve_dependencies(target_modules)
                        if ordered_files:
                            files_to_compile = [Path(f) for f in ordered_files]
                        else:
                            files_to_compile = [mod_file, tb_file]
                    else:
                        files_to_compile = [mod_file, tb_file]
                        
                except Exception as dep_e:
                    self.logger.warning(f"⚠️ 依赖分析失败，使用默认文件列表: {str(dep_e)}")
                    files_to_compile = [mod_file, tb_file]
                    
            else:
                # 创建临时文件
                mod_file = self.artifacts_dir / "temp_module.v" 
                tb_file = self.artifacts_dir / "temp_testbench.v"
                
                with open(mod_file, 'w') as f:
                    f.write(module_code or "")
                with open(tb_file, 'w') as f:
                    f.write(testbench_code or "")
                
                files_to_compile = [mod_file, tb_file]
            
            # 使用智能仿真执行
            sim_result = await self._run_iverilog_simulation_with_deps(files_to_compile, simulation_options)
            self.logger.info(f"🔍 仿真结果: {sim_result}")
            
            # ✅ 修复错误处理 - 准确反映仿真状态
            actual_success = sim_result.get("success", False)
            
            if actual_success:
                self.logger.info(f"✅ 仿真执行成功")
                return {
                    "success": actual_success,
                    "simulator": simulator,
                    "simulation_output": sim_result.get("output", ""),
                    "compilation_output": sim_result.get("compilation_output", ""),
                    "waveform_file": sim_result.get("waveform_file"),
                    "simulation_time": sim_result.get("simulation_time", 0),
                    "errors": sim_result.get("errors", []),
                    "warnings": sim_result.get("warnings", []),
                    "stage": sim_result.get("stage", "complete"),
                    "files_compiled": [str(f) for f in files_to_compile],
                    "dependency_analysis": sim_result.get("dependency_analysis", {}),
                    "error_message": "",
                    "compilation_errors": "",
                    "simulation_errors": ""
                }
            else:
                # 🚨 新的错误处理机制
                error_message = sim_result.get("error", "未知错误")
                stage = sim_result.get("stage", "unknown")
                self.logger.error(f"❌ 仿真执行失败 ({stage}): {error_message}")
                
                # 1. 错误分类处理
                error_context = {
                    "file_paths": [str(f) for f in files_to_compile],
                    "stage": stage,
                    "simulator": simulator,
                    "command": sim_result.get("command", ""),
                    "timestamp": str(time.time()),
                    "working_directory": str(Path.cwd())
                }
                
                enhanced_error = self._enhance_error_information(
                    error_message=error_message,
                    error_context=error_context,
                    simulation_result=sim_result
                )
                
                # 2. 记录增强的错误信息
                self.logger.info(f"🔍 错误分类: {enhanced_error['error_classification']['error_type']}")
                self.logger.info(f"🔍 错误严重程度: {enhanced_error['error_classification']['severity']}")
                self.logger.info(f"🔍 修复优先级: {enhanced_error['error_classification']['fix_priority']}")
                
                # 3. 生成特殊错误处理prompt
                design_code = module_code if module_code else ""
                testbench_code = testbench_code if testbench_code else ""
                
                error_prompt = self._generate_simulation_error_prompt(
                    enhanced_error=enhanced_error,
                    design_code=design_code,
                    testbench_code=testbench_code
                )
                
                # 4. 将错误prompt存储到实例变量中，供后续使用
                self._last_error_prompt = error_prompt
                self._last_enhanced_error = enhanced_error
                
                # 5. 返回增强的错误信息
                return {
                    "success": False,
                    "simulator": simulator,
                    "simulation_output": sim_result.get("output", ""),
                    "compilation_output": sim_result.get("compilation_output", ""),
                    "waveform_file": sim_result.get("waveform_file"),
                    "simulation_time": sim_result.get("simulation_time", 0),
                    "errors": sim_result.get("errors", []),
                    "warnings": sim_result.get("warnings", []),
                    "stage": stage,
                    "files_compiled": [str(f) for f in files_to_compile],
                    "dependency_analysis": sim_result.get("dependency_analysis", {}),
                    "error_message": error_message,
                    "compilation_errors": sim_result.get("compilation_output", ""),
                    "simulation_errors": sim_result.get("simulation_output", ""),
                    # 🆕 新增：增强错误处理信息
                    "enhanced_error_info": enhanced_error,
                    "error_classification": enhanced_error["error_classification"],
                    "recovery_suggestions": enhanced_error["recovery_suggestions"],
                    "debug_information": enhanced_error["debug_information"],
                    "error_prompt_available": True
                }
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            
            # 🚨 对异常也应用错误处理机制
            error_message = f"仿真执行异常: {str(e)}"
            error_context = {
                "file_paths": [str(f) for f in files_to_compile] if 'files_to_compile' in locals() else [],
                "stage": "exception",
                "simulator": simulator,
                "command": "",
                "timestamp": str(time.time()),
                "working_directory": str(Path.cwd())
            }
            
            simulation_result = {
                "success": False,
                "stage": "exception",
                "return_code": -1,
                "error_output": str(e)
            }
            
            enhanced_error = self._enhance_error_information(
                error_message=error_message,
                error_context=error_context,
                simulation_result=simulation_result
            )
            
            # 记录增强的错误信息
            self.logger.info(f"🔍 异常错误分类: {enhanced_error['error_classification']['error_type']}")
            self.logger.info(f"🔍 异常错误严重程度: {enhanced_error['error_classification']['severity']}")
            
            return {
                "success": False,
                "error": error_message,
                "error_message": error_message,
                "compilation_errors": "",
                "simulation_errors": "",
                "stage": "exception",
                # 🆕 新增：增强错误处理信息
                "enhanced_error_info": enhanced_error,
                "error_classification": enhanced_error["error_classification"],
                "recovery_suggestions": enhanced_error["recovery_suggestions"],
                "debug_information": enhanced_error["debug_information"],
                "error_prompt_available": True
            }
    
    async def _find_missing_dependencies(self, missing_modules: List[str]) -> List[str]:
        """从文件管理器中查找缺失的依赖模块"""
        additional_files = []
        
        try:
            from core.file_manager import get_file_manager
            file_manager = get_file_manager()
            
            # 获取所有Verilog文件
            all_verilog_files = file_manager.get_files_by_type("verilog")
            
            for missing_module in missing_modules:
                self.logger.info(f"🔍 搜索缺失模块: {missing_module}")
                
                # 在文件名或内容中搜索模块
                for file_ref in all_verilog_files:
                    file_path = file_ref.file_path
                    filename = Path(file_path).stem.lower()
                    
                    # 简单的文件名匹配
                    if missing_module.lower() in filename:
                        if file_path not in additional_files:
                            additional_files.append(file_path)
                            self.logger.info(f"✅ 找到依赖文件: {Path(file_path).name}")
                        break
                    
                    # 内容匹配（更精确但较慢）
                    try:
                        if Path(file_path).exists():
                            content = Path(file_path).read_text(encoding='utf-8')
                            if f"module {missing_module}" in content:
                                if file_path not in additional_files:
                                    additional_files.append(file_path)
                                    self.logger.info(f"✅ 在文件内容中找到模块 {missing_module}: {Path(file_path).name}")
                                break
                    except:
                        continue
        except Exception as e:
            self.logger.warning(f"查找缺失依赖时出错: {str(e)}")
        
        return additional_files
    
    async def _run_iverilog_simulation_with_deps(self, files_to_compile: List[Path], 
                                               options: Dict) -> Dict[str, Any]:
        """执行iverilog仿真（支持多文件依赖）"""
        try:
            self.logger.info(f"🔨 开始编译 {len(files_to_compile)} 个文件")
            
            # 验证所有文件存在
            missing_files = []
            for file_path in files_to_compile:
                if not file_path.exists():
                    missing_files.append(str(file_path))
            
            if missing_files:
                return {
                    "success": False,
                    "error": f"编译文件缺失: {missing_files}",
                    "stage": "file_validation"
                }
            
            # 确保输出目录存在
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建仿真命令
            output_file = self.artifacts_dir / "simulation"
            vcd_file = self.artifacts_dir / "simulation.vcd"
            
            # 尝试从文件中识别顶层模块
            top_module = self._identify_top_module(files_to_compile)
            
            compile_cmd = ["iverilog", "-o", str(output_file)]
            if top_module:
                compile_cmd.extend(["-s", top_module])
            compile_cmd.extend([str(f) for f in files_to_compile])
            
            self.logger.info(f"🔨 编译命令: {' '.join(compile_cmd)}")
            
            # 编译 - 使用项目根目录作为工作目录
            project_root = Path.cwd()
            self.logger.info(f"🔨 编译工作目录: {project_root}")
            
            compile_result = await asyncio.create_subprocess_exec(
                *compile_cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root
            )
            
            compile_stdout, compile_stderr = await compile_result.communicate()
            
            compile_stdout_str = compile_stdout.decode('utf-8', errors='ignore') if compile_stdout else ""
            compile_stderr_str = compile_stderr.decode('utf-8', errors='ignore') if compile_stderr else ""
            
            if compile_result.returncode != 0:
                self.logger.error(f"❌ 编译失败，返回码: {compile_result.returncode}")
                self.logger.error(f"编译错误: {compile_stderr_str}")
                
                # 🚨 在底层方法中也应用错误处理机制
                error_message = f"编译失败: {compile_stderr_str}"
                error_context = {
                    "file_paths": [str(f) for f in files_to_compile],
                    "stage": "compilation",
                    "simulator": "iverilog",
                    "command": " ".join(compile_cmd),
                    "timestamp": str(time.time()),
                    "working_directory": str(Path.cwd())
                }
                
                simulation_result = {
                    "success": False,
                    "stage": "compilation",
                    "return_code": compile_result.returncode,
                    "compilation_output": compile_stderr_str,
                    "error_output": compile_stderr_str
                }
                
                enhanced_error = self._enhance_error_information(
                    error_message=error_message,
                    error_context=error_context,
                    simulation_result=simulation_result
                )
                
                # 记录增强的错误信息
                self.logger.info(f"🔍 编译错误分类: {enhanced_error['error_classification']['error_type']}")
                self.logger.info(f"🔍 编译错误严重程度: {enhanced_error['error_classification']['severity']}")
                
                return {
                    "success": False,
                    "error": error_message,
                    "stage": "compilation",
                    "compilation_output": compile_stderr_str,
                    "command": " ".join(compile_cmd),
                    # 🆕 新增：增强错误处理信息
                    "enhanced_error_info": enhanced_error,
                    "error_classification": enhanced_error["error_classification"],
                    "recovery_suggestions": enhanced_error["recovery_suggestions"],
                    "debug_information": enhanced_error["debug_information"],
                    "error_prompt_available": True
                }
            
            # 验证输出文件已创建
            if not output_file.exists():
                return {
                    "success": False,
                    "error": f"编译成功但输出文件未创建: {output_file}",
                    "stage": "compilation",
                    "compilation_output": compile_stdout_str
                }
            
            # 运行仿真 - 使用vvp执行编译后的仿真文件
            run_cmd = ["vvp", str(output_file)]
            self.logger.info(f"🔨 运行仿真命令: {' '.join(run_cmd)}")
            run_result = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root
            )
            
            run_stdout, run_stderr = await run_result.communicate()
            
            # 安全解码输出，处理None情况
            stdout_text = run_stdout.decode('utf-8', errors='ignore') if run_stdout else ""
            stderr_text = run_stderr.decode('utf-8', errors='ignore') if run_stderr else ""
            
            simulation_success = run_result.returncode == 0
            
            # 记录仿真结果
            if simulation_success:
                self.logger.info(f"✅ 仿真执行成功")
                if stdout_text:
                    self.logger.debug(f"仿真输出: {stdout_text[:2000]}...")
                
                return {
                    "success": simulation_success,
                    "output": stdout_text,
                    "compilation_output": compile_stdout_str,
                    "waveform_file": str(vcd_file) if vcd_file.exists() else None,
                    "errors": [stderr_text] if stderr_text else [],
                    "warnings": [],
                    "return_code": run_result.returncode,
                    "command": " ".join(run_cmd),
                    "stage": "simulation"
                }
            else:
                self.logger.error(f"❌ 仿真执行失败，返回码: {run_result.returncode}")
                if stderr_text:
                    self.logger.error(f"仿真错误: {stderr_text}")
                
                # 🚨 在底层方法中也应用错误处理机制
                error_message = f"仿真执行失败: {stderr_text}" if stderr_text else f"仿真执行失败，返回码: {run_result.returncode}"
                error_context = {
                    "file_paths": [str(f) for f in files_to_compile],
                    "stage": "simulation_failed",
                    "simulator": "iverilog",
                    "command": " ".join(run_cmd),
                    "timestamp": str(time.time()),
                    "working_directory": str(Path.cwd())
                }
                
                simulation_result = {
                    "success": False,
                    "stage": "simulation_failed",
                    "return_code": run_result.returncode,
                    "simulation_output": stdout_text,
                    "error_output": stderr_text
                }
                
                enhanced_error = self._enhance_error_information(
                    error_message=error_message,
                    error_context=error_context,
                    simulation_result=simulation_result
                )
                
                # 记录增强的错误信息
                self.logger.info(f"🔍 仿真错误分类: {enhanced_error['error_classification']['error_type']}")
                self.logger.info(f"🔍 仿真错误严重程度: {enhanced_error['error_classification']['severity']}")
                
                return {
                    "success": False,
                    "error": error_message,
                    "output": stdout_text,
                    "compilation_output": compile_stdout_str,
                    "waveform_file": str(vcd_file) if vcd_file.exists() else None,
                    "errors": [stderr_text] if stderr_text else [],
                    "warnings": [],
                    "return_code": run_result.returncode,
                    "command": " ".join(run_cmd),
                    "stage": "simulation_failed",
                    # 🆕 新增：增强错误处理信息
                    "enhanced_error_info": enhanced_error,
                    "error_classification": enhanced_error["error_classification"],
                    "recovery_suggestions": enhanced_error["recovery_suggestions"],
                    "debug_information": enhanced_error["debug_information"],
                    "error_prompt_available": True
                }
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            
            # 🚨 对异常也应用错误处理机制
            error_message = f"仿真执行异常: {str(e)}"
            error_context = {
                "file_paths": [str(f) for f in files_to_compile] if 'files_to_compile' in locals() else [],
                "stage": "exception",
                "simulator": "iverilog",
                "command": "",
                "timestamp": str(time.time()),
                "working_directory": str(Path.cwd())
            }
            
            simulation_result = {
                "success": False,
                "stage": "exception",
                "return_code": -1,
                "error_output": str(e)
            }
            
            enhanced_error = self._enhance_error_information(
                error_message=error_message,
                error_context=error_context,
                simulation_result=simulation_result
            )
            
            # 记录增强的错误信息
            self.logger.info(f"🔍 异常错误分类: {enhanced_error['error_classification']['error_type']}")
            self.logger.info(f"🔍 异常错误严重程度: {enhanced_error['error_classification']['severity']}")
            
            return {
                "success": False,
                "error": error_message,
                "stage": "exception",
                # 🆕 新增：增强错误处理信息
                "enhanced_error_info": enhanced_error,
                "error_classification": enhanced_error["error_classification"],
                "recovery_suggestions": enhanced_error["recovery_suggestions"],
                "debug_information": enhanced_error["debug_information"],
                "error_prompt_available": True
            }

    async def _run_iverilog_simulation(self, module_file: Path, testbench_file: Path,
                                     options: Dict) -> Dict[str, Any]:
        """执行iverilog仿真"""
        try:
            # 确保输出目录存在
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建仿真命令
            output_file = self.artifacts_dir / "simulation"
            vcd_file = self.artifacts_dir / "simulation.vcd"
            
            compile_cmd = [
                "iverilog",
                "-o", str(output_file),
                str(module_file),
                str(testbench_file)
            ]
            
            # 编译 - 使用项目根目录作为工作目录
            project_root = Path.cwd()
            self.logger.info(f"🔨 编译工作目录: {project_root}")
            
            compile_result = await asyncio.create_subprocess_exec(
                *compile_cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root
            )
            
            compile_stdout, compile_stderr = await compile_result.communicate()
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "output": compile_stderr.decode(),
                    "errors": [compile_stderr.decode()]
                }
            
            # 运行仿真 - 使用vvp执行编译后的仿真文件
            run_cmd = ["vvp", str(output_file)]
            run_result = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root
            )
            
            run_stdout, run_stderr = await run_result.communicate()
            
            # 安全解码输出，处理None情况
            stdout_text = run_stdout.decode('utf-8', errors='ignore') if run_stdout else ""
            stderr_text = run_stderr.decode('utf-8', errors='ignore') if run_stderr else ""
            
            simulation_success = run_result.returncode == 0
            
            # 记录仿真结果
            if simulation_success:
                self.logger.info(f"✅ 仿真执行成功")
                if stdout_text:
                    self.logger.debug(f"仿真输出: {stdout_text[:2000]}...")
            else:
                self.logger.error(f"❌ 仿真执行失败，返回码: {run_result.returncode}")
                if stderr_text:
                    self.logger.error(f"仿真错误: {stderr_text}")
            
            return {
                "success": simulation_success,
                "output": stdout_text,
                "waveform_file": str(vcd_file) if vcd_file.exists() else None,
                "errors": [stderr_text] if stderr_text else [],
                "warnings": [],
                "return_code": run_result.returncode,
                "command": " ".join(run_cmd)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
        
        if error_count > 0:
            recommendations.append(f"修复 {error_count} 个语法错误以确保代码可编译")
        
        if warning_count > 5:
            recommendations.append("考虑解决主要的代码风格警告以提高可读性")
        
        if any("line exceeds" in issue["message"] for issue in issues):
            recommendations.append("将长行分解为多行以提高代码可读性")
            
        if len(recommendations) == 0:
            recommendations.append("代码质量良好，继续保持！")
        
        return recommendations
    
    async def _tool_generate_build_script(self, verilog_files: List[str], testbench_files: List[str],
                                        script_type: str = "makefile", target_name: str = "simulation",
                                        build_options: Dict = None) -> Dict[str, Any]:
        """生成构建脚本工具实现"""
        try:
            self.logger.info(f"📜 生成构建脚本: {script_type}")
            build_options = build_options or {}
            
            script_content = await self._generate_script_content(
                verilog_files, testbench_files, script_type, target_name, build_options
            )
            
            # 确定脚本文件名
            if script_type == "makefile":
                script_filename = "Makefile"
            elif script_type == "bash":
                script_filename = f"build_{target_name}.sh"
            elif script_type == "tcl":
                script_filename = f"build_{target_name}.tcl"
            else:
                script_filename = f"build_{target_name}.py"
            
            # 保存脚本
            script_path = self.artifacts_dir / script_filename
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 为shell脚本添加执行权限
            if script_type == "bash":
                os.chmod(script_path, 0o755)
            
            return {
                "success": True,
                "script_type": script_type,
                "script_filename": script_filename,
                "script_path": str(script_path),
                "target_name": target_name,
                "verilog_files": verilog_files,
                "testbench_files": testbench_files,
                "build_options": build_options,
                "save_reminder": f"⚠️ 重要提醒：构建脚本已生成完成，文件已保存到 {script_path}！",
                "save_status": {
                    "script_saved": True,
                    "script_path": str(script_path),
                    "executable": script_type == "bash"
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 构建脚本生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_script_content(self, verilog_files: List[str], testbench_files: List[str],
                                     script_type: str, target_name: str, build_options: Dict) -> str:
        """生成脚本内容"""
        simulator = build_options.get("simulator", "iverilog")
        
        if script_type == "makefile":
            return self._generate_makefile(verilog_files, testbench_files, target_name, simulator)
        elif script_type == "bash":
            return self._generate_bash_script(verilog_files, testbench_files, target_name, simulator)
        else:
            return f"# {script_type} script generation not implemented yet"
    
    def _generate_makefile(self, verilog_files: List[str], testbench_files: List[str],
                          target_name: str, simulator: str) -> str:
        """生成Makefile"""
        all_files = " ".join(verilog_files + testbench_files)
        
        makefile_content = f"""# Generated Makefile for {target_name}
# Simulator: {simulator}

VERILOG_FILES = {' '.join(verilog_files)}
TESTBENCH_FILES = {' '.join(testbench_files)}
ALL_FILES = $(VERILOG_FILES) $(TESTBENCH_FILES)

TARGET = {target_name}
VCD_FILE = $(TARGET).vcd

# Default target
all: compile simulate

# Compile the design
compile: $(TARGET)

$(TARGET): $(ALL_FILES)
\t{simulator} -o $(TARGET) $(ALL_FILES)

# Run simulation
simulate: $(TARGET)
\t./$(TARGET)

# View waveforms (if GTKWave is available)
waves: $(VCD_FILE)
\tgtkwave $(VCD_FILE) &

# Clean generated files
clean:
\trm -f $(TARGET) $(VCD_FILE) *.vvp

# Lint check
lint:
\tverilator --lint-only $(VERILOG_FILES)

.PHONY: all compile simulate waves clean lint
"""
        return makefile_content
    
    def _generate_bash_script(self, verilog_files: List[str], testbench_files: List[str],
                            target_name: str, simulator: str) -> str:
        """生成Bash脚本"""
        all_files = " ".join(verilog_files + testbench_files)
        
        bash_content = f"""#!/bin/bash
# Generated build script for {target_name}
# Simulator: {simulator}

set -e  # Exit on any error

VERILOG_FILES="{' '.join(verilog_files)}"
TESTBENCH_FILES="{' '.join(testbench_files)}"
TARGET="{target_name}"
VCD_FILE="${target_name}.vcd"

# Function to compile
compile() {{
    echo "Compiling design..."
    {simulator} -o $TARGET $VERILOG_FILES $TESTBENCH_FILES
    echo "Compilation completed successfully"
}}

# Function to simulate
simulate() {{
    echo "Running simulation..."
    ./$TARGET
    echo "Simulation completed"
}}

# Function to clean
clean() {{
    echo "Cleaning generated files..."
    rm -f $TARGET $VCD_FILE *.vvp
    echo "Clean completed"
}}

# Main execution
case "$1" in
    compile)
        compile
        ;;
    simulate)
        simulate
        ;;
    all)
        compile
        simulate
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {{compile|simulate|all|clean}}"
        echo "  compile  - Compile the design"
        echo "  simulate - Run simulation"
        echo "  all      - Compile and simulate"
        echo "  clean    - Clean generated files"
        exit 1
        ;;
esac
"""
        return bash_content
    
    async def _tool_execute_build_script(self, script_name: str, action: str = "all",
                                       arguments: List[str] = None, timeout: int = 300,
                                       working_directory: str = None) -> Dict[str, Any]:
        """执行构建脚本工具实现"""
        try:
            self.logger.info(f"⚙️ 执行构建脚本: {script_name} - {action}")
            
            arguments = arguments or []
            work_dir = Path(working_directory) if working_directory else self.artifacts_dir
            script_path = work_dir / script_name
            
            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"Script file not found: {script_name}"
                }
            
            # 构建命令
            if script_name.lower() == "makefile" or script_name.endswith(".mk"):
                cmd = ["make", "-f", script_name, action] + arguments
            elif script_name.endswith(".sh"):
                cmd = ["bash", script_name, action] + arguments
            else:
                cmd = [str(script_path), action] + arguments
            
            # 执行脚本
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"Script execution timed out after {timeout} seconds"
                }
            
            success = process.returncode == 0
            
            return {
                "success": success,
                "return_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "script_name": script_name,
                "action": action,
                "execution_time": timeout,  # This would be actual time in real implementation
                "working_directory": str(work_dir)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 构建脚本执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    

    

    

    
    async def _tool_analyze_test_failures(self, design_code: str, 
                                         compilation_errors: str = "", 
                                         simulation_errors: str = "",
                                         test_assertions: str = "",
                                         testbench_code: str = "",
                                         testbench_file: str = "",
                                         iteration_number: int = 1,
                                         previous_fixes: List[str] = None) -> Dict[str, Any]:
        """测试失败分析工具实现 - 智能分析并自动修复测试失败"""
        try:
            self.logger.info(f"🔍 第{iteration_number}次迭代：智能分析测试失败并尝试自动修复")
            
            # 使用LLM分析错误并生成修复方案
            analysis_prompt = f"""
作为资深Verilog/SystemVerilog专家，请深入分析以下测试失败情况并提供精确的修复方案：

**编译错误:**
{compilation_errors}

**仿真错误:**
{simulation_errors}

**测试断言失败:**
{test_assertions}

**设计代码:**
{design_code}

**测试台代码:**
{testbench_code}

## 🔧 专业Verilog语法修复指导

### ⚠️ 常见语法错误识别与修复策略

#### 1. **未命名begin块变量声明错误**
**错误模式**: `Variable declaration in unnamed block requires SystemVerilog`
**根本原因**: 在未命名的begin-end块中声明变量违反了Verilog标准
**标准修复方法**:
```verilog
// ❌ 错误写法
@(posedge clk);
begin
    reg [4:0] expected;  // SystemVerilog语法
    reg [4:0] actual;
    // 逻辑...
end

// ✅ 修复方法1: 移动变量声明到initial块顶部
initial begin
    reg [4:0] expected;
    reg [4:0] actual;
    
    // 等待时钟
    @(posedge clk);
    expected = 5'b00000;
    actual = {{cout, sum}};
    // 验证逻辑...
end

// ✅ 修复方法2: 使用wire类型
wire [4:0] expected = 5'b00000;
wire [4:0] actual = {{cout, sum}};
@(posedge clk);
// 验证逻辑...
```

#### 2. **时序和组合逻辑混合错误**
**错误识别**: always块类型不匹配
**修复策略**: 明确区分组合逻辑(always @(*))和时序逻辑(always @(posedge clk))

#### 3. **端口连接和模块实例化错误**
**常见问题**: 端口名不匹配、位宽不一致
**修复方法**: 检查端口声明与实例化的一致性

#### 4. **testbench结构错误**
**标准testbench模板**:
```verilog
`timescale 1ns/1ps

module tb_module;
    // 1. 信号声明(在模块顶部)
    reg [N-1:0] input_signals;
    wire [M-1:0] output_signals;
    
    // 2. 时钟生成(如需要)
    reg clk = 0;
    always #5 clk = ~clk;
    
    // 3. 被测模块实例化
    module_name uut (.ports(signals));
    
    // 4. 测试逻辑
    initial begin
        // 初始化
        // 波形设置
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_module);
        
        // 测试用例
        // 结束仿真
        $finish;
    end
endmodule
```

### 🎯 分析要求

请基于以上专业知识，提供：
1. **精确的错误根本原因分析** (区分语法、语义、时序错误)
2. **具体的修复步骤** (提供完整的代码修改)
3. **标准Verilog转换** (如果涉及SystemVerilog特性)
4. **修复验证方法** (如何确认修复效果)
5. **防止循环修复** (确保一次性彻底解决问题)

### 📋 重要修复原则
- **语法严格性**: 严格遵循IEEE 1364-2005 Verilog标准
- **变量作用域**: 确保变量在正确的作用域内声明
- **时序正确性**: 正确处理时钟域和reset逻辑
- **可综合性**: 确保代码可被综合工具处理
- **仿真兼容性**: 确保与iverilog等开源工具兼容

格式化输出为JSON：
{{
    "error_analysis": "详细的错误根本原因分析，包括具体的语法规则违反",
    "fix_required": true/false,
    "fix_type": "design_code" | "testbench" | "both",
    "specific_fixes": ["详细的修复步骤1", "步骤2", "步骤3"],
    "code_changes": {{
        "file_to_modify": "需要修改的文件路径",
        "modifications": "完整的修复后的代码内容"
    }},
    "syntax_violations": ["具体违反的Verilog语法规则"],
    "prevention_tips": ["防止类似错误的建议"]
}}
"""

            # 🔧 修复：调用LLM进行智能分析（使用直接调用避免递归工具调用）
            llm_response = await self.llm_manager.llm_client.send_prompt(
                analysis_prompt,
                system_prompt="你是一位专业的Verilog测试和调试专家。请分析测试失败原因并提供修复建议。请直接返回分析结果，不要使用工具调用。"
            )
            
            self.logger.info(f"🤖 LLM分析结果: {llm_response[:2000]}...")
            
            # 解析LLM响应
            try:
                import json
                import re
                
                # 尝试提取JSON内容
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    # 如果没有找到JSON，创建基本分析结果
                    analysis_data = {
                        "error_analysis": "智能分析中...",
                        "fix_required": True,
                        "fix_type": "testbench",
                        "specific_fixes": ["需要修复SystemVerilog语法错误"],
                        "code_changes": {
                            "file_to_modify": testbench_file,
                            "modifications": "转换SystemVerilog语法为标准Verilog"
                        }
                    }
                
                # 如果LLM判断需要修复，则尝试自动修复
                fix_results = []
                if analysis_data.get("fix_required", False):
                    self.logger.info("🔧 LLM建议进行自动修复，开始执行修复...")
                    
                    # 1. 检查是否是未命名begin块变量声明错误
                    if "Variable declaration in unnamed block requires SystemVerilog" in compilation_errors:
                        self.logger.info("🎯 检测到未命名begin块变量声明错误，执行专项修复...")
                        fix_result = await self._auto_fix_unnamed_block_variables(
                            testbench_file, compilation_errors, testbench_code
                        )
                        fix_results.append(fix_result)
                        
                        if fix_result.get("success"):
                            self.logger.info("✅ 未命名begin块变量声明错误修复完成")
                        else:
                            self.logger.warning(f"⚠️ 未命名begin块修复失败: {fix_result.get('error', 'Unknown error')}")
                    
                    # 2. 通用SystemVerilog语法错误修复
                    elif "SystemVerilog" in compilation_errors and testbench_file:
                        fix_result = await self._auto_fix_systemverilog_syntax(
                            testbench_file, compilation_errors, testbench_code
                        )
                        fix_results.append(fix_result)
                        
                        if fix_result.get("success"):
                            self.logger.info("✅ SystemVerilog语法自动修复完成")
                        else:
                            self.logger.warning(f"⚠️ 自动修复失败: {fix_result.get('error', 'Unknown error')}")
                    
                    # 3. 基于LLM分析结果的智能修复
                    elif analysis_data.get("code_changes", {}).get("modifications"):
                        self.logger.info("🤖 基于LLM分析结果执行智能修复...")
                        fix_result = await self._apply_llm_suggested_fixes(
                            analysis_data["code_changes"], testbench_file
                        )
                        fix_results.append(fix_result)
                        
                        if fix_result.get("success"):
                            self.logger.info("✅ LLM建议的修复方案应用完成")
                        else:
                            self.logger.warning(f"⚠️ LLM修复方案应用失败: {fix_result.get('error', 'Unknown error')}")
                
                return {
                    "success": True,
                    "analysis": analysis_data,
                    "llm_response": llm_response,
                    "auto_fix_attempted": len(fix_results) > 0,
                    "fix_results": fix_results,
                    "iteration_context": {
                        "iteration_number": iteration_number,
                        "has_compilation_errors": bool(compilation_errors),
                        "fix_required": analysis_data.get("fix_required", False)
                    },
                    "next_action": "retry_simulation" if any(r.get("success") for r in fix_results) else "manual_review"
                }
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"⚠️ LLM响应解析失败: {e}, 使用fallback分析")
                # Fallback到基础分析逻辑
                return await self._fallback_analysis(compilation_errors, simulation_errors, test_assertions, testbench_file)
            
        except Exception as e:
            self.logger.error(f"❌ 智能测试失败分析异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_suggestions": [
                    "检查SystemVerilog语法兼容性",
                    "验证testbench文件语法",
                    "确认编译器支持的Verilog标准"
                ]
            }
    
    async def _auto_fix_unnamed_block_variables(self, testbench_file: str, compilation_errors: str, testbench_code: str) -> Dict[str, Any]:
        """专门修复未命名begin块中的变量声明错误"""
        try:
            self.logger.info(f"🎯 专项修复未命名begin块变量声明错误: {testbench_file}")
            
            # 使用规则基础的修复方法，针对常见的模式进行修复
            fixed_code = testbench_code
            
            # 修复模式1: @(posedge clk); begin ... end 块中的变量声明
            import re
            
            # 查找问题模式：@(posedge clk); 后跟 begin 块，其中包含变量声明
            pattern = r'(@\(posedge\s+\w+\);\s*\n?\s*)begin\s*\n(\s*reg\s+.*?\n(?:\s*reg\s+.*?\n)*)(.*?)end'
            
            def fix_unnamed_block(match):
                clock_event = match.group(1)
                variable_declarations = match.group(2).strip()
                remaining_logic = match.group(3).strip()
                
                # 将变量声明移动到initial块的开头
                # 这里我们需要找到当前的initial块，并将变量声明添加到其开头
                
                # 修复方案：将整个块改为使用已声明的变量
                # 创建临时变量名（避免冲突）
                temp_vars = []
                var_assignments = []
                
                for line in variable_declarations.split('\n'):
                    if 'reg' in line and line.strip():
                        # 提取变量名和类型
                        var_match = re.search(r'reg\s+(?:\[.*?\])?\s*(\w+)', line)
                        if var_match:
                            var_name = var_match.group(1)
                            temp_vars.append(var_name)
                            # 创建赋值语句
                            if 'expected' in var_name:
                                var_assignments.append(f"        {var_name} = 5'b00000;")
                            elif 'actual' in var_name:
                                var_assignments.append(f"        {var_name} = {{cout, sum}};")
                
                # 重构代码块
                fixed_block = f"{clock_event}\n"
                if var_assignments:
                    fixed_block += "\n".join(var_assignments) + "\n"
                if remaining_logic:
                    fixed_block += f"        {remaining_logic.strip()}\n"
                
                return fixed_block
            
            # 应用修复
            fixed_code = re.sub(pattern, fix_unnamed_block, fixed_code, flags=re.DOTALL | re.MULTILINE)
            
            # 额外修复：将所有reg变量声明移动到模块级别
            # 查找所有在begin块中的reg声明
            reg_declarations = []
            lines = fixed_code.split('\n')
            in_initial_block = False
            indent_level = 0
            
            for i, line in enumerate(lines):
                if 'initial begin' in line:
                    in_initial_block = True
                    continue
                
                if in_initial_block:
                    if 'begin' in line:
                        indent_level += 1
                    if 'end' in line:
                        indent_level -= 1
                        if indent_level < 0:
                            in_initial_block = False
                    
                    # 如果在begin块中发现reg声明，提取并移除
                    if re.match(r'\s*reg\s+', line.strip()) and 'reg clk' not in line:
                        reg_declarations.append(line.strip())
                        lines[i] = ''  # 移除这行
            
            # 将reg声明添加到模块级别（在其他reg声明之后）
            if reg_declarations:
                # 找到合适的位置插入（在已有的reg声明之后）
                insert_position = -1
                for i, line in enumerate(lines):
                    if re.match(r'\s*reg\s+', line.strip()) and 'reg clk' not in line:
                        insert_position = i + 1
                
                if insert_position > 0:
                    # 插入新的reg声明
                    for reg_decl in reg_declarations:
                        lines.insert(insert_position, reg_decl)
                        insert_position += 1
            
            fixed_code = '\n'.join(lines)
            
            # 写入修复后的代码
            if fixed_code != testbench_code:
                with open(testbench_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                
                self.logger.info(f"✅ 未命名begin块变量声明错误修复完成: {testbench_file}")
                return {
                    "success": True,
                    "message": "已修复未命名begin块中的变量声明错误",
                    "fixed_file": testbench_file,
                    "changes_made": "将begin块中的变量声明移动到模块级别，重构测试逻辑"
                }
            else:
                return {
                    "success": False,
                    "error": "未检测到需要修复的模式"
                }
                
        except Exception as e:
            self.logger.error(f"❌ 未命名begin块修复失败: {str(e)}")
            return {
                "success": False,
                "error": f"修复过程中发生异常: {str(e)}"
            }
    
    async def _auto_fix_systemverilog_syntax(self, testbench_file: str, compilation_errors: str, testbench_code: str) -> Dict[str, Any]:
        """自动修复SystemVerilog语法错误"""
        try:
            self.logger.info(f"🔧 开始自动修复SystemVerilog语法错误: {testbench_file}")
            
            # 使用LLM智能转换SystemVerilog语法为标准Verilog
            fix_prompt = f"""
请将以下Verilog testbench代码中的SystemVerilog语法转换为标准Verilog-2001语法：

**编译错误信息:**
{compilation_errors}

**原始testbench代码:**
{testbench_code}

**修复要求:**
1. 将SystemVerilog的task语法转换为标准Verilog语法
2. 如果task包含多条语句，使用begin/end块包围
3. 确保所有语法符合Verilog-2001标准
4. 保持功能逻辑不变

请直接输出修复后的完整Verilog代码，不要添加任何解释。
"""
            
            # 🔧 修复：调用LLM生成修复后的代码（使用直接调用避免递归工具调用）
            fixed_code = await self.llm_manager.llm_client.send_prompt(
                fix_prompt,
                system_prompt="你是一位专业的Verilog修复专家。请输出修复后的完整代码。请直接返回代码，不要使用工具调用。"
            )
            
            # 清理LLM响应，提取纯代码部分
            fixed_code = self._extract_verilog_code(fixed_code)
            
            if fixed_code:
                # 写入修复后的代码
                with open(testbench_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                
                self.logger.info(f"✅ SystemVerilog语法修复完成: {testbench_file}")
                return {
                    "success": True,
                    "message": "SystemVerilog语法已转换为标准Verilog",
                    "fixed_file": testbench_file,
                    "changes_made": "将SystemVerilog task语法转换为标准Verilog语法"
                }
            else:
                return {
                    "success": False,
                    "error": "无法从LLM响应中提取有效的Verilog代码"
                }
                
        except Exception as e:
            self.logger.error(f"❌ SystemVerilog语法自动修复失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_verilog_code(self, llm_response: str) -> str:
        """使用统一的FileOperationManager提取Verilog代码（重构后）"""
        try:
            # 使用统一的文件操作管理器进行代码提取
            extracted_code = self.file_manager.extract_verilog_code(llm_response)
            
            if extracted_code:
                self.logger.debug(f"✅ 成功提取Verilog代码: {len(extracted_code)}字符")
                return extracted_code
            else:
                self.logger.warning(f"⚠️ 未找到有效的Verilog代码")
                return ""
                
        except Exception as e:
            self.logger.warning(f"⚠️ 代码提取失败: {e}")
            return ""
    
    async def _fallback_analysis(self, compilation_errors: str, simulation_errors: str, test_assertions: str, testbench_file: str) -> Dict[str, Any]:
        """备用分析逻辑"""
        try:
            # 简单的基于规则的分析
            if "SystemVerilog" in compilation_errors and testbench_file:
                # 尝试直接修复SystemVerilog错误
                fix_result = await self._auto_fix_systemverilog_syntax(
                    testbench_file, compilation_errors, ""
                )
                
                return {
                    "success": True,
                    "analysis": {
                        "error_analysis": "检测到SystemVerilog语法错误",
                        "fix_required": True,
                        "fix_type": "testbench"
                    },
                    "auto_fix_attempted": True,
                    "fix_results": [fix_result],
                    "next_action": "retry_simulation" if fix_result.get("success") else "manual_review"
                }
            
            return {
                "success": True,
                "analysis": {
                    "error_analysis": "需要手动检查测试失败原因",
                    "fix_required": False,
                    "fix_type": "manual"
                },
                "auto_fix_attempted": False,
                "fix_results": [],
                "next_action": "manual_review"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_assertion_failures(self, assertions: str, design_code: str, testbench_code: str) -> Dict[str, List[str]]:
        """分析测试断言失败"""
        analysis = {
            "failure_types": [],
            "root_causes": [],
            "fix_suggestions": []
        }
        
        assertion_lines = assertions.lower()
        
        if "assert" in assertion_lines and "failed" in assertion_lines:
            analysis["failure_types"].append("功能测试失败")
            analysis["root_causes"].append("设计逻辑与预期行为不符")
            analysis["fix_suggestions"].append("逐步调试：添加$display语句跟踪信号变化")
            analysis["fix_suggestions"].append("验证算法逻辑，特别是进位和边界条件")
            analysis["fix_suggestions"].append("检查测试向量是否正确设置")
        
        if "timeout" in assertion_lines or "infinite" in assertion_lines:
            analysis["failure_types"].append("仿真超时")
            analysis["root_causes"].append("可能存在无限循环或死锁")
            analysis["fix_suggestions"].append("检查always块的敏感列表")
            analysis["fix_suggestions"].append("确保所有路径都有$finish语句")
        
        return analysis
    
    def _generate_detailed_fix_guidance(self, analysis: Dict, design_code: str, iteration: int) -> Dict[str, Any]:
        """生成详细的修复指导"""
        guidance = {
            "immediate_actions": [],
            "code_modifications": [],
            "verification_steps": [],
            "debugging_tips": []
        }
        
        # 根据失败类型生成具体指导
        for failure_type in analysis["failure_types"]:
            if "未定义宏" in failure_type:
                guidance["immediate_actions"].append("扫描代码中的所有 ` 字符，移除不必要的宏定义")
                guidance["code_modifications"].append("将类似 `simple_8bit_adder、`verilog 等替换为正确的模块名")
                guidance["verification_steps"].append("使用语法检查器验证清理后的代码")
            
            elif "模块引用错误" in failure_type:
                guidance["immediate_actions"].append("列出所有模块实例化，验证被调用模块存在")
                guidance["code_modifications"].append("确保子模块在同一文件中定义或正确包含")
                guidance["verification_steps"].append("编译单个模块文件验证模块定义正确")
            
            elif "功能测试失败" in failure_type:
                guidance["debugging_tips"].append("在关键信号处添加 $display(\"signal=%b\", signal) 语句")
                guidance["debugging_tips"].append("手动计算几个测试案例的预期输出")
                guidance["verification_steps"].append("使用波形查看器分析信号时序")
        
        # 根据迭代次数调整指导策略
        if iteration >= 3:
            guidance["immediate_actions"].insert(0, "考虑重新设计架构，当前方法可能存在根本性问题")
            guidance["debugging_tips"].append("寻求代码审查或使用不同的实现方法")
        
        return guidance
    
    def _recommend_next_steps(self, analysis: Dict, iteration: int) -> List[str]:
        """推荐下一步行动"""
        steps = []
        
        if "未定义宏错误" in analysis["failure_types"]:
            steps.append("1. 清理代码中的所有宏定义问题")
            steps.append("2. 重新编译验证语法正确性")
        
        if "模块引用错误" in analysis["failure_types"]:
            steps.append("3. 验证所有模块依赖关系")
            steps.append("4. 确保编译顺序正确")
        
        if "功能测试失败" in analysis["failure_types"]:
            steps.append("5. 添加调试输出语句")
            steps.append("6. 逐步验证算法逻辑")
        
        if iteration >= 2:
            steps.append("7. 考虑简化设计或分解复杂逻辑")
        
        steps.append("8. 运行修复后的完整测试验证")
        
        return steps

    async def _validate_verilog_file_content(self, content: str) -> bool:
        """验证Verilog代码内容的基本语法"""
        try:
            # 基本语法检查
            if not content.strip():
                return False
            
            # 检查是否包含基本的Verilog结构
            if not any(keyword in content for keyword in ['module', 'endmodule']):
                return False
            
            # 检查是否有明显的语法错误（如未闭合的括号）
            open_braces = content.count('{')
            close_braces = content.count('}')
            if abs(open_braces - close_braces) > 2:  # 允许少量不匹配
                return False
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            if abs(open_parens - close_parens) > 2:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 内容验证失败: {str(e)}")
            return False

    async def _fix_testbench_syntax(self, content: str, module_name: str) -> str:
        """修复测试台语法错误"""
        try:
            # 简单的语法修复
            fixed_content = content
            
            # 修复常见的语法问题
            fixed_content = fixed_content.replace('`', '')  # 移除宏定义符号
            fixed_content = fixed_content.replace('``', '')  # 移除双宏定义符号
            
            # 确保模块名正确
            if f"module {module_name}_tb" in fixed_content:
                fixed_content = fixed_content.replace(f"module {module_name}_tb", f"module tb_{module_name}")
            
            # 确保实例化名称正确
            if f"{module_name}_tb uut" in fixed_content:
                fixed_content = fixed_content.replace(f"{module_name}_tb uut", f"tb_{module_name} uut")
            
            return fixed_content
            
        except Exception as e:
            self.logger.warning(f"⚠️ 语法修复失败: {str(e)}")
            return content

    async def _validate_verilog_file(self, file_path: Path) -> bool:
        """验证Verilog文件的基本语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本语法检查
            if not content.strip():
                return False
            
            # 检查是否包含基本的Verilog结构
            if not any(keyword in content for keyword in ['module', 'endmodule']):
                return False
            
            # 检查是否有明显的语法错误（如未闭合的括号）
            open_braces = content.count('{')
            close_braces = content.count('}')
            if abs(open_braces - close_braces) > 2:  # 允许少量不匹配
                return False
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            if abs(open_parens - close_parens) > 2:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 文件验证失败: {str(e)}")
            return False

    async def _apply_llm_suggested_fixes(self, code_changes: Dict[str, Any], testbench_file: str) -> Dict[str, Any]:
        """应用LLM建议的修复方案"""
        try:
            self.logger.info(f"🤖 应用LLM建议的修复方案到: {testbench_file}")
            
            # 从code_changes中获取修复内容
            modifications = code_changes.get("modifications", "")
            file_to_modify = code_changes.get("file_to_modify", testbench_file)
            
            if not modifications:
                return {
                    "success": False,
                    "error": "LLM未提供具体的修复内容"
                }
            
            # 如果LLM提供的是完整的代码，直接使用
            if "module " in modifications and "endmodule" in modifications:
                # 这是完整的Verilog代码
                fixed_code = modifications
            else:
                # 这是修复说明，需要我们自己应用修复
                # 读取现有文件内容
                try:
                    with open(file_to_modify, 'r', encoding='utf-8') as f:
                        current_code = f.read()
                except FileNotFoundError:
                    return {
                        "success": False,
                        "error": f"目标文件不存在: {file_to_modify}"
                    }
                
                # 使用LLM重新生成修复后的代码
                fix_prompt = f"""
基于以下修复指导，请修复Verilog测试台代码：

**原始代码:**
{current_code}

**修复指导:**
{modifications}

**修复要求:**
1. 严格遵循Verilog-2001标准
2. 将所有变量声明移到模块级别
3. 避免在未命名begin块中声明变量
4. 保持功能逻辑不变

请输出完整的修复后代码：
"""
                
                # 🔧 修复：调用LLM生成修复后的代码（使用直接调用避免递归工具调用）
                llm_response = await self.llm_manager.llm_client.send_prompt(
                    fix_prompt,
                    system_prompt="你是一位专业的Verilog修复专家。请输出修复后的完整代码。请直接返回代码，不要使用工具调用。"
                )
                
                # 提取Verilog代码
                fixed_code = self._extract_verilog_code(llm_response)
                
                if not fixed_code:
                    return {
                        "success": False,
                        "error": "无法从LLM响应中提取有效的Verilog代码"
                    }
            
            # 写入修复后的代码
            with open(file_to_modify, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            self.logger.info(f"✅ LLM建议的修复方案应用完成: {file_to_modify}")
            return {
                "success": True,
                "message": "LLM建议的修复方案已成功应用",
                "fixed_file": file_to_modify,
                "changes_made": "基于LLM分析结果应用了智能修复"
            }
            
        except Exception as e:
            self.logger.error(f"❌ LLM修复方案应用失败: {str(e)}")
            return {
                "success": False,
                "error": f"修复过程中发生异常: {str(e)}"
            }
    
    def _extract_design_file_path_from_task(self, task_description: str) -> Optional[str]:
        """从任务描述中提取设计文件路径"""
        try:
            import re
            
            # 方法1：查找 "设计文件:" 后面的路径
            design_file_pattern = r'设计文件[:\s]+([^\s\n]+\.v)'
            match = re.search(design_file_pattern, task_description)
            if match:
                return match.group(1)
            
            # 方法2：查找 "设计文件路径" 部分
            path_section_pattern = r'设计文件路径[:\s]*\n.*?设计文件[:\s]+([^\s\n]+\.v)'
            match = re.search(path_section_pattern, task_description, re.DOTALL)
            if match:
                return match.group(1)
            
            # 方法3：查找任何 .v 文件路径
            verilog_file_pattern = r'([^\s\n]+\.v)'
            matches = re.findall(verilog_file_pattern, task_description)
            if matches:
                # 优先选择包含 "design" 或 "counter" 等关键词的路径
                for path in matches:
                    if any(keyword in path.lower() for keyword in ['design', 'counter', 'module']):
                        return path
                # 如果没有找到关键词匹配的，返回第一个
                return matches[0]
            
            self.logger.warning("⚠️ 未从任务描述中找到设计文件路径")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 提取设计文件路径时出错: {str(e)}")
            return None
    
    def _read_design_file_content(self, file_path: str) -> Optional[str]:
        """读取设计文件内容"""
        try:
            from pathlib import Path
            
            # 处理相对路径
            if not os.path.isabs(file_path):
                # 尝试多种可能的路径组合
                possible_paths = [
                    file_path,
                    f"./file_workspace/designs/{os.path.basename(file_path)}",
                    f"./file_workspace/{os.path.basename(file_path)}",
                    f"file_workspace/designs/{os.path.basename(file_path)}",
                    f"file_workspace/{os.path.basename(file_path)}"
                ]
                
                for path in possible_paths:
                    if Path(path).exists():
                        file_path = path
                        break
                else:
                    self.logger.warning(f"⚠️ 未找到设计文件: {file_path}")
                    return None
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"✅ 成功读取设计文件: {file_path} (长度: {len(content)} 字符)")
            return content
            
        except Exception as e:
            self.logger.error(f"❌ 读取设计文件失败: {str(e)}")
            return None
    
    def _generate_code_review_tool_guide(self) -> List[str]:
        """生成EnhancedRealCodeReviewAgent专用的工具使用指导"""
        guide = []
        
        guide.append("\n=== EnhancedRealCodeReviewAgent 工具调用指导 ===")
        guide.append("")
        
        guide.append("【可用工具列表】")
        guide.append("1. generate_testbench - 测试台生成")
        guide.append("   功能: 为Verilog模块生成全面的测试台(testbench)")
        guide.append("   参数: module_name, module_code, test_scenarios, clock_period, simulation_time")
        guide.append("   示例: generate_testbench('adder_8bit', verilog_code, test_scenarios, 10.0, 10000)")
        guide.append("")
        
        guide.append("2. run_simulation - 仿真执行")
        guide.append("   功能: 使用专业工具运行Verilog仿真和验证")
        guide.append("   参数: module_code, testbench_code, simulator, simulation_options")
        guide.append("   示例: run_simulation(verilog_code, testbench_code, 'iverilog', {'timescale':'1ns/1ps'})")
        guide.append("")
        
        guide.append("3. use_external_testbench - 外部测试台使用")
        guide.append("   功能: 使用外部提供的testbench文件进行测试验证")
        guide.append("   参数: design_code, external_testbench_path, design_module_name, simulator")
        guide.append("   示例: use_external_testbench(verilog_code, 'testbench.v', 'adder_8bit', 'iverilog')")
        guide.append("")
        
        guide.append("4. generate_build_script - 构建脚本生成")
        guide.append("   功能: 生成专业的构建脚本(Makefile或shell脚本)")
        guide.append("   参数: verilog_files, testbench_files, script_type, target_name, build_options")
        guide.append("   示例: generate_build_script(['design.v'], ['tb.v'], 'makefile', 'simulation')")
        guide.append("")
        
        guide.append("5. execute_build_script - 脚本执行")
        guide.append("   功能: 安全执行构建脚本进行编译和仿真")
        guide.append("   参数: script_name, action, arguments, timeout, working_directory")
        guide.append("   示例: execute_build_script('Makefile', 'all', None, 300)")
        guide.append("")
        
        guide.append("6. analyze_test_failures - 测试失败分析")
        guide.append("   功能: 分析测试失败原因并提供具体修复建议")
        guide.append("   参数: design_code, compilation_errors, simulation_errors, test_assertions, testbench_code")
        guide.append("   示例: analyze_test_failures(verilog_code, comp_errors, sim_errors, assertions, testbench_code)")
        guide.append("")
        
        guide.append("7. get_tool_usage_guide - 工具使用指导")
        guide.append("   功能: 获取工具使用指导")
        guide.append("   参数: include_examples, include_best_practices")
        guide.append("   示例: get_tool_usage_guide(True, True)")
        guide.append("")
        
        guide.append("【验证流程最佳实践】")
        guide.append("1. 测试台生成: generate_testbench")
        guide.append("2. 仿真执行: run_simulation")
        guide.append("3. 失败分析: analyze_test_failures (如有问题)")
        guide.append("4. 构建脚本: generate_build_script (自动化)")
        guide.append("5. 脚本执行: execute_build_script")
        guide.append("6. 外部测试: use_external_testbench (如有外部测试台)")
        guide.append("")
        
        guide.append("【注意事项】")
        guide.append("- 专注于代码审查、测试和验证，不负责Verilog设计")
        guide.append("- 支持多种仿真器：iverilog, modelsim, vivado")
        guide.append("- 所有工具都支持Schema验证，确保参数格式正确")
        guide.append("- 建议按照最佳实践流程调用工具")
        guide.append("- 支持外部测试台文件，灵活适应不同测试需求")
        guide.append("- 提供详细的失败分析和修复建议")
        
        return guide
    
    async def _tool_get_tool_usage_guide(self, include_examples: bool = True,
                                       include_best_practices: bool = True) -> Dict[str, Any]:
        """获取EnhancedRealCodeReviewAgent专用的工具使用指导"""
        try:
            guide = self._generate_code_review_tool_guide()
            
            return {
                "success": True,
                "guide": guide,
                "agent_type": "EnhancedRealCodeReviewAgent",
                "include_examples": include_examples,
                "include_best_practices": include_best_practices,
                "total_tools": 7,  # EnhancedRealCodeReviewAgent有7个工具
                "message": "成功生成EnhancedRealCodeReviewAgent的工具使用指导"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 生成工具使用指导失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成工具使用指导时发生错误"
            }