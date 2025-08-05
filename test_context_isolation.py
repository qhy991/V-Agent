#!/usr/bin/env python3
"""
测试智能体对话上下文隔离
验证协调智能体和设计智能体之间的对话历史不会混淆
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from config.config import FrameworkConfig

class ContextIsolationTester:
    """对话上下文隔离测试器"""
    
    def __init__(self):
        self.config = FrameworkConfig()
        self.coordinator = LLMCoordinatorAgent(self.config)
        self.design_agent = EnhancedRealVerilogAgent(self.config)
        
    async def setup_agents(self):
        """设置智能体"""
        print("🔧 设置智能体...")
        
        # 注册设计智能体到协调智能体
        await self.coordinator.register_agent(self.design_agent)
        
        print("✅ 智能体设置完成")
        
    async def test_context_isolation(self):
        """测试对话上下文隔离"""
        print("\n🧪 测试1: 对话上下文隔离")
        print("="*60)
        
        # 第一步：协调智能体进行一些对话
        print("📋 步骤1: 协调智能体进行初始对话")
        coordinator_response1 = await self.coordinator.process_with_function_calling(
            user_request="请分析一下当前的任务分配策略",
            conversation_id="test_session_001",
            preserve_context=True,
            max_iterations=3
        )
        
        print(f"协调智能体响应1长度: {len(coordinator_response1)}")
        print(f"协调智能体对话历史长度: {len(self.coordinator.conversation_history)}")
        
        # 第二步：协调智能体再次对话
        print("\n📋 步骤2: 协调智能体进行第二次对话")
        coordinator_response2 = await self.coordinator.process_with_function_calling(
            user_request="请检查一下已注册的智能体状态",
            conversation_id="test_session_001",
            preserve_context=True,
            max_iterations=3
        )
        
        print(f"协调智能体响应2长度: {len(coordinator_response2)}")
        print(f"协调智能体对话历史长度: {len(self.coordinator.conversation_history)}")
        
        # 第三步：协调智能体调用设计智能体
        print("\n📋 步骤3: 协调智能体调用设计智能体")
        
        # 检查设计智能体调用前的状态
        print(f"设计智能体调用前对话历史长度: {len(self.design_agent.conversation_history)}")
        print(f"设计智能体调用前对话ID: {getattr(self.design_agent, 'current_conversation_id', 'None')}")
        
        # 模拟协调智能体调用设计智能体
        design_response = await self.design_agent.process_with_function_calling(
            user_request="请设计一个4位加法器模块",
            conversation_id="test_session_001",  # 使用相同的对话ID
            preserve_context=True,
            max_iterations=5
        )
        
        print(f"设计智能体响应长度: {len(design_response)}")
        print(f"设计智能体调用后对话历史长度: {len(self.design_agent.conversation_history)}")
        print(f"设计智能体调用后对话ID: {getattr(self.design_agent, 'current_conversation_id', 'None')}")
        
        # 第四步：验证对话历史隔离
        print("\n📋 步骤4: 验证对话历史隔离")
        
        # 检查协调智能体的对话历史是否包含设计智能体的内容
        coordinator_history_text = " ".join([msg.get("content", "") for msg in self.coordinator.conversation_history])
        design_history_text = " ".join([msg.get("content", "") for msg in self.design_agent.conversation_history])
        
        # 检查设计智能体的对话历史是否包含协调智能体的内容
        coordinator_keywords = ["任务分配", "智能体状态", "协调"]
        design_keywords = ["4位加法器", "Verilog", "模块"]
        
        coordinator_in_design = any(keyword in design_history_text for keyword in coordinator_keywords)
        design_in_coordinator = any(keyword in coordinator_history_text for keyword in design_keywords)
        
        print(f"协调智能体对话历史包含设计内容: {design_in_coordinator}")
        print(f"设计智能体对话历史包含协调内容: {coordinator_in_design}")
        
        # 验证结果
        if not coordinator_in_design and not design_in_coordinator:
            print("✅ 对话上下文隔离测试通过！")
            return True
        else:
            print("❌ 对话上下文隔离测试失败！")
            if coordinator_in_design:
                print("   - 协调智能体对话历史中包含了设计智能体的内容")
            if design_in_coordinator:
                print("   - 设计智能体对话历史中包含了协调智能体的内容")
            return False
    
    async def test_agent_specific_conversation_ids(self):
        """测试智能体特定的对话ID生成"""
        print("\n🧪 测试2: 智能体特定对话ID生成")
        print("="*60)
        
        # 测试协调智能体
        await self.coordinator.process_with_function_calling(
            user_request="测试消息",
            conversation_id="test_id_001",
            preserve_context=False,
            max_iterations=1
        )
        
        coordinator_conversation_id = getattr(self.coordinator, 'current_conversation_id', None)
        print(f"协调智能体对话ID: {coordinator_conversation_id}")
        
        # 测试设计智能体
        await self.design_agent.process_with_function_calling(
            user_request="测试消息",
            conversation_id="test_id_001",  # 相同的原始ID
            preserve_context=False,
            max_iterations=1
        )
        
        design_conversation_id = getattr(self.design_agent, 'current_conversation_id', None)
        print(f"设计智能体对话ID: {design_conversation_id}")
        
        # 验证对话ID是否不同
        if coordinator_conversation_id != design_conversation_id:
            print("✅ 智能体特定对话ID生成测试通过！")
            print(f"   - 协调智能体: {coordinator_conversation_id}")
            print(f"   - 设计智能体: {design_conversation_id}")
            return True
        else:
            print("❌ 智能体特定对话ID生成测试失败！")
            print(f"   - 两个智能体使用了相同的对话ID: {coordinator_conversation_id}")
            return False
    
    async def test_context_preservation_within_agent(self):
        """测试同一智能体内的上下文保持"""
        print("\n🧪 测试3: 同一智能体内的上下文保持")
        print("="*60)
        
        # 设计智能体第一次调用
        await self.design_agent.process_with_function_calling(
            user_request="请设计一个2位计数器",
            conversation_id="design_session_001",
            preserve_context=True,
            max_iterations=3
        )
        
        initial_history_length = len(self.design_agent.conversation_history)
        print(f"第一次调用后对话历史长度: {initial_history_length}")
        
        # 设计智能体第二次调用（应该保持上下文）
        await self.design_agent.process_with_function_calling(
            user_request="请优化刚才设计的计数器",
            conversation_id="design_session_001",
            preserve_context=True,
            max_iterations=3
        )
        
        final_history_length = len(self.design_agent.conversation_history)
        print(f"第二次调用后对话历史长度: {final_history_length}")
        
        # 验证上下文是否保持
        if final_history_length > initial_history_length:
            print("✅ 同一智能体内上下文保持测试通过！")
            print(f"   - 对话历史从 {initial_history_length} 增加到 {final_history_length}")
            return True
        else:
            print("❌ 同一智能体内上下文保持测试失败！")
            print(f"   - 对话历史没有增加: {initial_history_length} -> {final_history_length}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始对话上下文隔离测试")
        print("="*80)
        
        await self.setup_agents()
        
        test_results = []
        
        # 运行测试
        test_results.append(await self.test_context_isolation())
        test_results.append(await self.test_agent_specific_conversation_ids())
        test_results.append(await self.test_context_preservation_within_agent())
        
        # 总结结果
        print("\n📊 测试结果总结")
        print("="*80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"通过测试: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！对话上下文隔离功能正常工作。")
        else:
            print("⚠️ 部分测试失败，需要进一步调试。")
        
        return passed_tests == total_tests

async def main():
    """主函数"""
    tester = ContextIsolationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ 对话上下文隔离修复验证成功！")
        print("现在协调智能体和设计智能体将维护独立的对话历史。")
    else:
        print("\n❌ 对话上下文隔离修复验证失败！")
        print("需要进一步检查和修复。")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 