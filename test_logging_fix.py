#!/usr/bin/env python3
"""
测试日志修复 - 验证所有智能体和协调器的日志都能正确写入
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_component_logger,
    get_agent_logger,
    get_coordinator_logger,
    get_llm_logger,
    get_function_calling_logger
)

async def test_logging_system():
    """测试日志系统是否正确工作"""
    print("🧪 开始测试日志系统...")
    
    # 1. 初始化日志系统
    logger_manager = setup_enhanced_logging()
    print(f"📂 实验目录: {logger_manager.get_session_dir()}")
    
    # 2. 测试各种logger
    print("\n📝 测试各种日志器...")
    
    # 框架日志
    framework_logger = get_component_logger('framework')
    framework_logger.info("框架日志测试 - INFO级别")
    framework_logger.debug("框架日志测试 - DEBUG级别")
    
    # 协调器日志
    coordinator_logger = get_coordinator_logger()
    coordinator_logger.info("协调器日志测试 - INFO级别")
    coordinator_logger.debug("协调器日志测试 - DEBUG级别")
    
    # 智能体日志 - 通过不同方式获取
    verilog_agent_logger = get_agent_logger('RealVerilogDesignAgent')
    verilog_agent_logger.info("Verilog智能体日志测试 - INFO级别")
    verilog_agent_logger.debug("Verilog智能体日志测试 - DEBUG级别")
    
    code_reviewer_logger = get_agent_logger('RealCodeReviewAgent')
    code_reviewer_logger.info("代码审查智能体日志测试 - INFO级别")
    code_reviewer_logger.debug("代码审查智能体日志测试 - DEBUG级别")
    
    # 基础智能体日志 - 模拟Agent.前缀
    base_agent_logger = get_component_logger('base_agent', 'Agent.test_agent')
    base_agent_logger.info("基础智能体日志测试 - INFO级别")
    base_agent_logger.debug("基础智能体日志测试 - DEBUG级别")
    
    # LLM客户端日志
    llm_logger = get_llm_logger()
    llm_logger.info("LLM客户端日志测试 - INFO级别")
    llm_logger.warning("LLM客户端警告测试")
    
    # Function Calling日志
    fc_logger = get_function_calling_logger()
    fc_logger.info("Function Calling日志测试 - INFO级别")
    fc_logger.debug("Function Calling日志测试 - DEBUG级别")
    
    # 测试错误日志
    framework_logger.error("测试错误日志 - 应该出现在all_errors.log中")
    
    print("\n✅ 日志测试完成")
    
    # 3. 检查日志文件
    print("\n📊 检查日志文件...")
    session_dir = logger_manager.get_session_dir()
    
    log_files_to_check = [
        'framework.log',
        'centralized_coordinator.log', 
        'base_agent.log',
        'real_verilog_agent.log',
        'real_code_reviewer.log',
        'enhanced_llm_client.log',
        'function_calling.log',
        'all_errors.log',
        'experiment_summary.log'
    ]
    
    for log_file in log_files_to_check:
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {log_file}: {size} bytes")
            
            # 显示最后几行内容
            if size > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if lines:
                        print(f"   最后一行: {lines[-1].strip()}")
                except Exception as e:
                    print(f"   读取失败: {e}")
        else:
            print(f"❌ {log_file}: 文件不存在")
    
    # 4. 创建会话摘要
    logger_manager.create_session_summary()
    print(f"\n📋 会话摘要已创建: {session_dir}/session_summary.md")
    
    return logger_manager

if __name__ == "__main__":
    asyncio.run(test_logging_system())