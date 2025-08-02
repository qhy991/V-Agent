#!/usr/bin/env python3
"""
测试高级修复效果 - 针对依赖关系和编译错误理解
复现用户分析中的具体问题场景
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
from extensions.test_analyzer import TestAnalyzer
from extensions.verilog_dependency_analyzer import VerilogDependencyAnalyzer


def setup_logging():
    """设置详细日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_advanced_fixes.log')
        ]
    )


def create_problematic_design():
    """创建用户分析中提到的problematic设计：缺少full_adder子模块的simple_8bit_adder"""
    file_manager = get_file_manager()
    
    print("🏗️ 创建问题设计文件（缺少依赖）...")
    
    # 创建一个引用了full_adder但没有定义的8位加法器
    problematic_design = """module simple_8bit_adder(
    input [7:0] a, b,
    input cin,
    output [7:0] sum,
    output cout
);
    wire [7:0] carry;
    
    // 实例化8个full_adder，但没有提供full_adder的定义
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : adder_stage
            if (i == 0) begin
                full_adder fa (
                    .a(a[i]),
                    .b(b[i]), 
                    .cin(cin),
                    .sum(sum[i]),
                    .cout(carry[i])
                );
            end else begin
                full_adder fa (
                    .a(a[i]),
                    .b(b[i]),
                    .cin(carry[i-1]),
                    .sum(sum[i]),
                    .cout(carry[i])
                );
            end
        end
    endgenerate
    
    assign cout = carry[7];
endmodule"""

    design_file_ref = file_manager.save_file(
        content=problematic_design,
        filename="simple_8bit_adder_problematic.v",
        file_type="verilog",
        created_by="enhanced_real_verilog_agent",
        description="问题设计文件 - 缺少full_adder依赖"
    )
    
    print(f"  ✅ 创建问题设计文件: {design_file_ref.file_path}")
    
    return design_file_ref


def create_complete_design():
    """创建完整的设计文件（包含依赖）"""
    file_manager = get_file_manager()
    
    print("🔧 创建完整设计文件（包含依赖）...")
    
    # 创建包含full_adder定义的完整设计
    complete_design = """// Full Adder module definition
module full_adder(
    input a, b, cin,
    output sum, cout
);
    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (b & cin) | (a & cin);
endmodule

// 8-bit adder using full_adder modules
module simple_8bit_adder(
    input [7:0] a, b,
    input cin,
    output [7:0] sum,
    output cout
);
    wire [7:0] carry;
    
    // 实例化8个full_adder
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : adder_stage
            if (i == 0) begin
                full_adder fa (
                    .a(a[i]),
                    .b(b[i]), 
                    .cin(cin),
                    .sum(sum[i]),
                    .cout(carry[i])
                );
            end else begin
                full_adder fa (
                    .a(a[i]),
                    .b(b[i]),
                    .cin(carry[i-1]),
                    .sum(sum[i]),
                    .cout(carry[i])
                );
            end
        end
    endgenerate
    
    assign cout = carry[7];
endmodule"""

    complete_file_ref = file_manager.save_file(
        content=complete_design,
        filename="simple_8bit_adder_complete.v",
        file_type="verilog",
        created_by="enhanced_real_verilog_agent",
        description="完整设计文件 - 包含full_adder依赖"
    )
    
    print(f"  ✅ 创建完整设计文件: {complete_file_ref.file_path}")
    
    return complete_file_ref


def create_testbench():
    """创建测试台文件"""
    file_manager = get_file_manager()
    
    print("🧪 创建测试台文件...")
    
    testbench_content = """module simple_8bit_adder_tb;
    reg [7:0] a, b;
    reg cin;
    wire [7:0] sum;
    wire cout;
    
    // 实例化被测试模块
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    initial begin
        $dumpfile("simple_8bit_adder.vcd");
        $dumpvars(0, simple_8bit_adder_tb);
        
        // 测试用例
        $display("开始8位加法器测试...");
        
        // 测试1: 简单加法
        a = 8'h0F; b = 8'h10; cin = 0; #10;
        $display("Test 1: %h + %h + %b = %h (cout=%b)", a, b, cin, sum, cout);
        
        // 测试2: 带进位
        a = 8'hFF; b = 8'h01; cin = 0; #10;
        $display("Test 2: %h + %h + %b = %h (cout=%b)", a, b, cin, sum, cout);
        
        // 测试3: 最大值
        a = 8'hFF; b = 8'hFF; cin = 1; #10;
        $display("Test 3: %h + %h + %b = %h (cout=%b)", a, b, cin, sum, cout);
        
        $display("测试完成");
        $finish;
    end
endmodule"""

    testbench_ref = file_manager.save_file(
        content=testbench_content,
        filename="simple_8bit_adder_tb.v",
        file_type="testbench",
        created_by="enhanced_real_code_reviewer",
        description="8位加法器测试台"
    )
    
    print(f"  ✅ 创建测试台文件: {testbench_ref.file_path}")
    
    return testbench_ref


async def test_dependency_analysis():
    """测试依赖分析功能"""
    print("\n" + "="*60)
    print("🔍 测试Verilog依赖分析功能")
    print("="*60)
    
    analyzer = VerilogDependencyAnalyzer()
    
    # 获取文件
    file_manager = get_file_manager()
    verilog_files = file_manager.get_files_by_type("verilog")
    
    print(f"📊 分析 {len(verilog_files)} 个Verilog文件...")
    
    for file_ref in verilog_files:
        print(f"\n🔍 分析文件: {Path(file_ref.file_path).name}")
        modules = analyzer.analyze_file(file_ref.file_path)
        
        for module in modules:
            print(f"  📦 模块: {module.name}")
            print(f"    - 类型: {'测试台' if module.is_testbench else '设计模块'}")
            print(f"    - 依赖: {list(module.dependencies) if module.dependencies else '无'}")
    
    # 查找顶层模块
    top_modules = analyzer.find_top_level_modules()
    print(f"\n🎯 顶层模块: {top_modules}")
    
    return {
        "total_files": len(verilog_files),
        "total_modules": len(analyzer.modules),
        "top_level_modules": top_modules
    }


async def test_problematic_compilation():
    """测试问题编译场景（缺少依赖）"""
    print("\n" + "="*60)
    print("❌ 测试问题编译场景（缺少依赖）")
    print("="*60)
    
    analyzer = TestAnalyzer()
    file_manager = get_file_manager()
    
    # 获取问题设计文件
    verilog_files = file_manager.get_files_by_type("verilog")
    problematic_file = None
    testbench_file = None
    
    for file_ref in verilog_files:
        if "problematic" in file_ref.file_path:
            problematic_file = file_ref
        
    testbench_files = file_manager.get_files_by_type("testbench")
    if testbench_files:
        testbench_file = testbench_files[0]
    
    if not problematic_file or not testbench_file:
        print("❌ 未找到问题文件或测试台文件")
        return {"status": "files_not_found"}
    
    print(f"🎯 测试文件: {Path(problematic_file.file_path).name}")
    print(f"🧪 测试台: {Path(testbench_file.file_path).name}")
    
    # 构建文件引用
    design_refs = [{
        "file_path": problematic_file.file_path,
        "file_type": problematic_file.file_type,
        "file_id": problematic_file.file_id
    }]
    
    try:
        result = await analyzer.run_with_user_testbench(
            design_refs,
            testbench_file.file_path
        )
        
        print(f"\n📊 编译结果:")
        print(f"  - 成功: {result.get('success', False)}")
        print(f"  - 阶段: {result.get('stage', 'unknown')}")
        
        # 分析依赖分析结果
        dep_analysis = result.get('dependency_analysis', {})
        if dep_analysis:
            print(f"\n🔍 依赖分析结果:")
            print(f"  - 兼容性: {dep_analysis.get('compatible', 'unknown')}")
            print(f"  - 缺失依赖: {dep_analysis.get('missing_dependencies', [])}")
            print(f"  - 附加文件: {len(dep_analysis.get('additional_files', []))} 个")
            
            issues = dep_analysis.get('issues', [])
            if issues:
                print(f"  - 发现问题:")
                for i, issue in enumerate(issues, 1):
                    print(f"    {i}. {issue}")
            
            suggestions = dep_analysis.get('suggestions', [])
            if suggestions:
                print(f"  - 修复建议:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"    {i}. {suggestion}")
        
        if not result.get("success"):
            error = result.get("error", "unknown")
            print(f"  - 错误: {error}")
            
            # 分析详细的编译错误
            if result.get("compile_stderr"):
                print(f"  - 编译错误详情: {result.get('compile_stderr', '')[:200]}...")
            
            # 检查是否有智能错误分析
            if "failure_reasons" in result:
                print(f"  - 失败原因分析: {result.get('failure_reasons', [])}")
            
            if "suggestions" in result:
                print(f"  - 智能建议: {result.get('suggestions', [])[:3]}")  # 显示前3条建议
        
        return {
            "status": "completed",
            "success": result.get("success", False),
            "has_dependency_analysis": bool(dep_analysis),
            "has_intelligent_suggestions": bool(result.get("suggestions")),
            "missing_dependencies": dep_analysis.get("missing_dependencies", [])
        }
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return {"status": "exception", "error": str(e)}


async def test_complete_compilation():
    """测试完整编译场景（包含依赖）"""
    print("\n" + "="*60)
    print("✅ 测试完整编译场景（包含依赖）")
    print("="*60)
    
    analyzer = TestAnalyzer()
    file_manager = get_file_manager()
    
    # 获取完整设计文件
    verilog_files = file_manager.get_files_by_type("verilog")
    complete_file = None
    testbench_file = None
    
    for file_ref in verilog_files:
        if "complete" in file_ref.file_path:
            complete_file = file_ref
    
    testbench_files = file_manager.get_files_by_type("testbench") 
    if testbench_files:
        testbench_file = testbench_files[0]
    
    if not complete_file or not testbench_file:
        print("❌ 未找到完整文件或测试台文件")
        return {"status": "files_not_found"}
    
    print(f"🎯 测试文件: {Path(complete_file.file_path).name}")
    print(f"🧪 测试台: {Path(testbench_file.file_path).name}")
    
    # 构建文件引用
    design_refs = [{
        "file_path": complete_file.file_path,
        "file_type": complete_file.file_type,
        "file_id": complete_file.file_id
    }]
    
    try:
        result = await analyzer.run_with_user_testbench(
            design_refs,
            testbench_file.file_path
        )
        
        print(f"\n📊 编译结果:")
        print(f"  - 成功: {result.get('success', False)}")
        print(f"  - 测试通过: {result.get('all_tests_passed', False)}")
        
        if result.get("success"):
            if result.get('simulation_stdout'):
                stdout_lines = result.get('simulation_stdout', '').split('\n')[:5]
                print(f"  - 仿真输出前5行:")
                for line in stdout_lines:
                    if line.strip():
                        print(f"    {line}")
        
        # 检查依赖分析结果
        dep_analysis = result.get('dependency_analysis', {})
        if dep_analysis:
            print(f"\n🔍 依赖分析结果:")
            print(f"  - 兼容性: {dep_analysis.get('compatible', 'unknown')}")
            print(f"  - 设计模块: {dep_analysis.get('design_modules', [])}")
            print(f"  - 测试台模块: {dep_analysis.get('testbench_modules', [])}")
        
        return {
            "status": "completed",
            "success": result.get("success", False),
            "all_tests_passed": result.get("all_tests_passed", False)
        }
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return {"status": "exception", "error": str(e)}


async def test_testbench_strategy():
    """测试testbench选择策略"""
    print("\n" + "="*60)
    print("🎯 测试Testbench选择策略")
    print("="*60)
    
    # 创建TDD协调器
    config = FrameworkConfig.from_env()
    base_coordinator = EnhancedCentralizedCoordinator(config)
    tdd_config = TestDrivenConfig(max_iterations=1)
    tdd_coordinator = TestDrivenCoordinator(base_coordinator, tdd_config)
    
    # 模拟不同迭代的testbench策略
    file_manager = get_file_manager()
    testbench_files = file_manager.get_files_by_type("testbench")
    
    if not testbench_files:
        print("❌ 没有测试台文件用于测试")
        return {"status": "no_testbench"}
    
    user_testbench = testbench_files[0].file_path
    current_testbench = testbench_files[0].file_path  # 模拟智能体生成的
    
    print("🧪 测试不同迭代的testbench选择策略:")
    
    strategies = []
    for iteration in [1, 2, 3]:
        strategy = tdd_coordinator._determine_testbench_strategy(
            iteration, user_testbench, current_testbench
        )
        
        print(f"\n  第{iteration}次迭代:")
        print(f"    - 策略: {strategy['strategy']}")
        print(f"    - 说明: {strategy['reason']}")
        print(f"    - 选择: {Path(strategy['selected_testbench']).name if strategy['selected_testbench'] else '无'}")
        
        strategies.append(strategy)
    
    return {
        "status": "completed",
        "strategies": strategies
    }


async def main():
    """主测试流程"""
    print("🚀 高级修复效果测试")
    print("=" * 60)
    
    # 设置日志
    setup_logging()
    
    # 初始化文件管理器（使用临时目录避免污染）
    temp_workspace = Path(tempfile.mkdtemp(prefix="tdd_advanced_test_"))
    initialize_file_manager(temp_workspace)
    print(f"📁 使用临时工作空间: {temp_workspace}")
    
    try:
        # 1. 创建测试数据
        print("\n🏗️ 步骤1: 创建测试数据")
        problematic_file = create_problematic_design()
        complete_file = create_complete_design()  
        testbench_file = create_testbench()
        
        # 2. 测试依赖分析
        print("\n🔍 步骤2: 测试依赖分析功能")
        dependency_result = await test_dependency_analysis()
        
        # 3. 测试问题编译场景
        print("\n❌ 步骤3: 测试问题编译场景")
        problematic_result = await test_problematic_compilation()
        
        # 4. 测试完整编译场景
        print("\n✅ 步骤4: 测试完整编译场景")
        complete_result = await test_complete_compilation()
        
        # 5. 测试testbench策略
        print("\n🎯 步骤5: 测试Testbench策略")
        strategy_result = await test_testbench_strategy()
        
        # 6. 结果汇总
        print("\n" + "="*60)
        print("📊 高级修复测试结果汇总")
        print("="*60)
        
        print(f"🔍 依赖分析测试:")
        print(f"  - 文件数量: {dependency_result['total_files']}")
        print(f"  - 模块数量: {dependency_result['total_modules']}")
        print(f"  - 顶层模块: {dependency_result['top_level_modules']}")
        
        print(f"\n❌ 问题编译测试:")
        print(f"  - 执行状态: {problematic_result['status']}")
        if problematic_result['status'] == 'completed':
            print(f"  - 编译成功: {problematic_result['success']}")
            print(f"  - 有依赖分析: {problematic_result['has_dependency_analysis']}")
            print(f"  - 有智能建议: {problematic_result['has_intelligent_suggestions']}")
            print(f"  - 缺失依赖: {problematic_result['missing_dependencies']}")
        
        print(f"\n✅ 完整编译测试:")
        print(f"  - 执行状态: {complete_result['status']}")
        if complete_result['status'] == 'completed':
            print(f"  - 编译成功: {complete_result['success']}")
            print(f"  - 测试通过: {complete_result['all_tests_passed']}")
        
        print(f"\n🎯 Testbench策略测试:")
        print(f"  - 执行状态: {strategy_result['status']}")
        
        # 7. 验证修复效果
        print(f"\n✅ 高级修复效果验证:")
        
        fixes_working = 0
        total_fixes = 4
        
        # 依赖分析功能
        if dependency_result['total_modules'] > 0:
            print(f"  ✅ 依赖分析功能: 识别了 {dependency_result['total_modules']} 个模块")
            fixes_working += 1
        else:
            print(f"  ⚠️ 依赖分析功能: 未能识别模块")
        
        # 问题检测和建议
        if (problematic_result['status'] == 'completed' and 
            problematic_result['has_dependency_analysis'] and
            problematic_result['has_intelligent_suggestions']):
            print(f"  ✅ 智能错误分析: 检测到依赖问题并提供建议")
            fixes_working += 1
        else:
            print(f"  ⚠️ 智能错误分析: 功能不完整")
        
        # 完整编译成功
        if (complete_result['status'] == 'completed' and 
            complete_result['success']):
            print(f"  ✅ 完整编译: 包含依赖的设计编译成功")
            fixes_working += 1
        else:
            print(f"  ⚠️ 完整编译: 仍有问题")
        
        # Testbench策略
        if strategy_result['status'] == 'completed':
            print(f"  ✅ Testbench策略: 统一策略运行正常")
            fixes_working += 1
        else:
            print(f"  ⚠️ Testbench策略: 功能异常")
        
        success_rate = fixes_working / total_fixes
        print(f"\n🎯 高级修复成功率: {fixes_working}/{total_fixes} ({success_rate*100:.1f}%)")
        
        if success_rate >= 0.75:
            print("✅ 高级修复效果优秀！解决了依赖分析和错误理解问题")
        elif success_rate >= 0.5:
            print("🔄 高级修复效果良好，还有提升空间")
        else:
            print("⚠️ 高级修复效果有待改进")
        
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_workspace)
            print(f"\n🧹 清理临时工作空间: {temp_workspace}")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())