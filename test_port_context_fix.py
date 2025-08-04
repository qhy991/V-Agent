#!/usr/bin/env python3
"""
测试端口上下文传递修复效果
==================================================

这个脚本用于验证修复后的端口上下文传递机制是否正常工作
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.port_validator import port_validator
from core.file_manager import CentralFileManager
from core.context_manager import FullContextManager


def test_port_extraction():
    """测试端口信息提取"""
    print("🧪 测试端口信息提取...")
    
    # 测试设计文件
    design_content = """
module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志
);

    assign result = (op == 4'b0000) ? a + b :
                   (op == 4'b0001) ? a - b :
                   (op == 4'b0010) ? a & b :
                   (op == 4'b0011) ? a | b :
                   (op == 4'b0100) ? a ^ b :
                   (op == 4'b0101) ? a << b[4:0] :
                   (op == 4'b0110) ? a >> b[4:0] :
                   32'b0;

    assign zero = (result == 32'b0) ? 1'b1 : 1'b0;

endmodule
"""
    
    # 提取端口信息
    module_info = port_validator.extract_module_ports(design_content, "alu_32bit.v")
    
    if module_info:
        print(f"✅ 成功提取模块信息:")
        print(f"   模块名: {module_info.name}")
        print(f"   端口数: {module_info.port_count}")
        print(f"   端口列表:")
        for port in module_info.ports:
            print(f"     - {port.direction} [{port.width-1}:0] {port.name}")
        return module_info
    else:
        print("❌ 端口信息提取失败")
        return None


def test_port_validation():
    """测试端口验证"""
    print("\n🧪 测试端口验证...")
    
    # 获取设计模块信息
    module_info = test_port_extraction()
    if not module_info:
        return
    
    # 测试台内容（有错误的端口连接）
    testbench_content = """
module testbench_alu_32bit;
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire carry_out;  // 错误的端口名，应该是 zero
    
    // 实例化ALU
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .carry_out(carry_out)  // 错误的端口连接
    );
    
    // 测试代码...
    initial begin
        // 测试用例
    end
endmodule
"""
    
    # 验证端口一致性
    validation_result = port_validator.validate_testbench_ports(testbench_content, module_info)
    
    print(f"端口验证结果:")
    print(f"   验证通过: {validation_result.get('valid', False)}")
    print(f"   缺失端口: {validation_result.get('missing_ports', [])}")
    print(f"   多余端口: {validation_result.get('extra_ports', [])}")
    
    # 生成详细报告
    report = port_validator.generate_port_report(validation_result)
    print(f"\n详细报告:\n{report}")
    
    return validation_result


def test_auto_fix():
    """测试自动修复"""
    print("\n🧪 测试自动修复...")
    
    # 获取设计模块信息
    module_info = test_port_extraction()
    if not module_info:
        return
    
    # 有错误的测试台内容
    testbench_content = """
module testbench_alu_32bit;
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire carry_out;
    
    // 实例化ALU（有错误的端口连接）
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .carry_out(carry_out)  // 错误的端口
    );
    
    initial begin
        $display("Testing ALU...");
    end
endmodule
"""
    
    # 自动修复
    fixed_content = port_validator.auto_fix_testbench_ports(testbench_content, module_info)
    
    if fixed_content:
        print("✅ 自动修复成功!")
        print("修复后的测试台内容:")
        print(fixed_content)
        
        # 验证修复后的内容
        validation_result = port_validator.validate_testbench_ports(fixed_content, module_info)
        print(f"\n修复后验证结果: {validation_result['valid']}")
        
        return fixed_content
    else:
        print("❌ 自动修复失败")
        return None


def test_file_manager_integration():
    """测试文件管理器集成"""
    print("\n🧪 测试文件管理器集成...")
    
    # 创建文件管理器
    file_manager = CentralFileManager()
    
    # 设计文件内容
    design_content = """
module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output [31:0] result,
    output        zero
);
    assign result = (op == 4'b0000) ? a + b : 32'b0;
    assign zero = (result == 32'b0) ? 1'b1 : 1'b0;
endmodule
"""
    
    # 保存设计文件
    design_ref = file_manager.save_file(
        content=design_content,
        filename="alu_32bit.v",
        file_type="verilog",
        created_by="test_agent",
        description="32位ALU设计"
    )
    
    print(f"✅ 设计文件已保存:")
    print(f"   文件ID: {design_ref.file_id}")
    print(f"   端口信息: {design_ref.port_info}")
    
    # 获取端口信息
    port_info = file_manager.get_design_port_info("alu_32bit")
    if port_info:
        print(f"✅ 成功获取端口信息:")
        print(f"   模块名: {port_info['module_name']}")
        print(f"   端口数: {port_info['port_count']}")
    
    return design_ref


def test_context_manager_integration():
    """测试上下文管理器集成"""
    print("\n🧪 测试上下文管理器集成...")
    
    # 创建上下文管理器
    context_manager = FullContextManager("test_session")
    context_manager.start_new_iteration(1)
    
    # 添加端口信息
    port_info = {
        "module_name": "alu_32bit",
        "ports": [
            {"name": "a", "direction": "input", "width": 32},
            {"name": "b", "direction": "input", "width": 32},
            {"name": "op", "direction": "input", "width": 4},
            {"name": "result", "direction": "output", "width": 32},
            {"name": "zero", "direction": "output", "width": 1}
        ],
        "port_count": 5
    }
    
    context_manager.add_port_info("alu_32bit", port_info)
    
    # 获取端口信息
    retrieved_port_info = context_manager.get_port_info("alu_32bit")
    if retrieved_port_info:
        print(f"✅ 上下文管理器端口信息:")
        print(f"   模块名: {retrieved_port_info['module_name']}")
        print(f"   端口数: {retrieved_port_info['port_count']}")
    
    # 测试端口验证
    testbench_content = """
module testbench;
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
endmodule
"""
    
    validation_result = context_manager.validate_port_consistency("alu_32bit", testbench_content)
    print(f"✅ 端口一致性验证: {validation_result['valid']}")
    
    return context_manager


async def main():
    """主测试函数"""
    print("🚀 开始测试端口上下文传递修复效果")
    print("=" * 50)
    
    # 测试端口提取
    test_port_extraction()
    
    # 测试端口验证
    test_port_validation()
    
    # 测试自动修复
    test_auto_fix()
    
    # 测试文件管理器集成
    test_file_manager_integration()
    
    # 测试上下文管理器集成
    test_context_manager_integration()
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成!")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    asyncio.run(main()) 