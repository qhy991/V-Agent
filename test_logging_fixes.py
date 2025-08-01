#!/usr/bin/env python3
"""
测试日志修复 - 验证协调器日志和LLM对话日志
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_logging_config import setup_enhanced_logging, get_test_logger
from config.config import FrameworkConfig
from agents.real_verilog_agent import RealVerilogDesignAgent
from core.centralized_coordinator import CentralizedCoordinator

async def test_logging_fixes():
    """测试日志修复"""
    print("🧪 开始测试日志修复...")
    
    # 1. 设置独立的日志会话
    logger_manager = setup_enhanced_logging("test_logging_fixes")
    test_logger = get_test_logger()
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 测试会话目录: {session_dir}")
    
    # 2. 初始化配置和智能体
    config = FrameworkConfig.from_env()
    
    # 创建协调器
    test_logger.info("创建协调器...")
    coordinator = CentralizedCoordinator(config)
    
    # 创建智能体
    test_logger.info("创建Verilog智能体...")
    verilog_agent = RealVerilogDesignAgent(config)
    
    # 注册智能体到协调器
    coordinator.register_agent(verilog_agent)
    
    # 3. 测试简单的任务协调（这会触发LLM调用）
    test_logger.info("开始任务协调测试...")
    
    simple_task = "请设计一个简单的AND门，输入为a和b，输出为y"
    
    try:
        # 这会触发协调器分析任务、选择智能体，以及智能体的LLM调用
        result = await coordinator.coordinate_task_execution(simple_task)
        test_logger.info(f"任务协调完成，结果长度: {len(str(result))}")
    except Exception as e:
        test_logger.error(f"任务协调失败: {str(e)}")
    
    # 4. 检查日志文件
    print("\n📊 检查日志文件...")
    
    log_files_to_check = [
        ('centralized_coordinator.log', '协调器日志'),
        ('enhanced_llm_client.log', 'LLM客户端日志'),
        ('real_verilog_agent.log', 'Verilog智能体日志'),
        ('base_agent.log', '基础智能体日志'),
        ('experiment_summary.log', '实验摘要')
    ]
    
    for log_file, description in log_files_to_check:
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            if size > 0:
                print(f"✅ {description}: {size} bytes")
                
                # 显示一些关键行
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 统计特定类型的日志行
                    llm_lines = [line for line in lines if '🤖' in line or '📋' in line or '👤' in line]
                    coordinator_lines = [line for line in lines if 'centralized_coordinator' in line or '🔍 DEBUG:' in line]
                    
                    if llm_lines:
                        print(f"   📈 LLM对话记录: {len(llm_lines)} 行")
                    if coordinator_lines:
                        print(f"   🧠 协调器活动: {len(coordinator_lines)} 行")
                    
                    # 显示最后几行
                    if lines:
                        print(f"   📝 最新记录: {lines[-1].strip()}")
                        
                except Exception as e:
                    print(f"   ❌ 读取失败: {e}")
            else:
                print(f"❌ {description}: 文件为空")
        else:
            print(f"❌ {description}: 文件不存在")
    
    test_logger.info("测试完成")
    return session_dir

if __name__ == "__main__":
    session_dir = asyncio.run(test_logging_fixes())
    print(f"\n🎉 测试完成！查看详细日志: {session_dir}")
    print("🔍 重点检查:")
    print(f"  - 协调器日志: {session_dir}/centralized_coordinator.log")
    print(f"  - LLM对话日志: {session_dir}/enhanced_llm_client.log")
    print(f"  - 完整摘要: {session_dir}/experiment_summary.log")