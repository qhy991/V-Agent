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
            "tool_name": "generate_testbench",
            "parameters": {
                "module_name": "target_module",
                "code": "module target_module(...); endmodule",
                "test_scenarios": [
                    {"name": "basic_test", "description": "基本功能验证"},
                    {"name": "corner_test", "description": "边界条件测试"}
                ]
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
                "module_name": "target_module",
                "verilog_code": "module target_module(...); endmodule",
                "test_scenarios": [
                    {"name": "basic_test", "description": "基本功能验证"},
                    {"name": "corner_test", "description": "边界条件测试"}
                ]
            }
        }
    ]
}
```

🎯 **可用工具列表**:

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

### 3. generate_build_script
**必需参数**:
- `verilog_files` (array): Verilog文件列表（也可使用 `design_files`）
- `testbench_files` (array): 测试台文件列表
**可选参数**:
- `script_type` (string): "makefile", "bash", "tcl", "python"
- `build_options` (object): 构建选项配置

### 4. execute_build_script
**必需参数**:
- `script_name` (string): 脚本文件名
**可选参数**:
- `action` (string): "all", "compile", "simulate", "clean"
- `timeout` (integer): 超时时间(秒)

### 5. analyze_test_failures ⭐ **TDD专用**
**必需参数**:
- `design_code` (string): 需要分析的设计代码
**可选参数**:
- `compilation_errors` (string): 编译错误输出
- `simulation_errors` (string): 仿真错误输出
- `test_assertions` (string): 测试断言失败信息
- `testbench_code` (string): 测试台代码
- `iteration_number` (integer): 当前TDD迭代次数
- `previous_fixes` (array): 之前尝试的修复方法

### 6. write_file
**必需参数**:
- `filename` (string): 文件名
- `content` (string): 文件内容
**可选参数**:
- `description` (string): 文件描述

### 7. read_file
**必需参数**:
- `filepath` (string): 文件路径
**可选参数**:
- `encoding` (string): 文件编码，默认"utf-8"
- `test_assertions` (string): 测试断言失败信息
- `testbench_code` (string): 测试台代码
- `iteration_number` (integer): 当前TDD迭代次数
- `previous_fixes` (array): 之前尝试的修复方法

🎯 **使用建议**:
1. 优先使用简洁直观的字段名，如 `code` 而不是 `verilog_code`
2. 字段名称可以使用你习惯的方式，系统会智能适配
3. 不必担心参数格式错误，系统会自动修正
4. 专注于审查逻辑，让系统处理格式细节

⚠️ **重要提醒**:
- 只能调用上述列出的工具，不要尝试调用其他工具
- 如果任务需要接口验证或设计合规性检查，请使用现有的工具组合完成
- 不要调用 `verify_interface_compliance`、`validate_design_compliance` 等不存在的工具

📊 **推荐工作流程**:
收到代码审查任务时，建议流程：
1. 生成全面的测试台进行验证 (generate_testbench)
2. 执行仿真并分析结果 (run_simulation)
3. 生成构建脚本确保可重现性 (generate_build_script)
4. 提供详细的审查报告和建议

💡 **关键优势**: 现在你可以使用自然直观的参数格式，系统的智能适配层会确保与底层工具的完美兼容！

🎯 **重要提示 - 文件名传递**:
当使用多个工具时，请确保文件名的一致性：

1. **generate_testbench** 工具会返回 `testbench_filename` 字段
2. **run_simulation** 工具应使用该文件名，而不是硬编码的文件名
3. 示例：
```json
// 第一步：生成测试台
{
    "tool_name": "generate_testbench",
    "parameters": {
        "module_name": "adder_16bit",
        "verilog_code": "..."
    }
}

// 第二步：使用返回的文件名运行仿真
{
    "tool_name": "run_simulation", 
    "parameters": {
        "module_file": "adder_16bit.v",
        "testbench_file": "testbench_adder_16bit.v"  // 使用generate_testbench返回的文件名
    }
}
```

🎯 **重要提示 - 错误分析和修复**:
当工具执行失败时，请务必分析错误信息并采取相应措施：

1. **编译错误**：检查语法错误、模块引用、端口匹配等
2. **仿真错误**：检查测试台逻辑、信号连接、时序问题等
3. **功能错误**：检查设计逻辑、算法实现、边界条件等

**⚠️ 强制错误分析流程**：
当检测到仿真失败时，你必须按照以下步骤执行：

**第一步：必须分析错误**
```json
{
    "tool_name": "analyze_test_failures",
    "parameters": {
        "design_code": "模块代码",
        "compilation_errors": "编译错误信息",
        "simulation_errors": "仿真错误信息",
        "testbench_code": "测试台代码",
        "iteration_number": 当前迭代次数
    }
}
```

**第二步：根据分析结果修复代码**
- 如果分析显示测试台语法错误，必须重新生成测试台
- 如果分析显示设计代码问题，必须修改设计代码
- 如果分析显示配置问题，必须调整参数

**第三步：验证修复效果**
- 重新运行仿真验证修复是否成功
- 如果仍有问题，重复分析-修复-验证流程

**🎯 关键原则**：
1. **仿真失败时，必须先调用 analyze_test_failures 分析错误**
2. **根据分析结果，必须修改相应的代码（设计或测试台）**
3. **不要只是重新执行相同的工具，必须进行实际的代码修复**
4. **每次修复后都要验证效果，确保问题得到解决**

🎯 **重要提示 - 文件名传递**:
"""
        return base_prompt
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.VERIFICATION
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

确保测试台能够充分验证模块的所有功能，并使用标准Verilog语法。
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
                self.logger.error(f"❌ 测试台文件保存失败: {write_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": f"测试台文件保存失败: {write_result.get('error', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "module_name": module_name,
                "design_code": module_code,
                "design_filename": design_filename if design_saved else None,
                "design_file_path": design_write_result.get("file_path") if design_saved else None,
                "design_file_id": design_write_result.get("file_id") if design_saved else None,
                "testbench_code": response,
                "testbench_filename": tb_filename,  # 添加文件名信息
                "file_path": write_result.get("file_path"),
                "file_id": write_result.get("file_id"),
                "test_scenarios": test_scenarios,
                "simulation_config": {
                    "clock_period": clock_period,
                    "simulation_time": simulation_time,
                    "coverage_enabled": coverage_options.get('enable_coverage', False)
                },
                "message": f"✅ 成功生成测试台: {tb_filename}" + (f" 和设计代码: {design_filename}" if design_saved else "")
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
                "dependency_analysis": sim_result.get("dependency_analysis", {}),
                "error_message": sim_result.get("error", ""),  # 添加错误信息字段
                "compilation_errors": sim_result.get("compilation_output", ""),  # 添加编译错误字段
                "simulation_errors": sim_result.get("simulation_output", "")  # 添加仿真错误字段
            }
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"仿真执行异常: {str(e)}",
                "error_message": f"仿真执行异常: {str(e)}",
                "compilation_errors": "",
                "simulation_errors": "",
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
            "fix_suggestions": [],
            "error_patterns": {}
        }
        
        error_lines = errors.split('\n')
        
        # 分析SystemVerilog相关错误
        sv_errors = [line for line in error_lines if "SystemVerilog" in line]
        if sv_errors:
            analysis["failure_types"].append("SystemVerilog语法错误")
            analysis["root_causes"].append("使用了SystemVerilog特性但编译器不支持")
            analysis["fix_suggestions"].append("将SystemVerilog语法转换为标准Verilog语法")
            analysis["fix_suggestions"].append("检查task/function定义，确保符合Verilog标准")
            analysis["error_patterns"]["systemverilog"] = sv_errors
        
        # 分析语法错误
        syntax_errors = [line for line in error_lines if "syntax error" in line.lower()]
        if syntax_errors:
            analysis["failure_types"].append("语法错误")
            analysis["root_causes"].append("代码语法不符合Verilog标准")
            analysis["fix_suggestions"].append("检查括号匹配、分号使用、关键字拼写")
            analysis["error_patterns"]["syntax"] = syntax_errors
        
        # 分析语句错误
        statement_errors = [line for line in error_lines if "malformed statement" in line.lower()]
        if statement_errors:
            analysis["failure_types"].append("语句格式错误")
            analysis["root_causes"].append("语句结构不正确")
            analysis["fix_suggestions"].append("检查语句语法，确保正确的begin/end结构")
            analysis["error_patterns"]["statements"] = statement_errors
        
        # 分析循环错误
        loop_errors = [line for line in error_lines if "for loop" in line.lower() or "incomprehensible" in line.lower()]
        if loop_errors:
            analysis["failure_types"].append("循环结构错误")
            analysis["root_causes"].append("for循环语法不正确")
            analysis["fix_suggestions"].append("检查for循环的初始化、条件和增量表达式")
            analysis["error_patterns"]["loops"] = loop_errors
        
        # 分析赋值错误
        assignment_errors = [line for line in error_lines if "assignment statement" in line.lower()]
        if assignment_errors:
            analysis["failure_types"].append("赋值语句错误")
            analysis["root_causes"].append("赋值语句的左侧值不正确")
            analysis["fix_suggestions"].append("检查变量声明和赋值语句的语法")
            analysis["error_patterns"]["assignments"] = assignment_errors
        
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
            self.logger.warning(f"⚠️ 文件验证失败 {file_path}: {str(e)}")
            return False