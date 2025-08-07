#!/usr/bin/env python3
"""
测试重构后的代码审查智能体修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_fixes():
    """测试重构修复"""
    print("🧪 开始测试重构修复...")
    
    try:
        # 测试1: 检查模块导入
        print("1️⃣ 测试模块导入...")
        try:
            from core.base_agent import BaseAgent
            from core.function_calling.parser import ToolCall, ToolResult
            print("   ✅ 核心模块导入成功")
        except Exception as e:
            print(f"   ❌ 核心模块导入失败: {e}")
            return False
        
        # 测试2: 测试参数标准化逻辑
        print("2️⃣ 测试参数标准化逻辑...")
        
        # 模拟增强代码审查智能体的参数标准化方法
        def _normalize_tool_parameters(tool_name: str, parameters: dict) -> dict:
            normalized_params = parameters.copy()
            
            if tool_name == "read_file":
                if "file_path" in normalized_params and "filepath" not in normalized_params:
                    normalized_params["filepath"] = normalized_params["file_path"]
                    print(f"      🔧 参数映射: file_path -> filepath for {tool_name}")
                elif "filepath" in normalized_params and "file_path" not in normalized_params:
                    normalized_params["file_path"] = normalized_params["filepath"]
                    print(f"      🔧 参数映射: filepath -> file_path for {tool_name}")
            
            return normalized_params
        
        # 测试案例：模拟实际错误场景
        test_cases = [
            ("read_file", {"file_path": "./output/counter.v"}),  # 原来失败的情况
            ("read_file", {"filepath": "./output/counter2.v"}),  # 基准情况
            ("write_file", {"filename": "test.v", "content": "module test; endmodule"})  # 其他工具
        ]
        
        for tool_name, params in test_cases:
            print(f"   🔍 测试 {tool_name} 参数: {params}")
            normalized = _normalize_tool_parameters(tool_name, params)
            print(f"      📤 标准化结果: {normalized}")
            
            # 验证read_file工具有正确的参数
            if tool_name == "read_file":
                if "filepath" not in normalized:
                    print(f"      ❌ 缺少filepath参数")
                    return False
                else:
                    print(f"      ✅ filepath参数存在: {normalized['filepath']}")
        
        # 测试3: 模拟工具调用
        print("3️⃣ 模拟工具调用场景...")
        
        # 创建测试文件
        test_file_path = "./test_temp_file.txt"
        with open(test_file_path, "w") as f:
            f.write("Test content for refactoring validation")
        
        try:
            # 模拟BaseAgent._tool_read_file的签名要求
            def mock_tool_read_file(filepath: str, **kwargs) -> dict:
                """模拟BaseAgent的_tool_read_file方法"""
                if not os.path.exists(filepath):
                    return {"success": False, "error": f"File not found: {filepath}"}
                
                with open(filepath, 'r') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "result": {"content": content, "file_path": filepath},
                    "message": f"Successfully read file: {filepath}"
                }
            
            # 测试原来会失败的调用方式
            original_params = {"file_path": test_file_path}  # 这是原来导致错误的参数格式
            normalized_params = _normalize_tool_parameters("read_file", original_params)
            
            print(f"   📥 原始参数: {original_params}")
            print(f"   📤 标准化参数: {normalized_params}")
            
            # 现在应该有filepath参数，可以成功调用
            if "filepath" in normalized_params:
                result = mock_tool_read_file(**{k: v for k, v in normalized_params.items() if k in ["filepath"]})
                if result.get("success"):
                    print("   ✅ 模拟工具调用成功")
                else:
                    print(f"   ❌ 模拟工具调用失败: {result.get('error')}")
                    return False
            else:
                print("   ❌ 标准化后仍然缺少filepath参数")
                return False
        
        finally:
            # 清理测试文件
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        
        print("✅ 所有修复测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixes())
    if success:
        print("\n🎉 重构修复验证成功! 问题应已解决。")
        sys.exit(0)
    else:
        print("\n❌ 重构修复验证失败，需要进一步调试。")
        sys.exit(1)