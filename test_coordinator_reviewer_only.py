#!/usr/bin/env python3
"""
专门测试协调智能体和审查智能体协作的实验
不涉及设计智能体，专注于两者的协作能力
"""

import asyncio
import sys
import tempfile
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_coordinator_reviewer_collaboration():
    """测试协调器和审查智能体的直接协作"""
    
    print("🧪 协调器+审查智能体协作测试")
    print("=" * 60)
    
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        print("1️⃣ 初始化智能体...")
        coordinator = LLMCoordinatorAgent(config)
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        # 手动注册审查智能体到协调器
        coordinator.register_agent(reviewer)
        print(f"   ✅ 协调器初始化: {coordinator.agent_id}")
        print(f"   ✅ 审查智能体初始化: {reviewer.agent_id}")
        print(f"   📋 已注册智能体数量: {len(coordinator.registered_agents)}")
        
        # 准备一个现成的Verilog文件供审查
        print("\n2️⃣ 准备测试用Verilog文件...")
        test_verilog_content = """// 简单的4位计数器
module simple_counter(
    input clk,
    input reset,
    output reg [3:0] count
);

always @(posedge clk or posedge reset) begin
    if (reset)
        count <= 4'b0000;
    else
        count <= count + 1;
end

endmodule"""
        
        # 创建临时文件
        test_dir = Path("./test_coordinator_reviewer")
        test_dir.mkdir(exist_ok=True)
        
        verilog_file = test_dir / "simple_counter.v"
        with open(verilog_file, 'w') as f:
            f.write(test_verilog_content)
        
        print(f"   📁 测试文件创建: {verilog_file}")
        print(f"   📄 文件内容: {len(test_verilog_content)} 字符")
        
        # 设计一个只需要审查智能体的任务
        task_request = f"""请对以下Verilog模块进行代码审查和验证：

文件路径: {verilog_file}

要求：
1. 分析代码质量和设计规范
2. 生成完整的测试台（testbench）
3. 运行仿真验证功能正确性
4. 提供改进建议（如果有）

这是一个纯审查和验证任务，不需要重新设计模块。"""
        
        print("\n3️⃣ 测试任务:")
        print("=" * 50)
        print(task_request)
        print("=" * 50)
        
        # 执行协调器处理
        print("\n4️⃣ 执行协调器处理...")
        start_time = time.time()
        
        result = await coordinator.process_user_request(
            task_request,
            conversation_id=f"coord_reviewer_test_{int(time.time())}"
        )
        
        execution_time = time.time() - start_time
        print(f"\n✅ 处理完成！耗时: {execution_time:.2f}秒")
        
        # 分析结果
        print("\n5️⃣ 结果分析:")
        print(f"   📊 结果类型: {type(result)}")
        print(f"   🎯 处理是否成功: {result.get('success', 'Unknown')}")
        
        if isinstance(result, dict):
            if 'final_result' in result:
                final_result = result['final_result']
                if isinstance(final_result, str):
                    print(f"   📝 最终结果长度: {len(final_result)} 字符")
                    print(f"   📄 结果预览:")
                    preview = final_result[:300] + "..." if len(final_result) > 300 else final_result
                    print(f"      {preview}")
                else:
                    print(f"   📋 最终结果: {final_result}")
            
            if 'assigned_agent' in result:
                print(f"   🤖 分配给智能体: {result['assigned_agent']}")
            
            if 'task_type' in result:
                print(f"   📋 任务类型: {result['task_type']}")
        
        # 检查是否生成了测试文件
        print("\n6️⃣ 检查生成的文件:")
        generated_files = []
        
        # 检查测试目录
        if test_dir.exists():
            for file_path in test_dir.rglob("*.v"):
                if file_path != verilog_file:  # 排除原始文件
                    generated_files.append(file_path)
        
        # 检查实验目录
        experiment_dirs = list(Path(".").glob("experiments/*/"))
        latest_experiment = None
        if experiment_dirs:
            latest_experiment = max(experiment_dirs, key=lambda p: p.stat().st_mtime)
            print(f"   📁 最新实验目录: {latest_experiment}")
            
            for file_path in latest_experiment.rglob("*.v"):
                generated_files.append(file_path)
        
        if generated_files:
            print(f"   📄 生成的Verilog文件: {len(generated_files)} 个")
            for file_path in generated_files[:5]:  # 显示前5个
                print(f"      - {file_path}")
                try:
                    file_size = file_path.stat().st_size
                    print(f"        大小: {file_size} 字节")
                except:
                    pass
        else:
            print("   ⚠️ 未发现生成的Verilog文件")
        
        # 清理测试文件
        print("\n7️⃣ 清理测试环境...")
        try:
            if verilog_file.exists():
                verilog_file.unlink()
            if test_dir.exists() and not any(test_dir.iterdir()):
                test_dir.rmdir()
            print("   🧹 测试文件清理完成")
        except Exception as e:
            print(f"   ⚠️ 清理失败: {e}")
        
        return result.get('success', False) if isinstance(result, dict) else False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_coordinator_task_identification():
    """测试协调器的任务识别能力"""
    
    print("\n" + "=" * 60)
    print("🧪 协调器任务识别测试")
    print("=" * 60)
    
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 测试不同类型的任务
        test_cases = [
            {
                "name": "代码审查任务",
                "request": "请审查我的Verilog代码并生成测试台进行验证",
                "expected_type": "verification"
            },
            {
                "name": "测试任务", 
                "request": "为我的counter.v文件生成testbench并运行仿真",
                "expected_type": "verification"
            },
            {
                "name": "分析任务",
                "request": "分析这个Verilog模块的代码质量，给出改进建议",
                "expected_type": "verification"
            },
            {
                "name": "设计任务",
                "request": "设计一个新的8位ALU模块",
                "expected_type": "design"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}️⃣ 测试: {test_case['name']}")
            print(f"   请求: {test_case['request']}")
            
            start_time = time.time()
            
            # 只调用任务识别，不执行完整流程
            try:
                # 直接调用任务识别工具
                task_id_result = await coordinator._tool_identify_task_type(
                    user_request=test_case['request']
                )
                
                execution_time = time.time() - start_time
                
                print(f"   ⏱️ 识别耗时: {execution_time:.2f}秒")
                print(f"   📋 识别结果: {task_id_result}")
                
                identified_type = task_id_result.get('task_type') if isinstance(task_id_result, dict) else None
                expected_type = test_case['expected_type']
                
                success = identified_type == expected_type
                results.append(success)
                
                print(f"   🎯 预期类型: {expected_type}")
                print(f"   🔍 识别类型: {identified_type}")
                print(f"   ✅ 识别正确: {'是' if success else '否'}")
                
            except Exception as e:
                print(f"   ❌ 识别失败: {e}")
                results.append(False)
        
        # 汇总结果
        success_count = sum(results)
        total_count = len(results)
        success_rate = success_count / total_count * 100
        
        print(f"\n📊 任务识别测试汇总:")
        print(f"   成功: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        return success_rate >= 75.0  # 75%以上算成功
        
    except Exception as e:
        print(f"❌ 任务识别测试失败: {e}")
        return False

async def test_reviewer_direct_call():
    """测试直接调用审查智能体（不通过协调器）"""
    
    print("\n" + "=" * 60)
    print("🧪 审查智能体直接调用测试")
    print("=" * 60)
    
    try:
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        print("✅ 审查智能体初始化成功")
        
        # 创建简单的测试代码
        test_code = """module test_and_gate(
    input a,
    input b, 
    output y
);

assign y = a & b;

endmodule"""
        
        task = f"""请为以下简单的与门模块生成测试台并验证功能：

{test_code}

要求：
1. 生成testbench文件
2. 测试所有输入组合 (00, 01, 10, 11)
3. 验证输出正确性"""
        
        print(f"\n📋 测试任务:")
        print(test_code)
        
        start_time = time.time()
        
        result = await reviewer.process_with_function_calling(
            task,
            max_iterations=3,
            conversation_id=f"reviewer_direct_test_{int(time.time())}"
        )
        
        execution_time = time.time() - start_time
        
        print(f"\n✅ 审查智能体处理完成！")
        print(f"⏱️ 耗时: {execution_time:.2f}秒") 
        print(f"📊 结果类型: {type(result)}")
        
        if isinstance(result, str):
            print(f"📝 结果长度: {len(result)} 字符")
            preview = result[:200] + "..." if len(result) > 200 else result
            print(f"📄 结果预览: {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ 审查智能体直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 协调器+审查智能体专项测试")
    print("专注测试两者协作，避免设计智能体干扰")
    
    async def run_all_tests():
        results = []
        
        # 运行所有测试
        print("\n🚀 开始测试...")
        
        test1_result = await test_coordinator_task_identification()
        results.append(("任务识别", test1_result))
        
        test2_result = await test_reviewer_direct_call()  
        results.append(("审查智能体直接调用", test2_result))
        
        test3_result = await test_coordinator_reviewer_collaboration()
        results.append(("协调器+审查智能体协作", test3_result))
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")
        
        for test_name, success in results:
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        success_count = sum(1 for _, success in results if success)
        total_count = len(results)
        
        print(f"\n🎯 总体结果: {success_count}/{total_count} 测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试通过！协调器和审查智能体协作正常！")
        else:
            print("⚠️ 部分测试失败，需要进一步调试")
    
    asyncio.run(run_all_tests())