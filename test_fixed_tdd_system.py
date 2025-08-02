#!/usr/bin/env python3
"""
测试修复后的TDD系统
验证Enhanced智能体是否正确使用write_file工具
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.file_manager import initialize_file_manager, get_file_manager
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_agent_write_file():
    """测试Enhanced智能体是否使用write_file工具"""
    logger.info("🧪 测试Enhanced智能体write_file功能")
    
    # 初始化文件管理器
    workspace = project_root / "test_fixed_workspace"
    workspace.mkdir(exist_ok=True)
    file_manager = initialize_file_manager(workspace)
    
    # 创建Enhanced Verilog智能体
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 测试generate_verilog_code工具
    result = await agent.process_with_enhanced_validation(
        "设计一个简单的全加器模块，输入为a、b、cin，输出为sum、cout",
        max_iterations=2
    )
    
    logger.info(f"✅ 智能体处理结果: {result.get('success', False)}")
    if result.get('success'):
        logger.info(f"📄 工具调用结果: {result.get('tool_results', [])}")
    
    # 检查文件管理器中的文件
    verilog_files = file_manager.get_files_by_type("verilog")
    logger.info(f"🗂️ 文件管理器中有 {len(verilog_files)} 个Verilog文件")
    
    for i, file_ref in enumerate(verilog_files, 1):
        logger.info(f"  {i}. {file_ref.file_path} (ID: {file_ref.file_id})")
        logger.info(f"     创建者: {file_ref.created_by}")
        logger.info(f"     描述: {file_ref.description}")
    
    return result, verilog_files

async def test_quick_tdd_workflow():
    """测试快速TDD工作流"""
    logger.info("🔄 测试快速TDD工作流")
    
    try:
        from extensions.test_driven_coordinator import TestDrivenConfig, create_test_driven_coordinator
        from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        
        # 创建协调器
        base_coordinator = EnhancedCentralizedCoordinator()
        
        # 注册智能体
        config = FrameworkConfig.from_env()
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer = EnhancedRealCodeReviewAgent(config)
        
        base_coordinator.register_agent(verilog_agent)
        base_coordinator.register_agent(code_reviewer)
        
        # 创建TDD协调器
        tdd_config = TestDrivenConfig(max_iterations=2, save_iteration_logs=True)
        tdd_coordinator = create_test_driven_coordinator(base_coordinator, tdd_config)
        
        # 执行快速TDD任务
        result = await tdd_coordinator.execute_test_driven_task(
            "设计一个2位加法器，输入为a[1:0]、b[1:0]，输出为sum[2:0]"
        )
        
        logger.info(f"✅ TDD工作流完成: {result.get('success', False)}")
        logger.info(f"📊 迭代次数: {result.get('total_iterations', 0)}")
        logger.info(f"📄 最终设计文件: {len(result.get('final_design', []))} 个")
        
        # 检查最终设计文件
        final_files = result.get('final_design', [])
        for i, file_ref in enumerate(final_files, 1):
            logger.info(f"  设计文件 {i}: {file_ref}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ TDD工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def main():
    """主测试函数"""
    logger.info("🧪 开始测试修复后的TDD系统")
    
    try:
        # 1. 测试Enhanced智能体write_file功能
        logger.info("=" * 50)
        agent_result, verilog_files = await test_enhanced_agent_write_file()
        
        # 2. 测试快速TDD工作流
        logger.info("=" * 50)
        tdd_result = await test_quick_tdd_workflow()
        
        # 汇总结果
        logger.info("=" * 50)
        logger.info("📋 测试结果汇总:")
        logger.info(f"  Enhanced智能体测试: {'✅ 通过' if agent_result.get('success') else '❌ 失败'}")
        logger.info(f"  TDD工作流测试: {'✅ 通过' if tdd_result.get('success') else '❌ 失败'}")
        logger.info(f"  文件管理器文件数: {len(verilog_files)}")
        
        # 显示工作空间状态
        file_manager = get_file_manager()
        workspace_info = file_manager.get_workspace_info()
        logger.info(f"🗂️ 工作空间状态: 共 {workspace_info['total_files']} 个文件")
        
    except Exception as e:
        logger.error(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())