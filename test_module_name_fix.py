#!/usr/bin/env python3
"""
测试模块名提取修复功能

这个脚本用来测试修复后的模块名提取功能，确保review agent能正确提取带参数的模块名。
"""

import asyncio
import sys
import logging
from pathlib import Path
import tempfile
import os

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.task_file_context import TaskFileContext, set_task_context
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试用的Verilog代码（带参数）
PARAMETERIZED_COUNTER_VERILOG = """module counter #(
    parameter WIDTH = 8  // Counter bit width, adjustable via parameter
)(
    // Clock and reset
    input      clk,        // Positive edge clock
    input      rst_n,      // Active-low asynchronous reset
    
    // Control signals
    input      en,         // Enable signal
    input      up,         // Direction: 1=up, 0=down
    input      load,       // Load enable
    input [WIDTH-1:0] data_in, // Load data
    
    // Outputs
    output reg [WIDTH-1:0] count,  // Counter value
    output     carry_out           // Carry/borrow out
);

// Internal signals
reg [WIDTH-1:0] next_count;

// Counter logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
    end else if (load) begin
        count <= data_in;
    end else if (en) begin
        count <= up ? count + 1 : count - 1;
    end
end

// Carry out logic
assign carry_out = (up && count == {WIDTH{1'b1}}) || (!up && count == {WIDTH{1'b0}});

endmodule"""

SIMPLE_COUNTER_VERILOG = """module test_counter(input clk, output reg [3:0] count);
always @(posedge clk) begin
    count <= count + 1;
end
endmodule"""

async def test_module_name_extraction_review_agent():
    """测试review agent的模块名提取功能"""
    logger.info("🧪 测试1: Review Agent模块名提取功能")
    
    try:
        config = FrameworkConfig.from_env()
        review_agent = EnhancedRealCodeReviewAgent(config)
        
        # 测试1: 参数化模块
        logger.info("测试参数化模块...")
        extracted_name = review_agent._extract_module_name_from_code(PARAMETERIZED_COUNTER_VERILOG)
        logger.info(f"参数化模块提取结果: {extracted_name}")
        assert extracted_name == "counter", f"期望 'counter'，实际得到 '{extracted_name}'"
        
        # 测试2: 简单模块
        logger.info("测试简单模块...")
        extracted_name = review_agent._extract_module_name_from_code(SIMPLE_COUNTER_VERILOG)
        logger.info(f"简单模块提取结果: {extracted_name}")
        assert extracted_name == "test_counter", f"期望 'test_counter'，实际得到 '{extracted_name}'"
        
        logger.info("✅ 测试1通过: Review Agent模块名提取正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试1失败: {e}")
        return False

async def test_coordinator_module_name_extraction():
    """测试coordinator的模块名提取功能"""
    logger.info("🧪 测试2: Coordinator模块名提取功能")
    
    try:
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 测试1: 参数化模块
        logger.info("测试参数化模块...")
        extracted_name = coordinator._extract_module_name_from_verilog(PARAMETERIZED_COUNTER_VERILOG)
        logger.info(f"参数化模块提取结果: {extracted_name}")
        assert extracted_name == "counter", f"期望 'counter'，实际得到 '{extracted_name}'"
        
        # 测试2: 简单模块
        logger.info("测试简单模块...")
        extracted_name = coordinator._extract_module_name_from_verilog(SIMPLE_COUNTER_VERILOG)
        logger.info(f"简单模块提取结果: {extracted_name}")
        assert extracted_name == "test_counter", f"期望 'test_counter'，实际得到 '{extracted_name}'"
        
        logger.info("✅ 测试2通过: Coordinator模块名提取正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试2失败: {e}")
        return False

async def test_context_passing():
    """测试上下文传递功能"""
    logger.info("🧪 测试3: 上下文传递功能")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
        f.write(PARAMETERIZED_COUNTER_VERILOG)
        temp_file_path = f.name
    
    try:
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        review_agent = EnhancedRealCodeReviewAgent(config)
        
        # 模拟coordinator处理文件
        task_id = "test_task_module_name"
        task_file_context = TaskFileContext(task_id)
        
        # 模拟coordinator读取文件并提取模块名
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            design_content = f.read()
        
        actual_module_name = coordinator._extract_module_name_from_verilog(design_content)
        logger.info(f"协调器提取模块名: {actual_module_name}")
        
        # 添加到上下文（包含模块名元数据）
        module_metadata = {"actual_module_name": actual_module_name}
        task_file_context.add_file(
            file_path=temp_file_path,
            content=design_content,
            is_primary_design=True,
            metadata=module_metadata
        )
        
        set_task_context(task_id, task_file_context)
        
        # 模拟review agent获取上下文
        exported_context = task_file_context.export_for_agent()
        review_agent.agent_state_cache["task_file_context"] = exported_context
        
        # 模拟调用generate_testbench工具
        result = await review_agent._tool_generate_testbench(
            module_name=None,  # 不提供模块名，让它从上下文中获取
            test_scenarios=[{"name": "basic_test", "description": "基础功能测试"}]
        )
        
        if result.get("success"):
            # 检查结果中的模块名
            testbench_content = result.get("result", "")
            
            # 检查是否包含正确的模块实例化（更精确的检查）
            correct_instantiation = f"{actual_module_name} #"  # 参数化模块实例化
            simple_instantiation = f"{actual_module_name} uut"  # 简单模块实例化
            
            # 检查是否生成的测试台文件名正确
            module_name_in_result = result.get("module_name", "")
            
            logger.info(f"检查模块实例化: {correct_instantiation} 或 {simple_instantiation}")
            logger.info(f"结果中的模块名: {module_name_in_result}")
            logger.info(f"测试台内容包含正确模块名: {actual_module_name in testbench_content}")
            
            if (correct_instantiation in testbench_content or simple_instantiation in testbench_content) and module_name_in_result == actual_module_name:
                logger.info("✅ 测试3通过: 上下文传递功能正常")
                return True
            else:
                logger.error("❌ 测试3失败: 生成的测试台中未包含正确的模块实例化")
                logger.error(f"测试台内容预览: {testbench_content[:500]}...")
                return False
        else:
            logger.error(f"❌ 测试3失败: 生成测试台失败: {result.get('error')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试3失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始模块名提取修复测试")
    
    tests = [
        ("Review Agent模块名提取", test_module_name_extraction_review_agent),
        ("Coordinator模块名提取", test_coordinator_module_name_extraction),
        ("上下文传递功能", test_context_passing),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"开始测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
            results.append((test_name, False))
    
    # 总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！模块名提取修复功能正常。")
        return True
    else:
        logger.error("⚠️ 部分测试失败，需要进一步调试。")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎯 模块名提取修复测试完成 - 所有功能正常")
        sys.exit(0)
    else:
        print("\n⚠️ 模块名提取修复测试完成 - 发现问题")
        sys.exit(1)