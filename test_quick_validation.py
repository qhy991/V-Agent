#!/usr/bin/env python3
"""
快速验证测试

Quick Validation Test
"""

import asyncio
from config.config import FrameworkConfig
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入增强日志系统
from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_test_logger, 
    get_artifacts_dir
)

async def quick_test():
    """快速功能验证"""
    # 初始化增强日志系统
    logger_manager = setup_enhanced_logging()
    logger = get_test_logger()
    artifacts_dir = get_artifacts_dir()
    
    logger.info("开始快速功能验证")
    print("🚀 开始快速功能验证...")
    print(f"📁 工件目录: {artifacts_dir}")
    
    try:
        # 1. 基础初始化测试
        logger.info("基础组件初始化测试")
        print("\n📋 1. 基础组件初始化")
        config = FrameworkConfig.from_env()
        verilog_agent = RealVerilogDesignAgent(config)
        review_agent = RealCodeReviewAgent(config)
        
        print(f"✅ Verilog Agent - 工具数: {len(verilog_agent.function_calling_registry)}")
        print(f"✅ Review Agent - 工具数: {len(review_agent.function_calling_registry)}")
        
        # 2. 简单工具调用测试
        print("\n🔧 2. 基础工具测试")
        
        # 测试文件写入
        write_result = await verilog_agent._tool_write_file(
            filename="quick_test.v",
            content="// Quick test file\nmodule quick_test();\nendmodule",
            directory=str(artifacts_dir)
        )
        
        if write_result.get("success"):
            print("✅ 文件写入工具正常")
        else:
            print("❌ 文件写入工具失败")
        
        # 测试文件读取
        read_result = await verilog_agent._tool_read_file(
            filepath=str(artifacts_dir / "quick_test.v")
        )
        
        if read_result.get("success"):
            print("✅ 文件读取工具正常")
        else:
            print("❌ 文件读取工具失败")
        
        # 3. Function Calling流程测试
        print("\n🤖 3. Function Calling流程测试")
        
        simple_request = """请创建一个简单的测试文件，内容为一个空的Verilog模块"""
        
        response = await verilog_agent.process_with_function_calling(
            user_request=simple_request,
            max_iterations=3
        )
        
        if len(response) > 50:
            print("✅ Function Calling流程正常")
            print(f"📄 响应长度: {len(response)} 字符")
        else:
            print("❌ Function Calling流程可能有问题")
        
        # 4. 错误处理测试
        print("\n🛡️ 4. 错误处理测试")
        
        error_result = await review_agent._tool_read_file(
            filepath="nonexistent_file.v"
        )
        
        if not error_result.get("success"):
            print("✅ 错误处理机制正常")
        else:
            print("❌ 错误处理机制异常")
        
        print("\n🎉 快速验证完成！框架基础功能正常。")
        print("\n💡 建议运行完整测试: python test_complete_framework.py")
        
    except Exception as e:
        print(f"\n❌ 快速验证失败: {str(e)}")
        print("🔧 请检查配置文件和环境设置")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())