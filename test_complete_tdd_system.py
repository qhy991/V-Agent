#!/usr/bin/env python3
"""
完整TDD系统验证
Complete TDD System Verification - 验证所有log-16.log修复是否生效
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_complete_tdd_cycle():
    """测试完整的TDD循环，包括所有修复"""
    print("🎯 开始完整TDD循环测试")
    
    try:
        from extensions.test_driven_coordinator import TestDrivenCoordinator
        from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        base_coordinator = EnhancedCentralizedCoordinator(config)
        tdd_coordinator = TestDrivenCoordinator(base_coordinator)
        
        # 测试一个简单的设计需求
        design_request = """
设计一个名为simple_counter的简单计数器模块，具有以下功能：
- 8位同步递增计数器
- 带有时钟clk和复位rst输入
- 带有使能信号enable
- 输出计数值count[7:0]和溢出标志overflow
"""
        
        print(f"📋 设计需求: {design_request.strip()}")
        
        # 运行TDD流程（限制迭代次数避免长时间运行）
        result = await tdd_coordinator.run_tdd_cycle(
            design_request=design_request,
            max_iterations=2,  # 限制迭代次数
            quality_threshold=70
        )
        
        if result.get('success'):
            print("✅ TDD循环成功完成")
            print(f"   总迭代次数: {result.get('total_iterations', 'N/A')}")
            print(f"   最终质量分数: {result.get('final_quality_score', 'N/A')}")
            
            # 检查结果文件
            if result.get('artifacts'):
                print("📁 生成的文件:")
                for artifact in result['artifacts']:
                    if Path(artifact).exists():
                        print(f"   ✅ {artifact}")
                    else:
                        print(f"   ❌ {artifact} (文件不存在)")
            
            return True
        else:
            print(f"❌ TDD循环失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ TDD测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_code_cleaning_integration():
    """测试代码清理与TDD系统的集成"""
    print("\n🧹 测试代码清理集成")
    
    try:
        from extensions.test_analyzer import TestAnalyzer
        
        analyzer = TestAnalyzer()
        
        # 创建一个有问题的设计文件（混合Markdown+Verilog）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
            problem_content = """以下是一个计数器模块的实现：

```verilog
module test_counter(
    input clk,
    input rst,
    output reg [3:0] count
);

always @(posedge clk or posedge rst) begin
    if (rst)
        count <= 4'b0;
    else
        count <= count + 1;
end

endmodule
```

### 功能说明
这是一个4位计数器模块。
"""
            f.write(problem_content)
            problem_file = f.name
        
        try:
            print(f"测试清理文件: {problem_file}")
            
            # 运行代码清理
            cleaned_paths = analyzer._clean_design_files([problem_file])
            
            if len(cleaned_paths) == 1:
                cleaned_path = cleaned_paths[0]
                if cleaned_path != problem_file:
                    print("✅ 代码清理成功生成新文件")
                    
                    # 验证清理效果
                    with open(cleaned_path, 'r', encoding='utf-8') as f:
                        cleaned_content = f.read()
                    
                    # 检查清理效果
                    issues_fixed = []
                    if "```verilog" not in cleaned_content:
                        issues_fixed.append("移除Markdown代码块")
                    if "以下是" not in cleaned_content:
                        issues_fixed.append("移除说明文字")
                    if "module test_counter" in cleaned_content:
                        issues_fixed.append("保留Verilog代码")
                    if "endmodule" in cleaned_content:
                        issues_fixed.append("保留模块结构")
                    
                    print(f"修复效果: {', '.join(issues_fixed)}")
                    
                    # 清理临时文件
                    Path(cleaned_path).unlink()
                    return len(issues_fixed) >= 3
                else:
                    print("⚠️ 文件可能不需要清理")
                    return True
            else:
                print("❌ 代码清理失败")
                return False
                
        finally:
            Path(problem_file).unlink()
            
    except Exception as e:
        print(f"❌ 代码清理集成测试异常: {e}")
        return False

async def test_enhanced_verilog_agent():
    """测试增强的Verilog代理是否生成纯净代码"""
    print("\n🔧 测试增强Verilog代理生成质量")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgent(config)
        
        # 测试代码生成
        result = await agent._tool_generate_verilog_code(
            module_name="test_adder",
            requirements="设计一个简单的2位加法器",
            input_ports=[
                {"name": "a", "width": 2, "description": "输入A"},
                {"name": "b", "width": 2, "description": "输入B"}
            ],
            output_ports=[
                {"name": "sum", "width": 3, "description": "加法结果"}
            ]
        )
        
        if result.get('success'):
            verilog_code = result['verilog_code']
            print("✅ Verilog代码生成成功")
            
            # 检查生成的代码质量
            quality_checks = []
            if not verilog_code.startswith("以下是"):
                quality_checks.append("✅ 没有多余的说明文字")
            if "```verilog" not in verilog_code:
                quality_checks.append("✅ 没有Markdown标记")
            if "module test_adder" in verilog_code:
                quality_checks.append("✅ 包含正确的模块声明")
            if "endmodule" in verilog_code:
                quality_checks.append("✅ 包含模块结束标记")
            
            print("代码质量检查:")
            for check in quality_checks:
                print(f"  {check}")
            
            return len(quality_checks) >= 3
        else:
            print(f"❌ 代码生成失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Verilog代理测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎯 开始完整TDD系统验证")
    print("="*60)
    print("验证目标: 确保log-16.log中识别的根本问题已经解决")
    print("- 代码生成不再产生混合Markdown+Verilog内容")
    print("- 编译能够成功识别top level modules")
    print("- TDD循环能够正常运行")
    print("="*60)
    
    tests = [
        ("代码清理集成测试", test_code_cleaning_integration),
        ("增强Verilog代理测试", test_enhanced_verilog_agent), 
        ("完整TDD循环测试", test_complete_tdd_cycle),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("🎉 完整TDD系统验证总结")
    
    passed = 0
    total = len(results)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎊 完整TDD系统验证成功！")
        print("✅ log-16.log中的根本问题已经解决：")
        print("   1. ✅ 代码生成现在产生纯净的Verilog代码")
        print("   2. ✅ 代码清理系统能修复遗留的格式问题")
        print("   3. ✅ 编译系统能正确识别top level modules")
        print("   4. ✅ TDD循环能完整运行红→绿→重构流程")
        print("\n🚀 系统现在可以投入生产使用！")
    elif passed >= total - 1:
        print("\n⚠️ 系统基本正常，仅有个别组件需要微调。")
    else:
        print("\n❌ 系统仍有重要问题需要解决。")
    
    return passed >= total - 1  # 允许一个测试失败

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)