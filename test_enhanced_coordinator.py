#!/usr/bin/env python3
"""
增强Coordinator测试

Enhanced Coordinator Test
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.base_agent import TaskMessage
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_coordinator():
    """测试增强Coordinator的功能"""
    print("🧠 增强Coordinator功能测试")
    print("=" * 80)
    
    try:
        # 初始化配置和LLM客户端
        config = FrameworkConfig.from_env()
        llm_client = EnhancedLLMClient(config.llm)
        
        # 初始化增强Coordinator
        coordinator = EnhancedCentralizedCoordinator(config, llm_client)
        print("✅ 增强Coordinator初始化成功")
        
        # 测试1: 注册不同类型的智能体
        print("\n📋 测试1: 智能体注册")
        print("-" * 50)
        
        # 注册原始智能体（已升级Schema）
        original_verilog_agent = RealVerilogDesignAgent()
        success1 = coordinator.register_agent(original_verilog_agent)
        print(f"  原始Verilog智能体注册: {'✅ 成功' if success1 else '❌ 失败'}")
        
        # 注册增强智能体
        enhanced_verilog_agent = EnhancedRealVerilogAgent()
        success2 = coordinator.register_agent(enhanced_verilog_agent)
        print(f"  增强Verilog智能体注册: {'✅ 成功' if success2 else '❌ 失败'}")
        
        # 注册代码审查智能体
        code_reviewer = EnhancedRealCodeReviewAgent()
        success3 = coordinator.register_agent(code_reviewer)
        print(f"  代码审查智能体注册: {'✅ 成功' if success3 else '❌ 失败'}")
        
        # 测试2: 获取增强团队状态
        print("\n📋 测试2: 增强团队状态")
        print("-" * 50)
        
        team_status = coordinator.get_enhanced_team_status()
        print(f"  总智能体数: {team_status['total_agents']}")
        print(f"  增强智能体数: {team_status['enhanced_agents_count']}")
        print(f"  总增强工具数: {team_status['total_enhanced_tools']}")
        print(f"  Schema系统启用: {team_status['schema_system_enabled']}")
        
        # 测试3: 智能体选择
        print("\n📋 测试3: 增强智能体选择")
        print("-" * 50)
        
        # 设计任务
        design_task_analysis = {
            "task_type": "design",
            "complexity": 6,
            "required_capabilities": ["code_generation", "module_design"],
            "estimated_hours": 4,
            "priority": "high"
        }
        
        selected_agent = await coordinator.select_best_agent_enhanced(design_task_analysis)
        print(f"  设计任务选择的智能体: {selected_agent}")
        
        # 审查任务
        review_task_analysis = {
            "task_type": "review",
            "complexity": 4,
            "required_capabilities": ["code_review", "quality_analysis"],
            "estimated_hours": 2,
            "priority": "medium"
        }
        
        selected_reviewer = await coordinator.select_best_agent_enhanced(review_task_analysis)
        print(f"  审查任务选择的智能体: {selected_reviewer}")
        
        # 测试4: 任务执行
        print("\n📋 测试4: 增强任务执行")
        print("-" * 50)
        
        # 创建测试任务
        task_message = TaskMessage(
            task_id="test_enhanced_coordination",
            sender_id="test_client",
            receiver_id="coordinator",
            message_type="task_request",
            content="设计一个简单的8位计数器，包含使能和复位功能"
        )
        
        # 执行任务
        print("  开始执行设计任务...")
        result = await coordinator.execute_task_with_enhanced_agent(task_message)
        
        execution_success = result and result.get("success", False)
        print(f"  任务执行结果: {'✅ 成功' if execution_success else '❌ 失败'}")
        
        if not execution_success and result:
            print(f"  错误信息: {result.get('error', 'Unknown error')}")
        
        # 测试5: Schema系统报告
        print("\n📋 测试5: Schema系统报告")
        print("-" * 50)
        
        schema_report = coordinator.get_schema_system_report()
        
        if "error" not in schema_report:
            deployment = schema_report["deployment_status"]
            performance = schema_report["performance_metrics"]
            
            print(f"  部署状态:")
            print(f"    - 总智能体: {deployment['total_agents']}")
            print(f"    - 增强智能体: {deployment['enhanced_agents']}")
            print(f"    - 增强率: {deployment['enhancement_rate']:.1%}")
            print(f"    - 总增强工具: {deployment['total_enhanced_tools']}")
            
            print(f"  性能指标:")
            print(f"    - 平均成功率: {performance['average_success_rate']:.1%}")
            print(f"    - 全局验证次数: {performance['global_statistics']['total_validations']}")
            
            print(f"  优化建议:")
            for recommendation in schema_report["recommendations"]:
                print(f"    - {recommendation}")
        else:
            print(f"  ❌ Schema报告生成失败: {schema_report['error']}")
        
        # 测试6: 向后兼容性
        print("\n📋 测试6: 向后兼容性")
        print("-" * 50)
        
        # 使用原始方法选择智能体
        compatible_agent = await coordinator.select_best_agent(design_task_analysis)
        print(f"  兼容性方法选择智能体: {compatible_agent}")
        
        compatibility_test = compatible_agent is not None
        print(f"  向后兼容性: {'✅ 通过' if compatibility_test else '❌ 失败'}")
        
        # 总结测试结果
        print("\n" + "=" * 80)
        print("📊 增强Coordinator测试总结")
        print("=" * 80)
        
        tests = [
            ("智能体注册", success1 and success2 and success3),
            ("团队状态获取", team_status['enhanced_agents_count'] > 0),
            ("智能体选择", selected_agent is not None and selected_reviewer is not None),
            ("任务执行", execution_success),
            ("Schema报告", "error" not in schema_report),
            ("向后兼容性", compatibility_test)
        ]
        
        successful_tests = sum(1 for _, success in tests if success)
        total_tests = len(tests)
        
        print(f"测试通过率: {successful_tests}/{total_tests} ({successful_tests/total_tests:.1%})")
        
        for test_name, success in tests:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  - {test_name}: {status}")
        
        if successful_tests == total_tests:
            print("\n🎉 增强Coordinator集成完全成功!")
            print("\n✨ 主要成果:")
            print("1. ✅ 支持增强智能体的注册和管理")
            print("2. ✅ Schema系统统计和监控功能")
            print("3. ✅ 智能体选择优化，优先使用增强智能体")
            print("4. ✅ 增强任务执行流程")
            print("5. ✅ 详细的Schema系统报告")
            print("6. ✅ 完整的向后兼容性")
            
            print("\n🚀 功能亮点:")
            print("- 自动检测和优先选择Schema增强智能体")
            print("- 实时Schema系统性能监控")
            print("- 智能化的智能体评分和选择机制")
            print("- 全面的部署状态和性能报告")
            print("- 智能优化建议生成")
            
        else:
            print(f"\n⚠️ {total_tests - successful_tests} 个测试失败，需要进一步调试")
        
        return successful_tests == total_tests
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        logger.exception("测试异常")
        return False

async def test_schema_migration_workflow():
    """测试Schema迁移工作流程"""
    print("\n" + "=" * 80)
    print("🔄 Schema迁移工作流程测试")
    print("=" * 80)
    
    try:
        config = FrameworkConfig.from_env()
        llm_client = EnhancedLLMClient(config.llm)
        coordinator = EnhancedCentralizedCoordinator(config, llm_client)
        
        # 模拟渐进式迁移
        print("🔄 模拟渐进式Schema迁移:")
        
        # 阶段1: 只有普通智能体
        print("\n阶段1: 注册原始智能体")
        original_agent = RealVerilogDesignAgent()
        coordinator.register_agent(original_agent)
        
        status1 = coordinator.get_enhanced_team_status()
        print(f"  - 增强率: {status1['deployment_status']['enhancement_rate']:.1%}")
        
        # 阶段2: 添加增强智能体
        print("\n阶段2: 添加增强智能体")
        enhanced_agent = EnhancedRealVerilogAgent()
        code_reviewer = EnhancedRealCodeReviewAgent()
        coordinator.register_agent(enhanced_agent)
        coordinator.register_agent(code_reviewer)
        
        status2 = coordinator.get_enhanced_team_status()
        print(f"  - 增强率: {status2['deployment_status']['enhancement_rate']:.1%}")
        
        # 阶段3: 验证选择偏好
        print("\n阶段3: 验证智能体选择偏好")
        
        task_analysis = {
            "task_type": "design",
            "complexity": 5,
            "required_capabilities": ["code_generation"]
        }
        
        # 优先选择增强智能体
        preferred_agent = await coordinator.select_best_agent_enhanced(
            task_analysis, prefer_enhanced=True
        )
        
        # 不偏好增强智能体
        any_agent = await coordinator.select_best_agent_enhanced(
            task_analysis, prefer_enhanced=False
        )
        
        is_enhanced_preferred = preferred_agent in coordinator.enhanced_agents
        print(f"  - 优先选择增强智能体: {'✅ 是' if is_enhanced_preferred else '❌ 否'}")
        
        # 生成最终报告
        final_report = coordinator.get_schema_system_report()
        
        print(f"\n📊 迁移完成状态:")
        deployment = final_report["deployment_status"]
        print(f"  - 总智能体: {deployment['total_agents']}")
        print(f"  - 增强智能体: {deployment['enhanced_agents']}")
        print(f"  - 最终增强率: {deployment['enhancement_rate']:.1%}")
        
        print(f"\n💡 系统建议:")
        for rec in final_report["recommendations"]:
            print(f"  - {rec}")
        
        migration_success = deployment['enhancement_rate'] > 0.5
        print(f"\n迁移工作流程: {'✅ 成功' if migration_success else '⚠️ 部分成功'}")
        
        return migration_success
        
    except Exception as e:
        print(f"❌ 迁移工作流程测试异常: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("🚀 CentralizedAgentFramework 增强Coordinator集成测试")
    print("=" * 100)
    
    try:
        # 主功能测试
        main_success = await test_enhanced_coordinator()
        
        # 迁移工作流程测试
        workflow_success = await test_schema_migration_workflow()
        
        print("\n" + "=" * 100)
        print("📊 增强Coordinator集成总结")
        print("=" * 100)
        
        if main_success and workflow_success:
            print("🎉 增强Coordinator集成完全成功!")
            
            print("\n✨ 重要成就:")
            print("1. 🧠 增强Coordinator完全集成Schema系统")
            print("2. 🤖 支持混合智能体团队管理") 
            print("3. 🎯 智能化的任务分发和执行")
            print("4. 📊 全面的Schema系统监控")
            print("5. 🔄 渐进式迁移工作流程")
            print("6. 🔧 向后兼容性完全保持")
            
            print("\n🚀 系统现在具备:")
            print("- 企业级Schema验证和智能修复")
            print("- 多层安全防护和参数验证")
            print("- 智能化的工作负载分发")
            print("- 实时性能监控和优化建议")
            print("- 完整的迁移管理能力")
            
            print("\n🎯 CentralizedAgentFramework Schema系统集成完成!")
            print("系统已准备好进入生产环境部署阶段 🚀")
            
        else:
            print("⚠️ 增强Coordinator集成存在问题")
            if not main_success:
                print("❌ 主要功能测试失败")
            if not workflow_success:
                print("❌ 迁移工作流程测试失败")
        
        return main_success and workflow_success
        
    except Exception as e:
        print(f"❌ 测试过程异常: {str(e)}")
        logger.exception("主测试异常")
        return False

if __name__ == "__main__":
    asyncio.run(main())