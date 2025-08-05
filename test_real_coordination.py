#!/usr/bin/env python3
"""
真实协调任务测试
使用真实LLM调用验证完整的智能体协作流程
"""

import asyncio
import time
import logging
from pathlib import Path

# 设置项目路径
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
from core.enhanced_logging_config import setup_enhanced_logging

class RealCoordinationTest:
    """真实协调任务测试"""
    
    def __init__(self):
        """初始化测试环境"""
        # 设置日志
        setup_enhanced_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置 - 从.env文件加载
        self.config = FrameworkConfig.from_env()
        
        # 初始化智能体
        self.coordinator = LLMCoordinatorAgent(self.config)
        self.verilog_agent = EnhancedRealVerilogAgent(self.config)
        self.review_agent = EnhancedRealCodeReviewAgent(self.config)
        
        self.logger.info("🔧 真实协调任务测试初始化完成")
    
    async def setup_agents(self):
        """设置智能体"""
        try:
            # 注册智能体到协调器
            await self.coordinator.register_agent(self.verilog_agent)
            await self.coordinator.register_agent(self.review_agent)
            
            self.logger.info("✅ 智能体注册完成")
            self.logger.info(f"📋 已注册智能体: {list(self.coordinator.get_registered_agents().keys())}")
            
        except Exception as e:
            self.logger.error(f"❌ 智能体设置失败: {str(e)}")
            raise
    
    async def test_real_coordination(self):
        """测试真实协调任务"""
        self.logger.info("🧪 开始真实协调任务测试")
        
        # 测试任务
        user_request = "设计一个4位加法器模块，包含进位输入和进位输出，并生成测试台进行验证"
        
        self.logger.info(f"📋 用户请求: {user_request}")
        
        try:
            # 执行协调任务
            start_time = time.time()
            
            result = await self.coordinator.coordinate_task(
                user_request=user_request,
                conversation_id=f"test_conversation_{int(time.time())}",
                max_iterations=3
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.logger.info(f"⏱️ 执行时间: {execution_time:.2f}秒")
            self.logger.info(f"📊 协调结果: {result}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 协调任务执行失败: {str(e)}")
            return False
    
    async def run_test(self):
        """运行测试"""
        self.logger.info("🚀 开始运行真实协调任务测试")
        
        try:
            # 设置智能体
            await self.setup_agents()
            
            # 执行真实协调任务
            success = await self.test_real_coordination()
            
            if success:
                self.logger.info("✅ 真实协调任务测试完成")
            else:
                self.logger.error("❌ 真实协调任务测试失败")
                
        except Exception as e:
            self.logger.error(f"❌ 测试运行失败: {str(e)}")

async def main():
    """主函数"""
    test = RealCoordinationTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 