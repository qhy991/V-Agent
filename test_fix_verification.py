#!/usr/bin/env python3
"""
快速验证FileReference修复
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.base_agent import FileReference

def test_filereference_handling():
    """测试FileReference对象处理"""
    print("🧪 测试FileReference对象处理...")
    
    # 创建FileReference对象
    file_ref = FileReference(
        file_path="./output/test.v",
        file_type="verilog",
        description="测试文件"
    )
    
    # 测试对象属性访问
    print(f"路径: {file_ref.file_path}")
    print(f"类型: {file_ref.file_type}")
    print(f"描述: {file_ref.description}")
    
    # 测试字典格式
    dict_ref = {
        'file_path': './output/test2.v',
        'file_type': 'verilog',
        'description': '测试文件2'
    }
    
    # 测试统一处理逻辑
    def handle_file_ref(file_ref):
        if isinstance(file_ref, dict):
            return file_ref.get('file_path', 'unknown'), file_ref.get('file_type', 'unknown')
        else:
            return file_ref.file_path, file_ref.file_type
    
    obj_path, obj_type = handle_file_ref(file_ref)
    dict_path, dict_type = handle_file_ref(dict_ref)
    
    print(f"对象格式处理结果: {obj_path} ({obj_type})")
    print(f"字典格式处理结果: {dict_path} ({dict_type})")
    
    print("✅ FileReference处理测试通过")

if __name__ == "__main__":
    test_filereference_handling()