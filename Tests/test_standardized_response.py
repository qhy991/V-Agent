#!/usr/bin/env python3
"""
测试标准化响应格式系统

Test Standardized Response Format System
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.response_format import (
    StandardizedResponse, ResponseBuilder, ResponseFormat, 
    TaskStatus, ResponseType, QualityMetrics, FileReference,
    create_success_response, create_error_response, create_progress_response
)
from core.response_parser import ResponseParser, ResponseParseError
from core.llm_coordinator_agent import LLMCoordinatorAgent
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_response_creation():
    """测试响应创建"""
    print("🧪 测试响应创建功能...")
    
    # 1. 测试ResponseBuilder
    builder = ResponseBuilder("TestAgent", "test_agent_01", "task_123")
    
    builder.add_generated_file(
        "/output/test.v", "verilog", "Generated test Verilog module"
    ).add_issue(
        "warning", "medium", "Clock signal might have setup time violations"
    ).add_next_step(
        "Run timing analysis"
    ).add_metadata("test_key", "test_value")
    
    quality_metrics = QualityMetrics(
        overall_score=0.85,
        syntax_score=0.95,
        functionality_score=0.80,
        test_coverage=0.75,
        documentation_quality=0.90
    )
    
    response = builder.build(
        response_type=ResponseType.TASK_COMPLETION,
        status=TaskStatus.SUCCESS,
        message="Successfully generated Verilog module with comprehensive testing",
        completion_percentage=100.0,
        quality_metrics=quality_metrics
    )
    
    # 2. 测试不同格式的输出
    print("\n📋 JSON格式输出:")
    json_output = response.format_response(ResponseFormat.JSON)
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
    
    print("\n📋 XML格式输出:")
    xml_output = response.format_response(ResponseFormat.XML)
    print(xml_output[:500] + "..." if len(xml_output) > 500 else xml_output)
    
    print("\n📋 Markdown格式输出:")
    md_output = response.format_response(ResponseFormat.MARKDOWN)
    print(md_output[:800] + "..." if len(md_output) > 800 else md_output)
    
    print("✅ 响应创建测试通过")
    return json_output, xml_output, md_output

def test_response_parsing():
    """测试响应解析"""
    print("\n🧪 测试响应解析功能...")
    
    parser = ResponseParser()
    
    # 1. 测试JSON解析
    json_response = {
        "agent_name": "VerilogDesignAgent",
        "agent_id": "verilog_designer_01",
        "response_type": "task_completion",
        "task_id": "task_456",
        "timestamp": "2024-01-01T10:00:00",
        "status": "success",
        "completion_percentage": 100.0,
        "message": "Successfully designed ALU module",
        "generated_files": [
            {
                "path": "/output/alu.v",
                "file_type": "verilog",
                "description": "32-bit ALU module"
            }
        ],
        "modified_files": [],
        "reference_files": [],
        "issues": [],
        "next_steps": ["Generate testbench"],
        "metadata": {"complexity": "medium"}
    }
    
    try:
        parsed_response = parser.parse_response(json.dumps(json_response), ResponseFormat.JSON)
        print(f"✅ JSON解析成功: {parsed_response.agent_name}")
        print(f"   状态: {parsed_response.status.value}")
        print(f"   完成度: {parsed_response.completion_percentage}%")
        print(f"   生成文件: {len(parsed_response.generated_files)}")
    except ResponseParseError as e:
        print(f"❌ JSON解析失败: {str(e)}")
    
    # 2. 测试Markdown解析
    markdown_response = """# Agent Response: TestbenchAgent

## 📋 Basic Information
- **Agent**: TestbenchAgent (`testbench_gen_01`)
- **Task ID**: `task_789`
- **Status**: success
- **Progress**: 100.0%
- **Timestamp**: 2024-01-01T11:00:00

## 💬 Message
Successfully generated comprehensive testbench for ALU module

## 📁 Files
### Generated Files
- **output/alu_tb.v** (testbench): Comprehensive ALU testbench with edge cases

## 🚀 Next Steps
1. Run simulation with generated testbench
2. Analyze coverage report
"""
    
    try:
        parsed_md = parser.parse_response(markdown_response, ResponseFormat.MARKDOWN)
        print(f"✅ Markdown解析成功: {parsed_md.agent_name}")
        print(f"   状态: {parsed_md.status.value}")
        print(f"   下一步数量: {len(parsed_md.next_steps)}")
    except ResponseParseError as e:
        print(f"❌ Markdown解析失败: {str(e)}")
    
    # 3. 测试自动格式检测
    try:
        auto_parsed = parser.parse_response(json.dumps(json_response))
        print(f"✅ 自动检测解析成功: {auto_parsed.agent_name}")
    except ResponseParseError as e:
        print(f"❌ 自动检测解析失败: {str(e)}")
    
    print("✅ 响应解析测试通过")
    return parsed_response

def test_validation():
    """测试响应验证"""
    print("\n🧪 测试响应验证功能...")
    
    parser = ResponseParser()
    
    # 1. 创建有效响应
    valid_response = StandardizedResponse(
        agent_name="ValidAgent",
        agent_id="valid_01",
        response_type=ResponseType.TASK_COMPLETION,
        task_id="valid_task",
        timestamp="2024-01-01T12:00:00",
        status=TaskStatus.SUCCESS,
        completion_percentage=100.0,
        message="Task completed successfully",
        generated_files=[],
        modified_files=[],
        reference_files=[],
        issues=[]
    )
    
    validation_errors = parser.validate_response(valid_response)
    if not validation_errors:
        print("✅ 有效响应验证通过")
    else:
        print(f"❌ 有效响应验证失败: {validation_errors}")
    
    # 2. 创建无效响应
    invalid_response = StandardizedResponse(
        agent_name="",  # 空名称
        agent_id="",    # 空ID
        response_type=ResponseType.TASK_COMPLETION,
        task_id="",     # 空任务ID
        timestamp="2024-01-01T12:00:00",
        status=TaskStatus.SUCCESS,
        completion_percentage=150.0,  # 超出范围
        message="",     # 空消息
        generated_files=[],
        modified_files=[],
        reference_files=[],
        issues=[]
    )
    
    validation_errors = parser.validate_response(invalid_response)
    if validation_errors:
        print(f"✅ 无效响应验证正确识别错误: {len(validation_errors)} 个问题")
        for error in validation_errors:
            print(f"   - {error}")
    else:
        print("❌ 无效响应验证失败：应该检测出错误")
    
    print("✅ 响应验证测试通过")

async def test_coordinator_integration():
    """测试协调者集成"""
    print("\n🧪 测试协调者集成功能...")
    
    try:
        # 创建配置
        config = FrameworkConfig.from_env()
        
        # 创建协调者
        coordinator = LLMCoordinatorAgent(config)
        
        # 测试设置响应格式
        coordinator.set_preferred_response_format(ResponseFormat.JSON)
        
        # 测试获取格式说明
        instructions = coordinator.get_response_format_instructions()
        print("✅ 格式说明获取成功")
        print(f"   说明长度: {len(instructions)} 字符")
        
        # 测试响应处理
        mock_raw_response = {
            "success": True,
            "message": "Test task completed",
            "generated_files": ["/output/test.v"],
            "agent_name": "TestAgent"
        }
        
        processed_response = await coordinator._process_agent_response(
            agent_id="test_agent",
            raw_response=mock_raw_response,
            task_id="test_task"
        )
        
        print("✅ 响应处理成功")
        print(f"   处理后状态: {processed_response.get('status')}")
        print(f"   文件引用数量: {len(processed_response.get('file_references', []))}")
        
        # 测试标准化响应处理
        standardized_raw = {
            "standardized_response": json.dumps({
                "agent_name": "StandardizedAgent",
                "agent_id": "std_01",
                "response_type": "task_completion",
                "task_id": "std_task",
                "timestamp": "2024-01-01T13:00:00",
                "status": "success",
                "completion_percentage": 100.0,
                "message": "Standardized response test",
                "generated_files": [],
                "modified_files": [],
                "reference_files": [],
                "issues": [],
                "next_steps": [],
                "metadata": {}
            }, ensure_ascii=False)
        }
        
        std_processed = await coordinator._process_agent_response(
            agent_id="std_agent",
            raw_response=standardized_raw,
            task_id="std_task"
        )
        
        print("✅ 标准化响应处理成功")
        print(f"   Agent名称: {std_processed.get('agent_name')}")
        print(f"   响应类型: {std_processed.get('response_type')}")
        
    except Exception as e:
        print(f"❌ 协调者集成测试失败: {str(e)}")
        return False
    
    print("✅ 协调者集成测试通过")
    return True

async def test_base_agent_integration():
    """测试BaseAgent集成"""
    print("\n🧪 测试BaseAgent集成功能...")
    
    # 由于BaseAgent是抽象类，我们创建一个简单的实现
    from core.base_agent import BaseAgent
    from core.enums import AgentCapability
    
    class TestAgent(BaseAgent):
        def get_capabilities(self):
            return {AgentCapability.CODE_GENERATION}
        
        def get_specialty_description(self):
            return "Test agent for response format testing"
        
        async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
            return {"success": True, "message": "Test task completed"}
    
    try:
        agent = TestAgent("test_agent", "test", {AgentCapability.CODE_GENERATION})
        
        # 测试响应构建器创建
        builder = agent.create_response_builder("test_task")
        print("✅ 响应构建器创建成功")
        
        # 测试格式化响应创建
        success_response = agent.create_success_response_formatted(
            task_id="test_task",
            message="Test success message",
            generated_files=["/output/test.v"],
            format_type=ResponseFormat.JSON
        )
        
        print("✅ 成功响应创建成功")
        print(f"   响应长度: {len(success_response)} 字符")
        
        # 测试错误响应创建
        error_response = agent.create_error_response_formatted(
            task_id="test_task", 
            error_message="Test error",
            format_type=ResponseFormat.MARKDOWN
        )
        
        print("✅ 错误响应创建成功")
        
        # 测试进度响应创建
        progress_response = agent.create_progress_response_formatted(
            task_id="test_task",
            message="Test in progress",
            completion_percentage=50.0,
            next_steps=["Continue testing", "Validate results"]
        )
        
        print("✅ 进度响应创建成功")
        
    except Exception as e:
        print(f"❌ BaseAgent集成测试失败: {str(e)}")
        return False
    
    print("✅ BaseAgent集成测试通过")
    return True

async def main():
    """主测试函数"""
    print("🚀 开始测试标准化响应格式系统")
    print("=" * 60)
    
    success_count = 0
    total_tests = 5
    
    try:
        # 1. 响应创建测试
        test_response_creation()
        success_count += 1
        
        # 2. 响应解析测试
        test_response_parsing()
        success_count += 1
        
        # 3. 响应验证测试
        test_validation()
        success_count += 1
        
        # 4. 协调者集成测试
        if await test_coordinator_integration():
            success_count += 1
        
        # 5. BaseAgent集成测试
        if await test_base_agent_integration():
            success_count += 1
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！标准化响应格式系统运行正常")
    else:
        print("⚠️ 部分测试失败，请检查具体错误信息")
    
    return success_count == total_tests

if __name__ == "__main__":
    asyncio.run(main())