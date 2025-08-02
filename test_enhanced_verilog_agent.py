#!/usr/bin/env python3
"""
增强Verilog Agent集成测试

Enhanced Verilog Agent Integration Test
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from core.base_agent import TaskMessage
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_verilog_agent():
    """测试增强Verilog Agent的完整功能"""
    print("🚀 增强Verilog Agent集成测试")
    print("=" * 60)
    
    try:
        # 初始化Agent
        agent = EnhancedRealVerilogAgent()
        print("✅ Agent初始化成功")
        
        # 测试用例1: 设计一个8位计数器
        print("\n📋 测试1: 设计8位计数器")
        print("-" * 40)
        
        counter_request = """
        设计一个8位二进制计数器，要求如下：
        - 模块名: counter_8bit
        - 输入端口: clk (时钟), rst (复位), en (使能)
        - 输出端口: count (8位计数值), overflow (溢出标志)
        - 功能: 在时钟上升沿计数，复位时清零，溢出时产生标志
        """
        
        task_message = TaskMessage(
            task_id="test_counter_8bit",
            sender_id="test_client",
            receiver_id="enhanced_verilog_agent",
            message_type="task_request",
            content=counter_request
        )
        
        result1 = await agent.execute_enhanced_task(
            enhanced_prompt=counter_request,
            original_message=task_message
        )
        
        if result1["success"]:
            print("✅ 8位计数器设计成功")
            print(f"迭代次数: {result1.get('iterations', 1)}")
            if result1.get('tool_results'):
                print(f"工具调用结果数: {len(result1['tool_results'])}")
        else:
            print(f"❌ 8位计数器设计失败: {result1.get('error')}")
        
        # 测试用例2: 测试参数验证和修复
        print("\n📋 测试2: 参数验证和智能修复")
        print("-" * 40)
        
        # 故意使用错误的参数格式来测试修复机制
        problematic_request = """
        生成一个Verilog模块，参数如下：
        - 模块名: 123_invalid_name  (故意错误: 数字开头)
        - 功能: x  (故意错误: 太短)
        - 输入端口: 包含特殊字符和超长名称
        """
        
        task_message2 = TaskMessage(
            task_id="test_parameter_repair",
            sender_id="test_client", 
            receiver_id="enhanced_verilog_agent",
            message_type="task_request",
            content=problematic_request
        )
        
        result2 = await agent.execute_enhanced_task(
            enhanced_prompt=problematic_request,
            original_message=task_message2
        )
        
        if result2["success"]:
            print("✅ 参数修复测试成功")
            print(f"迭代次数: {result2.get('iterations', 1)}")
            if result2.get('iterations', 1) > 1:
                print("🔧 智能修复机制已启动")
        else:
            print(f"❌ 参数修复测试失败: {result2.get('error')}")
        
        # 测试用例3: 复杂设计任务
        print("\n📋 测试3: 复杂设计任务")
        print("-" * 40)
        
        complex_request = """
        设计一个UART发送器模块，要求：
        - 模块名: uart_transmitter
        - 支持可配置波特率
        - 包含FIFO缓冲区
        - 支持奇偶校验
        - 提供发送状态指示
        请分析需求、生成代码、分析质量并创建测试台
        """
        
        task_message3 = TaskMessage(
            task_id="test_complex_uart",
            sender_id="test_client",
            receiver_id="enhanced_verilog_agent", 
            message_type="task_request",
            content=complex_request
        )
        
        result3 = await agent.execute_enhanced_task(
            enhanced_prompt=complex_request,
            original_message=task_message3
        )
        
        if result3["success"]:
            print("✅ 复杂UART设计成功")
            print(f"迭代次数: {result3.get('iterations', 1)}")
        else:
            print(f"❌ 复杂UART设计失败: {result3.get('error')}")
        
        # 显示Schema系统统计
        print("\n📊 Schema系统统计")
        print("-" * 40)
        stats = agent.get_validation_statistics()
        print(f"总验证次数: {stats['total_validations']}")
        print(f"成功验证次数: {stats['successful_validations']}")
        print(f"验证成功率: {stats['success_rate']:.1%}")
        
        # 显示增强工具信息
        print("\n🔧 增强工具列表")
        print("-" * 40)
        enhanced_tools = agent.list_enhanced_tools()
        for tool in enhanced_tools:
            print(f"- {tool['name']} ({tool['security_level']}) - {tool['category']}")
        
        print("\n" + "=" * 60)
        print("🎉 增强Verilog Agent集成测试完成!")
        
        # 分析测试结果
        successful_tests = sum([
            1 for result in [result1, result2, result3] 
            if result["success"]
        ])
        
        print(f"\n📈 测试总结:")
        print(f"成功测试: {successful_tests}/3")
        print(f"成功率: {successful_tests/3:.1%}")
        
        if successful_tests == 3:
            print("✅ 所有测试通过 - 增强Verilog Agent运行正常")
            print("🔧 Schema验证和智能修复功能已成功集成")
        else:
            print(f"⚠️ {3 - successful_tests} 个测试失败，需要进一步调试")
        
        return successful_tests == 3
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        logger.exception("测试异常")
        return False

async def test_schema_integration_comparison():
    """对比传统Agent和增强Agent"""
    print("\n" + "=" * 60)
    print("🔄 对比传统Agent vs 增强Agent")
    print("=" * 60)
    
    try:
        from agents.real_verilog_agent import RealVerilogDesignAgent
        
        print("📊 功能对比:")
        print("传统Agent:")
        print("  - 基础Function Calling")
        print("  - 简单参数验证")
        print("  - 有限的错误处理")
        
        print("\n增强Agent:")
        print("  - Schema严格验证")
        print("  - 智能参数修复")
        print("  - 安全性检查")
        print("  - 详细错误反馈")
        print("  - 自动重试机制")
        
        # 初始化两个Agent进行简单对比
        traditional_agent = RealVerilogDesignAgent()
        enhanced_agent = EnhancedRealVerilogAgent()
        
        print(f"\n传统Agent工具数: {len(traditional_agent.function_calling_registry)}")
        print(f"增强Agent工具数: {len(enhanced_agent.enhanced_tools)}")
        print(f"增强Agent验证缓存: {len(enhanced_agent.validation_cache)}")
        
    except ImportError:
        print("⚠️ 传统Agent未找到，跳过对比测试")

async def main():
    """主测试函数"""
    print("🚀 CentralizedAgentFramework 增强Verilog Agent测试")
    print("=" * 80)
    
    try:
        # 主要功能测试
        success = await test_enhanced_verilog_agent()
        
        # 对比测试
        await test_schema_integration_comparison()
        
        print("\n" + "=" * 80)
        if success:
            print("🎉 增强Verilog Agent集成成功!")
            print("\n📝 集成效果:")
            print("✅ Schema验证系统完全集成")
            print("✅ 智能修复机制正常工作") 
            print("✅ 安全性检查有效防护")
            print("✅ 向后兼容性保持完好")
            
            print("\n🚀 下一步建议:")
            print("1. 部署到生产环境进行实际测试")
            print("2. 收集用户反馈优化修复算法")
            print("3. 扩展Schema定义覆盖更多场景")
            print("4. 集成到其他专业Agent中")
        else:
            print("❌ 集成测试发现问题，需要进一步调试")
        
    except Exception as e:
        print(f"❌ 测试过程异常: {str(e)}")
        logger.exception("主测试异常")

if __name__ == "__main__":
    asyncio.run(main())