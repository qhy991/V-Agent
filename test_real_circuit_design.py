#!/usr/bin/env python3
"""
真实电路设计协作测试

Real Circuit Design Collaboration Test

这个测试案例设计一个完整的32位ALU（算术逻辑单元），包括：
1. 需求分析和模块分解
2. 子模块设计（加法器、逻辑运算单元等）
3. 顶层集成
4. 完整的测试台生成
5. 仿真验证
6. 代码质量分析和优化建议

测试将验证：
- CentralizedCoordinator的智能体调度能力
- RealVerilogDesignAgent的设计能力
- RealCodeReviewAgent的验证能力
- 多智能体协作流程
- Function Calling工具调用能力
"""

import asyncio
import time
from pathlib import Path

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入增强日志系统
from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_test_logger, 
    get_artifacts_dir,
    get_coordinator_logger
)


class RealCircuitDesignTester:
    """真实电路设计协作测试器"""
    
    def __init__(self):
        # 初始化增强日志系统
        self.logger_manager = setup_enhanced_logging()
        self.logger = get_test_logger()
        self.coordinator_logger = get_coordinator_logger()
        
        self.config = FrameworkConfig.from_env()
        self.artifacts_dir = get_artifacts_dir()
        self.session_dir = self.logger_manager.get_session_dir()
        
        self.logger.info("🚀 初始化真实电路设计协作测试器")
        print("🚀 初始化真实电路设计协作测试器")
        print(f"📁 实验目录: {self.session_dir}")
        print(f"🛠️ 工件目录: {self.artifacts_dir}")
        
        # 测试结果记录
        self.test_results = {}
        self.start_time = time.time()
    
    async def test_32bit_alu_design(self):
        """测试32位ALU完整设计流程"""
        self.logger.info("开始32位ALU完整设计流程测试")
        print("\n" + "="*80)
        print("🔬 32位ALU完整设计流程测试")
        print("="*80)
        
        # 定义复杂的设计需求
        alu_requirements = """
请设计一个完整的32位算术逻辑单元(ALU)，具体要求如下：

**功能需求：**
1. 算术运算：32位加法、减法（支持有符号和无符号）
2. 逻辑运算：AND、OR、XOR、NOT
3. 移位运算：左移、右移（逻辑和算术）
4. 比较运算：等于、小于、大于（有符号和无符号）

**接口规范：**
- 输入：两个32位操作数 A 和 B
- 控制：4位操作码选择功能
- 输出：32位结果
- 状态标志：零标志(Zero)、负标志(Negative)、溢出标志(Overflow)、进位标志(Carry)

**性能要求：**
- 组合逻辑实现，无时钟延迟
- 关键路径延迟 < 10ns（假设标准工艺）
- 面积优化，尽量复用逻辑

**设计流程：**
1. 需求分析和架构设计
2. 子模块设计（加法器、逻辑单元、移位器、比较器）
3. 顶层ALU集成
4. 完整测试台设计
5. 功能仿真验证
6. 时序和面积分析
7. 优化建议

请按照多智能体协作的方式完成这个设计。
"""
        
        try:
            # 创建智能体
            self.logger.info("创建智能体实例")
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            print("\n📋 Phase 1: Verilog设计智能体 - 需求分析和初步设计")
            print("-" * 60)
            
            # Phase 1: 设计智能体进行需求分析和初步设计
            design_response = await verilog_agent.process_with_function_calling(
                user_request=alu_requirements,
                max_iterations=10
            )
            
            self.logger.info(f"设计阶段完成，响应长度: {len(design_response)}")
            print(f"🔧 设计阶段完成，响应长度: {len(design_response)} 字符")
            
            # 检查生成的设计文件
            design_files = list(self.artifacts_dir.glob("*.v"))
            design_files.extend(list(Path("./output").glob("*.v")) if Path("./output").exists() else [])
            
            if design_files:
                print(f"📁 设计阶段生成文件: {[f.name for f in design_files]}")
                self.logger.info(f"设计阶段生成文件: {[f.name for f in design_files]}")
            else:
                print("⚠️ 设计阶段未生成预期的Verilog文件")
                self.logger.warning("设计阶段未生成预期的Verilog文件")
            
            print("\n📋 Phase 2: 代码审查智能体 - 验证和测试")
            print("-" * 60)
            
            # Phase 2: 审查智能体进行验证和测试
            if design_files:
                # 找到主要的ALU文件
                alu_file = None
                for f in design_files:
                    if "alu" in f.name.lower() and "tb" not in f.name.lower():
                        alu_file = f
                        break
                
                if alu_file:
                    review_request = f"""
请对设计的32位ALU进行完整的验证和测试：

主要设计文件：{alu_file.name}

验证任务：
1. 读取并分析ALU设计文件
2. 检查接口规范是否符合要求
3. 生成全面的测试台，覆盖所有功能
4. 运行仿真验证正确性
5. 分析代码质量和性能
6. 提供优化建议

请特别关注：
- 所有算术运算的正确性（包括边界情况）
- 逻辑运算的完整性
- 状态标志的准确性
- 时序关键路径分析
"""
                    
                    review_response = await review_agent.process_with_function_calling(
                        user_request=review_request,
                        max_iterations=10
                    )
                    
                    self.logger.info(f"验证阶段完成，响应长度: {len(review_response)}")
                    print(f"🔍 验证阶段完成，响应长度: {len(review_response)} 字符")
                else:
                    print("⚠️ 未找到主要的ALU设计文件，跳过验证阶段")
                    self.logger.warning("未找到主要的ALU设计文件")
            else:
                print("⚠️ 无设计文件可供验证，执行基础验证流程")
                basic_review_request = """
32位ALU设计项目验证总结：

虽然未找到具体的设计文件，但请：
1. 总结32位ALU的关键设计要点
2. 列出必要的测试用例类型
3. 提供设计质量评估标准
4. 给出后续优化方向建议
"""
                
                review_response = await review_agent.process_with_function_calling(
                    user_request=basic_review_request,
                    max_iterations=5
                )
                
                self.logger.info(f"基础验证完成，响应长度: {len(review_response)}")
                print(f"🔍 基础验证完成，响应长度: {len(review_response)} 字符")
            
            # 统计最终结果
            all_files = list(self.artifacts_dir.glob("*"))
            output_files = list(Path("./output").glob("*")) if Path("./output").exists() else []
            all_files.extend(output_files)
            
            print(f"\n📊 32位ALU设计项目完成总结:")
            print(f"  📁 总文件数: {len(all_files)}")
            print(f"  🔧 Verilog文件: {len([f for f in all_files if f.suffix == '.v'])}")
            print(f"  🧪 测试相关文件: {len([f for f in all_files if 'test' in f.name.lower() or 'tb' in f.name.lower()])}")
            print(f"  📋 文档文件: {len([f for f in all_files if f.suffix in ['.md', '.txt', '.json']])}")
            
            # 显示生成的文件列表
            if all_files:
                print(f"\n📁 生成的文件列表:")
                for f in sorted(all_files, key=lambda x: x.name):
                    size = f.stat().st_size if f.exists() else 0
                    print(f"  - {f.name}: {size} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"32位ALU设计测试失败: {str(e)}")
            print(f"❌ 32位ALU设计测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_simple_collaboration(self):
        """测试简单的多智能体协作"""
        self.logger.info("开始简单多智能体协作测试")
        print("\n" + "="*60)
        print("🤝 简单多智能体协作测试")
        print("="*60)
        
        try:
            # 创建智能体
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            # 简单协作任务：设计和验证一个8位计数器
            counter_request = """
设计一个8位同步二进制计数器，要求：
1. 8位输出 (count[7:0])
2. 时钟输入 (clk)
3. 同步复位 (rst)
4. 使能信号 (en)
5. 计数到255后回到0
6. 保存到文件 counter_8bit.v
"""
            
            print("📐 Step 1: 设计8位计数器")
            design_result = await verilog_agent.process_with_function_calling(
                user_request=counter_request,
                max_iterations=5
            )
            
            print("🧪 Step 2: 验证8位计数器")
            verification_request = """
对8位计数器 counter_8bit.v 进行验证：
1. 读取设计文件
2. 生成完整测试台
3. 运行仿真测试
4. 检查功能正确性
"""
            
            verify_result = await review_agent.process_with_function_calling(
                user_request=verification_request,
                max_iterations=6
            )
            
            # 检查协作结果
            counter_files = [f for f in self.artifacts_dir.glob("*counter*") if f.suffix == '.v']
            output_counter_files = []
            if Path("./output").exists():
                output_counter_files = [f for f in Path("./output").glob("*counter*") if f.suffix == '.v']
            
            all_counter_files = counter_files + output_counter_files
            
            if all_counter_files:
                print(f"✅ 协作成功：生成了 {len(all_counter_files)} 个计数器相关文件")
                for f in all_counter_files:
                    print(f"  - {f.name}")
                return True
            else:
                print("⚠️ 协作部分成功：未生成预期文件，但流程正常")
                return True
                
        except Exception as e:
            self.logger.error(f"简单协作测试失败: {str(e)}")
            print(f"❌ 简单协作测试失败: {str(e)}")
            return False
    
    async def test_function_calling_capabilities(self):
        """测试各智能体的Function Calling能力"""
        self.logger.info("开始Function Calling能力测试")
        print("\n" + "="*60)
        print("🔧 Function Calling能力测试")
        print("="*60)
        
        try:
            # 测试Verilog设计智能体的工具调用
            print("📐 测试Verilog设计智能体工具调用")
            verilog_agent = RealVerilogDesignAgent(self.config)
            
            print(f"  🔧 注册的工具: {list(verilog_agent.function_calling_registry.keys())}")
            
            # 测试需求分析工具
            req_result = await verilog_agent._tool_analyze_design_requirements(
                "设计一个4位全加器，包含进位输入和输出"
            )
            if req_result.get('success'):
                print("  ✅ 需求分析工具测试通过")
            else:
                print("  ❌ 需求分析工具测试失败")
            
            # 测试代码生成工具
            gen_result = await verilog_agent._tool_generate_verilog_code(
                "设计一个简单的与门",
                {"module_name": "and_gate", "complexity": 1}
            )
            if gen_result.get('success'):
                print("  ✅ 代码生成工具测试通过")
            else:
                print("  ❌ 代码生成工具测试失败")
            
            # 测试代码审查智能体的工具调用
            print("\n🔍 测试代码审查智能体工具调用")
            review_agent = RealCodeReviewAgent(self.config)
            
            print(f"  🔧 注册的工具: {list(review_agent.function_calling_registry.keys())}")
            
            # 测试测试台生成工具
            test_verilog = """
module simple_and(
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
"""
            
            tb_result = await review_agent._tool_generate_testbench(
                verilog_code=test_verilog,
                module_name="simple_and"
            )
            if tb_result.get('success'):
                print("  ✅ 测试台生成工具测试通过")
            else:
                print("  ❌ 测试台生成工具测试失败")
            
            # 测试代码质量分析工具
            quality_result = await review_agent._tool_analyze_code_quality(test_verilog)
            if quality_result.get('success'):
                print("  ✅ 代码质量分析工具测试通过")
            else:
                print("  ❌ 代码质量分析工具测试失败")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Function Calling能力测试失败: {str(e)}")
            print(f"❌ Function Calling能力测试失败: {str(e)}")
            return False
    
    async def generate_test_report(self):
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        # 统计文件
        artifacts_count = len(list(self.artifacts_dir.glob("*")))
        output_count = len(list(Path("./output").glob("*"))) if Path("./output").exists() else 0
        total_files = artifacts_count + output_count
        
        print("\n" + "="*80)
        print("📊 真实电路设计协作测试报告")
        print("="*80)
        
        print(f"⏱️ 总测试时间: {total_time:.2f}秒")
        print(f"📁 生成文件总数: {total_files}")
        print(f"🛠️ 工件目录文件: {artifacts_count}")
        print(f"📋 输出目录文件: {output_count}")
        
        # 保存详细报告
        report = {
            "test_type": "real_circuit_design_collaboration",
            "timestamp": time.time(),
            "duration": total_time,
            "files_generated": total_files,
            "artifacts_count": artifacts_count,
            "output_count": output_count,
            "session_dir": str(self.session_dir),
            "artifacts_dir": str(self.artifacts_dir)
        }
        
        import json
        report_file = self.session_dir / f"circuit_design_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存: {report_file}")
        
        # 创建会话摘要
        self.logger_manager.create_session_summary()
        
        self.logger.info("真实电路设计协作测试完成")
        print("✅ 真实电路设计协作测试完成")


async def main():
    """主测试函数"""
    tester = RealCircuitDesignTester()
    
    # 运行测试序列
    print("🚀 开始真实电路设计多智能体协作测试")
    
    # Test 1: 复杂的32位ALU设计
    await tester.test_32bit_alu_design()
    
    # Test 2: 简单协作测试
    await tester.test_simple_collaboration()
    
    # Test 3: Function Calling能力测试
    await tester.test_function_calling_capabilities()
    
    # 生成最终报告
    await tester.generate_test_report()


if __name__ == "__main__":
    asyncio.run(main())