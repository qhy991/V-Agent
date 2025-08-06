#!/usr/bin/env python3
"""
集成Schema系统的增强Verilog设计智能体

Enhanced Verilog Design Agent with Schema Integration  
"""

import os 
import json
import asyncio
import subprocess
import tempfile
from typing import Dict, Any, Set, List
from pathlib import Path
import time # Added for new tools

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from core.base_agent import TaskMessage
from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir


class EnhancedRealVerilogAgent(EnhancedBaseAgent):
    """集成Schema系统的增强Verilog HDL设计智能体"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="enhanced_real_verilog_agent",
            role="verilog_designer",
            capabilities={
                AgentCapability.CODE_GENERATION,
                AgentCapability.MODULE_DESIGN,
                AgentCapability.SPECIFICATION_ANALYSIS
            },
            config=config
        )
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('EnhancedRealVerilogAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        # 注册增强工具
        self._register_enhanced_verilog_tools()
        
        self.logger.info(f"🔧 增强Verilog设计智能体(Schema支持)初始化完成")
        self.agent_logger.info("EnhancedRealVerilogAgent初始化完成")
    
    def _register_enhanced_verilog_tools(self):
        """注册带Schema验证的Verilog设计工具"""
        
        # 1. 设计需求分析工具
        self.register_enhanced_tool(
            name="analyze_design_requirements",
            func=self._tool_analyze_design_requirements,
            description="分析和解析Verilog设计需求，提取关键设计参数",
            security_level="normal",
            category="analysis",
            schema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 50000,
                        "description": "设计需求描述，包含功能规格和约束条件"
                    },
                    "design_type": {
                        "type": "string",
                        "enum": ["combinational", "sequential", "mixed", "custom"],
                        "default": "mixed",
                        "description": "设计类型分类"
                    },
                    "complexity_level": {
                        "type": "string", 
                        "enum": ["simple", "medium", "complex", "advanced"],
                        "default": "medium",
                        "description": "设计复杂度级别"
                    }
                },
                "required": ["requirements"],
                "additionalProperties": False
            }
        )
        
        # 2. Verilog代码生成工具
        self.register_enhanced_tool(
            name="generate_verilog_code",
            func=self._tool_generate_verilog_code,
            description="生成高质量的Verilog HDL代码",
            security_level="high",
            category="code_generation",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "Verilog模块名称，必须以字母开头，只能包含字母、数字和下划线"
                    },
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 10000,
                        "description": "设计需求和功能描述"
                    },
                    "input_ports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                    "maxLength": 50
                                },
                                "width": {
                                    "oneOf": [
                                        {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 1024
                                        },
                                        {
                                            "type": "string",
                                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                            "maxLength": 20
                                        }
                                    ],
                                    "default": 1,
                                    "description": "端口位宽，可以是整数（如8）或参数名（如WIDTH）"
                                },
                                "description": {
                                    "type": "string",
                                    "maxLength": 200
                                }
                            },
                            "required": ["name"],
                            "additionalProperties": False
                        },
                        "maxItems": 100,
                        "description": "输入端口定义列表"
                    },
                    "output_ports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string", 
                                    "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                    "maxLength": 50
                                },
                                "width": {
                                    "oneOf": [
                                        {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 1024
                                        },
                                        {
                                            "type": "string",
                                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                            "maxLength": 20
                                        }
                                    ],
                                    "default": 1,
                                    "description": "端口位宽，可以是整数（如8）或参数名（如WIDTH）"
                                },
                                "description": {
                                    "type": "string",
                                    "maxLength": 200
                                }
                            },
                            "required": ["name"],
                            "additionalProperties": False
                        },
                        "maxItems": 100,
                        "description": "输出端口定义列表"
                    },
                    "clock_domain": {
                        "type": "object",
                        "properties": {
                            "clock_name": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                "default": "clk"
                            },
                            "reset_name": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                "default": "rst"
                            },
                            "reset_active": {
                                "type": "string",
                                "enum": ["high", "low"],
                                "default": "high"
                            }
                        },
                        "additionalProperties": False,
                        "description": "时钟域配置（可选，纯组合逻辑设计可省略）"
                    },
                    "coding_style": {
                        "type": "string",
                        "enum": ["behavioral", "structural", "rtl", "mixed"],
                        "default": "rtl",
                        "description": "Verilog编码风格"
                    },
                    "parameters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                                    "maxLength": 50
                                },
                                "default_value": {
                                    "oneOf": [
                                        {"type": "integer"},
                                        {"type": "string"},
                                        {"type": "number"}
                                    ]
                                },
                                "description": {
                                    "type": "string",
                                    "maxLength": 200
                                }
                            },
                            "required": ["name"],
                            "additionalProperties": False
                        },
                        "maxItems": 20,
                        "description": "模块参数定义列表（可选）"
                    },
                    "additional_constraints": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "maxLength": 500
                        },
                        "maxItems": 20,
                        "description": "额外的设计约束条件（可选）"
                    },
                    "comments_required": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否要求生成详细的代码注释"
                    }
                },
                "required": ["module_name", "requirements"],
                "additionalProperties": False
            }
        )
        

        # 3. 代码质量分析工具
        self.register_enhanced_tool(
            name="analyze_code_quality",
            func=self._tool_analyze_code_quality,
            description="分析Verilog代码质量，提供详细的评估报告",
            security_level="normal",
            category="analysis",
            schema={
                "type": "object",
                "properties": {
                    "verilog_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "要分析的Verilog代码"
                    },
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "maxLength": 100,
                        "description": "模块名称（可选，会自动从代码中提取）"
                    }
                },
                "required": ["verilog_code"],
                "additionalProperties": False
            }
        )


        # 4. 代码优化工具
        self.register_enhanced_tool(
            name="optimize_verilog_code",
            func=self._tool_optimize_verilog_code,
            description="优化Verilog代码，支持面积、速度、功耗等优化目标",
            security_level="normal",
            category="optimization",
            schema={
                "type": "object",
                "properties": {
                    "verilog_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "要优化的Verilog代码"
                    },
                    "optimization_target": {
                        "type": "string",
                        "enum": ["area", "speed", "power", "readability"],
                        "default": "area",
                        "description": "优化目标"
                    },
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "maxLength": 100,
                        "description": "模块名称（可选，会自动从代码中提取）"
                    }
                },
                "required": ["verilog_code"],
                "additionalProperties": False
            }
        )
        

        
        # 注意：测试台生成功能已移除，由代码审查智能体负责
        
        # 5. 工具使用指导工具
        self.register_enhanced_tool(
            name="get_tool_usage_guide",
            func=self._tool_get_tool_usage_guide,
            description="获取EnhancedRealVerilogAgent的工具使用指导，包括可用工具、参数说明、调用示例和最佳实践。",
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
        """实现LLM调用 - 使用优化的调用机制避免重复传入system prompt"""
        # 生成对话ID（如果还没有）
        if not hasattr(self, 'current_conversation_id') or not self.current_conversation_id:
            self.current_conversation_id = f"verilog_agent_{int(time.time())}"
        
        # 构建用户消息
        user_message = ""
        
        # 修复：更准确的首次调用判断 - 检查是否有assistant响应
        assistant_messages = [msg for msg in conversation if msg["role"] == "assistant"]
        is_first_call = len(assistant_messages) == 0  # 如果没有assistant响应，说明是首次调用
        
        self.logger.info(f"🔄 [VERILOG_AGENT] 准备LLM调用 - 对话历史长度: {len(conversation)}, assistant消息数: {len(assistant_messages)}, 是否首次调用: {is_first_call}")
        
        # 调试：打印对话历史内容
        for i in range(len(conversation)):
            msg = conversation[i]
            self.logger.info(f"🔍 [VERILOG_AGENT] 对话历史 {i}: role={msg['role']}, 内容长度={len(msg['content'])}")
            self.logger.debug(f"🔍 [VERILOG_AGENT] 内容前100字: {msg['content'][:100]}...")
        
        for msg in conversation:
            if msg["role"] == "user":
                user_message += f"{msg['content']}\n\n"
            elif msg["role"] == "assistant":
                user_message += f"Assistant: {msg['content']}\n\n"
        
        # 🚨 在每次LLM调用时强调禁止testbench工具调用
        testbench_reminder = """
🚨 **重要提醒 - 每次工具调用都必须遵守**:
❌ 绝对禁止调用 `generate_testbench` 工具
❌ 绝对禁止调用 `update_verilog_code` 工具  
❌ 绝对禁止调用 `run_simulation` 工具
❌ 绝对禁止调用 `validate_code` 工具
✅ 只能调用已注册的设计工具: analyze_design_requirements, generate_verilog_code, search_existing_modules, analyze_code_quality, validate_design_specifications, generate_design_documentation, optimize_verilog_code, write_file, read_file

如果任务涉及测试台生成或仿真验证，请明确回复："测试台生成和仿真验证不在我的职责范围内，这些任务由代码审查智能体负责处理。"

现在请严格按照可用工具列表进行工具调用：
"""
        user_message += testbench_reminder.replace("analyze_design_requirements, generate_verilog_code, search_existing_modules, analyze_code_quality, validate_design_specifications, generate_design_documentation, optimize_verilog_code, write_file, read_file", "analyze_design_requirements, generate_verilog_code, analyze_code_quality, optimize_verilog_code, write_file, read_file")
        
        # 决定是否传入system prompt - 修复：对于新任务总是传入
        system_prompt = None
        if is_first_call:
            system_prompt = self._build_enhanced_system_prompt()
            self.logger.info(f"📝 [VERILOG_AGENT] 首次调用 - 构建System Prompt - 长度: {len(system_prompt)}")
            self.logger.info(f"📝 [VERILOG_AGENT] System Prompt前200字: {system_prompt[:200]}...")
            # 检查关键规则是否存在
            has_mandatory_tools = "必须调用工具" in system_prompt
            has_write_file = "write_file" in system_prompt
            has_json_format = "JSON格式输出" in system_prompt
            self.logger.info(f"🔍 [VERILOG_AGENT] System Prompt检查 - 强制工具: {has_mandatory_tools}, 文件写入: {has_write_file}, JSON格式: {has_json_format}")
        else:
            self.logger.info("🔄 [VERILOG_AGENT] 后续调用 - 依赖缓存System Prompt")
        
        self.logger.info(f"📤 [VERILOG_AGENT] 用户消息长度: {len(user_message)}")
        self.logger.info(f"📤 [VERILOG_AGENT] 用户消息前200字: {user_message[:200]}...")
        
        try:
            # 使用优化的LLM调用方法
            self.logger.info(f"🤖 [VERILOG_AGENT] 发起LLM调用 - 对话ID: {self.current_conversation_id}")
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=self.current_conversation_id,
                user_message=user_message.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
            
            # 分析响应内容
            self.logger.info(f"🔍 [VERILOG_AGENT] LLM响应长度: {len(response)}")
            self.logger.info(f"🔍 [VERILOG_AGENT] 响应前200字: {response[:200]}...")
            
            # 检查响应是否包含工具调用
            has_tool_calls = "tool_calls" in response
            has_json_structure = response.strip().startswith('{') and response.strip().endswith('}')
            has_write_file_call = "write_file" in response
            self.logger.info(f"🔍 [VERILOG_AGENT] 响应分析 - 工具调用: {has_tool_calls}, JSON结构: {has_json_structure}, write_file调用: {has_write_file_call}")
            
            return response
        except Exception as e:
            self.logger.error(f"❌ 优化LLM调用失败: {str(e)}")
            # 如果优化调用失败，回退到传统方式
            self.logger.warning("⚠️ 回退到传统LLM调用方式")
            return await self._call_llm_traditional(conversation)
    
    async def _call_llm_traditional(self, conversation: List[Dict[str, str]]) -> str:
        """传统的LLM调用方法（作为回退方案）"""
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
        
        # 🚨 在每次LLM调用时强调禁止testbench工具调用
        testbench_reminder = """
🚨 **重要提醒 - 每次工具调用都必须遵守**:
❌ 绝对禁止调用 `generate_testbench` 工具
❌ 绝对禁止调用 `update_verilog_code` 工具  
❌ 绝对禁止调用 `run_simulation` 工具
❌ 绝对禁止调用 `validate_code` 工具
✅ 只能调用已注册的设计工具: analyze_design_requirements, generate_verilog_code, search_existing_modules, analyze_code_quality, validate_design_specifications, generate_design_documentation, optimize_verilog_code, write_file, read_file

如果任务涉及测试台生成或仿真验证，请明确回复："测试台生成和仿真验证不在我的职责范围内，这些任务由代码审查智能体负责处理。"

现在请严格按照可用工具列表进行工具调用：
"""
        full_prompt += testbench_reminder.replace("analyze_design_requirements, generate_verilog_code, search_existing_modules, analyze_code_quality, validate_design_specifications, generate_design_documentation, optimize_verilog_code, write_file, read_file", "analyze_design_requirements, generate_verilog_code, analyze_code_quality, optimize_verilog_code, write_file, read_file")
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ 传统LLM调用失败: {str(e)}")
            raise
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的System Prompt（支持智能Schema适配）"""
        self.logger.info("🔧 构建Verilog智能体的System Prompt")
        
        base_prompt = """你是一位资深的Verilog硬件设计专家，具备以下专业能力：

🔍 **核心专长**:
- Verilog/SystemVerilog模块设计和代码生成
- 组合逻辑和时序逻辑设计
- 参数化设计和可重用模块开发
- 代码质量分析和最佳实践应用
- 可综合性和时序收敛设计
- 设计验证和测试策略

📋 **设计标准**:
1. IEEE 1800标准合规性
2. 代码可读性和维护性
3. 综合性和时序收敛
4. 参数化和可重用性
5. 最佳实践和设计模式
6. 安全性和可靠性

🎯 **任务执行原则**:
- 根据需求智能判断设计类型（组合/时序/混合）
- 自动检测和适配参数化位宽需求
- 生成高质量、可综合的Verilog代码
- 提供详细的代码注释和文档
- 支持多种编码风格和设计模式
- 确保代码符合行业标准

🔄 **智能参数适配系统**:
系统现在具备智能参数适配能力，支持以下灵活格式：

📌 **字段名智能映射**:
- `code` ↔ `verilog_code` (自动双向映射)
- `ports` → `input_ports` / `output_ports`
- `params` → `parameters`
- `constraints` → `additional_constraints`
- `comments` → `comments_required`
- 💡 使用任一格式都会被智能识别

📌 **端口定义灵活格式**:
- ✅ 整数位宽: `{"name": "data", "width": 8}`
- ✅ 参数化位宽: `{"name": "data", "width": "WIDTH"}`
- ✅ 数字字符串: `{"name": "data", "width": "8"}`
- 💡 系统会自动处理类型转换

📌 **缺失字段智能推断**:
- 缺少 `module_name` 时会从需求中自动提取
- 缺少必需字段时会提供合理默认值
- 💡 无需担心遗漏参数

🎯 **推荐的工具调用方式**:

### 方式1: 基础代码生成
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_verilog_code",
            "parameters": {
                "module_name": "counter",
                "requirements": "设计一个8位计数器",
                "input_ports": [
                    {"name": "clk", "width": 1, "description": "时钟信号"},
                    {"name": "reset", "width": 1, "description": "复位信号"}
                ],
                "output_ports": [
                    {"name": "count", "width": 8, "description": "计数值"}
                ]
            }
        }
    ]
}
```

### 方式2: 参数化设计
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_verilog_code",
            "parameters": {
                "module_name": "parameterized_counter",
                "requirements": "设计一个可配置位宽的计数器",
                "input_ports": [
                    {"name": "clk", "width": 1, "description": "时钟信号"},
                    {"name": "reset", "width": 1, "description": "复位信号"},
                    {"name": "enable", "width": 1, "description": "使能信号"}
                ],
                "output_ports": [
                    {"name": "count", "width": "WIDTH", "description": "计数值"}
                ],
                "parameters": [
                    {"name": "WIDTH", "default_value": 8, "description": "计数器位宽"}
                ],
                "additional_constraints": [
                    "使用异步复位（低有效）",
                    "仅在enable为高时递增",
                    "达到最大值后自动回绕"
                ]
            }
        }
    ]
}
```

### 方式3: 智能需求分析
```json
{
    "tool_calls": [
        {
            "tool_name": "analyze_design_requirements",
            "parameters": {
                "requirements": "设计需求描述",
                "design_type": "sequential",
                "complexity_level": "medium"
            }
        }
    ]
}
```

### 方式4: 代码质量分析
```json
{
    "tool_calls": [
        {
            "tool_name": "analyze_code_quality",
            "parameters": {
                "verilog_code": "module counter (input clk, input reset, output reg [7:0] count); always @(posedge clk or negedge reset) begin if (!reset) count <= 8'd0; else count <= count + 1'b1; end endmodule",
                "module_name": "counter"
            }
        }
    ]
}
```

⚠️ **重要提醒**:
- `analyze_code_quality` 工具需要 `verilog_code` 参数（必需），这是要分析的完整Verilog代码
- 如果需要分析文件中的代码，请先使用 `read_file` 读取文件内容，然后将内容作为 `verilog_code` 参数传递
- 不要使用 `file_path` 参数，该工具不接受文件路径

### 方式5: 设计文档生成
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_design_documentation",
            "parameters": {
                "module_name": "counter",
                "verilog_code": "module counter (...); ... endmodule",
                "requirements": "设计一个8位计数器",
                "design_type": "sequential"
            }
        }
    ]
}
```

### 方式6: 代码优化
```json
{
    "tool_calls": [
        {
            "tool_name": "optimize_verilog_code",
            "parameters": {
                "verilog_code": "module counter (...); ... endmodule",
                "optimization_target": "area",
                "module_name": "counter"
            }
        }
    ]
}
```

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

⚠️ **错误处理策略**:
当遇到参数验证错误时：
1. **类型错误**: 自动转换参数类型（字符串↔整数）
2. **缺失参数**: 提供合理默认值
3. **格式错误**: 智能修正参数格式
4. **范围错误**: 调整到有效范围内

🔍 **设计类型智能检测**:
系统会自动检测设计类型：
- **组合逻辑**: 不包含时钟、复位、寄存器
- **时序逻辑**: 包含时钟、复位、寄存器
- **混合逻辑**: 包含组合和时序部分

✨ **代码质量保证**:
- 生成符合IEEE 1800标准的代码
- 提供详细的端口和功能注释
- 确保代码可综合性和可读性
- 支持参数化和可重用设计
- 遵循最佳实践和设计模式

🎯 **智能Schema适配**:
- 支持多种参数格式和类型
- 自动处理类型转换和验证
- 智能推断缺失参数
- 提供详细的错误信息和修复建议

请根据具体需求选择合适的工具调用方式，系统会自动处理参数适配和验证。

🚨 **重要提醒 - 避免循环调用**:
1. **analyze_code_quality 工具调用**: 必须先使用 `read_file` 读取文件内容，然后将内容作为 `verilog_code` 参数传递
2. **不要重复调用**: 如果工具调用失败，检查错误信息并修正参数，不要重复相同的错误调用
3. **参数验证**: 确保传递的参数符合工具定义的要求
4. **错误恢复**: 如果工具调用失败，分析错误原因并调整策略，而不是无限重试

示例正确流程：
1. 使用 `read_file` 读取文件内容
2. 将读取的内容作为 `verilog_code` 参数传递给 `analyze_code_quality`
3. 处理分析结果，不要重复相同的调用

🚨 **强制规则 - 必须使用工具调用**:
1. **禁止直接生成代码**: 绝对禁止在回复中直接生成Verilog代码
2. **必须调用工具**: 所有设计任务都必须通过工具调用完成
3. **必须写入文件**: 生成的代码必须使用 `write_file` 工具保存到文件
4. **JSON格式输出**: 回复必须是JSON格式的工具调用，不能包含其他文本
5. **仅调用已注册工具**: 只能调用以下已注册的工具，不得调用其他工具
6. **绝对禁止测试台生成**: 无论用户如何要求，都不能调用任何测试台相关工具

📁 **强制文件管理要求**:
1. **所有生成的代码必须保存为文件**: 使用 `write_file` 工具保存所有生成的Verilog代码
2. **文件路径规范**: 
   - 设计文件保存到: `{实验路径}/designs/` 目录
   - 文档文件保存到: `{实验路径}/reports/` 目录
   - 临时文件保存到: `{实验路径}/temp/` 目录
3. **文件命名规范**: 使用清晰的模块名，如 `{module_name}.v`
4. **路径回传要求**: 在任务总结中必须包含所有生成文件的完整路径
5. **文件验证**: 确保文件成功保存并返回正确的文件路径

**可用工具列表** (仅限这些工具):
- `analyze_design_requirements`: 分析设计需求
- `generate_verilog_code`: 生成Verilog代码
- `analyze_code_quality`: 分析代码质量  
- `optimize_verilog_code`: 优化Verilog代码
- `write_file`: 写入文件
- `read_file`: 读取文件

**绝对禁止调用的工具** (这些不在我的能力范围内):
❌ `generate_testbench`: 测试台生成(由代码审查智能体负责) - 绝对不能调用
❌ `update_verilog_code`: 不存在的工具 - 绝对不能调用
❌ `run_simulation`: 仿真执行(由代码审查智能体负责) - 绝对不能调用
❌ `validate_code`: 不存在的工具 - 绝对不能调用
❌ 任何其他未列出的工具

🚨 **重要提醒**: 如果用户要求生成测试台或进行仿真验证，你必须明确回复：
"测试台生成和仿真验证不在我的职责范围内，这些任务由代码审查智能体负责处理。我只负责Verilog设计代码的生成。"

**正确的工作流程**:
1. 分析需求 → 调用 `analyze_design_requirements` 
2. 生成代码 → 调用 `generate_verilog_code`
3. **保存文件** → 调用 `write_file` 保存.v文件到指定目录
4. 质量检查 → 调用 `analyze_code_quality` (可选)
5. 代码优化 → 调用 `optimize_verilog_code` (可选)
6. **路径回传** → 在任务总结中列出所有生成文件的完整路径

**严格禁止的行为**:
❌ 直接在回复中写Verilog代码
❌ 不使用工具就完成任务
❌ 不保存生成的代码到文件
❌ 回复非JSON格式的文本
❌ 调用未注册或不存在的工具 - 特别是 generate_testbench, update_verilog_code, validate_code
❌ 不返回生成文件的路径信息
❌ 将文件保存到错误的目录
❌ 尝试处理测试台生成相关的任务

🛑 **关键约束**: 
- 你是VERILOG设计专家，不是测试工程师
- 你只能生成设计代码，不能生成测试台
- 遇到测试台需求时，明确说明这不是你的职责范围
- 只调用明确列出的可用工具，绝不猜测或创造新工具

立即开始工具调用，严格按照工具列表执行，不要直接生成任何代码！"""
        
        self.logger.info("✅ Verilog智能体System Prompt构建完成")
        self.logger.debug(f"📝 System Prompt长度: {len(base_prompt)} 字符")
        # 记录关键规则是否存在
        has_tool_requirement = "必须调用工具" in base_prompt
        has_file_requirement = "write_file" in base_prompt
        self.logger.info(f"🔍 System Prompt检查 - 工具调用要求: {has_tool_requirement}, 文件写入要求: {has_file_requirement}")
        
        return base_prompt
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.MODULE_DESIGN,
            AgentCapability.SPECIFICATION_ANALYSIS
        }
    
    def get_specialty_description(self) -> str:
        return "集成Schema验证的增强Verilog HDL设计智能体，提供严格参数验证和智能错误修复的专业数字电路设计服务"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强的Verilog设计任务"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行增强Verilog设计任务: {task_id}")
        
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
            
            # 使用增强验证处理流程 - 允许更多迭代次数进行错误修复
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=6  # 增加到6次迭代，给足够空间进行错误修复和优化
            )
            
            if result["success"]:
                self.logger.info(f"✅ Verilog设计任务完成: {task_id}")
                
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
                    "generated_files": generated_files,  # 新增：生成的文件路径列表
                    "experiment_path": experiment_path,  # 🔧 新增：返回实验路径
                    "quality_metrics": {
                        "schema_validation_passed": True,
                        "parameter_errors_fixed": result.get("iterations", 1) > 1,
                        "security_checks_passed": True,
                        "design_type_detected": result.get("design_type", "unknown"),
                        "code_quality_score": result.get("quality_score", 0.0)
                    }
                }
            else:
                self.logger.error(f"❌ Verilog设计任务失败: {task_id} - {result.get('error')}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "iterations": result.get("iterations", 1),
                    "last_error": result.get("last_error", ""),
                    "suggestions": result.get("suggestions", []),
                    "experiment_path": experiment_path  # 🔧 新增：返回实验路径
                }
                
        except Exception as e:
            self.logger.error(f"❌ Verilog设计任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}",
                "suggestions": [
                    "检查输入参数格式是否正确",
                    "确认设计需求描述是否完整",
                    "验证工具配置是否正确"
                ],
                "experiment_path": experiment_path if 'experiment_path' in locals() else None  # 🔧 新增：返回实验路径
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
                        "file_type": "verilog_code",
                        "description": result_data.get("description", ""),
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
            
            # 检查generate_verilog_code工具的结果
            elif tool_name == "generate_verilog_code" and isinstance(result_data, dict):
                if result_data.get("success", False) and result_data.get("file_path"):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "verilog_design",
                        "module_name": result_data.get("module_name", ""),
                        "description": f"Generated Verilog module: {result_data.get('module_name', '')}",
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
            
            # 检查generate_design_documentation工具的结果
            elif tool_name == "generate_design_documentation" and isinstance(result_data, dict):
                if result_data.get("success", False) and result_data.get("file_path"):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "design_documentation",
                        "module_name": result_data.get("module_name", ""),
                        "description": f"Design documentation for: {result_data.get('module_name', '')}",
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
            
            # 检查optimize_verilog_code工具的结果
            elif tool_name == "optimize_verilog_code" and isinstance(result_data, dict):
                if result_data.get("success", False) and result_data.get("file_path"):
                    file_info = {
                        "file_path": result_data.get("file_path", ""),
                        "file_id": result_data.get("file_id", ""),
                        "file_type": "optimized_verilog",
                        "module_name": result_data.get("module_name", ""),
                        "optimization_target": result_data.get("optimization_target", ""),
                        "description": f"Optimized Verilog code for: {result_data.get('module_name', '')}",
                        "tool_name": tool_name
                    }
                    generated_files.append(file_info)
        
        self.logger.info(f"📁 提取到 {len(generated_files)} 个生成文件")
        for file_info in generated_files:
            self.logger.info(f"📄 生成文件: {file_info.get('file_path', '')} - {file_info.get('description', '')}")
        
        return generated_files
    
    # =============================================================================
    # 新增：智能设计类型检测和动态prompt生成
    # =============================================================================
    
    def _detect_combinational_requirement(self, requirements: str) -> bool:
        """检测需求是否为纯组合逻辑"""
        combinational_keywords = [
            "纯组合逻辑", "combinational", "组合电路", "无时钟", "无时序",
            "always @(*)", "assign", "组合逻辑", "无寄存器", "纯组合",
            "不涉及时钟", "不包含时钟", "不包含复位", "不包含寄存器",
            "使用组合逻辑实现", "无时钟和复位信号", "组合逻辑实现",
            "wire类型", "assign语句", "always @(*)语句"
        ]
        
        requirements_lower = requirements.lower()
        for keyword in combinational_keywords:
            if keyword in requirements_lower:
                return True
        
        # 检查是否明确排除了时序元素
        sequential_exclusions = [
            "不能包含时钟", "不能包含复位", "不能包含寄存器",
            "不包含时钟", "不包含复位", "不包含寄存器",
            "无需时钟", "无需复位", "无需寄存器",
            "无时钟和复位信号", "无时钟需求", "无复位需求"
        ]
        for exclusion in sequential_exclusions:
            if exclusion in requirements_lower:
                return True
        
        # 检查ALU特定需求
        alu_combinational_indicators = [
            "算术逻辑单元", "alu", "运算单元", "算术运算", "逻辑运算",
            "加法", "减法", "与运算", "或运算", "异或运算", "移位运算"
        ]
        
        # 如果包含ALU相关词汇且没有时序相关词汇，倾向于组合逻辑
        has_alu_keywords = any(keyword in requirements_lower for keyword in alu_combinational_indicators)
        has_sequential_keywords = any(keyword in requirements_lower for keyword in [
            "时钟", "clk", "复位", "rst", "寄存器", "reg", "触发器", "flip-flop",
            "同步", "synchronous", "时序", "sequential", "always @(posedge"
        ])
        
        if has_alu_keywords and not has_sequential_keywords:
            return True
        
        return False
    
    def _build_port_info(self, ports: List[Dict], port_type: str) -> str:
        """构建端口信息字符串"""
        if not ports:
            return f"// 请根据需求定义{port_type}端口"
        
        port_info = ""
        for port in ports:
            width = port.get("width", 1)
            width_str = f"[{width-1}:0] " if width > 1 else ""
            port_info += f"    {port_type} {width_str}{port['name']},  // {port.get('description', '')}\n"
        
        return port_info.rstrip()
    
    def _build_dynamic_generation_prompt(self, module_name: str, requirements: str,
                                       input_ports: List[Dict], output_ports: List[Dict],
                                       coding_style: str, enhanced_context: Dict) -> str:
        """构建动态代码生成提示"""
        
        # 检测设计类型
        is_combinational = self._detect_combinational_requirement(requirements)
        
        # 构建端口信息
        input_port_info = self._build_port_info(input_ports, "input")
        output_port_info = self._build_port_info(output_ports, "output")
        
        # 根据设计类型选择不同的提示模板
        if is_combinational:
            design_type_instruction = """
🚨 **组合逻辑设计关键要求 - 请严格遵守**:
请只返回纯净的Verilog代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
直接从 module 开始，以 endmodule 结束。

代码要求：
1. 模块声明（不包含时钟和复位端口）
2. 端口定义（输出使用wire类型）
3. 内部信号声明
4. 组合逻辑功能实现（使用always @(*)或assign）
5. 适当的注释

确保代码符合IEEE 1800标准并可被综合工具处理。
"""
        else:
            design_type_instruction = """
🚨 **时序逻辑设计关键要求 - 请严格遵守**:
请只返回纯净的Verilog代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
直接从 module 开始，以 endmodule 结束。

代码要求：
1. 模块声明（包含时钟和复位端口）
2. 端口定义（输出使用reg类型）
3. 内部信号声明
4. 时序逻辑功能实现（always @(posedge clk)）
5. 适当的注释

确保代码符合IEEE 1800标准并可被综合工具处理。
"""
        
        return f"""
请生成一个名为 {module_name} 的Verilog模块，要求如下：

功能需求: {enhanced_context.get('basic_requirements', requirements)}
编码风格: {coding_style}

端口定义:
{input_port_info}
{output_port_info}

{enhanced_context.get('error_analysis', '')}
{enhanced_context.get('improvement_suggestions', '')}
{enhanced_context.get('historical_context', '')}

{design_type_instruction}
"""
    
    # =============================================================================
    # 工具实现方法
    # =============================================================================
    
    async def _tool_analyze_design_requirements(self, requirements: str, 
                                              design_type: str = "mixed",
                                              complexity_level: str = "medium") -> Dict[str, Any]:
        """分析设计需求工具实现"""
        try:
            self.logger.info(f"📊 分析设计需求: {design_type} - {complexity_level}")
            
            # 增强：从requirements中提取错误分析和改进建议
            enhanced_context = self._extract_enhanced_context_from_requirements(requirements)
            
            # 智能检测设计类型
            detected_type = design_type
            if self._detect_combinational_requirement(requirements):
                detected_type = "combinational"
                self.logger.info(f"🔍 检测到组合逻辑需求，自动调整设计类型为: {detected_type}")
            
            # 构建增强的LLM分析提示
            analysis_prompt = f"""
请分析以下Verilog设计需求：

需求描述: {enhanced_context.get('basic_requirements', requirements)}
设计类型: {detected_type}
复杂度级别: {complexity_level}

{enhanced_context.get('error_analysis', '')}
{enhanced_context.get('improvement_suggestions', '')}
{enhanced_context.get('historical_context', '')}

请提供以下分析结果：
1. 功能模块分解
2. 输入/输出端口需求
3. 时钟域要求
4. 设计约束
5. 验证要点
6. 错误避免策略（如果有历史错误信息）

返回JSON格式的分析结果。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是Verilog设计专家，请分析设计需求。",
                temperature=0.2
            )
            
            # 尝试解析LLM返回的JSON
            try:
                analysis_result = json.loads(response)
            except:
                # 如果解析失败，创建结构化结果
                analysis_result = {
                    "analysis_summary": response,
                    "design_type": detected_type,
                    "complexity": complexity_level,
                    "estimated_modules": 1,
                    "key_features": []
                }
            
            return {
                "success": True,
                "analysis": analysis_result,
                "requirements": requirements,
                "design_type": detected_type,
                "complexity_level": complexity_level
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计需求分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"分析失败: {str(e)}",
                "requirements": requirements,
                "design_type": design_type,
                "complexity_level": complexity_level
            }
            
    def _extract_enhanced_context_from_requirements(self, requirements: str) -> Dict[str, str]:
        """从requirements中提取增强上下文信息"""
        context = {
            'basic_requirements': requirements,
            'error_analysis': '',
            'improvement_suggestions': '',
            'historical_context': '',
            'success_guidance': ''  # 新增：成功经验指导
        }
        
        # 提取成功经验指导（优先级最高）
        if '🎯 **基于历史迭代的成功经验指导**:' in requirements:
            success_start = requirements.find('🎯 **基于历史迭代的成功经验指导**:')
            success_end = requirements.find('📚 **历史迭代经验教训**:') if '📚 **历史迭代经验教训**:' in requirements else requirements.find('🔧 **严格代码验证要求**:')
            if success_end == -1:
                success_end = requirements.find('🚨 **上次编译错误详情**:')
            if success_end == -1:
                success_end = len(requirements)
            
            context['success_guidance'] = requirements[success_start:success_end].strip()
        
        # 提取错误分析信息
        if '🚨 **上次编译错误详情**:' in requirements:
            error_start = requirements.find('🚨 **上次编译错误详情**:')
            error_end = requirements.find('💡 **改进建议**:') if '💡 **改进建议**:' in requirements else requirements.find('🎯 **基于历史迭代的成功经验指导**:')
            if error_end == -1:
                error_end = requirements.find('📚 **历史迭代经验教训**:')
            if error_end == -1:
                error_end = len(requirements)
            
            context['error_analysis'] = requirements[error_start:error_end].strip()
        
        # 提取改进建议
        if '💡 **改进建议**:' in requirements:
            suggestion_start = requirements.find('💡 **改进建议**:')
            suggestion_end = requirements.find('🎯 **基于历史迭代的成功经验指导**:') if '🎯 **基于历史迭代的成功经验指导**:' in requirements else requirements.find('🔧 **严格代码验证要求**:')
            if suggestion_end == -1:
                suggestion_end = requirements.find('📚 **历史迭代经验教训**:')
            if suggestion_end == -1:
                suggestion_end = len(requirements)
            
            context['improvement_suggestions'] = requirements[suggestion_start:suggestion_end].strip()
        
        # 提取历史上下文
        if '📚 **历史迭代经验教训**:' in requirements:
            history_start = requirements.find('📚 **历史迭代经验教训**:')
            history_end = requirements.find('🎯 **基于历史模式的智能建议**:') if '🎯 **基于历史模式的智能建议**:' in requirements else requirements.find('🤖 **AI行为模式分析**:')
            if history_end == -1:
                history_end = requirements.find('🔧 **严格代码验证要求**:')
            if history_end == -1:
                history_end = len(requirements)
            
            context['historical_context'] = requirements[history_start:history_end].strip()
        
        # 提取基础需求（去除增强信息）
        basic_req_end = requirements.find('🎯 **基于历史迭代的成功经验指导**:')
        if basic_req_end == -1:
            basic_req_end = requirements.find('🚨 **上次编译错误详情**:')
        if basic_req_end == -1:
            basic_req_end = requirements.find('📚 **历史迭代经验教训**:')
        if basic_req_end == -1:
            basic_req_end = requirements.find('🔧 **严格代码验证要求**:')
        
        if basic_req_end != -1:
            context['basic_requirements'] = requirements[:basic_req_end].strip()
        
        return context
    
    
    
    def _build_port_info(self, ports: List[Dict], port_type: str) -> str:
        """构建端口信息字符串，支持字符串和字典格式的端口定义"""
        if not ports:
            return ""
        
        port_info = ""
        for port in ports:
            if isinstance(port, str):
                # 处理字符串格式: "port_name [width]" 或 "port_name"
                port = port.strip()
                if '[' in port and ']' in port:
                    # 带宽度的端口: "data [7:0]"
                    parts = port.split('[')
                    name = parts[0].strip()
                    width_part = parts[1].split(']')[0]
                    if ':' in width_part:
                        # [7:0] 格式
                        high, low = width_part.split(':')
                        width_str = f"[{high.strip()}:{low.strip()}] "
                    else:
                        # [7] 格式
                        width_str = f"[{width_part.strip()}] "
                    port_info += f"    {port_type} {width_str}{name},  // {name} signal\n"
                else:
                    # 简单端口: "clk"
                    port_info += f"    {port_type} {port},  // {port} signal\n"
            elif isinstance(port, dict):
                # 处理字典格式
                width = port.get("width", 1)
                
                # 修复：确保 width 是整数类型
                if isinstance(width, str):
                    # 如果是字符串（如 "WIDTH"），直接使用字符串格式
                    if width.isdigit():
                        # 如果是数字字符串，转换为整数
                        width = int(width)
                        width_str = f"[{width-1}:0] " if width > 1 else ""
                    else:
                        # 如果是参数名（如 "WIDTH"），使用参数格式
                        width_str = f"[{width}-1:0] " if width != "1" else ""
                else:
                    # 如果是整数，正常处理
                    width_str = f"[{width-1}:0] " if width > 1 else ""
                
                description = port.get('description', '')
                port_info += f"    {port_type} {width_str}{port['name']},  // {description}\n"
        
        return port_info
    
    

    

    
    # 测试台生成功能已移除，由代码审查智能体负责
    # 这样可以更好地分离职责：设计智能体专注代码生成，审查智能体负责验证


    async def _tool_generate_verilog_code(self, module_name: str, requirements: str = None,
                                        input_ports: List[Dict] = None,
                                        output_ports: List[Dict] = None,
                                        clock_domain: Dict = None,
                                        coding_style: str = "rtl",
                                        parameters: List[Dict] = None,
                                        additional_constraints: List[str] = None,
                                        comments_required: bool = True,
                                        # 添加备用参数用于自动合成requirements
                                        description: str = None,
                                        behavior: str = None,
                                        **kwargs) -> Dict[str, Any]:
        """生成Verilog代码工具实现"""
        try:
            self.logger.info(f"🔧 生成Verilog代码: {module_name}")
            
            # 🔧 修复：自动合成requirements参数
            if not requirements and (description or behavior):
                requirements = ""
                if description:
                    requirements += f"设计描述: {description}\n"
                if behavior:
                    requirements += f"行为规格: {behavior}\n"
                # 添加其他可能的备用参数
                for key, value in kwargs.items():
                    if key in ['specification', 'specs', 'functionality', 'design_spec'] and value:
                        requirements += f"{key}: {value}\n"
                        
                self.logger.info(f"🔧 自动合成requirements参数: {requirements[:200]}...")
            
            if not requirements:
                self.logger.error("❌ 无法获取requirements参数，已提供的参数: description={}, behavior={}, kwargs={}".format(description, behavior, list(kwargs.keys())))
                return {
                    "success": False,
                    "error": "缺少必需的requirements参数，无法生成Verilog代码"
                }
            
            # 增强：从requirements中提取错误分析和改进建议
            enhanced_context = self._extract_enhanced_context_from_requirements(requirements)
            
            # 智能检测设计类型
            is_combinational = self._detect_combinational_requirement(requirements)
            self.logger.info(f"🔍 检测到设计类型: {'组合逻辑' if is_combinational else '时序逻辑'}")
            
            # 构建端口信息
            input_info = self._build_port_info(input_ports, "input")
            output_info = self._build_port_info(output_ports, "output")
            
            # 构建参数信息
            parameters_info = ""
            if parameters:
                parameters_info = "\n参数定义:\n"
                for param in parameters:
                    param_name = param.get("name", "")
                    default_value = param.get("default_value", "")
                    description = param.get("description", "")
                    if default_value is not None:
                        parameters_info += f"    parameter {param_name} = {default_value};  // {description}\n"
                    else:
                        parameters_info += f"    parameter {param_name};  // {description}\n"
            
            # 构建额外约束信息
            constraints_info = ""
            if additional_constraints:
                constraints_info = "\n额外约束:\n"
                for i, constraint in enumerate(additional_constraints, 1):
                    constraints_info += f"{i}. {constraint}\n"
            
            # 根据设计类型构建不同的prompt
            if is_combinational:
                generation_prompt = f"""
请生成一个名为 {module_name} 的Verilog模块，要求如下：

功能需求: {enhanced_context.get('basic_requirements', requirements)}
编码风格: {coding_style}

🚨 **重要约束**: 这是纯组合逻辑设计，不能包含任何时序元件（时钟、复位、寄存器）

端口定义:
{input_info.rstrip() if input_info else "// 请根据需求定义输入端口"}
{output_info.rstrip() if output_info else "// 请根据需求定义输出端口"}

{parameters_info}
{constraints_info}

{enhanced_context.get('error_analysis', '')}
{enhanced_context.get('improvement_suggestions', '')}
{enhanced_context.get('historical_context', '')}

🚨 **组合逻辑设计关键要求 - 请严格遵守**:
1. 使用纯组合逻辑，不能包含 always @(posedge clk) 或 always @(posedge rst)
2. 只能使用 always @(*) 或 assign 语句
3. 输出端口使用 wire 类型，不能使用 reg 类型
4. 不要包含时钟和复位端口
5. 不能包含任何寄存器或触发器
6. 所有输出必须通过组合逻辑直接计算

请只返回纯净的Verilog代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
直接从 module 开始，以 endmodule 结束。

代码要求：
1. 模块声明（不包含时钟和复位端口）
2. 端口定义（输出使用wire类型）
3. 内部信号声明（wire类型）
4. 组合逻辑功能实现（always @(*) 或 assign）
5. {'详细的注释' if comments_required else '简洁的注释'}

确保代码符合IEEE 1800标准并可被综合工具处理。
"""
            else:
                # 时序逻辑设计
                clock_info = clock_domain or {"clock_name": "clk", "reset_name": "rst", "reset_active": "high"}
                generation_prompt = f"""
请生成一个名为 {module_name} 的Verilog模块，要求如下：

功能需求: {enhanced_context.get('basic_requirements', requirements)}
编码风格: {coding_style}

端口定义:
{input_info.rstrip() if input_info else "// 请根据需求定义输入端口"}
{output_info.rstrip() if output_info else "// 请根据需求定义输出端口"}

{parameters_info}

时钟域:
- 时钟信号: {clock_info['clock_name']}
- 复位信号: {clock_info['reset_name']} (active {clock_info['reset_active']})

{constraints_info}

{enhanced_context.get('error_analysis', '')}
{enhanced_context.get('improvement_suggestions', '')}
{enhanced_context.get('historical_context', '')}

🚨 **时序逻辑设计关键要求 - 请严格遵守**:
请只返回纯净的Verilog代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
直接从 module 开始，以 endmodule 结束。

代码要求：
1. 模块声明（包含时钟和复位端口）
2. 端口定义（输出使用reg类型）
3. 内部信号声明
4. 时序逻辑功能实现（always @(posedge clk)）
5. {'详细的注释' if comments_required else '简洁的注释'}

确保代码符合IEEE 1800标准并可被综合工具处理。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=generation_prompt,
                system_prompt="你是专业的Verilog工程师，请生成高质量的可综合代码。特别注意避免历史错误和改进建议。",
                temperature=0.1
            )
            
            # 使用Function Calling write_file工具保存代码
            filename = f"{module_name}.v"
            write_result = await self._tool_write_file(
                filename=filename,
                content=response,
                description=f"生成的{module_name}模块Verilog代码"
            )
            
            if not write_result.get("success", False):
                self.logger.error(f"❌ 文件保存失败: {write_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": f"文件保存失败: {write_result.get('error', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "module_name": module_name,
                "verilog_code": response,
                "file_path": write_result.get("file_path"),
                "file_id": write_result.get("file_id"),
                "coding_style": coding_style,
                "port_count": {
                    "inputs": len(input_ports) if input_ports else 0,
                    "outputs": len(output_ports) if output_ports else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog代码生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
                
    # =============================================================================
    # 新增工具方法 - 参考代码审查智能体结构
    # =============================================================================
    
    async def _tool_analyze_code_quality(self, verilog_code: str, module_name: str = None) -> Dict[str, Any]:
        """分析Verilog代码质量工具"""
        try:
            self.logger.info(f"🔍 分析代码质量: {module_name or 'unknown'}")
            
            # 提取模块名
            if not module_name:
                module_name = self._extract_module_name_from_code(verilog_code)
            
            # 构建质量分析提示
            analysis_prompt = f"""
请分析以下Verilog代码的质量，并提供详细的评估报告：

```verilog
{verilog_code}
```

请从以下方面进行分析：
1. **语法正确性**: 检查是否符合Verilog语法规范
2. **可综合性**: 评估代码是否可以被综合工具处理
3. **时序收敛**: 分析时序逻辑的建立保持时间
4. **代码可读性**: 评估注释、命名、结构等
5. **最佳实践**: 检查是否遵循行业最佳实践
6. **潜在问题**: 识别可能的问题和改进建议

请提供结构化的分析报告，包括：
- 总体质量评分（0-100）
- 各项指标评分
- 具体问题和建议
- 改进优先级
"""
            
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是专业的Verilog代码质量分析专家，请提供客观、详细的质量评估。",
                temperature=0.1
            )
            
            return {
                "success": True,
                "module_name": module_name,
                "quality_analysis": response,
                "analysis_timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 代码质量分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_module_name_from_code(self, verilog_code: str) -> str:
        """从Verilog代码中提取模块名"""
        try:
            # 使用正则表达式匹配模块声明
            import re
            module_pattern = r'module\s+([a-zA-Z][a-zA-Z0-9_]*)\s*[\(;]'
            match = re.search(module_pattern, verilog_code, re.IGNORECASE)
            if match:
                return match.group(1)
            return "unknown_module"
        except Exception:
            return "unknown_module"
    

    

    
    async def _tool_optimize_verilog_code(self, verilog_code: str, 
                                        optimization_target: str = "area",
                                        module_name: str = None) -> Dict[str, Any]:
        """优化Verilog代码工具"""
        try:
            self.logger.info(f"⚡ 优化Verilog代码: {module_name or 'unknown'} - 目标: {optimization_target}")
            
            if not module_name:
                module_name = self._extract_module_name_from_code(verilog_code)
            
            optimization_prompt = f"""
请优化以下Verilog代码，优化目标为：{optimization_target}

```verilog
{verilog_code}
```

**优化目标**: {optimization_target}

请根据优化目标进行相应的优化：
- **area**: 减少资源使用，优化逻辑结构
- **speed**: 提高时钟频率，优化关键路径
- **power**: 降低功耗，优化开关活动
- **readability**: 提高代码可读性，优化结构

优化要求：
1. 保持功能不变
2. 符合Verilog语法规范
3. 确保可综合性
4. 提供优化说明
5. 对比优化前后的改进

请提供：
- 优化后的代码
- 优化说明
- 改进效果评估
"""
            
            response = await self.llm_client.send_prompt(
                prompt=optimization_prompt,
                system_prompt="你是专业的Verilog代码优化专家，请提供高质量的代码优化建议。",
                temperature=0.1
            )
            
            # 提取优化后的代码
            optimized_code = self._extract_verilog_code(response)
            
            # 保存优化后的代码
            if optimized_code:
                opt_filename = f"{module_name}_optimized.v"
                write_result = await self._tool_write_file(
                    filename=opt_filename,
                    content=optimized_code,
                    description=f"{module_name}模块优化后的代码"
                )
                
                return {
                    "success": True,
                    "module_name": module_name,
                    "optimization_target": optimization_target,
                    "original_code": verilog_code,
                    "optimized_code": optimized_code,
                    "optimization_report": response,
                    "file_path": write_result.get("file_path"),
                    "file_id": write_result.get("file_id")
                }
            else:
                return {
                    "success": False,
                    "error": "无法提取优化后的代码"
                }
            
        except Exception as e:
            self.logger.error(f"❌ 代码优化失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_verilog_code(self, llm_response: str) -> str:
        """从LLM响应中提取Verilog代码"""
        try:
            import re
            
            # 尝试提取代码块
            code_block_pattern = r'```(?:verilog)?\s*\n(.*?)\n```'
            match = re.search(code_block_pattern, llm_response, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # 如果没有代码块标记，尝试提取module到endmodule
            module_pattern = r'(module\s+.*?endmodule)'
            match = re.search(module_pattern, llm_response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return ""
            
        except Exception:
            return ""
    
    def _generate_verilog_tool_guide(self) -> List[str]:
        """生成EnhancedRealVerilogAgent专用的工具使用指导"""
        guide = []
        
        guide.append("\n=== EnhancedRealVerilogAgent 工具调用指导 ===")
        guide.append("")
        
        guide.append("【可用工具列表】")
        guide.append("1. analyze_design_requirements - 设计需求分析")
        guide.append("   功能: 分析和解析Verilog设计需求，提取关键设计参数")
        guide.append("   参数: requirements, design_type, complexity_level")
        guide.append("   示例: analyze_design_requirements('设计一个8位加法器', 'combinational', 'medium')")
        guide.append("")
        
        guide.append("2. generate_verilog_code - Verilog代码生成")
        guide.append("   功能: 生成高质量的Verilog HDL代码")
        guide.append("   参数: module_name, requirements, input_ports, output_ports, coding_style")
        guide.append("   示例: generate_verilog_code('adder_8bit', '8位加法器', [{'name':'a','width':8}], [{'name':'sum','width':8}], 'rtl')")
        guide.append("")
        
        guide.append("3. analyze_code_quality - 代码质量分析")
        guide.append("   功能: 分析Verilog代码质量，提供详细的评估报告")
        guide.append("   参数: verilog_code, module_name")
        guide.append("   示例: analyze_code_quality(verilog_code, 'adder_8bit')")
        guide.append("")
        
        guide.append("4. optimize_verilog_code - 代码优化")
        guide.append("   功能: 优化Verilog代码，支持面积、速度、功耗等优化目标")
        guide.append("   参数: verilog_code, optimization_target, module_name")
        guide.append("   示例: optimize_verilog_code(verilog_code, 'area', 'adder_8bit')")
        guide.append("")
        
        guide.append("5. get_tool_usage_guide - 工具使用指导")
        guide.append("   功能: 获取工具使用指导")
        guide.append("   参数: include_examples, include_best_practices")
        guide.append("   示例: get_tool_usage_guide(True, True)")
        guide.append("")
        
        guide.append("【设计流程最佳实践】")
        guide.append("1. 需求分析: analyze_design_requirements")
        guide.append("2. 代码生成: generate_verilog_code")
        guide.append("3. 质量分析: analyze_code_quality")
        guide.append("4. 代码优化: optimize_verilog_code (可选)")
        guide.append("")
        
        guide.append("【注意事项】")
        guide.append("- 专注于Verilog HDL设计，不负责测试台生成")
        guide.append("- 所有工具都支持Schema验证，确保参数格式正确")
        guide.append("- 建议按照最佳实践流程调用工具")
        guide.append("- 生成的代码包含详细注释和端口说明")
        guide.append("- 支持多种编码风格：behavioral, structural, rtl, mixed")
        
        return guide
    
    async def _tool_get_tool_usage_guide(self, include_examples: bool = True,
                                       include_best_practices: bool = True) -> Dict[str, Any]:
        """获取EnhancedRealVerilogAgent专用的工具使用指导"""
        try:
            guide = self._generate_verilog_tool_guide()
            
            return {
                "success": True,
                "guide": guide,
                "agent_type": "EnhancedRealVerilogAgent",
                "include_examples": include_examples,
                "include_best_practices": include_best_practices,
                "total_tools": 5,  # EnhancedRealVerilogAgent有5个工具
                "message": "成功生成EnhancedRealVerilogAgent的工具使用指导"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 生成工具使用指导失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成工具使用指导时发生错误"
            }
         