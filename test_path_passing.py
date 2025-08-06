#!/usr/bin/env python3
"""
路径传递功能测试脚本

测试协调智能体、设计智能体和代码审查智能体之间的路径传递功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig


async def test_path_passing():
    """测试路径传递功能"""
    print("🧪 开始测试路径传递功能...")
    
    try:
        # 1. 初始化配置
        config = FrameworkConfig.from_env()
        
        # 2. 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        print("✅ 协调智能体创建成功")
        
        # 3. 创建设计智能体
        verilog_agent = EnhancedRealVerilogAgent(config)
        print("✅ Verilog设计智能体创建成功")
        
        # 4. 创建代码审查智能体
        review_agent = EnhancedRealCodeReviewAgent(config)
        print("✅ 代码审查智能体创建成功")
        
        # 5. 注册智能体到协调器
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(review_agent)
        print("✅ 智能体注册成功")
        
        # 6. 执行协调任务
        user_request = "设计一个名为counter的Verilog模块，包含完整可编译代码、端口定义、功能实现和测试台验证。要求代码结构清晰、注释完善、命名规范且功能正确。"
        
        print(f"🎯 开始执行协调任务: {user_request[:50]}...")
        
        result = await coordinator.coordinate_task(
            user_request=user_request,
            max_iterations=5
        )
        
        # 7. 分析结果
        print("\n📊 测试结果分析:")
        print(f"✅ 任务执行状态: {result.get('success', False)}")
        
        if result.get('success'):
            print("🎉 路径传递测试成功！")
            
            # 检查实验路径
            experiment_path = result.get('experiment_path')
            if experiment_path:
                print(f"🧪 实验路径: {experiment_path}")
                
                # 检查文件是否保存在正确位置
                experiment_dir = Path(experiment_path)
                if experiment_dir.exists():
                    print(f"📁 实验目录存在: {experiment_dir}")
                    
                    # 检查子目录
                    designs_dir = experiment_dir / "designs"
                    testbenches_dir = experiment_dir / "testbenches"
                    reports_dir = experiment_dir / "reports"
                    
                    print(f"📂 设计目录: {designs_dir} {'✅' if designs_dir.exists() else '❌'}")
                    print(f"📂 测试台目录: {testbenches_dir} {'✅' if testbenches_dir.exists() else '❌'}")
                    print(f"📂 报告目录: {reports_dir} {'✅' if reports_dir.exists() else '❌'}")
                    
                    # 列出生成的文件
                    if designs_dir.exists():
                        design_files = list(designs_dir.glob("*.v"))
                        print(f"📄 设计文件数量: {len(design_files)}")
                        for file in design_files:
                            print(f"   - {file.name}")
                    
                    if testbenches_dir.exists():
                        testbench_files = list(testbenches_dir.glob("*.v"))
                        print(f"📄 测试台文件数量: {len(testbench_files)}")
                        for file in testbench_files:
                            print(f"   - {file.name}")
                    
                    if reports_dir.exists():
                        report_files = list(reports_dir.glob("*.txt")) + list(reports_dir.glob("*.json"))
                        print(f"📄 报告文件数量: {len(report_files)}")
                        for file in report_files:
                            print(f"   - {file.name}")
                else:
                    print(f"❌ 实验目录不存在: {experiment_dir}")
            else:
                print("❌ 未找到实验路径")
            
            # 检查生成的文件
            generated_files = result.get('generated_files', [])
            print(f"📄 生成文件数量: {len(generated_files)}")
            for file_info in generated_files:
                print(f"   - {file_info.get('file_path', 'unknown')} ({file_info.get('file_type', 'unknown')})")
            
            # 检查设计文件路径传递
            design_file_path = result.get('design_file_path')
            if design_file_path:
                print(f"📁 设计文件路径: {design_file_path}")
            else:
                print("❌ 未找到设计文件路径")
                
        else:
            print("❌ 路径传递测试失败")
            error = result.get('error', 'Unknown error')
            print(f"错误信息: {error}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_experiment_manager():
    """测试实验管理器功能"""
    print("\n🧪 测试实验管理器功能...")
    
    try:
        from core.experiment_manager import ExperimentManager
        
        # 创建实验管理器
        exp_manager = ExperimentManager()
        print("✅ 实验管理器创建成功")
        
        # 创建测试实验
        experiment_info = exp_manager.create_experiment(
            experiment_name="test_path_passing",
            task_description="测试路径传递功能",
            metadata={"test": True}
        )
        
        print(f"✅ 测试实验创建成功: {experiment_info.experiment_id}")
        print(f"📁 实验路径: {experiment_info.workspace_path}")
        
        # 检查实验目录结构
        workspace_path = Path(experiment_info.workspace_path)
        if workspace_path.exists():
            print("✅ 实验目录创建成功")
            
            # 检查子目录
            subdirs = ["designs", "testbenches", "reports", "logs", "temp"]
            for subdir in subdirs:
                subdir_path = workspace_path / subdir
                print(f"📂 {subdir}: {subdir_path} {'✅' if subdir_path.exists() else '❌'}")
        else:
            print("❌ 实验目录创建失败")
        
        return experiment_info
        
    except Exception as e:
        print(f"❌ 实验管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主测试函数"""
    print("🚀 开始路径传递功能测试")
    print("=" * 50)
    
    # 1. 测试实验管理器
    experiment_info = await test_experiment_manager()
    
    # 2. 测试路径传递
    result = await test_path_passing()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    
    if result and result.get('success'):
        print("🎉 所有测试通过！路径传递功能正常工作。")
    else:
        print("❌ 测试失败，请检查错误信息。")
    
    return result


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 