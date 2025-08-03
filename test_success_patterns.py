#!/usr/bin/env python3
"""
测试成功经验累积机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.context_manager import FullContextManager

def test_success_pattern_learning():
    """测试成功经验累积功能"""
    print("🧪 测试成功经验累积机制")
    
    # 创建上下文管理器
    context_manager = FullContextManager("test_session")
    
    # 开始第一次迭代
    iteration_id = context_manager.start_new_iteration(1)
    print(f"✅ 开始迭代: {iteration_id}")
    
    # 添加一些代码文件
    test_code = """
module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    wire [16:0] carry;  // 正确的17位进位数组
    assign carry[0] = cin;
    assign sum[0] = a[0] ^ b[0] ^ carry[0];
    assign carry[1] = (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);
    
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);
    assign cout = carry[16];

endmodule
"""
    
    context_manager.add_code_file("adder_16bit.v", test_code, "adder_16bit", "design")
    print("✅ 添加代码文件")
    
    # 模拟编译错误（从之前的日志中提取）
    compilation_errors = [
        {
            "file": "adder_16bit.v",
            "line": 19,
            "message": "Index carry[16] is out of range.",
            "type": "array_bounds_error"
        }
    ]
    
    context_manager.add_compilation_errors(compilation_errors)
    print("✅ 添加编译错误")
    
    # 检查错误教训是否被提取
    print("\n📋 提取的错误教训:")
    for lesson in context_manager.global_context["error_lessons"]:
        print(f"  - {lesson}")
    
    # 模拟成功的迭代结果
    success_result = {
        "all_tests_passed": True,
        "design_files": [{"file_path": "adder_16bit.v"}],
        "test_results": {"success": True}
    }
    
    # 开始第二次迭代
    iteration_id2 = context_manager.start_new_iteration(2)
    print(f"\n✅ 开始第二次迭代: {iteration_id2}")
    
    # 添加成功的代码
    success_code = """
module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    wire [16:0] carry;  // 正确的17位进位数组
    assign carry[0] = cin;
    assign sum[0] = a[0] ^ b[0] ^ carry[0];
    assign carry[1] = (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);
    
    // 正确的溢出检测
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);
    assign cout = carry[16];

endmodule
"""
    
    context_manager.add_code_file("adder_16bit.v", success_code, "adder_16bit", "design")
    
    # 提取成功模式
    context_manager.extract_success_patterns(success_result)
    print("✅ 提取成功模式")
    
    # 检查成功模式
    print("\n📋 成功模式:")
    for category, patterns in context_manager.global_context["success_patterns"].items():
        if patterns["correct_patterns"]:
            print(f"\n  {category}:")
            for pattern in patterns["correct_patterns"]:
                print(f"    ✅ {pattern}")
    
    # 构建成功经验上下文
    success_context = context_manager.build_success_context_for_agent()
    print(f"\n🎯 成功经验上下文 (长度: {len(success_context)} 字符):")
    print(success_context[:500] + "..." if len(success_context) > 500 else success_context)
    
    print("\n✅ 成功经验累积机制测试完成！")

if __name__ == "__main__":
    test_success_pattern_learning() 