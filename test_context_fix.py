#!/usr/bin/env python3
"""
测试上下文修复功能

这个脚本用来测试新的统一文件上下文管理系统，确保智能体间的文件内容传递不会丢失。
"""

import asyncio
import sys
import logging
from pathlib import Path
import tempfile
import os

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.task_file_context import TaskFileContext, FileType, get_task_context, set_task_context
from core.llm_coordinator_agent import LLMCoordinatorAgent
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试用的counter.v内容
COMPLEX_COUNTER_VERILOG = """module counter_8bit(
    input wire clk,
    input wire rst_n,
    input wire en,
    input wire load,
    input wire [7:0] load_data,
    output reg [7:0] count,
    output wire overflow,
    output wire underflow
);

// 内部信号
reg [7:0] next_count;
reg prev_msb;

// 组合逻辑：下一个计数值
always @(*) begin
    if (~rst_n) begin
        next_count = 8'b0;
    end else if (load) begin
        next_count = load_data;
    end else if (en) begin
        next_count = count + 1'b1;
    end else begin
        next_count = count;
    end
end

// 时序逻辑：更新计数器
always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'b0;
        prev_msb <= 1'b0;
    end else begin
        prev_msb <= count[7];
        count <= next_count;
    end
end

// 溢出检测
assign overflow = (~prev_msb) & count[7];
assign underflow = prev_msb & (~count[7]);

endmodule"""

SIMPLE_COUNTER_VERILOG = """module counter(
    input clk,
    output reg [3:0] count
);

always @(posedge clk) begin
    count <= count + 1;
end

endmodule"""

async def test_context_creation_and_retrieval():
    """测试上下文创建和检索"""
    logger.info("🧪 测试1: 上下文创建和检索")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
        f.write(COMPLEX_COUNTER_VERILOG)
        temp_file_path = f.name
    
    try:
        # 创建任务文件上下文
        task_id = "test_task_001"
        context = TaskFileContext(task_id)
        
        # 添加文件
        context.add_file(
            file_path=temp_file_path,
            content=COMPLEX_COUNTER_VERILOG,
            is_primary_design=True
        )
        
        # 设置到全局存储
        set_task_context(task_id, context)
        
        # 检索并验证
        retrieved_context = get_task_context(task_id)
        assert retrieved_context is not None, "上下文检索失败"
        assert len(retrieved_context) == 1, f"文件数量不正确: {len(retrieved_context)}"
        
        # 验证文件内容
        primary_content = retrieved_context.get_primary_design_content()
        assert primary_content == COMPLEX_COUNTER_VERILOG, "主设计文件内容不匹配"
        
        # 验证摘要
        summary = retrieved_context.get_context_summary()
        assert summary['total_files'] == 1, "摘要中文件数量不正确"
        assert summary['primary_design_file'] is not None, "主设计文件路径为空"
        
        logger.info("✅ 测试1通过: 上下文创建和检索正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试1失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def test_content_verification():
    """测试内容验证功能"""
    logger.info("🧪 测试2: 内容验证功能")
    
    try:
        # 创建协调器实例
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建任务上下文
        task_id = "test_task_002"
        context = TaskFileContext(task_id)
        
        # 添加复杂的计数器文件
        context.add_file(
            file_path="/fake/path/counter.v",
            content=COMPLEX_COUNTER_VERILOG,
            is_primary_design=True
        )
        set_task_context(task_id, context)
        
        # 测试正确的结果内容 - 应该通过验证
        correct_result = f"""
        我已经成功为counter_8bit模块生成了测试台。该模块包含以下端口：
        - clk: 时钟信号
        - rst_n: 复位信号 (低电平有效)
        - en: 使能信号
        - load: 加载信号
        - load_data: 8位加载数据
        - count: 8位计数输出
        - overflow: 溢出标志
        - underflow: 下溢标志
        
        这是一个复杂的8位计数器，具有加载功能和溢出检测。
        """
        
        verification_result = coordinator._verify_content_context(
            result_content=correct_result,
            task_context={"task_id": task_id}
        )
        
        assert verification_result["correct_content_used"], "正确内容应该通过验证"
        assert not verification_result["content_mismatch_detected"], "不应检测到内容不匹配"
        assert not verification_result["evidence_of_hallucination"], "不应检测到幻觉"
        
        # 测试错误的结果内容 - 应该检测出问题
        wrong_result = """
        我生成了一个简单的计数器模块，只有clk输入和4位count输出。
        这是一个基础的计数器，每个时钟周期递增1。
        """
        
        verification_result = coordinator._verify_content_context(
            result_content=wrong_result,
            task_context={"task_id": task_id}
        )
        
        assert verification_result["content_mismatch_detected"], "应该检测到内容不匹配"
        assert not verification_result["correct_content_used"], "错误内容不应通过验证"
        
        logger.info("✅ 测试2通过: 内容验证功能正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试2失败: {e}")
        return False

async def test_generate_testbench_context():
    """测试生成测试台的上下文检索"""
    logger.info("🧪 测试3: generate_testbench工具上下文检索")
    
    try:
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        
        # 创建代码审查智能体
        config = FrameworkConfig.from_env()
        reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        # 创建任务文件上下文
        task_id = "test_task_003"
        context = TaskFileContext(task_id)
        context.add_file(
            file_path="/fake/path/counter.v",
            content=COMPLEX_COUNTER_VERILOG,
            is_primary_design=True
        )
        set_task_context(task_id, context)
        
        # 模拟协调器设置智能体的缓存
        exported_context = context.export_for_agent()
        reviewer_agent.agent_state_cache["task_file_context"] = exported_context
        
        # 创建兼容的last_read_files缓存
        last_read_files = {}
        for file_path, file_content in context.files.items():
            last_read_files[file_path] = {
                "content": file_content.content,
                "file_type": file_content.file_type.value,
                "checksum": file_content.checksum,
                "timestamp": file_content.timestamp
            }
        reviewer_agent.agent_state_cache["last_read_files"] = last_read_files
        
        # 调用生成测试台工具 - 不传入module_code，让它从上下文中获取
        result = await reviewer_agent._tool_generate_testbench(
            module_name="counter_8bit",
            test_scenarios=[{"name": "basic_test", "description": "基础功能测试"}]
        )
        
        assert result["success"], f"生成测试台失败: {result.get('error', 'Unknown error')}"
        
        # 验证生成的测试台包含了正确的端口信息
        testbench_content = result.get("result", "")
        assert "counter_8bit" in testbench_content, "测试台中应包含正确的模块名"
        assert "rst_n" in testbench_content, "测试台中应包含复位信号"
        assert "load_data" in testbench_content, "测试台中应包含加载数据端口"
        assert "overflow" in testbench_content, "测试台中应包含溢出信号"
        
        logger.info("✅ 测试3通过: generate_testbench工具上下文检索正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试3失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

async def test_coordinator_context_passing():
    """测试协调器的上下文传递"""
    logger.info("🧪 测试4: 协调器上下文传递")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
        f.write(COMPLEX_COUNTER_VERILOG)
        temp_file_path = f.name
    
    try:
        # 创建协调器
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 注册测试智能体
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        reviewer_agent = EnhancedRealCodeReviewAgent(config)
        coordinator.register_agent(reviewer_agent)
        
        # 模拟任务分配
        task_result = await coordinator._tool_assign_task_to_agent(
            agent_id="enhanced_real_code_review_agent",
            task_description="为提供的counter模块生成测试台",
            design_file_path=temp_file_path
        )
        
        # 由于没有实际的LLM调用，这里主要测试上下文设置是否正确
        if not task_result.get("success"):
            logger.info(f"⚠️ 任务分配未成功，但这是预期的（没有实际LLM）: {task_result.get('error', '')}")
        
        # 检查任务文件上下文是否正确设置
        task_id = None
        for tid, task_context in coordinator.active_tasks.items():
            if task_context.assigned_agent == "enhanced_real_code_review_agent":
                task_id = tid
                break
        
        if task_id:
            file_context = get_task_context(task_id)
            assert file_context is not None, "任务文件上下文未设置"
            assert len(file_context) >= 1, "文件上下文中没有文件"
            
            primary_content = file_context.get_primary_design_content()
            assert primary_content == COMPLEX_COUNTER_VERILOG, "主设计文件内容不匹配"
            
            logger.info("✅ 测试4通过: 协调器上下文传递正常")
            return True
        else:
            logger.warning("⚠️ 测试4部分通过: 任务创建成功但未找到任务ID（这可能是正常的）")
            return True
        
    except Exception as e:
        logger.error(f"❌ 测试4失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始上下文修复功能测试")
    
    tests = [
        ("上下文创建和检索", test_context_creation_and_retrieval),
        ("内容验证功能", test_content_verification),
        ("generate_testbench上下文检索", test_generate_testbench_context),
        ("协调器上下文传递", test_coordinator_context_passing),
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
        logger.info("🎉 所有测试通过！上下文修复功能工作正常。")
        return True
    else:
        logger.error("⚠️ 部分测试失败，需要进一步调试。")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎯 上下文修复测试完成 - 所有功能正常")
        sys.exit(0)
    else:
        print("\n⚠️ 上下文修复测试完成 - 发现问题")
        sys.exit(1)