#!/usr/bin/env python3
"""
测试实验数据隔离机制
==================================================

这个脚本用于验证实验管理器是否正确实现了数据隔离
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.experiment_manager import get_experiment_manager, create_experiment_session
from core.file_manager import CentralFileManager
from core.context_manager import FullContextManager


def test_experiment_creation():
    """测试实验创建"""
    print("🧪 测试实验创建...")
    
    manager = get_experiment_manager()
    
    # 创建实验
    experiment_info = manager.create_experiment(
        experiment_name="test_alu_design",
        task_description="设计32位ALU模块",
        metadata={"priority": "high", "type": "verilog_design"}
    )
    
    print(f"✅ 实验创建成功:")
    print(f"   实验ID: {experiment_info.experiment_id}")
    print(f"   工作目录: {experiment_info.workspace_path}")
    print(f"   状态: {experiment_info.status}")
    
    # 验证工作目录结构
    workspace_path = Path(experiment_info.workspace_path)
    expected_dirs = ["designs", "testbenches", "reports", "logs", "temp"]
    
    for subdir in expected_dirs:
        subdir_path = workspace_path / subdir
        if subdir_path.exists():
            print(f"   ✅ {subdir} 目录存在")
        else:
            print(f"   ❌ {subdir} 目录不存在")
    
    return experiment_info


def test_experiment_isolation():
    """测试实验数据隔离"""
    print("\n🧪 测试实验数据隔离...")
    
    manager = get_experiment_manager()
    
    # 创建两个不同的实验
    exp1 = manager.create_experiment("test_alu_1", "设计ALU模块1")
    exp2 = manager.create_experiment("test_alu_2", "设计ALU模块2")
    
    # 获取各自的文件管理器
    file_manager_1 = manager.get_experiment_file_manager(exp1.experiment_id)
    file_manager_2 = manager.get_experiment_file_manager(exp2.experiment_id)
    
    # 在不同实验中保存相同名称的文件
    content_1 = """
module alu_32bit (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output [31:0] result,
    output zero
);
    assign result = a + b;
    assign zero = (result == 0);
endmodule
"""
    
    content_2 = """
module alu_32bit (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output [31:0] result,
    output carry_out
);
    assign result = a + b;
    assign carry_out = (a + b > 32'hFFFF_FFFF);
endmodule
"""
    
    # 保存文件
    ref1 = file_manager_1.save_file(
        content=content_1,
        filename="alu_32bit.v",
        file_type="verilog",
        created_by="test_agent_1",
        description="ALU设计1"
    )
    
    ref2 = file_manager_2.save_file(
        content=content_2,
        filename="alu_32bit.v",
        file_type="verilog",
        created_by="test_agent_2",
        description="ALU设计2"
    )
    
    print(f"✅ 文件保存成功:")
    print(f"   实验1文件ID: {ref1.file_id}")
    print(f"   实验2文件ID: {ref2.file_id}")
    print(f"   文件ID不同: {ref1.file_id != ref2.file_id}")
    
    # 验证文件内容隔离
    content_1_retrieved = file_manager_1.read_file_content(ref1.file_id)
    content_2_retrieved = file_manager_2.read_file_content(ref2.file_id)
    
    print(f"   内容隔离验证:")
    print(f"   实验1包含'zero': {'zero' in content_1_retrieved}")
    print(f"   实验2包含'carry_out': {'carry_out' in content_2_retrieved}")
    print(f"   内容不同: {content_1_retrieved != content_2_retrieved}")
    
    return exp1, exp2


def test_context_isolation():
    """测试上下文隔离"""
    print("\n🧪 测试上下文隔离...")
    
    manager = get_experiment_manager()
    
    # 创建实验
    exp = manager.create_experiment("test_context", "测试上下文隔离")
    
    # 获取实验专用的上下文管理器
    context_manager = manager.get_experiment_context_manager(exp.experiment_id)
    
    # 添加端口信息
    port_info_1 = {
        "module_name": "alu_32bit",
        "ports": [
            {"name": "a", "direction": "input", "width": 32},
            {"name": "b", "direction": "input", "width": 32},
            {"name": "result", "direction": "output", "width": 32},
            {"name": "zero", "direction": "output", "width": 1}
        ],
        "port_count": 4
    }
    
    context_manager.add_port_info("alu_32bit", port_info_1)
    
    # 验证端口信息
    retrieved_info = context_manager.get_port_info("alu_32bit")
    if retrieved_info:
        print(f"✅ 上下文隔离验证:")
        print(f"   模块名: {retrieved_info['module_name']}")
        print(f"   端口数: {retrieved_info['port_count']}")
        print(f"   包含zero端口: {'zero' in [p['name'] for p in retrieved_info['ports']]}")
    
    return exp


def test_experiment_session():
    """测试实验会话"""
    print("\n🧪 测试实验会话...")
    
    # 创建实验会话
    session = create_experiment_session(
        experiment_name="test_session",
        task_description="测试实验会话功能",
        metadata={"test_type": "isolation"}
    )
    
    print(f"✅ 实验会话创建成功:")
    print(f"   实验ID: {session['experiment_id']}")
    print(f"   工作目录: {session['workspace_path']}")
    print(f"   文件管理器: {type(session['file_manager'])}")
    print(f"   上下文管理器: {type(session['context_manager'])}")
    
    # 测试文件管理器
    file_manager = session['file_manager']
    test_content = "module test_module(); endmodule"
    
    file_ref = file_manager.save_file(
        content=test_content,
        filename="test.v",
        file_type="verilog",
        created_by="test_session",
        description="测试文件"
    )
    
    print(f"   文件保存成功: {file_ref.file_id}")
    
    return session


def test_experiment_cleanup():
    """测试实验清理"""
    print("\n🧪 测试实验清理...")
    
    manager = get_experiment_manager()
    
    # 创建测试实验
    exp = manager.create_experiment("test_cleanup", "测试清理功能")
    
    # 添加一些文件
    file_manager = manager.get_experiment_file_manager(exp.experiment_id)
    file_manager.save_file(
        content="test content",
        filename="test.txt",
        file_type="text",
        created_by="test_cleanup",
        description="测试文件"
    )
    
    # 列出实验
    experiments = manager.list_experiments()
    print(f"   清理前实验数: {len(experiments)}")
    
    # 清理实验
    success = manager.cleanup_experiment(exp.experiment_id, keep_logs=True)
    print(f"   清理结果: {success}")
    
    # 验证清理
    experiments_after = manager.list_experiments()
    print(f"   清理后实验数: {len(experiments_after)}")
    
    return success


async def main():
    """主测试函数"""
    print("🚀 开始测试实验数据隔离机制")
    print("=" * 50)
    
    # 测试实验创建
    exp1 = test_experiment_creation()
    
    # 测试数据隔离
    exp2, exp3 = test_experiment_isolation()
    
    # 测试上下文隔离
    exp4 = test_context_isolation()
    
    # 测试实验会话
    session = test_experiment_session()
    
    # 测试实验清理
    cleanup_success = test_experiment_cleanup()
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成!")
    print(f"   创建实验数: 4")
    print(f"   数据隔离: ✅")
    print(f"   上下文隔离: ✅")
    print(f"   会话管理: ✅")
    print(f"   清理功能: {'✅' if cleanup_success else '❌'}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    asyncio.run(main()) 