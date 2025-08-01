#!/usr/bin/env python3
"""
测试agent的脚本执行和错误处理能力
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
from tools.script_tools import ScriptManager


async def test_agent_execution_capabilities():
    """测试agent的完整执行能力"""
    print("🤖 测试Agent脚本执行和错误处理")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    script_manager = ScriptManager()
    
    # 测试1: 成功执行
    print("\n🎯 测试1: 成功执行")
    
    test_dir = Path("agent_execution_test")
    test_dir.mkdir(exist_ok=True)
    
    # 创建正确的Verilog文件
    correct_v = test_dir / "correct.v"
    correct_v.write_text('''
module correct(input clk, output reg [7:0] count);
    initial begin
        count = 8'h00;
        #10 count = 8'hFF;
        #10 $display("Success: count = %d", count);
        #10 $finish;
    end
endmodule
''')
    
    tb_v = test_dir / "correct_tb.v"
    tb_v.write_text('''
module correct_tb();
    reg clk;
    wire [7:0] count;
    
    correct dut(.clk(clk), .count(count));
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        $monitor("Time: %t, Count: %d", $time, count);
        #100 $finish;
    end
endmodule
''')
    
    # 使用agent执行完整流程
    start_time = asyncio.get_event_loop().time()
    
    response = await agent.process_with_function_calling(
        user_request=f"""
        请为以下Verilog项目创建完整的构建和仿真环境：
        - 设计文件: {correct_v}
        - 测试文件: {tb_v}
        - 需要: 生成构建脚本并执行仿真
        - 要求: 如果执行失败，分析错误并提供修复建议
        """,
        max_iterations=5
    )
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    print(f"⏱️  处理时间: {duration:.2f} 秒")
    print(f"📊 响应长度: {len(str(response))} 字符")
    
    # 测试2: 故意创建错误并观察处理
    print("\n🎯 测试2: 错误处理与修复")
    
    error_v = test_dir / "error.v"
    error_v.write_text('''
module error(input clk, output reg [7:0] count);
    initial begin
        count = 8'h00;  // 正确
        #10 count = 8'hFF  // 缺少分号 - 故意错误
        #10 $display("This should fail");
        #10 $finish
    end
endmodule
''')
    
    error_response = await agent.process_with_function_calling(
        user_request=f"""
        尝试构建这个有错误的Verilog文件：
        - 文件: {error_v}
        - 要求: 如果编译失败，请分析错误并修复
        - 输出: 修复后的文件和成功的构建
        """,
        max_iterations=3
    )
    
    # 测试3: 直接工具调用测试
    print("\n🎯 测试3: 直接工具调用")
    
    # 测试脚本生成
    build_result = await agent._tool_write_build_script(
        verilog_files=[str(correct_v)],
        testbench_files=[str(tb_v)],
        target_name="test_build",
        script_type="bash"
    )
    
    if build_result["success"]:
        print(f"✅ 构建脚本生成成功: {build_result['script_path']}")
        
        # 测试脚本执行
        exec_result = await agent._tool_execute_build_script(
            script_name="test_build",
            action="all"
        )
        
        print(f"📊 执行结果: {exec_result}")
    
    # 测试4: 手动验证脚本执行
    print("\n🎯 测试4: 手动验证执行")
    
    # 生成并执行脚本
    script_content = script_manager.generate_build_script(
        verilog_files=[str(correct_v)],
        testbench_files=[str(tb_v)],
        target_name="manual_test",
        include_wave_generation=True
    )
    
    script_path = test_dir / "manual_build.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    print("📄 生成的脚本:")
    print("=" * 50)
    print(script_content)
    print("=" * 50)
    
    # 执行脚本
    exec_result = script_manager.execute_script(
        str(script_path),
        working_directory=str(test_dir)
    )
    
    print("📊 手动执行结果:")
    print(f"   成功: {exec_result['success']}")
    if exec_result['success']:
        print("✅ 输出:")
        print(exec_result['stdout'])
    else:
        print("❌ 错误:")
        print(exec_result['stderr'])
    
    # 测试5: 错误模拟和恢复
    print("\n🎯 测试5: 错误模拟和恢复")
    
    # 创建有错误的脚本
    bad_script = '''
#!/bin/bash
echo "This script has intentional errors"
iverilog -o bad bad.v  # 文件不存在
if [ $? -ne 0 ]; then
    echo "Compilation failed - this is expected"
    exit 1
fi
'''
    
    bad_script_path = test_dir / "bad_script.sh"
    bad_script_path.write_text(bad_script)
    bad_script_path.chmod(0o755)
    
    bad_result = script_manager.execute_script(
        str(bad_script_path),
        working_directory=str(test_dir)
    )
    
    print("📊 错误处理结果:")
    print(f"   成功: {bad_result['success']}")
    print(f"   错误类型: {bad_result.get('error', '无错误信息')}")
    print(f"   返回码: {bad_result.get('return_code', '未知')}")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 Agent执行能力总结:")
    
    # 检查生成的文件
    generated_files = list(test_dir.rglob("*"))
    print(f"   生成文件: {len([f for f in generated_files if f.is_file()])} 个")
    for f in generated_files:
        if f.is_file():
            print(f"      📄 {f.name}")
    
    print(f"\n🎉 Agent脚本执行和错误处理验证完成!")
    print(f"📁 测试文件位于: {test_dir}")


if __name__ == "__main__":
    asyncio.run(test_agent_execution_capabilities())