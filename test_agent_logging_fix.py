#!/usr/bin/env python3
"""
测试智能体日志路由修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 重置日志系统以应用修复
print("🔧 重置日志系统...")
import core.enhanced_logging_config
core.enhanced_logging_config.reset_logging_system()

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging, get_test_logger

async def test_agent_logging():
    """测试智能体日志路由修复"""
    print("🧪 测试智能体日志路由修复...")
    
    # 1. 重新初始化日志系统
    logger_manager = setup_enhanced_logging("agent_logging_test")
    test_logger = get_test_logger()
    session_dir = logger_manager.get_session_dir()
    
    print(f"📂 测试目录: {session_dir}")
    
    # 2. 创建配置
    config = FrameworkConfig.from_env()
    
    # 3. 创建协调器和智能体
    coordinator = CentralizedCoordinator(config)
    verilog_agent = RealVerilogDesignAgent(config)
    reviewer_agent = RealCodeReviewAgent(config)
    
    # 4. 记录测试日志 - 每个智能体记录一些内容
    print("📝 记录测试日志...")
    
    test_logger.info("开始智能体日志路由测试")
    
    coordinator.logger.info("这是协调器的测试日志 - 应该写入centralized_coordinator.log")
    coordinator.logger.warning("协调器警告测试")
    coordinator.logger.debug("协调器调试信息测试")
    
    verilog_agent.logger.info("这是Verilog智能体的测试日志 - 应该写入real_verilog_agent.log")
    verilog_agent.logger.warning("Verilog智能体警告测试")
    verilog_agent.logger.debug("Verilog智能体调试信息测试")
    
    reviewer_agent.logger.info("这是代码审查智能体的测试日志 - 应该写入real_code_reviewer.log")
    reviewer_agent.logger.warning("代码审查智能体警告测试")
    reviewer_agent.logger.debug("代码审查智能体调试信息测试")
    
    # 5. 检查日志文件
    print(f"\n📊 检查日志文件...")
    
    key_files = {
        'centralized_coordinator.log': '协调器专用日志',
        'real_verilog_agent.log': 'Verilog智能体专用日志',
        'real_code_reviewer.log': '代码审查智能体专用日志',
        'base_agent.log': '基础智能体日志（应该很少内容）',
        'test_framework.log': '测试框架日志'
    }
    
    results = {}
    all_working = True
    
    for log_file, description in key_files.items():
        file_path = session_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            results[log_file] = size
            
            if size > 0:
                print(f"✅ {description}: {size} bytes")
                
                # 检查内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 统计关键指标
                    coord_lines = content.count('协调器')
                    verilog_lines = content.count('Verilog智能体')
                    reviewer_lines = content.count('代码审查智能体')
                    
                    if coord_lines > 0:
                        print(f"   🧠 协调器相关: {coord_lines} 行")
                    if verilog_lines > 0:
                        print(f"   ⚡ Verilog智能体相关: {verilog_lines} 行")
                    if reviewer_lines > 0:
                        print(f"   🔍 代码审查智能体相关: {reviewer_lines} 行")
                        
                except Exception as e:
                    print(f"   ❌ 内容分析失败: {e}")
                    
            else:
                print(f"❌ {description}: 文件为空")
                if log_file in ['centralized_coordinator.log', 'real_verilog_agent.log', 'real_code_reviewer.log']:
                    all_working = False
        else:
            print(f"❌ {description}: 文件不存在")
            if log_file in ['centralized_coordinator.log', 'real_verilog_agent.log', 'real_code_reviewer.log']:
                all_working = False
    
    # 6. 验证结果
    print(f"\n🎯 智能体日志路由测试结果:")
    
    coord_working = results.get('centralized_coordinator.log', 0) > 0
    verilog_working = results.get('real_verilog_agent.log', 0) > 0
    reviewer_working = results.get('real_code_reviewer.log', 0) > 0
    
    if coord_working:
        print(f"✅ 协调器日志正确路由到 centralized_coordinator.log")
    else:
        print(f"❌ 协调器日志路由失败")
        all_working = False
    
    if verilog_working:
        print(f"✅ Verilog智能体日志正确路由到 real_verilog_agent.log")
    else:
        print(f"❌ Verilog智能体日志路由失败")
        all_working = False
    
    if reviewer_working:
        print(f"✅ 代码审查智能体日志正确路由到 real_code_reviewer.log")
    else:
        print(f"❌ 代码审查智能体日志路由失败")
        all_working = False
    
    if all_working:
        print(f"\n🎉 所有智能体日志路由修复成功！")
        print(f"   - 协调器日志: centralized_coordinator.log")
        print(f"   - Verilog智能体日志: real_verilog_agent.log")
        print(f"   - 代码审查智能体日志: real_code_reviewer.log")
        print(f"   - 基础智能体日志: base_agent.log (仅共享部分)")
        return True
    else:
        print(f"\n⚠️ 部分智能体日志路由仍有问题，需要进一步调试")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_logging())
    if success:
        print(f"\n🚀 智能体日志路由修复完成！现在运行多智能体测试时，每个智能体的日志都会写入各自的专用文件。")
    else:
        print(f"\n⚠️ 需要进一步调试智能体日志路由问题")