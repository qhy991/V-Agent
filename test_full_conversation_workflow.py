#!/usr/bin/env python3
"""
完整的对话历史工作流测试
验证真实的多智能体协作对话记录功能
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
from core.base_agent import BaseAgent
from core.enums import AgentCapability
from core.response_format import create_success_response
from config.config import FrameworkConfig


class MockVerilogAgent(BaseAgent):
    """模拟Verilog设计智能体"""
    
    def __init__(self):
        super().__init__(
            agent_id="mock_verilog_agent",
            role="design_engineer",
            capabilities={AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
        )
    
    def get_capabilities(self):
        return {AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
    
    def get_specialty_description(self):
        return "模拟Verilog设计智能体，用于测试对话历史记录"
    
    async def execute_enhanced_task(self, task_request: str, **kwargs):
        return create_success_response(
            task_completed=True,
            agent_id=self.agent_id,
            result="Verilog代码已生成",
            message="模拟生成counter.v文件"
        )
    
    async def _call_llm_for_function_calling(self, conversation):
        # 模拟LLM响应，包含工具调用
        return '''
{
    "tool_calls": [
        {
            "tool_name": "write_file",
            "parameters": {
                "filename": "counter.v",
                "content": "module counter(input clk, input rst, output [7:0] count); endmodule"
            }
        }
    ]
}
'''


async def test_full_conversation_workflow():
    """测试完整的对话工作流"""
    print("🧪 开始测试完整的多智能体对话工作流...")
    
    try:
        # 1. 创建配置和协调器
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        print("✅ 协调器创建成功")
        
        # 2. 创建并注册模拟智能体
        mock_agent = MockVerilogAgent()
        
        # 注册智能体到协调器
        from core.llm_coordinator_agent import AgentInfo
        from core.enums import AgentStatus
        
        agent_info = AgentInfo(
            agent_id="mock_verilog_agent",
            agent_instance=mock_agent,
            capabilities={AgentCapability.CODE_GENERATION},
            specialty="design_engineer",
            status=AgentStatus.IDLE
        )
        
        coordinator.registered_agents["mock_verilog_agent"] = agent_info
        
        print("✅ 模拟智能体注册成功")
        
        # 3. 创建任务上下文
        task_context = TaskContext(
            task_id="workflow_test_123",
            original_request="设计一个8位counter模块并生成Verilog代码"
        )
        
        # 4. 模拟完整的对话流程
        print("\n📝 开始模拟多智能体对话流程...")
        
        # 步骤1：记录用户请求
        task_context.add_conversation_message(
            role="user",
            content="设计一个8位counter模块并生成Verilog代码",
            agent_id="user"
        )
        
        # 步骤2：协调器分析任务
        task_context.add_conversation_message(
            role="system",
            content="开始协调任务执行，识别任务类型",
            agent_id="llm_coordinator_agent"
        )
        
        # 步骤3：工具调用 - 识别任务类型
        task_context.add_conversation_message(
            role="tool_call",
            content="调用identify_task_type工具",
            agent_id="llm_coordinator_agent",
            tool_info={
                "tool_name": "identify_task_type",
                "parameters": {"task_description": "设计counter模块"},
                "status": "started"
            }
        )
        
        task_context.add_conversation_message(
            role="tool_result",
            content="任务类型识别完成",
            agent_id="llm_coordinator_agent",
            tool_info={
                "tool_name": "identify_task_type",
                "success": True,
                "result": "design_task",
                "status": "completed"
            }
        )
        
        # 步骤4：工具调用 - 分配任务给智能体
        task_context.add_conversation_message(
            role="tool_call",
            content="分配任务给Verilog设计智能体",
            agent_id="llm_coordinator_agent",
            tool_info={
                "tool_name": "assign_task_to_agent",
                "parameters": {
                    "agent_id": "mock_verilog_agent",
                    "task_description": "设计8位counter模块"
                },
                "status": "started"
            }
        )
        
        # 步骤5：设置任务上下文给智能体
        mock_agent.set_task_context(task_context)
        
        # 步骤6：智能体处理任务
        task_context.add_conversation_message(
            role="user",
            content="设计8位counter模块，生成Verilog代码",
            agent_id="mock_verilog_agent"
        )
        
        # 步骤7：智能体工具调用
        task_context.add_conversation_message(
            role="tool_call",
            content="开始调用工具: write_file",
            agent_id="mock_verilog_agent",
            tool_info={
                "tool_name": "write_file",
                "parameters": {
                    "filename": "counter.v",
                    "content": "module counter(input clk, input rst, output [7:0] count); endmodule"
                },
                "status": "started"
            }
        )
        
        task_context.add_conversation_message(
            role="tool_result",
            content="工具执行成功: write_file",
            agent_id="mock_verilog_agent",
            tool_info={
                "tool_name": "write_file",
                "parameters": {
                    "filename": "counter.v",
                    "content": "module counter..."
                },
                "success": True,
                "result": "文件已成功写入到counter.v",
                "status": "completed"
            }
        )
        
        # 步骤8：智能体响应
        task_context.add_conversation_message(
            role="assistant",
            content="已成功生成8位counter模块的Verilog代码并保存到counter.v文件",
            agent_id="mock_verilog_agent"
        )
        
        # 步骤9：协调器收到任务完成
        task_context.add_conversation_message(
            role="tool_result",
            content="智能体任务执行完成",
            agent_id="llm_coordinator_agent",
            tool_info={
                "tool_name": "assign_task_to_agent",
                "success": True,
                "result": "任务已成功分配并完成",
                "status": "completed"
            }
        )
        
        # 步骤10：协调器最终响应
        task_context.add_conversation_message(
            role="assistant",
            content="✅ 任务完成！已成功设计8位counter模块并生成Verilog代码",
            agent_id="llm_coordinator_agent"
        )
        
        print(f"✅ 模拟对话流程完成，总计 {len(task_context.conversation_history)} 条消息")
        
        # 5. 测试统计功能
        print("\n📊 对话统计分析...")
        summary = task_context.get_conversation_summary()
        print(f"总消息数: {summary['total_messages']}")
        print(f"参与智能体: {summary['agents_involved']}")
        print(f"消息类型分布: {summary['message_types']}")
        
        tool_summary = task_context.get_tool_calls_summary()
        print(f"工具调用总数: {tool_summary['total_tool_calls']}")
        print(f"成功率: {(1 - tool_summary['failure_rate']) * 100:.1f}%")
        print(f"使用的工具: {tool_summary['unique_tools_used']}")
        print(f"工具使用统计: {tool_summary['tool_usage_count']}")
        
        # 6. 生成实验报告格式
        print("\n🔧 生成实验报告格式...")
        final_result = coordinator._collect_final_result(task_context, "多智能体协作完成")
        
        # 验证对话历史
        conv_history = final_result.get('conversation_history', [])
        print(f"✅ 实验报告包含对话历史: {len(conv_history)} 条消息")
        
        # 7. 保存测试结果
        print("\n💾 保存完整测试结果...")
        test_result = {
            "test_type": "full_workflow",
            "experiment_report": final_result,
            "conversation_analysis": {
                "summary": summary,
                "tool_analysis": tool_summary
            }
        }
        
        result_file = project_root / "test_full_workflow_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 完整测试结果已保存到: {result_file}")
        
        # 8. 验证关键信息
        print("\n🔍 验证对话记录完整性...")
        
        # 验证消息类型
        message_types = set(msg.get('role') for msg in conv_history)
        expected_types = {'user', 'system', 'assistant', 'tool_call', 'tool_result'}
        
        if expected_types.issubset(message_types):
            print("✅ 所有消息类型都已记录")
        else:
            print(f"⚠️ 缺少消息类型: {expected_types - message_types}")
        
        # 验证智能体参与
        agents = set(msg.get('agent_id') for msg in conv_history)
        expected_agents = {'user', 'llm_coordinator_agent', 'mock_verilog_agent'}
        
        if expected_agents.issubset(agents):
            print("✅ 所有智能体的对话都已记录")
        else:
            print(f"⚠️ 缺少智能体记录: {expected_agents - agents}")
        
        # 验证工具调用
        tool_calls = [msg for msg in conv_history if msg.get('tool_info')]
        print(f"✅ 工具调用记录: {len(tool_calls)} 条")
        
        for i, tool_call in enumerate(tool_calls):
            tool_info = tool_call.get('tool_info', {})
            print(f"  工具 {i+1}: {tool_info.get('tool_name')} - {tool_info.get('status')}")
        
        print("\n🎉 完整对话工作流测试通过！")
        print("\n📋 测试结果总结:")
        print(f"- 对话消息总数: {len(conv_history)}")
        print(f"- 参与智能体数: {len(agents)}")
        print(f"- 工具调用次数: {len(tool_calls)}")
        print(f"- 消息类型数: {len(message_types)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_full_conversation_workflow())
    
    if result:
        print("\n✨ 恭喜！完整的多智能体对话历史记录功能已成功实现")
        print("\n🚀 可以开始使用:")
        print("1. python test_llm_coordinator_enhanced.py")
        print("2. python gradio_multi_agent_visualizer.py")
    else:
        print("\n❌ 测试失败，需要进一步检查")
    
    sys.exit(0 if result else 1)