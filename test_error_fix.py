#!/usr/bin/env python3
"""
测试错误处理修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def test_error_handling_fix():
    """测试错误处理修复是否有效"""
    print("🧪 测试错误处理修复...")
    
    agent = EnhancedRealCodeReviewAgent()
    
    # 测试datetime错误是否已修复
    print("🔍 测试datetime错误修复...")
    try:
        # 模拟一个错误情况
        error_message = "file_workspace/testbenches/testbench_counter.v:76: syntax error"
        error_context = {
            "file_paths": ["counter.v", "testbench_counter.v"],
            "stage": "compilation",
            "simulator": "iverilog",
            "command": "iverilog -o simulation counter.v testbench_counter.v",
            "timestamp": str(time.time()),
            "working_directory": str(Path.cwd())
        }
        
        simulation_result = {
            "success": False,
            "stage": "compilation",
            "return_code": 10,
            "compilation_output": "syntax error in line 76",
            "error_output": "Syntax in assignment statement l-value"
        }
        
        enhanced_error = agent._enhance_error_information(
            error_message=error_message,
            error_context=error_context,
            simulation_result=simulation_result
        )
        
        print(f"✅ datetime错误修复成功")
        print(f"🔍 错误分类: {enhanced_error['error_classification']['error_type']}")
        print(f"🔍 错误严重程度: {enhanced_error['error_classification']['severity']}")
        
    except Exception as e:
        print(f"❌ datetime错误修复失败: {str(e)}")
        return False
    
    # 测试错误分类是否正常工作
    print("\n🔍 测试错误分类功能...")
    try:
        error_info = agent._classify_simulation_error("name 'datetime' is not defined")
        print(f"✅ 错误分类成功")
        print(f"🔍 分类结果: {error_info['error_type']}")
        print(f"🔍 严重程度: {error_info['severity']}")
        
    except Exception as e:
        print(f"❌ 错误分类失败: {str(e)}")
        return False
    
    print("\n✅ 所有测试通过！")
    return True


if __name__ == "__main__":
    import time
    success = asyncio.run(test_error_handling_fix())
    if success:
        print("\n🎉 错误处理修复验证成功！")
    else:
        print("\n❌ 错误处理修复验证失败！") 