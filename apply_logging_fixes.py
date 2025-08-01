#!/usr/bin/env python3
"""
强制应用日志修复 - 立即生效的修复脚本
"""

import sys
import importlib
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def force_reload_logging_system():
    """强制重新加载日志系统，应用修复"""
    print("🔄 强制重新加载日志系统...")
    
    # 方法1: 完全重置日志系统
    try:
        import core.enhanced_logging_config
        core.enhanced_logging_config.reset_logging_system()
        print("  ✅ 使用内置重置功能")
    except Exception as e:
        print(f"  ⚠️ 内置重置失败: {e}")
        
        # 方法2: 手动清理
        modules_to_reload = [
            'core.enhanced_logging_config',
            'llm_integration.enhanced_llm_client',
            'core.centralized_coordinator',
            'agents.real_verilog_agent',
            'agents.real_code_reviewer'
        ]
        
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                print(f"  🔄 重新加载模块: {module_name}")
                importlib.reload(sys.modules[module_name])
            else:
                print(f"  ⚠️ 模块未加载: {module_name}")
        
        # 特别处理日志管理器全局变量
        import core.enhanced_logging_config
        core.enhanced_logging_config._logger_manager = None
        print("  ✅ 清理日志管理器缓存")
    
    print("✅ 日志系统重新加载完成")

def verify_logging_fixes():
    """验证日志修复是否正确应用"""
    print("\n🔍 验证日志修复...")
    
    from core.enhanced_logging_config import ComponentLoggerManager
    
    # 创建新的日志管理器实例
    manager = ComponentLoggerManager("test_fixes")
    
    # 检查协调器映射
    component_mapping = {
        'Agent.centralized_coordinator': 'coordinator',
        'Agent.real_verilog_design_agent': 'base_agent',
        'enhanced_llm_client': 'enhanced_llm_client'
    }
    
    print("📋 验证日志器映射:")
    for logger_name, expected_component in component_mapping.items():
        try:
            logger = manager.get_component_logger(expected_component, logger_name)
            if logger:
                print(f"  ✅ {logger_name} -> {expected_component}")
            else:
                print(f"  ❌ {logger_name} -> 映射失败")
        except Exception as e:
            print(f"  ❌ {logger_name} -> 错误: {e}")
    
    print("✅ 日志映射验证完成")

if __name__ == "__main__":
    print("🔧 应用日志修复...")
    force_reload_logging_system()
    verify_logging_fixes()
    print("\n🎉 日志修复应用完成！现在可以运行你的测试脚本了。")