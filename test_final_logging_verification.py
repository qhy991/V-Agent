#!/usr/bin/env python3
"""
最终日志验证 - 强制重启日志系统以应用修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 强制清理现有的日志管理器实例
import core.enhanced_logging_config
core.enhanced_logging_config._logger_manager = None

from core.enhanced_logging_config import setup_enhanced_logging, get_test_logger
from config.config import FrameworkConfig
from agents.real_verilog_agent import RealVerilogDesignAgent
from core.centralized_coordinator import CentralizedCoordinator

async def test_final_logging():
    """最终日志验证测试"""
    print("🔥 最终日志验证测试 - 强制重启日志系统")
    
    # 1. 重新初始化日志系统（应用修复）
    logger_manager = setup_enhanced_logging("final_logging_test")
    test_logger = get_test_logger()
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 测试目录: {session_dir}")
    
    # 2. 创建智能体（应用新的日志配置）
    config = FrameworkConfig.from_env()
    
    coordinator = CentralizedCoordinator(config)
    verilog_agent = RealVerilogDesignAgent(config)
    coordinator.register_agent(verilog_agent)
    
    test_logger.info("开始简单任务测试...")
    
    # 3. 执行简单任务（触发LLM调用和协调器日志）
    try:
        result = await coordinator.coordinate_task_execution("设计一个简单的OR门")
        test_logger.info(f"任务完成，结果: {len(str(result))} 字符")
    except Exception as e:
        test_logger.error(f"任务失败: {str(e)}")
    
    # 4. 验证关键日志文件
    print(f"\n📊 验证修复效果...")
    
    key_logs = [
        ('centralized_coordinator.log', '协调器专用日志'),
        ('enhanced_llm_client.log', 'LLM完整对话'),
        ('base_agent.log', '基础智能体日志'),
        ('experiment_summary.log', '全局日志汇总')
    ]
    
    for log_file, description in key_logs:
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            if size > 0:
                print(f"✅ {description}: {size} bytes")
                
                # 统计重要内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 统计不同类型的日志
                    llm_requests = content.count('🤖 开始LLM请求')
                    system_prompts = content.count('📋 System Prompt')
                    user_prompts = content.count('👤 User Prompt')
                    llm_responses = content.count('🤖 LLM响应')
                    coordinator_debug = content.count('🔍 DEBUG:')
                    
                    if llm_requests > 0:
                        print(f"   📈 LLM请求: {llm_requests} 次")
                    if system_prompts > 0:
                        print(f"   📋 System Prompts: {system_prompts} 条")
                    if user_prompts > 0:
                        print(f"   👤 User Prompts: {user_prompts} 条") 
                    if llm_responses > 0:
                        print(f"   🤖 LLM响应: {llm_responses} 条")
                    if coordinator_debug > 0:
                        print(f"   🧠 协调器调试: {coordinator_debug} 条")
                        
                except Exception as e:
                    print(f"   ❌ 内容分析失败: {e}")
            else:
                print(f"❌ {description}: 文件为空")
        else:
            print(f"❌ {description}: 不存在")
    
    # 5. 显示修复前后的对比
    print(f"\n🎯 修复效果对比:")
    
    coord_log = session_dir / 'centralized_coordinator.log'
    base_log = session_dir / 'base_agent.log'
    
    if coord_log.exists() and coord_log.stat().st_size > 0:
        print(f"✅ 协调器日志现在正确写入到: centralized_coordinator.log")
    else:
        print(f"❌ 协调器日志仍然有问题")
    
    if base_log.exists():
        with open(base_log, 'r', encoding='utf-8') as f:
            base_content = f.read()
        
        coord_lines_in_base = base_content.count('centralized_coordinator')
        print(f"📊 base_agent.log中协调器相关行数: {coord_lines_in_base}")
    
    return session_dir

if __name__ == "__main__":
    session_dir = asyncio.run(test_final_logging())
    print(f"\n🎉 最终验证完成！")
    print(f"📂 详细日志目录: {session_dir}")
    print(f"🔍 检查协调器日志: {session_dir}/centralized_coordinator.log")
    print(f"🔍 检查LLM对话: {session_dir}/enhanced_llm_client.log")