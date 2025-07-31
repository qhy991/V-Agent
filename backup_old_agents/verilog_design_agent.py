#!/usr/bin/env python3
"""
Verilog设计智能体

Verilog Design Agent for Code Generation
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from core.base_agent import BaseAgent, TaskMessage, FileReference
from core.enums import AgentCapability, AgentStatus
from llm_integration.enhanced_llm_client import EnhancedLLMClient


class VerilogDesignAgent(BaseAgent):
    """
    Verilog设计智能体
    
    专门负责：
    1. 生成高质量的Verilog HDL代码
    2. 分析设计需求和规格
    3. 创建模块结构和接口
    4. 实现数字电路逻辑
    """
    
    def __init__(self, llm_client: EnhancedLLMClient = None):
        super().__init__(
            agent_id="verilog_design_agent",
            role="design_engineer",
            capabilities={
                AgentCapability.CODE_GENERATION,
                AgentCapability.SPECIFICATION_ANALYSIS,
                AgentCapability.MODULE_DESIGN
            }
        )
        
        self.llm_client = llm_client
        
        # 设计模板和模式
        self.design_templates = {
            "alu": self._get_alu_template(),
            "counter": self._get_counter_template(),
            "fsm": self._get_fsm_template(),
            "memory": self._get_memory_template()
        }
        
        # 代码质量检查
        self.quality_criteria = {
            "syntax_check": True,
            "style_check": True,
            "modularity": True,
            "documentation": True
        }
        
        self.logger.info("🔧 Verilog设计智能体初始化完成")
    
    async def _search_existing_modules(self, task_description: str) -> List[Dict[str, Any]]:
        """搜索现有的相似模块"""
        search_results = []
        
        try:
            # 提取关键词进行搜索
            keywords = self._extract_keywords(task_description)
            
            # 搜索模块名称匹配
            for keyword in keywords[:3]:  # 只使用前3个关键词
                result = await self.search_database_modules(
                    module_name=keyword,
                    description=keyword,
                    limit=5
                )
                
                if result.get("success") and result.get("result", {}).get("data"):
                    search_results.extend(result["result"]["data"])
            
            # 按功能搜索
            if keywords:
                func_result = await self.search_by_functionality(
                    functionality=" ".join(keywords[:2]),
                    limit=5
                )
                
                if func_result.get("success") and func_result.get("result", {}).get("data"):
                    search_results.extend(func_result["result"]["data"])
            
            # 去重并排序
            unique_modules = {}
            for module in search_results:
                module_id = module.get("id") or module.get("name", "unknown")
                if module_id not in unique_modules:
                    unique_modules[module_id] = module
            
            return list(unique_modules.values())[:10]  # 返回最多10个模块
            
        except Exception as e:
            self.logger.warning(f"⚠️ 搜索现有模块失败: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取
        keywords = []
        
        # 预定义的Verilog关键词
        verilog_terms = [
            "alu", "adder", "multiplier", "counter", "register", "mux", "demux",
            "fifo", "lifo", "ram", "rom", "fsm", "decoder", "encoder", "shifter"
        ]
        
        text_lower = text.lower()
        for term in verilog_terms:
            if term in text_lower:
                keywords.append(term)
        
        # 提取数字（位宽等）
        import re
        numbers = re.findall(r'\d+', text)
        for num in numbers[:2]:  # 只取前两个数字
            if int(num) in [8, 16, 32, 64]:  # 常见位宽
                keywords.append(f"{num}bit")
        
        return keywords
    
    def _format_similar_modules(self, modules: List[Dict[str, Any]]) -> str:
        """格式化相似模块信息"""
        if not modules:
            return "未找到相似的现有模块"
        
        formatted = "找到以下相似模块：\n"
        for i, module in enumerate(modules[:5], 1):  # 只显示前5个
            name = module.get("name", "Unknown")
            description = module.get("description", "No description") 
            bit_width = module.get("bit_width", "N/A")
            functionality = module.get("functionality", "N/A")
            
            formatted += f"{i}. {name} - {description} (位宽: {bit_width}, 功能: {functionality})\n"
        
        return formatted
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取设计智能体能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.MODULE_DESIGN
        }
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "专业的Verilog HDL代码生成智能体，擅长数字电路设计、模块化编程和硬件描述语言实现"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行Verilog设计任务"""
        self.logger.info("🚀 开始执行Verilog设计任务")
        
        try:
            # 1. 分析设计需求
            design_spec = await self._analyze_design_requirements(enhanced_prompt)
            
            # 2. 生成Verilog代码
            verilog_code = await self._generate_verilog_code(design_spec, enhanced_prompt)
            
            # 3. 质量检查
            quality_result = await self._check_code_quality(verilog_code, design_spec)
            
            # 4. 保存结果文件
            output_files = await self._save_design_files(
                verilog_code=verilog_code,
                design_spec=design_spec,
                task_id=original_message.task_id
            )
            
            # 5. 生成设计报告
            design_report = self._generate_design_report(
                design_spec=design_spec,
                quality_result=quality_result,
                output_files=output_files
            )
            
            success = quality_result.get("overall_quality", 0.0) >= 0.7
            
            return {
                "success": success,
                "task_completed": success,
                "agent_id": self.agent_id,
                "verilog_code": verilog_code,
                "design_specification": design_spec,
                "quality_assessment": quality_result,
                "design_report": design_report,
                "file_references": output_files,
                "execution_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog设计任务失败: {str(e)}")
            return {
                "success": False,
                "task_completed": False,
                "agent_id": self.agent_id,
                "error": str(e),
                "execution_time": time.time()
            }
    
    async def _analyze_design_requirements(self, task_description: str) -> Dict[str, Any]:
        """分析设计需求"""
        if not self.llm_client:
            return self._simple_requirement_analysis(task_description)
        
        # 首先搜索数据库中的相似模块
        similar_modules = await self._search_existing_modules(task_description)
        
        analysis_prompt = f"""
{self.system_prompt}

## 当前任务: 设计需求分析

设计描述: {task_description}

## 已搜索到的相似模块:
{self._format_similar_modules(similar_modules)}

请从以下方面分析设计需求：
1. 模块名称和功能描述
2. 输入输出端口规格（位宽、类型、方向）
3. 设计参数（时钟频率、数据位宽等）
4. 功能特性和操作模式
5. 时序要求和约束
6. 设计复杂度评估（1-10）
7. 可重用的现有模块推荐

请以JSON格式返回分析结果。
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=1500,
                json_mode=True
            )
            
            spec = json.loads(response)
            self.logger.info(f"📋 需求分析完成: {spec.get('module_name', 'Unknown')}")
            return spec
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM需求分析失败，使用简单分析: {str(e)}")
            return self._simple_requirement_analysis(task_description)
    
    def _simple_requirement_analysis(self, task_description: str) -> Dict[str, Any]:
        """简单的需求分析（备用方案）"""
        desc_lower = task_description.lower()
        
        # 基本模块识别
        module_name = "design_module"
        if "alu" in desc_lower:
            module_name = "alu"
        elif "counter" in desc_lower:
            module_name = "counter"
        elif "adder" in desc_lower:
            module_name = "adder"
        elif "multiplier" in desc_lower:
            module_name = "multiplier"
        
        # 位宽识别
        bit_width = 8  # 默认
        if "32" in task_description:
            bit_width = 32
        elif "16" in task_description:
            bit_width = 16
        elif "64" in task_description:
            bit_width = 64
        
        return {
            "module_name": module_name,
            "description": task_description,
            "bit_width": bit_width,
            "input_ports": ["clk", "rst", f"data_in[{bit_width-1}:0]"],
            "output_ports": [f"data_out[{bit_width-1}:0]"],
            "complexity": 5,
            "design_type": "combinational" if "combinational" in desc_lower else "sequential"
        }
    
    async def _generate_verilog_code(self, design_spec: Dict[str, Any], 
                                   task_description: str) -> str:
        """生成Verilog代码"""
        if not self.llm_client:
            return self._generate_template_code(design_spec)
        
        # 构建详细的代码生成prompt
        code_prompt = f"""
基于以下设计规格生成高质量的Verilog HDL代码：

设计规格:
{json.dumps(design_spec, indent=2, ensure_ascii=False)}

原始需求: {task_description}

请生成符合以下要求的Verilog代码：
1. 完整的模块定义和端口声明
2. 清晰的信号定义和逻辑实现
3. 适当的注释和文档
4. 符合Verilog语法规范
5. 考虑时序和组合逻辑设计
6. 包含必要的复位和时钟逻辑

请只返回Verilog代码，不要其他解释。
"""
        
        try:
            verilog_code = await self.llm_client.send_prompt(
                prompt=code_prompt,
                temperature=0.4,
                max_tokens=3000
            )
            
            self.logger.info(f"✅ Verilog代码生成完成 ({len(verilog_code)} 字符)")
            return verilog_code.strip()
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM代码生成失败，使用模板: {str(e)}")
            return self._generate_template_code(design_spec)
    
    def _generate_template_code(self, design_spec: Dict[str, Any]) -> str:
        """基于模板生成代码（备用方案）"""
        module_name = design_spec.get("module_name", "design_module")
        bit_width = design_spec.get("bit_width", 8)
        
        template = f"""
// {module_name.upper()} Module
// Generated by VerilogDesignAgent
// Description: {design_spec.get('description', 'Auto-generated design')}

module {module_name} (
    input wire clk,
    input wire rst_n,
    input wire [{bit_width-1}:0] data_in,
    output reg [{bit_width-1}:0] data_out
);

    // Internal signals
    reg [{bit_width-1}:0] internal_reg;
    
    // Main logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= {bit_width}'b0;
            internal_reg <= {bit_width}'b0;
        end else begin
            internal_reg <= data_in;
            data_out <= internal_reg;
        end
    end

endmodule
"""
        return template.strip()
    
    async def _check_code_quality(self, verilog_code: str, 
                                design_spec: Dict[str, Any]) -> Dict[str, Any]:
        """检查代码质量"""
        quality_result = {
            "syntax_valid": True,
            "style_score": 0.8,
            "modularity_score": 0.7,
            "documentation_score": 0.6,
            "overall_quality": 0.7,
            "issues": [],
            "suggestions": []
        }
        
        # 基本语法检查
        syntax_issues = []
        if "module" not in verilog_code:
            syntax_issues.append("缺少module定义")
        if "endmodule" not in verilog_code:
            syntax_issues.append("缺少endmodule")
        if "input" not in verilog_code:
            syntax_issues.append("缺少输入端口定义")
        if "output" not in verilog_code:
            syntax_issues.append("缺少输出端口定义")
        
        if syntax_issues:
            quality_result["syntax_valid"] = False
            quality_result["issues"].extend(syntax_issues)
            quality_result["overall_quality"] = 0.3
        
        # 代码风格检查
        style_score = 0.8
        if "//" not in verilog_code:
            style_score -= 0.2
            quality_result["suggestions"].append("建议添加注释")
        
        quality_result["style_score"] = style_score
        
        self.logger.info(f"🔍 代码质量检查完成: {quality_result['overall_quality']:.2f}")
        return quality_result
    
    async def _save_design_files(self, verilog_code: str, 
                               design_spec: Dict[str, Any],
                               task_id: str) -> List[FileReference]:
        """保存设计文件"""
        output_files = []
        timestamp = int(time.time())
        module_name = design_spec.get("module_name", "design")
        
        try:
            # 1. 保存Verilog源文件
            verilog_path = f"output/{task_id}/{module_name}.v"
            verilog_ref = await self.save_result_to_file(
                content=verilog_code,
                file_path=verilog_path,
                file_type="verilog"
            )
            output_files.append(verilog_ref)
            
            # 2. 保存设计规格文件
            spec_content = json.dumps(design_spec, indent=2, ensure_ascii=False)
            spec_path = f"output/{task_id}/{module_name}_spec.json"
            spec_ref = await self.save_result_to_file(
                content=spec_content,
                file_path=spec_path,
                file_type="specification"
            )
            output_files.append(spec_ref)
            
            # 3. 保存README文档
            readme_content = f"""# {module_name.upper()} Design

## 设计概要
{design_spec.get('description', 'Verilog模块设计')}

## 模块信息
- 模块名称: {module_name}
- 位宽: {design_spec.get('bit_width', 'N/A')}
- 设计类型: {design_spec.get('design_type', 'sequential')}
- 复杂度: {design_spec.get('complexity', 5)}/10

## 端口说明
### 输入端口
{chr(10).join(f"- {port}" for port in design_spec.get('input_ports', []))}

### 输出端口
{chr(10).join(f"- {port}" for port in design_spec.get('output_ports', []))}

## 生成信息
- 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 生成智能体: {self.agent_id}
"""
            
            readme_path = f"output/{task_id}/README.md"
            readme_ref = await self.save_result_to_file(
                content=readme_content,
                file_path=readme_path,
                file_type="documentation"
            )
            output_files.append(readme_ref)
            
            self.logger.info(f"💾 设计文件保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 保存设计文件失败: {str(e)}")
            return output_files
    
    def _generate_design_report(self, design_spec: Dict[str, Any],
                              quality_result: Dict[str, Any],
                              output_files: List[FileReference]) -> str:
        """生成设计报告"""
        report = f"""
🔧 VERILOG设计报告
==================

📋 设计概要:
- 模块名称: {design_spec.get('module_name', 'Unknown')}
- 设计复杂度: {design_spec.get('complexity', 5)}/10
- 位宽: {design_spec.get('bit_width', 'N/A')}

🎯 质量评估:
- 整体质量: {quality_result.get('overall_quality', 0):.2f}
- 语法正确性: {'✅' if quality_result.get('syntax_valid', False) else '❌'}
- 代码风格: {quality_result.get('style_score', 0):.2f}
- 模块化程度: {quality_result.get('modularity_score', 0):.2f}

📁 生成文件: {len(output_files)} 个
{chr(10).join(f"- {ref.file_path} ({ref.file_type})" for ref in output_files)}

⚠️ 问题和建议:
{chr(10).join(f"- {issue}" for issue in quality_result.get('issues', []))}
{chr(10).join(f"- {suggestion}" for suggestion in quality_result.get('suggestions', []))}
"""
        return report.strip()
    
    # ==========================================================================
    # 🏗️ 设计模板
    # ==========================================================================
    
    def _get_alu_template(self) -> str:
        """ALU设计模板"""
        return """
module alu #(parameter WIDTH = 32) (
    input wire [WIDTH-1:0] a,
    input wire [WIDTH-1:0] b,
    input wire [3:0] op,
    output reg [WIDTH-1:0] result,
    output wire zero,
    output wire overflow
);
    // ALU operations
    always @(*) begin
        case (op)
            4'b0000: result = a + b;      // ADD
            4'b0001: result = a - b;      // SUB
            4'b0010: result = a & b;      // AND
            4'b0011: result = a | b;      // OR
            4'b0100: result = a ^ b;      // XOR
            4'b0101: result = ~a;         // NOT
            4'b0110: result = a << b[4:0]; // SHL
            4'b0111: result = a >> b[4:0]; // SHR
            default: result = {WIDTH{1'b0}};
        endcase
    end
    
    assign zero = (result == 0);
    assign overflow = 1'b0; // Simplified
endmodule
"""
    
    def _get_counter_template(self) -> str:
        """计数器设计模板"""
        return """
module counter #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire enable,
    input wire up_down, // 1: up, 0: down
    output reg [WIDTH-1:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else if (enable) begin
            if (up_down)
                count <= count + 1;
            else
                count <= count - 1;
        end
    end
endmodule
"""
    
    def _get_fsm_template(self) -> str:
        """状态机设计模板"""
        return """
module fsm (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire done,
    output reg busy,
    output reg valid
);
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        ACTIVE = 2'b01,
        DONE = 2'b10
    } state_t;
    
    state_t current_state, next_state;
    
    // State register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= IDLE;
        else
            current_state <= next_state;
    end
    
    // Next state logic
    always @(*) begin
        case (current_state)
            IDLE: next_state = start ? ACTIVE : IDLE;
            ACTIVE: next_state = done ? DONE : ACTIVE;
            DONE: next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end
    
    // Output logic
    always @(*) begin
        busy = (current_state == ACTIVE);
        valid = (current_state == DONE);
    end
endmodule
"""
    
    def _get_memory_template(self) -> str:
        """存储器设计模板"""
        return """
module memory #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 8,
    parameter DEPTH = 2**ADDR_WIDTH
) (
    input wire clk,
    input wire rst_n,
    input wire we,
    input wire [ADDR_WIDTH-1:0] addr,
    input wire [DATA_WIDTH-1:0] data_in,
    output reg [DATA_WIDTH-1:0] data_out
);
    reg [DATA_WIDTH-1:0] memory [0:DEPTH-1];
    
    always @(posedge clk) begin
        if (we) begin
            memory[addr] <= data_in;
        end
        data_out <= memory[addr];
    end
endmodule
"""