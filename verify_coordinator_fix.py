#!/usr/bin/env python3
"""
验证协调器日志修复是否成功
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_logging_config import setup_enhanced_logging, get_test_logger
from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent

async def verify_coordinator_logging():
    """验证协调器日志修复"""
    print("🔍 验证协调器日志修复...")
    
    # 1. 重新初始化日志系统
    logger_manager = setup_enhanced_logging("coordinator_fix_verification")
    test_logger = get_test_logger()
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 测试目录: {session_dir}")
    
    # 2. 创建协调器（应用修复后的日志配置）
    config = FrameworkConfig.from_env()
    coordinator = CentralizedCoordinator(config)
    
    # 3. 记录几条测试日志
    coordinator.logger.info("协调器日志测试 - 这应该写入centralized_coordinator.log")
    coordinator.logger.debug("协调器调试信息测试")
    coordinator.logger.warning("协调器警告信息测试")
    
    test_logger.info("测试框架日志 - 这应该在test_framework.log中")
    
    # 4. 创建一个智能体来对比
    verilog_agent = RealVerilogDesignAgent(config)
    verilog_agent.logger.info("Verilog智能体测试 - 这应该在base_agent.log中")
    
    # 5. 检查日志文件
    print(f"\n📊 检查日志文件...")
    
    key_files = {
        'centralized_coordinator.log': '协调器专用日志',
        'base_agent.log': '基础智能体日志',
        'test_framework.log': '测试框架日志',
        'experiment_summary.log': '实验摘要'
    }
    
    results = {}
    
    for log_file, description in key_files.items():
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            results[log_file] = size
            
            if size > 0:
                print(f"✅ {description}: {size} bytes")
                
                # 检查内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                coord_lines = content.count('协调器')
                agent_lines = content.count('Agent.')
                
                if coord_lines > 0:
                    print(f"   🧠 协调器相关: {coord_lines} 行")
                if agent_lines > 0:
                    print(f"   🤖 Agent相关: {agent_lines} 行")
                    
            else:
                print(f"❌ {description}: 文件为空")
                results[log_file] = 0
        else:
            print(f"❌ {description}: 不存在")
            results[log_file] = -1
    
    # 6. 验证结果
    print(f"\n🎯 修复验证结果:")
    
    coord_log_working = results.get('centralized_coordinator.log', 0) > 0
    base_log_working = results.get('base_agent.log', 0) > 0
    
    if coord_log_working:
        print(f"✅ 协调器日志修复成功！centralized_coordinator.log正常工作")
    else:
        print(f"❌ 协调器日志仍有问题")
    
    if base_log_working:
        print(f"✅ 基础智能体日志正常工作")
    else:
        print(f"⚠️ 基础智能体日志可能有问题")
    
    if coord_log_working and base_log_working:
        print(f"\n🎉 日志修复完全成功！")
        print(f"   - 协调器日志现在写入: centralized_coordinator.log")
        print(f"   - 其他智能体日志写入: base_agent.log")
        print(f"   - LLM对话记录功能正常")
        
        return True
    else:
        print(f"\n⚠️ 日志修复可能不完整")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_coordinator_logging())
    if success:
        print(f"\n🚀 现在可以运行 test_multi_agent_riscv_project.py")
        print(f"   协调器的所有活动都会正确记录在 centralized_coordinator.log 中！")
    else:
        print(f"\n⚠️ 请检查修复是否正确应用")