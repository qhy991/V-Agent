#!/usr/bin/env python3
"""
标准化响应格式使用示例

Standardized Response Format Usage Examples
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_agent import BaseAgent
from core.enums import AgentCapability
from core.response_format import (
    ResponseBuilder, ResponseFormat, TaskStatus, ResponseType, 
    QualityMetrics, create_success_response
)

# 设置日志
logging.basicConfig(level=logging.INFO)

class VerilogDesignAgent(BaseAgent):
    """Verilog设计智能体示例"""
    
    def __init__(self):
        super().__init__(
            agent_id="verilog_designer_example",
            role="verilog_designer",
            capabilities={AgentCapability.CODE_GENERATION}
        )
    
    def get_capabilities(self):
        return {AgentCapability.CODE_GENERATION}
    
    def get_specialty_description(self):
        return "专业的Verilog HDL设计智能体，擅长数字电路设计和优化"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        """模拟执行Verilog设计任务"""
        task_id = original_message.task_id
        
        # 模拟设计过程
        await asyncio.sleep(0.1)  # 模拟处理时间
        
        # 示例1: 使用便捷方法创建成功响应
        if "simple" in enhanced_prompt.lower():
            return {
                "formatted_response": self.create_success_response_formatted(
                    task_id=task_id,
                    message="成功设计了简单的32位加法器模块",
                    generated_files=["/output/adder_32bit.v"],
                    format_type=ResponseFormat.JSON
                )
            }
        
        # 示例2: 使用ResponseBuilder创建复杂响应
        builder = self.create_response_builder(task_id)
        
        # 添加生成的文件
        builder.add_generated_file(
            "/output/alu_32bit.v", 
            "verilog", 
            "32位算术逻辑单元，支持8种运算操作"
        ).add_generated_file(
            "/output/alu_32bit_tb.v",
            "testbench", 
            "ALU模块的综合测试平台，包含1000个测试向量"
        )
        
        # 添加问题报告
        builder.add_issue(
            "warning", "medium", 
            "建议在关键路径上添加流水线寄存器以提高时钟频率",
            location="alu_32bit.v:156-168",
            solution="在加法器输出端添加寄存器级"
        ).add_issue(
            "suggestion", "low",
            "可以考虑使用更高效的乘法器IP核",
            location="alu_32bit.v:89-95"
        )
        
        # 添加质量指标
        quality_metrics = QualityMetrics(
            overall_score=0.87,
            syntax_score=0.95,
            functionality_score=0.85,
            test_coverage=0.82,
            documentation_quality=0.88,
            performance_score=0.79
        )
        
        # 添加下一步建议
        builder.add_next_step("运行功能仿真验证所有运算操作")
        builder.add_next_step("执行时序分析确认时钟约束")
        builder.add_next_step("进行面积和功耗评估")
        
        # 添加元数据
        builder.add_metadata("bit_width", 32)
        builder.add_metadata("operations", ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA"])
        builder.add_metadata("estimated_area", "1250 LUTs")
        builder.add_metadata("max_frequency", "150 MHz")
        
        # 构建最终响应
        response = builder.build(
            response_type=ResponseType.TASK_COMPLETION,
            status=TaskStatus.SUCCESS,
            message="成功设计了高性能32位ALU模块，通过了所有功能测试",
            completion_percentage=100.0,
            quality_metrics=quality_metrics
        )
        
        return {
            "formatted_response": response.format_response(ResponseFormat.JSON)
        }

class TestbenchAgent(BaseAgent):
    """测试平台生成智能体示例"""
    
    def __init__(self):
        super().__init__(
            agent_id="testbench_generator_example",
            role="testbench_generator", 
            capabilities={AgentCapability.TEST_GENERATION}
        )
    
    def get_capabilities(self):
        return {AgentCapability.TEST_GENERATION}
    
    def get_specialty_description(self):
        return "专业的Verilog测试平台生成智能体，提供全面的验证方案"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        """模拟执行测试平台生成任务"""
        task_id = original_message.task_id
        
        # 模拟处理过程
        await asyncio.sleep(0.1)
        
        # 使用高级响应创建方法
        quality_metrics = QualityMetrics(
            overall_score=0.91,
            syntax_score=0.98,
            functionality_score=0.88,
            test_coverage=0.95,
            documentation_quality=0.85
        )
        
        formatted_response = await self.create_advanced_response(
            task_id=task_id,
            response_type=ResponseType.TASK_COMPLETION,
            status=TaskStatus.SUCCESS,
            message="生成了覆盖率达95%的综合测试平台",
            completion_percentage=100.0,
            quality_metrics=quality_metrics,
            format_type=ResponseFormat.MARKDOWN
        )
        
        return {
            "formatted_response": formatted_response
        }

async def demonstrate_response_formats():
    """演示不同的响应格式"""
    print("🎭 演示标准化响应格式系统")
    print("=" * 60)
    
    # 创建智能体
    verilog_agent = VerilogDesignAgent()
    testbench_agent = TestbenchAgent()
    
    # 模拟任务消息
    from core.base_agent import TaskMessage
    
    # 示例1: 简单响应 (JSON格式)
    print("\n📋 示例1: 简单JSON响应")
    print("-" * 30)
    
    simple_task = TaskMessage(
        task_id="simple_task_001",
        sender_id="coordinator",
        receiver_id="verilog_designer_example",
        message_type="design_request",
        content="设计一个简单的32位加法器模块"
    )
    
    simple_result = await verilog_agent.execute_enhanced_task(
        "设计一个simple的32位加法器", simple_task, {}
    )
    
    print(simple_result["formatted_response"])
    
    # 示例2: 复杂响应 (JSON格式)
    print("\n📋 示例2: 复杂JSON响应")
    print("-" * 30)
    
    complex_task = TaskMessage(
        task_id="complex_task_002", 
        sender_id="coordinator",
        receiver_id="verilog_designer_example",
        message_type="design_request",
        content="设计一个高性能的32位ALU模块"
    )
    
    complex_result = await verilog_agent.execute_enhanced_task(
        "设计高性能ALU模块", complex_task, {}
    )
    
    print(complex_result["formatted_response"])
    
    # 示例3: Markdown格式响应
    print("\n📋 示例3: Markdown格式响应")
    print("-" * 30)
    
    testbench_task = TaskMessage(
        task_id="testbench_task_003",
        sender_id="coordinator", 
        receiver_id="testbench_generator_example",
        message_type="testbench_request",
        content="为ALU模块生成综合测试平台"
    )
    
    testbench_result = await testbench_agent.execute_enhanced_task(
        "生成ALU测试平台", testbench_task, {}
    )
    
    print(testbench_result["formatted_response"])

async def demonstrate_error_handling():
    """演示错误处理"""
    print("\n🚨 演示错误处理")
    print("-" * 30)
    
    class ErrorAgent(BaseAgent):
        def __init__(self):
            super().__init__("error_agent", "error_demo", {AgentCapability.CODE_GENERATION})
        
        def get_capabilities(self):
            return {AgentCapability.CODE_GENERATION}
        
        def get_specialty_description(self):
            return "用于演示错误处理的智能体"
        
        async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
            # 模拟遇到错误
            return {
                "formatted_response": self.create_error_response_formatted(
                    task_id=original_message.task_id,
                    error_message="输入参数验证失败",
                    error_details="位宽参数必须是8的倍数，当前值为33",
                    format_type=ResponseFormat.JSON
                )
            }
    
    error_agent = ErrorAgent()
    from core.base_agent import TaskMessage
    
    error_task = TaskMessage(
        task_id="error_task_004",
        sender_id="coordinator",
        receiver_id="error_agent", 
        message_type="design_request",
        content="设计33位加法器"
    )
    
    error_result = await error_agent.execute_enhanced_task(
        "设计33位加法器", error_task, {}
    )
    
    print(error_result["formatted_response"])

async def demonstrate_progress_updates():
    """演示进度更新"""
    print("\n📈 演示进度更新")
    print("-" * 30)
    
    class ProgressAgent(BaseAgent):
        def __init__(self):
            super().__init__("progress_agent", "progress_demo", {AgentCapability.CODE_GENERATION})
        
        def get_capabilities(self):
            return {AgentCapability.CODE_GENERATION}
        
        def get_specialty_description(self):
            return "用于演示进度更新的智能体"
        
        async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
            # 模拟多个进度更新
            progress_updates = [
                (30.0, "完成需求分析", ["开始架构设计", "准备接口定义"]),
                (60.0, "完成架构设计", ["开始RTL编码", "准备测试计划"]),
                (90.0, "完成RTL编码", ["开始功能验证", "准备文档编写"])
            ]
            
            responses = []
            for progress, message, next_steps in progress_updates:
                response = self.create_progress_response_formatted(
                    task_id=original_message.task_id,
                    message=message,
                    completion_percentage=progress,
                    next_steps=next_steps,
                    format_type=ResponseFormat.MARKDOWN
                )
                responses.append(response)
            
            return {"progress_updates": responses}
    
    progress_agent = ProgressAgent()
    from core.base_agent import TaskMessage
    
    progress_task = TaskMessage(
        task_id="progress_task_005",
        sender_id="coordinator",
        receiver_id="progress_agent",
        message_type="design_request", 
        content="设计复杂的处理器核心"
    )
    
    progress_result = await progress_agent.execute_enhanced_task(
        "设计处理器核心", progress_task, {}
    )
    
    for i, update in enumerate(progress_result["progress_updates"], 1):
        print(f"\n进度更新 {i}:")
        print(update)

async def demonstrate_quality_metrics():
    """演示质量指标"""
    print("\n📊 演示质量指标")  
    print("-" * 30)
    
    # 创建不同质量水平的响应
    quality_levels = [
        ("高质量", QualityMetrics(0.92, 0.98, 0.90, 0.88, 0.95, 0.89)),
        ("中等质量", QualityMetrics(0.75, 0.85, 0.70, 0.72, 0.78, 0.68)), 
        ("需要改进", QualityMetrics(0.58, 0.75, 0.55, 0.45, 0.60, 0.52))
    ]
    
    for level_name, quality in quality_levels:
        builder = ResponseBuilder("QualityDemoAgent", "quality_demo", f"quality_task_{level_name}")
        
        # 根据质量水平添加不同的问题
        if quality.overall_score < 0.7:
            builder.add_issue("error", "high", "代码存在语法错误")
            builder.add_issue("warning", "medium", "测试覆盖率不足")
        elif quality.overall_score < 0.8:
            builder.add_issue("warning", "medium", "建议优化性能")
        
        response = builder.build(
            response_type=ResponseType.QUALITY_REPORT,
            status=TaskStatus.SUCCESS if quality.overall_score >= 0.7 else TaskStatus.REQUIRES_RETRY,
            message=f"{level_name}模块设计完成",
            completion_percentage=100.0,
            quality_metrics=quality
        )
        
        print(f"\n{level_name} (总分: {quality.overall_score:.2f}):")
        print(response.format_response(ResponseFormat.JSON)[:400] + "...")

async def main():
    """主演示函数"""
    print("🚀 标准化响应格式系统演示")
    print("=" * 80)
    
    # 1. 基本响应格式演示
    await demonstrate_response_formats()
    
    # 2. 错误处理演示
    await demonstrate_error_handling()
    
    # 3. 进度更新演示
    await demonstrate_progress_updates()
    
    # 4. 质量指标演示
    await demonstrate_quality_metrics()
    
    print("\n" + "=" * 80)
    print("🎉 演示完成！")
    print("\n📚 更多信息请参考:")
    print("  - docs/STANDARDIZED_RESPONSE_GUIDE.md")
    print("  - test_standardized_response.py")

if __name__ == "__main__":
    asyncio.run(main())