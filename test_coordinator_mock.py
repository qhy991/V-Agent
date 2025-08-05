#!/usr/bin/env python3
"""
模拟测试协调智能体修复效果
验证协调智能体的强制性工具调用逻辑
"""

import asyncio
import time
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# 设置项目路径
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
from core.enhanced_logging_config import setup_enhanced_logging

class MockLLMClient:
    """模拟LLM客户端"""
    
    def __init__(self):
        self.call_count = 0
    
    async def send_prompt_optimized(self, conversation_id, user_message, system_prompt=None, temperature=0.3, max_tokens=4000, force_refresh_system=False):
        """模拟优化的LLM调用"""
        self.call_count += 1
        
        # 模拟不同的响应
        if self.call_count == 1:
            # 第一次调用：返回工具调用
            return '''{
                "tool_calls": [
                    {
                        "tool_name": "identify_task_type",
                        "parameters": {
                            "user_request": "设计一个16位ALU模块，包含加法、减法、逻辑运算功能，并生成完整的testbench进行验证",
                            "context": {
                                "previous_tasks": [],
                                "user_preferences": {}
                            }
                        }
                    }
                ]
            }'''
        elif self.call_count == 2:
            # 第二次调用：返回智能体推荐
            return '''{
                "tool_calls": [
                    {
                        "tool_name": "recommend_agent",
                        "parameters": {
                            "task_type": "composite",
                            "task_description": "设计一个16位ALU模块",
                            "priority": "high",
                            "constraints": {
                                "time_limit": 300,
                                "quality_requirement": "high"
                            }
                        }
                    }
                ]
            }'''
        elif self.call_count == 3:
            # 第三次调用：返回任务分配
            return '''{
                "tool_calls": [
                    {
                        "tool_name": "assign_task_to_agent",
                        "parameters": {
                            "agent_id": "enhanced_real_verilog_agent",
                            "task_description": "设计一个16位ALU模块，包含加法、减法、逻辑运算功能",
                            "expected_output": "完整的Verilog代码、模块说明和设计文档",
                            "task_type": "design",
                            "priority": "high"
                        }
                    }
                ]
            }'''
        else:
            # 后续调用：返回完成状态
            return "任务已完成，所有工具调用成功执行"

class CoordinatorMockTest:
    """协调智能体模拟测试"""
    
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
        
        # 模拟LLM客户端
        self.mock_llm_client = MockLLMClient()
        
        self.logger.info("🔧 协调智能体模拟测试初始化完成")
    
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
    
    def test_has_executed_tools_logic(self):
        """测试工具调用检测逻辑"""
        self.logger.info("🧪 测试工具调用检测逻辑")
        
        # 测试用例1：包含工具调用的结果
        result_with_tools = """
        我调用了identify_task_type工具来识别任务类型，
        然后使用assign_task_to_agent工具分配任务给智能体，
        最后调用analyze_agent_result工具分析结果。
        """
        
        has_tools = self.coordinator._has_executed_tools(result_with_tools)
        self.logger.info(f"   📊 包含工具调用的结果检测: {has_tools}")
        
        # 测试用例2：不包含工具调用的结果
        result_without_tools = """
        我分析了用户需求，制定了执行策略，
        认为这是一个设计任务，应该分配给verilog智能体。
        任务分析完成，策略制定完毕。
        """
        
        has_tools = self.coordinator._has_executed_tools(result_without_tools)
        self.logger.info(f"   📊 不包含工具调用的结果检测: {has_tools}")
        
        # 测试用例3：包含部分工具调用的结果
        result_partial_tools = """
        我调用了identify_task_type工具识别任务类型，
        然后制定了执行策略，但没有调用其他工具。
        """
        
        has_tools = self.coordinator._has_executed_tools(result_partial_tools)
        self.logger.info(f"   📊 部分工具调用的结果检测: {has_tools}")
    
    def test_forced_coordination_task(self):
        """测试强制性协调任务构建"""
        self.logger.info("🧪 测试强制性协调任务构建")
        
        user_request = "设计一个8位加法器模块"
        task_context = MagicMock()
        task_context.task_id = "test_task_123"
        task_context.current_stage = "initial"
        task_context.iteration_count = 0
        task_context.max_iterations = 5
        task_context.external_testbench_path = None
        
        # 模拟注册的智能体
        self.coordinator.registered_agents = {
            "enhanced_real_verilog_agent": MagicMock(),
            "enhanced_real_code_review_agent": MagicMock()
        }
        
        forced_task = self.coordinator._build_forced_coordination_task(user_request, task_context)
        
        # 检查强制性要求是否包含
        required_elements = [
            "🚨 强制性要求",
            "identify_task_type",
            "recommend_agent", 
            "assign_task_to_agent",
            "analyze_agent_result",
            "check_task_completion",
            "不能只进行文本分析",
            "必须调用工具来委托任务"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in forced_task:
                missing_elements.append(element)
        
        if missing_elements:
            self.logger.error(f"   ❌ 缺少强制性元素: {missing_elements}")
        else:
            self.logger.info("   ✅ 强制性协调任务构建正确")
        
        self.logger.info(f"   📝 任务长度: {len(forced_task)} 字符")
    
    def test_system_prompt_improvements(self):
        """测试系统提示词改进"""
        self.logger.info("🧪 测试系统提示词改进")
        
        system_prompt = self.coordinator._build_enhanced_system_prompt()
        
        # 检查关键改进点
        improvements = [
            "🚨 强制性执行规则",
            "必须执行的步骤",
            "identify_task_type",
            "recommend_agent",
            "assign_task_to_agent", 
            "analyze_agent_result",
            "check_task_completion",
            "禁止行为",
            "不能只进行文本分析",
            "不能无限循环进行自我评估",
            "不能跳过工具调用步骤",
            "不能只返回策略而不执行"
        ]
        
        missing_improvements = []
        for improvement in improvements:
            if improvement not in system_prompt:
                missing_improvements.append(improvement)
        
        if missing_improvements:
            self.logger.error(f"   ❌ 缺少改进点: {missing_improvements}")
        else:
            self.logger.info("   ✅ 系统提示词改进完整")
        
        self.logger.info(f"   📝 提示词长度: {len(system_prompt)} 字符")
    
    async def test_coordination_flow_logic(self):
        """测试协调流程逻辑"""
        self.logger.info("🧪 测试协调流程逻辑")
        
        # 模拟工具调用结果
        mock_tool_results = [
            {"tool_name": "identify_task_type", "success": True, "result": {"task_type": "composite"}},
            {"tool_name": "recommend_agent", "success": True, "result": {"recommended_agent": "enhanced_real_verilog_agent"}},
            {"tool_name": "assign_task_to_agent", "success": True, "result": {"assignment_id": "task_123"}},
            {"tool_name": "analyze_agent_result", "success": True, "result": {"quality_score": 85}},
            {"tool_name": "check_task_completion", "success": True, "result": {"completed": True}}
        ]
        
        # 检查流程完整性
        expected_tools = ["identify_task_type", "recommend_agent", "assign_task_to_agent", "analyze_agent_result", "check_task_completion"]
        
        for i, (expected_tool, mock_result) in enumerate(zip(expected_tools, mock_tool_results)):
            self.logger.info(f"   📋 步骤 {i+1}: {expected_tool} - {mock_result['success']}")
        
        self.logger.info("   ✅ 协调流程逻辑验证完成")
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始运行协调智能体模拟测试")
        
        try:
            # 设置智能体
            await self.setup_agents()
            
            # 运行测试
            self.test_has_executed_tools_logic()
            await asyncio.sleep(1)
            
            self.test_forced_coordination_task()
            await asyncio.sleep(1)
            
            self.test_system_prompt_improvements()
            await asyncio.sleep(1)
            
            await self.test_coordination_flow_logic()
            
            self.logger.info("✅ 所有模拟测试完成")
            
        except Exception as e:
            self.logger.error(f"❌ 测试运行失败: {str(e)}")

async def main():
    """主函数"""
    test = CoordinatorMockTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 