#!/usr/bin/env python3
"""
简单的协调智能体工具调用测试
禁用自我继续功能，直接测试工具调用
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

class SimpleCoordinatorTest:
    """简单的协调智能体测试"""
    
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
        self.code_review_agent = EnhancedRealCodeReviewAgent(self.config)
        
    async def setup_agents(self):
        """设置智能体"""
        self.logger.info("🔧 设置智能体...")
        
        # 注册智能体到协调器
        await self.coordinator.register_agent(self.verilog_agent)
        await self.coordinator.register_agent(self.code_review_agent)
        
        self.logger.info(f"✅ 智能体注册完成")
        self.logger.info(f"📋 已注册智能体: {list(self.coordinator.registered_agents.keys())}")
        
    async def test_simple_coordination(self):
        """测试简单的协调任务"""
        self.logger.info("🚀 开始简单协调任务测试")
        
        user_request = "设计一个4位加法器模块，包含基本加法功能和进位输出"
        
        try:
            # 直接调用process_with_function_calling，禁用自我继续
            self.logger.info(f"📝 用户请求: {user_request}")
            
            start_time = time.time()
            
            # 使用简化的调用方式，禁用自我继续
            result = await self.coordinator.process_with_function_calling(
                user_request=user_request,
                max_iterations=3,
                conversation_id=f"simple_test_{int(time.time())}",
                preserve_context=False,
                enable_self_continuation=False,  # 禁用自我继续
                max_self_iterations=0
            )
            
            execution_time = time.time() - start_time
            
            # 分析结果
            tool_calls_detected = self._analyze_tool_calls(result)
            
            self.logger.info(f"⏱️ 执行时间: {execution_time:.2f}秒")
            self.logger.info(f"🔧 检测到的工具调用: {tool_calls_detected}")
            self.logger.info(f"📄 结果长度: {len(str(result))} 字符")
            
            # 检查是否成功
            if tool_calls_detected:
                self.logger.info("✅ 测试成功 - 检测到工具调用")
                return {
                    "success": True,
                    "execution_time": execution_time,
                    "tool_calls_detected": tool_calls_detected,
                    "result_preview": str(result)[:500]
                }
            else:
                self.logger.warning("⚠️ 测试失败 - 未检测到工具调用")
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "tool_calls_detected": tool_calls_detected,
                    "result_preview": str(result)[:500]
                }
                
        except Exception as e:
            self.logger.error(f"❌ 测试异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    def _analyze_tool_calls(self, result):
        """分析结果中的工具调用"""
        if isinstance(result, dict):
            result_str = str(result)
        else:
            result_str = str(result)
        
        tool_indicators = [
            "identify_task_type",
            "recommend_agent", 
            "assign_task_to_agent",
            "analyze_agent_result",
            "check_task_completion",
            "query_agent_status",
            "tool_calls",
            "tool_name"
        ]
        
        detected_tools = []
        for tool in tool_indicators:
            if tool in result_str:
                detected_tools.append(tool)
        
        return detected_tools
    
    def print_result(self, result):
        """打印测试结果"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 简单协调任务测试结果")
        self.logger.info("="*60)
        
        if result.get('success', False):
            self.logger.info("✅ 测试成功")
            self.logger.info(f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒")
            self.logger.info(f"🔧 工具调用: {result.get('tool_calls_detected', [])}")
            self.logger.info("🎉 协调智能体工具调用修复成功！")
        else:
            self.logger.warning("❌ 测试失败")
            if result.get('error'):
                self.logger.warning(f"❌ 错误: {result['error']}")
            self.logger.warning(f"🔧 工具调用: {result.get('tool_calls_detected', [])}")
            self.logger.warning("⚠️ 协调智能体工具调用仍有问题")
        
        self.logger.info(f"📄 结果预览: {result.get('result_preview', '')[:200]}...")

async def main():
    """主函数"""
    test = SimpleCoordinatorTest()
    
    try:
        # 设置智能体
        await test.setup_agents()
        
        # 执行测试
        result = await test.test_simple_coordination()
        
        # 打印结果
        test.print_result(result)
        
    except Exception as e:
        logging.error(f"❌ 测试执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 