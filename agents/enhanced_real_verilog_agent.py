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
                        "description": "时钟域配置"
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
        

        
        # 5. 测试台生成工具
        self.register_enhanced_tool(
            name="generate_testbench",
            func=self._tool_generate_testbench,
            description="为Verilog模块生成测试台",
            security_level="normal",
            category="verification",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "maxLength": 100,
                        "description": "目标模块名称"
                    },
                    "verilog_code": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 50000,
                        "description": "目标模块的Verilog代码"
                    },
                    "test_scenarios": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "maxLength": 1000
                        },
                        "maxItems": 20,
                        "description": "测试场景描述列表"
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
                    }
                },
                "required": ["module_name", "verilog_code"],
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

🎯 **推荐的工具调用方式**:

### 方式1: 使用自然字符串格式（推荐）
```json
{
    "tool_calls": [
        {
            "tool_name": "generate_verilog_code",
            "parameters": {
                "module_name": "simple_adder",
                "requirements": "设计一个8位加法器",
                "input_ports": ["a [7:0]", "b [7:0]", "cin"],
                "output_ports": ["sum [7:0]", "cout"],
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
                "module_name": "simple_adder",
                "requirements": "设计一个8位加法器",
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

🎯 **工具列表和参数**:

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

### 4. generate_testbench
- `module_name` (必需): 目标模块名称
- `verilog_code` (必需): 目标模块的Verilog代码（也可使用 `code`）
- `test_scenarios` (可选): 测试场景描述列表（也可使用 `test_cases`）
- `clock_period` (可选): 时钟周期(ns)，0.1-1000.0
- `simulation_time` (可选): 仿真时间(时钟周期数)，100-1000000

🎯 **使用建议**:
1. 优先使用简洁直观的字符串格式定义端口，如 `"a [7:0]"`
2. 字段名称可以使用你习惯的方式，系统会智能适配
3. 不必担心参数格式错误，系统会自动修正
4. 专注于设计逻辑，让系统处理格式细节

**当收到设计任务时，建议流程**:
1. 分析设计需求 (analyze_design_requirements)
2. 搜索现有模块 (可选，search_existing_modules)  
3. 生成Verilog代码 (generate_verilog_code)
4. 生成测试台 (generate_testbench)

💡 **关键优势**: 现在你可以使用自然直观的参数格式，系统的智能适配层会确保与底层工具的完美兼容！
"""
        return base_prompt
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.MODULE_DESIGN,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.VERIFICATION
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
            # 使用增强验证处理流程
            result = await self.process_with_enhanced_validation(
                user_request=enhanced_prompt,
                max_iterations=5
            )
            
            if result["success"]:
                self.logger.info(f"✅ 任务完成: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "response": result.get("response", ""),
                    "tool_results": result.get("tool_results", []),
                    "iterations": result.get("iterations", 1),
                    "quality_metrics": {
                        "schema_validation_passed": True,
                        "parameter_errors_fixed": result.get("iterations", 1) > 1
                    }
                }
            else:
                self.logger.error(f"❌ 任务失败: {task_id} - {result.get('error')}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": result.get("error", "Unknown error"),
                    "iterations": result.get("iterations", 1)
                }
                
        except Exception as e:
            self.logger.error(f"❌ 任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}"
            }
    
    # =============================================================================
    # 工具实现方法
    # =============================================================================
    
    async def _tool_analyze_design_requirements(self, requirements: str, 
                                              design_type: str = "mixed",
                                              complexity_level: str = "medium") -> Dict[str, Any]:
        """分析设计需求工具实现"""
        try:
            self.logger.info(f"📊 分析设计需求: {design_type} - {complexity_level}")
            
            # 构建LLM分析提示
            analysis_prompt = f"""
请分析以下Verilog设计需求：

需求描述: {requirements}
设计类型: {design_type}
复杂度级别: {complexity_level}

请提供以下分析结果：
1. 功能模块分解
2. 输入/输出端口需求
3. 时钟域要求
4. 设计约束
5. 验证要点

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
                    "design_type": design_type,
                    "complexity": complexity_level,
                    "estimated_modules": 1,
                    "key_features": []
                }
            
            return {
                "success": True,
                "analysis": analysis_result,
                "requirements": requirements,
                "design_type": design_type,
                "complexity_level": complexity_level
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计需求分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_generate_verilog_code(self, module_name: str, requirements: str,
                                        input_ports: List[Dict] = None,
                                        output_ports: List[Dict] = None,
                                        clock_domain: Dict = None,
                                        coding_style: str = "rtl") -> Dict[str, Any]:
        """生成Verilog代码工具实现"""
        try:
            self.logger.info(f"🔧 生成Verilog代码: {module_name}")
            
            # 构建端口信息
            input_info = ""
            if input_ports:
                for port in input_ports:
                    width = port.get("width", 1)
                    width_str = f"[{width-1}:0] " if width > 1 else ""
                    input_info += f"    input {width_str}{port['name']},  // {port.get('description', '')}\n"
            
            output_info = ""
            if output_ports:
                for port in output_ports:
                    width = port.get("width", 1)
                    width_str = f"[{width-1}:0] " if width > 1 else ""
                    output_info += f"    output {width_str}{port['name']},  // {port.get('description', '')}\n"
            
            # 时钟域信息
            clock_info = clock_domain or {"clock_name": "clk", "reset_name": "rst", "reset_active": "high"}
            
            generation_prompt = f"""
请生成一个名为 {module_name} 的Verilog模块，要求如下：

功能需求: {requirements}
编码风格: {coding_style}

端口定义:
{input_info.rstrip() if input_info else "// 请根据需求定义输入端口"}
{output_info.rstrip() if output_info else "// 请根据需求定义输出端口"}

时钟域:
- 时钟信号: {clock_info['clock_name']}
- 复位信号: {clock_info['reset_name']} (active {clock_info['reset_active']})

🚨 **关键要求 - 请严格遵守**:
请只返回纯净的Verilog代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
直接从 module 开始，以 endmodule 结束。

代码要求：
1. 模块声明
2. 端口定义  
3. 内部信号声明
4. 功能实现
5. 适当的注释

确保代码符合IEEE 1800标准并可被综合工具处理。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=generation_prompt,
                system_prompt="你是专业的Verilog工程师，请生成高质量的可综合代码。",
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
    

    
    async def _tool_generate_testbench(self, module_name: str, verilog_code: str,
                                     test_scenarios: List[str] = None,
                                     clock_period: float = 10.0,
                                     simulation_time: int = 10000) -> Dict[str, Any]:
        """生成测试台工具实现"""
        try:
            self.logger.info(f"🧪 生成测试台: {module_name}")
            
            test_scenarios = test_scenarios or ["basic functionality test"]
            
            testbench_prompt = f"""
请为以下Verilog模块生成一个完整的测试台(testbench)：

目标模块: {module_name}
```verilog
{verilog_code}
```

测试要求:
- 时钟周期: {clock_period}ns
- 仿真时间: {simulation_time} 个时钟周期
- 测试场景: {', '.join(test_scenarios)}

🚨 **关键要求 - 请严格遵守**:
请只返回纯净的Verilog测试台代码，不要包含任何解释文字、Markdown格式或代码块标记。
不要使用```verilog 或 ``` 标记。
不要添加"以下是..."、"说明："等解释性文字。
不要包含功能说明、测试报告示例、文件结构建议等文字内容。
直接从 `timescale 开始，以 endmodule 结束。

测试台必须包含：
1. `timescale 声明
2. testbench模块声明
3. 信号声明
4. 时钟和复位生成
5. 被测模块实例化
6. 测试激励生成
7. 结果检查和显示
8. 适当的$display和$monitor语句
9. 波形转储设置

确保测试台能够充分验证模块功能，并且是纯Verilog代码。
"""
            
            response = await self.llm_client.send_prompt(
                prompt=testbench_prompt,
                system_prompt="你是验证工程师，请生成全面的Verilog测试台。记住：只返回纯Verilog代码，不要任何解释文字或Markdown格式。",
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
                    "simulation_time": simulation_time
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试台生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }