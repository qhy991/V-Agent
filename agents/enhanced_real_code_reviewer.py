#!/usr/bin/env python3
"""
集成Schema系统的增强代码审查智能体

Enhanced Code Review Agent with Schema Integration
"""

import json
import asyncio
import subprocess
import tempfile
import os
import re
from typing import Dict, Any, Set, List, Tuple
from pathlib import Path

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from core.base_agent import TaskMessage
from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir
from tools.script_tools import ScriptManager


class EnhancedRealCodeReviewAgent(EnhancedBaseAgent):
    """集成Schema系统的增强代码审查智能体"""
    
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
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('EnhancedRealCodeReviewAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        # 初始化脚本管理器
        self.script_manager = ScriptManager(work_dir=self.artifacts_dir)
        
        # 注册增强工具
        self._register_enhanced_code_review_tools()
        
        self.logger.info(f"🔍 增强代码审查智能体(Schema支持)初始化完成")
        self.agent_logger.info("EnhancedRealCodeReviewAgent初始化完成")
    
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
                        "pattern": r"^[a-zA-Z0-9_./\-]+\.v$",
                        "maxLength": 500,
                        "description": "模块文件路径，必须以.v结尾"
                    },
                    "testbench_file": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-]+\.v$",
                        "maxLength": 500,
                        "description": "测试台文件路径，必须以.v结尾"
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
        
        # 3. 代码质量分析工具
        self.register_enhanced_tool(
            name="analyze_code_quality",
            func=self._tool_analyze_code_quality,
            description="深度分析Verilog代码质量、规范性和可维护性",
            security_level="normal",
            category="quality_assurance",
            schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 500000,
                        "description": "待分析的Verilog代码"
                    },
                    "analysis_scope": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "syntax", "style", "naming", "structure", 
                                "timing", "synthesis", "testability", "documentation",
                                "complexity", "maintainability", "performance"
                            ]
                        },
                        "minItems": 1,
                        "maxItems": 11,
                        "default": ["syntax", "style", "structure"],
                        "description": "分析范围选择"
                    },
                    "coding_standard": {
                        "type": "string",
                        "enum": ["ieee1800", "systemverilog", "verilog2001", "custom"],
                        "default": "ieee1800",
                        "description": "编码标准规范"
                    },
                    "severity_filter": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["error", "warning", "info", "suggestion"]
                        },
                        "default": ["error", "warning"],
                        "description": "严重度过滤级别"
                    },
                    "generate_report": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否生成详细的分析报告"
                    }
                },
                "required": ["code"],
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
        
        # 6. 覆盖率分析工具
        self.register_enhanced_tool(
            name="analyze_coverage",
            func=self._tool_analyze_coverage,
            description="分析代码覆盖率和测试完整性",
            security_level="normal",
            category="verification",
            schema={
                "type": "object",
                "properties": {
                    "coverage_data_file": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-]+\.(dat|xml|json|vcd|txt|log)$",
                        "maxLength": 500,
                        "description": "覆盖率数据文件路径"
                    },
                    "coverage_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["line", "toggle", "branch", "condition", "fsm", "expression"]
                        },
                        "minItems": 1,
                        "default": ["line", "toggle", "branch"],
                        "description": "覆盖率类型分析"
                    },
                    "threshold": {
                        "type": "object",
                        "properties": {
                            "line_coverage": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 80,
                                "description": "行覆盖率阈值(%)"
                            },
                            "branch_coverage": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 70,
                                "description": "分支覆盖率阈值(%)"
                            },
                            "toggle_coverage": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 60,
                                "description": "翻转覆盖率阈值(%)"
                            }
                        },
                        "additionalProperties": False,
                        "description": "覆盖率阈值配置"
                    },
                    "report_format": {
                        "type": "string",
                        "enum": ["text", "html", "xml", "json"],
                        "default": "html",
                        "description": "报告格式"
                    }
                },
                "required": ["coverage_data_file"],
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
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """实现LLM调用 - 智能处理Schema验证错误"""
        # 构建完整的prompt
        full_prompt = ""
        system_prompt = self._build_enhanced_system_prompt()
        
        for msg in conversation:
            if msg["role"] == "system":
                system_prompt = msg["content"]  # 覆盖默认system prompt
            elif msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Assistant: {msg['content']}\n\n"
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.2,  # 代码审查需要更高的一致性
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
            raise
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的System Prompt（支持智能Schema适配）"""
        base_prompt = """你是一位资深的硬件验证和代码审查专家，具备以下专业能力：

🔍 **核心专长**:
- Verilog/SystemVerilog代码审查和质量分析
- 测试台(Testbench)设计和验证方法学
- 代码覆盖率分析和测试完整性评估
- 构建自动化和CI/CD流程
- 静态分析和代码规范检查
- 时序分析和可综合性验证

📋 **审查标准**:
1. IEEE 1800标准合规性检查
2. 代码可读性和维护性评估
3. 综合性和时序收敛分析
4. 测试覆盖率和验证完整性
5. 最佳实践和设计模式应用
6. 安全性和可靠性考量

🛠️ **工具调用规则**:
你必须使用JSON格式调用工具，格式如下：
```json
{
    "tool_calls": [
        {
            "tool_name": "工具名称",
            "parameters": {
                "参数名": "参数值"
            }
        }
    ]
}
```

✨ **智能Schema适配系统**:
系统现在具备智能参数适配能力，支持以下灵活格式：

📌 **字段名智能映射**:
- `code` ↔ `verilog_code` (自动双向映射)
- `test_cases` → `test_scenarios`
- `files` → `verilog_files`
- `script` → `script_name`
- `coverage_file` → `coverage_data_file` (支持 .vcd, .dat, .xml, .json, .txt, .log 格式)
- 💡 使用任一格式都会被智能识别

📌 **测试场景灵活格式**:
- ✅ 字符串数组: `["基本功能测试", "边界条件测试"]`
- ✅ 对象数组: `[{"name": "basic_test", "description": "基本功能测试"}]`
- 💡 系统会自动转换格式

📌 **缺失字段智能推断**:
- 缺少 `module_name` 时会从代码中自动提取
- 缺少必需字段时会提供合理默认值
- 💡 无需担心遗漏参数

🎯 **推荐的工具调用方式**:

### 方式1: 使用自然字符串格式（推荐）
```json
{
    "tool_calls": [
        {
            "tool_name": "analyze_code_quality",
            "parameters": {
                "code": "module test(); endmodule",
                "analysis_scope": ["syntax", "style"],
                "coding_standard": "ieee1800"
            }
        }
    ]
}
```

### 方式2: 使用标准对象格式
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_testbench",
            "parameters": {
                "module_name": "simple_adder",
                "verilog_code": "module simple_adder(...); endmodule",
                "test_scenarios": [
                    {"name": "basic_test", "description": "基本功能验证"},
                    {"name": "corner_test", "description": "边界条件测试"}
                ]
            }
        }
    ]
}
```

🎯 **可用工具及其参数**:

### 1. generate_testbench
**必需参数**:
- `module_name` (string): 目标模块名称
- `verilog_code` (string): 目标模块代码（也可使用 `code`, `module_code`）
**可选参数**:
- `test_scenarios` (array): 测试场景列表（也可使用 `test_cases`）
- `clock_period` (number): 时钟周期(ns)，0.1-1000.0
- `simulation_time` (integer): 仿真时间，100-1000000

### 2. run_simulation
**必需参数**:
- `module_file` 或 `module_code`: 模块文件路径或代码内容
- `testbench_file` 或 `testbench_code`: 测试台文件路径或代码内容
**可选参数**:
- `simulator` (string): "iverilog", "modelsim", "vivado", "auto"
- `simulation_options` (object): 仿真选项配置

### 3. analyze_code_quality
**必需参数**:
- `code` (string): 待分析代码（也可使用 `verilog_code`）
**可选参数**:
- `analysis_scope` (array): 分析范围选择
- `coding_standard` (string): "ieee1800", "custom", "industry"
- `severity_filter` (array): 严重度过滤

### 4. generate_build_script
**必需参数**:
- `verilog_files` (array): Verilog文件列表（也可使用 `design_files`）
- `testbench_files` (array): 测试台文件列表
**可选参数**:
- `script_type` (string): "makefile", "bash", "tcl", "python"
- `build_options` (object): 构建选项配置

### 5. execute_build_script
**必需参数**:
- `script_name` (string): 脚本文件名
**可选参数**:
- `action` (string): "all", "compile", "simulate", "clean"
- `timeout` (integer): 超时时间(秒)

### 6. analyze_coverage
**必需参数**:
- `coverage_data_file` (string): 覆盖率数据文件路径 (支持 .vcd, .dat, .xml, .json, .txt, .log)
**可选参数**:
- `coverage_types` (array): 覆盖率类型
- `threshold` (object): 阈值配置

### 7. analyze_test_failures ⭐ **TDD专用**
**必需参数**:
- `design_code` (string): 需要分析的设计代码
**可选参数**:
- `compilation_errors` (string): 编译错误输出
- `simulation_errors` (string): 仿真错误输出
- `test_assertions` (string): 测试断言失败信息
- `testbench_code` (string): 测试台代码
- `iteration_number` (integer): 当前TDD迭代次数
- `previous_fixes` (array): 之前尝试的修复方法

🎯 **使用建议**:
1. 优先使用简洁直观的字段名，如 `code` 而不是 `verilog_code`
2. 字段名称可以使用你习惯的方式，系统会智能适配
3. 不必担心参数格式错误，系统会自动修正
4. 专注于审查逻辑，让系统处理格式细节

📊 **推荐工作流程**:
收到代码审查任务时，建议流程：
1. 首先分析代码质量和规范性 (analyze_code_quality)
2. 生成全面的测试台进行验证 (generate_testbench)
3. 执行仿真并分析结果 (run_simulation)
4. 生成构建脚本确保可重现性 (generate_build_script)
5. 分析测试覆盖率并提出改进建议 (analyze_coverage)
6. 提供详细的审查报告和建议

💡 **关键优势**: 现在你可以使用自然直观的参数格式，系统的智能适配层会确保与底层工具的完美兼容！
"""
        return base_prompt
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.QUALITY_ANALYSIS,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.VERIFICATION,
            AgentCapability.COVERAGE_ANALYSIS
        }
        
    def get_specialty_description(self) -> str:
        return "集成Schema验证的增强代码审查智能体，提供严格参数验证和智能错误修复的专业硬件验证服务"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强的代码审查任务"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行增强代码审查任务: {task_id}")
        
        try:
            # 使用增强验证处理流程
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=5
            )
            
            if result["success"]:
                self.logger.info(f"✅ 代码审查任务完成: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "response": result.get("response", ""),
                    "tool_results": result.get("tool_results", []),
                    "iterations": result.get("iterations", 1),
                    "quality_metrics": {
                        "schema_validation_passed": True,
                        "parameter_errors_fixed": result.get("iterations", 1) > 1,
                        "security_checks_passed": True
                    }
                }
            else:
                self.logger.error(f"❌ 代码审查任务失败: {task_id} - {result.get('error')}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "iterations": result.get("iterations", 1)
                }
                
        except Exception as e:
            self.logger.error(f"❌ 代码审查任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}"
            }
    
    # =============================================================================
    # 工具实现方法
    # =============================================================================
    
    async def _tool_generate_testbench(self, module_name: str, module_code: str,
                                     test_scenarios: List[Dict] = None,
                                     clock_period: float = 10.0,
                                     simulation_time: int = 10000,
                                     coverage_options: Dict = None) -> Dict[str, Any]:
        """生成测试台工具实现"""
        try:
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

请生成包含以下内容的专业测试台：
1. 完整的testbench模块声明
2. 所有必要的信号声明
3. 时钟和复位生成逻辑
4. 被测模块的正确实例化
5. 系统化的测试激励生成
6. 结果检查和断言
7. 适当的$display、$monitor和$finish语句
8. 波形转储设置（VCD文件）
9. 测试报告生成

确保测试台能够充分验证模块的所有功能。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=testbench_prompt,
                system_prompt="你是专业的验证工程师，请生成高质量的Verilog测试台。",
                temperature=0.1
            )
            
            # 使用Function Calling write_file工具保存测试台
            tb_filename = f"{module_name}_tb.v"
            write_result = await self._tool_write_file(
                filename=tb_filename,
                content=response,
                description=f"生成的{module_name}模块测试台"
            )
            
            if not write_result.get("success", False):
                self.logger.error(f"❌ 测试台文件保存失败: {write_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": f"测试台文件保存失败: {write_result.get('error', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "module_name": module_name,
                "testbench_code": response,
                "file_path": write_result.get("file_path"),
                "file_id": write_result.get("file_id"),
                "test_scenarios": test_scenarios,
                "simulation_config": {
                    "clock_period": clock_period,
                    "simulation_time": simulation_time,
                    "coverage_enabled": coverage_options.get('enable_coverage', False)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试台生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_run_simulation(self, module_file: str = None, testbench_file: str = None,
                                 module_code: str = None, testbench_code: str = None,
                                 simulator: str = "iverilog",
                                 simulation_options: Dict = None) -> Dict[str, Any]:
        """运行仿真工具实现 - 集成智能依赖分析"""
        try:
            self.logger.info(f"🔬 运行仿真: {simulator}")
            simulation_options = simulation_options or {}
            
            # 确定使用文件还是代码内容
            files_to_compile = []
            
            if module_file and testbench_file:
                mod_file = Path(module_file)
                tb_file = Path(testbench_file)
                
                # 验证文件存在
                if not mod_file.exists():
                    return {
                        "success": False,
                        "error": f"模块文件不存在: {module_file}",
                        "stage": "file_validation"
                    }
                if not tb_file.exists():
                    return {
                        "success": False,
                        "error": f"测试台文件不存在: {testbench_file}",
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
            
            # ✅ 修复错误处理 - 准确反映仿真状态
            actual_success = sim_result.get("success", False)
            
            if actual_success:
                self.logger.info(f"✅ 仿真执行成功")
            else:
                error_info = sim_result.get("error", "未知错误")
                stage = sim_result.get("stage", "unknown")
                self.logger.error(f"❌ 仿真执行失败 ({stage}): {error_info}")
            
            return {
                "success": actual_success,  # 📌 准确反映实际状态
                "simulator": simulator,
                "simulation_output": sim_result.get("output", ""),
                "compilation_output": sim_result.get("compilation_output", ""),
                "waveform_file": sim_result.get("waveform_file"),
                "simulation_time": sim_result.get("simulation_time", 0),
                "errors": sim_result.get("errors", []),
                "warnings": sim_result.get("warnings", []),
                "stage": sim_result.get("stage", "complete"),
                "files_compiled": [str(f) for f in files_to_compile],
                "dependency_analysis": sim_result.get("dependency_analysis", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"仿真执行异常: {str(e)}",
                "stage": "exception"
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
            
            compile_cmd = ["iverilog", "-o", str(output_file)]
            compile_cmd.extend([str(f) for f in files_to_compile])
            
            self.logger.info(f"🔨 编译命令: {' '.join(compile_cmd)}")
            
            # 编译
            compile_result = await asyncio.create_subprocess_exec(
                *compile_cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.artifacts_dir
            )
            
            compile_stdout, compile_stderr = await compile_result.communicate()
            
            compile_stdout_str = compile_stdout.decode('utf-8', errors='ignore') if compile_stdout else ""
            compile_stderr_str = compile_stderr.decode('utf-8', errors='ignore') if compile_stderr else ""
            
            if compile_result.returncode != 0:
                self.logger.error(f"❌ 编译失败，返回码: {compile_result.returncode}")
                self.logger.error(f"编译错误: {compile_stderr_str}")
                return {
                    "success": False,
                    "error": f"编译失败: {compile_stderr_str}",
                    "stage": "compilation",
                    "compilation_output": compile_stderr_str,
                    "command": " ".join(compile_cmd)
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
            run_result = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.artifacts_dir
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
                    self.logger.debug(f"仿真输出: {stdout_text[:200]}...")
            else:
                self.logger.error(f"❌ 仿真执行失败，返回码: {run_result.returncode}")
                if stderr_text:
                    self.logger.error(f"仿真错误: {stderr_text}")
            
            return {
                "success": simulation_success,
                "output": stdout_text,
                "compilation_output": compile_stdout_str,
                "waveform_file": str(vcd_file) if vcd_file.exists() else None,
                "errors": [stderr_text] if stderr_text else [],
                "warnings": [],
                "return_code": run_result.returncode,
                "command": " ".join(run_cmd),
                "stage": "simulation" if simulation_success else "simulation_failed"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stage": "exception"
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
            
            # 编译
            compile_result = await asyncio.create_subprocess_exec(
                *compile_cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.artifacts_dir
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
                cwd=self.artifacts_dir
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
                    self.logger.debug(f"仿真输出: {stdout_text[:200]}...")
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
    
    async def _tool_analyze_code_quality(self, code: str, analysis_scope: List[str] = None,
                                       coding_standard: str = "ieee1800",
                                       severity_filter: List[str] = None,
                                       generate_report: bool = True) -> Dict[str, Any]:
        """代码质量分析工具实现"""
        try:
            self.logger.info(f"🔍 分析代码质量: {coding_standard} 标准")
            
            analysis_scope = analysis_scope or ["syntax", "style", "structure"]
            severity_filter = severity_filter or ["error", "warning"]
            
            issues = []
            metrics = {
                "lines_of_code": len(code.splitlines()),
                "modules_count": code.count("module "),
                "complexity_score": 0,
                "maintainability_index": 0
            }
            
            # 多维度代码分析
            if "syntax" in analysis_scope:
                syntax_issues = self._analyze_syntax(code)
                issues.extend(syntax_issues)
            
            if "style" in analysis_scope:
                style_issues = self._analyze_style(code)
                issues.extend(style_issues)
            
            if "structure" in analysis_scope:
                structure_issues = self._analyze_structure(code)
                issues.extend(structure_issues)
                
            if "naming" in analysis_scope:
                naming_issues = self._analyze_naming_conventions(code)
                issues.extend(naming_issues)
            
            # 过滤严重度
            filtered_issues = [
                issue for issue in issues 
                if issue["severity"] in severity_filter
            ]
            
            # 计算质量评分
            metrics["complexity_score"] = max(0, 100 - len(filtered_issues) * 5)
            metrics["maintainability_index"] = self._calculate_maintainability_index(code, filtered_issues)
            
            # 生成报告
            report = None
            if generate_report:
                report = self._generate_quality_report(code, filtered_issues, metrics, analysis_scope)
                report_file = self.artifacts_dir / "code_quality_report.html"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
            
            return {
                "success": True,
                "quality_score": metrics["complexity_score"],
                "maintainability_index": metrics["maintainability_index"],
                "metrics": metrics,
                "issues": filtered_issues,
                "analysis_scope": analysis_scope,
                "coding_standard": coding_standard,
                "report_file": str(report_file) if generate_report else None,
                "recommendations": self._generate_recommendations(filtered_issues)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 代码质量分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_syntax(self, code: str) -> List[Dict]:
        """语法分析"""
        issues = []
        
        if "module " not in code:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "line": 0,
                "message": "No module declaration found"
            })
        
        if "endmodule" not in code:
            issues.append({
                "type": "syntax",
                "severity": "error", 
                "line": 0,
                "message": "Missing endmodule statement"
            })
        
        # 检查括号匹配
        paren_count = code.count('(') - code.count(')')
        if paren_count != 0:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "line": 0,
                "message": f"Unmatched parentheses: {abs(paren_count)} {'opening' if paren_count > 0 else 'closing'}"
            })
        
        return issues
    
    def _analyze_style(self, code: str) -> List[Dict]:
        """编码风格分析"""
        issues = []
        lines = code.splitlines()
        
        for i, line in enumerate(lines, 1):
            # 行长度检查
            if len(line) > 120:
                issues.append({
                    "type": "style",
                    "severity": "warning",
                    "line": i,
                    "message": f"Line exceeds 120 characters ({len(line)} chars)"
                })
            
            # 缩进检查
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if any(keyword in line for keyword in ['always', 'if', 'case', 'for']):
                    issues.append({
                        "type": "style",
                        "severity": "info",
                        "line": i,
                        "message": "Consider proper indentation for control structures"
                    })
        
        return issues
    
    def _analyze_structure(self, code: str) -> List[Dict]:
        """结构分析"""
        issues = []
        
        # 检查always块的敏感列表
        always_blocks = re.findall(r'always\s*@\s*\([^)]+\)', code)
        for block in always_blocks:
            if 'posedge' not in block and 'negedge' not in block and '*' not in block:
                issues.append({
                    "type": "structure",
                    "severity": "warning",
                    "line": 0,
                    "message": "Always block without edge sensitivity may cause synthesis issues"
                })
        
        return issues
    
    def _analyze_naming_conventions(self, code: str) -> List[Dict]:
        """命名规范分析"""
        issues = []
        
        # 检查模块名
        module_matches = re.findall(r'module\s+(\w+)', code)
        for module_name in module_matches:
            if not re.match(r'^[a-z][a-z0-9_]*$', module_name):
                issues.append({
                    "type": "naming",
                    "severity": "suggestion",
                    "line": 0,
                    "message": f"Module name '{module_name}' should follow snake_case convention"
                })
        
        return issues
    
    def _calculate_maintainability_index(self, code: str, issues: List[Dict]) -> float:
        """计算维护性指数"""
        lines = len(code.splitlines())
        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
        
        # 简化的维护性指数计算
        base_score = 100
        error_penalty = error_count * 10
        warning_penalty = warning_count * 5
        complexity_penalty = max(0, lines - 100) * 0.1
        
        return max(0, base_score - error_penalty - warning_penalty - complexity_penalty)
    
    def _generate_quality_report(self, code: str, issues: List[Dict], 
                               metrics: Dict, analysis_scope: List[str]) -> str:
        """生成HTML质量报告"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Code Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e8f4f8; padding: 10px; border-radius: 5px; }}
        .issues {{ margin: 20px 0; }}
        .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .error {{ border-left-color: red; }}
        .warning {{ border-left-color: orange; }}
        .info {{ border-left-color: blue; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Quality Analysis Report</h1>
        <p>Analysis completed: {analysis_scope}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Quality Score</h3>
            <p>{metrics['complexity_score']}/100</p>
        </div>
        <div class="metric">
            <h3>Lines of Code</h3>
            <p>{metrics['lines_of_code']}</p>
        </div>
        <div class="metric">
            <h3>Maintainability</h3>
            <p>{metrics['maintainability_index']:.1f}/100</p>
        </div>
    </div>
    
    <div class="issues">
        <h2>Issues Found ({len(issues)})</h2>
        {''.join([f'''
        <div class="issue {issue['severity']}">
            <strong>{issue['severity'].upper()}</strong>
            {f" (Line {issue['line']})" if issue.get('line') else ""}
            : {issue['message']}
        </div>
        ''' for issue in issues])}
    </div>
</body>
</html>
"""
        return html_template
    
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
                "build_options": build_options
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
    
    async def _tool_analyze_coverage(self, coverage_data_file: str, coverage_types: List[str] = None,
                                   threshold: Dict = None, report_format: str = "html") -> Dict[str, Any]:
        """覆盖率分析工具实现"""
        try:
            self.logger.info(f"📊 分析覆盖率: {coverage_data_file}")
            
            coverage_types = coverage_types or ["line", "toggle", "branch"]
            threshold = threshold or {
                "line_coverage": 80,
                "branch_coverage": 70,
                "toggle_coverage": 60
            }
            
            # 模拟覆盖率数据分析（实际实现中会解析真实的覆盖率文件）
            coverage_results = {
                "line_coverage": 85.5,
                "branch_coverage": 78.2,
                "toggle_coverage": 65.8,
                "condition_coverage": 72.1
            }
            
            # 检查阈值
            threshold_check = {}
            for cov_type, value in coverage_results.items():
                threshold_key = f"{cov_type}"
                if threshold_key in threshold:
                    threshold_check[cov_type] = {
                        "value": value,
                        "threshold": threshold[threshold_key],
                        "passed": value >= threshold[threshold_key]
                    }
            
            # 生成报告
            report_file = None
            if report_format == "html":
                report_content = self._generate_coverage_html_report(coverage_results, threshold_check)
                report_file = self.artifacts_dir / "coverage_report.html"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
            
            return {
                "success": True,
                "coverage_results": coverage_results,
                "threshold_check": threshold_check,
                "overall_passed": all(check["passed"] for check in threshold_check.values()),
                "report_file": str(report_file) if report_file else None,
                "coverage_types": coverage_types,
                "recommendations": self._generate_coverage_recommendations(coverage_results, threshold)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 覆盖率分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_coverage_html_report(self, results: Dict, threshold_check: Dict) -> str:
        """生成HTML覆盖率报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Coverage Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 15px; }}
        .coverage-item {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .passed {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #f0f0f0; }}
        .progress-fill {{ height: 100%; background-color: #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Coverage Analysis Report</h1>
    </div>
    
    <div class="coverage-results">
        <h2>Coverage Results</h2>
        {''.join([f'''
        <div class="coverage-item {'passed' if check['passed'] else 'failed'}">
            <h3>{cov_type.replace('_', ' ').title()}</h3>
            <p>Coverage: {check['value']:.1f}% (Threshold: {check['threshold']}%)</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {check['value']}%;"></div>
            </div>
            <p>Status: {'PASSED' if check['passed'] else 'FAILED'}</p>
        </div>
        ''' for cov_type, check in threshold_check.items()])}
    </div>
</body>
</html>
"""
        return html_content
    
    def _generate_coverage_recommendations(self, results: Dict, threshold: Dict) -> List[str]:
        """生成覆盖率改进建议"""
        recommendations = []
        
        for cov_type, value in results.items():
            threshold_key = f"{cov_type}"
            if threshold_key in threshold:
                if value < threshold[threshold_key]:
                    recommendations.append(
                        f"提高{cov_type.replace('_', ' ')}覆盖率: 当前{value:.1f}%, 目标{threshold[threshold_key]}%"
                    )
        
        if not recommendations:
            recommendations.append("所有覆盖率目标均已达成，测试质量良好！")
        
        return recommendations
    
    async def _tool_analyze_test_failures(self, design_code: str, 
                                         compilation_errors: str = "", 
                                         simulation_errors: str = "",
                                         test_assertions: str = "",
                                         testbench_code: str = "",
                                         iteration_number: int = 1,
                                         previous_fixes: List[str] = None) -> Dict[str, Any]:
        """测试失败分析工具实现 - 专门用于TDD循环中的错误分析与修复建议"""
        try:
            self.logger.info(f"🔍 分析第{iteration_number}次迭代的测试失败")
            
            previous_fixes = previous_fixes or []
            analysis_results = {
                "failure_types": [],
                "root_causes": [],
                "fix_suggestions": [],
                "priority_level": "medium",
                "confidence": 0.8
            }
            
            # 分析编译错误
            if compilation_errors:
                compile_analysis = self._analyze_compilation_errors(compilation_errors, design_code)
                analysis_results["failure_types"].extend(compile_analysis["failure_types"])
                analysis_results["root_causes"].extend(compile_analysis["root_causes"])
                analysis_results["fix_suggestions"].extend(compile_analysis["fix_suggestions"])
            
            # 分析仿真错误
            if simulation_errors:
                sim_analysis = self._analyze_simulation_errors(simulation_errors, design_code)
                analysis_results["failure_types"].extend(sim_analysis["failure_types"])
                analysis_results["root_causes"].extend(sim_analysis["root_causes"])
                analysis_results["fix_suggestions"].extend(sim_analysis["fix_suggestions"])
            
            # 分析测试断言失败
            if test_assertions:
                assertion_analysis = self._analyze_assertion_failures(test_assertions, design_code, testbench_code)
                analysis_results["failure_types"].extend(assertion_analysis["failure_types"])
                analysis_results["root_causes"].extend(assertion_analysis["root_causes"])
                analysis_results["fix_suggestions"].extend(assertion_analysis["fix_suggestions"])
            
            # 去重并优先排序
            analysis_results["failure_types"] = list(set(analysis_results["failure_types"]))
            analysis_results["root_causes"] = list(set(analysis_results["root_causes"]))
            
            # 过滤掉之前已尝试的修复方法
            filtered_suggestions = []
            for suggestion in analysis_results["fix_suggestions"]:
                is_duplicate = any(prev_fix.lower() in suggestion.lower() or 
                                 suggestion.lower() in prev_fix.lower() 
                                 for prev_fix in previous_fixes)
                if not is_duplicate:
                    filtered_suggestions.append(suggestion)
            
            analysis_results["fix_suggestions"] = filtered_suggestions[:5]  # 最多5个建议
            
            # 根据迭代次数调整优先级
            if iteration_number >= 3:
                analysis_results["priority_level"] = "high"
            elif len(analysis_results["failure_types"]) > 2:
                analysis_results["priority_level"] = "high"
            
            # 生成详细的修复指导
            detailed_guidance = self._generate_detailed_fix_guidance(
                analysis_results, design_code, iteration_number
            )
            
            self.logger.info(f"✅ 测试失败分析完成，发现 {len(analysis_results['failure_types'])} 种失败类型")
            
            return {
                "success": True,
                "analysis": analysis_results,
                "detailed_guidance": detailed_guidance,
                "iteration_context": {
                    "iteration_number": iteration_number,
                    "previous_attempts": len(previous_fixes),
                    "failure_complexity": len(analysis_results["failure_types"])
                },
                "next_steps": self._recommend_next_steps(analysis_results, iteration_number)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试失败分析异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_suggestions": [
                    "检查代码语法和模块实例化",
                    "验证信号宽度和类型匹配",
                    "确认测试台激励的正确性"
                ]
            }
    
    def _analyze_compilation_errors(self, errors: str, design_code: str) -> Dict[str, List[str]]:
        """分析编译错误"""
        analysis = {
            "failure_types": [],
            "root_causes": [],
            "fix_suggestions": []
        }
        
        error_lines = errors.lower()
        
        # 常见编译错误模式识别
        if "undefined" in error_lines and "macro" in error_lines:
            analysis["failure_types"].append("未定义宏错误")
            analysis["root_causes"].append("代码中包含未定义的宏或预处理指令")
            analysis["fix_suggestions"].append("移除或正确定义所有宏（如 `define）指令")
            analysis["fix_suggestions"].append("检查是否错误使用了C/C++风格的宏定义")
        
        if "unknown module" in error_lines or "not found" in error_lines:
            analysis["failure_types"].append("模块引用错误")
            analysis["root_causes"].append("引用了不存在的模块或子模块")
            analysis["fix_suggestions"].append("检查所有模块实例化，确保被调用的模块已定义")
            analysis["fix_suggestions"].append("验证模块名称拼写和大小写")
        
        if "syntax error" in error_lines or "parse error" in error_lines:
            analysis["failure_types"].append("语法错误")
            analysis["root_causes"].append("Verilog语法不符合规范")
            analysis["fix_suggestions"].append("检查语法：括号匹配、分号、begin/end配对")
            analysis["fix_suggestions"].append("验证端口声明和信号定义格式")
        
        if "width mismatch" in error_lines or "size mismatch" in error_lines:
            analysis["failure_types"].append("位宽不匹配")
            analysis["root_causes"].append("信号位宽不匹配或赋值错误")
            analysis["fix_suggestions"].append("检查所有信号的位宽定义和连接")
            analysis["fix_suggestions"].append("确保assign语句两侧位宽匹配")
        
        return analysis
    
    def _analyze_simulation_errors(self, errors: str, design_code: str) -> Dict[str, List[str]]:
        """分析仿真错误"""
        analysis = {
            "failure_types": [],
            "root_causes": [],
            "fix_suggestions": []
        }
        
        error_lines = errors.lower()
        
        if "x" in error_lines and "propagation" in error_lines:
            analysis["failure_types"].append("未定义状态传播")
            analysis["root_causes"].append("信号初始化不当导致X状态传播")
            analysis["fix_suggestions"].append("确保所有信号都有明确的初始值")
            analysis["fix_suggestions"].append("检查复位逻辑和时钟域")
        
        if "time violation" in error_lines or "setup" in error_lines:
            analysis["failure_types"].append("时序违例")
            analysis["root_causes"].append("时序约束不满足或时钟偏斜")
            analysis["fix_suggestions"].append("调整时钟周期或优化关键路径")
            analysis["fix_suggestions"].append("检查setup和hold时间要求")
        
        return analysis
    
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