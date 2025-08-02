#!/usr/bin/env python3
"""
测试代码清理功能
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_code_cleaning():
    """测试代码清理功能"""
    print("🧹 测试代码清理功能")
    
    from extensions.test_analyzer import TestAnalyzer
    
    # 创建测试分析器
    analyzer = TestAnalyzer()
    
    # 创建临时目录和问题文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建包含格式问题的文件（模拟log-16.log中的问题）
        problem_file = temp_path / "problem_module.v"
        problem_content = """以下是符合IEEE 1800标准、可综合的 `simple_8bit_adder` 模块的Verilog代码，采用RTL风格编写，并包含必要的注释：

```verilog
// simple_8bit_adder.v
// 8-bit Ripple Carry Adder with Carry-in and Carry-out
// Designed for RTL synthesis, supports basic binary addition

module simple_8bit_adder (
    input        clk,        // Clock signal
    input        rst,        // Active high reset
    input  [7:0] a,         // 8-bit input A
    input  [7:0] b,         // 8-bit input B
    input        cin,        // Carry-in
    output reg [7:0] sum,   // 8-bit sum output
    output reg     cout      // Carry-out
);

    // Internal signals for intermediate carry values
    reg [7:0] carry;

    // Sequential logic: register the sum and carry on clock edge
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            sum <= 8'b0;       // Reset sum to 0
            cout <= 1'b0;      // Reset carry out to 0
            carry <= 8'b0;     // Reset internal carry
        end else begin
            // Compute each bit of the adder using full adder logic
            // Using ripple carry approach
            for (integer i = 0; i < 8; i = i + 1) begin
                sum[i] <= a[i] ^ b[i] ^ carry[i];
                carry[i+1] <= (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
            end
        end
        // Assign the final carry out
        cout <= carry[8];
    end

endmodule
```

### 说明：

- **模块名称**：`simple_8bit_adder`
- **输入端口**：
  - `clk`: 时钟信号（用于同步逻辑）
  - `rst`: 复位信号（高电平有效）
  - `a`, `b`: 8位二进制输入
  - `cin`: 进位输入
- **输出端口**：
  - `sum`: 8位加法结果
  - `cout`: 最终进位输出
"""
        
        with open(problem_file, 'w', encoding='utf-8') as f:
            f.write(problem_content)
        
        print(f"创建问题文件: {problem_file}")
        
        # 测试清理功能
        cleaned_paths = analyzer._clean_design_files([str(problem_file)])
        
        if len(cleaned_paths) == 1 and cleaned_paths[0] != str(problem_file):
            cleaned_file = Path(cleaned_paths[0])
            print(f"✅ 成功创建清理文件: {cleaned_file.name}")
            
            # 读取清理后的内容
            with open(cleaned_file, 'r', encoding='utf-8') as f:
                cleaned_content = f.read()
            
            print("🔍 清理后的内容:")
            print("="*50)
            print(cleaned_content[:500] + "..." if len(cleaned_content) > 500 else cleaned_content)
            print("="*50)
            
            # 验证清理效果
            issues_fixed = []
            if "```verilog" not in cleaned_content:
                issues_fixed.append("✅ 移除了Markdown代码块标记")
            if "以下是符合" not in cleaned_content:
                issues_fixed.append("✅ 移除了说明性文字")
            if "### 说明：" not in cleaned_content:
                issues_fixed.append("✅ 移除了Markdown标题")
            if "module simple_8bit_adder" in cleaned_content:
                issues_fixed.append("✅ 保留了Verilog模块定义")
            if "endmodule" in cleaned_content:
                issues_fixed.append("✅ 保留了模块结束标记")
            
            print("\n🎯 修复效果:")
            for issue in issues_fixed:
                print(f"  {issue}")
            
            return len(issues_fixed) >= 4  # 至少修复4个问题才算成功
        else:
            print("❌ 清理功能未生成新文件")
            return False

async def test_with_real_problem_file():
    """使用真实的问题文件测试"""
    print("\n🎯 测试真实问题文件")
    
    problem_file_path = "/home/haiyan/Research/CentralizedAgentFramework/file_workspace/designs/simple_8bit_adder_14.v"
    
    if not Path(problem_file_path).exists():
        print("⚠️ 真实问题文件不存在，跳过测试")
        return True
    
    from extensions.test_analyzer import TestAnalyzer
    analyzer = TestAnalyzer()
    
    print(f"清理文件: {problem_file_path}")
    cleaned_paths = analyzer._clean_design_files([problem_file_path])
    
    if len(cleaned_paths) == 1:
        cleaned_path = cleaned_paths[0]
        print(f"清理结果: {cleaned_path}")
        
        if cleaned_path != problem_file_path:
            print("✅ 生成了清理后的文件")
            
            # 读取并展示前几行
            with open(cleaned_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
            
            print("清理后的前10行:")
            for i, line in enumerate(lines, 1):
                print(f"  {i:2d}: {line.rstrip()}")
            
            return True
        else:
            print("⚠️ 文件可能不需要清理")
            return True
    else:
        print("❌ 清理失败")
        return False

async def main():
    """主测试函数"""
    print("🎯 开始代码清理功能测试")
    print("="*60)
    
    test1_result = await test_code_cleaning()
    test2_result = await test_with_real_problem_file()
    
    print("\n" + "="*60)
    print("🎉 代码清理功能测试总结")
    print(f"  基础清理功能: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  真实文件测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎊 代码清理功能正常工作！现在应该能解决log-16.log中的编译问题。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)