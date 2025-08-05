#!/usr/bin/env python3
"""
优化LLM调用机制演示脚本

演示智能System Prompt缓存和上下文优化功能
"""

import asyncio
import time
import logging
from typing import Dict, Any, List
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_integration.enhanced_llm_client import EnhancedLLMClient, OptimizedLLMClient
from config.config import LLMConfig
from core.base_agent import BaseAgent
from core.schema_system.enhanced_base_agent import EnhancedBaseAgent


class DemoAgent(BaseAgent):
    """演示用的智能体"""
    
    def __init__(self):
        super().__init__("demo_agent", "演示智能体", set())
        self.system_prompt = """你是一个专业的演示助手，专门用于展示LLM调用优化功能。

你的主要职责：
1. 回答用户问题
2. 展示优化效果
3. 提供技术建议

请保持专业、友好的态度，并尽可能详细地回答问题。"""


class EnhancedDemoAgent(EnhancedBaseAgent):
    """增强演示智能体"""
    
    def __init__(self):
        super().__init__("enhanced_demo_agent", "增强演示智能体", set())
        self._register_enhanced_tools()
    
    def _register_enhanced_tools(self):
        """注册增强工具"""
        self.register_enhanced_tool(
            name="get_optimization_stats",
            func=self._tool_get_optimization_stats,
            description="获取优化统计信息",
            schema={
                "type": "object",
                "properties": {
                    "include_details": {
                        "type": "boolean",
                        "description": "是否包含详细信息",
                        "default": True
                    }
                },
                "required": []
            }
        )
    
    async def _tool_get_optimization_stats(self, include_details: bool = True) -> Dict[str, Any]:
        """获取优化统计信息工具"""
        stats = self.get_enhanced_optimization_stats()
        if not include_details:
            # 只返回关键指标
            return {
                "cache_hit_rate": stats.get("cache_hit_rate", 0),
                "total_requests": stats.get("total_requests", 0),
                "average_time": stats.get("average_time", 0),
                "token_savings": stats.get("token_savings", 0)
            }
        return stats
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """实现LLM调用"""
        # 使用优化的LLM调用
        user_message = conversation[-1]["content"] if conversation else ""
        is_first_call = len(conversation) <= 2  # 只有system和user消息时是第一次调用
        
        return await self._call_llm_optimized_with_history(user_message, conversation[:-1], is_first_call)


async def demo_basic_optimization():
    """演示基础优化功能"""
    print("🚀 开始基础优化演示")
    print("=" * 60)
    
    # 创建LLM配置
    config = LLMConfig(
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_key="your-api-key",  # 请替换为实际的API密钥
        api_base_url="https://api.openai.com/v1",
        temperature=0.3,
        max_tokens=4000,
        timeout=30,
        retry_attempts=3,
        retry_delay=1.0
    )
    
    # 创建优化的LLM客户端
    llm_client = EnhancedLLMClient(config)
    
    # 演示对话
    conversation_id = "demo_conversation_001"
    system_prompt = "你是一个专业的助手，请简洁地回答用户问题。"
    
    questions = [
        "你好，请介绍一下自己。",
        "什么是人工智能？",
        "请解释一下机器学习的基本概念。",
        "深度学习与传统机器学习有什么区别？",
        "请推荐一些学习AI的资源。"
    ]
    
    print("📝 开始多轮对话演示...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n🔄 第 {i} 轮对话:")
        print(f"👤 用户: {question}")
        
        start_time = time.time()
        
        # 使用优化的LLM调用
        response = await llm_client.send_prompt_optimized(
            conversation_id=conversation_id,
            user_message=question,
            system_prompt=system_prompt if i == 1 else None,  # 只在第一轮传递system prompt
            temperature=0.3,
            max_tokens=1000
        )
        
        duration = time.time() - start_time
        
        print(f"🤖 助手: {response[:200]}...")
        print(f"⏱️ 耗时: {duration:.2f}秒")
    
    # 获取优化统计
    stats = llm_client.get_optimization_stats()
    print(f"\n📊 优化统计:")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.1%}")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  平均响应时间: {stats['average_time']:.2f}秒")
    print(f"  上下文优化次数: {stats['context_optimizations']}")
    
    await llm_client.close()


async def demo_agent_optimization():
    """演示智能体优化功能"""
    print("\n🚀 开始智能体优化演示")
    print("=" * 60)
    
    # 创建演示智能体
    agent = DemoAgent()
    
    # 模拟LLM客户端（实际使用时需要真实的LLM配置）
    print("📝 演示智能体优化功能...")
    
    # 演示多轮对话
    conversation_id = "agent_demo_001"
    
    requests = [
        "请介绍一下你的功能。",
        "你能帮我做什么？",
        "请解释一下LLM优化的原理。",
        "优化后的性能提升如何？",
        "有什么使用建议吗？"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n🔄 第 {i} 轮请求:")
        print(f"👤 用户: {request}")
        
        start_time = time.time()
        
        # 使用优化的Function Calling
        result = await agent.process_with_optimized_function_calling(
            user_request=request,
            conversation_id=conversation_id,
            max_iterations=3,
            enable_self_continuation=False
        )
        
        duration = time.time() - start_time
        
        print(f"🤖 智能体: {result[:200]}...")
        print(f"⏱️ 耗时: {duration:.2f}秒")
    
    # 获取优化统计
    stats = agent.get_llm_optimization_stats()
    print(f"\n📊 智能体优化统计:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")


async def demo_enhanced_agent_optimization():
    """演示增强智能体优化功能"""
    print("\n🚀 开始增强智能体优化演示")
    print("=" * 60)
    
    # 创建增强演示智能体
    agent = EnhancedDemoAgent()
    
    print("📝 演示增强智能体优化功能...")
    
    # 演示工具调用
    conversation_id = "enhanced_agent_demo_001"
    
    requests = [
        "请获取优化统计信息。",
        "请获取详细的优化统计信息。",
        "请分析当前的性能表现。",
        "请提供优化建议。"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n🔄 第 {i} 轮请求:")
        print(f"👤 用户: {request}")
        
        start_time = time.time()
        
        # 使用增强验证处理
        result = await agent.process_with_enhanced_validation(
            user_request=request,
            max_iterations=3
        )
        
        duration = time.time() - start_time
        
        if result["success"]:
            print(f"🤖 智能体: {result['response'][:200]}...")
        else:
            print(f"❌ 错误: {result['error']}")
        
        print(f"⏱️ 耗时: {duration:.2f}秒")
        print(f"🔄 迭代次数: {result['iterations']}")
    
    # 获取增强优化统计
    stats = agent.get_enhanced_optimization_stats()
    print(f"\n📊 增强智能体优化统计:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")


async def demo_performance_comparison():
    """演示性能对比"""
    print("\n🚀 开始性能对比演示")
    print("=" * 60)
    
    # 创建配置
    config = LLMConfig(
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_key="your-api-key",  # 请替换为实际的API密钥
        api_base_url="https://api.openai.com/v1",
        temperature=0.3,
        max_tokens=4000,
        timeout=30,
        retry_attempts=3,
        retry_delay=1.0
    )
    
    # 创建两个客户端进行对比
    standard_client = EnhancedLLMClient(config)
    optimized_client = EnhancedLLMClient(config)
    
    system_prompt = "你是一个专业的助手，请简洁地回答用户问题。"
    test_questions = [
        "什么是人工智能？",
        "请解释机器学习。",
        "深度学习有什么特点？",
        "请推荐学习资源。"
    ]
    
    print("📊 性能对比测试...")
    
    # 标准方式测试
    print("\n🔴 标准方式测试:")
    standard_times = []
    standard_tokens = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"  第 {i} 轮...")
        start_time = time.time()
        
        response = await standard_client.send_prompt(
            prompt=question,
            system_prompt=system_prompt,  # 每次都传递system prompt
            temperature=0.3,
            max_tokens=1000
        )
        
        duration = time.time() - start_time
        standard_times.append(duration)
        standard_tokens += len(question) + len(response)
        
        print(f"    耗时: {duration:.2f}秒")
    
    # 优化方式测试
    print("\n🟢 优化方式测试:")
    optimized_times = []
    optimized_tokens = 0
    conversation_id = "performance_test_001"
    
    for i, question in enumerate(test_questions, 1):
        print(f"  第 {i} 轮...")
        start_time = time.time()
        
        response = await optimized_client.send_prompt_optimized(
            conversation_id=conversation_id,
            user_message=question,
            system_prompt=system_prompt if i == 1 else None,  # 只在第一轮传递
            temperature=0.3,
            max_tokens=1000
        )
        
        duration = time.time() - start_time
        optimized_times.append(duration)
        optimized_tokens += len(question) + len(response)
        
        print(f"    耗时: {duration:.2f}秒")
    
    # 计算性能提升
    avg_standard_time = sum(standard_times) / len(standard_times)
    avg_optimized_time = sum(optimized_times) / len(optimized_times)
    
    time_improvement = ((avg_standard_time - avg_optimized_time) / avg_standard_time) * 100
    token_savings = ((standard_tokens - optimized_tokens) / standard_tokens) * 100
    
    print(f"\n📈 性能对比结果:")
    print(f"  标准方式平均耗时: {avg_standard_time:.2f}秒")
    print(f"  优化方式平均耗时: {avg_optimized_time:.2f}秒")
    print(f"  时间提升: {time_improvement:.1f}%")
    print(f"  Token节省: {token_savings:.1f}%")
    
    # 获取优化统计
    opt_stats = optimized_client.get_optimization_stats()
    print(f"  缓存命中率: {opt_stats['cache_hit_rate']:.1%}")
    print(f"  上下文优化次数: {opt_stats['context_optimizations']}")
    
    await standard_client.close()
    await optimized_client.close()


async def main():
    """主函数"""
    print("🎯 LLM调用优化机制演示")
    print("=" * 80)
    
    try:
        # 演示基础优化功能
        await demo_basic_optimization()
        
        # 演示智能体优化功能
        await demo_agent_optimization()
        
        # 演示增强智能体优化功能
        await demo_enhanced_agent_optimization()
        
        # 演示性能对比
        await demo_performance_comparison()
        
        print("\n✅ 所有演示完成！")
        print("\n📋 优化功能总结:")
        print("  🚀 智能System Prompt缓存")
        print("  🗜️ 上下文压缩优化")
        print("  📊 详细的性能统计")
        print("  🔄 自动缓存管理")
        print("  💰 Token使用优化")
        print("  ⚡ 响应速度提升")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
        logging.exception("演示错误详情")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(main()) 