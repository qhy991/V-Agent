#!/usr/bin/env python3
"""
专门测试协调器日志映射
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 清理已有的日志管理器实例
import core.enhanced_logging_config
core.enhanced_logging_config._logger_manager = None

from core.enhanced_logging_config import setup_enhanced_logging, get_coordinator_logger
from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator

async def test_coordinator_logging():
    """专门测试协调器日志"""
    print("🧪 测试协调器日志映射...")
    
    # 1. 重新初始化日志系统
    logger_manager = setup_enhanced_logging("coordinator_log_test")
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 测试目录: {session_dir}")
    
    # 2. 手动测试不同logger名称的映射
    print("\n📝 测试logger映射...")
    
    # 测试coordinator相关的logger
    coord_logger = get_coordinator_logger()
    coord_logger.info("测试coordinator logger")
    
    # 手动创建Agent.centralized_coordinator logger
    agent_coord_logger = logger_manager.get_component_logger('coordinator', 'Agent.centralized_coordinator')
    agent_coord_logger.info("测试Agent.centralized_coordinator logger")
    
    # 3. 创建真实的协调器
    config = FrameworkConfig.from_env()
    coordinator = CentralizedCoordinator(config)
    coordinator.logger.info("真实协调器初始化完成")
    
    # 4. 检查日志文件
    print(f"\n📊 检查日志文件...")
    
    coord_log = session_dir / 'centralized_coordinator.log'
    base_log = session_dir / 'base_agent.log'
    
    print(f"协调器日志文件: {coord_log}")
    if coord_log.exists():
        size = coord_log.stat().st_size
        print(f"✅ centralized_coordinator.log: {size} bytes")
        if size > 0:
            with open(coord_log, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"📄 内容:\n{content}")
    else:
        print("❌ centralized_coordinator.log: 不存在")
    
    print(f"\n基础智能体日志文件: {base_log}")
    if base_log.exists():
        size = base_log.stat().st_size
        print(f"✅ base_agent.log: {size} bytes")
        if size > 0:
            with open(base_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            coord_lines = [line for line in lines if 'centralized_coordinator' in line]
            print(f"📄 协调器相关行数: {len(coord_lines)}")
            if coord_lines:
                print("📄 示例行:")
                for line in coord_lines[:3]:
                    print(f"  {line.strip()}")
    else:
        print("❌ base_agent.log: 不存在")
    
    return session_dir

if __name__ == "__main__":
    session_dir = asyncio.run(test_coordinator_logging())
    print(f"\n🎉 测试完成！日志目录: {session_dir}")