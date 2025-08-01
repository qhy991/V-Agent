#!/usr/bin/env python3
"""
测试真实智能体的日志记录
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
from agents.real_code_reviewer import RealCodeReviewAgent
from core.centralized_coordinator import CentralizedCoordinator

async def test_real_agents_logging():
    """测试真实智能体的日志记录"""
    print("🧪 开始测试真实智能体日志记录...")
    
    # 1. 初始化日志系统
    logger_manager = setup_enhanced_logging()
    test_logger = get_test_logger()
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 实验目录: {session_dir}")
    
    # 2. 初始化配置
    config = FrameworkConfig.from_env()
    
    # 3. 创建智能体实例
    test_logger.info("创建智能体实例...")
    
    verilog_agent = RealVerilogDesignAgent(config)
    code_reviewer = RealCodeReviewAgent(config)
    coordinator = CentralizedCoordinator(config)
    
    test_logger.info("智能体创建完成")
    
    # 4. 测试简单的Function Calling
    test_logger.info("测试Function Calling...")
    
    # 测试Verilog智能体的工具调用
    test_request = "请分析一个简单AND门的设计需求"
    verilog_response = await verilog_agent.process_with_function_calling(
        user_request=test_request,
        max_iterations=2
    )
    
    test_logger.info(f"Verilog智能体响应: {len(str(verilog_response))} 字符")
    
    # 测试代码审查智能体
    review_request = "请生成一个简单的测试台"
    review_response = await code_reviewer.process_with_function_calling(
        user_request=review_request,
        max_iterations=2
    )
    
    test_logger.info(f"代码审查智能体响应: {len(str(review_response))} 字符")
    
    # 5. 检查日志文件内容
    print("\n📊 检查日志文件内容...")
    
    log_files = [
        'centralized_coordinator.log',
        'real_verilog_agent.log', 
        'real_code_reviewer.log',
        'enhanced_llm_client.log',
        'function_calling.log',
        'base_agent.log'
    ]
    
    for log_file in log_files:
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {log_file}: {size} bytes")
            
            if size > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    print(f"   总行数: {len(lines)}")
                    if lines:
                        print(f"   第一行: {lines[0].strip()}")
                        print(f"   最后一行: {lines[-1].strip()}")
                except Exception as e:
                    print(f"   读取失败: {e}")
        else:
            print(f"❌ {log_file}: 文件不存在")
    
    # 6. 显示实验摘要
    summary_file = session_dir / 'experiment_summary.log'
    if summary_file.exists():
        print(f"\n📋 实验摘要 ({summary_file.stat().st_size} bytes):")
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines[-10:]:  # 显示最后10行
                print(f"   {line.strip()}")
        except Exception as e:
            print(f"   读取摘要失败: {e}")
    
    test_logger.info("测试完成")
    return session_dir

if __name__ == "__main__":
    session_dir = asyncio.run(test_real_agents_logging())
    print(f"\n🎉 测试完成！查看日志目录: {session_dir}")