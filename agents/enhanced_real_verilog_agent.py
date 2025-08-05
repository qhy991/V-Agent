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
        
        # 3. 模块搜索工具
        self.register_enhanced_tool(
            name="search_existing_modules",
            func=self._tool_search_existing_modules,
            description="搜索现有的Verilog模块和IP核",
            security_level="normal",
            category="database",
            schema={
                "type": "object",
                "properties": {
                    "module_type": {
                        "type": "string",
                        "enum": ["arithmetic", "memory", "interface", "controller", "dsp", "custom"],
                        "description": "模块类型分类"
                    },
                    "functionality": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 500,
                        "description": "功能关键词描述"
                    },
                    "complexity_filter": {
                        "type": "string",
                        "enum": ["simple", "medium", "complex", "any"],
                        "default": "any",
                        "description": "复杂度过滤条件"
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                        "description": "最大返回结果数"
                    }
                },
                "additionalProperties": False
            }
        )
        
        # 4. 代码质量分析工具
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
        
        # 5. 设计规格验证工具
        self.register_enhanced_tool(
            name="validate_design_specifications",
            func=self._tool_validate_design_specifications,
            description="验证设计需求与生成代码的符合性",
            security_level="normal",
            category="validation",
            schema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 10000,
                        "description": "设计需求描述"
                    },
                    "generated_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "生成的Verilog代码（可选）"
                    },
                    "design_type": {
                        "type": "string",
                        "enum": ["combinational", "sequential", "mixed", "custom"],
                        "default": "mixed",
                        "description": "设计类型"
                    }
                },
                "required": ["requirements"],
                "additionalProperties": False
            }
        )
        
        # 6. 设计文档生成工具
        self.register_enhanced_tool(
            name="generate_design_documentation",
            func=self._tool_generate_design_documentation,
            description="为Verilog模块生成完整的设计文档",
            security_level="normal",
            category="documentation",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "maxLength": 100,
                        "description": "模块名称"
                    },
                    "verilog_code": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 100000,
                        "description": "Verilog代码"
                    },
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 10000,
                        "description": "设计需求描述"
                    },
                    "design_type": {
                        "type": "string",
                        "enum": ["combinational", "sequential", "mixed", "custom"],
                        "default": "mixed",
                        "description": "设计类型"
                    }
                },
                "required": ["module_name", "verilog_code", "requirements"],
                "additionalProperties": False
            }
        )
        
        # 7. 代码优化工具
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
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """实现LLM调用 - 使用优化的调用机制避免重复传入system prompt"""
        # 生成对话ID（如果还没有）
        if not hasattr(self, 'current_conversation_id') or not self.current_conversation_id:
            self.current_conversation_id = f"verilog_agent_{int(time.time())}"
        
        # 构建用户消息
        user_message = ""
        is_first_call = len(conversation) <= 1  # 如果对话历史很少，认为是第一次调用
        
        for msg in conversation:
            if msg["role"] == "user":
                user_message += f"{msg['content']}\n\n"
            elif msg["role"] == "assistant":
                user_message += f"Assistant: {msg['content']}\n\n"
        
        try:
            # 使用优化的LLM调用方法
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=self.current_conversation_id,
                user_message=user_message.strip(),
                system_prompt=self._build_enhanced_system_prompt() if is_first_call else None,
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
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
3. 处理分析结果，不要重复相同的调用"""
        
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
            # 使用增强验证处理流程 - 允许更多迭代次数进行错误修复
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=6  # 增加到6次迭代，给足够空间进行错误修复和优化
            )
            
            if result["success"]:
                self.logger.info(f"✅ Verilog设计任务完成: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "response": result.get("response", ""),
                    "tool_results": result.get("tool_results", []),
                    "iterations": result.get("iterations", 1),
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
                    "suggestions": result.get("suggestions", [])
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
                ]
            }
    
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
    
    
    async def _tool_search_existing_modules(self, module_type: str = None,
                                          functionality: str = None,
                                          complexity_filter: str = "any",
                                          max_results: int = 10) -> Dict[str, Any]:
        """搜索现有模块工具实现"""
        try:
            self.logger.info(f"🔍 搜索现有模块: {module_type} - {functionality}")
            
            # 模拟数据库搜索（实际项目中连接真实数据库）
            sample_modules = [
                {
                    "name": "counter_8bit",
                    "type": "arithmetic",
                    "functionality": "8-bit binary counter with enable and reset",
                    "complexity": "simple",
                    "file_path": "lib/counters/counter_8bit.v"
                },
                {
                    "name": "fifo_sync",
                    "type": "memory", 
                    "functionality": "Synchronous FIFO buffer with configurable depth",
                    "complexity": "medium",
                    "file_path": "lib/memory/fifo_sync.v"
                },
                {
                    "name": "uart_tx",
                    "type": "interface",
                    "functionality": "UART transmitter with configurable baud rate",
                    "complexity": "medium",
                    "file_path": "lib/communication/uart_tx.v"
                }
            ]
            
            # 应用过滤条件
            results = []
            for module in sample_modules:
                if module_type and module["type"] != module_type:
                    continue
                if functionality and functionality.lower() not in module["functionality"].lower():
                    continue
                if complexity_filter != "any" and module["complexity"] != complexity_filter:
                    continue
                results.append(module)
                
                if len(results) >= max_results:
                    break
            
            return {
                "success": True,
                "results": results,
                "total_found": len(results),
                "search_criteria": {
                    "module_type": module_type,
                    "functionality": functionality,
                    "complexity_filter": complexity_filter
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 模块搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    

    
    # 测试台生成功能已移除，由代码审查智能体负责
    # 这样可以更好地分离职责：设计智能体专注代码生成，审查智能体负责验证


    async def _tool_generate_verilog_code(self, module_name: str, requirements: str,
                                        input_ports: List[Dict] = None,
                                        output_ports: List[Dict] = None,
                                        clock_domain: Dict = None,
                                        coding_style: str = "rtl",
                                        parameters: List[Dict] = None,
                                        additional_constraints: List[str] = None,
                                        comments_required: bool = True) -> Dict[str, Any]:
        """生成Verilog代码工具实现"""
        try:
            self.logger.info(f"🔧 生成Verilog代码: {module_name}")
            
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
    
    async def _tool_validate_design_specifications(self, requirements: str, 
                                                 generated_code: str = None,
                                                 design_type: str = "mixed") -> Dict[str, Any]:
        """验证设计规格符合性工具"""
        try:
            self.logger.info(f"🔍 验证设计规格符合性: {design_type}")
            
            validation_prompt = f"""
请验证以下设计需求与生成代码的符合性：

**设计需求**:
{requirements}

**设计类型**: {design_type}

{f"**生成的代码**:\n```verilog\n{generated_code}\n```" if generated_code else "**注意**: 暂无生成代码，仅验证需求完整性"}

请从以下方面进行验证：
1. **功能完整性**: 需求中的所有功能是否在代码中实现
2. **接口一致性**: 端口定义是否与需求匹配
3. **约束满足**: 是否满足所有设计约束
4. **参数化支持**: 参数化需求是否正确实现
5. **设计类型匹配**: 代码结构是否与设计类型一致

请提供详细的验证报告，包括：
- 符合性评分（0-100）
- 各项指标验证结果
- 不符合项详细说明
- 改进建议
"""
            
            response = await self.llm_client.send_prompt(
                prompt=validation_prompt,
                system_prompt="你是专业的设计验证专家，请提供准确、全面的规格符合性验证。",
                temperature=0.1
            )
            
            return {
                "success": True,
                "design_type": design_type,
                "validation_report": response,
                "validation_timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计规格验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_generate_design_documentation(self, module_name: str, 
                                                verilog_code: str,
                                                requirements: str,
                                                design_type: str = "mixed") -> Dict[str, Any]:
        """生成设计文档工具"""
        try:
            self.logger.info(f"📄 生成设计文档: {module_name}")
            
            doc_prompt = f"""
请为以下Verilog模块生成完整的设计文档：

**模块名称**: {module_name}
**设计类型**: {design_type}

**设计需求**:
{requirements}

**Verilog代码**:
```verilog
{verilog_code}
```

请生成包含以下内容的设计文档：
1. **模块概述**: 功能描述、设计目标
2. **接口说明**: 端口定义、信号描述
3. **功能规格**: 详细的功能说明
4. **设计架构**: 内部结构、关键组件
5. **时序要求**: 时钟、复位、时序约束
6. **使用说明**: 实例化示例、注意事项
7. **测试建议**: 测试策略、验证要点

文档格式要求：
- 使用Markdown格式
- 结构清晰，层次分明
- 包含代码示例
- 提供完整的接口说明
"""
            
            response = await self.llm_client.send_prompt(
                prompt=doc_prompt,
                system_prompt="你是专业的技术文档编写专家，请生成清晰、完整的设计文档。",
                temperature=0.1
            )
            
            # 保存文档文件
            doc_filename = f"{module_name}_design_doc.md"
            write_result = await self._tool_write_file(
                filename=doc_filename,
                content=response,
                description=f"{module_name}模块设计文档"
            )
            
            return {
                "success": True,
                "module_name": module_name,
                "documentation": response,
                "file_path": write_result.get("file_path"),
                "file_id": write_result.get("file_id")
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计文档生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
                
         