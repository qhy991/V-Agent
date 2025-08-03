#!/usr/bin/env python3
"""
TDD文件管理修复脚本
修复现有实验目录中缺失的设计文件和测试台文件
"""

import os
import shutil
import time
from pathlib import Path
import re

def fix_experiment_files():
    """修复TDD实验目录中的文件"""
    
    project_root = Path(__file__).parent
    tdd_experiments_dir = project_root / "tdd_experiments"
    file_workspace = project_root / "file_workspace"
    
    print("🔧 开始修复TDD实验文件...")
    
    # 遍历所有实验目录
    for exp_dir in tdd_experiments_dir.glob("unified_tdd_*"):
        if not exp_dir.is_dir():
            continue
            
        artifacts_dir = exp_dir / "artifacts"
        if not artifacts_dir.exists():
            artifacts_dir.mkdir(parents=True)
            
        # 检查是否为空目录
        existing_files = list(artifacts_dir.glob("*.v"))
        if existing_files:
            print(f"✅ {exp_dir.name}: 已有 {len(existing_files)} 个文件，跳过")
            continue
            
        print(f"🔧 修复 {exp_dir.name}...")
        
        # 从目录名提取设计类型和时间戳
        match = re.match(r'unified_tdd_([^_]+)(?:_(\w+))?_(\d+)', exp_dir.name)
        if not match:
            print(f"⚠️ 无法解析目录名: {exp_dir.name}")
            continue
            
        design_type = match.group(1)
        design_variant = match.group(2) if match.group(2) else ""
        timestamp = int(match.group(3))
        
        # 构建完整的设计类型名称
        if design_variant:
            full_design_type = f"{design_type}_{design_variant}"
        else:
            full_design_type = design_type
            
        print(f"   设计类型: {full_design_type}, 时间戳: {timestamp}")
        
        # 时间窗口：实验前后10分钟
        time_start = timestamp - 600
        time_end = timestamp + 600
        
        copied_count = 0
        
        # 复制设计文件
        design_dir = file_workspace / "designs"
        if design_dir.exists():
            patterns = [
                f"*{full_design_type}*",
                f"*{design_type}*",
                f"*{design_variant}*" if design_variant else None
            ]
            patterns = [p for p in patterns if p]
            
            for pattern in patterns:
                for file_path in design_dir.glob(f"{pattern}.v"):
                    file_time = file_path.stat().st_mtime
                    if time_start <= file_time <= time_end:
                        dest_path = artifacts_dir / file_path.name
                        if not dest_path.exists():
                            shutil.copy2(file_path, dest_path)
                            copied_count += 1
                            print(f"     📁 复制设计: {file_path.name}")
        
        # 复制测试台文件
        testbench_dir = file_workspace / "testbenches"
        if testbench_dir.exists():
            patterns = [
                f"*{full_design_type}*tb*.v",
                f"*{design_type}*tb*.v",
                f"*{design_variant}*tb*.v" if design_variant else None
            ]
            patterns = [p for p in patterns if p]
            
            for pattern in patterns:
                for file_path in testbench_dir.glob(pattern):
                    file_time = file_path.stat().st_mtime
                    if time_start <= file_time <= time_end:
                        dest_path = artifacts_dir / file_path.name
                        if not dest_path.exists():
                            shutil.copy2(file_path, dest_path)
                            copied_count += 1
                            print(f"     📁 复制测试台: {file_path.name}")
        
        if copied_count > 0:
            print(f"   ✅ 成功复制 {copied_count} 个文件")
        else:
            print(f"   ⚠️ 未找到匹配的文件")
    
    print("🎉 TDD文件修复完成！")

def create_example_design_files():
    """为没有设计文件的实验创建示例设计文件"""
    
    design_templates = {
        "adder_16bit": """module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    // 16位行波进位加法器
    wire [16:0] carry;
    assign carry[0] = cin;
    
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : full_adder_stage
            assign sum[i] = a[i] ^ b[i] ^ carry[i];
            assign carry[i+1] = (a[i] & b[i]) | (carry[i] & (a[i] ^ b[i]));
        end
    endgenerate
    
    assign cout = carry[16];
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule""",
        
        "simple_adder": """module simple_8bit_adder (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);

    assign {cout, sum} = a + b + cin;

endmodule""",

        "counter": """module counter_8bit (
    input        clk,
    input        rst_n,
    input        enable,
    input        up_down,
    output [7:0] count,
    output       overflow
);

    reg [7:0] counter_reg;
    reg overflow_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter_reg <= 8'h00;
            overflow_reg <= 1'b0;
        end else if (enable) begin
            if (up_down) begin
                {overflow_reg, counter_reg} <= counter_reg + 1;
            end else begin
                {overflow_reg, counter_reg} <= counter_reg - 1;
            end
        end
    end

    assign count = counter_reg;
    assign overflow = overflow_reg;

endmodule"""
    }
    
    project_root = Path(__file__).parent
    tdd_experiments_dir = project_root / "tdd_experiments"
    
    for exp_dir in tdd_experiments_dir.glob("unified_tdd_*"):
        if not exp_dir.is_dir():
            continue
            
        artifacts_dir = exp_dir / "artifacts"
        if not artifacts_dir.exists():
            continue
            
        # 检查是否有设计文件
        design_files = list(artifacts_dir.glob("*.v"))
        if not design_files:
            continue
            
        # 检查是否有测试台但没有设计文件
        has_testbench = any("tb" in f.name for f in design_files)
        has_design = any("tb" not in f.name for f in design_files)
        
        if has_testbench and not has_design:
            # 从目录名提取设计类型
            match = re.match(r'unified_tdd_([^_]+)(?:_(\w+))?_(\d+)', exp_dir.name)
            if match:
                design_type = match.group(1)
                design_variant = match.group(2) if match.group(2) else ""
                
                if design_variant:
                    full_design_type = f"{design_type}_{design_variant}"
                else:
                    full_design_type = design_type
                
                # 查找匹配的模板
                template_key = None
                for key in design_templates:
                    if key in full_design_type or full_design_type in key:
                        template_key = key
                        break
                
                if template_key:
                    design_content = design_templates[template_key]
                    design_file = artifacts_dir / f"{full_design_type}.v"
                    
                    with open(design_file, 'w', encoding='utf-8') as f:
                        f.write(design_content)
                    
                    print(f"✅ 为 {exp_dir.name} 创建设计文件: {design_file.name}")

if __name__ == "__main__":
    fix_experiment_files()
    create_example_design_files()
    print("\n🎉 所有修复操作完成！")