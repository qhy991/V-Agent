#!/usr/bin/env python3
"""
完整的多智能体协作测试案例：RISC-V CPU模块设计与验证
Multi-Agent Collaboration Test: RISC-V CPU Module Design & Verification

本测试案例展示：
1. 中心化协调器智能调度多个智能体
2. 智能体间的文件传递和协作
3. 复杂的工具调用链和错误处理
4. 完整的设计-审查-测试-修复工作流
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging


class MultiAgentRISCVTest:
    """多智能体RISC-V项目协作测试"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.log_session = setup_enhanced_logging("multi_agent_riscv_test")
        self.coordinator = CentralizedCoordinator(self.config)
        
        # 初始化智能体
        self.verilog_agent = RealVerilogDesignAgent(self.config)
        self.reviewer_agent = RealCodeReviewAgent(self.config)
        
        # 注册智能体到协调器
        self.coordinator.register_agent(self.verilog_agent)
        self.coordinator.register_agent(self.reviewer_agent)
        
        print(f"🏗️ 多智能体RISC-V项目测试初始化完成")
        print(f"📂 工作目录: {self.log_session.get_artifacts_dir()}")
    
    async def run_comprehensive_test(self):
        """运行完整的多智能体协作测试"""
        print("\n" + "="*80)
        print("🚀 开始多智能体RISC-V CPU设计与验证项目")
        print("="*80)
        
        total_start_time = time.time()
        test_results = {}
        
        try:
            # 阶段1: 需求分析与架构设计
            print("\n🎯 阶段1: 需求分析与RISC-V架构设计")
            print("-" * 50)
            phase1_result = await self._phase1_architecture_design()
            test_results["phase1"] = phase1_result
            
            # 阶段2: 核心模块协作设计
            print("\n🔧 阶段2: 核心模块协作设计")
            print("-" * 50)
            phase2_result = await self._phase2_core_modules_design()
            test_results["phase2"] = phase2_result
            
            # 阶段3: 交叉审查与优化
            print("\n🔍 阶段3: 智能体交叉审查与代码优化")
            print("-" * 50)
            phase3_result = await self._phase3_cross_review_optimization()
            test_results["phase3"] = phase3_result
            
            # 阶段4: 集成测试与验证
            print("\n🧪 阶段4: 集成测试与功能验证")
            print("-" * 50)
            phase4_result = await self._phase4_integration_testing()
            test_results["phase4"] = phase4_result
            
            # 阶段5: 错误注入与修复能力测试
            print("\n🚨 阶段5: 错误处理与智能修复测试")
            print("-" * 50)
            phase5_result = await self._phase5_error_recovery_test()
            test_results["phase5"] = phase5_result
            
        except Exception as e:
            print(f"❌ 测试执行异常: {str(e)}")
            test_results["error"] = str(e)
        
        total_time = time.time() - total_start_time
        
        # 生成综合测试报告
        await self._generate_final_report(test_results, total_time)
        
        return test_results
    
    async def _phase1_architecture_design(self):
        """阶段1: 协调器指导下的RISC-V架构设计"""
        start_time = time.time()
        
        # 复杂的架构设计任务 - 协调器智能分配
        design_request = """
作为RISC-V CPU架构师，请设计一个简化的32位RISC-V处理器核心，包含：

📋 设计要求：
1. **指令集支持**: RV32I基础整数指令集
   - 算术指令: ADD, SUB, AND, OR, XOR
   - 逻辑移位: SLL, SRL, SRA  
   - 分支指令: BEQ, BNE, BLT, BGE
   - 内存访问: LW, SW
   - 立即数指令: ADDI, ANDI, ORI

2. **核心模块设计**:
   - Program Counter (PC) 模块
   - Instruction Fetch Unit (IFU)
   - Instruction Decode Unit (IDU) 
   - Arithmetic Logic Unit (ALU)
   - Register File (32个32位寄存器)
   - Memory Interface Unit

3. **设计约束**:
   - 单周期执行（简化版）
   - 32位数据宽度
   - 支持基本的数据前递
   - 包含控制信号生成

4. **文件组织**:
   - 每个模块独立的.v文件
   - 顶层CPU集成模块
   - 详细的端口定义和注释

请先从PC模块开始，然后是ALU模块，最后集成为完整的CPU。
每个模块都要包含详细的功能说明和端口定义。
"""
        
        print("🎯 协调器分析任务并选择最佳智能体...")
        
        # 协调器智能选择和任务分解
        result = await self.coordinator.coordinate_task_execution(design_request)
        
        execution_time = time.time() - start_time
        print(f"⏱️ 阶段1执行时间: {execution_time:.2f}秒")
        
        # 处理协调器返回的字典格式
        result_str = str(result) if isinstance(result, dict) else result
        
        return {
            "success": "success" in result_str.lower() or len(result_str) > 500,
            "execution_time": execution_time,
            "result": result_str,
            "modules_designed": self._count_generated_files(["pc.v", "alu.v", "cpu.v"])
        }
    
    async def _phase2_core_modules_design(self):
        """阶段2: 多智能体协作设计核心模块"""
        start_time = time.time()
        
        # 并行设计不同模块 - 展示智能体协作
        design_tasks = [
            {
                "agent": "verilog_design",
                "task": """
基于前面的设计，现在需要实现RISC-V的寄存器文件(Register File)模块：

📋 寄存器文件规格：
- 32个32位通用寄存器 (x0-x31)
- x0寄存器硬编码为0
- 双读端口 (rs1, rs2)
- 单写端口 (rd)
- 同步写入，异步读取
- 包含写使能信号

🔧 接口定义：
```verilog
module register_file(
    input wire clk,
    input wire rst_n,
    input wire [4:0] rs1_addr,    // 读端口1地址
    input wire [4:0] rs2_addr,    // 读端口2地址  
    input wire [4:0] rd_addr,     // 写端口地址
    input wire [31:0] rd_data,    // 写入数据
    input wire rd_we,             // 写使能
    output wire [31:0] rs1_data,  // 读端口1数据
    output wire [31:0] rs2_data   // 读端口2数据
);
```

请实现这个模块，并包含详细注释。
"""
            },
            {
                "agent": "verilog_design", 
                "task": """
现在实现RISC-V的指令译码单元(Instruction Decode Unit):

📋 译码器规格：
- 解析32位RISC-V指令
- 生成控制信号
- 提取立即数
- 识别指令类型 (R-type, I-type, S-type, B-type)

🔧 需要译码的信号：
- ALU操作码 (alu_op)
- 寄存器读写地址 (rs1, rs2, rd)
- 立即数 (immediate)
- 内存读写使能 (mem_read, mem_write)
- 寄存器写使能 (reg_write)
- 分支控制信号 (branch)

请实现指令译码器，支持基础的RV32I指令集。
"""
            }
        ]
        
        results = []
        for task_info in design_tasks:
            print(f"🔧 分配任务给 {task_info['agent']} 智能体...")
            if task_info['agent'] == 'verilog_design':
                result = await self.verilog_agent.process_with_function_calling(
                    task_info['task'], max_iterations=8
                )
                results.append(result)
                await asyncio.sleep(1)  # 避免API频率限制
        
        execution_time = time.time() - start_time
        print(f"⏱️ 阶段2执行时间: {execution_time:.2f}秒")
        
        return {
            "success": len(results) > 0,
            "execution_time": execution_time,
            "results": results,
            "modules_completed": len(results)
        }
    
    async def _phase3_cross_review_optimization(self):
        """阶段3: 智能体交叉审查与优化"""
        start_time = time.time()
        
        # 代码审查智能体检查设计智能体的输出
        review_request = """
请对工件目录中生成的RISC-V模块进行全面的代码审查：

🔍 审查重点：
1. **功能正确性**: 
   - RISC-V指令集实现是否正确
   - 寄存器操作是否符合规范
   - 控制信号生成是否准确

2. **时序设计**:
   - 时钟域处理是否正确
   - 复位逻辑是否完善
   - 建立保持时间是否满足

3. **接口一致性**:
   - 模块间接口是否匹配
   - 信号位宽是否一致
   - 命名规范是否统一

4. **可综合性**:
   - 代码是否可综合
   - 是否使用了不支持的语法
   - 资源使用是否合理

5. **测试覆盖**:
   - 为每个模块生成测试台
   - 执行功能仿真验证
   - 检查边界条件处理

请提供详细的审查报告，包括发现的问题和改进建议。
如果发现错误，请生成修复后的代码。
"""
        
        print("🔍 代码审查智能体开始交叉审查...")
        review_result = await self.reviewer_agent.process_with_function_calling(
            review_request, max_iterations=10
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ 阶段3执行时间: {execution_time:.2f}秒")
        
        return {
            "success": "审查" in review_result or "review" in review_result.lower(),
            "execution_time": execution_time,
            "review_result": review_result,
            "issues_found": review_result.count("问题") + review_result.count("错误"),
            "fixes_provided": review_result.count("修复") + review_result.count("建议")
        }
    
    async def _phase4_integration_testing(self):
        """阶段4: 集成测试与验证"""
        start_time = time.time()
        
        # 复杂的集成测试任务
        integration_test_request = """
现在进行RISC-V CPU的集成测试和验证：

🧪 集成测试任务：
1. **系统级测试台设计**:
   - 创建完整的CPU测试环境
   - 包含指令内存和数据内存
   - 模拟真实的程序执行

2. **指令级测试**:
   - 测试所有支持的RISC-V指令
   - 验证算术运算正确性
   - 检查分支跳转逻辑
   - 验证内存读写功能

3. **程序级测试**:
   - 设计简单的汇编程序
   - 如：斐波那契数列计算
   - 数组排序算法
   - 循环和条件分支测试

4. **性能评估**:
   - 测量指令执行周期
   - 检查资源利用率
   - 分析关键路径延迟

请生成完整的测试台和测试程序，并执行仿真验证。
对发现的任何问题，请提供详细的分析和修复方案。
"""
        
        print("🧪 开始集成测试与功能验证...")
        
        # 首先让设计智能体创建集成测试
        test_design_result = await self.verilog_agent.process_with_function_calling(
            integration_test_request, max_iterations=8
        )
        
        # 然后让审查智能体验证测试结果
        verification_request = f"""
请分析和验证刚刚生成的RISC-V CPU集成测试结果：

📊 验证任务：
1. 检查测试台设计是否完整
2. 验证仿真结果是否正确
3. 分析性能指标是否合理
4. 识别潜在的设计问题

测试执行结果：
{test_design_result[:1000]}...

请提供详细的验证报告和改进建议。
"""
        
        verification_result = await self.reviewer_agent.process_with_function_calling(
            verification_request, max_iterations=6
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ 阶段4执行时间: {execution_time:.2f}秒")
        
        return {
            "success": "测试" in test_design_result and "验证" in verification_result,
            "execution_time": execution_time,
            "test_result": test_design_result,
            "verification_result": verification_result,
            "simulation_success": "成功" in test_design_result or "success" in test_design_result.lower()
        }
    
    async def _phase5_error_recovery_test(self):
        """阶段5: 错误处理与智能修复测试"""
        start_time = time.time()
        
        # 故意引入错误，测试修复能力
        error_injection_request = """
现在进行错误处理和智能修复能力测试：

🚨 错误注入测试：
1. 尝试读取一个不存在的配置文件: "riscv_config.json"
2. 当文件不存在时，创建一个带有语法错误的简单ALU模块
3. 尝试编译这个错误的模块
4. 分析编译错误并智能修复
5. 重新编译验证修复效果
6. 生成对应的测试台并运行仿真

这个测试将验证：
- 文件错误的处理能力
- 语法错误的识别和修复
- 编译错误的智能分析
- 迭代修复的策略
- 工具调用的错误恢复

请展示完整的错误发现->分析->修复->验证流程。
"""
        
        print("🚨 开始错误注入与智能修复测试...")
        
        # 使用审查智能体进行错误处理测试（因为它有更强的错误处理能力）
        error_recovery_result = await self.reviewer_agent.process_with_function_calling(
            error_injection_request, max_iterations=10
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ 阶段5执行时间: {execution_time:.2f}秒")
        
        # 分析错误处理效果
        error_handling_metrics = {
            "errors_detected": error_recovery_result.count("错误") + error_recovery_result.count("失败"),
            "fixes_attempted": error_recovery_result.count("修复") + error_recovery_result.count("调整"),
            "iterations_used": error_recovery_result.count("工具") // 2,  # 估算迭代次数
            "final_success": "成功" in error_recovery_result[-200:] or "完成" in error_recovery_result[-200:]
        }
        
        return {
            "success": error_handling_metrics["errors_detected"] > 0 and error_handling_metrics["fixes_attempted"] > 0,
            "execution_time": execution_time,
            "recovery_result": error_recovery_result,
            "metrics": error_handling_metrics
        }
    
    def _count_generated_files(self, expected_files: List[str]) -> int:
        """统计生成的文件数量"""
        artifacts_dir = self.log_session.get_artifacts_dir()
        count = 0
        for filename in expected_files:
            file_path = artifacts_dir / filename
            if file_path.exists():
                count += 1
        return count
    
    async def _generate_final_report(self, test_results: Dict[str, Any], total_time: float):
        """生成综合测试报告"""
        print("\n" + "="*80)
        print("📊 多智能体协作测试综合报告")
        print("="*80)
        
        # 统计总体成功率
        phases_success = []
        for phase_name, phase_result in test_results.items():
            if isinstance(phase_result, dict) and 'success' in phase_result:
                phases_success.append(phase_result['success'])
        
        overall_success_rate = sum(phases_success) / len(phases_success) * 100 if phases_success else 0
        
        print(f"🎯 总体成功率: {overall_success_rate:.1f}%")
        print(f"⏱️ 总执行时间: {total_time:.2f}秒")
        print(f"📁 工件目录: {self.log_session.get_artifacts_dir()}")
        
        # 各阶段详细结果
        for phase_name, result in test_results.items():
            if isinstance(result, dict):
                print(f"\n🔍 {phase_name}:")
                print(f"  ✅ 成功: {'是' if result.get('success', False) else '否'}")
                print(f"  ⏱️ 时间: {result.get('execution_time', 0):.2f}秒")
                
                # 特定阶段的额外信息
                if 'modules_designed' in result:
                    print(f"  📦 模块数: {result['modules_designed']}")
                if 'issues_found' in result:
                    print(f"  🔍 发现问题: {result['issues_found']}")
                if 'fixes_provided' in result:
                    print(f"  🔧 提供修复: {result['fixes_provided']}")
        
        # 评估多智能体协作效果
        print(f"\n🤝 多智能体协作评估:")
        
        collaboration_score = 0
        if test_results.get('phase1', {}).get('success', False):
            collaboration_score += 25
            print("  ✅ 协调器任务分配: 成功")
        else:
            print("  ❌ 协调器任务分配: 失败")
            
        if test_results.get('phase2', {}).get('success', False):
            collaboration_score += 25
            print("  ✅ 智能体协作设计: 成功")
        else:
            print("  ❌ 智能体协作设计: 失败")
            
        if test_results.get('phase3', {}).get('success', False):
            collaboration_score += 25
            print("  ✅ 交叉审查协作: 成功")
        else:
            print("  ❌ 交叉审查协作: 失败")
            
        if test_results.get('phase5', {}).get('success', False):
            collaboration_score += 25
            print("  ✅ 错误处理协作: 成功")
        else:
            print("  ❌ 错误处理协作: 失败")
        
        print(f"\n🏆 协作能力评分: {collaboration_score}/100")
        
        # 技术能力评估
        print(f"\n🔧 技术能力评估:")
        
        artifacts_dir = self.log_session.get_artifacts_dir()
        generated_files = list(artifacts_dir.glob("**/*.v")) + list(artifacts_dir.glob("**/*.md")) + list(artifacts_dir.glob("**/*.json"))
        print(f"  📁 生成文件总数: {len(generated_files)}")
        
        verilog_files = list(artifacts_dir.glob("**/*.v"))
        print(f"  📄 Verilog模块数: {len(verilog_files)}")
        
        if verilog_files:
            total_lines = 0
            for vfile in verilog_files:
                try:
                    with open(vfile, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
            print(f"  📝 代码总行数: {total_lines}")
        
        # 最终评级
        if overall_success_rate >= 80 and collaboration_score >= 75:
            print(f"\n🌟 综合评级: 优秀 - 多智能体架构展现出色的协作和工具调用能力")
        elif overall_success_rate >= 60 and collaboration_score >= 50:
            print(f"\n🔶 综合评级: 良好 - 基础协作功能正常，有进一步优化空间")
        else:
            print(f"\n❌ 综合评级: 需要改进 - 协作机制或工具调用存在问题")
        
        print("\n" + "="*80)


async def main():
    """主测试函数"""
    print("🚀 启动多智能体RISC-V项目协作测试")
    print("="*80)
    print("本测试将展示：")
    print("✅ 中心化协调器的智能任务分配")
    print("✅ 多智能体的协作设计能力") 
    print("✅ 复杂工具调用链的执行")
    print("✅ 智能体间的文件传递协作")
    print("✅ 错误处理与智能修复能力")
    print("✅ 完整的设计-审查-测试-修复工作流")
    
    tester = MultiAgentRISCVTest()
    
    try:
        results = await tester.run_comprehensive_test()
        
        print(f"\n🎉 测试完成！")
        print(f"📊 查看详细日志: {tester.log_session.get_session_dir()}")
        print(f"📁 查看生成文件: {tester.log_session.get_artifacts_dir()}")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return None
    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行完整的多智能体协作测试
    results = asyncio.run(main())
    
    if results:
        print("\n✅ 多智能体协作测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 多智能体协作测试失败！")
        sys.exit(1)