#!/usr/bin/env python3
"""
测试Verilog代码测试功能

Test Verilog Code Testing Functionality
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig
from core.base_agent import TaskMessage

async def test_verilog_testing():
    """测试Verilog代码测试功能"""
    
    # 创建一个简单的ALU模块用于测试
    test_verilog_code = '''
module simple_alu (
    input [3:0] a,
    input [3:0] b,
    input [1:0] op,
    output reg [3:0] result,
    output reg zero_flag
);

always @(*) begin
    case (op)
        2'b00: result = a + b;  // 加法
        2'b01: result = a - b;  // 减法
        2'b10: result = a & b;  // 与运算
        2'b11: result = a | b;  // 或运算
        default: result = 4'b0000;
    endcase
    
    zero_flag = (result == 4'b0000);
end

endmodule
'''
    
    print("🧪 开始测试Verilog代码测试功能")
    print("=" * 60)
    
    try:
        # 1. 创建审查智能体
        config = FrameworkConfig.from_env()
        reviewer = RealCodeReviewAgent(config)
        
        print("✅ 审查智能体创建成功")
        
        # 2. 准备测试任务
        task_message = TaskMessage(
            task_id="test_verilog_testing",
            sender_id="test_runner",
            receiver_id="real_code_review_agent",
            message_type="task_execution",
            content="请对这个简单的ALU模块进行代码审查，并生成测试台进行功能验证",
            metadata={"test_mode": True}
        )
        
        # 3. 准备文件内容
        file_contents = {
            "simple_alu.v": {
                "type": "verilog",
                "content": test_verilog_code
            }
        }
        
        print("📝 开始执行测试任务...")
        
        # 4. 执行增强任务
        result = await reviewer.execute_enhanced_task(
            enhanced_prompt="请对ALU模块进行全面的代码审查，包括语法检查、设计质量评估，并生成完整的测试台验证其功能正确性",
            original_message=task_message,
            file_contents=file_contents
        )
        
        print("✅ 测试任务执行完成")
        print("\n📊 测试结果:")
        
        if "formatted_response" in result:
            import json
            try:
                response_data = json.loads(result["formatted_response"])
                print(f"- 智能体: {response_data.get('agent_name', 'Unknown')}")
                print(f"- 状态: {response_data.get('status', 'Unknown')}")
                print(f"- 完成度: {response_data.get('completion_percentage', 0)}%")
                print(f"- 消息: {response_data.get('message', 'No message')}")
                
                # 检查生成的文件
                generated_files = response_data.get('generated_files', [])
                print(f"- 生成文件数: {len(generated_files)}")
                for file_info in generated_files:
                    print(f"  * {file_info.get('path', 'Unknown')}: {file_info.get('description', 'No description')}")
                
                # 检查测试相关的元数据
                metadata = response_data.get('metadata', {})
                if metadata.get('testing_performed'):
                    print(f"- 测试执行: ✅")
                    print(f"- 测试数量: {metadata.get('total_tests', 0)}")
                    print(f"- 成功测试: {metadata.get('successful_tests', 0)}")
                    print(f"- 测试覆盖率: {metadata.get('test_coverage', 0):.1%}")
                    if 'average_test_pass_rate' in metadata:
                        print(f"- 平均通过率: {metadata['average_test_pass_rate']:.1%}")
                else:
                    print(f"- 测试执行: ❌")
                
                # 检查质量指标
                quality_metrics = response_data.get('quality_metrics', {})
                if quality_metrics:
                    print(f"- 整体质量: {quality_metrics.get('overall_score', 0):.2f}")
                    print(f"- 语法正确性: {quality_metrics.get('syntax_score', 0):.2f}")
                    print(f"- 功能质量: {quality_metrics.get('functionality_score', 0):.2f}")
                
            except json.JSONDecodeError as e:
                print(f"❌ 响应解析失败: {e}")
                print("原始响应:", result["formatted_response"][:500] + "...")
        else:
            print("❌ 未找到格式化响应")
            print("原始结果:", result)
        
        print("\n🎉 测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_verilog_testing())
    sys.exit(0 if success else 1)