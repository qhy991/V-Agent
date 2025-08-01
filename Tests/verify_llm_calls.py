#!/usr/bin/env python3
"""
验证测试agent是否调用真实LLM
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient


async def verify_llm_connection():
    """验证LLM连接"""
    print("🔍 验证LLM连接...")
    
    try:
        config = FrameworkConfig.from_env()
        llm_client = EnhancedLLMClient(config.llm)
        
        print(f"📊 LLM配置:")
        print(f"   提供商: {config.llm.provider}")
        print(f"   模型: {config.llm.model}")
        print(f"   API端点: {config.llm.api_base_url}")
        
        # 发送简单测试提示
        test_prompt = "请回复'LLM连接成功'并说明你的模型名称"
        
        print(f"\n🚀 发送测试请求...")
        response = await llm_client.send_prompt(
            prompt=test_prompt,
            system_prompt="你是一个测试助手，用于验证LLM连接"
        )
        
        print(f"✅ LLM响应:")
        print(f"   {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM连接失败: {e}")
        return False


async def verify_agent_llm_usage():
    """验证智能体使用LLM"""
    print("\n🤖 验证智能体LLM使用...")
    
    try:
        from agents.real_code_reviewer import RealCodeReviewAgent
        
        config = FrameworkConfig.from_env()
        agent = RealCodeReviewAgent(config)
        
        # 创建一个简单的代码审查请求
        test_code = """
        module test(input clk, output reg [7:0] count);
        always @(posedge clk) count <= count + 1;
        endmodule
        """
        
        print(f"📋 测试代码:")
        print(f"   {test_code.strip()}")
        
        # 直接调用LLM进行代码分析
        response = await agent._call_llm_for_function_calling([
            {"role": "user", "content": f"请分析这段Verilog代码: {test_code}"}
        ])
        
        print(f"\n✅ 智能体LLM响应:")
        print(f"   响应长度: {len(response)} 字符")
        print(f"   包含'module': {'module' in response}")
        print(f"   包含'analysis': {'analysis' in response.lower()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能体LLM使用失败: {e}")
        return False


async def main():
    """主验证程序"""
    print("🎯 LLM调用验证程序")
    print("=" * 40)
    
    # 验证1: 直接LLM连接
    llm_ok = await verify_llm_connection()
    
    # 验证2: 智能体LLM使用
    agent_ok = await verify_agent_llm_usage()
    
    print("\n" + "=" * 40)
    print("📊 验证结果:")
    print(f"   直接LLM连接: {'✅ 成功' if llm_ok else '❌ 失败'}")
    print(f"   智能体LLM使用: {'✅ 成功' if agent_ok else '❌ 失败'}")
    
    if llm_ok and agent_ok:
        print("\n🎉 确认：测试agent确实调用真实LLM！")
    else:
        print("\n⚠️  检查LLM配置或网络连接")


if __name__ == "__main__":
    asyncio.run(main())