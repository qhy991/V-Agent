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
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 1024,
                                    "default": 1
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
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 1024,
                                    "default": 1
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
        

        
        # 注意：测试台生成功能已移除，由代码审查智能体负责
    
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
                temperature=0.3,  # 降低温度以提高一致性
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
            raise
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的System Prompt（支持智能Schema适配）"""
        base_prompt = """你是一位专业的Verilog HDL设计专家，具备以下能力：

🔧 **核心能力**:
- Verilog/SystemVerilog代码设计和生成
- 数字电路架构设计
- 时序分析和优化
- 可综合代码编写
- 测试台(Testbench)开发

📋 **工作原则**:
1. 严格遵循IEEE 1800标准
2. 编写可综合、可仿真的代码
3. 注重代码可读性和维护性
4. 确保时序收敛和功能正确性
5. 使用标准化的命名规范

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

📌 **端口定义灵活格式**:
- ✅ 字符串格式: `["a [7:0]", "b [7:0]", "cin"]`
- ✅ 对象格式: `[{"name": "a", "width": 8}, {"name": "b", "width": 8}, {"name": "cin", "width": 1}]`
- 💡 系统会自动转换字符串格式为对象格式

📌 **字段名智能映射**:
- `code` ↔ `verilog_code` (自动双向映射)
- `design_files` → `verilog_files`
- `test_cases` → `test_scenarios`
- 💡 使用任一格式都会被智能识别

📌 **缺失字段智能推断**:
- 缺少 `module_name` 时会从需求描述中自动提取
- 缺少必需字段时会提供合理默认值
- 💡 无需担心遗漏参数

🎯 **设计类型识别指导**:
- 如果需求明确提到"纯组合逻辑"、"combinational"、"无时钟"等关键词，使用组合逻辑设计
- 组合逻辑设计：使用 always @(*) 或 assign，输出使用 wire 类型
- 时序逻辑设计：使用 always @(posedge clk)，输出使用 reg 类型

⚠️ **组合逻辑设计规则**:
1. 不能包含时钟信号 (clk)
2. 不能包含复位信号 (rst)  
3. 不能使用 always @(posedge clk) 语句
4. 输出端口使用 wire 类型，不能使用 reg 类型
5. 只能使用 always @(*) 或 assign 语句

🎯 **推荐的工具调用方式**:

### 方式1: 使用自然字符串格式（推荐）
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_verilog_code",
            "parameters": {
                "module_name": "target_module",
                "requirements": "设计目标模块",
                "input_ports": ["input1 [7:0]", "input2 [7:0]", "ctrl"],
                "output_ports": ["output1 [7:0]", "status"],
                "coding_style": "rtl"
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
            "tool_name": "generate_verilog_code", 
            "parameters": {
                "module_name": "target_module",
                "requirements": "设计目标模块",
                "input_ports": [
                    {"name": "a", "width": 8, "description": "第一个操作数"},
                    {"name": "b", "width": 8, "description": "第二个操作数"},
                    {"name": "cin", "width": 1, "description": "输入进位"}
                ],
                "output_ports": [
                    {"name": "sum", "width": 8, "description": "加法结果"},
                    {"name": "cout", "width": 1, "description": "输出进位"}
                ],
                "coding_style": "rtl"
            }
        }
    ]
}
```

🎯 **可用工具列表**:

### 1. analyze_design_requirements
- `requirements` (必需): 设计需求描述
- `design_type` (可选): "combinational", "sequential", "mixed", "custom"
- `complexity_level` (可选): "simple", "medium", "complex", "advanced"

### 2. generate_verilog_code  
- `module_name` (必需): 模块名称
- `requirements` (必需): 设计需求和功能描述
- `input_ports` (可选): 输入端口定义（支持字符串或对象数组）
- `output_ports` (可选): 输出端口定义（支持字符串或对象数组）
- `coding_style` (可选): "behavioral", "structural", "rtl", "mixed"

### 3. search_existing_modules
- `module_type` (可选): "arithmetic", "memory", "interface", "controller", "dsp", "custom"
- `functionality` (可选): 功能关键词描述
- `complexity_filter` (可选): "simple", "medium", "complex", "any"
- `max_results` (可选): 最大返回结果数，1-50

### 4. write_file
- `filename` (必需): 文件名
- `content` (必需): 文件内容
- `description` (可选): 文件描述

### 5. read_file
- `filepath` (必需): 文件路径
- `encoding` (可选): 文件编码，默认"utf-8"

🎯 **使用建议**:
1. 优先使用简洁直观的字符串格式定义端口，如 `"a [7:0]"`
2. 字段名称可以使用你习惯的方式，系统会智能适配
3. 不必担心参数格式错误，系统会自动修正
4. 专注于设计逻辑，让系统处理格式细节

⚠️ **重要提醒**:
- 只能调用上述列出的工具，不要尝试调用其他工具
- 如果任务需要接口验证或设计合规性检查，请使用现有的工具组合完成
- 不要调用 `verify_interface_compliance`、`validate_design_compliance` 等不存在的工具

**当收到设计任务时，建议流程**:
1. 分析设计需求 (analyze_design_requirements)
2. 搜索现有模块 (可选，search_existing_modules)  
3. 生成Verilog代码 (generate_verilog_code)

⚠️ **职责边界**: 本智能体专注于Verilog代码设计和生成，测试台生成、仿真验证等功能由代码审查智能体负责。

💡 **关键优势**: 现在你可以使用自然直观的参数格式，系统的智能适配层会确保与底层工具的完美兼容！

🎯 **设计类型识别指导**:
- 如果需求明确提到"纯组合逻辑"、"combinational"、"无时钟"等关键词，使用组合逻辑设计
- 组合逻辑设计：使用 always @(*) 或 assign，输出使用 wire 类型
- 时序逻辑设计：使用 always @(posedge clk)，输出使用 reg 类型

⚠️ **组合逻辑设计规则**:
1. 不能包含时钟信号 (clk)
2. 不能包含复位信号 (rst)  
3. 不能使用 always @(posedge clk) 语句
4. 输出端口使用 wire 类型，不能使用 reg 类型
5. 只能使用 always @(*) 或 assign 语句
6. 不能包含任何寄存器或触发器

⚠️ **时序逻辑设计规则**:
1. 必须包含时钟信号 (clk)
2. 通常包含复位信号 (rst)
3. 使用 always @(posedge clk) 语句
4. 输出端口使用 reg 类型
5. 可以包含寄存器和触发器

🔍 **智能检测**: 系统会自动检测设计类型并生成相应的代码结构。
"""
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
        """执行增强的Verilog设计任务 - 支持多轮对话"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行增强Verilog设计任务: {task_id}")
        
        # 🎯 新增：从任务消息中获取对话历史
        conversation_history = []
        if original_message.metadata:
            # 从元数据中获取对话历史
            conversation_history = original_message.metadata.get("conversation_history", [])
            self.logger.info(f"🔗 从任务消息获取到{len(conversation_history)}轮对话历史")
            
            # 检查是否为持续对话
            if original_message.metadata.get("persistent_conversation", False):
                self.logger.info(f"🔗 检测到持续对话模式: {original_message.metadata.get('conversation_id', 'unknown')}")
        
        try:
            # 🎯 新增：使用增强验证处理流程，传递对话历史
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=3,  # 减少最大迭代次数，避免无限循环
                conversation_history=conversation_history  # 传递对话历史
            )
            
            if result["success"]:
                self.logger.info(f"✅ 任务完成: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "response": result.get("response", ""),
                    "content": result.get("content", result.get("response", "")),
                    "tool_results": result.get("tool_results", []),
                    "tool_calls": result.get("tool_calls", []),
                    "iterations": result.get("iterations", 1),
                    "conversation_history": result.get("conversation_history", []),
                    "quality_metrics": {
                        "schema_validation_passed": True,
                        "parameter_errors_fixed": result.get("iterations", 1) > 1,
                        "conversation_rounds": len(result.get("conversation_history", []))
                    }
                }
            else:
                self.logger.error(f"❌ 任务失败: {task_id} - {result.get('error')}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "iterations": result.get("iterations", 1),
                    "conversation_history": result.get("conversation_history", []),
                    "permanently_failed_tools": result.get("permanently_failed_tools", []),
                    "param_validation_failed_tools": result.get("param_validation_failed_tools", [])
                }
                
        except Exception as e:
            self.logger.error(f"❌ 任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}",
                "conversation_history": conversation_history
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
    
    
    
    def _build_port_info(self, ports, port_type: str) -> str:
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
                                        coding_style: str = "rtl") -> Dict[str, Any]:
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
5. 适当的注释

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

时钟域:
- 时钟信号: {clock_info['clock_name']}
- 复位信号: {clock_info['reset_name']} (active {clock_info['reset_active']})

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
5. 适当的注释

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
                
         