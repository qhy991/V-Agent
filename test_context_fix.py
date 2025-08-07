#!/usr/bin/env python3
"""
测试上下文传递修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
from core.base_agent import TaskMessage
from core.types import FileReference

async def test_context_fix():
    """测试上下文传递修复"""
    print("🧪 开始测试上下文传递修复...")
    
    # 创建配置
    config = FrameworkConfig.from_env()
    
    # 创建代码审查智能体
    agent = EnhancedRealCodeReviewAgent(config)
    
    # 创建测试文件
    test_file_path = "test_counter.v"
    test_content = """module counter (
    input      clk,            // Clock input
    input      rst_n,          // Active-low reset
    input      en,             // Counter enable
    input      up,             // Direction: 1 for up, 0 for down
    input      load,           // Load enable
    input [3:0] load_value,    // Value to load into counter
    output reg [3:0] count,    // Current count value
    output     zero,           // High when count is zero
    output     terminal_count  // High when count is terminal (all 1s or all 0s)
);

// Output logic
assign zero = (count == 4'b0000) ? 1'b1 : 1'b0;
assign terminal_count = up ? 
                        (count == 4'b1111) : 
                        (count == 4'b0000);

// Sequential logic for counter
always @(posedge clk) begin
    if (!rst_n) begin
        count <= 4'b0000;
    end else if (load) begin
        count <= load_value;
    end else if (en) begin
        if (up) begin
            count <= count + 1;
        end else begin
            count <= count - 1;
        end
    end
end

endmodule
"""
    
    # 写入测试文件
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"📄 创建测试文件: {test_file_path}")
    
    try:
        # 1. 首先读取文件，触发缓存机制
        print("\n🔍 步骤1: 读取文件触发缓存...")
        read_result = await agent._tool_read_file(test_file_path)
        print(f"读取结果: {read_result.get('success', False)}")
        
        # 2. 检查缓存状态
        print("\n🔍 步骤2: 检查缓存状态...")
        cached_files = agent.agent_state_cache.get("last_read_files", {})
        print(f"缓存中的文件数量: {len(cached_files)}")
        for filepath, file_info in cached_files.items():
            print(f"  - {filepath}: {file_info.get('file_type', 'unknown')} ({len(file_info.get('content', ''))} 字符)")
        
        # 3. 测试generate_testbench工具调用（不提供module_code参数）
        print("\n🔍 步骤3: 测试generate_testbench工具调用...")
        
        # 创建工具调用
        from core.function_calling import ToolCall
        tool_call = ToolCall(
            tool_name="generate_testbench",
            parameters={
                "module_name": "counter",
                "test_scenarios": [{"name": "basic_test", "description": "基础功能测试"}],
                "clock_period": 10.0,
                "simulation_time": 10000
            }
        )
        
        # 执行上下文检查
        print("🧠 执行工具调用前的上下文检查...")
        agent._check_context_before_tool_call(tool_call)
        
        # 检查参数是否被正确添加
        print(f"工具调用参数: {list(tool_call.parameters.keys())}")
        if "module_code" in tool_call.parameters:
            module_code = tool_call.parameters["module_code"]
            print(f"✅ 成功从缓存恢复模块代码，长度: {len(module_code)} 字符")
            print(f"代码预览: {module_code[:100]}...")
        else:
            print("❌ 未能从缓存恢复模块代码")
        
        # 4. 实际执行generate_testbench工具
        print("\n🔍 步骤4: 实际执行generate_testbench工具...")
        result = await agent._tool_generate_testbench(**tool_call.parameters)
        print(f"执行结果: {result.get('success', False)}")
        if result.get('success'):
            print(f"生成的测试台文件: {result.get('file_path', 'N/A')}")
        else:
            print(f"错误信息: {result.get('error', 'N/A')}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"🧹 清理测试文件: {test_file_path}")

if __name__ == "__main__":
    asyncio.run(test_context_fix()) 