#!/usr/bin/env python3
"""
测试协调智能体修复效果
验证协调智能体能够正确调用工具来委托任务
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

class CoordinatorFixTest:
    """协调智能体修复测试"""
    
    def __init__(self):
        """初始化测试环境"""
        # 设置日志
        setup_enhanced_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置
        self.config = FrameworkConfig()
        
        # 初始化智能体
        self.coordinator = LLMCoordinatorAgent(self.config)
        self.verilog_agent = EnhancedRealVerilogAgent(self.config)
        self.review_agent = EnhancedRealCodeReviewAgent(self.config)
        
        self.logger.info("🔧 协调智能体修复测试初始化完成")
    
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
    
    async def test_simple_design_task(self):
        """测试简单设计任务"""
        self.logger.info("🧪 开始测试简单设计任务")
        
        user_request = "设计一个4位加法器模块，包含基本加法功能和进位输出"
        
        try:
            start_time = time.time()
            
            # 执行协调任务
            result = await self.coordinator.coordinate_task(
                user_request=user_request,
                max_iterations=5
            )
            
            execution_time = time.time() - start_time
            
            # 分析结果
            self._analyze_coordination_result(result, execution_time, "简单设计任务")
            
        except Exception as e:
            self.logger.error(f"❌ 简单设计任务测试失败: {str(e)}")
    
    async def test_verification_task(self):
        """测试验证任务"""
        self.logger.info("🧪 开始测试验证任务")
        
        user_request = "验证一个8位计数器的代码质量，生成testbench并进行仿真测试"
        
        try:
            start_time = time.time()
            
            # 执行协调任务
            result = await self.coordinator.coordinate_task(
                user_request=user_request,
                max_iterations=5
            )
            
            execution_time = time.time() - start_time
            
            # 分析结果
            self._analyze_coordination_result(result, execution_time, "验证任务")
            
        except Exception as e:
            self.logger.error(f"❌ 验证任务测试失败: {str(e)}")
    
    async def test_composite_task(self):
        """测试复合任务"""
        self.logger.info("🧪 开始测试复合任务")
        
        user_request = "设计一个16位ALU模块，包含加法、减法、逻辑运算功能，并生成完整的testbench进行验证"
        
        try:
            start_time = time.time()
            
            # 执行协调任务
            result = await self.coordinator.coordinate_task(
                user_request=user_request,
                max_iterations=8
            )
            
            execution_time = time.time() - start_time
            
            # 分析结果
            self._analyze_coordination_result(result, execution_time, "复合任务")
            
        except Exception as e:
            self.logger.error(f"❌ 复合任务测试失败: {str(e)}")
    
    def _analyze_coordination_result(self, result: dict, execution_time: float, task_name: str):
        """分析协调结果"""
        self.logger.info(f"📊 {task_name} 结果分析:")
        self.logger.info(f"   ⏱️ 执行时间: {execution_time:.2f}秒")
        self.logger.info(f"   ✅ 成功状态: {result.get('success', False)}")
        
        # 检查工具调用情况
        coordination_result = result.get('coordination_result', '')
        tool_calls_detected = self._detect_tool_calls(coordination_result)
        
        self.logger.info(f"   🔧 工具调用检测: {tool_calls_detected}")
        
        # 检查智能体参与情况
        agent_results = result.get('agent_results', {})
        self.logger.info(f"   🤖 参与智能体数量: {len(agent_results)}")
        
        for agent_id, agent_result in agent_results.items():
            self.logger.info(f"     - {agent_id}: {agent_result.get('success', False)}")
        
        # 检查执行摘要
        execution_summary = result.get('execution_summary', {})
        if execution_summary:
            self.logger.info(f"   📋 执行摘要:")
            for key, value in execution_summary.items():
                self.logger.info(f"     - {key}: {value}")
        
        # 检查错误信息
        if 'error' in result:
            self.logger.error(f"   ❌ 错误信息: {result['error']}")
    
    def _detect_tool_calls(self, result: str) -> dict:
        """检测工具调用情况"""
        tool_indicators = {
            "identify_task_type": "任务类型识别",
            "recommend_agent": "智能体推荐", 
            "assign_task_to_agent": "任务分配",
            "analyze_agent_result": "结果分析",
            "check_task_completion": "完成检查",
            "query_agent_status": "状态查询"
        }
        
        detected_tools = {}
        for tool_name, description in tool_indicators.items():
            if tool_name in result:
                detected_tools[tool_name] = description
        
        return detected_tools
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始运行协调智能体修复测试")
        
        try:
            # 设置智能体
            await self.setup_agents()
            
            # 运行测试
            await self.test_simple_design_task()
            await asyncio.sleep(2)  # 等待一下
            
            await self.test_verification_task()
            await asyncio.sleep(2)  # 等待一下
            
            await self.test_composite_task()
            
            self.logger.info("✅ 所有测试完成")
            
        except Exception as e:
            self.logger.error(f"❌ 测试运行失败: {str(e)}")

async def main():
    """主函数"""
    test = CoordinatorFixTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 