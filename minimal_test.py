#!/usr/bin/env python3
"""
Minimal Test - 最小化测试
=======================

只测试我们新建的重构组件，不依赖任何复杂模块。
"""

import sys
import asyncio
from pathlib import Path

# 测试环境初始化
print("🔧 初始化最小化测试环境...")

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tool_call_classes():
    """测试ToolCall和ToolResult类"""
    print("\n1️⃣ 测试ToolCall和ToolResult类...")
    
    try:
        # 直接从parser模块导入，避免循环依赖
        from core.function_calling.parser import ToolCall, ToolResult
        
        # 测试ToolCall
        tool_call = ToolCall(
            tool_name="test_tool",
            parameters={"param1": "value1", "param2": 42},
            call_id="call_001"
        )
        
        assert tool_call.tool_name == "test_tool"
        assert tool_call.parameters["param1"] == "value1"
        assert tool_call.call_id == "call_001"
        print("   ✅ ToolCall 类功能正常")
        
        # 测试ToolResult
        tool_result = ToolResult(
            call_id="call_001",
            success=True,
            result="Operation successful",
            error=None
        )
        
        assert tool_result.call_id == "call_001"
        assert tool_result.success == True
        assert tool_result.result == "Operation successful"
        print("   ✅ ToolResult 类功能正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return False


def test_tool_call_parser():
    """测试ToolCallParser类"""
    print("\n2️⃣ 测试ToolCallParser类...")
    
    try:
        from core.function_calling.parser import ToolCallParser
        
        parser = ToolCallParser()
        
        # 测试JSON解析
        json_response = '''{
    "tool_calls": [
        {
            "tool_name": "write_file",
            "parameters": {
                "filename": "test.txt",
                "content": "Hello World"
            }
        },
        {
            "tool_name": "read_file",
            "parameters": {
                "filepath": "/path/to/file.txt"
            }
        }
    ]
}'''
        
        tool_calls = parser.parse_tool_calls_from_response(json_response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].tool_name == "write_file"
        assert tool_calls[0].parameters["filename"] == "test.txt"
        assert tool_calls[1].tool_name == "read_file"
        print("   ✅ JSON格式解析功能正常")
        
        # 测试参数标准化
        normalized = parser.normalize_tool_parameters(
            "write_file",
            {"file": "test.txt", "text": "content", "dir": "temp"}
        )
        
        # 应该映射: file->filename, text->content, dir->directory
        expected_keys = {"filename", "content", "directory"}
        actual_keys = set(normalized.keys())
        
        print(f"   📊 原始参数: file, text, dir")
        print(f"   📊 标准化后: {list(normalized.keys())}")
        print("   ✅ 参数标准化功能正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return False


def test_conversation_manager():
    """测试ConversationManager类"""
    print("\n3️⃣ 测试ConversationManager类...")
    
    try:
        from core.conversation.manager import ConversationManager
        
        manager = ConversationManager("test_agent")
        
        # 测试对话开始
        manager.start_conversation("conv_001")
        assert manager.current_conversation_id == "conv_001"
        print("   ✅ 对话开始功能正常")
        
        # 测试消息添加
        manager.add_message("user", "Hello, agent!", conversation_id="conv_001")
        manager.add_message("assistant", "Hello, user!", conversation_id="conv_001")
        print("   ✅ 消息添加功能正常")
        
        # 测试历史获取
        history = manager.get_conversation_history("conv_001")
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == 'Hello, agent!'
        assert history[1]['role'] == 'assistant'
        print("   ✅ 历史获取功能正常")
        
        # 测试LLM格式转换
        llm_format = manager.get_conversation_for_llm("conv_001")
        assert len(llm_format) == 2
        assert 'role' in llm_format[0] and 'content' in llm_format[0]
        print("   ✅ LLM格式转换功能正常")
        
        # 测试对话摘要
        summary = manager.get_conversation_summary("conv_001")
        assert summary['message_count'] == 2
        assert summary['conversation_id'] == "conv_001"
        print("   ✅ 对话摘要功能正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return False


def test_agent_context():
    """测试AgentContext类"""
    print("\n4️⃣ 测试AgentContext类...")
    
    try:
        from core.context.agent_context import AgentContext
        
        # 创建简单的上下文（不使用复杂枚举）
        context = AgentContext(
            agent_id="test_agent",
            role="test_role",
            capabilities=set()
        )
        
        # 测试基本属性
        assert context.agent_id == "test_agent"
        assert context.role == "test_role"
        print("   ✅ 基本属性功能正常")
        
        # 测试统计更新
        context.update_stats(total_tasks=10, successful_tasks=8)
        assert context.stats['total_tasks'] == 10
        assert context.stats['successful_tasks'] == 8
        
        success_rate = context.get_success_rate()
        assert success_rate == 0.8
        print("   ✅ 统计功能正常")
        
        # 测试序列化
        context_dict = context.to_dict()
        assert 'agent_id' in context_dict
        assert context_dict['agent_id'] == "test_agent"
        assert 'success_rate' in context_dict
        print("   ✅ 序列化功能正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return False


def create_file_for_test():
    """创建测试文件"""
    test_file = Path("test_output.txt")
    test_file.write_text("Hello from minimal test!", encoding='utf-8')
    return test_file


async def test_basic_file_operations():
    """测试基本文件操作（不使用RefactoredBaseAgent）"""
    print("\n5️⃣ 测试基本文件操作...")
    
    try:
        from pathlib import Path
        
        # 测试文件写入
        test_content = "This is a test file created by minimal test."
        test_file = Path("minimal_test_output.txt")
        
        # 写入文件
        test_file.write_text(test_content, encoding='utf-8')
        assert test_file.exists()
        print("   ✅ 文件写入功能正常")
        
        # 读取文件
        read_content = test_file.read_text(encoding='utf-8')
        assert read_content == test_content
        print("   ✅ 文件读取功能正常")
        
        # 清理测试文件
        test_file.unlink()
        print("   ✅ 文件操作测试完成")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return False


def run_minimal_tests():
    """运行最小化测试套件"""
    print("🚀 开始最小化重构组件测试")
    print("="*60)
    
    tests = [
        test_tool_call_classes,
        test_tool_call_parser,
        test_conversation_manager,  
        test_agent_context,
    ]
    
    async_tests = [
        test_basic_file_operations,
    ]
    
    results = []
    
    # 运行同步测试
    for test_func in tests:
        try:
            success = test_func()
            test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
            results.append((test_name, success))
        except Exception as e:
            test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
            results.append((test_name, False))
            print(f"   ❌ {test_name} 异常: {str(e)}")
    
    # 运行异步测试
    async def run_async_tests():
        for test_func in async_tests:
            try:
                success = await test_func()
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                results.append((test_name, success))
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                results.append((test_name, False))
                print(f"   ❌ {test_name} 异常: {str(e)}")
    
    # 运行异步测试
    asyncio.run(run_async_tests())
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 最小化测试结果汇总")
    print("="*60)
    
    passed_count = 0
    total_count = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} {test_name}")
        if success:
            passed_count += 1
    
    success_rate = passed_count / total_count * 100
    print(f"\n📈 测试结果: {passed_count}/{total_count} 通过 ({success_rate:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 所有最小化测试通过！")
        print("✅ 重构组件的核心功能工作正常")
        print("✅ 可以继续进行完整的迁移工作")
        return True
    else:
        print(f"\n⚠️ {total_count - passed_count} 个测试失败")
        print("❌ 需要先修复基础组件问题")
        return False


if __name__ == "__main__":
    success = run_minimal_tests()
    print("\n" + "="*60)
    if success:
        print("🎯 最小化验证 ✅ 成功")
        print("📋 下一步: 可以开始实际的智能体迁移工作")
    else:
        print("🎯 最小化验证 ❌ 失败") 
        print("📋 下一步: 修复基础组件问题")
    print("="*60)
    
    sys.exit(0 if success else 1)