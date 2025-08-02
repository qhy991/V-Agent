#!/usr/bin/env python3
"""
测试依赖分析和错误报告修复
"""

import asyncio
import tempfile
import subprocess
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_dependency_analysis():
    """测试依赖分析功能"""
    print("🔍 测试依赖分析功能")
    
    # 创建临时文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建主模块文件（依赖于sub_module）
        main_module = temp_path / "main_module.v"
        main_module.write_text("""
module main_module (
    input a,
    input b,
    output y
);
    
    sub_module inst1 (.in1(a), .in2(b), .out(y));
    
endmodule
""")
        
        # 创建子模块文件
        sub_module = temp_path / "sub_module.v"
        sub_module.write_text("""
module sub_module (
    input in1,
    input in2,
    output out
);
    
    assign out = in1 & in2;
    
endmodule
""")
        
        # 创建测试台文件
        testbench = temp_path / "main_module_tb.v"
        testbench.write_text("""
module main_module_tb;
    reg a, b;
    wire y;
    
    main_module uut (.a(a), .b(b), .y(y));
    
    initial begin
        $dumpfile("test.vcd");
        $dumpvars(0, main_module_tb);
        
        a = 0; b = 0; #10;
        a = 0; b = 1; #10;
        a = 1; b = 0; #10;
        a = 1; b = 1; #10;
        
        $finish;
    end
    
endmodule
""")
        
        # 测试依赖分析器
        from extensions.verilog_dependency_analyzer import VerilogDependencyAnalyzer
        
        analyzer = VerilogDependencyAnalyzer()
        
        # 分析文件
        main_modules = analyzer.analyze_file(str(main_module))
        sub_modules = analyzer.analyze_file(str(sub_module))
        
        print(f"主模块分析结果: {[m.name for m in main_modules]}")
        print(f"子模块分析结果: {[m.name for m in sub_modules]}")
        
        # 检查依赖关系
        if main_modules:
            main_deps = main_modules[0].dependencies
            print(f"主模块依赖: {list(main_deps)}")
            
            if "sub_module" in main_deps:
                print("✅ 依赖分析成功：正确识别了sub_module依赖")
            else:
                print("❌ 依赖分析失败：未识别sub_module依赖")
        
        # 测试编译顺序生成
        required_files, missing = analyzer.resolve_dependencies(["main_module"])
        print(f"编译所需文件: {[Path(f).name for f in required_files]}")
        print(f"缺失模块: {missing}")
        
        # 测试兼容性分析
        compatibility = analyzer.analyze_compatibility(str(main_module), str(testbench))
        print(f"兼容性分析: {compatibility['compatible']}")
        if compatibility["issues"]:
            print(f"兼容性问题: {compatibility['issues']}")

async def test_simulation_error_reporting():
    """测试仿真错误报告"""
    print("\n🧪 测试仿真错误报告")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建有错误的模块（依赖缺失）
        broken_module = temp_path / "broken_module.v"
        broken_module.write_text("""
module broken_module (
    input a,
    input b,
    output y
);
    
    // 这里引用了不存在的模块
    missing_module inst1 (.in1(a), .in2(b), .out(y));
    
endmodule
""")
        
        # 创建测试台
        testbench = temp_path / "broken_module_tb.v"
        testbench.write_text("""
module broken_module_tb;
    reg a, b;
    wire y;
    
    broken_module uut (.a(a), .b(b), .y(y));
    
    initial begin
        a = 0; b = 0; #10;
        $finish;
    end
    
endmodule
""")
        
        # 尝试直接编译（应该失败）
        try:
            result = subprocess.run([
                "iverilog", "-o", str(temp_path / "test"), 
                str(broken_module), str(testbench)
            ], capture_output=True, text=True, timeout=10)
            
            print(f"编译返回码: {result.returncode}")
            print(f"编译错误输出: {result.stderr}")
            
            if result.returncode != 0:
                print("✅ 错误检测成功：iverilog正确报告编译失败")
                
                # 检查是否包含"No top level modules"或类似错误
                if "not found" in result.stderr or "No top level modules" in result.stderr:
                    print("✅ 错误信息正确：包含模块缺失信息")
                else:
                    print("⚠️ 错误信息不完整：缺少具体的模块缺失信息")
            else:
                print("❌ 错误检测失败：编译应该失败但返回成功")
                
        except subprocess.TimeoutExpired:
            print("⚠️ 编译超时")
        except FileNotFoundError:
            print("⚠️ iverilog未找到，跳过编译测试")

async def test_enhanced_code_reviewer_integration():
    """测试增强代码审查器集成"""
    print("\n🤖 测试增强代码审查器集成")
    
    try:
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        
        # 创建代码审查器实例
        config = FrameworkConfig.from_env()
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        print("✅ 增强代码审查器初始化成功")
        
        # 检查是否有依赖分析器
        if hasattr(reviewer, 'dependency_analyzer'):
            print("✅ 代码审查器包含依赖分析器")
        else:
            print("❌ 代码审查器缺少依赖分析器")
            
        # 检查run_simulation工具是否存在
        if "run_simulation" in reviewer.enhanced_tools:
            tool_def = reviewer.enhanced_tools["run_simulation"]
            print("✅ run_simulation工具已注册为增强工具")
            print(f"工具描述: {tool_def.description}")
        else:
            print("❌ run_simulation工具未注册为增强工具")
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

async def main():
    """主测试函数"""
    print("🎯 开始依赖分析和错误报告测试")
    print("="*60)
    
    await test_dependency_analysis()
    await test_simulation_error_reporting()
    await test_enhanced_code_reviewer_integration()
    
    print("\n" + "="*60)
    print("🎉 依赖分析和错误报告测试完成")

if __name__ == "__main__":
    asyncio.run(main())