#!/usr/bin/env python3
"""
测试LLM优化机制修复
验证system prompt是否只在第一次调用时传入
"""

import asyncio
import time
from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def test_llm_optimization():
    """测试LLM优化机制"""
    print("🧪 测试LLM优化机制修复")
    print("=" * 60)
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    print("🤖 创建LLM协调智能体...")
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建其他智能体
    print("🤖 创建Verilog设计智能体...")
    verilog_agent = EnhancedRealVerilogAgent(config)
    
    print("🤖 创建代码审查智能体...")
    code_review_agent = EnhancedRealCodeReviewAgent(config)
    
    # 注册智能体
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(code_review_agent)
    
    print("✅ 智能体创建和注册完成")
    print()
    
    # 测试任务
    test_request = """
请设计一个名为 counter 的Verilog模块。

**基本要求**：
1. 生成完整、可编译的Verilog代码
2. 包含适当的端口定义和功能实现
3. 符合Verilog标准语法
4. 生成对应的测试台进行验证

**质量要求**：
- 代码结构清晰，注释完善
- 遵循良好的命名规范
- 确保功能正确性
"""
    
    print("🚀 开始执行测试任务...")
    print(f"📋 任务: {test_request.strip()}")
    print()
    
    # 执行协调任务
    start_time = time.time()
    result = await coordinator.coordinate_task(
        user_request=test_request,
        max_iterations=3
    )
    end_time = time.time()
    
    print()
    print("📊 执行结果:")
    print(f"⏱️  总执行时间: {end_time - start_time:.2f}秒")
    print(f"✅ 任务状态: {result.get('status', 'unknown')}")
    
    # 获取优化统计信息
    print()
    print("📈 LLM优化统计信息:")
    
    # 协调智能体统计
    coordinator_stats = coordinator.get_enhanced_optimization_stats()
    print(f"🤖 协调智能体:")
    print(f"   - 缓存命中率: {coordinator_stats.get('cache_hit_rate', 0):.1%}")
    print(f"   - 总请求数: {coordinator_stats.get('total_requests', 0)}")
    print(f"   - 缓存命中: {coordinator_stats.get('cache_hits', 0)}")
    print(f"   - 缓存未命中: {coordinator_stats.get('cache_misses', 0)}")
    
    # Verilog智能体统计
    verilog_stats = verilog_agent.get_enhanced_optimization_stats()
    print(f"🔧 Verilog智能体:")
    print(f"   - 缓存命中率: {verilog_stats.get('cache_hit_rate', 0):.1%}")
    print(f"   - 总请求数: {verilog_stats.get('total_requests', 0)}")
    print(f"   - 缓存命中: {verilog_stats.get('cache_hits', 0)}")
    print(f"   - 缓存未命中: {verilog_stats.get('cache_misses', 0)}")
    
    # 代码审查智能体统计
    code_review_stats = code_review_agent.get_enhanced_optimization_stats()
    print(f"🔍 代码审查智能体:")
    print(f"   - 缓存命中率: {code_review_stats.get('cache_hit_rate', 0):.1%}")
    print(f"   - 总请求数: {code_review_stats.get('total_requests', 0)}")
    print(f"   - 缓存命中: {code_review_stats.get('cache_hits', 0)}")
    print(f"   - 缓存未命中: {code_review_stats.get('cache_misses', 0)}")
    
    print()
    print("🎯 优化效果分析:")
    
    total_requests = (coordinator_stats.get('total_requests', 0) + 
                     verilog_stats.get('total_requests', 0) + 
                     code_review_stats.get('total_requests', 0))
    
    total_cache_hits = (coordinator_stats.get('cache_hits', 0) + 
                       verilog_stats.get('cache_hits', 0) + 
                       code_review_stats.get('cache_hits', 0))
    
    if total_requests > 0:
        overall_hit_rate = total_cache_hits / total_requests
        print(f"📊 总体缓存命中率: {overall_hit_rate:.1%}")
        
        if overall_hit_rate > 0.5:
            print("✅ 优化机制工作正常！System prompt缓存有效")
        else:
            print("⚠️  优化效果不明显，可能需要进一步调试")
    else:
        print("❌ 没有检测到LLM请求")
    
    print()
    print("🏁 测试完成")


if __name__ == "__main__":
    asyncio.run(test_llm_optimization()) 