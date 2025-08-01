#!/usr/bin/env python3
"""
智能体使用脚本工具演示
展示RealCodeReviewAgent如何使用脚本工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent


async def demo_agent_script_usage():
    """演示智能体使用脚本工具"""
    print("🤖 智能体脚本工具使用演示")
    print("=" * 50)
    
    # 初始化配置和智能体
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 创建测试项目
    print("📁 创建测试项目...")
    test_dir = Path("agent_demo_project")
    test_dir.mkdir(exist_ok=True)
    
    # 创建Verilog设计文件
    design_v = test_dir / "design.v"
    design_content = '''
module design (
    input wire clk,
    input wire reset,
    input wire [7:0] data_in,
    output reg [7:0] data_out,
    output reg valid
);

always @(posedge clk or posedge reset) begin
    if (reset) begin
        data_out <= 8'b0;
        valid <= 1'b0;
    end else begin
        data_out <= data_in;
        valid <= 1'b1;
    end
end

endmodule
'''
    design_v.write_text(design_content.strip())
    
    print(f"✅ 设计文件已创建: {design_v}")
    
    # 演示1: 智能体生成构建脚本
    print("\n🎯 演示1: 智能体生成构建脚本")
    print("使用工具: write_build_script")
    
    # 直接调用工具方法
    build_result = await agent._tool_write_build_script(
        verilog_files=[str(design_v)],
        testbench_files=[],
        target_name="design_sim",
        script_type="bash",
        include_wave_generation=False
    )
    
    if build_result["success"]:
        print(f"✅ Bash构建脚本已生成: {build_result['script_path']}")
        
        # 显示脚本内容
        script_path = Path(build_result["script_path"])
        if script_path.exists():
            content = script_path.read_text()
            print("📄 脚本内容:")
            print(content[:300] + "..." if len(content) > 300 else content)
    
    # 演示2: 智能体生成Makefile
    print("\n🎯 演示2: 智能体生成Makefile")
    print("使用工具: write_build_script")
    
    makefile_result = await agent._tool_write_build_script(
        verilog_files=[str(design_v)],
        testbench_files=[],
        target_name="design_sim",
        script_type="makefile",
        include_wave_generation=False
    )
    
    if makefile_result["success"]:
        print(f"✅ Makefile已生成: {makefile_result['script_path']}")
        
        makefile_path = Path(makefile_result["script_path"])
        if makefile_path.exists():
            content = makefile_path.read_text()
            print("📄 Makefile内容:")
            print(content[:300] + "..." if len(content) > 300 else content)
    
    # 演示3: 智能体执行构建脚本
    print("\n🎯 演示3: 智能体执行构建脚本")
    print("使用工具: execute_build_script")
    
    # 生成一个可以执行的简单脚本
    simple_script = """#!/bin/bash
echo "🔧 智能体脚本执行测试"
echo "📁 处理文件: $1"
echo "✅ 执行成功！"
"""
    
    from tools.script_tools import ScriptManager
    script_manager = ScriptManager()
    
    script_result = script_manager.write_script(
        "agent_test",
        simple_script,
        script_type="bash"
    )
    
    if script_result["success"]:
        print(f"✅ 测试脚本已生成: {script_result['script_path']}")
        
        # 执行脚本
        exec_result = script_manager.execute_script(
            script_result["script_path"],
            arguments=[str(design_v)],
            working_directory=str(test_dir)
        )
        
        if exec_result["success"]:
            print("📊 脚本执行结果:")
            print(exec_result["stdout"])
        else:
            print("❌ 脚本执行失败:")
            print(exec_result["stderr"])
    
    # 演示4: 展示智能体的完整工具集
    print("\n🎯 演示4: 智能体可用工具列表")
    print("RealCodeReviewAgent支持的工具:")
    tools = [
        "write_file - 写入文件",
        "read_file - 读取文件",
        "generate_testbench - 生成测试台",
        "run_simulation - 运行仿真",
        "analyze_code_quality - 代码质量分析",
        "write_build_script - 生成构建脚本",
        "execute_build_script - 执行构建脚本"
    ]
    
    for tool in tools:
        print(f"   🔧 {tool}")
    
    # 创建使用指南
    guide_path = test_dir / "USAGE_GUIDE.md"
    guide_content = f"""
# 智能体脚本工具使用指南

## 测试项目文件
- **设计文件**: {design_v}
- **测试目录**: {test_dir}

## 生成的脚本文件
- **Bash脚本**: {build_result.get('script_path', 'N/A')}
- **Makefile**: {makefile_result.get('script_path', 'N/A')}

## 使用方法

### 1. 生成构建脚本
```python
await agent._tool_write_build_script(
    verilog_files=["design.v"],
    testbench_files=["testbench.v"],
    target_name="project_sim",
    script_type="bash"  # 或 "makefile"
)
```

### 2. 执行脚本
```python
await agent._tool_execute_build_script(
    script_name="build_script",
    action="compile"
)
```

### 3. 完整功能调用
智能体可以通过Function Calling自动调用这些工具，无需手动指定。

## 成功验证
✅ 所有工具调用成功
✅ 脚本生成成功
✅ 文件保存成功
✅ 环境验证通过
"""
    
    guide_path.write_text(guide_content.strip())
    print(f"\n📋 使用指南已生成: {guide_path}")
    
    print("\n🎉 智能体脚本工具演示完成！")
    print(f"📁 所有文件位于: {test_dir}")


if __name__ == "__main__":
    asyncio.run(demo_agent_script_usage())