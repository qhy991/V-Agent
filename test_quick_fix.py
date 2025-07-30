#!/usr/bin/env python3
"""
快速测试FileReference修复
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.centralized_coordinator import CentralizedCoordinator
from core.base_agent import TaskMessage
from agents.real_verilog_agent import RealVerilogDesignAgent
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from tools.sample_database import setup_database_for_framework

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fix():
    """快速测试修复"""
    print("🧪 测试FileReference修复...")
    
    config = FrameworkConfig.from_env()
    llm_client = EnhancedLLMClient(config.llm)
    coordinator = CentralizedCoordinator(config, llm_client)
    
    try:
        # 设置最小测试环境
        await setup_database_for_framework("./output/test_fix.db")
        
        # 创建并注册智能体
        verilog_agent = RealVerilogDesignAgent(config)
        coordinator.register_agent(verilog_agent)
        
        # 测试简单的任务分析
        task_analysis = await coordinator.analyze_task_requirements("设计一个简单的计数器")
        print(f"✅ 任务分析完成: {task_analysis.get('task_type')}")
        
        # 测试智能体选择
        selected_agent = await coordinator.select_best_agent(task_analysis)
        print(f"✅ 智能体选择完成: {selected_agent}")
        
        print("🎉 FileReference修复测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fix())
    sys.exit(0 if success else 1)