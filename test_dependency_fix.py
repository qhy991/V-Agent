#!/usr/bin/env python3
"""
快速验证依赖分析修复效果
"""

import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from extensions.verilog_dependency_analyzer import VerilogDependencyAnalyzer
from core.file_manager import initialize_file_manager, get_file_manager


def test_dependency_analyzer():
    """测试修复后的依赖分析器"""
    print("🔍 测试修复后的Verilog依赖分析器")
    print("="*50)
    
    # 创建临时工作空间
    temp_workspace = Path(tempfile.mkdtemp(prefix="dep_test_"))
    initialize_file_manager(temp_workspace)
    file_manager = get_file_manager()
    
    try:
        # 创建问题设计文件（缺少full_adder）
        problematic_content = """module simple_8bit_adder(
    input [7:0] a, b,
    input cin,
    output [7:0] sum,
    output cout
);
    wire [7:0] carry;
    
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );
    
    full_adder fa1 (
        .a(a[1]),
        .b(b[1]),
        .cin(carry[0]),
        .sum(sum[1]),
        .cout(carry[1])
    );
    
    assign cout = carry[7];
endmodule"""

        # 创建完整设计文件（包含full_adder）
        complete_content = """module full_adder(
    input a, b, cin,
    output sum, cout
);
    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (b & cin) | (a & cin);
endmodule

module simple_8bit_adder(
    input [7:0] a, b,
    input cin,
    output [7:0] sum,
    output cout
);
    wire [7:0] carry;
    
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );
    
    full_adder fa1 (
        .a(a[1]),
        .b(b[1]),
        .cin(carry[0]),
        .sum(sum[1]),
        .cout(carry[1])
    );
    
    assign cout = carry[1];
endmodule"""

        # 创建测试台
        testbench_content = """module simple_8bit_adder_tb;
    reg [7:0] a, b;
    reg cin;
    wire [7:0] sum;
    wire cout;
    
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    initial begin
        a = 8'h0F; b = 8'h10; cin = 0; #10;
        $display("Test: %h + %h = %h", a, b, sum);
        $finish;
    end
endmodule"""

        # 保存文件
        problematic_file = file_manager.save_file(
            content=problematic_content,
            filename="problematic.v",
            file_type="verilog",
            created_by="test_script",
            description="问题设计文件"
        )
        
        complete_file = file_manager.save_file(
            content=complete_content,
            filename="complete.v", 
            file_type="verilog",
            created_by="test_script",
            description="完整设计文件"
        )
        
        testbench_file = file_manager.save_file(
            content=testbench_content,
            filename="testbench.v",
            file_type="testbench",
            created_by="test_script",
            description="测试台文件"
        )
        
        # 测试依赖分析器
        analyzer = VerilogDependencyAnalyzer()
        
        print("📋 测试问题文件分析:")
        modules = analyzer.analyze_file(problematic_file.file_path)
        for module in modules:
            print(f"  模块: {module.name}")
            print(f"  依赖: {list(module.dependencies) if module.dependencies else '无'}")
            print(f"  是测试台: {module.is_testbench}")
        
        print("\n📋 测试完整文件分析:")
        modules = analyzer.analyze_file(complete_file.file_path)
        for module in modules:
            print(f"  模块: {module.name}")
            print(f"  依赖: {list(module.dependencies) if module.dependencies else '无'}")
            print(f"  是测试台: {module.is_testbench}")
        
        print("\n📋 测试台文件分析:")
        modules = analyzer.analyze_file(testbench_file.file_path)
        for module in modules:
            print(f"  模块: {module.name}")
            print(f"  依赖: {list(module.dependencies) if module.dependencies else '无'}")
            print(f"  是测试台: {module.is_testbench}")
        
        # 测试兼容性分析
        print("\n🔍 兼容性分析测试:")
        
        print("1. 问题文件 vs 测试台:")
        compatibility = analyzer.analyze_compatibility(
            problematic_file.file_path, testbench_file.file_path
        )
        print(f"   兼容: {compatibility['compatible']}")
        print(f"   设计模块: {compatibility['design_modules']}")
        print(f"   测试台模块: {compatibility['testbench_modules']}")
        print(f"   缺失依赖: {compatibility['missing_dependencies']}")
        if compatibility['issues']:
            print(f"   问题: {compatibility['issues']}")
        
        print("\n2. 完整文件 vs 测试台:")
        compatibility = analyzer.analyze_compatibility(
            complete_file.file_path, testbench_file.file_path
        )
        print(f"   兼容: {compatibility['compatible']}")
        print(f"   设计模块: {compatibility['design_modules']}")
        print(f"   测试台模块: {compatibility['testbench_modules']}")
        print(f"   缺失依赖: {compatibility['missing_dependencies']}")
        if compatibility['issues']:
            print(f"   问题: {compatibility['issues']}")
        
        # 测试修复建议
        print("\n💡 修复建议:")
        suggestions = analyzer.suggest_fixes(compatibility)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print("\n✅ 依赖分析修复测试完成")
        
    finally:
        # 清理
        shutil.rmtree(temp_workspace)


if __name__ == "__main__":
    test_dependency_analyzer()