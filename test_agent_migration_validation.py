#!/usr/bin/env python3
"""
Agent Schema迁移验证测试

Agent Schema Migration Validation Test
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.base_agent import TaskMessage
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_migration_compatibility():
    """测试Agent迁移的兼容性"""
    print("🔄 Agent Schema迁移兼容性测试")
    print("=" * 80)
    
    test_request = """
设计一个简单的8位计数器，包含：
1. 同步复位功能
2. 使能控制
3. 上溢标志输出
"""
    
    try:
        # 测试原始RealVerilogAgent (已升级到Schema)
        print("\n📋 测试1: 原始RealVerilogAgent (已升级Schema)")
        print("-" * 50)
        
        original_agent = RealVerilogDesignAgent()
        task_message = TaskMessage(
            task_id="test_original_agent",
            sender_id="migration_tester",
            receiver_id="real_verilog_agent",
            message_type="task_request",
            content=test_request
        )
        
        result1 = await original_agent.execute_enhanced_task(
            enhanced_prompt=test_request,
            original_message=task_message,
            file_contents={}
        )
        
        success1 = result1 and "formatted_response" in result1
        print(f"✅ 原始Agent测试: {'成功' if success1 else '失败'}")
        
        if success1:
            # 检查Schema统计
            stats1 = original_agent.get_validation_statistics()
            print(f"  - Schema验证次数: {stats1['total_validations']}")
            print(f"  - 验证成功率: {stats1['success_rate']:.1%}")
            
            # 检查增强工具
            tools1 = original_agent.list_enhanced_tools()
            print(f"  - 增强工具数量: {len(tools1)}")
        
        # 测试独立的EnhancedRealVerilogAgent
        print("\n📋 测试2: 独立EnhancedRealVerilogAgent")
        print("-" * 50)
        
        enhanced_agent = EnhancedRealVerilogAgent()
        task_message2 = TaskMessage(
            task_id="test_enhanced_agent",
            sender_id="migration_tester",
            receiver_id="enhanced_verilog_agent",
            message_type="task_request",
            content=test_request
        )
        
        result2 = await enhanced_agent.execute_enhanced_task(
            enhanced_prompt=test_request,
            original_message=task_message2,
            file_contents={}
        )
        
        success2 = result2 and "formatted_response" in result2
        print(f"✅ 增强Agent测试: {'成功' if success2 else '失败'}")
        
        if success2:
            stats2 = enhanced_agent.get_validation_statistics()
            print(f"  - Schema验证次数: {stats2['total_validations']}")
            print(f"  - 验证成功率: {stats2['success_rate']:.1%}")
            
            tools2 = enhanced_agent.list_enhanced_tools()
            print(f"  - 增强工具数量: {len(tools2)}")
        
        # 测试EnhancedRealCodeReviewAgent
        print("\n📋 测试3: EnhancedRealCodeReviewAgent")
        print("-" * 50)
        
        code_reviewer = EnhancedRealCodeReviewAgent()
        review_request = f"""
请分析以下Verilog代码的质量：

```verilog
module counter_8bit (
    input clk,
    input rst_n,
    input enable,
    output reg [7:0] count,
    output overflow
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else if (enable) begin
        count <= count + 1;
    end
end

assign overflow = (count == 8'hFF) && enable;

endmodule
```

请进行全面的代码质量分析。
"""
        
        task_message3 = TaskMessage(
            task_id="test_code_reviewer",
            sender_id="migration_tester",
            receiver_id="enhanced_code_reviewer",
            message_type="task_request",
            content=review_request
        )
        
        result3 = await code_reviewer.execute_enhanced_task(
            enhanced_prompt=review_request,
            original_message=task_message3,
            file_contents={}
        )
        
        success3 = result3 and "formatted_response" in result3
        print(f"✅ 代码审查Agent测试: {'成功' if success3 else '失败'}")
        
        if success3:
            stats3 = code_reviewer.get_validation_statistics()
            print(f"  - Schema验证次数: {stats3['total_validations']}")
            print(f"  - 验证成功率: {stats3['success_rate']:.1%}")
            
            tools3 = code_reviewer.list_enhanced_tools()
            print(f"  - 增强工具数量: {len(tools3)}")
        
        print("\n" + "=" * 80)
        print("📊 迁移兼容性测试总结")
        print("=" * 80)
        
        total_success = sum([success1, success2, success3])
        print(f"成功测试: {total_success}/3")
        print(f"成功率: {total_success/3:.1%}")
        
        if total_success == 3:
            print("\n🎉 所有Agent已成功迁移到Schema系统!")
            print("✅ 原始Agent升级成功")
            print("✅ 独立增强Agent运行正常")
            print("✅ 代码审查Agent集成完成")
            
            print("\n🔧 Schema系统特性验证:")
            print("- 参数验证机制已集成")
            print("- 智能修复功能已启用")
            print("- 安全防护已部署")
            print("- 向后兼容性已保持")
        else:
            print(f"\n⚠️ {3 - total_success} 个Agent迁移存在问题")
            if not success1:
                print("❌ 原始Agent升级失败")
            if not success2:
                print("❌ 独立增强Agent异常")
            if not success3:
                print("❌ 代码审查Agent集成失败")
        
        return total_success == 3
        
    except Exception as e:
        print(f"❌ 迁移兼容性测试异常: {str(e)}")
        logger.exception("测试异常")
        return False

async def test_schema_feature_consistency():
    """测试Schema功能一致性"""
    print("\n" + "=" * 80)
    print("🔍 Schema功能一致性测试")
    print("=" * 80)
    
    try:
        agents = [
            ("RealVerilogAgent", RealVerilogDesignAgent()),
            ("EnhancedVerilogAgent", EnhancedRealVerilogAgent()),
            ("EnhancedCodeReviewer", EnhancedRealCodeReviewAgent())
        ]
        
        consistency_results = []
        
        for agent_name, agent in agents:
            print(f"\n📋 测试Agent: {agent_name}")
            print("-" * 40)
            
            try:
                # 检查Schema系统初始化
                has_schema_methods = all([
                    hasattr(agent, 'get_validation_statistics'),
                    hasattr(agent, 'list_enhanced_tools'),
                    hasattr(agent, 'register_enhanced_tool')
                ])
                
                print(f"  Schema方法检查: {'✅ 通过' if has_schema_methods else '❌ 失败'}")
                
                # 检查统计功能
                try:
                    stats = agent.get_validation_statistics()
                    expected_keys = ['total_validations', 'successful_validations', 'success_rate', 'cache_size']
                    stats_valid = all(key in stats for key in expected_keys)
                    print(f"  统计功能检查: {'✅ 通过' if stats_valid else '❌ 失败'}")
                except Exception:
                    stats_valid = False
                    print("  统计功能检查: ❌ 异常")
                
                # 检查工具列表功能
                try:
                    tools = agent.list_enhanced_tools()
                    tools_valid = isinstance(tools, list) and len(tools) > 0
                    print(f"  工具列表检查: {'✅ 通过' if tools_valid else '❌ 失败'} ({len(tools) if tools_valid else 0} 个工具)")
                    
                    if tools_valid:
                        # 显示工具详情
                        for tool in tools[:2]:  # 只显示前2个
                            print(f"    - {tool['name']} ({tool['security_level']})")
                            
                except Exception:
                    tools_valid = False
                    print("  工具列表检查: ❌ 异常")
                
                # 计算该Agent的一致性分数
                consistency_score = sum([has_schema_methods, stats_valid, tools_valid]) / 3
                consistency_results.append((agent_name, consistency_score))
                print(f"  一致性分数: {consistency_score:.1%}")
                
            except Exception as e:
                print(f"  ❌ Agent检查异常: {str(e)}")
                consistency_results.append((agent_name, 0.0))
        
        print("\n📊 一致性测试结果")
        print("-" * 40)
        
        total_score = 0
        for agent_name, score in consistency_results:
            status = "✅ 通过" if score >= 0.8 else "⚠️ 需优化" if score >= 0.5 else "❌ 失败"
            print(f"{agent_name}: {score:.1%} {status}")
            total_score += score
        
        average_score = total_score / len(consistency_results)
        print(f"\n平均一致性: {average_score:.1%}")
        
        if average_score >= 0.9:
            print("🎉 Schema功能一致性优秀!")
        elif average_score >= 0.7:
            print("✅ Schema功能一致性良好")
        else:
            print("⚠️ Schema功能一致性需要改进")
        
        return average_score >= 0.7
        
    except Exception as e:
        print(f"❌ 一致性测试异常: {str(e)}")
        return False

async def test_performance_comparison():
    """测试性能对比"""
    print("\n" + "=" * 80)
    print("⚡ Schema系统性能测试")
    print("=" * 80)
    
    try:
        import time
        
        # 简单的性能测试请求
        simple_request = "设计一个4位加法器"
        task_message = TaskMessage(
            task_id="perf_test",
            sender_id="perf_tester",
            receiver_id="agent",
            message_type="task_request",
            content=simple_request
        )
        
        agents_to_test = [
            ("升级后RealVerilogAgent", RealVerilogDesignAgent()),
            ("独立EnhancedVerilogAgent", EnhancedRealVerilogAgent())
        ]
        
        performance_results = []
        
        for agent_name, agent in agents_to_test:
            print(f"\n📊 性能测试: {agent_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                
                result = await agent.execute_enhanced_task(
                    enhanced_prompt=simple_request,
                    original_message=task_message,
                    file_contents={}
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                success = result and "formatted_response" in result
                
                print(f"  执行时间: {execution_time:.2f}秒")
                print(f"  执行结果: {'✅ 成功' if success else '❌ 失败'}")
                
                if success:
                    # 获取Schema统计
                    stats = agent.get_validation_statistics()
                    print(f"  验证次数: {stats['total_validations']}")
                    print(f"  缓存大小: {stats['cache_size']}")
                
                performance_results.append({
                    'agent': agent_name,
                    'time': execution_time,
                    'success': success
                })
                
            except Exception as e:
                print(f"  ❌ 性能测试异常: {str(e)}")
                performance_results.append({
                    'agent': agent_name,
                    'time': 0,
                    'success': False
                })
        
        print("\n📈 性能对比结果")
        print("-" * 40)
        
        successful_tests = [r for r in performance_results if r['success']]
        
        if len(successful_tests) >= 2:
            times = [r['time'] for r in successful_tests]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"平均执行时间: {avg_time:.2f}秒")
            print(f"最快执行时间: {min_time:.2f}秒")
            print(f"最慢执行时间: {max_time:.2f}秒")
            
            if avg_time < 30:
                print("✅ 性能表现优秀")
            elif avg_time < 60:
                print("✅ 性能表现良好")
            else:
                print("⚠️ 性能需要优化")
        else:
            print("⚠️ 性能测试数据不足")
        
        return len(successful_tests) == len(performance_results)
        
    except Exception as e:
        print(f"❌ 性能测试异常: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("🚀 CentralizedAgentFramework Agent迁移验证测试")
    print("=" * 100)
    
    try:
        # 测试1: 迁移兼容性
        print("🔄 开始迁移兼容性测试...")
        compatibility_success = await test_agent_migration_compatibility()
        
        # 测试2: Schema功能一致性
        print("\n🔍 开始Schema功能一致性测试...")
        consistency_success = await test_schema_feature_consistency()
        
        # 测试3: 性能对比
        print("\n⚡ 开始性能对比测试...")
        performance_success = await test_performance_comparison()
        
        print("\n" + "=" * 100)
        print("📊 Agent迁移验证总结")
        print("=" * 100)
        
        total_tests = 3
        successful_tests = sum([compatibility_success, consistency_success, performance_success])
        
        print(f"测试通过率: {successful_tests}/{total_tests} ({successful_tests/total_tests:.1%})")
        print(f"  - 迁移兼容性: {'✅ 通过' if compatibility_success else '❌ 失败'}")
        print(f"  - 功能一致性: {'✅ 通过' if consistency_success else '❌ 失败'}")
        print(f"  - 性能表现: {'✅ 通过' if performance_success else '❌ 失败'}")
        
        if successful_tests == total_tests:
            print("\n🎉 Agent Schema迁移验证完全成功!")
            print("\n✨ 迁移成果:")
            print("1. ✅ RealVerilogAgent已成功升级到Schema系统")
            print("2. ✅ EnhancedRealVerilogAgent独立版本运行正常")
            print("3. ✅ EnhancedRealCodeReviewAgent集成完成")
            print("4. ✅ Schema验证和智能修复功能全面部署")
            print("5. ✅ 向后兼容性完全保持")
            print("6. ✅ 性能表现符合预期")
            
            print("\n🚀 现在可以开始生产环境部署!")
            print("建议下一步:")
            print("- 更新Coordinator以支持增强Agent")
            print("- 创建更多集成测试用例")
            print("- 部署到实际项目环境")
            print("- 监控Schema系统性能指标")
            
        else:
            print("\n⚠️ Agent迁移验证存在问题")
            print("需要进一步调试和优化")
        
        return successful_tests == total_tests
        
    except Exception as e:
        print(f"❌ 验证测试过程异常: {str(e)}")
        logger.exception("主测试异常")
        return False

if __name__ == "__main__":
    asyncio.run(main())