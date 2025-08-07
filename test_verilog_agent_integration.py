#!/usr/bin/env python3
"""
重构后Verilog智能体测试
验证使用统一LLM通信模块的Verilog智能体功能
"""

import asyncio
import sys
from typing import Dict, Any

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试重构后Verilog智能体基础功能...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        # 创建配置
        config = FrameworkConfig.from_env()
        
        # 创建重构后的智能体
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        print("✅ 重构后Verilog智能体创建成功")
        print(f"📊 智能体ID: {agent.agent_id}")
        print(f"🎯 角色: {agent.role}")
        print(f"🔧 能力: {agent.get_capabilities()}")
        print(f"📝 专业描述: {agent.get_specialty_description()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_communication():
    """测试LLM通信功能"""
    print("\n🧪 测试LLM通信功能...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试System Prompt构建
        system_prompt = await agent._build_system_prompt()
        print(f"✅ System Prompt构建成功，长度: {len(system_prompt)} 字符")
        print(f"📝 Prompt预览: {system_prompt[:200]}...")
        
        # 验证Prompt内容
        assert "Verilog硬件设计专家" in system_prompt
        assert "代码生成能力" in system_prompt
        assert "Function Calling模式" in system_prompt
        
        # 测试LLM调用
        conversation = [
            {"role": "user", "content": "请简要介绍Verilog设计的基本原则"}
        ]
        
        response = await agent._call_llm_for_function_calling(conversation)
        print(f"✅ LLM调用成功，响应长度: {len(response)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM通信测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_registration():
    """测试工具注册功能"""
    print("\n🧪 测试工具注册功能...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 检查工具注册
        registered_tools = agent.get_registered_tools()
        print(f"✅ 工具注册成功，注册工具数量: {len(registered_tools)}")
        
        # 验证关键工具
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in registered_tools]
        expected_tools = [
            "analyze_design_requirements",
            "generate_verilog_code", 
            "analyze_code_quality",
            "optimize_verilog_code",
            "get_tool_usage_guide"
        ]
        
        for tool_name in expected_tools:
            if tool_name in tool_names:
                print(f"✅ 工具 {tool_name} 注册成功")
            else:
                print(f"❌ 工具 {tool_name} 未找到")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 工具注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_design_requirements_analysis():
    """测试设计需求分析工具"""
    print("\n🧪 测试设计需求分析工具...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试需求分析
        requirements = """
        设计一个4位同步计数器模块，具有以下特性：
        1. 时钟上升沿触发
        2. 异步复位功能
        3. 使能信号控制
        4. 计数范围：0-15
        5. 溢出时自动回零
        """
        
        result = await agent._tool_analyze_design_requirements(
            requirements=requirements,
            design_type="sequential",
            complexity_level="medium"
        )
        
        print(f"✅ 需求分析成功")
        print(f"📊 分析结果长度: {len(str(result))} 字符")
        print(f"🔍 设计类型: {result.get('design_type', 'N/A')}")
        print(f"📈 复杂度级别: {result.get('complexity_level', 'N/A')}")
        
        # 验证结果
        assert "analysis_result" in result
        assert result["design_type"] == "sequential"
        assert result["complexity_level"] == "medium"
        
        return True
        
    except Exception as e:
        print(f"❌ 需求分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_verilog_code_generation():
    """测试Verilog代码生成工具"""
    print("\n🧪 测试Verilog代码生成工具...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试代码生成
        result = await agent._tool_generate_verilog_code(
            module_name="counter_4bit",
            requirements="4位同步计数器，时钟上升沿触发，异步复位",
            input_ports=[
                {"name": "clk", "width": 1, "description": "时钟信号"},
                {"name": "rst_n", "width": 1, "description": "异步复位信号"},
                {"name": "en", "width": 1, "description": "使能信号"}
            ],
            output_ports=[
                {"name": "count", "width": 4, "description": "计数值输出"}
            ],
            coding_style="rtl"
        )
        
        print(f"✅ 代码生成成功")
        print(f"📊 生成代码长度: {len(result.get('verilog_code', ''))} 字符")
        print(f"🔧 编码风格: {result.get('coding_style', 'N/A')}")
        print(f"⏱️ 生成时间: {result.get('generation_time', 'N/A')}")
        
        # 验证结果
        assert "verilog_code" in result
        assert result["module_name"] == "counter_4bit"
        assert result["coding_style"] == "rtl"
        
        # 验证代码内容
        code = result["verilog_code"]
        assert "module counter_4bit" in code.lower()
        assert "input" in code.lower()
        assert "output" in code.lower()
        
        return True
        
    except Exception as e:
        print(f"❌ 代码生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_code_quality_analysis():
    """测试代码质量分析工具"""
    print("\n🧪 测试代码质量分析工具...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试代码质量分析
        test_code = """
module test_module (
    input wire clk,
    input wire rst_n,
    input wire [3:0] data_in,
    output reg [3:0] data_out
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_out <= 4'b0000;
    end else begin
        data_out <= data_in;
    end
end

endmodule
"""
        
        result = await agent._tool_analyze_code_quality(
            verilog_code=test_code,
            module_name="test_module"
        )
        
        print(f"✅ 代码质量分析成功")
        print(f"📊 分析结果长度: {len(str(result))} 字符")
        print(f"🔍 模块名称: {result.get('module_name', 'N/A')}")
        print(f"📏 代码长度: {result.get('code_length', 'N/A')}")
        
        # 验证结果
        assert "quality_analysis" in result
        assert result["module_name"] == "test_module"
        assert result["code_length"] == len(test_code)
        
        return True
        
    except Exception as e:
        print(f"❌ 代码质量分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_execution():
    """测试任务执行功能"""
    print("\n🧪 测试任务执行功能...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        from core.base_agent import TaskMessage
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 创建测试任务
        task_message = TaskMessage(
            task_id="test_task_001",
            content="请设计一个简单的2位计数器模块",
            sender_id="test_user",
            receiver_id="verilog_agent",
            message_type="task_request"
        )
        
        # 执行任务
        result = await agent.execute_enhanced_task(
            enhanced_prompt="设计一个2位同步计数器，具有时钟和复位功能",
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ 任务执行成功")
        print(f"📊 响应状态: {result.get('status', 'N/A')}")
        print(f"🎯 响应类型: {result.get('response_type', 'N/A')}")
        
        # 验证结果
        assert "status" in result
        assert "response_type" in result
        assert "message" in result
        
        return True
        
    except Exception as e:
        print(f"❌ 任务执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始重构后Verilog智能体测试...\n")
    
    # 基础功能测试
    basic_success = test_basic_functionality()
    
    # LLM通信测试
    llm_success = await test_llm_communication()
    
    # 工具注册测试
    tool_success = await test_tool_registration()
    
    # 需求分析测试
    analysis_success = await test_design_requirements_analysis()
    
    # 代码生成测试
    generation_success = await test_verilog_code_generation()
    
    # 代码质量分析测试
    quality_success = await test_code_quality_analysis()
    
    # 任务执行测试
    execution_success = await test_task_execution()
    
    # 总结
    print("\n" + "="*60)
    print("📋 重构后Verilog智能体测试结果总结:")
    print(f"   基础功能: {'✅ 通过' if basic_success else '❌ 失败'}")
    print(f"   LLM通信: {'✅ 通过' if llm_success else '❌ 失败'}")
    print(f"   工具注册: {'✅ 通过' if tool_success else '❌ 失败'}")
    print(f"   需求分析: {'✅ 通过' if analysis_success else '❌ 失败'}")
    print(f"   代码生成: {'✅ 通过' if generation_success else '❌ 失败'}")
    print(f"   质量分析: {'✅ 通过' if quality_success else '❌ 失败'}")
    print(f"   任务执行: {'✅ 通过' if execution_success else '❌ 失败'}")
    
    all_success = all([basic_success, llm_success, tool_success, 
                      analysis_success, generation_success, quality_success, execution_success])
    
    if all_success:
        print("\n🎉 所有重构后Verilog智能体测试通过！")
        print("💡 重构后的Verilog智能体已准备就绪，可以替换原版本。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 