#!/usr/bin/env python3
"""
测试实验管理器设置
"""

import asyncio
import time
from pathlib import Path
from core.experiment_manager import ExperimentManager

async def test_experiment_manager():
    print("🧪 测试实验管理器设置")
    
    # 创建实验目录
    artifacts_dir = Path("tdd_experiments") / f"unified_tdd_adder_16bit_{int(time.time())}"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 实验目录: {artifacts_dir}")
    
    # 设置实验管理器
    exp_manager = ExperimentManager(base_workspace=artifacts_dir.parent)
    exp_path = exp_manager.create_new_experiment(
        experiment_name=f"unified_tdd_adder_16bit_{int(time.time())}",
        description="统一TDD实验: adder_16bit 设计"
    )
    
    print(f"🔧 实验管理器设置完成:")
    print(f"   - 基础路径: {exp_manager.base_workspace}")
    print(f"   - 当前实验: {exp_manager.current_experiment}")
    print(f"   - 实验路径: {exp_manager.current_experiment_path}")
    
    # 设置全局实验管理器实例
    import core.experiment_manager as exp_module
    exp_module._experiment_manager = exp_manager
    
    # 测试保存文件
    test_content = "module test_module(); endmodule"
    file_path = exp_manager.save_file(
        content=test_content,
        filename="test.v",
        subdir="designs",
        description="测试文件"
    )
    
    print(f"📝 测试文件保存结果: {file_path}")
    
    # 检查文件是否存在
    if file_path and file_path.exists():
        print(f"✅ 文件保存成功: {file_path}")
        print(f"📄 文件内容: {file_path.read_text()}")
    else:
        print(f"❌ 文件保存失败")

if __name__ == "__main__":
    asyncio.run(test_experiment_manager()) 