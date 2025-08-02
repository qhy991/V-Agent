#!/usr/bin/env python3
"""
测试TDD修复效果 - 复现test-10.log问题并验证修复
"""

import sys
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from extensions.test_driven_coordinator import TestDrivenCoordinator, TestDrivenConfig
from core.file_manager import get_file_manager, initialize_file_manager
import datetime


def setup_logging():
    """设置详细日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_tdd_fixes.log')
        ]
    )


def create_mock_design_files():
    """创建模拟的设计文件来测试历史文件混合问题"""
    file_manager = get_file_manager()
    
    # 模拟历史版本的设计文件
    historical_designs = [
        ("simple_adder_v1.v", "verilog", "模拟历史版本1"),
        ("simple_adder_v2.v", "verilog", "模拟历史版本2"), 
        ("simple_adder_v3.v", "verilog", "模拟历史版本3")
    ]
    
    historical_testbenches = [
        ("simple_adder_tb_v1.v", "testbench", "模拟历史测试台1"),
        ("simple_adder_tb_v2.v", "testbench", "模拟历史测试台2")
    ]
    
    print("🏗️ 创建模拟历史文件...")
    
    saved_files = {"designs": [], "testbenches": []}
    
    # 创建历史设计文件
    for filename, file_type, description in historical_designs:
        content = f"""module simple_adder(
    input [7:0] a, b,
    output [7:0] sum
);
    assign sum = a + b;  // {description}
endmodule"""
        
        file_ref = file_manager.save_file(
            content=content,
            filename=filename,
            file_type=file_type,
            created_by="test_script",
            description=description
        )
        saved_files["designs"].append(file_ref)
        print(f"  ✅ 创建设计文件: {filename}")
    
    # 创建历史测试台文件
    for filename, file_type, description in historical_testbenches:
        content = f"""module simple_adder_tb;
    reg [7:0] a, b;
    wire [7:0] sum;
    
    simple_adder uut(.a(a), .b(b), .sum(sum));
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        // {description}
        a = 8'h10; b = 8'h20; #10;
        $display("a=%h, b=%h, sum=%h", a, b, sum);
        
        $finish;
    end
endmodule"""
        
        file_ref = file_manager.save_file(
            content=content,
            filename=filename,
            file_type=file_type,
            created_by="test_script",
            description=description
        )
        saved_files["testbenches"].append(file_ref)
        print(f"  ✅ 创建测试台文件: {filename}")
    
    return saved_files


def create_current_iteration_files():
    """创建当前迭代的文件（最新版本）"""
    file_manager = get_file_manager()
    
    print("🆕 创建当前迭代文件...")
    
    # 当前迭代的设计文件
    current_design_content = """module simple_adder(
    input [7:0] a, b,
    output [8:0] sum  // 修正：应该是9位输出防止溢出
);
    assign sum = a + b;  // 当前最新版本
endmodule"""
    
    current_design = file_manager.save_file(
        content=current_design_content,
        filename="simple_adder_current.v",
        file_type="verilog",
        created_by="enhanced_real_verilog_agent",
        description="当前迭代的设计文件"
    )
    
    # 当前迭代的测试台
    current_testbench_content = """module simple_adder_tb;
    reg [7:0] a, b;
    wire [8:0] sum;  // 匹配设计的9位输出
    
    simple_adder uut(.a(a), .b(b), .sum(sum));
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        // 当前迭代测试用例
        a = 8'hFF; b = 8'hFF; #10;  // 测试最大值相加
        if (sum == 9'h1FE) 
            $display("PASS: a=%h, b=%h, sum=%h", a, b, sum);
        else
            $display("FAIL: a=%h, b=%h, sum=%h (expected 1FE)", a, b, sum);
        
        a = 8'h00; b = 8'h00; #10;  // 测试零值
        if (sum == 9'h000)
            $display("PASS: a=%h, b=%h, sum=%h", a, b, sum);
        else
            $display("FAIL: a=%h, b=%h, sum=%h (expected 000)", a, b, sum);
            
        $finish;
    end
endmodule"""
    
    current_testbench = file_manager.save_file(
        content=current_testbench_content,
        filename="simple_adder_tb_current.v",
        file_type="testbench", 
        created_by="enhanced_real_code_reviewer",
        description="当前迭代的测试台文件"
    )
    
    print(f"  ✅ 创建当前设计文件: {current_design.file_path}")
    print(f"  ✅ 创建当前测试台文件: {current_testbench.file_path}") 
    
    return {
        "design": current_design,
        "testbench": current_testbench
    }


async def test_old_behavior_simulation():
    """测试修复前的行为（应该会出现文件混合问题）"""
    print("\n" + "="*60)
    print("🔍 测试修复前行为模拟（历史文件混合问题）")
    print("="*60)
    
    file_manager = get_file_manager()
    
    # 获取所有历史文件（模拟修复前的行为）
    all_verilog_files = file_manager.get_files_by_type("verilog")
    all_testbench_files = file_manager.get_files_by_type("testbench")
    
    print(f"📊 文件管理器状态:")
    print(f"  - Verilog设计文件: {len(all_verilog_files)} 个")
    print(f"  - 测试台文件: {len(all_testbench_files)} 个")
    
    print(f"\n📋 所有Verilog文件:")
    for i, file_ref in enumerate(all_verilog_files):
        print(f"  {i+1}. {Path(file_ref.file_path).name} (创建于: {file_ref.created_at})")
    
    print(f"\n📋 所有测试台文件:")
    for i, file_ref in enumerate(all_testbench_files):
        print(f"  {i+1}. {Path(file_ref.file_path).name} (创建于: {file_ref.created_at})")
    
    # 模拟旧版本会传递所有文件到编译器
    all_verilog_paths = [f.file_path for f in all_verilog_files]
    print(f"\n⚠️ 旧版本行为: 会将 {len(all_verilog_paths)} 个设计文件全部传递给编译器")
    print("   这会导致 'No top level modules' 错误")
    
    return {
        "total_verilog_files": len(all_verilog_files),
        "total_testbench_files": len(all_testbench_files),
        "would_compile_files": len(all_verilog_paths)
    }


async def test_new_behavior():
    """测试修复后的行为（应该只选择当前迭代文件）"""
    print("\n" + "="*60)
    print("🔧 测试修复后行为（智能文件选择）")  
    print("="*60)
    
    # 创建TDD协调器
    config = FrameworkConfig.from_env()
    base_coordinator = EnhancedCentralizedCoordinator(config)
    tdd_config = TestDrivenConfig(max_iterations=1)
    tdd_coordinator = TestDrivenCoordinator(base_coordinator, tdd_config)
    
    # 模拟设计阶段的结果（没有明确的文件引用，会触发从文件管理器获取）
    mock_design_result = {
        "success": True,
        "tool_results": []  # 空的工具结果，会触发从文件管理器获取
    }
    
    print("🔄 测试文件引用提取逻辑...")
    extracted_refs = tdd_coordinator._extract_file_references(mock_design_result)
    
    print(f"\n📊 文件引用提取结果:")
    print(f"  - 提取到的文件数量: {len(extracted_refs)}")
    
    for i, file_ref in enumerate(extracted_refs):
        if isinstance(file_ref, dict):
            filename = Path(file_ref.get("file_path", "")).name
            file_type = file_ref.get("file_type", "unknown")
            file_id = file_ref.get("file_id", "N/A")
            print(f"  {i+1}. {filename} (类型: {file_type}, ID: {file_id})")
    
    # 测试测试阶段的文件准备
    print(f"\n🧪 测试测试阶段文件准备...")
    
    # 分离设计文件和测试台文件
    design_files = [ref for ref in extracted_refs if ref.get("file_type") == "verilog"]
    testbench_files = [ref for ref in extracted_refs if ref.get("file_type") == "testbench"]
    
    print(f"  - 设计文件: {len(design_files)} 个")
    for design in design_files:
        print(f"    ✅ {Path(design['file_path']).name}")
    
    print(f"  - 测试台文件: {len(testbench_files)} 个") 
    for testbench in testbench_files:
        print(f"    ✅ {Path(testbench['file_path']).name}")
    
    return {
        "extracted_files": len(extracted_refs),
        "design_files": len(design_files),
        "testbench_files": len(testbench_files),
        "selected_files": extracted_refs
    }


async def test_testanalyzer_compilation():
    """测试TestAnalyzer的编译逻辑"""
    print("\n" + "="*60)
    print("🧪 测试TestAnalyzer编译逻辑")
    print("="*60)
    
    from extensions.test_analyzer import TestAnalyzer
    
    analyzer = TestAnalyzer()
    
    # 获取当前迭代文件
    file_manager = get_file_manager()
    latest_designs = file_manager.get_latest_files_by_type("verilog", limit=1)
    latest_testbenches = file_manager.get_latest_files_by_type("testbench", limit=1)
    
    if not latest_designs or not latest_testbenches:
        print("❌ 没有找到设计文件或测试台文件")
        return {"status": "no_files"}
    
    current_design = latest_designs[0]
    current_testbench = latest_testbenches[0]
    
    print(f"🎯 选择的文件:")
    print(f"  - 设计文件: {Path(current_design.file_path).name}")
    print(f"  - 测试台文件: {Path(current_testbench.file_path).name}")
    
    # 构建文件引用格式
    design_refs = [{
        "file_path": current_design.file_path,
        "file_type": current_design.file_type,
        "file_id": current_design.file_id
    }]
    
    print(f"\n🔨 执行编译测试...")
    
    try:
        # 测试仿真
        result = await analyzer.run_with_user_testbench(
            design_refs,
            current_testbench.file_path
        )
        
        print(f"\n📊 编译结果:")
        print(f"  - 成功: {result.get('success', False)}")
        print(f"  - 阶段: {result.get('stage', 'unknown')}")
        
        if result.get("success"):
            print(f"  - 测试通过: {result.get('all_tests_passed', False)}")
            if result.get('simulation_stdout'):
                print(f"  - 仿真输出: {result.get('simulation_stdout', '')[:200]}...")
        else:
            print(f"  - 错误: {result.get('error', 'unknown')}")
            if result.get('compile_stderr'):
                print(f"  - 编译错误: {result.get('compile_stderr', '')[:200]}...")
        
        return {
            "status": "completed",
            "success": result.get("success", False),
            "all_tests_passed": result.get("all_tests_passed", False),
            "error": result.get("error")
        }
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return {
            "status": "exception", 
            "error": str(e)
        }


async def main():
    """主测试流程"""
    print("🚀 TDD修复效果测试")
    print("="*60)
    
    # 设置日志
    setup_logging()
    
    # 初始化文件管理器（使用临时目录避免污染）
    temp_workspace = Path(tempfile.mkdtemp(prefix="tdd_test_"))
    initialize_file_manager(temp_workspace)
    print(f"📁 使用临时工作空间: {temp_workspace}")
    
    try:
        # 1. 创建测试数据
        print("\n🏗️ 步骤1: 创建测试数据")
        historical_files = create_mock_design_files()
        current_files = create_current_iteration_files()
        
        # 2. 测试修复前行为
        print("\n🔍 步骤2: 测试修复前行为模拟")
        old_behavior_result = await test_old_behavior_simulation()
        
        # 3. 测试修复后行为
        print("\n🔧 步骤3: 测试修复后行为") 
        new_behavior_result = await test_new_behavior()
        
        # 4. 测试实际编译
        print("\n🧪 步骤4: 测试实际编译执行")
        compilation_result = await test_testanalyzer_compilation()
        
        # 5. 结果汇总
        print("\n" + "="*60)
        print("📊 测试结果汇总")
        print("="*60)
        
        print(f"🔍 修复前模拟:")
        print(f"  - 历史Verilog文件数: {old_behavior_result['total_verilog_files']}")
        print(f"  - 历史测试台文件数: {old_behavior_result['total_testbench_files']}")
        print(f"  - 会传递给编译器的文件数: {old_behavior_result['would_compile_files']}")
        print(f"  - 预期结果: ❌ 编译失败 (No top level modules)")
        
        print(f"\n🔧 修复后实际:")
        print(f"  - 智能选择的文件数: {new_behavior_result['extracted_files']}")
        print(f"  - 设计文件数: {new_behavior_result['design_files']}")
        print(f"  - 测试台文件数: {new_behavior_result['testbench_files']}")
        
        print(f"\n🧪 实际编译测试:")
        print(f"  - 执行状态: {compilation_result['status']}")
        if compilation_result['status'] == 'completed':
            print(f"  - 编译成功: {compilation_result['success']}")
            print(f"  - 测试通过: {compilation_result.get('all_tests_passed', 'N/A')}")
        else:
            print(f"  - 错误: {compilation_result.get('error', 'unknown')}")
        
        # 6. 验证修复效果
        print(f"\n✅ 修复效果验证:")
        
        if old_behavior_result['would_compile_files'] > new_behavior_result['extracted_files']:
            print(f"  ✅ 文件选择优化: 从 {old_behavior_result['would_compile_files']} 个减少到 {new_behavior_result['extracted_files']} 个")
        else:
            print(f"  ⚠️ 文件选择未优化")
        
        if new_behavior_result['design_files'] <= 1 and new_behavior_result['testbench_files'] <= 1:
            print(f"  ✅ 文件数量控制: 设计文件≤1个, 测试台文件≤1个")
        else:
            print(f"  ⚠️ 文件数量控制未生效")
        
        if compilation_result['status'] == 'completed' and compilation_result['success']:
            print(f"  ✅ 编译成功: 修复有效，避免了'No top level modules'错误")
        else:
            print(f"  ⚠️ 编译仍有问题: {compilation_result.get('error', 'unknown')}")
        
        success_rate = sum([
            old_behavior_result['would_compile_files'] > new_behavior_result['extracted_files'],
            new_behavior_result['design_files'] <= 1 and new_behavior_result['testbench_files'] <= 1,
            compilation_result['status'] == 'completed' and compilation_result['success']
        ])
        
        print(f"\n🎯 修复成功率: {success_rate}/3 ({success_rate/3*100:.1f}%)")
        
        if success_rate >= 2:
            print("✅ 修复效果良好！")
        else:
            print("⚠️ 修复效果有待提升")
        
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_workspace)
            print(f"\n🧹 清理临时工作空间: {temp_workspace}")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())