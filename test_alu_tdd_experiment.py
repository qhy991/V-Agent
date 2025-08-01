#!/usr/bin/env python3
"""
ALU测试驱动开发实验 - 可配置的实验入口

这个脚本展示完整的测试驱动开发流程：
1. 用户提供设计需求和测试台路径
2. 系统自动迭代优化设计直到通过测试
3. 提供详细的实验配置和结果分析
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入测试驱动扩展
from extensions import create_test_driven_coordinator, TestDrivenConfig


class ALUTestDrivenExperiment:
    """ALU测试驱动开发实验类"""
    
    def __init__(self, experiment_config: Dict[str, Any] = None):
        """
        初始化实验
        
        Args:
            experiment_config: 实验配置，包含以下可选参数：
                - max_iterations: 最大迭代次数 (默认: 5)
                - timeout_per_iteration: 每次迭代超时秒数 (默认: 300)
                - enable_deep_analysis: 启用深度分析 (默认: True)
                - save_detailed_logs: 保存详细日志 (默认: True)
                - testbench_path: 测试台路径 (默认: 使用内置测试台)
                - design_complexity: 设计复杂度 (simple/standard/advanced)
        """
        self.config = experiment_config or {}
        self.experiment_id = f"alu_tdd_exp_{int(time.time())}"
        
        # 实验配置
        self.max_iterations = self.config.get('max_iterations', 5)
        self.timeout_per_iteration = self.config.get('timeout_per_iteration', 300)
        self.enable_deep_analysis = self.config.get('enable_deep_analysis', True)
        self.save_detailed_logs = self.config.get('save_detailed_logs', True)
        
        # 测试台配置
        self.testbench_path = self.config.get('testbench_path', 
            str(project_root / "test_cases" / "alu_testbench.v"))
        
        # 设计复杂度配置
        self.design_complexity = self.config.get('design_complexity', 'standard')
        
        print(f"🧪 初始化ALU测试驱动实验: {self.experiment_id}")
        print(f"📋 实验配置:")
        print(f"   最大迭代次数: {self.max_iterations}")
        print(f"   每次迭代超时: {self.timeout_per_iteration}秒")
        print(f"   深度分析: {self.enable_deep_analysis}")
        print(f"   设计复杂度: {self.design_complexity}")
        print(f"   测试台路径: {self.testbench_path}")
    
    def get_design_requirements(self) -> str:
        """根据复杂度配置生成设计需求"""
        
        base_requirements = """
请设计一个32位ALU（算术逻辑单元）模块，必须严格按照以下规格实现：

🔧 模块接口规格：
```verilog
module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数  
    input  [3:0]  op,      // 4位操作码
    output [31:0] result,  // 32位运算结果
    output        zero     // 零标志位（结果为0时为1）
);
```

📋 操作码定义（必须严格遵守）：
- 4'b0000 (OP_ADD): 加法运算 (result = a + b)
- 4'b0001 (OP_SUB): 减法运算 (result = a - b)
- 4'b0010 (OP_AND): 逻辑与 (result = a & b)
- 4'b0011 (OP_OR):  逻辑或 (result = a | b)
- 4'b0100 (OP_XOR): 异或 (result = a ^ b)
- 4'b0101 (OP_SLL): 左移 (result = a << b[4:0])
- 4'b0110 (OP_SRL): 右移 (result = a >> b[4:0])
- 其他操作码: 输出0

🎯 功能要求：
1. 支持32位算术运算（加法、减法）
2. 支持32位逻辑运算（与、或、异或）
3. 支持移位运算（左移、右移，使用b的低5位作为移位位数）
4. zero标志位：当result为32'h00000000时，zero=1；否则zero=0
5. 对于无效操作码，输出result=32'h00000000, zero=1

⚡ 设计约束：
- 使用纯组合逻辑实现（不需要时钟）
- 确保所有路径都有明确的输出
- 代码必须可综合
- 遵循良好的Verilog编码规范
"""
        
        complexity_additions = {
            'simple': """
🔰 简化要求：
- 实现基本的加法、减法和逻辑运算即可
- 移位运算可以简化实现
            """,
            
            'standard': """
🎯 标准要求：
- 完整实现所有指定操作
- 正确处理边界条件和溢出
- 确保移位运算的正确性
            """,
            
            'advanced': """
🚀 高级要求：
- 完整实现所有指定操作
- 优化关键路径延迟
- 添加详细的内部注释
- 考虑面积和功耗优化
- 添加assertion检查（可选）
            """
        }
        
        test_requirements = f"""

🧪 测试要求：
- 测试台路径: {self.testbench_path}
- 必须通过所有16个测试用例
- 测试台包含详细的分组测试：
  * 加法运算测试（3个用例）
  * 减法运算测试（3个用例）
  * 逻辑运算测试（5个用例）
  * 移位运算测试（4个用例）
  * 边界条件测试（2个用例）

⚠️ 关键要求：
- 如果测试失败，请仔细分析失败原因
- 根据测试台的具体错误信息调整设计
- 确保操作码定义与测试台完全一致
- 确保zero标志位逻辑正确
- 继续迭代直到所有测试通过

📊 成功标准：
测试台最终输出 "🎉 所有测试通过！ALU设计正确！"
"""
        
        return (base_requirements + 
                complexity_additions.get(self.design_complexity, complexity_additions['standard']) +
                test_requirements)
    
    async def setup_framework(self):
        """设置框架组件"""
        print("\n🏗️ 初始化测试驱动框架...")
        
        # 1. 创建标准组件
        framework_config = FrameworkConfig.from_env()
        self.coordinator = CentralizedCoordinator(framework_config)
        
        # 2. 注册智能体
        self.verilog_agent = RealVerilogDesignAgent(framework_config)
        self.reviewer_agent = RealCodeReviewAgent(framework_config)
        
        self.coordinator.register_agent(self.verilog_agent)
        self.coordinator.register_agent(self.reviewer_agent)
        
        print("   ✅ 标准协调器和智能体初始化完成")
        
        # 3. 创建测试驱动配置
        tdd_config = TestDrivenConfig(
            max_iterations=self.max_iterations,
            enable_deep_analysis=self.enable_deep_analysis,
            timeout_per_iteration=self.timeout_per_iteration,
            save_iteration_logs=self.save_detailed_logs
        )
        
        # 4. 升级为测试驱动协调器
        self.tdd_coordinator = create_test_driven_coordinator(self.coordinator, tdd_config)
        
        print("   ✅ 测试驱动扩展启用成功")
        
        # 5. 验证测试台文件
        testbench_path = Path(self.testbench_path)
        if not testbench_path.exists():
            raise FileNotFoundError(f"测试台文件不存在: {self.testbench_path}")
        
        print(f"   ✅ 测试台文件验证通过: {testbench_path.name}")
        
        return True
    
    async def run_experiment(self) -> Dict[str, Any]:
        """运行完整的ALU测试驱动实验"""
        experiment_start_time = time.time()
        
        print(f"\n🚀 开始ALU测试驱动开发实验")
        print("=" * 80)
        
        try:
            # 1. 设置框架
            await self.setup_framework()
            
            # 2. 构建设计任务
            design_requirements = self.get_design_requirements()
            
            print(f"\n📋 设计需求已生成 (长度: {len(design_requirements)} 字符)")
            print(f"🎯 目标: 设计32位ALU并通过 {Path(self.testbench_path).name} 的所有测试")
            
            # 3. 执行测试驱动任务
            print(f"\n🔄 启动测试驱动开发循环...")
            print(f"   最大迭代次数: {self.max_iterations}")
            print(f"   每次迭代超时: {self.timeout_per_iteration}秒")
            
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
    
    async def _analyze_experiment_result(self, result: Dict[str, Any], 
                                       duration: float) -> Dict[str, Any]:
        """分析实验结果"""
        print(f"\n📊 实验结果分析")
        print("=" * 80)
        
        analysis = {
            "experiment_id": self.experiment_id,
            "success": result.get("success", False),
            "total_duration": duration,
            "configuration": self.config,
            "result_summary": {}
        }
        
        if result.get("success"):
            print("🎉 实验成功完成！")
            
            iterations = result.get("total_iterations", 0)
            final_design = result.get("final_design", [])
            
            print(f"   📈 总迭代次数: {iterations}/{self.max_iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   📁 最终设计文件: {len(final_design)} 个")
            
            analysis["result_summary"] = {
                "iterations_used": iterations,
                "iterations_available": self.max_iterations,
                "efficiency": f"{(1 - iterations/self.max_iterations)*100:.1f}%",
                "files_generated": len(final_design),
                "completion_reason": result.get("completion_reason", "unknown")
            }
            
            # 显示设计文件信息
            if final_design:
                print(f"\n📄 生成的设计文件:")
                for i, file_info in enumerate(final_design, 1):
                    if isinstance(file_info, dict):
                        file_path = file_info.get('file_path', str(file_info))
                        print(f"   {i}. {Path(file_path).name}")
            
        else:
            print("❌ 实验未能完成")
            
            iterations = result.get("total_iterations", 0)
            error = result.get("error", "未知错误")
            
            print(f"   📈 已用迭代次数: {iterations}/{self.max_iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   ❌ 失败原因: {error}")
            
            analysis["result_summary"] = {
                "iterations_used": iterations,
                "iterations_available": self.max_iterations,
                "completion_reason": result.get("completion_reason", "failed"),
                "error": error
            }
            
            # 分析部分结果
            partial_results = result.get("partial_results", [])
            if partial_results:
                print(f"\n🔍 迭代历史分析:")
                for i, iteration in enumerate(partial_results, 1):
                    iter_result = iteration.get("result", {})
                    success = iter_result.get("all_tests_passed", False)
                    print(f"   第{i}次迭代: {'✅ 通过' if success else '❌ 失败'}")
        
        # 显示会话信息
        session_id = result.get("session_id")
        if session_id:
            session_info = self.tdd_coordinator.get_session_info(session_id)
            if session_info:
                print(f"\n📋 会话详情:")
                print(f"   会话ID: {session_id}")
                print(f"   状态: {session_info.get('status', 'unknown')}")
                
                iterations_detail = session_info.get('iterations', [])
                if iterations_detail:
                    print(f"   详细迭代: {len(iterations_detail)} 次")
        
        print("=" * 80)
        return analysis
    
    def save_experiment_report(self, analysis: Dict[str, Any], 
                             output_path: Optional[str] = None):
        """保存实验报告"""
        if output_path is None:
            output_path = f"alu_tdd_experiment_report_{self.experiment_id}.json"
        
        report = {
            "experiment_metadata": {
                "experiment_id": self.experiment_id,
                "timestamp": time.time(),
                "framework_version": "1.0.0",
                "experiment_type": "alu_test_driven_development"
            },
            "configuration": self.config,
            "results": analysis,
            "testbench_info": {
                "path": self.testbench_path,
                "exists": Path(self.testbench_path).exists(),
                "size": Path(self.testbench_path).stat().st_size if Path(self.testbench_path).exists() else 0
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 实验报告已保存: {output_path}")


# 预定义实验配置
EXPERIMENT_CONFIGS = {
    "quick_test": {
        "max_iterations": 3,
        "timeout_per_iteration": 120,
        "design_complexity": "simple",
        "enable_deep_analysis": True,
        "save_detailed_logs": True
    },
    
    "standard_test": {
        "max_iterations": 5,
        "timeout_per_iteration": 300,
        "design_complexity": "standard", 
        "enable_deep_analysis": True,
        "save_detailed_logs": True
    },
    
    "thorough_test": {
        "max_iterations": 8,
        "timeout_per_iteration": 600,
        "design_complexity": "advanced",
        "enable_deep_analysis": True,
        "save_detailed_logs": True
    },
    
    "minimal_test": {
        "max_iterations": 2,
        "timeout_per_iteration": 60,
        "design_complexity": "simple",
        "enable_deep_analysis": False,
        "save_detailed_logs": False
    }
}


async def main():
    """主实验入口"""
    print("🧪 ALU测试驱动开发实验平台")
    print("=" * 60)
    
    # 显示可用配置
    print("📋 可用实验配置:")
    for name, config in EXPERIMENT_CONFIGS.items():
        print(f"   {name}: {config['design_complexity']}复杂度, "
              f"{config['max_iterations']}次迭代, "
              f"{config['timeout_per_iteration']}秒超时")
    
    # 选择实验配置
    print(f"\n🎯 使用默认配置: standard_test")
    experiment_config = EXPERIMENT_CONFIGS["standard_test"]
    
    # 创建并运行实验
    experiment = ALUTestDrivenExperiment(experiment_config)
    
    try:
        result = await experiment.run_experiment()
        
        # 保存实验报告
        experiment.save_experiment_report(result)
        
        # 显示最终结果
        print(f"\n🏁 实验完成")
        if result["success"]:
            print("✅ ALU设计成功完成并通过所有测试！")
        else:
            print("❌ ALU设计未能通过所有测试，请检查日志分析原因")
        
        return result["success"]
        
    except Exception as e:
        print(f"💥 实验执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)