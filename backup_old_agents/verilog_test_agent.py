#!/usr/bin/env python3
"""
Verilog测试智能体

Verilog Test Agent for Testbench Generation
"""

import asyncio
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from core.base_agent import BaseAgent, TaskMessage, FileReference
from core.enums import AgentCapability, AgentStatus
from llm_integration.enhanced_llm_client import EnhancedLLMClient


class VerilogTestAgent(BaseAgent):
    """
    Verilog测试智能体
    
    专门负责：
    1. 生成全面的testbench文件
    2. 设计测试向量和测试场景
    3. 验证功能正确性
    4. 生成测试报告和覆盖率分析
    """
    
    def __init__(self, llm_client: EnhancedLLMClient = None):
        super().__init__(
            agent_id="verilog_test_agent",
            role="test_engineer",
            capabilities={
                AgentCapability.TEST_GENERATION,
                AgentCapability.VERIFICATION,
                AgentCapability.COVERAGE_ANALYSIS
            }
        )
        
        self.llm_client = llm_client
        
        # 测试模式配置
        self.test_modes = {
            "functional": "功能测试",
            "corner_case": "边界情况测试", 
            "stress": "压力测试",
            "random": "随机测试"
        }
        
        # 测试覆盖率目标
        self.coverage_targets = {
            "statement": 0.95,
            "branch": 0.90,
            "condition": 0.85,
            "toggle": 0.80
        }
        
        self.logger.info("🧪 Verilog测试智能体初始化完成")
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取测试智能体能力"""
        return {
            AgentCapability.TEST_GENERATION,
            AgentCapability.VERIFICATION,
            AgentCapability.COVERAGE_ANALYSIS
        }
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "专业的Verilog测试智能体，擅长testbench生成、功能验证、测试向量设计和覆盖率分析"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行Verilog测试任务"""
        self.logger.info("🧪 开始执行Verilog测试任务")
        
        try:
            # 1. 分析待测试的Verilog代码
            dut_analysis = await self._analyze_design_under_test(enhanced_prompt, file_contents)
            
            # 2. 设计测试策略
            test_strategy = await self._design_test_strategy(dut_analysis)
            
            # 3. 生成testbench代码
            testbench_code = await self._generate_testbench(dut_analysis, test_strategy)
            
            # 4. 生成测试向量
            test_vectors = await self._generate_test_vectors(dut_analysis, test_strategy)
            
            # 5. 保存测试文件
            output_files = await self._save_test_files(
                testbench_code=testbench_code,
                test_vectors=test_vectors,
                dut_analysis=dut_analysis,
                task_id=original_message.task_id
            )
            
            # 6. 生成测试报告
            test_report = self._generate_test_report(
                dut_analysis=dut_analysis,
                test_strategy=test_strategy,
                output_files=output_files
            )
            
            return {
                "success": True,
                "task_completed": True,
                "agent_id": self.agent_id,
                "testbench_code": testbench_code,
                "test_vectors": test_vectors,
                "dut_analysis": dut_analysis,
                "test_strategy": test_strategy,
                "test_report": test_report,
                "file_references": output_files,
                "execution_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog测试任务失败: {str(e)}")
            return {
                "success": False,
                "task_completed": False,
                "agent_id": self.agent_id,
                "error": str(e),
                "execution_time": time.time()
            }
    
    async def _analyze_design_under_test(self, task_description: str, 
                                       file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """分析待测试设计"""
        # 查找Verilog源码文件
        verilog_content = None
        verilog_file = None
        
        for file_path, content_info in file_contents.items():
            if content_info.get("type") == "verilog" or file_path.endswith(".v"):
                verilog_content = content_info.get("content", "")
                verilog_file = file_path
                break
        
        if not verilog_content:
            # 如果没有找到Verilog文件，尝试从任务描述中提取
            return self._simple_dut_analysis(task_description)
        
        if not self.llm_client:
            return self._parse_verilog_manually(verilog_content, verilog_file)
        
        # 使用LLM分析Verilog代码
        analysis_prompt = f"""
请分析以下Verilog模块，提取测试所需的关键信息：

文件: {verilog_file}
Verilog代码:
{verilog_content}

请分析并提取：
1. 模块名称和功能描述
2. 输入端口（名称、位宽、类型）
3. 输出端口（名称、位宽、类型）
4. 参数定义
5. 主要功能和操作
6. 时钟和复位信号
7. 测试关键点和边界条件
8. 预期的测试场景

请以JSON格式返回分析结果。
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                temperature=0.2,
                max_tokens=2000,
                json_mode=True
            )
            
            analysis = json.loads(response)
            analysis["source_file"] = verilog_file
            analysis["source_code"] = verilog_content
            
            self.logger.info(f"📋 DUT分析完成: {analysis.get('module_name', 'Unknown')}")
            return analysis
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM DUT分析失败，使用手动解析: {str(e)}")
            return self._parse_verilog_manually(verilog_content, verilog_file)
    
    def _parse_verilog_manually(self, verilog_content: str, 
                              verilog_file: str) -> Dict[str, Any]:
        """手动解析Verilog代码"""
        analysis = {
            "source_file": verilog_file,
            "source_code": verilog_content,
            "module_name": "unknown",
            "inputs": [],
            "outputs": [],
            "parameters": [],
            "has_clock": False,
            "has_reset": False
        }
        
        try:
            # 查找module声明
            module_match = re.search(r'module\s+(\w+)', verilog_content)
            if module_match:
                analysis["module_name"] = module_match.group(1)
            
            # 查找输入端口
            input_matches = re.findall(r'input\s+.*?(\w+)', verilog_content, re.MULTILINE)
            analysis["inputs"] = input_matches
            
            # 查找输出端口
            output_matches = re.findall(r'output\s+.*?(\w+)', verilog_content, re.MULTILINE)
            analysis["outputs"] = output_matches
            
            # 检查时钟和复位信号
            analysis["has_clock"] = "clk" in verilog_content.lower()
            analysis["has_reset"] = any(reset in verilog_content.lower() 
                                     for reset in ["rst", "reset", "rst_n"])
            
            self.logger.info(f"🔍 手动解析完成: {analysis['module_name']}")
            
        except Exception as e:
            self.logger.error(f"❌ 手动解析失败: {str(e)}")
        
        return analysis
    
    def _simple_dut_analysis(self, task_description: str) -> Dict[str, Any]:
        """简单的DUT分析（备用方案）"""
        desc_lower = task_description.lower()
        
        return {
            "module_name": "dut",
            "description": task_description,
            "inputs": ["clk", "rst_n", "data_in"],
            "outputs": ["data_out"],
            "has_clock": "clk" in desc_lower or "clock" in desc_lower,
            "has_reset": "rst" in desc_lower or "reset" in desc_lower,
            "test_scenarios": ["basic_functionality", "reset_test", "edge_cases"]
        }
    
    async def _design_test_strategy(self, dut_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """设计测试策略"""
        module_name = dut_analysis.get("module_name", "dut")
        has_clock = dut_analysis.get("has_clock", False)
        has_reset = dut_analysis.get("has_reset", False)
        
        # 基本测试策略
        strategy = {
            "test_modes": [],
            "test_scenarios": [],
            "stimulus_types": [],
            "coverage_goals": self.coverage_targets.copy(),
            "simulation_time": "1000ns"
        }
        
        # 根据设计特点选择测试模式
        strategy["test_modes"].append("functional")
        
        if has_reset:
            strategy["test_scenarios"].append("reset_test")
        
        if has_clock:
            strategy["test_scenarios"].append("clock_edge_test")
            strategy["stimulus_types"].append("sequential")
        else:
            strategy["stimulus_types"].append("combinational")
        
        # 添加通用测试场景
        strategy["test_scenarios"].extend([
            "basic_functionality",
            "boundary_conditions",
            "corner_cases"
        ])
        
        strategy["test_modes"].extend(["corner_case", "random"])
        
        self.logger.info(f"📋 测试策略设计完成: {len(strategy['test_scenarios'])} 个场景")
        return strategy
    
    async def _generate_testbench(self, dut_analysis: Dict[str, Any], 
                                test_strategy: Dict[str, Any]) -> str:
        """生成testbench代码"""
        if not self.llm_client:
            return self._generate_template_testbench(dut_analysis, test_strategy)
        
        testbench_prompt = f"""
基于以下DUT分析和测试策略生成完整的SystemVerilog testbench：

DUT信息:
{json.dumps(dut_analysis, indent=2, ensure_ascii=False)}

测试策略:
{json.dumps(test_strategy, indent=2, ensure_ascii=False)}

请生成包含以下特性的testbench：
1. 完整的module定义和信号声明
2. 时钟和复位生成逻辑
3. DUT实例化
4. 测试激励生成
5. 响应检查和断言
6. 测试场景覆盖
7. 适当的显示和监控语句

请只返回SystemVerilog代码，不要其他解释。
"""
        
        try:
            testbench_code = await self.llm_client.send_prompt(
                prompt=testbench_prompt,
                temperature=0.3,
                max_tokens=4000
            )
            
            self.logger.info(f"✅ Testbench生成完成 ({len(testbench_code)} 字符)")
            return testbench_code.strip()
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM testbench生成失败，使用模板: {str(e)}")
            return self._generate_template_testbench(dut_analysis, test_strategy)
    
    def _generate_template_testbench(self, dut_analysis: Dict[str, Any], 
                                   test_strategy: Dict[str, Any]) -> str:
        """基于模板生成testbench（备用方案）"""
        module_name = dut_analysis.get("module_name", "dut")
        has_clock = dut_analysis.get("has_clock", False)
        has_reset = dut_analysis.get("has_reset", False)
        
        # 基本testbench模板
        testbench = f"""
// Testbench for {module_name}
// Generated by VerilogTestAgent

`timescale 1ns/1ps

module tb_{module_name};

    // Parameters
    parameter CLK_PERIOD = 10; // 100MHz clock
    parameter SIM_TIME = 1000;
    
    // Signals
"""
        
        # 添加信号声明
        if has_clock:
            testbench += "    reg clk;\n"
        if has_reset:
            testbench += "    reg rst_n;\n"
        
        # 添加输入输出信号
        inputs = dut_analysis.get("inputs", [])
        outputs = dut_analysis.get("outputs", [])
        
        for inp in inputs:
            if inp not in ["clk", "rst_n"]:
                testbench += f"    reg {inp};\n"
        
        for out in outputs:
            testbench += f"    wire {out};\n"
        
        testbench += f"""
    // DUT instantiation
    {module_name} dut (
"""
        
        # 端口连接
        all_ports = inputs + outputs
        for i, port in enumerate(all_ports):
            comma = "," if i < len(all_ports) - 1 else ""
            testbench += f"        .{port}({port}){comma}\n"
        
        testbench += "    );\n\n"
        
        # 时钟生成
        if has_clock:
            testbench += """    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
"""
        
        # 测试序列
        testbench += """    // Test sequence
    initial begin
        $display("=== Test Start ===");
        
"""
        
        # 复位序列
        if has_reset:
            testbench += """        // Reset sequence
        rst_n = 0;
        #(CLK_PERIOD * 2);
        rst_n = 1;
        #(CLK_PERIOD);
        
"""
        
        # 基本测试
        testbench += """        // Basic functionality test
        $display("Starting basic functionality test...");
        
        // Add test vectors here
        
        // Wait and finish
        #SIM_TIME;
        $display("=== Test Complete ===");
        $finish;
    end
    
    // Monitor signals
    initial begin
        $monitor("Time=%0t: ", $time);
    end
    
endmodule
"""
        
        return testbench.strip()
    
    async def _generate_test_vectors(self, dut_analysis: Dict[str, Any], 
                                   test_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成测试向量"""
        test_vectors = []
        
        # 基本功能测试向量
        basic_vectors = {
            "name": "basic_functionality",
            "description": "基本功能测试",
            "vectors": [
                {"inputs": {"data_in": "8'h00"}, "expected": {"data_out": "8'h00"}},
                {"inputs": {"data_in": "8'hFF"}, "expected": {"data_out": "8'hFF"}},
                {"inputs": {"data_in": "8'h55"}, "expected": {"data_out": "8'h55"}},
                {"inputs": {"data_in": "8'hAA"}, "expected": {"data_out": "8'hAA"}}
            ]
        }
        test_vectors.append(basic_vectors)
        
        # 边界条件测试
        boundary_vectors = {
            "name": "boundary_conditions", 
            "description": "边界条件测试",
            "vectors": [
                {"inputs": {"data_in": "8'h00"}, "expected": {"data_out": "8'h00"}},
                {"inputs": {"data_in": "8'hFF"}, "expected": {"data_out": "8'hFF"}},
                {"inputs": {"data_in": "8'h7F"}, "expected": {"data_out": "8'h7F"}},
                {"inputs": {"data_in": "8'h80"}, "expected": {"data_out": "8'h80"}}
            ]
        }
        test_vectors.append(boundary_vectors)
        
        # 随机测试向量
        random_vectors = {
            "name": "random_test",
            "description": "随机测试",
            "vectors": []
        }
        
        # 生成随机测试向量
        import random
        for i in range(10):
            random_val = random.randint(0, 255)
            random_vectors["vectors"].append({
                "inputs": {"data_in": f"8'h{random_val:02X}"},
                "expected": {"data_out": f"8'h{random_val:02X}"}
            })
        
        test_vectors.append(random_vectors)
        
        self.logger.info(f"🎯 测试向量生成完成: {len(test_vectors)} 个测试集")
        return test_vectors
    
    async def _save_test_files(self, testbench_code: str, 
                             test_vectors: List[Dict[str, Any]],
                             dut_analysis: Dict[str, Any],
                             task_id: str) -> List[FileReference]:
        """保存测试文件"""
        output_files = []
        module_name = dut_analysis.get("module_name", "dut")
        
        try:
            # 1. 保存testbench文件
            tb_path = f"output/{task_id}/tb_{module_name}.sv"
            tb_ref = await self.save_result_to_file(
                content=testbench_code,
                file_path=tb_path,
                file_type="testbench"
            )
            output_files.append(tb_ref)
            
            # 2. 保存测试向量文件
            vectors_content = json.dumps(test_vectors, indent=2, ensure_ascii=False)
            vectors_path = f"output/{task_id}/test_vectors.json"
            vectors_ref = await self.save_result_to_file(
                content=vectors_content,
                file_path=vectors_path,
                file_type="test_data"
            )
            output_files.append(vectors_ref)
            
            # 3. 保存仿真脚本
            sim_script = self._generate_simulation_script(module_name, task_id)
            script_path = f"output/{task_id}/run_sim.sh"
            script_ref = await self.save_result_to_file(
                content=sim_script,
                file_path=script_path,
                file_type="script"
            )
            output_files.append(script_ref)
            
            # 4. 保存测试文档
            doc_content = f"""# {module_name.upper()} 测试文档

## 测试概要
本文档描述了{module_name}模块的测试策略和测试结果。

## 测试文件
- `tb_{module_name}.sv`: 主要testbench文件
- `test_vectors.json`: 测试向量数据
- `run_sim.sh`: 仿真运行脚本

## 测试场景
{chr(10).join(f"- {tv['name']}: {tv['description']}" for tv in test_vectors)}

## 运行方法
```bash
chmod +x run_sim.sh
./run_sim.sh
```

## 生成信息
- 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 生成智能体: {self.agent_id}
"""
            
            doc_path = f"output/{task_id}/TEST_README.md"
            doc_ref = await self.save_result_to_file(
                content=doc_content,
                file_path=doc_path,
                file_type="documentation"
            )
            output_files.append(doc_ref)
            
            self.logger.info(f"💾 测试文件保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 保存测试文件失败: {str(e)}")
            return output_files
    
    def _generate_simulation_script(self, module_name: str, task_id: str) -> str:
        """生成仿真脚本"""
        script = f"""#!/bin/bash
# Simulation script for {module_name}
# Generated by VerilogTestAgent

echo "Starting simulation for {module_name}..."

# Create work directory
if [ ! -d "work" ]; then
    mkdir work
fi

# Compile with ModelSim/QuestaSim
vlog -work work {module_name}.v
vlog -work work tb_{module_name}.sv

# Run simulation
vsim -work work -c -do "run -all; quit" tb_{module_name}

echo "Simulation completed!"
echo "Check modelsim.log for results"

# Alternative with Icarus Verilog
# iverilog -o tb_{module_name} {module_name}.v tb_{module_name}.sv
# vvp tb_{module_name}

# Alternative with Verilator
# verilator --cc --exe --build tb_{module_name}.sv {module_name}.v
# ./obj_dir/Vtb_{module_name}
"""
        return script.strip()
    
    def _generate_test_report(self, dut_analysis: Dict[str, Any],
                            test_strategy: Dict[str, Any],
                            output_files: List[FileReference]) -> str:
        """生成测试报告"""
        module_name = dut_analysis.get("module_name", "Unknown")
        
        report = f"""
🧪 VERILOG测试报告
==================

📋 测试概要:
- 被测模块: {module_name}
- 测试模式: {', '.join(test_strategy.get('test_modes', []))}
- 测试场景: {len(test_strategy.get('test_scenarios', []))} 个

🎯 测试策略:
- 功能覆盖率目标: {test_strategy.get('coverage_goals', {}).get('statement', 0.95)*100:.0f}%
- 分支覆盖率目标: {test_strategy.get('coverage_goals', {}).get('branch', 0.90)*100:.0f}%
- 仿真时间: {test_strategy.get('simulation_time', 'N/A')}

📁 生成文件: {len(output_files)} 个
{chr(10).join(f"- {ref.file_path} ({ref.file_type})" for ref in output_files)}

🔍 DUT分析结果:
- 输入端口: {len(dut_analysis.get('inputs', []))} 个
- 输出端口: {len(dut_analysis.get('outputs', []))} 个
- 时钟信号: {'✅' if dut_analysis.get('has_clock', False) else '❌'}
- 复位信号: {'✅' if dut_analysis.get('has_reset', False) else '❌'}

📋 测试场景:
{chr(10).join(f"- {scenario}" for scenario in test_strategy.get('test_scenarios', []))}
"""
        return report.strip()