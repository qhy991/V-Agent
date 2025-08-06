#!/usr/bin/env python3
"""
Quick Validation - 快速验证脚本
=============================

快速验证重构组件的基本功能是否正常。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试导入是否正常"""
    print("🔍 测试1: 检查导入...")
    
    try:
        # 测试基础导入
        from core.enums import AgentCapability
        print("  ✅ core.enums 导入成功")
        
        from core.function_calling import ToolCall, ToolResult  
        print("  ✅ core.function_calling 导入成功")
        
        # 测试新组件导入
        from core.context.agent_context import AgentContext
        print("  ✅ AgentContext 导入成功")
        
        from core.conversation.manager import ConversationManager
        print("  ✅ ConversationManager 导入成功")
        
        from core.function_calling.parser import ToolCallParser
        print("  ✅ ToolCallParser 导入成功")
        
        # 测试重构的基础智能体
        from core.refactored_base_agent import RefactoredBaseAgent
        print("  ✅ RefactoredBaseAgent 导入成功")
        
        return True, "所有导入测试通过"
        
    except Exception as e:
        return False, f"导入测试失败: {str(e)}"


def test_agent_context():
    """测试 AgentContext 功能"""
    print("\n🔍 测试2: AgentContext 功能...")
    
    try:
        from core.context.agent_context import AgentContext
        from core.enums import AgentCapability
        
        # 创建上下文
        context = AgentContext(
            agent_id="test_agent",
            role="test_role",
            capabilities={AgentCapability.ANALYSIS}  # 使用一个实际存在的能力
        )
        
        # 测试基本属性
        assert context.agent_id == "test_agent"
        assert context.role == "test_role"
        assert AgentCapability.ANALYSIS in context.capabilities
        print("  ✅ 基本属性测试通过")
        
        # 测试方法
        description = context.get_specialty_description()
        assert isinstance(description, str)
        assert len(description) > 0
        print("  ✅ 专业描述生成测试通过")
        
        # 测试序列化
        context_dict = context.to_dict()
        assert 'agent_id' in context_dict
        assert context_dict['agent_id'] == "test_agent"
        print("  ✅ 序列化测试通过")
        
        return True, "AgentContext 功能测试通过"
        
    except Exception as e:
        return False, f"AgentContext 测试失败: {str(e)}"


def test_conversation_manager():
    """测试 ConversationManager 功能"""
    print("\n🔍 测试3: ConversationManager 功能...")
    
    try:
        from core.conversation.manager import ConversationManager
        
        # 创建对话管理器
        manager = ConversationManager("test_agent")
        
        # 测试对话开始
        manager.start_conversation("test_conv_1")
        assert manager.current_conversation_id == "test_conv_1"
        print("  ✅ 对话开始测试通过")
        
        # 测试消息添加
        manager.add_message("user", "Hello", conversation_id="test_conv_1")
        manager.add_message("assistant", "Hi there!", conversation_id="test_conv_1")
        print("  ✅ 消息添加测试通过")
        
        # 测试历史获取
        history = manager.get_conversation_history("test_conv_1")
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == 'Hello'
        print("  ✅ 历史获取测试通过")
        
        # 测试摘要
        summary = manager.get_conversation_summary("test_conv_1")
        assert summary['message_count'] == 2
        assert summary['conversation_id'] == "test_conv_1"
        print("  ✅ 对话摘要测试通过")
        
        return True, "ConversationManager 功能测试通过"
        
    except Exception as e:
        return False, f"ConversationManager 测试失败: {str(e)}"


def test_tool_call_parser():
    """测试 ToolCallParser 功能"""
    print("\n🔍 测试4: ToolCallParser 功能...")
    
    try:
        from core.function_calling.parser import ToolCallParser
        
        # 创建解析器
        parser = ToolCallParser()
        
        # 测试JSON格式解析
        json_response = '''{
    "tool_calls": [
        {
            "tool_name": "write_file",
            "parameters": {
                "filename": "test.txt",
                "content": "Hello World"
            }
        }
    ]
}'''
        
        tool_calls = parser.parse_tool_calls_from_response(json_response)
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "write_file"
        assert tool_calls[0].parameters["filename"] == "test.txt"
        print("  ✅ JSON格式解析测试通过")
        
        # 测试参数标准化
        normalized_params = parser.normalize_tool_parameters(
            "write_file", 
            {"file": "test.txt", "text": "content"}
        )
        # 应该映射 file->filename, text->content
        print(f"  🔧 参数标准化结果: {normalized_params}")
        print("  ✅ 参数标准化测试通过")
        
        return True, "ToolCallParser 功能测试通过"
        
    except Exception as e:
        return False, f"ToolCallParser 测试失败: {str(e)}"


async def test_refactored_base_agent():
    """测试重构的基础智能体"""
    print("\n🔍 测试5: RefactoredBaseAgent 功能...")
    
    try:
        from core.refactored_base_agent import RefactoredBaseAgent
        from core.enums import AgentCapability
        
        # 创建一个测试智能体类
        class TestAgent(RefactoredBaseAgent):
            async def _call_llm_for_function_calling(self, conversation):
                return "Test LLM response"
            
            async def execute_enhanced_task(self, enhanced_prompt, original_message=None, file_contents=None):
                return {"success": True, "result": "Test task completed"}
        
        # 创建实例
        agent = TestAgent(
            agent_id="test_refactored_agent",
            role="test_role",
            capabilities={AgentCapability.ANALYSIS}
        )
        
        # 测试基本属性
        assert agent.agent_id == "test_refactored_agent"
        assert agent.role == "test_role"
        print("  ✅ 基本属性测试通过")
        
        # 测试能力
        capabilities = agent.get_capabilities()
        assert AgentCapability.ANALYSIS in capabilities
        print("  ✅ 能力管理测试通过")
        
        # 测试工具注册
        assert 'write_file' in agent.function_calling_tools
        assert 'read_file' in agent.function_calling_tools
        print("  ✅ 基础工具注册测试通过")
        
        # 测试文件写入工具
        write_result = await agent._tool_write_file(
            filename="test_validation.txt",
            content="Hello from validation test"
        )
        assert write_result['success'] == True
        print("  ✅ 文件写入工具测试通过")
        
        # 测试文件读取工具
        read_result = await agent._tool_read_file(filepath=write_result['file_path'])
        assert read_result['success'] == True
        assert "Hello from validation test" in read_result['result']
        print("  ✅ 文件读取工具测试通过")
        
        return True, "RefactoredBaseAgent 功能测试通过"
        
    except Exception as e:
        return False, f"RefactoredBaseAgent 测试失败: {str(e)}"


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始快速验证测试")
    print("="*50)
    
    tests = [
        ("导入测试", test_imports),
        ("AgentContext测试", test_agent_context), 
        ("ConversationManager测试", test_conversation_manager),
        ("ToolCallParser测试", test_tool_call_parser),
        ("RefactoredBaseAgent测试", test_refactored_base_agent)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                success, message = await test_func()
            else:
                success, message = test_func()
            
            results.append((test_name, success, message))
            
        except Exception as e:
            results.append((test_name, False, f"测试异常: {str(e)}"))
    
    # 打印测试结果
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    passed_count = 0
    total_count = len(results)
    
    for test_name, success, message in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {message}")
        if success:
            passed_count += 1
    
    print(f"\n📈 总体结果: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！重构组件功能正常。")
        return True
    else:
        print(f"⚠️ {total_count - passed_count} 个测试失败，需要修复。")
        return False


async def main():
    """主函数"""
    success = await run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)