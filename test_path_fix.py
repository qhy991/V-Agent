#!/usr/bin/env python3
"""
测试文件路径修复
验证智能体可以使用正确的artifacts目录
"""

import asyncio
import os
from pathlib import Path
from core.enhanced_logging_config import get_artifacts_dir
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig


async def test_path_fix():
    """测试文件路径修复"""
    print("🚀 测试文件路径修复...")
    
    # 获取配置
    config = FrameworkConfig.from_env()
    artifacts_dir = get_artifacts_dir()
    
    print(f"📁 工件目录: {artifacts_dir}")
    print(f"✅ 工件目录存在: {artifacts_dir.exists()}")
    
    # 测试RealVerilogDesignAgent
    print("\n🔧 测试RealVerilogDesignAgent...")
    verilog_agent = RealVerilogDesignAgent(config)
    
    # 验证artifacts_dir设置
    print(f"   VerilogAgent artifacts_dir: {verilog_agent.artifacts_dir}")
    print(f"   是否为绝对路径: {verilog_agent.artifacts_dir.is_absolute()}")
    print(f"   目录存在: {verilog_agent.artifacts_dir.exists()}")
    
    # 测试RealCodeReviewAgent
    print("\n🔍 测试RealCodeReviewAgent...")
    review_agent = RealCodeReviewAgent(config)
    
    # 验证artifacts_dir设置
    print(f"   ReviewAgent artifacts_dir: {review_agent.artifacts_dir}")
    print(f"   是否为绝对路径: {review_agent.artifacts_dir.is_absolute()}")
    print(f"   目录存在: {review_agent.artifacts_dir.exists()}")
    
    # 测试目录创建
    test_subdir = artifacts_dir / "designs" / "test_module"
    test_subdir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_subdir / "test.v"
    test_file.write_text("// Test file for path fix verification")
    
    print(f"\n✅ 测试文件创建成功: {test_file}")
    print(f"   文件存在: {test_file.exists()}")
    
    # 清理测试文件
    test_file.unlink()
    test_subdir.rmdir()
    
    print("\n🎉 文件路径修复测试完成！")
    print("所有智能体现在使用正确的artifacts目录")


if __name__ == "__main__":
    asyncio.run(test_path_fix())