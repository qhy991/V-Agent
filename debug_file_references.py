#!/usr/bin/env python3
"""
调试文件引用传递问题
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.file_manager import get_file_manager
from extensions.test_driven_coordinator import TestDrivenCoordinator, TestDrivenConfig
from extensions.test_analyzer import TestAnalyzer
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_file_references():
    """调试文件引用传递"""
    print("🔍 调试文件引用传递问题")
    
    # 1. 检查文件管理器状态
    print("\n1. 📂 检查文件管理器状态:")
    file_manager = get_file_manager()
    workspace_info = file_manager.get_workspace_info()
    print(f"   工作空间: {workspace_info['workspace_root']}")
    print(f"   总文件数: {workspace_info['total_files']}")
    
    # 2. 获取最新的设计文件
    print("\n2. 🔍 获取最新设计文件:")
    verilog_files = file_manager.get_latest_files_by_type("verilog", limit=5)
    print(f"   找到 {len(verilog_files)} 个Verilog文件:")
    
    for i, file_ref in enumerate(verilog_files, 1):
        print(f"   {i}. 文件ID: {file_ref.file_id}")
        print(f"      文件路径: {file_ref.file_path}")
        print(f"      文件类型: {file_ref.file_type}")
        print(f"      文件存在: {Path(file_ref.file_path).exists()}")
        print(f"      绝对路径: {Path(file_ref.file_path).resolve()}")
        print()
    
    # 3. 模拟TDD协调器的文件引用提取
    print("\n3. 🔄 模拟TDD协调器文件引用提取:")
    from config.config import FrameworkConfig
    config = FrameworkConfig.from_env()
    base_coordinator = EnhancedCentralizedCoordinator(config)
    tdd_config = TestDrivenConfig(max_iterations=1)
    tdd_coordinator = TestDrivenCoordinator(base_coordinator, tdd_config)
    
    # 创建模拟的design_result
    mock_design_result = {
        "success": True,
        "tool_results": []  # 空的工具结果，会触发从文件管理器获取
    }
    
    # 调用_extract_file_references方法
    extracted_refs = tdd_coordinator._extract_file_references(mock_design_result)
    print(f"   提取到 {len(extracted_refs)} 个文件引用:")
    
    for i, file_ref in enumerate(extracted_refs, 1):
        print(f"   {i}. 类型: {type(file_ref)}")
        print(f"      内容: {file_ref}")
        if isinstance(file_ref, dict):
            print(f"      file_path: {file_ref.get('file_path')}")
            print(f"      file_type: {file_ref.get('file_type')}")
        print()
    
    # 4. 测试TestAnalyzer的路径提取
    print("\n4. 🧪 测试TestAnalyzer路径提取:")
    
    # 只传递Verilog设计文件（过滤掉testbench）
    design_only_refs = [ref for ref in extracted_refs if ref.get('file_type') == 'verilog']
    print(f"   仅设计文件: {len(design_only_refs)} 个")
    
    for i, ref in enumerate(design_only_refs, 1):
        print(f"   设计文件 {i}: {ref['file_path']}")
        print(f"      文件存在: {Path(ref['file_path']).exists()}")
    
    # 设置DEBUG级别的日志来查看TestAnalyzer内部处理
    analyzer_logger = logging.getLogger("extensions.test_analyzer.TestAnalyzer")
    analyzer_logger.setLevel(logging.DEBUG)
    
    analyzer = TestAnalyzer()
    extracted_paths = analyzer._extract_file_paths(design_only_refs)
    print(f"   TestAnalyzer提取到 {len(extracted_paths)} 个路径:")
    
    for i, path in enumerate(extracted_paths, 1):
        print(f"   {i}. {path}")
        print(f"      文件存在: {Path(path).exists()}")
    
    return extracted_paths

if __name__ == "__main__":
    result = debug_file_references()
    print(f"\n🎯 调试结果: 成功提取 {len(result)} 个有效文件路径")