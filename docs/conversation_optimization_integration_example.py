#!/usr/bin/env python3
"""
对话显示优化集成示例
演示如何在现有代码中集成对话显示优化功能
"""

import asyncio
from core.conversation_display_optimizer import conversation_optimizer, optimize_agent_output
from core.conversation_config import get_conversation_config


class OptimizedAgentExample:
    """集成了对话显示优化的智能体示例"""
    
    def __init__(self, agent_id: str = "example_agent"):
        self.agent_id = agent_id
        self.conversation_config = get_conversation_config()
        self.iteration_count = 0
    
    async def process_with_optimized_display(self, user_request: str) -> str:
        """使用优化显示的处理方法"""
        self.iteration_count += 1
        
        # 模拟AI响应（这里会是实际的LLM调用）
        ai_response = f"这是针对'{user_request}'的AI响应。" * 20  # 模拟长响应
        
        # 应用显示优化
        if self.conversation_config.should_optimize_display():
            # 使用优化显示
            optimized_display = optimize_agent_output(
                agent_id=self.agent_id,
                user_request=user_request,
                ai_response=ai_response,
                iteration_count=self.iteration_count
            )
            print(optimized_display)
        else:
            # 使用原始显示（会很长）
            print(f"\n原始响应（第{self.iteration_count}轮）:")
            print(f"用户: {user_request}")
            print(f"AI: {ai_response}")
            print("-" * 100)
        
        return ai_response
    
    def demonstrate_history_optimization(self, conversation_history: list) -> list:
        """演示对话历史优化"""
        print(f"\n📊 对话历史优化演示:")
        print(f"原始历史长度: {len(conversation_history)} 条消息")
        
        # 应用历史优化
        optimized_history = conversation_optimizer.optimize_conversation_history(
            conversation_history=conversation_history,
            keep_last_n_turns=self.conversation_config.max_history_turns
        )
        
        print(f"优化后历史长度: {len(optimized_history)} 条消息")
        
        # 创建对话摘要
        summary = conversation_optimizer.create_conversation_summary(conversation_history)
        print(f"\n对话摘要:\n{summary}")
        
        return optimized_history


async def main():
    """主演示函数"""
    print("🚀 对话显示优化集成演示")
    print("=" * 60)
    
    # 创建优化智能体实例
    agent = OptimizedAgentExample("demo_agent")
    
    # 演示1: 优化显示
    print("\n📋 演示1: 对话显示优化")
    await agent.process_with_optimized_display("设计一个计数器模块")
    await agent.process_with_optimized_display("添加测试台")
    await agent.process_with_optimized_display("修复编译错误")
    
    # 演示2: 对话历史优化
    print("\n📋 演示2: 对话历史优化")
    sample_history = [
        {"role": "system", "content": "你是一个Verilog设计助手"},
        {"role": "user", "content": "设计ALU"},
        {"role": "assistant", "content": "我将为您设计一个ALU模块..."},
        {"role": "user", "content": "添加加法功能"},
        {"role": "assistant", "content": "我将添加加法功能..."},
        {"role": "user", "content": "添加减法功能"},
        {"role": "assistant", "content": "我将添加减法功能..."},
        {"role": "user", "content": "生成测试台"},
        {"role": "assistant", "content": "我将生成测试台..."},
        {"role": "user", "content": "修复错误"},
        {"role": "assistant", "content": "我将修复错误..."}
    ]
    
    agent.demonstrate_history_optimization(sample_history)
    
    # 演示3: 配置控制
    print("\n📋 演示3: 配置控制")
    config = get_conversation_config()
    print(f"当前配置:")
    print(f"- 显示优化: {config.enable_display_optimization}")
    print(f"- 最大显示轮数: {config.max_display_rounds}")
    print(f"- 紧凑模式: {config.enable_compact_mode}")
    print(f"- 最大历史轮数: {config.max_history_turns}")
    print(f"- 为Ollama优化: {config.optimize_for_ollama}")


class IntegrationGuide:
    """集成指南类"""
    
    @staticmethod
    def show_integration_steps():
        """显示集成步骤"""
        print("\n🔧 对话显示优化集成指南")
        print("=" * 60)
        
        steps = [
            "1. 导入必要模块:",
            "   from core.conversation_display_optimizer import optimize_agent_output",
            "   from core.conversation_config import get_conversation_config",
            "",
            "2. 在智能体类中添加配置:",
            "   self.conversation_config = get_conversation_config()",
            "",
            "3. 在输出响应时应用优化:",
            "   if self.conversation_config.should_optimize_display():",
            "       optimized_display = optimize_agent_output(",
            "           agent_id=self.agent_id,",
            "           user_request=user_request,",
            "           ai_response=ai_response,",
            "           iteration_count=iteration_count",
            "       )",
            "       print(optimized_display)",
            "",
            "4. 对话历史优化（可选）:",
            "   from core.conversation_display_optimizer import conversation_optimizer",
            "   optimized_history = conversation_optimizer.optimize_conversation_history(",
            "       conversation_history=full_history,",
            "       keep_last_n_turns=3",
            "   )",
            "",
            "5. 环境变量控制（可选）:",
            "   export CONVERSATION_DISPLAY_OPTIMIZATION=true",
            "   export CONVERSATION_MAX_DISPLAY_ROUNDS=1",
            "   export CONVERSATION_COMPACT_MODE=true",
            "   export CONVERSATION_MAX_RESPONSE_LENGTH=500"
        ]
        
        for step in steps:
            print(step)
    
    @staticmethod 
    def show_specific_fixes():
        """显示针对特定问题的修复方案"""
        print("\n🎯 针对执行结果问题的具体修复")
        print("=" * 60)
        
        fixes = [
            "问题: 每次迭代都显示完整对话历史，导致输出越来越长",
            "",
            "解决方案1 - 在test_llm_coordinator_enhanced.py中应用:",
            "```python",
            "# 在显示结果时使用优化",
            "from core.conversation_display_optimizer import optimize_agent_output",
            "",
            "# 替换原来的长输出",
            "optimized_output = optimize_agent_output(",
            "    agent_id='coordinator',",
            "    user_request=requirements,",
            "    ai_response=result.get('coordination_result', ''),",
            "    iteration_count=analysis.get('total_iterations', 1)",
            ")",
            "print(optimized_output)",
            "```",
            "",
            "解决方案2 - 在enhanced_base_agent.py中集成:",
            "```python",
            "# 在process_with_function_calling方法的最后",
            "if hasattr(self, 'conversation_config') and self.conversation_config.should_optimize_display():",
            "    return optimize_agent_output(",
            "        agent_id=self.agent_id,",
            "        user_request=user_request,",
            "        ai_response=final_response,",
            "        iteration_count=iteration_count",
            "    )",
            "```",
            "",
            "解决方案3 - 环境变量控制（立即生效）:",
            "```bash",
            "export CONVERSATION_DISPLAY_OPTIMIZATION=true",
            "export CONVERSATION_MAX_RESPONSE_LENGTH=200",
            "export CONVERSATION_COMPACT_MODE=true",
            "```"
        ]
        
        for fix in fixes:
            print(fix)


if __name__ == "__main__":
    # 显示集成指南
    IntegrationGuide.show_integration_steps()
    IntegrationGuide.show_specific_fixes()
    
    print("\n" + "=" * 60)
    
    # 运行演示
    asyncio.run(main())