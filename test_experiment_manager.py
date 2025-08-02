#!/usr/bin/env python3
"""
测试实验管理器功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_experiment_manager():
    """测试实验管理器基本功能"""
    print("🧪 测试实验管理器功能")
    
    from core.experiment_manager import ExperimentManager, create_experiment, save_experiment_file
    
    # 创建实验管理器
    exp_manager = ExperimentManager()
    
    # 测试1: 创建新实验
    print("\n📋 测试1: 创建新实验")
    exp_path = exp_manager.create_new_experiment(
        experiment_name="test_adder_experiment",
        description="测试8位加法器的TDD实验"
    )
    print(f"实验路径: {exp_path}")
    print(f"实验文件夹存在: {exp_path.exists()}")
    
    # 检查子文件夹
    subdirs = ["designs", "testbenches", "outputs", "logs", "artifacts", "dependencies"]
    for subdir in subdirs:
        subdir_path = exp_path / subdir
        print(f"  {subdir}: {subdir_path.exists()}")
    
    # 测试2: 保存文件到实验文件夹
    print("\n📋 测试2: 保存文件到实验文件夹")
    
    # 保存设计文件
    design_code = """
module simple_adder (
    input [7:0] a,
    input [7:0] b,
    output [8:0] sum
);
    assign sum = a + b;
endmodule
"""
    
    design_path = exp_manager.save_file(
        content=design_code,
        filename="simple_adder.v",
        subdir="designs",
        description="简单的8位加法器设计"
    )
    print(f"设计文件保存至: {design_path}")
    
    # 保存测试台文件
    testbench_code = """
module simple_adder_tb;
    reg [7:0] a, b;
    wire [8:0] sum;
    
    simple_adder uut (.a(a), .b(b), .sum(sum));
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        a = 8'd10; b = 8'd20; #10;
        a = 8'd255; b = 8'd1; #10;
        a = 8'd128; b = 8'd128; #10;
        
        $finish;
    end
endmodule
"""
    
    testbench_path = exp_manager.save_file(
        content=testbench_code,
        filename="simple_adder_tb.v",
        subdir="testbenches",
        description="简单加法器测试台"
    )
    print(f"测试台文件保存至: {testbench_path}")
    
    # 测试3: 复制依赖文件
    print("\n📋 测试3: 复制依赖文件")
    # 创建一个临时依赖文件
    temp_dep = exp_path.parent / "temp_dependency.v"
    temp_dep.write_text("// 临时依赖文件\nmodule temp_module; endmodule")
    
    if temp_dep.exists():
        dep_path = exp_manager.copy_dependency(
            str(temp_dep),
            description="临时依赖模块"
        )
        print(f"依赖文件复制至: {dep_path}")
        # 清理临时文件
        temp_dep.unlink()
    
    # 测试4: 获取实验摘要
    print("\n📋 测试4: 获取实验摘要")
    summary = exp_manager.get_experiment_summary()
    print(f"实验摘要: {summary}")
    
    # 测试5: 列出所有实验
    print("\n📋 测试5: 列出所有实验")
    experiments = exp_manager.list_experiments()
    print(f"实验数量: {len(experiments)}")
    for exp in experiments[:3]:  # 只显示前3个
        print(f"  - {exp['experiment_name']}: {exp['status']} ({exp.get('iterations', 0)} 迭代)")
    
    # 测试6: 结束实验
    print("\n📋 测试6: 结束实验")
    exp_manager.finish_experiment(
        success=True,
        final_notes="测试实验成功完成"
    )
    
    final_summary = exp_manager.get_experiment_summary()
    print(f"最终状态: {final_summary.get('status', 'unknown')}")
    
    print("\n✅ 实验管理器测试完成")
    return exp_path

def test_integration_with_base_agent():
    """测试与基础智能体的集成"""
    print("\n🤖 测试与基础智能体的集成")
    
    from core.experiment_manager import get_experiment_manager
    
    # 确保有活跃的实验
    exp_manager = get_experiment_manager()
    if not exp_manager.current_experiment_path:
        exp_path = exp_manager.create_new_experiment(
            experiment_name="base_agent_test",
            description="基础智能体集成测试"
        )
        print(f"创建测试实验: {exp_path}")
    
    # 测试基础智能体的文件保存
    try:
        from core.base_agent import BaseAgent
        from core.enums import AgentCapability
        
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="test_agent",
                    role="test",
                    capabilities={AgentCapability.CODE_GENERATION}
                )
            
            async def _call_llm_for_function_calling(self, conversation):
                return "Test response"
            
            def execute_enhanced_task(self, *args, **kwargs):
                pass
            
            def get_capabilities(self):
                return {AgentCapability.CODE_GENERATION}
            
            def get_specialty_description(self):
                return "测试智能体"
        
        # 创建测试智能体
        agent = TestAgent()
        
        print("✅ 测试智能体创建成功")
        print(f"当前实验路径: {exp_manager.current_experiment_path}")
        
    except Exception as e:
        print(f"❌ 基础智能体集成测试失败: {e}")

def main():
    """主测试函数"""
    print("🎯 开始实验管理器测试")
    print("="*60)
    
    exp_path = test_experiment_manager()
    test_integration_with_base_agent()
    
    print("\n" + "="*60)
    print("🎉 实验管理器测试完成")
    print(f"📁 测试实验位置: {exp_path}")

if __name__ == "__main__":
    main()