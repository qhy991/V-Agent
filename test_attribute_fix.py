#!/usr/bin/env python3
"""
测试属性错误修复
==================================================

这个脚本用于测试修复后的UnifiedTDDTest类是否不再出现AttributeError
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_tdd_test import UnifiedTDDTest

def test_basic_initialization():
    """测试基本初始化"""
    print("🧪 测试基本初始化...")
    
    # 测试默认参数
    tdd = UnifiedTDDTest()
    assert hasattr(tdd, 'design_type'), "缺少design_type属性"
    assert hasattr(tdd, 'custom_config'), "缺少custom_config属性"
    assert tdd.design_type == "alu", f"design_type应该是'alu'，实际是'{tdd.design_type}'"
    assert tdd.custom_config is None, f"custom_config应该是None，实际是{tdd.custom_config}"
    print("✅ 默认参数初始化测试通过")

def test_custom_config():
    """测试自定义配置"""
    print("🧪 测试自定义配置...")
    
    custom_config = {
        'max_iterations': 5,
        'timeout_per_iteration': 180,
        'deep_analysis': True
    }
    
    tdd = UnifiedTDDTest(
        design_type="simple_adder",
        config_profile="quick",
        custom_config=custom_config
    )
    
    assert tdd.custom_config == custom_config, "custom_config未正确保存"
    assert tdd.design_type == "simple_adder", "design_type未正确设置"
    assert tdd.config_profile == "quick", "config_profile未正确设置"
    print("✅ 自定义配置测试通过")

def test_validation():
    """测试配置验证"""
    print("🧪 测试配置验证...")
    
    # 测试有效配置
    tdd = UnifiedTDDTest(design_type="simple_adder")
    try:
        tdd._validate_experiment_config()
        print("✅ 有效配置验证通过")
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")
        return False
    
    # 测试无效设计类型
    try:
        tdd.design_type = "invalid_design"
        tdd._validate_experiment_config()
        print("❌ 无效设计类型验证应该失败")
        return False
    except ValueError as e:
        print("✅ 无效设计类型验证正确失败")
    
    # 测试无效配置档案
    try:
        tdd.design_type = "simple_adder"
        tdd.config_profile = "invalid_profile"
        tdd._validate_experiment_config()
        print("❌ 无效配置档案验证应该失败")
        return False
    except ValueError as e:
        print("✅ 无效配置档案验证正确失败")
    
    return True

def test_custom_config_validation():
    """测试自定义配置验证"""
    print("🧪 测试自定义配置验证...")
    
    # 测试无效的max_iterations
    try:
        tdd = UnifiedTDDTest(
            design_type="simple_adder",
            custom_config={'max_iterations': 0}
        )
        tdd._validate_experiment_config()
        print("❌ 无效max_iterations验证应该失败")
        return False
    except ValueError as e:
        print("✅ 无效max_iterations验证正确失败")
    
    # 测试无效的timeout_per_iteration
    try:
        tdd = UnifiedTDDTest(
            design_type="simple_adder",
            custom_config={'timeout_per_iteration': 10}
        )
        tdd._validate_experiment_config()
        print("❌ 无效timeout_per_iteration验证应该失败")
        return False
    except ValueError as e:
        print("✅ 无效timeout_per_iteration验证正确失败")
    
    # 测试无效的deep_analysis
    try:
        tdd = UnifiedTDDTest(
            design_type="simple_adder",
            custom_config={'deep_analysis': "not_a_bool"}
        )
        tdd._validate_experiment_config()
        print("❌ 无效deep_analysis验证应该失败")
        return False
    except ValueError as e:
        print("✅ 无效deep_analysis验证正确失败")
    
    return True

def main():
    """主测试函数"""
    print("🔧 测试AttributeError修复")
    print("=" * 50)
    
    try:
        test_basic_initialization()
        test_custom_config()
        
        if test_validation():
            print("✅ 配置验证测试通过")
        else:
            print("❌ 配置验证测试失败")
            return False
        
        if test_custom_config_validation():
            print("✅ 自定义配置验证测试通过")
        else:
            print("❌ 自定义配置验证测试失败")
            return False
        
        print("\n🎉 所有测试通过！AttributeError修复成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 