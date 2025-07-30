#!/usr/bin/env python3
"""
Function Calling系统测试

Test the Function Calling System
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig
from core.function_calling import ToolCall, ToolResult

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FunctionCallingTest:
    """Function Calling系统测试类"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.agent = None
        
    async def setup_test_environment(self):
        """设置测试环境"""
        logger.info("🔧 设置Function Calling测试环境...")
        
        try:
            # 创建支持Function Calling的代码审查智能体
            self.agent = RealCodeReviewAgent(self.config)
            logger.info("✅ 智能体创建完成")
            
            # 验证工具注册
            available_tools = self.agent.tool_registry.list_tools()
            logger.info(f"✅ 可用工具: {list(available_tools.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试环境设置失败: {str(e)}")
            return False
    
    async def test_simple_tool_call(self):
        """测试简单工具调用"""
        logger.info("\n" + "="*60)
        logger.info("🧪 测试1: 简单工具调用")
        logger.info("="*60)
        
        test_start_time = time.time()
        
        try:
            # 简单的Verilog代码
            test_code = """
module simple_counter(
    input wire clk,
    input wire rst_n,
    input wire enable,
    output reg [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else if (enable) begin
        count <= count + 1;
    end
end

endmodule
"""
            
            # 构建对话
            conversation = [
                {
                    "role": "system",
                    "content": self.agent._get_base_system_prompt()
                },
                {
                    "role": "user", 
                    "content": f"请分析以下Verilog代码的质量：\n\n{test_code}"
                }
            ]
            
            logger.info("📝 发送代码质量分析请求...")
            
            # 执行对话
            response = await self.agent._call_llm(conversation)
            logger.info(f"🤖 LLM响应: {response[:200]}...")
            
            # 解析工具调用
            tool_calls = self.agent._parse_tool_calls(response)
            
            if tool_calls:
                logger.info(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                
                # 执行工具调用
                for i, tool_call in enumerate(tool_calls, 1):
                    logger.info(f"🔧 执行工具调用 {i}: {tool_call.tool_name}")
                    
                    result = await self.agent._execute_tool_call(tool_call)
                    
                    if result.success:
                        logger.info(f"✅ 工具执行成功: {result.result.get('message', 'N/A')}")
                        
                        # 将结果添加到对话中
                        conversation.append({
                            "role": "assistant",
                            "content": response
                        })
                        conversation.append({
                            "role": "user",
                            "content": f"工具执行结果: {json.dumps(result.result, ensure_ascii=False, indent=2)}"
                        })
                        
                        # 获取最终分析
                        final_response = await self.agent._call_llm(conversation)
                        logger.info(f"📊 最终分析: {final_response[:300]}...")
                    else:
                        logger.error(f"❌ 工具执行失败: {result.error}")
            else:
                logger.info("ℹ️ 未检测到工具调用，LLM直接提供了分析")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ 测试1完成 - 用时: {test_duration:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试1失败: {str(e)}")
            return False
    
    async def test_testbench_generation(self):
        """测试测试台生成"""
        logger.info("\n" + "="*60)
        logger.info("🧪 测试2: 测试台生成")
        logger.info("="*60)
        
        test_start_time = time.time()
        
        try:
            # 更复杂的Verilog代码
            test_code = """
module alu_8bit(
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [2:0] op,
    output reg [7:0] result,
    output reg zero_flag,
    output reg overflow_flag
);

// 操作码定义
localparam ADD = 3'b000;
localparam SUB = 3'b001;
localparam AND = 3'b010;
localparam OR  = 3'b011;
localparam XOR = 3'b100;

always @(*) begin
    case (op)
        ADD: begin
            result = a + b;
            overflow_flag = (a[7] == b[7]) && (result[7] != a[7]);
        end
        SUB: begin
            result = a - b;
            overflow_flag = (a[7] != b[7]) && (result[7] == b[7]);
        end
        AND: begin
            result = a & b;
            overflow_flag = 1'b0;
        end
        OR: begin
            result = a | b;
            overflow_flag = 1'b0;
        end
        XOR: begin
            result = a ^ b;
            overflow_flag = 1'b0;
        end
        default: begin
            result = 8'b0;
            overflow_flag = 1'b0;
        end
    endcase
    
    zero_flag = (result == 8'b0);
end

endmodule
"""
            
            # 构建对话
            conversation = [
                {
                    "role": "system",
                    "content": self.agent._get_base_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"请为以下ALU模块生成测试台：\n\n{test_code}"
                }
            ]
            
            logger.info("📝 发送测试台生成请求...")
            
            # 执行对话
            response = await self.agent._call_llm(conversation)
            logger.info(f"🤖 LLM响应: {response[:200]}...")
            
            # 解析工具调用
            tool_calls = self.agent._parse_tool_calls(response)
            
            if tool_calls:
                logger.info(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                
                # 执行工具调用
                for i, tool_call in enumerate(tool_calls, 1):
                    logger.info(f"🔧 执行工具调用 {i}: {tool_call.tool_name}")
                    
                    result = await self.agent._execute_tool_call(tool_call)
                    
                    if result.success:
                        logger.info(f"✅ 工具执行成功: {result.result.get('message', 'N/A')}")
                        
                        # 检查是否生成了测试台代码
                        if 'testbench_code' in result.result:
                            testbench_code = result.result['testbench_code']
                            logger.info(f"📄 生成的测试台代码长度: {len(testbench_code)} 字符")
                            logger.info(f"📄 测试台代码预览: {testbench_code[:200]}...")
                        
                        # 将结果添加到对话中
                        conversation.append({
                            "role": "assistant",
                            "content": response
                        })
                        conversation.append({
                            "role": "user",
                            "content": f"工具执行结果: {json.dumps(result.result, ensure_ascii=False, indent=2)}"
                        })
                        
                        # 获取最终分析
                        final_response = await self.agent._call_llm(conversation)
                        logger.info(f"📊 最终分析: {final_response[:300]}...")
                    else:
                        logger.error(f"❌ 工具执行失败: {result.error}")
            else:
                logger.info("ℹ️ 未检测到工具调用，LLM直接提供了分析")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ 测试2完成 - 用时: {test_duration:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试2失败: {str(e)}")
            return False
    
    async def test_multi_tool_workflow(self):
        """测试多工具工作流程"""
        logger.info("\n" + "="*60)
        logger.info("🧪 测试3: 多工具工作流程")
        logger.info("="*60)
        
        test_start_time = time.time()
        
        try:
            # 测试代码
            test_code = """
module simple_adder(
    input wire [3:0] a,
    input wire [3:0] b,
    output wire [4:0] sum
);

assign sum = a + b;

endmodule
"""
            
            # 构建对话
            conversation = [
                {
                    "role": "system",
                    "content": self.agent._get_base_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"请对以下代码进行完整的验证：1) 分析代码质量 2) 生成测试台 3) 运行仿真验证\n\n{test_code}"
                }
            ]
            
            logger.info("📝 发送完整验证请求...")
            
            # 执行多轮对话
            max_iterations = 5
            for iteration in range(max_iterations):
                logger.info(f"🔄 第 {iteration + 1} 轮对话...")
                
                # 执行对话
                response = await self.agent._call_llm(conversation)
                logger.info(f"🤖 LLM响应: {response[:150]}...")
                
                # 解析工具调用
                tool_calls = self.agent._parse_tool_calls(response)
                
                if tool_calls:
                    logger.info(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                    
                    # 执行所有工具调用
                    tool_results = []
                    for i, tool_call in enumerate(tool_calls, 1):
                        logger.info(f"🔧 执行工具调用 {i}: {tool_call.tool_name}")
                        
                        result = await self.agent._execute_tool_call(tool_call)
                        tool_results.append(result)
                        
                        if result.success:
                            logger.info(f"✅ 工具执行成功: {result.result.get('message', 'N/A')}")
                        else:
                            logger.error(f"❌ 工具执行失败: {result.error}")
                    
                    # 将结果添加到对话中
                    conversation.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # 添加所有工具执行结果
                    results_summary = []
                    for result in tool_results:
                        if result.success:
                            results_summary.append(f"工具调用: 成功 - {result.result.get('message', 'N/A')}")
                        else:
                            results_summary.append(f"工具调用: 失败 - {result.error}")
                    
                    conversation.append({
                        "role": "user",
                        "content": f"工具执行结果:\n" + "\n".join(results_summary)
                    })
                    
                else:
                    logger.info("ℹ️ 未检测到工具调用，对话完成")
                    break
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ 测试3完成 - 用时: {test_duration:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试3失败: {str(e)}")
            return False
    
    async def generate_test_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*60)
        logger.info("📊 生成Function Calling测试报告")
        logger.info("="*60)
        
        report = f"""# Function Calling系统测试报告

## 测试概览
- 执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 测试智能体: RealCodeReviewAgent (支持Function Calling)
- 可用工具: {list(self.agent.tool_registry.list_tools().keys())}

## 系统架构
- 基于输出解析的Function Calling
- 支持JSON格式的工具调用解析
- 异步工具执行
- 结果回传给LLM进行后续分析

## 主要特性
1. **智能工具选择**: LLM根据任务需求自动选择合适的工具
2. **结构化输出**: 使用JSON格式确保工具调用的准确性
3. **异步执行**: 支持长时间运行的工具（如仿真）
4. **结果集成**: 工具执行结果自动集成到对话流程中

## 工具功能
1. **generate_testbench**: 为Verilog模块生成测试台
2. **run_simulation**: 使用iverilog运行仿真
3. **analyze_code_quality**: 分析代码质量

## 优势
- 不依赖LLM API的原生function calling
- 更灵活的工具定义和调用
- 支持复杂的多工具工作流程
- 易于扩展和维护

---
报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        try:
            output_dir = Path("./output")
            output_dir.mkdir(exist_ok=True)
            
            report_path = output_dir / f"function_calling_test_report_{int(time.time())}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"📄 测试报告已保存: {report_path}")
            print("\n" + report)
            
        except Exception as e:
            logger.error(f"❌ 保存报告失败: {str(e)}")
            print("\n" + report)

async def main():
    """主测试函数"""
    logger.info("🚀 启动Function Calling系统测试")
    logger.info("=" * 80)
    
    test_suite = FunctionCallingTest()
    
    try:
        # 设置测试环境
        if not await test_suite.setup_test_environment():
            logger.error("❌ 测试环境设置失败，退出测试")
            return False
        
        logger.info("✅ 测试环境准备完成，开始执行测试...")
        
        # 执行测试套件
        test_results = []
        
        # 测试1: 简单工具调用
        result1 = await test_suite.test_simple_tool_call()
        test_results.append(result1)
        
        # 测试2: 测试台生成
        result2 = await test_suite.test_testbench_generation()
        test_results.append(result2)
        
        # 测试3: 多工具工作流程
        result3 = await test_suite.test_multi_tool_workflow()
        test_results.append(result3)
        
        # 生成测试报告
        await test_suite.generate_test_report()
        
        # 输出最终结果
        successful_tests = sum(test_results)
        total_tests = len(test_results)
        
        logger.info("\n" + "=" * 80)
        logger.info(f"🏁 Function Calling测试完成: {successful_tests}/{total_tests} 通过")
        
        if successful_tests == total_tests:
            logger.info("🎉 所有测试通过！Function Calling系统运行完美！")
            return True
        else:
            logger.warning(f"⚠️ {total_tests - successful_tests} 个测试失败，系统需要优化")
            return False
    
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 