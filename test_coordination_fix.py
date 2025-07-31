#!/usr/bin/env python3
"""
协调智能体修复测试

Test Coordination Agent Fix
"""

import asyncio
import time
from pathlib import Path

from config.config import FrameworkConfig
from core.real_centralized_coordinator import RealCentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入增强日志系统
from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_test_logger, 
    get_artifacts_dir
)


async def test_coordination_fix():
    """测试协调智能体修复效果"""
    
    # 初始化增强日志系统
    logger_manager = setup_enhanced_logging()
    logger = get_test_logger()
    artifacts_dir = get_artifacts_dir()
    
    logger.info("开始协调智能体修复测试")
    print("🚀 协调智能体修复测试")
    print(f"📁 实验目录: {logger_manager.get_session_dir()}")
    print(f"🛠️ 工件目录: {artifacts_dir}")
    
    try:
        # 创建协调智能体
        config = FrameworkConfig.from_env()
        coordinator = RealCentralizedCoordinator(config)
        
        # 创建和注册专业智能体
        verilog_agent = RealVerilogDesignAgent(config)
        review_agent = RealCodeReviewAgent(config)
        
        coordinator.register_agent(verilog_agent)
        coordinator.register_agent(review_agent)
        
        print(f"✅ 协调智能体创建完成，注册了 {len(coordinator.registered_agents)} 个智能体")
        
        # 定义一个简单明确的任务
        simple_task = """
设计一个4位二进制加法器模块，要求：
1. 输入：两个4位数据 A[3:0] 和 B[3:0]，以及进位输入 Cin  
2. 输出：4位和 Sum[3:0] 和进位输出 Cout
3. 使用Verilog HDL编写
4. 保存到文件中

设计完成后，生成测试台验证功能正确性。
"""
        
        print("📋 测试任务:")
        print(simple_task.strip())
        
        # 通过协调智能体处理任务
        start_time = time.time()
        result = await coordinator.process_user_task(simple_task, max_rounds=6)
        execution_time = time.time() - start_time
        
        print(f"\n📊 协调执行结果:")
        print(f"  🎯 任务成功: {result.get('success', False)}")
        print(f"  🆔 对话ID: {result.get('conversation_id', 'N/A')}")
        print(f"  ⏱️ 执行时间: {execution_time:.2f}秒")
        print(f"  🔄 执行轮次: {result.get('execution_summary', {}).get('total_rounds', 0)}")
        print(f"  📋 完成任务数: {result.get('execution_summary', {}).get('successful_tasks', 0)}")
        print(f"  📁 生成文件数: {result.get('execution_summary', {}).get('generated_files', 0)}")
        
        # 显示任务执行详情
        if result.get('task_results'):
            print(f"\n📋 任务执行详情:")
            for i, task in enumerate(result['task_results']):
                print(f"  {i+1}. 任务 {task.get('task_id', 'N/A')}")
                print(f"     - 智能体: {task.get('agent_id', 'N/A')}")
                print(f"     - 状态: {task.get('status', 'N/A')}")
                print(f"     - 执行时间: {task.get('execution_time', 0):.2f}秒")
                
                # 显示响应摘要
                result_data = task.get('result_data', {})
                if 'response' in result_data:
                    response = result_data['response']
                    print(f"     - 响应长度: {len(response)}字符")
        
        # 显示生成的文件
        if result.get('generated_files'):
            print(f"\n📁 生成的文件:")
            for file_path in result['generated_files'][:5]:  # 显示前5个文件
                file_name = Path(file_path).name
                print(f"  - {file_name}")
            if len(result['generated_files']) > 5:
                print(f"  ... 还有 {len(result['generated_files']) - 5} 个文件")
                
        # 创建会话摘要
        logger_manager.create_session_summary()
        
        success = result.get('success', False)
        task_count = result.get('execution_summary', {}).get('successful_tasks', 0)
        
        if success and task_count >= 1:
            print(f"\n🎉 协调智能体修复成功！")
            print(f"  ✅ 成功完成 {task_count} 个任务")
            print(f"  🤖 智能体协作正常工作")
            return True
        else:
            print(f"\n⚠️ 协调智能体仍需优化")
            print(f"  📊 完成任务数: {task_count}")
            return False
            
    except Exception as e:
        logger.error(f"协调智能体测试失败: {str(e)}")
        print(f"❌ 协调智能体测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    success = await test_coordination_fix()
    
    if success:
        print(f"\n🎊 测试通过：协调智能体修复成功！")
    else:
        print(f"\n🔧 测试失败：协调智能体需要进一步调试")


if __name__ == "__main__":
    asyncio.run(main())