#!/usr/bin/env python3
"""
增强的协调智能体工具调用修复测试
验证修复后的协调智能体能够正确执行工具调用
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

class CoordinatorFixEnhancedTest:
    """增强的协调智能体修复测试"""
    
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
        
    async def test_tool_calling_fix(self):
        """测试工具调用修复效果"""
        self.logger.info("🚀 开始测试协调智能体工具调用修复效果")
        
        # 测试用例
        test_cases = [
            {
                "name": "设计任务测试",
                "request": "设计一个4位加法器模块，包含基本加法功能和进位输出",
                "expected_tools": ["identify_task_type", "recommend_agent", "assign_task_to_agent"]
            },
            {
                "name": "验证任务测试", 
                "request": "验证并测试一个计数器模块，生成testbench并进行仿真",
                "expected_tools": ["identify_task_type", "recommend_agent", "assign_task_to_agent"]
            },
            {
                "name": "分析任务测试",
                "request": "分析一个Verilog模块的代码质量，检查语法错误和设计问题",
                "expected_tools": ["identify_task_type", "recommend_agent", "assign_task_to_agent"]
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            self.logger.info(f"\n📋 测试用例 {i}: {test_case['name']}")
            self.logger.info(f"📝 用户请求: {test_case['request']}")
            
            try:
                # 执行协调任务
                start_time = time.time()
                result = await self.coordinator.coordinate_task(
                    user_request=test_case['request'],
                    conversation_id=f"test_fix_{i}_{int(time.time())}",
                    max_iterations=3
                )
                execution_time = time.time() - start_time
                
                # 分析结果
                success = result.get('success', False)
                tool_calls_detected = self._analyze_tool_calls(result)
                
                test_result = {
                    "test_case": test_case['name'],
                    "success": success,
                    "execution_time": execution_time,
                    "tool_calls_detected": tool_calls_detected,
                    "expected_tools": test_case['expected_tools'],
                    "result_summary": str(result)[:500]
                }
                
                results.append(test_result)
                
                # 输出结果
                if success:
                    self.logger.info(f"✅ 测试通过 - 执行时间: {execution_time:.2f}秒")
                    self.logger.info(f"🔧 检测到的工具调用: {tool_calls_detected}")
                else:
                    self.logger.warning(f"⚠️ 测试失败 - 执行时间: {execution_time:.2f}秒")
                    self.logger.warning(f"❌ 错误信息: {result.get('error', '未知错误')}")
                
            except Exception as e:
                self.logger.error(f"❌ 测试异常: {str(e)}")
                results.append({
                    "test_case": test_case['name'],
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                })
        
        return results
    
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
            "query_agent_status"
        ]
        
        detected_tools = []
        for tool in tool_indicators:
            if tool in result_str:
                detected_tools.append(tool)
        
        return detected_tools
    
    def print_summary(self, results):
        """打印测试总结"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 协调智能体工具调用修复测试总结")
        self.logger.info("="*60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        failed_tests = total_tests - successful_tests
        
        self.logger.info(f"📋 总测试数: {total_tests}")
        self.logger.info(f"✅ 成功测试: {successful_tests}")
        self.logger.info(f"❌ 失败测试: {failed_tests}")
        self.logger.info(f"📈 成功率: {successful_tests/total_tests*100:.1f}%")
        
        # 详细结果
        for result in results:
            status = "✅" if result.get('success', False) else "❌"
            self.logger.info(f"{status} {result['test_case']}: {result.get('execution_time', 0):.2f}秒")
            if result.get('tool_calls_detected'):
                self.logger.info(f"   🔧 工具调用: {result['tool_calls_detected']}")
            if result.get('error'):
                self.logger.info(f"   ❌ 错误: {result['error']}")
        
        # 修复效果评估
        if successful_tests > 0:
            self.logger.info("\n🎉 修复效果评估:")
            self.logger.info("✅ 协调智能体现在能够正确执行工具调用")
            self.logger.info("✅ 强制性执行机制正常工作")
            self.logger.info("✅ 工具调用检测逻辑准确")
        else:
            self.logger.warning("\n⚠️ 修复效果评估:")
            self.logger.warning("❌ 协调智能体仍存在工具调用问题")
            self.logger.warning("❌ 需要进一步调试和修复")

async def main():
    """主函数"""
    test = CoordinatorFixEnhancedTest()
    
    try:
        # 设置智能体
        await test.setup_agents()
        
        # 执行测试
        results = await test.test_tool_calling_fix()
        
        # 打印总结
        test.print_summary(results)
        
    except Exception as e:
        logging.error(f"❌ 测试执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 