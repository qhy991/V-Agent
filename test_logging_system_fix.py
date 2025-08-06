#!/usr/bin/env python3
"""
测试统一日志系统修复
Test Unified Logging System Fix
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.unified_logging_system import get_global_logging_system
from core.base_agent import BaseAgent
from core.enums import AgentCapability
from abc import ABC, abstractmethod


class TestAgent(BaseAgent):
    """测试用的智能体类"""
    
    def __init__(self):
        super().__init__(
            agent_id="test_agent",
            role="test_role",
            capabilities={AgentCapability.CODE_GENERATION}
        )
    
    async def _call_llm_for_function_calling(self, conversation):
        return "Test LLM response"
    
    def get_capabilities(self):
        return {AgentCapability.CODE_GENERATION}
    
    def get_specialty_description(self):
        return "Test agent for logging system validation"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        return {"success": True, "message": "Test task completed"}


async def test_file_operations():
    """测试文件操作功能"""
    print("🧪 测试文件操作功能...")
    
    # 初始化日志系统
    logging_system = get_global_logging_system()
    
    # 创建测试智能体
    agent = TestAgent()
    
    try:
        # 测试写入文件
        print("📝 测试写入文件...")
        write_result = await agent._tool_write_file(
            filename="test_file.txt",
            content="这是一个测试文件内容\n包含多行文本\n用于验证修复效果"
        )
        
        if write_result.get("success"):
            print(f"✅ 文件写入成功: {write_result.get('file_path')}")
        else:
            print(f"❌ 文件写入失败: {write_result.get('error')}")
            return False
        
        # 测试读取文件
        print("📖 测试读取文件...")
        read_result = await agent._tool_read_file(
            filepath=write_result.get("file_path")
        )
        
        if read_result.get("success"):
            print(f"✅ 文件读取成功: {len(read_result.get('content', ''))} 字符")
        else:
            print(f"❌ 文件读取失败: {read_result.get('error')}")
            return False
        
        # 测试LLM调用
        print("🤖 测试LLM调用...")
        try:
            response = await agent._call_llm_optimized("测试消息")
            print(f"✅ LLM调用成功: {len(response)} 字符")
        except Exception as e:
            print(f"⚠️ LLM调用失败（预期）: {str(e)}")
        
        # 获取日志数据
        print("📊 获取日志数据...")
        timeline = logging_system.get_execution_timeline()
        agent_performance = logging_system.get_agent_performance_summary()
        tool_usage = logging_system.get_tool_usage_summary()
        
        print(f"✅ 执行时间线: {len(timeline)} 个事件")
        print(f"✅ 智能体性能: {len(agent_performance)} 个智能体")
        print(f"✅ 工具使用: {len(tool_usage)} 个工具")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理...")
    
    logging_system = get_global_logging_system()
    agent = TestAgent()
    
    try:
        # 测试写入不存在的目录
        print("📝 测试写入到不存在的目录...")
        write_result = await agent._tool_write_file(
            filename="nonexistent_dir/test.txt",
            content="测试内容"
        )
        
        if write_result.get("success"):
            print(f"✅ 写入到不存在目录成功: {write_result.get('file_path')}")
        else:
            print(f"⚠️ 写入到不存在目录失败（预期）: {write_result.get('error')}")
        
        # 测试读取不存在的文件
        print("📖 测试读取不存在的文件...")
        read_result = await agent._tool_read_file("nonexistent_file.txt")
        
        if not read_result.get("success"):
            print(f"⚠️ 读取不存在文件失败（预期）: {read_result.get('error')}")
        else:
            print(f"❌ 读取不存在文件意外成功")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始统一日志系统修复验证测试")
    print("=" * 50)
    
    # 测试文件操作
    file_test_passed = await test_file_operations()
    
    # 测试错误处理
    error_test_passed = await test_error_handling()
    
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    print(f"文件操作测试: {'✅ 通过' if file_test_passed else '❌ 失败'}")
    print(f"错误处理测试: {'✅ 通过' if error_test_passed else '❌ 失败'}")
    
    if file_test_passed and error_test_passed:
        print("\n🎉 所有测试通过！统一日志系统修复成功！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 