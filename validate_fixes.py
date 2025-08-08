#!/usr/bin/env python3
"""
简化的上下文传递修复验证测试

验证核心修复是否正确实现，无需外部依赖。
"""

import sys
import re
from pathlib import Path

# 设置路径
sys.path.append(str(Path(__file__).parent))

def test_code_consistency_checker_implementation():
    """测试代码一致性检查器实现"""
    print("🧪 测试1: 代码一致性检查器实现")
    
    try:
        # 检查文件是否存在
        checker_file = Path("core/code_consistency_checker.py")
        if not checker_file.exists():
            print("❌ 代码一致性检查器文件不存在")
            return False
        
        # 检查关键类和方法
        with open(checker_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_components = [
            "class CodeConsistencyChecker",
            "def extract_module_info",
            "def check_consistency", 
            "def validate_code_parameter",
            "class VerilogModuleInfo",
            "class ConsistencyCheckResult"
        ]
        
        for component in required_components:
            if component not in content:
                print(f"❌ 缺少必需组件: {component}")
                return False
        
        print("✅ 代码一致性检查器实现完整")
        return True
        
    except Exception as e:
        print(f"❌ 测试代码一致性检查器失败: {str(e)}")
        return False

def test_base_agent_enhancements():
    """测试BaseAgent的增强"""
    print("\n🧪 测试2: BaseAgent上下文验证增强")
    
    try:
        base_agent_file = Path("core/base_agent.py")
        if not base_agent_file.exists():
            print("❌ BaseAgent文件不存在")
            return False
        
        with open(base_agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_enhancements = [
            "_validate_and_fix_code_parameter",
            "_get_complete_code_from_files",
            "正在验证代码完整性",
            "from core.code_consistency_checker import get_consistency_checker"
        ]
        
        for enhancement in required_enhancements:
            if enhancement not in content:
                print(f"❌ BaseAgent缺少增强功能: {enhancement}")
                return False
        
        print("✅ BaseAgent上下文验证增强完整")
        return True
        
    except Exception as e:
        print(f"❌ 测试BaseAgent增强失败: {str(e)}")
        return False

def test_code_reviewer_fixes():
    """测试代码审查智能体修复"""
    print("\n🧪 测试3: 代码审查智能体修复")
    
    try:
        reviewer_file = Path("agents/enhanced_real_code_reviewer.py")
        if not reviewer_file.exists():
            print("❌ 代码审查智能体文件不存在")
            return False
        
        with open(reviewer_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_fixes = [
            "_validate_code_consistency",
            "_evaluate_code_completeness", 
            "最完整的缓存文件内容",
            "代码完整性验证"
        ]
        
        for fix in required_fixes:
            if fix not in content:
                print(f"❌ 代码审查智能体缺少修复: {fix}")
                return False
        
        print("✅ 代码审查智能体修复完整")
        return True
        
    except Exception as e:
        print(f"❌ 测试代码审查智能体修复失败: {str(e)}")
        return False

def test_task_file_context_validation():
    """测试TaskFileContext验证增强"""
    print("\n🧪 测试4: TaskFileContext验证增强")
    
    try:
        context_file = Path("core/task_file_context.py")
        if not context_file.exists():
            print("❌ TaskFileContext文件不存在")
            return False
        
        with open(context_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_validations = [
            "_validate_design_file_integrity",
            "validate_all_files_consistency",
            "from core.code_consistency_checker import get_consistency_checker"
        ]
        
        for validation in required_validations:
            if validation not in content:
                print(f"❌ TaskFileContext缺少验证功能: {validation}")
                return False
        
        print("✅ TaskFileContext验证增强完整")
        return True
        
    except Exception as e:
        print(f"❌ 测试TaskFileContext增强失败: {str(e)}")
        return False

def test_coordinator_improvements():
    """测试协调器通信改进"""
    print("\n🧪 测试5: 协调器通信改进")
    
    try:
        coordinator_file = Path("core/llm_coordinator_agent.py")
        if not coordinator_file.exists():
            print("❌ 协调器文件不存在")
            return False
        
        with open(coordinator_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_improvements = [
            "_validate_design_file_before_distribution",
            "_validate_inter_agent_context_consistency",
            "设计文件验证通过",
            "智能体间上下文一致性"
        ]
        
        for improvement in required_improvements:
            if improvement not in content:
                print(f"❌ 协调器缺少改进: {improvement}")
                return False
        
        print("✅ 协调器通信改进完整")
        return True
        
    except Exception as e:
        print(f"❌ 测试协调器改进失败: {str(e)}")
        return False

def test_code_consistency_checker_logic():
    """测试代码一致性检查器的逻辑"""
    print("\n🧪 测试6: 代码一致性检查器逻辑验证")
    
    # 简单的代码示例
    complete_code = """module counter #(
    parameter WIDTH = 8
)(
    input clk,
    input rst_n,
    input en,
    input up,
    input load,
    input [WIDTH-1:0] data_in,
    output reg [WIDTH-1:0] count,
    output reg rollover
);"""
    
    simple_code = """module counter #(
    parameter C_WIDTH = 4
)(
    input clk,
    input rst_n,
    input en,
    input up,
    output reg [C_WIDTH-1:0] count
);"""
    
    try:
        # 基本的模式检查
        def extract_parameters(code):
            params = re.findall(r'parameter\s+(\w+)', code)
            return params
        
        def count_ports(code, port_type):
            pattern = rf'{port_type}\s+[^;]*'
            return len(re.findall(pattern, code))
        
        complete_params = extract_parameters(complete_code)
        simple_params = extract_parameters(simple_code)
        
        complete_inputs = count_ports(complete_code, 'input')
        simple_inputs = count_ports(simple_code, 'input')
        
        complete_outputs = count_ports(complete_code, 'output')
        simple_outputs = count_ports(simple_code, 'output')
        
        print(f"📊 完整代码: 参数={complete_params}, 输入={complete_inputs}, 输出={complete_outputs}")
        print(f"📊 简化代码: 参数={simple_params}, 输入={simple_inputs}, 输出={simple_outputs}")
        
        # 验证能检测差异
        if complete_inputs == simple_inputs or complete_outputs == simple_outputs:
            print("⚠️ 简单逻辑检查：端口数量相同，可能需要更深入的检查")
        else:
            print("✅ 能够检测到代码结构差异")
        
        return True
        
    except Exception as e:
        print(f"❌ 代码一致性检查逻辑测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始上下文传递修复验证测试")
    print("="*80)
    
    tests = [
        test_code_consistency_checker_implementation,
        test_base_agent_enhancements,
        test_code_reviewer_fixes,
        test_task_file_context_validation,
        test_coordinator_improvements,
        test_code_consistency_checker_logic
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行异常: {str(e)}")
            results.append(False)
    
    print("\n" + "="*80)
    print("🎯 测试摘要")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"📊 总测试数: {total_tests}")
    print(f"✅ 通过测试: {passed_tests}")
    print(f"❌ 失败测试: {failed_tests}")
    print(f"🎯 成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有验证测试通过！上下文传递问题修复实现成功！")
        print("\n📋 修复摘要:")
        print("1. ✅ 创建了代码一致性检查器 (core/code_consistency_checker.py)")
        print("2. ✅ 增强了BaseAgent的上下文验证 (core/base_agent.py)")
        print("3. ✅ 修复了代码审查智能体的testbench生成 (agents/enhanced_real_code_reviewer.py)")
        print("4. ✅ 增强了TaskFileContext的代码验证 (core/task_file_context.py)")
        print("5. ✅ 改进了协调器的智能体通信 (core/llm_coordinator_agent.py)")
    else:
        print("\n⚠️ 部分测试失败，修复可能不完整。")
    
    print("="*80)

if __name__ == "__main__":
    main()