#!/usr/bin/env python3
"""
数据库集成示例

Database Integration Example for Centralized Agent Framework
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.verilog_design_agent import VerilogDesignAgent
from agents.verilog_test_agent import VerilogTestAgent
from agents.verilog_review_agent import VerilogReviewAgent
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from tools.sample_database import setup_database_for_framework


async def test_database_tools():
    """测试数据库工具功能"""
    print("🗄️ 测试数据库工具功能...")
    
    # 设置数据库
    db_path = "output/sample_verilog.db"
    await setup_database_for_framework(db_path)
    
    # 创建一个设计智能体进行测试
    design_agent = VerilogDesignAgent()
    
    print("\n1. 🔍 测试模块搜索...")
    search_result = await design_agent.search_database_modules(
        module_name="alu",
        description="arithmetic",
        limit=3
    )
    
    print(f"搜索结果: {search_result.get('success')}")
    if search_result.get('success'):
        data = search_result.get('result', {}).get('data', [])
        print(f"找到 {len(data)} 个模块:")
        for module in data:
            print(f"  - {module.get('name')}: {module.get('description')}")
    
    print("\n2. 🎯 测试功能搜索...")
    func_result = await design_agent.search_by_functionality(
        functionality="counter",
        tags="sequential",
        limit=2
    )
    
    print(f"功能搜索结果: {func_result.get('success')}")
    if func_result.get('success'):
        data = func_result.get('result', {}).get('data', [])
        print(f"找到 {len(data)} 个匹配模块:")
        for module in data:
            print(f"  - {module.get('name')}: {module.get('functionality')}")
    
    print("\n3. 📋 测试获取数据库架构...")
    schema_result = await design_agent.get_database_schema()
    
    print(f"架构获取结果: {schema_result.get('success')}")
    if schema_result.get('success'):
        schema = schema_result.get('result', {})
        tables = schema.get('tables', {})
        print(f"数据库包含 {len(tables)} 个表:")
        for table_name, table_info in tables.items():
            row_count = table_info.get('row_count', 0)
            print(f"  - {table_name}: {row_count} 行")
    
    print("\n4. 💾 测试保存查询结果...")
    if search_result.get('success'):
        save_result = await design_agent.save_database_result_to_file(
            query_result=search_result['result'],
            file_path="output/search_results.json",
            format_type="json"
        )
        
        print(f"保存结果: {save_result.get('success')}")
        if save_result.get('success'):
            print(f"文件已保存: {save_result.get('file_path')}")
    
    return True


async def test_enhanced_design_workflow():
    """测试增强的设计工作流程"""
    print("\n🚀 测试增强的设计工作流程...")
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 1. 设置数据库
        db_path = "output/sample_verilog.db"
        await setup_database_for_framework(db_path)
        
        # 2. 配置框架
        config = FrameworkConfig.from_env()
        
        # 3. 创建LLM客户端（如果有API密钥）
        llm_client = None
        if config.llm.api_key:
            llm_client = EnhancedLLMClient(config.llm)
            print("✅ LLM客户端创建完成")
        else:
            print("⚠️ 未配置API密钥，将使用离线模式")
        
        # 4. 创建协调者和智能体
        coordinator = CentralizedCoordinator(config, llm_client)
        
        design_agent = VerilogDesignAgent(llm_client)
        test_agent = VerilogTestAgent(llm_client)
        review_agent = VerilogReviewAgent(llm_client)
        
        # 注册智能体
        coordinator.register_agent(design_agent)
        coordinator.register_agent(test_agent)
        coordinator.register_agent(review_agent)
        
        print(f"✅ 框架初始化完成，注册了 {len(coordinator.registered_agents)} 个智能体")
        
        # 5. 执行带数据库检索的设计任务
        task_description = """
设计一个16位加法器模块，要求：
1. 支持进位输入和输出
2. 组合逻辑实现
3. 参考现有的加法器设计
4. 生成相应的测试用例
"""
        
        print(f"\n🎯 开始执行任务...")
        print(f"任务: {task_description.strip()}")
        
        # 6. 协调任务执行
        result = await coordinator.coordinate_task_execution(
            initial_task=task_description,
            context={"database_enabled": True, "priority": "high"}
        )
        
        # 7. 显示执行结果
        print(f"\n📊 任务执行结果:")
        print(f"- 成功状态: {result.get('success', False)}")
        print(f"- 对话ID: {result.get('conversation_id', 'N/A')}")
        print(f"- 总轮次: {result.get('total_iterations', 0)}")
        print(f"- 执行时间: {result.get('duration', 0):.2f}秒")
        print(f"- 生成文件: {len(result.get('file_references', []))}")
        
        # 8. 显示生成的文件
        if result.get('file_references'):
            print(f"\n📁 生成的文件:")
            for file_ref in result.get('file_references', []):
                if isinstance(file_ref, dict):
                    file_path = file_ref.get('file_path', 'Unknown')
                    file_type = file_ref.get('file_type', 'Unknown')
                else:
                    file_path = file_ref.file_path
                    file_type = file_ref.file_type
                print(f"- {file_path} ({file_type})")
        
        # 9. 保存对话日志
        try:
            log_path = coordinator.save_conversation_log("output/database_integration_conversation.json")
            print(f"\n💾 对话日志已保存: {log_path}")
        except Exception as e:
            print(f"⚠️ 保存对话日志失败: {str(e)}")
        
        # 10. 显示统计信息
        stats = coordinator.get_conversation_statistics()
        print(f"\n📈 对话统计:")
        print(f"- 总对话数: {stats['total_conversations']}")
        print(f"- 总轮次: {stats['total_rounds']}")
        print(f"- 智能体活动: {len(stats.get('agent_activity', {}))}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 数据库集成测试开始...")
    
    try:
        # 确保输出目录存在
        Path("output").mkdir(exist_ok=True)
        
        # 测试数据库工具
        db_test_success = await test_database_tools()
        
        if db_test_success:
            print("\n" + "="*60)
            # 测试完整工作流程
            workflow_success = await test_enhanced_design_workflow()
            
            if workflow_success:
                print("\n✅ 所有测试通过！数据库集成成功！")
                return 0
            else:
                print("\n⚠️ 工作流程测试失败")
                return 1
        else:
            print("\n❌ 数据库工具测试失败")
            return 1
            
    except Exception as e:
        print(f"❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)