#!/usr/bin/env python3
"""
🧪 多轮对话功能测试脚本
==================================================

测试智能体是否能够：
1. 记住之前的对话历史
2. 在后续迭代中避免重复错误
3. 基于之前的上下文进行改进
"""

import asyncio
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from extensions import create_test_driven_coordinator, TestDrivenConfig


class MultiRoundConversationTest:
    """多轮对话功能测试"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        if not self.config.llm.api_key:
            self.config.llm.api_key = "sk-66ed80a639194920a3840f7013960171"
        
        # 创建智能体
        self.verilog_agent = EnhancedRealVerilogAgent(self.config)
        self.review_agent = EnhancedRealCodeReviewAgent(self.config)
        
        # 创建协调器
        base_coordinator = EnhancedCentralizedCoordinator(self.config)
        base_coordinator.register_agent(self.verilog_agent)
        base_coordinator.register_agent(self.review_agent)
        
        # 创建测试驱动协调器
        self.coordinator = create_test_driven_coordinator(
            base_coordinator=base_coordinator,
            config=TestDrivenConfig(
                max_iterations=3,
                timeout_per_iteration=300,
                enable_deep_analysis=True,
                auto_fix_suggestions=True,
                save_iteration_logs=True,
                enable_persistent_conversation=True,  # 启用持续对话
                max_conversation_history=50
            )
        )
        
        print("🧪 多轮对话功能测试初始化完成")
    
    async def test_basic_multiround_conversation(self):
        """测试基本的多轮对话功能"""
        print("\n" + "="*60)
        print("🧪 测试1: 基本多轮对话功能")
        print("="*60)
        
        # 第一轮对话
        print("🔄 第一轮对话: 设计一个简单的8位加法器")
        task1 = """
设计一个简单的8位加法器模块，支持基本的二进制加法运算。

模块接口：
```verilog
module simple_8bit_adder (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);
```

功能要求：
1. 实现8位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 支持所有可能的输入组合（0到255）
4. 处理进位传播
        """
        
        result1 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task1,
            max_iterations=2,
            conversation_history=[]  # 空的历史
        )
        
        print(f"✅ 第一轮结果: {'成功' if result1['success'] else '失败'}")
        print(f"   对话轮数: {len(result1.get('conversation_history', []))}")
        
        # 第二轮对话 - 基于第一轮的结果
        print("\n🔄 第二轮对话: 修复编译错误")
        task2 = """
根据第一轮的设计结果，修复任何编译错误。

请分析之前的代码，找出问题并进行修复。
        """
        
        # 使用第一轮的对话历史
        conversation_history = result1.get('conversation_history', [])
        print(f"🔗 传递{len(conversation_history)}轮对话历史到第二轮")
        
        result2 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task2,
            max_iterations=2,
            conversation_history=conversation_history  # 传递历史
        )
        
        print(f"✅ 第二轮结果: {'成功' if result2['success'] else '失败'}")
        print(f"   对话轮数: {len(result2.get('conversation_history', []))}")
        
        # 第三轮对话 - 进一步改进
        print("\n🔄 第三轮对话: 优化设计")
        task3 = """
基于前两轮的设计，进一步优化代码：

1. 改进代码风格和可读性
2. 添加适当的注释
3. 确保代码符合Verilog最佳实践
        """
        
        # 使用前两轮的完整历史
        full_history = result2.get('conversation_history', [])
        print(f"🔗 传递{len(full_history)}轮完整对话历史到第三轮")
        
        result3 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task3,
            max_iterations=2,
            conversation_history=full_history  # 传递完整历史
        )
        
        print(f"✅ 第三轮结果: {'成功' if result3['success'] else '失败'}")
        print(f"   对话轮数: {len(result3.get('conversation_history', []))}")
        
        # 分析结果
        print("\n📊 多轮对话分析:")
        print(f"   总对话轮数: {len(result3.get('conversation_history', []))}")
        print(f"   成功轮数: {sum(1 for r in [result1, result2, result3] if r['success'])}/3")
        
        # 检查对话历史是否连续
        history = result3.get('conversation_history', [])
        if len(history) >= 6:  # 至少应该有6轮对话（3轮用户输入 + 3轮AI响应）
            print(f"   ✅ 对话历史连续性: 正常 ({len(history)} 轮)")
        else:
            print(f"   ❌ 对话历史连续性: 异常 ({len(history)} 轮)")
        
        return result1, result2, result3
    
    async def test_tdd_multiround_conversation(self):
        """测试TDD模式下的多轮对话功能"""
        print("\n" + "="*60)
        print("🧪 测试2: TDD模式多轮对话功能")
        print("="*60)
        
        task_description = """
设计一个16位加法器模块adder_16bit，严格按照以下接口规范实现：

**关键要求 - 接口必须完全匹配**:
```verilog
module adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数
    input         cin,      // 输入进位
    output [15:0] sum,      // 16位和输出
    output        cout,     // 输出进位
    output        overflow  // 溢出标志（有符号运算）
);
```

**功能要求**:
1. **加法运算**: 实现16位二进制加法 sum = a + b + cin
2. **进位处理**: 正确计算输出进位 cout
3. **溢出检测**: 检测有符号数溢出（当两个同号数相加结果变号时）
4. **全组合覆盖**: 支持所有可能的16位输入组合
5. **边界处理**: 正确处理最大值(0xFFFF)和最小值(0x0000)
        """
        
        print("🚀 开始TDD多轮对话测试...")
        print(f"   任务: {task_description[:100]}...")
        print(f"   配置: 持续对话模式已启用")
        
        # 执行TDD任务
        result = await self.coordinator.execute_test_driven_task(
            task_description=task_description,
            testbench_path=None  # 让AI生成测试台
        )
        
        print(f"\n📊 TDD多轮对话结果:")
        print(f"   成功: {'是' if result.get('success') else '否'}")
        print(f"   迭代次数: {result.get('total_iterations', 0)}")
        print(f"   完成原因: {result.get('completion_reason', 'unknown')}")
        
        # 分析对话历史
        conversation_history = result.get('conversation_history', [])
        print(f"   对话历史长度: {len(conversation_history)} 轮")
        
        if conversation_history:
            print(f"   🔍 对话历史分析:")
            user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
            assistant_messages = [msg for msg in conversation_history if msg.get('role') == 'assistant']
            print(f"      - 用户消息: {len(user_messages)} 轮")
            print(f"      - AI响应: {len(assistant_messages)} 轮")
            
            # 检查是否有迭代标记
            iterations = set()
            for msg in conversation_history:
                if 'iteration' in msg:
                    iterations.add(msg['iteration'])
            print(f"      - 涉及迭代: {sorted(iterations)}")
        
        return result
    
    async def test_conversation_memory(self):
        """测试对话记忆功能"""
        print("\n" + "="*60)
        print("🧪 测试3: 对话记忆功能")
        print("="*60)
        
        # 第一轮：设计一个模块
        print("🔄 第一轮: 设计模块")
        task1 = "设计一个4位计数器模块，包含时钟、复位和计数输出。"
        
        result1 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task1,
            max_iterations=2
        )
        
        history1 = result1.get('conversation_history', [])
        print(f"   第一轮对话轮数: {len(history1)}")
        
        # 第二轮：询问之前的设计
        print("\n🔄 第二轮: 询问之前的设计")
        task2 = "请告诉我你刚才设计的4位计数器模块的名称和主要功能。"
        
        result2 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task2,
            max_iterations=2,
            conversation_history=history1  # 传递第一轮历史
        )
        
        history2 = result2.get('conversation_history', [])
        print(f"   第二轮对话轮数: {len(history2)}")
        
        # 第三轮：要求修改
        print("\n🔄 第三轮: 要求修改")
        task3 = "请修改之前的4位计数器，添加一个使能信号。"
        
        result3 = await self.verilog_agent.process_with_enhanced_validation(
            user_request=task3,
            max_iterations=2,
            conversation_history=history2  # 传递完整历史
        )
        
        history3 = result3.get('conversation_history', [])
        print(f"   第三轮对话轮数: {len(history3)}")
        
        # 分析记忆效果
        print(f"\n🧠 对话记忆分析:")
        print(f"   总对话轮数: {len(history3)}")
        print(f"   历史连续性: {'✅ 正常' if len(history3) >= 6 else '❌ 异常'}")
        
        # 检查AI是否记得之前的设计
        final_response = result3.get('response', '')
        if '4位计数器' in final_response or 'counter' in final_response.lower():
            print(f"   记忆效果: ✅ AI记得之前的设计")
        else:
            print(f"   记忆效果: ❌ AI可能忘记了之前的设计")
        
        return result1, result2, result3
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始多轮对话功能测试套件")
        print("="*80)
        
        test_results = {}
        
        try:
            # 测试1: 基本多轮对话
            test_results['basic'] = await self.test_basic_multiround_conversation()
            
            # 测试2: TDD多轮对话
            test_results['tdd'] = await self.test_tdd_multiround_conversation()
            
            # 测试3: 对话记忆
            test_results['memory'] = await self.test_conversation_memory()
            
            # 总结
            print("\n" + "="*80)
            print("📊 多轮对话功能测试总结")
            print("="*80)
            
            success_count = 0
            total_tests = 0
            
            for test_name, result in test_results.items():
                if isinstance(result, tuple):
                    # 多结果测试
                    test_success = all(r.get('success', False) for r in result)
                    total_tests += 1
                    if test_success:
                        success_count += 1
                    print(f"   {test_name}: {'✅ 通过' if test_success else '❌ 失败'}")
                else:
                    # 单结果测试
                    test_success = result.get('success', False)
                    total_tests += 1
                    if test_success:
                        success_count += 1
                    print(f"   {test_name}: {'✅ 通过' if test_success else '❌ 失败'}")
            
            print(f"\n🎯 总体结果: {success_count}/{total_tests} 测试通过")
            
            if success_count == total_tests:
                print("🎉 所有多轮对话功能测试通过！")
                print("✅ 智能体能够正确记住对话历史")
                print("✅ 多轮对话机制工作正常")
                print("✅ 上下文传递功能正常")
            else:
                print("⚠️ 部分测试失败，需要进一步调试")
            
            return success_count == total_tests
            
        except Exception as e:
            print(f"❌ 测试执行异常: {str(e)}")
            return False


async def main():
    """主函数"""
    print("🧪 多轮对话功能测试")
    print("="*50)
    
    test = MultiRoundConversationTest()
    success = await test.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 