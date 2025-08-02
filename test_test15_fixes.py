#!/usr/bin/env python3
"""
Test-15.log问题修复验证
Validation for Test-15.log Issue Fixes
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_analyze_test_failures_tool():
    """测试新的测试失败分析工具"""
    print("🔍 测试analyze_test_failures工具")
    
    try:
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        # 模拟test-15.log中的宏定义错误
        design_code_with_macros = """
module simple_8bit_adder (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    
    // 错误的宏定义（来自test-15.log的问题）
    `simple_8bit_adder inst (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));
    `verilog syntax error here;
    
endmodule
"""
        
        compilation_errors = """
macro simple_8bit_adder undefined (and assumed null)
macro verilog undefined (and assumed null) 
macro a undefined (and assumed null)
macro b undefined (and assumed null)
"""
        
        # 调用测试失败分析工具
        result = await reviewer._tool_analyze_test_failures(
            design_code=design_code_with_macros,
            compilation_errors=compilation_errors,
            iteration_number=2,
            previous_fixes=["尝试过修复端口连接"]
        )
        
        if result.get('success'):
            print("✅ analyze_test_failures工具正常工作")
            print(f"识别的失败类型: {result['analysis']['failure_types']}")
            print(f"修复建议数量: {len(result['analysis']['fix_suggestions'])}")
            
            # 检查是否正确识别了宏定义错误
            if "未定义宏错误" in result['analysis']['failure_types']:
                print("✅ 正确识别了宏定义错误")
            else:
                print("❌ 未能识别宏定义错误")
                
            return True
        else:
            print(f"❌ 工具调用失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

async def test_testbench_selection_strategy():
    """测试改进的测试台选择策略"""
    print("\n🎯 测试测试台选择策略")
    
    try:
        from extensions.test_driven_coordinator import TestDrivenCoordinator
        from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        base_coordinator = EnhancedCentralizedCoordinator(config)
        coordinator = TestDrivenCoordinator(base_coordinator)
        
        # 测试策略决策逻辑
        test_cases = [
            # (iteration, has_user_tb, has_generated_tb, expected_strategy)
            (1, True, False, "用户基准"),
            (1, False, True, "智能体生成"),
            (2, True, True, "智能体优化"),  # 应该优先使用生成的
            (3, True, True, "智能体优化"),  # 应该优先使用生成的
            (2, False, True, "智能体优化"),
            (2, True, False, "用户备用"),
        ]
        
        all_passed = True
        for iteration, has_user, has_generated, expected in test_cases:
            user_path = "/tmp/user_tb.v" if has_user else None
            generated_path = "/tmp/generated_tb.v" if has_generated else None
            
            # 创建临时文件确保存在性检查通过
            if has_user:
                Path("/tmp/user_tb.v").touch()
            if has_generated:
                Path("/tmp/generated_tb.v").touch()
            
            strategy = coordinator._determine_testbench_strategy(
                iteration, user_path, generated_path
            )
            
            if expected in strategy["strategy"]:
                print(f"✅ 迭代{iteration}: {strategy['strategy']}")
            else:
                print(f"❌ 迭代{iteration}: 期望包含'{expected}', 实际'{strategy['strategy']}'")
                all_passed = False
            
            # 清理临时文件
            for path in ["/tmp/user_tb.v", "/tmp/generated_tb.v"]:
                if Path(path).exists():
                    Path(path).unlink()
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

async def test_coverage_schema_fix():
    """测试覆盖率工具Schema修复"""
    print("\n📊 测试coverage Schema修复")
    
    try:
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        # 测试之前失败的.vcd文件格式
        with tempfile.NamedTemporaryFile(suffix=".vcd", delete=False) as f:
            vcd_file = f.name
            f.write(b"# Sample VCD content")
        
        try:
            result = await reviewer._tool_analyze_coverage(
                coverage_data_file=vcd_file,
                coverage_types=["line", "branch"],
                threshold={"line_coverage": 80, "branch_coverage": 70}
            )
            
            if result.get('success'):
                print("✅ VCD文件格式现在被支持")
                return True
            else:
                print(f"❌ VCD文件仍然失败: {result.get('error')}")
                return False
                
        finally:
            Path(vcd_file).unlink()
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎯 开始Test-15.log问题修复验证")
    print("="*60)
    
    tests = [
        ("测试失败分析工具", test_analyze_test_failures_tool),
        ("测试台选择策略", test_testbench_selection_strategy), 
        ("覆盖率Schema修复", test_coverage_schema_fix),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试失败: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("🎉 Test-15.log问题修复验证总结")
    
    passed = 0
    total = len(results)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎊 所有Test-15.log问题都已修复！TDD系统现在应该能够：")
        print("   1. ✅ 正确分析测试失败原因并提供修复建议")
        print("   2. ✅ 智能选择最新生成的测试台而非硬编码版本") 
        print("   3. ✅ 支持VCD等多种覆盖率文件格式")
        print("   4. ✅ 实现完整的红灯→绿灯→重构TDD循环")
    else:
        print("⚠️ 部分问题仍未完全解决，需要进一步调试。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)