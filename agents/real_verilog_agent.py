#!/usr/bin/env python3
"""
真实LLM驱动的Verilog设计智能体

Real LLM-powered Verilog Design Agent
"""

import os 
import json
import asyncio
import subprocess
import tempfile
from typing import Dict, Any, Set, List
from pathlib import Path

from core.base_agent import BaseAgent, TaskMessage
from core.enums import AgentCapability
from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir


class RealVerilogDesignAgent(BaseAgent):
    """真实LLM驱动的Verilog HDL设计智能体"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="real_verilog_design_agent",
            role="verilog_designer",
            capabilities={
                AgentCapability.CODE_GENERATION,
                AgentCapability.MODULE_DESIGN,
                AgentCapability.SPECIFICATION_ANALYSIS
            }
        )
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('RealVerilogDesignAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        self.logger.info(f"🔧 真实Verilog设计智能体(Function Calling支持)初始化完成")
        self.agent_logger.info("RealVerilogDesignAgent初始化完成")
    
    def _register_function_calling_tools(self):
        """注册Verilog设计专用工具"""
        # 调用父类方法注册基础工具
        super()._register_function_calling_tools()
        
        # 注册Verilog设计专用工具
        self.register_function_calling_tool(
            name="analyze_design_requirements",
            func=self._tool_analyze_design_requirements,
            description="分析Verilog设计需求",
            parameters={
                "requirements": {"type": "string", "description": "设计需求描述", "required": True}
            }
        )
        
        self.register_function_calling_tool(
            name="search_existing_modules",
            func=self._tool_search_existing_modules,
            description="搜索现有的Verilog模块",
            parameters={
                "module_type": {"type": "string", "description": "模块类型", "required": False},
                "functionality": {"type": "string", "description": "功能描述", "required": False}
            }
        )
        
        self.register_function_calling_tool(
            name="generate_verilog_code",
            func=self._tool_generate_verilog_code,
            description="生成Verilog代码",
            parameters={
                "requirements": {"type": "string", "description": "设计需求", "required": True},
                "module_info": {"type": "object", "description": "模块信息", "required": False}
            }
        )
        
        self.register_function_calling_tool(
            name="analyze_code_quality", 
            func=self._tool_analyze_code_quality,
            description="分析Verilog代码质量",
            parameters={
                "code": {"type": "string", "description": "Verilog代码", "required": True}
            }
        )
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """实现LLM调用"""
        # 构建完整的prompt
        full_prompt = ""
        system_prompt = None
        
        for msg in conversation:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Assistant: {msg['content']}\n\n"
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
            raise
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.MODULE_DESIGN, 
            AgentCapability.SPECIFICATION_ANALYSIS
        }
    
    def get_specialty_description(self) -> str:
        return "真实LLM驱动的Verilog HDL设计智能体，提供专业的数字电路设计和代码生成服务"
    
    async def execute_enhanced_task(self, enhanced_prompt: str, 
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行Verilog设计任务，包含LLM驱动的错误修复"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行真实Verilog设计任务: {task_id}")
        
        max_retries = 3
        current_code = None
        
        try:
            # 1. 分析任务需求
            task_analysis = await self._analyze_design_requirements(enhanced_prompt)
            self.logger.info(f"📊 任务分析: {task_analysis.get('module_type', 'unknown')}")
            
            for attempt in range(max_retries):
                self.logger.info(f"🔄 设计尝试 {attempt + 1}/{max_retries}")
                
                try:
                    # 2. 搜索相关的现有模块（只在第一次或需要时）
                    if attempt == 0:
                        search_results = await self._search_existing_modules(task_analysis)
                    else:
                        search_results = {"success": False, "result": {"data": []}}
                    
                    # 3. 生成或修复Verilog代码
                    if attempt == 0:
                        # 首次生成代码
                        current_code = await self._generate_verilog_code(
                            enhanced_prompt, task_analysis, search_results, file_contents
                        )
                    else:
                        # 基于错误修复代码
                        current_code = await self._regenerate_verilog_code(
                            enhanced_prompt, task_analysis, current_code, last_error
                        )
                    
                    if not current_code:
                        raise Exception("未能生成有效代码")
                    
                    # 保存每次迭代的代码用于调试
                    await self._save_debug_code(current_code, task_id, attempt + 1)
                    
                    # 4. 代码质量分析
                    quality_metrics = await self._analyze_code_quality(current_code)
                    
                    # 5. 尝试编译和基础验证
                    compilation_result = await self._basic_verilog_validation(current_code, attempt + 1)
                    
                    if compilation_result['success']:
                        # 6. 保存生成的文件
                        output_files = await self._save_generated_files(
                            current_code, task_analysis, task_id, attempt + 1
                        )
                        
                        # 7. 创建标准化响应
                        response = await self._create_design_response(
                            task_id, task_analysis, quality_metrics, output_files, 
                            current_code, attempt + 1, compilation_result.get('warnings', [])
                        )
                        
                        return {"formatted_response": response}
                    
                    # 8. 记录错误用于下次修复
                    last_error = compilation_result.get('error', '编译验证失败')
                    self.logger.info(f"⚠️ 第{attempt + 1}次尝试失败: {last_error}")
                    
                    if attempt == max_retries - 1:
                        # 最后一次尝试仍失败
                        output_files = await self._save_generated_files(
                            current_code, task_analysis, task_id, attempt + 1
                        )
                        
                        response = await self._create_design_response(
                            task_id, task_analysis, quality_metrics, output_files,
                            current_code, attempt + 1, [f"编译错误: {last_error}"]
                        )
                        
                        return {"formatted_response": response}
                    
                except Exception as e:
                    last_error = str(e)
                    self.logger.error(f"❌ 第{attempt + 1}次尝试异常: {last_error}")
                    
                    if attempt == max_retries - 1:
                        raise e
                    
                    await asyncio.sleep(0.5)  # 短暂延迟后重试
            
        except Exception as e:
            self.logger.error(f"❌ Verilog设计任务失败: {str(e)}")
            error_response = self.create_error_response_formatted(
                task_id=task_id,
                error_message=f"Verilog设计失败: {str(e)}",
                error_details="请检查任务需求和LLM连接状态",
                format_type=ResponseFormat.JSON
            )
            return {"formatted_response": error_response}
    
    async def _analyze_design_requirements(self, prompt: str) -> Dict[str, Any]:
        """使用LLM分析设计需求"""
        analysis_prompt = f"""
你是一位资深的Verilog/FPGA设计专家。请分析以下设计需求并返回详细的技术规格。

设计需求:
{prompt}

## 关键检测词 - 优先级排序
1. **RISC-V CPU检测** (最高优先级):
   - 如果需求包含以下任何词汇："RISC-V", "riscv", "CPU", "处理器", "中央处理单元", "instruction set", "指令集"
   - 如果需求描述中包含"32位"、"RV32I"、"RV64I"等架构特征
   - 如果需求涉及多个模块如"PC", "ALU", "寄存器", "译码器", "控制器"等
   - 立即识别为"riscv_cpu"类型，复杂度设为9-10

2. **复杂系统设计检测**:
   - 如果需求包含"SoC", "系统芯片", "微架构", "流水线", "缓存", "内存管理"
   - 识别为"complex_system"类型，复杂度设为8-10

3. **简单模块检测** (仅当无上述特征时):
   - "计数器", "counter" → counter类型，复杂度3-4
   - "加法器", "adder" → adder类型，复杂度4-5
   - "ALU", "算术逻辑单元" → alu类型，复杂度6-7

## 复杂度评估标准
- **1-3**: 简单组合逻辑或时序逻辑
- **4-6**: 中等复杂度模块（ALU、寄存器文件等）
- **7-8**: 复杂模块（处理器子系统）
- **9-10**: 完整处理器或SoC设计

请从专业角度分析以下内容，并以JSON格式返回：

1. module_type: 模块类型 (如: riscv_cpu, alu, counter, register_file, instruction_decoder, pc_unit, complex_system)
2. bit_width: 数据位宽 (如: 8, 16, 32, 64)
3. functionality: 详细功能描述，必须准确反映原始需求内容，不能简化
4. complexity: 设计复杂度 (1-10, 其中1最简单，10最复杂，RISC-V CPU应为9-10)
5. input_ports: 输入端口列表 (包括端口名和位宽)
6. output_ports: 输出端口列表 (包括端口名和位宽)
7. clock_domain: 时钟域信息 (single/multiple)
8. reset_type: 复位类型 (async/sync/both)
9. special_features: 特殊功能需求列表
10. timing_constraints: 时序约束要求
11. area_constraints: 面积约束要求
12. power_considerations: 功耗考虑

## 示例返回 - RISC-V CPU
对于包含"RISC-V CPU设计"的需求，返回：
{{
    "module_type": "riscv_cpu",
    "bit_width": 32,
    "functionality": "完整的32位RISC-V处理器核心，支持RV32I基础整数指令集，包含程序计数器(PC)、指令获取单元(IFU)、指令译码单元(IDU)、算术逻辑单元(ALU)、32x32位寄存器文件、内存接口单元等关键模块，采用单周期执行架构",
    "complexity": 9,
    "input_ports": [
        {{"name": "clk", "width": 1, "description": "系统时钟信号"}},
        {{"name": "rst_n", "width": 1, "description": "异步复位信号（低电平有效）"}},
        {{"name": "instruction_in", "width": 32, "description": "从指令内存读取的32位指令"}},
        {{"name": "mem_data_in", "width": 32, "description": "从数据内存读取的32位数据"}}
    ],
    "output_ports": [
        {{"name": "pc_out", "width": 32, "description": "当前程序计数器值，连接到指令内存地址"}},
        {{"name": "mem_addr", "width": 32, "description": "数据内存地址总线"}},
        {{"name": "mem_data_out", "width": 32, "description": "要写入数据内存的32位数据"}},
        {{"name": "mem_write_en", "width": 1, "description": "数据内存写使能信号"}},
        {{"name": "mem_read_en", "width": 1, "description": "数据内存读使能信号"}}
    ],
    "clock_domain": "single",
    "reset_type": "async",
    "special_features": ["RV32I完整指令集支持", "单周期执行架构", "32位RISC-V架构", "哈佛总线结构", "数据前递机制", "完整控制单元"],
    "timing_constraints": "目标时钟频率100MHz，关键路径优化",
    "area_constraints": "优化逻辑资源使用，平衡性能与面积",
    "power_considerations": "低功耗设计，门控时钟，逻辑优化"
}}

## 关键规则
- **当需求明确提到"RISC-V"或"CPU"时，绝对不能简化为"counter"**
- **必须完整保留原始需求的复杂度描述**
- **复杂度评估必须基于实际功能需求，不能低估**

请严格按照上述格式，基于实际的设计需求返回准确的分析结果：
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=4000,
                json_mode=True
            )
            
            analysis = json.loads(response)
            self.logger.info(f"📋 LLM需求分析完成: {analysis.get('module_type')} - 复杂度{analysis.get('complexity')}")
            return analysis
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM需求分析失败: {str(e)}")
            return self._fallback_requirement_analysis(prompt)
    
    def _fallback_requirement_analysis(self, prompt: str) -> Dict[str, Any]:
        """备用需求分析 - 增强RISC-V CPU检测"""
        prompt_lower = prompt.lower()
        
        # 扩展的RISC-V CPU检测词汇表
        cpu_keywords = [
            "risc-v", "riscv", "cpu", "processor", "中央处理单元", "处理器",
            "instruction set", "指令集", "微处理器", "微控制器", "程序计数器",
            "alu", "寄存器文件", "译码器", "控制器", "取指单元", "执行单元"
        ]
        
        # 检查是否为RISC-V CPU设计需求
        is_riscv_cpu = any(keyword in prompt_lower for keyword in cpu_keywords)
        
        if is_riscv_cpu:
            # 提取位宽信息
            bit_width = 32
            for width in [64, 32, 16, 8]:
                if str(width) in prompt_lower or f"{width}位" in prompt_lower:
                    bit_width = width
                    break
            
            # 提取指令集信息
            instruction_set = "RV32I"
            if "rv64" in prompt_lower or "64位" in prompt_lower:
                instruction_set = "RV64I"
            elif "rv32" in prompt_lower or "32位" in prompt_lower:
                instruction_set = "RV32I"
            
            # 构建详细的功能描述
            functionality = f"完整的{bit_width}位RISC-V处理器核心设计"
            if "单周期" in prompt_lower or "single cycle" in prompt_lower:
                functionality += "，采用单周期执行架构"
            elif "流水线" in prompt_lower or "pipeline" in prompt_lower:
                functionality += "，采用流水线架构"
            
            functionality += f"，支持{instruction_set}基础整数指令集，包含程序计数器(PC)、指令获取单元(IFU)、指令译码单元(IDU)、算术逻辑单元(ALU)、{bit_width}x{bit_width}位寄存器文件、内存接口单元等关键模块"
            
            return {
                "module_type": "riscv_cpu",
                "bit_width": bit_width,
                "functionality": functionality,
                "complexity": 9,
                "input_ports": [
                    {"name": "clk", "width": 1, "description": "系统时钟信号"},
                    {"name": "rst_n", "width": 1, "description": "异步复位信号（低电平有效）"},
                    {"name": "instruction_in", "width": bit_width, "description": f"从指令内存读取的{bit_width}位指令"},
                    {"name": "mem_data_in", "width": bit_width, "description": f"从数据内存读取的{bit_width}位数据"}
                ],
                "output_ports": [
                    {"name": "pc_out", "width": bit_width, "description": f"当前{bit_width}位程序计数器值，连接到指令内存地址"},
                    {"name": "mem_addr", "width": bit_width, "description": f"{bit_width}位数据内存地址总线"},
                    {"name": "mem_data_out", "width": bit_width, "description": f"要写入数据内存的{bit_width}位数据"},
                    {"name": "mem_write_en", "width": 1, "description": "数据内存写使能信号"},
                    {"name": "mem_read_en", "width": 1, "description": "数据内存读使能信号"}
                ],
                "clock_domain": "single",
                "reset_type": "async",
                "special_features": [
                    f"{instruction_set}完整指令集支持",
                    f"{bit_width}位RISC-V架构",
                    "哈佛总线结构",
                    "数据前递机制",
                    "完整控制单元",
                    "边界条件处理"
                ],
                "timing_constraints": "目标时钟频率100MHz，关键路径优化",
                "area_constraints": "优化逻辑资源使用，平衡性能与面积",
                "power_considerations": "低功耗设计，门控时钟，逻辑优化"
            }
        
        # 基本类型识别
        if "alu" in prompt_lower:
            module_type = "alu"
            complexity = 6
        elif "adder" in prompt_lower or "加法" in prompt_lower:
            module_type = "adder"
            complexity = 4
        elif "counter" in prompt_lower or "计数" in prompt_lower:
            module_type = "counter"
            complexity = 3
        elif "mux" in prompt_lower or "选择" in prompt_lower:
            module_type = "mux"
            complexity = 2
        else:
            module_type = "generic"
            complexity = 5
        
        # 位宽识别
        bit_width = 8  # 默认
        for width in [64, 32, 16, 8]:
            if str(width) in prompt:
                bit_width = width
                break
        
        return {
            "module_type": module_type,
            "bit_width": bit_width,
            "functionality": f"{bit_width}位{module_type}模块",
            "complexity": complexity,
            "input_ports": [
                {"name": "clk", "width": 1, "description": "时钟信号"},
                {"name": "rst_n", "width": 1, "description": "异步复位"},
                {"name": "data_in", "width": bit_width, "description": "输入数据"}
            ],
            "output_ports": [
                {"name": "data_out", "width": bit_width, "description": "输出数据"}
            ],
            "clock_domain": "single",
            "reset_type": "async",
            "special_features": [],
            "timing_constraints": "标准时序要求",
            "area_constraints": "标准面积要求",
            "power_considerations": "标准功耗要求"
        }
    
    async def _search_existing_modules(self, task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """搜索现有模块"""
        try:
            module_type = task_analysis.get('module_type', '')
            functionality = task_analysis.get('functionality', '')
            
            search_result = await self.search_database_modules(
                module_name=module_type,
                description=functionality,
                limit=3
            )
            
            if search_result.get('success') and search_result.get('result', {}).get('data'):
                self.logger.info(f"🔍 找到 {len(search_result['result']['data'])} 个相关模块")
                return search_result
            else:
                self.logger.info("🔍 未找到相关模块，将完全原创设计")
                return {"success": False, "result": {"data": []}}
                
        except Exception as e:
            self.logger.warning(f"⚠️ 模块搜索失败: {str(e)}")
            return {"success": False, "result": {"data": []}}
    
    async def _generate_verilog_code(self, prompt: str, task_analysis: Dict[str, Any],
                                   search_results: Dict[str, Any], 
                                   file_contents: Dict[str, Dict]) -> str:
        """使用LLM生成高质量Verilog代码"""
        
        # 构建参考信息
        reference_info = ""
        if search_results.get('success') and search_results.get('result', {}).get('data'):
            reference_info = "## 参考现有模块设计\n"
            for module in search_results['result']['data'][:2]:  # 只参考前2个
                reference_info += f"- {module.get('name', 'Unknown')}: {module.get('description', 'No description')}\n"
                if module.get('code'):
                    reference_info += f"  代码片段: {module['code'][:200]}...\n"
            reference_info += "\n"
        
        # 添加文件内容上下文
        if file_contents:
            reference_info += "## 相关文件内容\n"
            for file_path, content_info in file_contents.items():
                reference_info += f"- {file_path}: {content_info.get('description', 'No description')}\n"
                if content_info.get('content'):
                    reference_info += f"  内容: {content_info['content'][:300]}...\n"
            reference_info += "\n"
        
        design_prompt = f"""
你是一位世界级的Verilog/SystemVerilog设计专家，拥有20年的FPGA和ASIC设计经验。请根据以下详细需求设计高质量、工业级的Verilog代码。

## 原始设计需求
{prompt}

## 详细技术规格
{json.dumps(task_analysis, indent=2, ensure_ascii=False)}

{reference_info}

## 设计要求
1. **代码质量**: 使用标准Verilog-2001/SystemVerilog语法，确保代码可综合
2. **架构设计**: 采用清晰的模块化架构，良好的信号命名规范  
3. **时序设计**: 正确处理时钟域、复位逻辑和时序约束
4. **错误处理**: 包含适当的边界检查和错误处理机制
5. **性能优化**: 考虑关键路径延迟和资源使用效率
6. **可维护性**: 添加详细注释和模块文档
7. **可测试性**: 设计便于验证和调试的结构

## 代码规范
- 使用4空格缩进
- 信号名采用snake_case命名
- 模块名采用小写加下划线
- 添加详细的端口注释
- 包含模块功能描述头注释
- 使用参数化设计提高可重用性
- **绝对禁止使用`\`开头的宏定义（如`\verilog`, `\pc_counter`, `\WIDTH`, `\rst_n`）**
- **必须使用`parameter`或`localparam`定义常量**
- **必须使用标准Verilog语法，避免任何非标准语法**

## 端口驱动规则（重要！）
- **output reg 端口**：只能被 `always` 块驱动，不能使用 `assign` 语句
- **output wire 端口**：只能被 `assign` 语句驱动，不能使用 `always` 块
- **推荐模式**：对于时序逻辑输出，使用 `output wire` + 内部 `reg` + `assign`
- **避免混合驱动**：不要对同一个信号使用多种驱动方式

## 严格语法规则
1. **常量定义**: 使用`parameter`或`localparam`，如：`parameter WIDTH = 32;`
2. **信号命名**: 使用标准命名如`clk`, `rst_n`, `pc_counter`, `data_in`, `data_out`
3. **端口声明**: 使用标准格式：`input wire clk` 而不是 `input \clk`
4. **位宽声明**: 使用`[WIDTH-1:0]`而不是`[\WIDTH-1:0]`
5. **模块实例化**: 使用标准实例化语法

## 输出要求 - 严格格式
**必须只输出纯Verilog代码，不允许包含任何markdown格式**

代码结构：
1. 模块头注释（使用//或/* */格式）
2. 参数定义（使用parameter/localparam）
3. 端口声明和详细注释
4. 内部信号声明
5. 主要逻辑实现
6. 适当的断言和检查

## 绝对禁止
❌ 禁止包含```verilog或```等markdown标记
❌ 禁止包含#开头的markdown标题
❌ 禁止包含*或-开头的列表项
❌ 禁止包含反斜杠宏定义
❌ 禁止包含任何非Verilog内容

## 语法检查清单
✅ 使用`parameter`定义常量，如`parameter WIDTH = 32;`
✅ 使用标准信号名：clk, rst_n, data_in, data_out
✅ 所有代码必须是有效的Verilog-2001语法
✅ 模块名使用标准小写字母和下划线
✅ 使用标准端口声明：input/output wire/reg [WIDTH-1:0] signal_name

开始生成纯Verilog代码：
"""
        
        try:
            verilog_code = await self.llm_client.send_prompt(
                prompt=design_prompt,
                temperature=0.4,
                max_tokens=4000
            )
            
            # 移除markdown格式，提取纯Verilog代码
            verilog_code = self._extract_verilog_from_markdown(verilog_code)
            self.logger.info(f"{verilog_code=}")
            self.logger.info(f"✅ LLM Verilog代码生成完成: {len(verilog_code)} 字符")
            return verilog_code.strip()
            
        except Exception as e:
            self.logger.error(f"❌ LLM Verilog代码生成失败: {str(e)}")
            raise Exception(f"LLM代码生成失败: {str(e)}")
    
    async def _analyze_code_quality(self, verilog_code: str) -> QualityMetrics:
        """使用LLM分析代码质量"""
        
        quality_prompt = f"""
你是一位资深的Verilog代码审查专家。请对以下代码进行全面的质量评估：

```verilog
{verilog_code}
```

请从以下维度评估代码质量（每个维度0.0-1.0分）：

1. **syntax_score**: 语法正确性
   - Verilog语法是否正确
   - 是否有语法错误或警告
   - 是否符合可综合代码规范

2. **functionality_score**: 功能实现度
   - 是否正确实现了设计需求
   - 逻辑是否完整和正确
   - 边界条件处理是否恰当

3. **structure_score**: 代码结构
   - 模块化程度和层次结构
   - 信号组织和命名规范
   - 代码布局和可读性

4. **documentation_score**: 文档质量
   - 注释的完整性和清晰度
   - 端口和信号说明
   - 模块功能描述

5. **performance_score**: 性能考虑
   - 关键路径优化
   - 资源使用效率
   - 时序设计合理性

6. **maintainability_score**: 可维护性
   - 代码的可扩展性
   - 参数化设计
   - 调试和测试友好性

请以JSON格式返回评估结果，并包含具体的问题和建议：

{{
    "syntax_score": 0.95,
    "functionality_score": 0.88,
    "structure_score": 0.92,
    "documentation_score": 0.85,
    "performance_score": 0.80,
    "maintainability_score": 0.87,
    "issues": [
        {{"type": "warning", "severity": "medium", "description": "具体问题描述", "location": "代码行数或模块"}},
        {{"type": "error", "severity": "high", "description": "具体错误描述", "location": "代码行数或模块"}}
    ],
    "suggestions": [
        "具体改进建议1",
        "具体改进建议2"
    ],
    "overall_assessment": "整体评价和总结"
}}
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=quality_prompt,
                temperature=0.2,
                max_tokens=4000,
                json_mode=True
            )
            
            quality_data = json.loads(response)
            
            # 计算总体质量分数
            scores = [
                quality_data.get('syntax_score', 0.8),
                quality_data.get('functionality_score', 0.8),
                quality_data.get('structure_score', 0.8),
                quality_data.get('documentation_score', 0.8),
                quality_data.get('performance_score', 0.8),
                quality_data.get('maintainability_score', 0.8)
            ]
            overall_score = sum(scores) / len(scores)
            
            quality_metrics = QualityMetrics(
                overall_score=overall_score,
                syntax_score=quality_data.get('syntax_score', 0.8),
                functionality_score=quality_data.get('functionality_score', 0.8), 
                test_coverage=0.0,  # 设计阶段暂无测试覆盖率
                documentation_quality=quality_data.get('documentation_score', 0.8),
                performance_score=quality_data.get('performance_score', 0.8)
            )
            
            self.logger.info(f"📊 LLM代码质量分析完成: 总分 {overall_score:.2f}")
            
            # 保存详细的质量分析结果
            self.last_quality_analysis = quality_data
            
            return quality_metrics
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM质量分析失败，使用基础评估: {str(e)}")
            return self._basic_quality_analysis(verilog_code)
    
    def _basic_quality_analysis(self, verilog_code: str) -> QualityMetrics:
        """基础质量分析（增强版）"""
        code_lower = verilog_code.lower()
        
        # 语法检查
        has_module = "module" in code_lower and "endmodule" in code_lower
        has_bad_macros = "\\" in verilog_code  # 检查反斜杠宏
        has_define = "`define" in code_lower  # 检查宏定义
        has_parameter = "parameter" in code_lower or "localparam" in code_lower
        
        # 基础功能检查
        has_always = "always" in code_lower
        has_assign = "assign" in code_lower
        has_ports = "input" in code_lower and "output" in code_lower
        
        # 文档检查
        has_comments = "//" in verilog_code or "/*" in verilog_code
        has_header = "/*" in verilog_code  # 检查是否有头注释
        
        # 计算各项分数
        syntax_score = 0.9 if has_module else 0.3
        if has_bad_macros:
            syntax_score = 0.1  # 严重降级如果有反斜杠宏
        elif has_define and not has_parameter:
            syntax_score = 0.6  # 轻微降级如果使用define而非parameter
        
        func_score = 0.8 if (has_always or has_assign) and has_ports else 0.4
        doc_score = 0.9 if has_header else (0.7 if has_comments else 0.3)
        
        # 性能预估（基于代码结构）
        performance_score = 0.75
        if "parameter" in code_lower:
            performance_score = 0.85  # 参数化设计通常性能更好
        
        overall = (syntax_score + doc_score + func_score + performance_score) / 4
        
        return QualityMetrics(
            overall_score=overall,
            syntax_score=syntax_score,
            functionality_score=func_score,
            test_coverage=0.0,
            documentation_quality=doc_score,
            performance_score=performance_score
        )
    
    async def _save_generated_files(self, verilog_code: str, task_analysis: Dict[str, Any],
                                  task_id: str, attempt_number: int = 1) -> list:
        """保存生成的文件"""
        output_files = []
        
        try:
            # 生成文件名
            module_type = task_analysis.get('module_type', 'module')
            bit_width = task_analysis.get('bit_width', 8)
            filename = f"{module_type}_{bit_width}bit.v"
            
            # 使用工件目录确保目录存在
            output_dir = self.artifacts_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = output_dir / filename
            
            # 保存Verilog文件
            file_ref = await self.save_result_to_file(
                content=verilog_code,
                file_path=str(file_path),
                file_type="verilog"
            )
            output_files.append(file_ref)
            
            # 保存设计文档
            doc_content = f"""# {task_analysis.get('functionality', 'Verilog Module')} 设计文档

## 模块信息
- 名称: {module_type}
- 位宽: {task_analysis.get('bit_width', 8)}
- 复杂度: {task_analysis.get('complexity', 5)}/10
- 时钟域: {task_analysis.get('clock_domain', 'single')}
- 复位类型: {task_analysis.get('reset_type', 'async')}

## 功能描述
{task_analysis.get('functionality', 'Basic functionality')}

## 输入端口
{chr(10).join(f"- {port.get('name', 'unknown')} [{port.get('width', 1)-1 if port.get('width', 1) > 1 else ''}:0]: {port.get('description', 'No description')}" for port in task_analysis.get('input_ports', []))}

## 输出端口
{chr(10).join(f"- {port.get('name', 'unknown')} [{port.get('width', 1)-1 if port.get('width', 1) > 1 else ''}:0]: {port.get('description', 'No description')}" for port in task_analysis.get('output_ports', []))}

## 特殊功能
{chr(10).join(f"- {feature}" for feature in task_analysis.get('special_features', []))}

## 约束条件
- 时序约束: {task_analysis.get('timing_constraints', 'N/A')}
- 面积约束: {task_analysis.get('area_constraints', 'N/A')}
- 功耗考虑: {task_analysis.get('power_considerations', 'N/A')}

## 生成信息
- 任务ID: {task_id}
- 生成智能体: {self.agent_id}
"""
            
            doc_path = output_dir / f"{module_type}_{bit_width}bit_doc.md"
            doc_ref = await self.save_result_to_file(
                content=doc_content,
                file_path=str(doc_path),
                file_type="documentation"
            )
            output_files.append(doc_ref)
            
            self.logger.info(f"💾 文件保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 文件保存失败: {str(e)}")
            return []
    
    async def _save_debug_code(self, verilog_code: str, task_id: str, attempt_number: int) -> None:
        """保存调试代码到可访问目录"""
        try:
            debug_dir = self.artifacts_dir / "debug_iterations"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            debug_file = debug_dir / f"iteration_{attempt_number}_{task_id}.v"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(verilog_code)
            
            self.logger.info(f"🔍 调试代码已保存: {debug_file}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 调试代码保存失败: {str(e)}")
    
    async def _basic_verilog_validation(self, verilog_code: str, attempt_number: int = 1) -> Dict[str, Any]:
        """基础Verilog代码验证"""
        try:
            # 使用工件目录而不是临时目录，便于调试
            debug_dir = self.artifacts_dir / "debug_validation"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建调试Verilog文件
            test_file = debug_dir / f"test_module_attempt_{attempt_number}.v"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(verilog_code)
            
            self.logger.info(f"🔍 调试文件已保存: {test_file}")
            
            # 尝试编译
            compile_cmd = ['iverilog', '-o', str(debug_dir / f'test_attempt_{attempt_number}'), str(test_file)]
            
            compile_process = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(debug_dir)
            )
            
            if compile_process.returncode == 0:
                return {
                    'success': True,
                    'warnings': []
                }
            else:
                return {
                    'success': False,
                    'error': compile_process.stderr.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '编译超时'
            }
        except FileNotFoundError:
            return {
                'success': True,
                'warnings': ['iverilog未安装，跳过编译验证']
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'验证异常: {str(e)}'
            }
    
    async def _regenerate_verilog_code(self, prompt: str, task_analysis: Dict[str, Any],
                                     previous_code: str, error_message: str) -> str:
        """基于错误信息重新生成Verilog代码"""
        try:
            regenerate_prompt = f"""
你是一位资深的Verilog设计专家。之前的Verilog代码存在以下问题，请重新生成修复后的代码。

## 设计需求
{prompt}

## 模块规格
{json.dumps(task_analysis, indent=2, ensure_ascii=False)}

## 之前的代码（存在错误）
```verilog
{previous_code}
```

## 错误信息
{error_message}

## 关键修复规则
1. **output reg 端口驱动规则**：
   - 如果端口声明为 `output reg`，只能被 `always` 块驱动，不能使用 `assign` 语句
   - 如果端口声明为 `output wire`，只能被 `assign` 语句驱动，不能使用 `always` 块
   - 解决方案：要么改为 `output wire` + `assign`，要么在 `always` 块中直接驱动 `output reg`

2. **常见错误模式**：
   ```verilog
   // ❌ 错误：output reg 被 assign 驱动
   output reg [31:0] pc_out;
   reg [31:0] pc_reg;
   always @(posedge clk) pc_reg <= new_value;
   assign pc_out = pc_reg;  // 错误！
   
   // ✅ 正确方案1：改为 output wire
   output wire [31:0] pc_out;
   reg [31:0] pc_reg;
   always @(posedge clk) pc_reg <= new_value;
   assign pc_out = pc_reg;  // 正确！
   
   // ✅ 正确方案2：直接驱动 output reg
   output reg [31:0] pc_out;
   always @(posedge clk) pc_out <= new_value;  // 直接驱动！
   ```

3. **信号绑定错误**：
   - 确保所有使用的信号都已正确声明
   - 检查信号名拼写是否正确
   - 确保端口连接正确

## 修复要求
1. **精确定位错误**：分析错误信息，找到确切的语法或逻辑问题
2. **完整修复**：提供修复后的完整代码
3. **保持功能**：确保修复后的代码实现原有的设计功能
4. **最佳实践**：遵循Verilog最佳实践

请返回修复后的完整Verilog代码：
"""
            
            fixed_code = await self.llm_client.send_prompt(
                prompt=regenerate_prompt,
                temperature=0.2,
                max_tokens=4000
            )
            
            # 移除markdown格式，提取纯Verilog代码
            fixed_code = self._extract_verilog_from_markdown(fixed_code)
            
            return fixed_code.strip()
            
        except Exception as e:
            self.logger.error(f"❌ 代码重新生成失败: {str(e)}")
            return previous_code  # 返回原代码如果修复失败
    
    def _extract_verilog_from_markdown(self, content: str) -> str:
        """从markdown格式中提取纯Verilog代码"""
        import re
        
        # 查找所有verilog代码块
        verilog_blocks = re.findall(r'```verilog\s*\n(.*?)\n\s*```', content, re.DOTALL)
        
        if verilog_blocks:
            # 如果找到verilog代码块，提取所有块
            verilog_code = '\n\n'.join(block.strip() for block in verilog_blocks)
            self.logger.info(f"📋 从markdown中提取Verilog代码: {len(verilog_code)} 字符")
            return verilog_code
        
        # 如果没有找到verilog代码块，尝试其他格式
        # 查找```代码块
        code_blocks = re.findall(r'```\s*\n(.*?)\n\s*```', content, re.DOTALL)
        if code_blocks:
            code = '\n\n'.join(block.strip() for block in code_blocks)
            # 检查是否包含Verilog特征
            if 'module' in code and 'endmodule' in code:
                self.logger.info(f"📋 从通用代码块中提取Verilog代码: {len(code)} 字符")
                return code
        
        # 如果以上都失败，尝试清理文本
        lines = content.split('\n')
        clean_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过markdown标题
            if stripped.startswith('#'):
                continue
            
            # 跳过空行和注释行
            if not stripped or stripped.startswith('-') or stripped.startswith('*'):
                continue
            
            # 跳过非Verilog内容
            if '```' in stripped:
                if 'verilog' in stripped.lower():
                    in_code = True
                else:
                    in_code = False
                continue
            
            if in_code or ('module' in stripped.lower() or 'endmodule' in stripped.lower()):
                clean_lines.append(line)
        
        clean_content = '\n'.join(clean_lines)
        
        # 最终检查：是否包含Verilog特征
        if 'module' in clean_content and 'endmodule' in clean_content:
            return clean_content
        
        # 如果清理后仍然有问题，返回原始内容用于调试
        self.logger.warning("⚠️ 无法提取有效Verilog代码，返回清理后的内容")
        return clean_content.strip()

    async def _create_design_response(self, task_id: str, task_analysis: Dict[str, Any],
                                    quality_metrics: QualityMetrics, output_files: list,
                                    verilog_code: str, iterations: int = 1, warnings: List[str] = None) -> str:
        """创建标准化设计响应"""
        
        builder = self.create_response_builder(task_id)
        
        # 添加生成的文件
        for file_ref in output_files:
            builder.add_generated_file(
                file_ref.file_path,
                file_ref.file_type,
                file_ref.description
            )
        
        # 根据质量分数添加问题和建议
        if hasattr(self, 'last_quality_analysis') and self.last_quality_analysis:
            # 添加LLM分析的具体问题
            for issue in self.last_quality_analysis.get('issues', []):
                builder.add_issue(
                    issue.get('type', 'warning'),
                    issue.get('severity', 'medium'),
                    issue.get('description', ''),
                    location=issue.get('location', ''),
                    solution=""
                )
            
            # 添加LLM建议作为下一步
            for suggestion in self.last_quality_analysis.get('suggestions', []):
                builder.add_next_step(suggestion)
        
        # 通用质量相关的问题和建议
        if quality_metrics.overall_score < 0.7:
            builder.add_issue(
                "warning", "high",
                f"代码质量需要提升 (总分: {quality_metrics.overall_score:.2f})",
                solution="建议进行代码审查和重构"
            )
        elif quality_metrics.overall_score < 0.8:
            builder.add_issue(
                "suggestion", "medium", 
                "代码质量良好，可进一步优化",
                solution="考虑性能和可维护性优化"
            )
        
        if quality_metrics.syntax_score < 0.8:
            builder.add_issue(
                "error", "high",
                "语法检查发现潜在问题",
                solution="使用Verilog lint工具进行语法验证"
            )
        
        # 添加标准下一步建议
        builder.add_next_step("对生成的Verilog代码进行语法验证")
        builder.add_next_step("创建对应的测试平台(testbench)")
        builder.add_next_step("进行功能仿真验证")
        
        if quality_metrics.performance_score < 0.8:
            builder.add_next_step("进行时序分析和关键路径优化")
        
        # 添加元数据
        builder.add_metadata("module_type", task_analysis.get('module_type'))
        builder.add_metadata("bit_width", task_analysis.get('bit_width'))
        builder.add_metadata("complexity", task_analysis.get('complexity'))
        builder.add_metadata("clock_domain", task_analysis.get('clock_domain'))
        builder.add_metadata("reset_type", task_analysis.get('reset_type'))
        builder.add_metadata("code_lines", len(verilog_code.split('\n')))
        builder.add_metadata("file_count", len(output_files))
        builder.add_metadata("llm_powered", True)
        builder.add_metadata("iterations", iterations)
        builder.add_metadata("warnings", warnings or [])
        
        # 构建响应
        status = TaskStatus.SUCCESS if quality_metrics.overall_score >= 0.7 else TaskStatus.REQUIRES_RETRY
        completion = 100.0 if status == TaskStatus.SUCCESS else 80.0
        
        message = f"成功设计了{task_analysis.get('functionality', 'Verilog模块')}"
        if iterations > 1:
            message += f"（经过{iterations}次迭代修复）"
        message += f"，代码质量分数: {quality_metrics.overall_score:.2f}"
        
        response = builder.build(
            response_type=ResponseType.TASK_COMPLETION,
            status=status,
            message=message,
            completion_percentage=completion,
            quality_metrics=quality_metrics
        )
        
        return response.format_response(ResponseFormat.JSON)
    
    # ==========================================================================
    # 🔧 Function Calling 工具实现方法
    # ==========================================================================
    
    async def _tool_analyze_design_requirements(self, requirements: str, **kwargs) -> Dict[str, Any]:
        """工具：分析设计需求"""
        try:
            self.logger.info("🔧 工具调用: 分析设计需求")
            
            analysis = await self._analyze_design_requirements(requirements)
            
            return {
                "success": True,
                "analysis": analysis,
                "message": "设计需求分析完成"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计需求分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"分析失败: {str(e)}",
                "analysis": None
            }
    
    async def _tool_search_existing_modules(self, module_type: str = "", functionality: str = "", **kwargs) -> Dict[str, Any]:
        """工具：搜索现有模块"""
        try:
            self.logger.info("🔧 工具调用: 搜索现有模块")
            
            search_result = await self.search_database_modules(
                module_name=module_type,
                description=functionality,
                limit=5
            )
            
            return {
                "success": True,
                "modules": search_result.get('result', {}).get('data', []),
                "count": len(search_result.get('result', {}).get('data', [])),
                "message": "模块搜索完成"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 模块搜索失败: {str(e)}")
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}",
                "modules": []
            }
    
    async def _tool_generate_verilog_code(self, requirements: str, module_info: Dict = None, **kwargs) -> Dict[str, Any]:
        """工具：生成Verilog代码"""
        try:
            self.logger.info("🔧 工具调用: 生成Verilog代码")
            
            # 如果没有提供module_info，先分析需求
            if not module_info:
                module_info = await self._analyze_design_requirements(requirements)
            
            # 搜索相关模块
            search_results = await self._search_existing_modules(module_info)
            
            # 生成代码
            verilog_code = await self._generate_verilog_code(
                requirements, module_info, search_results, {}
            )
            
            return {
                "success": True,
                "code": verilog_code,
                "module_info": module_info,
                "message": "Verilog代码生成完成"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog代码生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"代码生成失败: {str(e)}",
                "code": None
            }
    
    async def _tool_analyze_code_quality(self, code: str, **kwargs) -> Dict[str, Any]:
        """工具：分析代码质量"""
        try:
            self.logger.info("🔧 工具调用: 分析代码质量")
            
            quality_metrics = await self._analyze_code_quality(code)
            
            return {
                "success": True,
                "quality_metrics": {
                    "overall_score": quality_metrics.overall_score,
                    "syntax_score": quality_metrics.syntax_score,
                    "functionality_score": quality_metrics.functionality_score,
                    "documentation_quality": quality_metrics.documentation_quality,
                    "performance_score": quality_metrics.performance_score
                },
                "message": "代码质量分析完成"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 代码质量分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"质量分析失败: {str(e)}",
                "quality_metrics": None
            }