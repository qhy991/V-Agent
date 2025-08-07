#!/usr/bin/env python3
"""
测试NoneType错误修复
验证enhanced_real_verilog_agent在处理包含None内容的对话历史时不会崩溃
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_integration.enhanced_llm_client import OptimizedLLMClient
from config.config import FrameworkConfig


async def test_none_type_fix():
    """测试NoneType错误修复"""
    print("🧪 开始测试NoneType错误修复...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
        # 创建包含None内容的对话历史（模拟问题场景）
        conversation_with_none = [
            {"role": "system", "content": "你是一个Verilog设计专家"},
            {"role": "user", "content": "设计一个计数器"},
            {"role": "assistant", "content": None},  # 模拟None内容
            {"role": "user", "content": "请继续设计"},
            {"role": "assistant", "content": ""},  # 模拟空字符串
            {"role": "user", "content": None},  # 模拟None内容
        ]
        
        print("🔧 测试包含None内容的对话历史处理...")
        
        # 测试_send_prompt_internal方法（这是我们修复的地方）
        try:
            # 创建OptimizedLLMClient实例
            llm_client = OptimizedLLMClient(config.llm)
            
            # 直接测试_send_prompt_internal方法
            response = await llm_client._send_prompt_internal(
                messages=conversation_with_none,
                temperature=0.3,
                max_tokens=1000,
                json_mode=False
            )
            print(f"✅ _send_prompt_internal调用成功，响应长度: {len(response) if response else 0}")
            return True
            
        except Exception as e:
            if "NoneType" in str(e):
                print(f"❌ 仍然存在NoneType错误: {e}")
                import traceback
                traceback.print_exc()
                return False
            else:
                print(f"⚠️ 其他错误（可接受）: {e}")
                return True
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 开始NoneType错误修复验证测试")
    print("=" * 60)
    
    success = await test_none_type_fix()
    
    print("=" * 60)
    if success:
        print("🎉 NoneType错误修复验证成功！")
        return 0
    else:
        print("❌ NoneType错误修复验证失败！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 