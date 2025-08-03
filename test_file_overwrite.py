#!/usr/bin/env python3
"""
测试文件覆盖功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.file_manager import get_file_manager

def test_file_overwrite():
    """测试文件覆盖功能"""
    print("🧪 测试文件覆盖功能")
    print("=" * 60)
    
    # 获取文件管理器
    file_manager = get_file_manager()
    
    # 测试文件名
    test_filename = "test_overwrite.v"
    
    print(f"📝 测试文件名: {test_filename}")
    
    # 第一次保存
    print("\n1️⃣ 第一次保存文件...")
    content1 = """
module test_module1;
    output reg [7:0] data;
    initial begin
        data = 8'hAA;
        $display("Module 1: data = %h", data);
    end
endmodule
"""
    
    file_ref1 = file_manager.save_file(
        content=content1,
        filename=test_filename,
        file_type="verilog",
        created_by="test_agent_1",
        description="第一次保存的测试文件"
    )
    
    print(f"   文件ID: {file_ref1.file_id}")
    print(f"   文件路径: {file_ref1.file_path}")
    print(f"   创建时间: {file_ref1.created_at}")
    
    # 检查文件是否存在
    file_path = Path(file_ref1.file_path)
    print(f"   文件存在: {file_path.exists()}")
    if file_path.exists():
        print(f"   文件内容长度: {len(file_path.read_text())}")
    
    # 第二次保存（覆盖）
    print("\n2️⃣ 第二次保存文件（覆盖）...")
    content2 = """
module test_module2;
    output reg [15:0] data;
    initial begin
        data = 16'hBBCC;
        $display("Module 2: data = %h", data);
    end
endmodule
"""
    
    file_ref2 = file_manager.save_file(
        content=content2,
        filename=test_filename,
        file_type="verilog",
        created_by="test_agent_2",
        description="第二次保存的测试文件（覆盖）"
    )
    
    print(f"   文件ID: {file_ref2.file_id}")
    print(f"   文件路径: {file_ref2.file_path}")
    print(f"   创建时间: {file_ref2.created_at}")
    
    # 检查文件是否被覆盖
    print(f"   文件存在: {file_path.exists()}")
    if file_path.exists():
        print(f"   文件内容长度: {len(file_path.read_text())}")
        print(f"   文件内容: {file_path.read_text()[:100]}...")
    
    # 验证ID是否相同
    print(f"\n🔍 验证结果:")
    print(f"   文件ID相同: {file_ref1.file_id == file_ref2.file_id}")
    print(f"   文件路径相同: {file_ref1.file_path == file_ref2.file_path}")
    
    # 检查注册表中的文件数量
    all_files = file_manager.list_all_files()
    verilog_files = [f for f in all_files if f.file_type == "verilog"]
    print(f"   注册表中的Verilog文件数量: {len(verilog_files)}")
    
    # 列出所有Verilog文件
    print(f"\n📋 所有Verilog文件:")
    for i, file_ref in enumerate(verilog_files, 1):
        print(f"   {i}. {Path(file_ref.file_path).name} (ID: {file_ref.file_id})")
    
    print("\n" + "=" * 60)
    print("✅ 文件覆盖功能测试完成！")

if __name__ == "__main__":
    test_file_overwrite() 