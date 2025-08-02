#!/usr/bin/env python3
"""
综合TDD实验 - 设计一个带有明确接口规范的FIFO模块
避免之前遇到的问题：
1. 接口不匹配（特别是复位信号命名）
2. 错误反馈不明确
3. 测试台与设计不兼容
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions.test_driven_coordinator import TestDrivenCoordinator
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

def create_fifo_testbench():
    """创建FIFO测试台，避免接口不匹配问题"""
    testbench_content = '''`timescale 1ns / 1ps

//========================================================================
// 同步FIFO测试台 - 严格按照接口规范设计
//========================================================================
module sync_fifo_tb;

    // 测试台参数
    parameter CLK_PERIOD = 10;  // 10ns时钟周期
    parameter DATA_WIDTH = 8;
    parameter FIFO_DEPTH = 16;
    parameter ADDR_WIDTH = 4;   // log2(16) = 4
    
    // 信号声明 - 严格匹配接口规范
    reg                    clk;
    reg                    rst_n;        // 注意：使用rst_n（低电平复位）
    reg                    wr_en;
    reg                    rd_en;
    reg  [DATA_WIDTH-1:0]  wr_data;
    wire [DATA_WIDTH-1:0]  rd_data;
    wire                   full;
    wire                   empty;
    wire [ADDR_WIDTH:0]    count;       // FIFO中数据个数
    
    // 被测模块实例化 - 接口名称必须完全匹配
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(FIFO_DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .clk(clk),           // 时钟
        .rst_n(rst_n),       // 异步复位（低电平有效）- 关键接口
        .wr_en(wr_en),       // 写使能
        .rd_en(rd_en),       // 读使能
        .wr_data(wr_data),   // 写数据
        .rd_data(rd_data),   // 读数据
        .full(full),         // 满标志
        .empty(empty),       // 空标志
        .count(count)        // 计数
    );
    
    // 时钟生成
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    // 测试变量
    integer i;
    reg [DATA_WIDTH-1:0] test_data;
    reg [DATA_WIDTH-1:0] expected_data;
    integer error_count;
    
    // 主测试流程
    initial begin
        $display("=================================================================");
        $display("开始同步FIFO功能测试");
        $display("时间: %0t", $time);
        $display("=================================================================");
        
        // 初始化信号
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        wr_data = 0;
        error_count = 0;
        
        // 复位测试
        $display("\\n--- 测试用例1: 异步复位功能测试 ---");
        #(CLK_PERIOD * 2);
        if (empty !== 1'b1 || full !== 1'b0 || count !== 0) begin
            $display("❌ 复位测试失败: empty=%b, full=%b, count=%d", empty, full, count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 复位测试通过: FIFO正确复位为空状态");
        end
        
        // 释放复位
        rst_n = 1;
        #(CLK_PERIOD);
        
        // 写入测试
        $display("\\n--- 测试用例2: 写入功能测试 ---");
        for (i = 0; i < 8; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            wr_data = 8'hA0 + i;  // 写入测试数据 A0, A1, A2...
            @(posedge clk);
            wr_en = 0;
            #1;  // 等待信号稳定
            $display("写入数据[%0d]: 0x%02X, count=%d, full=%b", i, wr_data, count, full);
        end
        
        // 检查写入后状态
        if (count !== 8) begin
            $display("❌ 写入测试失败: 期望count=8, 实际count=%d", count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 写入测试通过: 成功写入8个数据");
        end
        
        // 读取测试
        $display("\\n--- 测试用例3: 读取功能测试 ---");
        for (i = 0; i < 8; i = i + 1) begin
            expected_data = 8'hA0 + i;
            @(posedge clk);
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            #1;  // 等待信号稳定
            $display("读取数据[%0d]: 0x%02X (期望: 0x%02X), count=%d, empty=%b", 
                    i, rd_data, expected_data, count, empty);
            
            if (rd_data !== expected_data) begin
                $display("❌ 数据不匹配: 读取=0x%02X, 期望=0x%02X", rd_data, expected_data);
                error_count = error_count + 1;
            end
        end
        
        // 检查读取后状态
        if (count !== 0 || empty !== 1'b1) begin
            $display("❌ 读取测试失败: 期望count=0且empty=1, 实际count=%d, empty=%b", count, empty);
            error_count = error_count + 1;
        end else begin
            $display("✅ 读取测试通过: FIFO正确变为空状态");
        end
        
        // 满状态测试
        $display("\\n--- 测试用例4: 满状态测试 ---");
        for (i = 0; i < FIFO_DEPTH; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            wr_data = 8'h10 + i;
            @(posedge clk);
            wr_en = 0;
            #1;
        end
        
        if (full !== 1'b1 || count !== FIFO_DEPTH) begin
            $display("❌ 满状态测试失败: 期望full=1且count=%d, 实际full=%b, count=%d", 
                    FIFO_DEPTH, full, count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 满状态测试通过: FIFO正确检测满状态");
        end
        
        // 溢出保护测试
        $display("\\n--- 测试用例5: 溢出保护测试 ---");
        @(posedge clk);
        wr_en = 1;
        wr_data = 8'hFF;  // 尝试在满状态下写入
        @(posedge clk);
        wr_en = 0;
        #1;
        
        if (count > FIFO_DEPTH) begin
            $display("❌ 溢出保护失败: count=%d 超过了FIFO深度", count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 溢出保护测试通过: 满状态下写入被正确忽略");
        end
        
        // 同时读写测试
        $display("\\n--- 测试用例6: 同时读写测试 ---");
        // 先清空FIFO
        while (!empty) begin
            @(posedge clk);
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            #1;
        end
        
        // 同时进行读写操作
        for (i = 0; i < 5; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            rd_en = (i > 0) ? 1 : 0;  // 第一次只写不读
            wr_data = 8'h20 + i;
            @(posedge clk);
            wr_en = 0;
            rd_en = 0;
            #1;
            $display("同时读写[%0d]: wr_data=0x%02X, rd_data=0x%02X, count=%d", 
                    i, wr_data, rd_data, count);
        end
        
        // 测试总结
        $display("\\n=================================================================");
        if (error_count == 0) begin
            $display("🎉 所有测试通过! FIFO设计功能正确");
        end else begin
            $display("❌ 发现 %0d 个错误，需要修复设计", error_count);
        end
        $display("测试完成时间: %0t", $time);
        $display("=================================================================");
        
        // 生成波形文件
        $dumpfile("sync_fifo_tb.vcd");
        $dumpvars(0, sync_fifo_tb);
        
        #(CLK_PERIOD * 5);
        $finish;
    end
    
    // 监控重要信号变化
    always @(posedge clk) begin
        if (rst_n && (wr_en || rd_en)) begin
            $display("时间 %0t: wr_en=%b, rd_en=%b, wr_data=0x%02X, rd_data=0x%02X, count=%d, full=%b, empty=%b",
                    $time, wr_en, rd_en, wr_data, rd_data, count, full, empty);
        end
    end
    
    // 错误检测
    always @(posedge clk) begin
        if (rst_n) begin
            // 检查count的合理性
            if (count > FIFO_DEPTH) begin
                $display("❌ 错误: count=%d 超过FIFO深度 %d", count, FIFO_DEPTH);
            end
            
            // 检查full和empty的一致性
            if (full && empty) begin
                $display("❌ 错误: full和empty不能同时为1");
            end
            
            if (count == 0 && !empty) begin
                $display("❌ 错误: count=0时empty应该为1");
            end
            
            if (count == FIFO_DEPTH && !full) begin
                $display("❌ 错误: count=FIFO_DEPTH时full应该为1");
            end
        end
    end

endmodule'''

    # 创建测试台文件
    os.makedirs("test_cases", exist_ok=True)
    testbench_path = "test_cases/sync_fifo_tb.v"
    
    with open(testbench_path, 'w', encoding='utf-8') as f:
        f.write(testbench_content)
    
    return os.path.abspath(testbench_path)

async def run_comprehensive_tdd_experiment():
    """运行综合TDD实验"""
    print("🧪 综合TDD实验 - 同步FIFO设计")
    print("=" * 60)
    print("📋 实验目标:")
    print("   1. 测试TDD系统对复杂模块的处理能力")
    print("   2. 验证明确接口规范的重要性")
    print("   3. 检验错误反馈和迭代修复机制")
    print("   4. 避免之前发现的接口不匹配问题")
    print("=" * 60)
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 初始化协调器
    coordinator = EnhancedCentralizedCoordinator(config)
    
    # 注册智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    review_agent = EnhancedRealCodeReviewAgent(config)
    
    coordinator.register_agent(verilog_agent)
    coordinator.register_agent(review_agent)
    
    # 初始化TDD协调器
    tdd_coordinator = TestDrivenCoordinator(coordinator)
    tdd_coordinator.config.max_iterations = 4  # 允许更多迭代来处理复杂设计
    
    # 创建测试台
    testbench_path = create_fifo_testbench()
    print(f"✅ 测试台已创建: {testbench_path}")
    
    # 设计需求 - 基于我们的经验教训，使用非常明确的规范
    design_requirements = """
设计一个参数化的同步FIFO模块sync_fifo，严格按照以下接口规范实现：

**关键要求 - 接口必须完全匹配**:
```verilog
module sync_fifo #(
    parameter DATA_WIDTH = 8,     // 数据位宽
    parameter FIFO_DEPTH = 16,    // FIFO深度
    parameter ADDR_WIDTH = 4      // 地址位宽 (log2(FIFO_DEPTH))
)(
    input                    clk,        // 时钟
    input                    rst_n,      // 异步复位（低电平有效）- 注意是rst_n不是rst！
    input                    wr_en,      // 写使能
    input                    rd_en,      // 读使能
    input  [DATA_WIDTH-1:0]  wr_data,    // 写数据
    output [DATA_WIDTH-1:0]  rd_data,    // 读数据
    output                   full,       // 满标志
    output                   empty,      // 空标志
    output [ADDR_WIDTH:0]    count       // FIFO中数据个数（需要ADDR_WIDTH+1位）
);
```

**功能要求**:
1. **异步复位**: 当rst_n为低电平时，所有指针复位，empty=1, full=0, count=0
2. **写操作**: wr_en=1且!full时，在时钟上升沿写入数据
3. **读操作**: rd_en=1且!empty时，在时钟上升沿读出数据
4. **状态标志**:
   - empty: FIFO为空时为1（count == 0）
   - full: FIFO满时为1（count == FIFO_DEPTH）
   - count: 实时显示FIFO中数据个数
5. **边界保护**: 满时写入无效，空时读出无效

**设计要求**:
- 使用双端口RAM或寄存器阵列实现
- 使用环形缓冲区设计（写指针和读指针）
- 同步设计：所有操作在时钟上升沿进行
- 支持同时读写操作

**严格警告**：
1. 端口名必须严格匹配上述接口，特别是rst_n（不是rst）！
2. 复位逻辑必须是negedge rst_n，复位条件必须是if (!rst_n)！
3. 参数必须正确使用：DATA_WIDTH, FIFO_DEPTH, ADDR_WIDTH
4. count输出必须是[ADDR_WIDTH:0]位宽（比地址多1位）
5. 所有信号命名必须与接口规范完全一致

**测试要求**:
设计必须通过提供的测试台验证，包括：
- 复位功能测试
- 写入/读取功能测试  
- 满/空状态检测
- 溢出保护测试
- 同时读写测试
"""
    
    print("🎯 开始TDD流程...")
    print(f"📋 设计需求: 同步FIFO with严格接口规范")
    
    try:
        # 执行TDD循环
        result = await tdd_coordinator.execute_test_driven_task(
            task_description=design_requirements,
            testbench_path=testbench_path
        )
        
        print("\n" + "=" * 60)
        print("📊 综合TDD实验结果")
        print("=" * 60)
        
        if result.get("success", False):
            print("✅ TDD流程成功完成")
            print(f"📈 总迭代次数: {result.get('iterations_completed', 0)}")
            print(f"⏱️ 总耗时: {result.get('total_duration', 0):.2f} 秒")
            
            # 分析最终设计质量
            print("\n🔍 设计质量分析:")
            if "final_design_files" in result:
                for file_path in result["final_design_files"]:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 检查关键接口
                        interface_checks = {
                            "rst_n端口": "input rst_n" in content and "input rst" not in content.replace("rst_n", ""),
                            "复位逻辑": "negedge rst_n" in content,
                            "复位条件": "if (!rst_n)" in content or "if(!rst_n)" in content,
                            "参数使用": "DATA_WIDTH" in content and "FIFO_DEPTH" in content,
                            "count位宽": "[ADDR_WIDTH:0]" in content
                        }
                        
                        print(f"   📄 {file_path}:")
                        for check, passed in interface_checks.items():
                            status = "✅" if passed else "❌"
                            print(f"      {status} {check}")
            
            return True
        else:
            print("❌ TDD流程失败")
            error_msg = result.get("error", "未知错误")
            print(f"❌ 失败原因: {error_msg}")
            
            # 分析失败迭代
            if "iteration_results" in result:
                print("\n🔍 失败迭代分析:")
                for i, iteration in enumerate(result["iteration_results"], 1):
                    print(f"   第{i}次迭代:")
                    if "compilation_errors" in iteration and iteration["compilation_errors"]:
                        print(f"      📤 编译错误: {iteration['compilation_errors'][:200]}...")
                    if "simulation_errors" in iteration and iteration["simulation_errors"]:
                        print(f"      🔍 仿真错误: {iteration['simulation_errors'][:200]}...")
                    if "improvement_suggestions" in iteration:
                        print(f"      💡 改进建议: {len(iteration['improvement_suggestions'])} 条")
            
            return False
            
    except Exception as e:
        print(f"❌ 实验异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 启动综合TDD实验")
    success = asyncio.run(run_comprehensive_tdd_experiment())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 综合TDD实验成功完成!")
        print("✅ 验证了TDD系统的可靠性和错误反馈机制")
        print("✅ 证明了明确接口规范的重要性")
        print("✅ 展示了系统处理复杂设计的能力")
    else:
        print("💥 综合TDD实验失败")
        print("🔍 需要进一步分析和改进系统")
    
    print("=" * 60)