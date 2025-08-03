#!/usr/bin/env python3
"""
🧠 上下文优化TDD框架测试脚本
==================================================

测试优化后的TDD框架的完整上下文传递功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.centralized_coordinator import CentralizedCoordinator
from extensions.test_driven_coordinator import create_test_driven_coordinator, TestDrivenConfig
from core.context_manager import get_context_manager


async def test_context_optimization():
    """测试上下文优化功能"""
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 开始测试上下文优化TDD框架")
    
    try:
        # 1. 创建基础协调器
        base_coordinator = CentralizedCoordinator()
        
        # 2. 创建增强的TDD协调器
        tdd_config = TestDrivenConfig(
            max_iterations=3,
            enable_deep_analysis=True,
            auto_fix_suggestions=True,
            save_iteration_logs=True,
            timeout_per_iteration=120
        )
        
        enhanced_coordinator = create_test_driven_coordinator(
            base_coordinator, 
            tdd_config
        )
        
        logger.info("✅ TDD协调器创建成功")
        
        # 3. 测试任务
        test_task = """
设计一个简单的8位加法器，支持基本的二进制加法运算。

模块接口：
```verilog
module simple_8bit_adder (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);
```

🎯 功能要求：
1. 实现8位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 支持所有可能的输入组合（0到255）
4. 处理进位传播

💡 设计提示：
- 可以使用简单的行波进位链
- 确保所有边界条件正确处理
- 代码要简洁清晰，易于理解
"""
        
        # 4. 执行TDD任务
        logger.info("🚀 开始执行TDD任务")
        result = await enhanced_coordinator.execute_test_driven_task(
            task_description=test_task,
            testbench_path=None,  # 让AI生成测试台
            context={}
        )
        
        # 5. 分析结果
        logger.info("📊 分析TDD执行结果")
        logger.info(f"✅ 执行成功: {result.get('success', False)}")
        logger.info(f"🔄 总迭代次数: {result.get('total_iterations', 0)}")
        logger.info(f"📄 最终设计文件: {len(result.get('final_design', []))}")
        logger.info(f"🧠 上下文文件: {result.get('context_file', 'N/A')}")
        
        # 6. 获取上下文统计信息
        if enhanced_coordinator.context_manager:
            session_id = enhanced_coordinator.context_manager.session_id
            stats = enhanced_coordinator.get_context_statistics(session_id)
            logger.info("📈 上下文统计信息:")
            logger.info(f"   - 总迭代次数: {stats.get('total_iterations', 0)}")
            logger.info(f"   - 对话轮次: {stats.get('total_conversation_turns', 0)}")
            logger.info(f"   - 代码文件: {stats.get('total_code_files', 0)}")
            logger.info(f"   - 测试台文件: {stats.get('total_testbench_files', 0)}")
            logger.info(f"   - 编译错误: {stats.get('compilation_errors_count', 0)}")
            logger.info(f"   - 成功迭代: {stats.get('successful_iterations', 0)}")
            logger.info(f"   - 失败迭代: {stats.get('failed_iterations', 0)}")
            
            # 7. 导出上下文摘要
            summary = enhanced_coordinator.export_context_summary(session_id)
            logger.info("🔍 上下文摘要:")
            for insight in summary.get('key_insights', []):
                logger.info(f"   - {insight['message']}")
            
            for rec in summary.get('recommendations', []):
                logger.info(f"   - [{rec['priority']}] {rec['message']}")
        
        # 8. 验证上下文文件
        if result.get('context_file'):
            context_file = Path(result['context_file'])
            if context_file.exists():
                logger.info(f"✅ 上下文文件已保存: {context_file}")
                logger.info(f"📏 文件大小: {context_file.stat().st_size} 字节")
            else:
                logger.warning(f"⚠️ 上下文文件不存在: {context_file}")
        
        logger.info("🎉 上下文优化测试完成")
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_context_loading():
    """测试上下文加载功能"""
    logger = logging.getLogger(__name__)
    
    try:
        # 创建协调器
        base_coordinator = CentralizedCoordinator()
        enhanced_coordinator = create_test_driven_coordinator(base_coordinator)
        
        # 测试加载不存在的文件
        result = enhanced_coordinator.load_context_from_file("nonexistent_file.json")
        logger.info(f"加载不存在文件的结果: {result}")
        
        # 测试获取未初始化的上下文统计
        stats = enhanced_coordinator.get_context_statistics("test_session")
        logger.info(f"未初始化上下文统计: {stats}")
        
    except Exception as e:
        logger.error(f"❌ 上下文加载测试失败: {str(e)}")


if __name__ == "__main__":
    # 运行测试
    async def main():
        # 测试1: 完整TDD执行
        result = await test_context_optimization()
        
        # 测试2: 上下文加载
        await test_context_loading()
        
        if result:
            print("\n" + "="*60)
            print("🎯 测试总结:")
            print(f"✅ TDD执行: {'成功' if result.get('success') else '失败'}")
            print(f"🔄 迭代次数: {result.get('total_iterations', 0)}")
            print(f"🧠 上下文管理: {'已启用' if result.get('context_file') else '未启用'}")
            print("="*60)
        else:
            print("\n❌ 测试失败")
    
    asyncio.run(main()) 