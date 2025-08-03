#!/usr/bin/env python3
"""
测试代码提取功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.base_agent import BaseAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from config.config import FrameworkConfig

def test_code_extraction():
    """测试代码提取功能"""
    print("🧪 测试代码提取功能")
    print("=" * 60)
    
    # 创建代理实例
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 测试用例1: 包含Markdown格式的Verilog代码
    test_content_1 = """
以下是为 `adder_16bit` 模块设计的**专业、完整且结构清晰的Verilog测试台（testbench）**，满足所有指定的要求：

---

## ✅ **Testbench: adder_16bit_tb.v**

```verilog
`timescale 1ns / 1ps

module adder_16bit_tb;

    // 参数定义
    parameter CLK_PERIOD = 10.0; // 时钟周期 10ns

    // 信号声明
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // 被测模块实例化
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // 测试主程序
    initial begin
        $display("=== Starting Testbench for adder_16bit ===");
        
        // 波形转储设置
        $dumpfile("adder_16bit_tb.vcd");
        $dumpvars(0, adder_16bit_tb);
        
        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #10;

        // 基本加法测试
        $display("=== Test Case: basic_addition ===");
        a = 16'h0001; b = 16'h0002; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h0003, 1'b0, 1'b0);

        $display("=== Testbench Finished ===");
        $finish;
    end

    // 结果检查任务
    task check_result;
        input [15:0] a_val, b_val;
        input cin_val;
        input [15:0] expected_sum;
        input expected_cout, expected_overflow;
        
        reg [15:0] actual_sum;
        reg actual_cout, actual_overflow;
        
        begin
            #2; // 等待信号稳定
            
            actual_sum = sum;
            actual_cout = cout;
            actual_overflow = overflow;

            if (actual_sum !== expected_sum) begin
                $display("ERROR: Sum mismatch");
                $display("  a = 0x%04X, b = 0x%04X, cin = %b", a_val, b_val, cin_val);
                $display("  Expected sum = 0x%04X, Actual sum = 0x%04X", expected_sum, actual_sum);
            end else begin
                $display("PASS: Sum matches");
            end
        end
    endtask

    // 实时监控
    initial begin
        $monitor("Time=%0t | a=0x%04X | b=0x%04X | cin=%b | sum=0x%04X | cout=%b | overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

endmodule
```

---

## 🧪 **功能说明与验证覆盖**

### ✅ **主要功能**
- **时钟和复位逻辑**：使用 `initial` 和 `forever` 生成时钟信号，并提供复位。
- **波形转储**：通过 `$dumpfile` 和 `$dumpvars` 生成 VCD 文件用于波形分析。
- **测试场景**：
  - **basic_addition**: 验证基本加法（如 1+2）。
  - **carry_propagation**: 验证进位传播（如 FFFF + 1）。
  - **overflow_detection**: 验证正数+正数溢出或负数+负数溢出。
  - **boundary_values**: 验证边界值（0x0000, 0xFFFF）。
  - **random_data**: 验证随机输入下的正确性。
- **结果检查**：使用 `check_result` 任务进行断言和错误提示。
- **实时监控**：使用 `$monitor` 显示关键信号。

---

## 📊 **测试报告输出示例**

```
=== Starting Testbench for adder_16bit ===
=== Test Case: basic_addition ===
PASS: Sum matches at test case 0
PASS: Cout matches at test case 0
PASS: Overflow matches at test case 0
=== Test Case: carry_propagation ===
PASS: Sum matches at test case 1
PASS: Cout matches at test case 1
PASS: Overflow matches at test case 1
=== Test Case: overflow_detection ===
PASS: Sum matches at test case 2
PASS: Cout matches at test case 2
PASS: Overflow matches at test case 2
...
=== Testbench Finished ===
```

---

## 📁 **文件结构建议**

- `adder_16bit.v`: 被测模块
- `full_adder.v`: 全加器模块
- `adder_16bit_tb.v`: 测试台
- `adder_16bit_tb.vcd`: 波形转储文件（用于仿真查看）

---

## 🔍 **注意事项**

- 如果使用 ModelSim 或 QuestaSim，可以加载 `.vcd` 文件查看波形。
- 可以通过修改 `CLK_PERIOD` 来调整仿真速度。
- 若需要覆盖率收集，可以启用 `$coverage` 相关指令（但根据要求已禁用）。

---

如需进一步扩展（如加入覆盖率收集、更复杂的激励生成等），也可以继续优化此测试台。是否需要我为你生成一个带有覆盖率收集的版本？
"""
    
    print("📝 测试用例1: 包含Markdown格式的Verilog代码")
    print("-" * 40)
    
    # 提取代码
    extracted_code = agent.extract_verilog_code(test_content_1)
    
    print(f"原始内容长度: {len(test_content_1)}")
    print(f"提取后长度: {len(extracted_code)}")
    print(f"提取比例: {len(extracted_code)/len(test_content_1)*100:.1f}%")
    
    print("\n📋 提取的代码前10行:")
    print("-" * 40)
    lines = extracted_code.split('\n')[:10]
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line}")
    
    print("\n" + "=" * 60)
    
    # 测试用例2: 纯Verilog代码
    test_content_2 = """
`timescale 1ns / 1ps

module simple_test;
    input clk;
    output reg [7:0] count;
    
    always @(posedge clk) begin
        count <= count + 1;
    end
endmodule
"""
    
    print("📝 测试用例2: 纯Verilog代码")
    print("-" * 40)
    
    extracted_code_2 = agent.extract_verilog_code(test_content_2)
    
    print(f"原始内容长度: {len(test_content_2)}")
    print(f"提取后长度: {len(extracted_code_2)}")
    print(f"是否相同: {extracted_code_2 == test_content_2.strip()}")
    
    print("\n📋 提取的代码:")
    print("-" * 40)
    print(extracted_code_2)
    
    print("\n" + "=" * 60)
    
    # 测试用例3: 无效内容
    test_content_3 = """
这是一个无效的测试内容，不包含任何Verilog代码。

## 标题1
### 标题2
**粗体文本**
- 列表项1
- 列表项2

这里没有任何代码块或module声明。
"""
    
    print("📝 测试用例3: 无效内容")
    print("-" * 40)
    
    extracted_code_3 = agent.extract_verilog_code(test_content_3)
    
    print(f"原始内容长度: {len(test_content_3)}")
    print(f"提取后长度: {len(extracted_code_3)}")
    print(f"是否返回原始内容: {extracted_code_3 == test_content_3.strip()}")
    
    print("\n📋 提取结果:")
    print("-" * 40)
    print(extracted_code_3[:100] + "..." if len(extracted_code_3) > 100 else extracted_code_3)
    
    print("\n" + "=" * 60)
    print("✅ 代码提取功能测试完成！")

if __name__ == "__main__":
    test_code_extraction() 