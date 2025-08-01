#!/usr/bin/env python3
"""
超前进位加法器测试驱动开发实验

这个实验展示了智能体如何根据测试台反馈进行迭代改进：
1. 从简单的行波进位开始
2. 根据测试台要求改进为超前进位
3. 迭代优化直到通过所有测试
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from extensions import create_test_driven_coordinator, TestDrivenConfig


class CarryLookaheadTDDExperiment:
    """超前进位加法器测试驱动开发实验"""
    
    def __init__(self):
        self.experiment_id = f"cla_tdd_exp_{int(time.time())}"
        self.testbench_path = str(project_root / "test_cases" / "carry_lookahead_adder_tb.v")
        
    async def setup_framework(self):
        """设置测试驱动框架"""
        print("🏗️ 初始化测试驱动框架...")
        
        # 1. 创建标准组件
        config = FrameworkConfig.from_env()
        self.coordinator = CentralizedCoordinator(config)
        
        # 2. 注册智能体
        self.verilog_agent = RealVerilogDesignAgent(config)
        self.reviewer_agent = RealCodeReviewAgent(config)
        
        self.coordinator.register_agent(self.verilog_agent)
        self.coordinator.register_agent(self.reviewer_agent)
        
        print("   ✅ 标准协调器和智能体初始化完成")
        
        # 3. 创建测试驱动配置
        tdd_config = TestDrivenConfig(
            max_iterations=5,
            enable_deep_analysis=True,
            timeout_per_iteration=300,
            save_iteration_logs=True
        )
        
        # 4. 升级为测试驱动协调器
        self.tdd_coordinator = create_test_driven_coordinator(self.coordinator, tdd_config)
        
        print("   ✅ 测试驱动扩展启用成功")
        
        # 5. 验证测试台文件
        if not Path(self.testbench_path).exists():
            raise FileNotFoundError(f"测试台文件不存在: {self.testbench_path}")
        
        print(f"   ✅ 测试台文件验证通过: {Path(self.testbench_path).name}")
        
        return True
    
    def get_design_requirements(self) -> str:
        """构建设计需求"""
        return """
请设计一个16位超前进位加法器（Carry Lookahead Adder），实现高效的并行加法运算。

🔧 模块接口规格：
```verilog
module carry_lookahead_adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数  
    input         cin,      // 输入进位
    output [15:0] sum,      // 16位和
    output        cout      // 输出进位
);
```

🎯 功能要求：
1. 实现16位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 使用超前进位技术提高性能，而不是简单的行波进位
4. 支持所有可能的输入组合

📊 超前进位加法器设计要点：
1. **进位生成 (Generate)**: Gi = Ai & Bi
2. **进位传播 (Propagate)**: Pi = Ai ^ Bi
3. **超前进位计算**: 
   - C1 = G0 + P0×C0
   - C2 = G1 + P1×G0 + P1×P0×C0
   - C3 = G2 + P2×G1 + P2×P1×G0 + P2×P1×P0×C0
   - ...
4. **求和**: Si = Pi ^ Ci

⚡ 设计约束：
- 使用纯组合逻辑实现
- 优化关键路径延迟
- 确保所有路径都有明确的输出
- 代码必须可综合

🧪 测试要求：
- 测试台包含20个全面的测试用例
- 覆盖基本加法、进位传播、边界条件、随机测试
- 必须通过所有测试用例
- 测试台会验证功能正确性和进位逻辑

📈 成功标准：
测试台最终输出 "🎉 所有测试通过！超前进位加法器设计正确！"

⚠️ 重要提醒：
- 不要使用简单的行波进位（ripple carry）
- 必须实现真正的超前进位逻辑
- 确保模块名为 carry_lookahead_adder_16bit
- 如果测试失败，请分析错误原因并改进设计
"""
    
    async def run_experiment(self):
        """运行完整的实验"""
        experiment_start_time = time.time()
        
        print(f"🚀 开始超前进位加法器测试驱动开发实验")
        print("=" * 80)
        
        try:
            # 1. 设置框架
            await self.setup_framework()
            
            # 2. 获取设计需求
            design_requirements = self.get_design_requirements()
            
            print(f"📋 设计需求已生成")
            print(f"🎯 目标: 16位超前进位加法器 + 通过 {Path(self.testbench_path).name} 测试")
            
            # 3. 执行测试驱动任务
            print(f"🔄 启动测试驱动开发循环...")
            
            result = await self.tdd_coordinator.execute_test_driven_task(
                task_description=design_requirements,
                testbench_path=self.testbench_path
            )
            
            # 4. 分析结果
            experiment_duration = time.time() - experiment_start_time
            analysis = await self._analyze_experiment_result(result, experiment_duration)
            
            return analysis
            
        except Exception as e:
            print(f"❌ 实验执行异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "experiment_id": self.experiment_id,
                "duration": time.time() - experiment_start_time
            }
    
    async def _analyze_experiment_result(self, result, duration):
        """分析实验结果"""
        print(f"📊 实验结果分析")
        print("=" * 80)
        
        analysis = {
            "experiment_id": self.experiment_id,
            "success": result.get("success", False),
            "total_duration": duration,
            "result_summary": {}
        }
        
        if result.get("success"):
            print("🎉 实验成功完成！")
            
            iterations = result.get("total_iterations", 0)
            final_design = result.get("final_design", [])
            
            print(f"   📈 总迭代次数: {iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   📁 最终设计文件: {len(final_design)} 个")
            
            analysis["result_summary"] = {
                "iterations_used": iterations,
                "efficiency": f"成功率: 100%",
                "files_generated": len(final_design),
                "completion_reason": result.get("completion_reason", "tests_passed")
            }
            
            # 显示设计文件信息
            if final_design:
                print(f"📄 生成的设计文件:")
                for i, file_info in enumerate(final_design, 1):
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path', str(file_info))
                    else:
                        file_path = str(file_info)
                    print(f"   {i}. {Path(file_path).name}")
            
        else:
            print("❌ 实验未能完成")
            
            iterations = result.get("total_iterations", 0)
            error = result.get("error", "未知错误")
            
            print(f"   📈 已用迭代次数: {iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   ❌ 失败原因: {error}")
            
            analysis["result_summary"] = {
                "iterations_used": iterations,
                "completion_reason": result.get("completion_reason", "failed"),
                "error": error
            }
            
            # 分析部分结果
            partial_results = result.get("partial_results", [])
            if partial_results:
                print(f"🔍 迭代历史分析:")
                for i, iteration in enumerate(partial_results, 1):
                    iter_result = iteration.get("result", {})
                    success = iter_result.get("all_tests_passed", False)
                    print(f"   第{i}次迭代: {'✅ 通过' if success else '❌ 失败'}")
        
        # 显示会话信息
        session_id = result.get("session_id")
        if session_id:
            session_info = self.tdd_coordinator.get_session_info(session_id)
            if session_info:
                print(f"📋 会话详情:")
                print(f"   会话ID: {session_id}")
                print(f"   状态: {session_info.get('status', 'unknown')}")
        
        print("=" * 80)
        return analysis


async def main():
    """主实验入口"""
    print("🧪 超前进位加法器测试驱动开发实验")
    print("=" * 70)
    print("🎯 实验目标: 验证智能体能否根据测试台反馈迭代改进设计")
    print("📝 测试重点: 从简单加法器逐步改进为超前进位加法器")
    print("=" * 70)
    
    # 创建并运行实验
    experiment = CarryLookaheadTDDExperiment()
    
    try:
        result = await experiment.run_experiment()
        
        # 显示最终结果
        print(f"🏁 实验完成")
        if result["success"]:
            print("✅ 超前进位加法器设计成功完成并通过所有测试！")
            print("🎯 测试驱动开发功能验证成功")
        else:
            print("❌ 超前进位加法器设计未能通过所有测试")
            print("🔍 可以查看日志分析迭代改进过程")
        
        return result["success"]
        
    except Exception as e:
        print(f"💥 实验执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)