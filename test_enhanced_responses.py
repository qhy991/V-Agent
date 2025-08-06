#!/usr/bin/env python3
"""
测试增强响应系统 - 验证智能体现在返回详细响应
Test Enhanced Response System - Verify agents now return detailed responses
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.unified_logging_system import UnifiedLoggingSystem, set_global_logging_system


async def test_verilog_agent_detailed_response():
    """测试Verilog智能体现在是否返回详细响应"""
    print("🧪 测试Verilog智能体详细响应...")
    
    # 创建配置和智能体
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 简单的计数器设计请求
    test_request = "设计一个简单的8位计数器模块，包含时钟、复位和计数输出端口。"
    
    try:
        # 执行任务
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=5,
            conversation_id=f"test_verilog_{int(time.time())}"
        )
        
        print(f"📊 Verilog智能体响应长度: {len(response)} 字符")
        print(f"📝 响应前300字符:")
        print(response[:300] + "..." if len(response) > 300 else response)
        
        # 检查响应质量
        is_detailed = len(response) > 100
        has_technical_content = any(keyword in response for keyword in [
            "模块", "端口", "时钟", "复位", "计数", "Verilog", "设计"
        ])
        
        print(f"✅ 详细响应: {is_detailed}")
        print(f"✅ 包含技术内容: {has_technical_content}")
        
        return is_detailed and has_technical_content
        
    except Exception as e:
        print(f"❌ Verilog智能体测试失败: {e}")
        return False


async def test_code_reviewer_detailed_response():
    """测试代码审查智能体现在是否返回详细响应"""
    print("\n🧪 测试代码审查智能体详细响应...")
    
    # 创建配置和智能体
    config = FrameworkConfig.from_env()
    agent = EnhancedRealCodeReviewAgent(config)
    
    # 先创建一个测试文件
    test_verilog_code = """
module simple_counter (
    input wire clk,
    input wire reset,
    output reg [7:0] count
);

always @(posedge clk or posedge reset) begin
    if (reset)
        count <= 8'b0;
    else
        count <= count + 1;
end

endmodule
"""
    
    test_file_path = Path("test_counter.v")
    test_file_path.write_text(test_verilog_code, encoding='utf-8')
    
    # 代码审查请求
    test_request = f"请审查 {test_file_path} 文件中的Verilog代码，生成测试台并运行仿真验证。"
    
    try:
        # 执行任务
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=5,
            conversation_id=f"test_reviewer_{int(time.time())}"
        )
        
        print(f"📊 代码审查智能体响应长度: {len(response)} 字符")
        print(f"📝 响应前300字符:")
        print(response[:300] + "..." if len(response) > 300 else response)
        
        # 检查响应质量
        is_detailed = len(response) > 100
        has_technical_content = any(keyword in response for keyword in [
            "审查", "测试", "仿真", "代码", "质量", "验证", "问题", "建议"
        ])
        
        print(f"✅ 详细响应: {is_detailed}")
        print(f"✅ 包含技术内容: {has_technical_content}")
        
        # 清理测试文件
        if test_file_path.exists():
            test_file_path.unlink()
            
        return is_detailed and has_technical_content
        
    except Exception as e:
        print(f"❌ 代码审查智能体测试失败: {e}")
        # 清理测试文件
        if test_file_path.exists():
            test_file_path.unlink()
        return False


async def main():
    """主测试函数"""
    print("🚀 开始测试增强响应系统...")
    
    # 初始化统一日志系统
    session_id = f"test_enhanced_responses_{int(time.time())}"
    logging_system = UnifiedLoggingSystem(session_id)
    set_global_logging_system(logging_system)
    
    try:
        # 测试Verilog智能体
        verilog_success = await test_verilog_agent_detailed_response()
        
        # 测试代码审查智能体
        reviewer_success = await test_code_reviewer_detailed_response()
        
        # 总结结果
        print(f"\n📋 测试结果总结:")
        print(f"   🔧 Verilog智能体详细响应: {'✅' if verilog_success else '❌'}")
        print(f"   🧪 代码审查智能体详细响应: {'✅' if reviewer_success else '❌'}")
        
        overall_success = verilog_success and reviewer_success
        print(f"\n🎯 整体测试结果: {'✅ 成功' if overall_success else '❌ 失败'}")
        
        if overall_success:
            print("✅ 智能体现在能够返回详细的响应内容！")
        else:
            print("❌ 部分智能体仍返回简短响应，需要进一步调试。")
            
        return overall_success
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)