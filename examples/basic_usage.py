#!/usr/bin/env python3
"""
基础使用示例

Basic Usage Example for Centralized Agent Framework
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
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from llm_integration.enhanced_llm_client import EnhancedLLMClient


async def main():
    """主函数演示基础用法"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 启动中心化智能体框架演示...")
    
    try:
        # 1. 加载配置
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载完成: LLM提供商={config.llm.provider}")
        
        # 2. 创建LLM客户端
        llm_client = None
        if config.llm.api_key:
            llm_client = EnhancedLLMClient(config.llm)
            print("✅ LLM客户端创建完成")
        else:
            print("⚠️ 未配置API密钥，将使用离线模式")
        
        # 3. 创建协调者
        coordinator = LLMCoordinatorAgent(config, llm_client)
        print("✅ 中心化协调者创建完成")
        
        # 4. 创建专业智能体
        design_agent = VerilogDesignAgent(llm_client)
        test_agent = VerilogTestAgent(llm_client)
        review_agent = VerilogReviewAgent(llm_client)
        
        # 5. 注册智能体到协调者
        coordinator.register_agent(design_agent)
        coordinator.register_agent(test_agent)
        coordinator.register_agent(review_agent)
        
        print(f"✅ 智能体注册完成: {len(coordinator.registered_agents)} 个智能体")
        
        # 6. 显示团队状态
        team_status = coordinator.get_team_status()
        print(f"\n📊 团队状态:")
        print(f"- 总智能体数: {team_status['total_agents']}")
        print(f"- 活跃智能体: {team_status['active_agents']}")
        print(f"- 空闲智能体: {team_status['idle_agents']}")
        
        # 7. 执行示例任务
        task_description = """
设计一个32位ALU（算术逻辑单元），支持以下操作：
- 加法 (ADD)
- 减法 (SUB) 
- 按位与 (AND)
- 按位或 (OR)
- 按位异或 (XOR)
- 按位非 (NOT)
- 左移 (SHL)
- 右移 (SHR)

要求：
- 32位数据位宽
- 4位操作码
- 包含零标志和溢出标志输出
- 同步复位设计
"""
        
        print(f"\n🎯 开始执行任务...")
        print(f"任务描述: {task_description[:100]}...")
        
        # 8. 协调任务执行
        result = await coordinator.coordinate_task_execution(
            initial_task=task_description,
            context={"example": True, "priority": "high"}
        )
        
        # 9. 显示执行结果
        print(f"\n📊 任务执行结果:")
        print(f"- 成功状态: {result.get('success', False)}")
        print(f"- 对话ID: {result.get('conversation_id', 'N/A')}")
        print(f"- 总轮次: {result.get('total_iterations', 0)}")
        print(f"- 执行时间: {result.get('duration', 0):.2f}秒")
        print(f"- 生成文件: {len(result.get('file_references', []))}")
        print(f"- 最终发言者: {result.get('final_speaker', 'N/A')}")
        
        # 10. 显示生成的文件
        if result.get('file_references'):
            print(f"\n📁 生成的文件:")
            for file_ref in result.get('file_references', []):
                if isinstance(file_ref, dict):
                    print(f"- {file_ref.get('file_path', 'Unknown')} ({file_ref.get('file_type', 'Unknown')})")
                else:
                    print(f"- {file_ref.file_path} ({file_ref.file_type})")
        
        # 11. 保存对话日志
        log_path = coordinator.save_conversation_log("output/example_conversation.json")
        print(f"\n💾 对话日志已保存: {log_path}")
        
        # 12. 显示统计信息
        stats = coordinator.get_conversation_statistics()
        print(f"\n📈 对话统计:")
        print(f"- 总对话数: {stats['total_conversations']}")
        print(f"- 总轮次: {stats['total_rounds']}")
        print(f"- 平均轮次: {stats['average_rounds_per_conversation']:.1f}")
        
        print(f"\n✅ 演示完成！")
        
    except Exception as e:
        print(f"❌ 演示执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())