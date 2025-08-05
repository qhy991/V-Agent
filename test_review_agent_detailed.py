#!/usr/bin/env python3
"""
单独测试审查智能体的详细测试

Test Review Agent Context and Problem Solving
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging


class ReviewAgentTester:
    """审查智能体测试器"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.reviewer = EnhancedRealCodeReviewAgent(self.config)
        
    def create_buggy_alu_code(self) -> str:
        """创建包含已知错误的ALU代码"""
        return '''module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果 - 🚨 错误1: 应该是 output reg
    output        zero      // 零标志 - 🚨 错误2: 应该是 output reg
);

    // 🚨 错误3: 中间信号没有声明
    // wire [31:0] add_result;
    // wire [31:0] sub_result;
    
    // 🚨 错误4: always块中给wire类型赋值
    always @(*) begin
        case (op)
            4'b0000: result = a + b;        // ADD
            4'b0001: result = a - b;        // SUB  
            4'b0010: result = a & b;        // AND
            4'b0011: result = a | b;        // OR
            4'b0100: result = a ^ b;        // XOR
            4'b0101: result = a << b[4:0];  // SLL
            4'b0110: result = a >> b[4:0];  // SRL
            default: result = 32'h00000000;
        endcase
    end
    
    // 🚨 错误5: zero信号的assign与always块冲突
    assign zero = (result == 32'h0);

endmodule'''

    def create_buggy_testbench(self) -> str:
        """创建包含SystemVerilog语法错误的测试台"""
        return '''`timescale 1ns/1ps

module testbench_alu_32bit;
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    
    alu_32bit uut (
        .a(a),
        .b(b), 
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    initial begin
        $display("ALU Test Starting...");
        
        // 🚨 错误6: task中多语句没有begin..end
        test_add_operation;
        test_sub_operation;
        
        $finish;
    end
    
    // 🚨 错误7: task语法错误 - 多语句需要begin..end
    task test_add_operation;
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0000;
        #10;
        $display("ADD: %h + %h = %h", a, b, result);
    endtask
    
    task test_sub_operation;
        a = 32'hFFFFFFFF;
        b = 32'h00000001;
        op = 4'b0001;
        #10;
        $display("SUB: %h - %h = %h", a, b, result);
    endtask

endmodule'''

    async def test_context_preservation(self):
        """测试上下文保持能力"""
        print("🧠 测试1: 上下文保持能力")
        print("="*60)
        
        conversation_id = "test_context_001"
        
        # 第一轮：提供有问题的代码进行初步分析
        print("📋 第一轮：初步代码分析")
        initial_summary = self.reviewer.get_conversation_summary()
        print(f"初始状态: {initial_summary}")
        
        buggy_code = self.create_buggy_alu_code()
        
        response1 = await self.reviewer.process_with_function_calling(
            user_request=f"""请分析以下Verilog代码的问题：

{buggy_code}

重点分析：
1. 语法错误
2. 类型声明问题  
3. 逻辑冲突

请先保存代码到文件，然后进行详细分析。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=5
        )
        
        after_first = self.reviewer.get_conversation_summary()
        print(f"第一轮后: {after_first}")
        print(f"响应长度: {len(response1)} 字符")
        
        # 第二轮：基于第一轮的分析，要求具体修复
        print("\n📋 第二轮：基于上次分析进行修复")
        response2 = await self.reviewer.process_with_function_calling(
            user_request="""基于刚才的分析，请修复所有发现的问题：

1. 修复wire/reg类型声明错误
2. 解决assign与always的冲突  
3. 生成修复后的完整代码

请直接修复代码文件，不要只是说明问题。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=5
        )
        
        after_second = self.reviewer.get_conversation_summary()
        print(f"第二轮后: {after_second}")
        print(f"响应长度: {len(response2)} 字符")
        
        # 第三轮：验证修复效果
        print("\n📋 第三轮：验证修复效果")
        response3 = await self.reviewer.process_with_function_calling(
            user_request="""请验证刚才的修复是否正确：

1. 读取修复后的代码文件
2. 生成对应的测试台
3. 运行仿真验证功能正确性

如果还有问题，请继续修复。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=8
        )
        
        after_third = self.reviewer.get_conversation_summary()
        print(f"第三轮后: {after_third}")
        print(f"响应长度: {len(response3)} 字符")
        
        # 分析上下文保持效果
        context_growth = (
            after_second['message_count'] > after_first['message_count'] and
            after_third['message_count'] > after_second['message_count']
        )
        
        print(f"\n📊 上下文分析:")
        print(f"  - 消息数量增长: {context_growth}")
        print(f"  - 总对话时长: {after_third['conversation_duration']:.1f}秒")
        print(f"  - 对话历史长度: {len(self.reviewer.conversation_history)}")
        
        # 检查内容连贯性
        context_aware = any(keyword in response2.lower() for keyword in 
                          ["刚才", "之前", "上面", "分析", "发现"])
        validation_aware = any(keyword in response3.lower() for keyword in 
                             ["修复", "刚才", "之前", "验证"])
        
        print(f"  - 第二轮上下文感知: {context_aware}")
        print(f"  - 第三轮验证感知: {validation_aware}")
        
        return {
            "context_preserved": context_growth,
            "context_aware": context_aware and validation_aware,
            "conversation_length": len(self.reviewer.conversation_history),
            "total_duration": after_third['conversation_duration']
        }

    async def test_problem_solving_capability(self):
        """测试问题解决能力"""
        print("\n🔧 测试2: 问题解决能力")
        print("="*60)
        
        conversation_id = "test_solving_002"
        
        # 创建一个明确的错误场景
        buggy_testbench = self.create_buggy_testbench()
        
        print("📋 场景：SystemVerilog语法错误修复")
        response = await self.reviewer.process_with_function_calling(
            user_request=f"""以下测试台代码有SystemVerilog语法错误，导致iverilog编译失败：

{buggy_testbench}

错误信息：
"error: Task body with multiple statements requires SystemVerilog."

请：
1. 保存原始代码到文件
2. 分析具体错误原因
3. 修复语法错误（使其符合Verilog-2001标准）
4. 保存修复后的代码
5. 验证修复是否正确

重点：必须实际修改代码文件，不要只是分析。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=8
        )
        
        final_summary = self.reviewer.get_conversation_summary()
        print(f"最终状态: {final_summary}")
        
        # 检查是否真正解决了问题
        fixed_code = "begin" in response and "endtask" in response
        file_operations = "write_file" in response.lower() or "保存" in response
        
        print(f"\n📊 解决能力分析:")
        print(f"  - 识别到语法错误: {'task' in response.lower()}")
        print(f"  - 提供了修复方案: {fixed_code}")
        print(f"  - 执行了文件操作: {file_operations}")
        print(f"  - 响应长度: {len(response)} 字符")
        
        return {
            "problem_identified": "task" in response.lower(),
            "solution_provided": fixed_code,
            "files_modified": file_operations,
            "response_length": len(response)
        }

    async def test_iterative_debugging(self):
        """测试迭代调试能力"""
        print("\n🔍 测试3: 迭代调试能力") 
        print("="*60)
        
        conversation_id = "test_debug_003"
        
        # 模拟编译失败场景
        print("📋 场景：模拟编译失败的迭代修复过程")
        
        # 第一次：报告编译错误
        response1 = await self.reviewer.process_with_function_calling(
            user_request="""我有一个ALU设计和测试台，但编译失败了。

编译错误日志：
```
testbench.v:45: error: Task body with multiple statements requires SystemVerilog.
testbench.v:52: error: Task body with multiple statements requires SystemVerilog.
testbench.v:59: error: Task body with multiple statements requires SystemVerilog.
```

请分析这些错误并制定修复计划。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=3
        )
        
        print(f"第一次分析: {len(response1)} 字符")
        
        # 第二次：提供具体代码要求修复
        response2 = await self.reviewer.process_with_function_calling(
            user_request=f"""基于刚才的分析，这是出问题的测试台代码：

{self.create_buggy_testbench()}

请：
1. 立即修复所有SystemVerilog语法错误
2. 保存修复后的代码到文件
3. 确保代码符合Verilog-2001标准""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=5
        )
        
        print(f"第二次修复: {len(response2)} 字符")
        
        # 第三次：模拟修复后的验证
        response3 = await self.reviewer.process_with_function_calling(
            user_request="""现在测试修复效果：

1. 读取刚才修复的文件
2. 检查语法是否正确
3. 如果还有问题，继续修复
4. 最终确保代码可以编译通过

请给出最终的评估结果。""",
            conversation_id=conversation_id,
            preserve_context=True,
            max_iterations=5
        )
        
        print(f"第三次验证: {len(response3)} 字符")
        
        # 分析迭代效果
        iterative_awareness = all([
            "刚才" in response2 or "之前" in response2,
            "修复" in response3 or "验证" in response3,
            len(response2) > len(response1),  # 第二次应该更详细
            "begin" in response2.lower() or "endtask" in response2.lower()
        ])
        
        final_summary = self.reviewer.get_conversation_summary()
        
        print(f"\n📊 迭代调试分析:")
        print(f"  - 迭代上下文感知: {iterative_awareness}")
        print(f"  - 最终消息数: {final_summary['message_count']}")
        print(f"  - 对话总时长: {final_summary['conversation_duration']:.1f}秒")
        
        return {
            "iterative_awareness": iterative_awareness,
            "final_message_count": final_summary['message_count'],
            "provided_concrete_fix": "begin" in response2.lower()
        }

    async def run_comprehensive_test(self):
        """运行完整测试"""
        print("🚀 开始审查智能体综合测试")
        print("="*80)
        
        # 设置日志
        setup_enhanced_logging()
        
        print(f"📋 测试智能体: {self.reviewer.agent_id}")
        print(f"📋 初始状态: {self.reviewer.get_conversation_summary()}")
        
        try:
            # 测试1：上下文保持
            context_results = await self.test_context_preservation()
            
            # 清空对话历史，准备下一个测试
            self.reviewer.clear_conversation_history()
            
            # 测试2：问题解决能力  
            solving_results = await self.test_problem_solving_capability()
            
            # 清空对话历史，准备下一个测试
            self.reviewer.clear_conversation_history()
            
            # 测试3：迭代调试
            debug_results = await self.test_iterative_debugging()
            
            # 生成综合报告
            print("\n" + "="*80)
            print("📊 综合测试报告")
            print("="*80)
            
            print(f"\n🧠 上下文保持能力:")
            print(f"  ✅ 上下文保持: {'通过' if context_results['context_preserved'] else '失败'}")
            print(f"  ✅ 上下文感知: {'通过' if context_results['context_aware'] else '失败'}")
            print(f"  📈 对话长度: {context_results['conversation_length']} 条消息")
            print(f"  ⏱️ 对话时长: {context_results['total_duration']:.1f} 秒")
            
            print(f"\n🔧 问题解决能力:")
            print(f"  ✅ 问题识别: {'通过' if solving_results['problem_identified'] else '失败'}")
            print(f"  ✅ 方案提供: {'通过' if solving_results['solution_provided'] else '失败'}")
            print(f"  ✅ 文件修改: {'通过' if solving_results['files_modified'] else '失败'}")
            print(f"  📝 响应质量: {solving_results['response_length']} 字符")
            
            print(f"\n🔍 迭代调试能力:")
            print(f"  ✅ 迭代感知: {'通过' if debug_results['iterative_awareness'] else '失败'}")
            print(f"  ✅ 具体修复: {'通过' if debug_results['provided_concrete_fix'] else '失败'}")
            print(f"  📈 最终消息: {debug_results['final_message_count']} 条")
            
            # 总体评估
            total_score = sum([
                context_results['context_preserved'],
                context_results['context_aware'],
                solving_results['problem_identified'],
                solving_results['solution_provided'], 
                solving_results['files_modified'],
                debug_results['iterative_awareness'],
                debug_results['provided_concrete_fix']
            ])
            
            print(f"\n🎯 总体评估: {total_score}/7 ({total_score/7*100:.1f}%)")
            
            if total_score >= 6:
                print("🎉 测试结果：优秀 -Agent具备良好的上下文和问题解决能力")
            elif total_score >= 4:
                print("⚠️ 测试结果：良好 - Agent基本功能正常，但有改进空间")  
            else:
                print("❌ 测试结果：需要改进 - Agent存在关键功能缺陷")
                
            return {
                "context_test": context_results,
                "solving_test": solving_results,
                "debug_test": debug_results,
                "total_score": total_score,
                "max_score": 7
            }
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


async def main():
    """主函数"""
    tester = ReviewAgentTester()
    results = await tester.run_comprehensive_test()
    
    if "error" not in results:
        print(f"\n🎯 测试完成 - 总分: {results['total_score']}/{results['max_score']}")
    else:
        print(f"\n❌ 测试失败: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())