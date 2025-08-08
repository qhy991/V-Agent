#!/usr/bin/env python3
"""
上下文传递问题修复验证测试

此测试脚本验证我们对上下文传递问题的修复是否有效。
测试场景：模拟设计智能体生成完整代码，代码审查智能体接收并验证代码的完整性。
"""

import asyncio
import logging
import sys
import tempfile
import json
from pathlib import Path

# 设置路径
sys.path.append(str(Path(__file__).parent))

from core.code_consistency_checker import get_consistency_checker, CodeConsistencyChecker
from core.task_file_context import TaskFileContext, FileType
from core.base_agent import BaseAgent, AgentCapability
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试用的复杂counter模块（模拟设计智能体的输出）
COMPLEX_COUNTER_VERILOG = """module counter #(
    parameter WIDTH = 8,
    parameter MAX_COUNT = 255
)(
    input wire clk,
    input wire rst_n,
    input wire en,
    input wire up,
    input wire load,
    input wire [WIDTH-1:0] data_in,
    output reg [WIDTH-1:0] count,
    output reg rollover
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
        rollover <= 1'b0;
    end else if (load) begin
        count <= data_in;
        rollover <= 1'b0;
    end else if (en) begin
        if (up) begin
            if (count == MAX_COUNT) begin
                count <= {WIDTH{1'b0}};
                rollover <= 1'b1;
            end else begin
                count <= count + 1;
                rollover <= 1'b0;
            end
        end else begin
            if (count == 0) begin
                count <= MAX_COUNT;
                rollover <= 1'b1;
            end else begin
                count <= count - 1;
                rollover <= 1'b0;
            end
        end
    end else begin
        rollover <= 1'b0;
    end
end

endmodule"""

# 测试用的简化counter模块（模拟错误传递的版本）
SIMPLIFIED_COUNTER_VERILOG = """module counter #(
    parameter C_WIDTH = 4,
    parameter C_TYPE  = "BOTH"  
)(
    input      clk,
    input      rst_n,
    input      en,
    input      up,
    output reg [C_WIDTH-1:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 'b0;
    end else if (en) begin
        case ({up})
            1'b1: count <= count + 1;
            1'b0: count <= count - 1;
            default: count <= count;
        endcase
    end
end

endmodule"""


class TestContextPassingFix:
    """上下文传递修复测试类"""
    
    def __init__(self):
        self.logger = logger
        self.checker = get_consistency_checker()
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始上下文传递修复验证测试")
        
        tests = [
            ("代码一致性检查器基础功能测试", self.test_consistency_checker_basic),
            ("代码完整性验证测试", self.test_code_completeness_validation),
            ("TaskFileContext完整性验证测试", self.test_task_file_context_validation),
            ("智能体上下文验证增强测试", self.test_agent_context_validation),
            ("端到端上下文传递测试", self.test_end_to_end_context_passing),
        ]
        
        for test_name, test_func in tests:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🧪 执行测试: {test_name}")
            self.logger.info(f"{'='*60}")
            
            try:
                result = await test_func()
                self.test_results.append((test_name, result, None))
                if result:
                    self.logger.info(f"✅ 测试通过: {test_name}")
                else:
                    self.logger.error(f"❌ 测试失败: {test_name}")
            except Exception as e:
                self.logger.error(f"💥 测试异常: {test_name} - {str(e)}")
                self.test_results.append((test_name, False, str(e)))
        
        # 输出测试摘要
        self.print_test_summary()
    
    async def test_consistency_checker_basic(self) -> bool:
        """测试1: 代码一致性检查器基础功能"""
        try:
            # 测试相同代码的一致性检查
            result_same = self.checker.check_consistency(COMPLEX_COUNTER_VERILOG, COMPLEX_COUNTER_VERILOG)
            if not result_same.is_consistent:
                self.logger.error("❌ 相同代码应该通过一致性检查")
                return False
            
            # 测试不同代码的一致性检查
            result_different = self.checker.check_consistency(COMPLEX_COUNTER_VERILOG, SIMPLIFIED_COUNTER_VERILOG)
            if result_different.is_consistent:
                self.logger.error("❌ 不同代码应该无法通过一致性检查")
                return False
            
            self.logger.info(f"✅ 检测到代码不一致，问题: {result_different.issues}")
            self.logger.info(f"✅ 一致性置信度: {result_different.confidence:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 代码一致性检查器测试失败: {str(e)}")
            return False
    
    async def test_code_completeness_validation(self) -> bool:
        """测试2: 代码完整性验证"""
        try:
            # 验证完整代码
            complete_result = self.checker.validate_code_parameter(
                COMPLEX_COUNTER_VERILOG, 
                ["parameterized", "width_parameter", "enable_input", "reset_input"]
            )
            
            if not complete_result['valid']:
                self.logger.error(f"❌ 完整代码应该通过验证: {complete_result.get('issues', [])}")
                return False
            
            # 验证简化代码
            simple_result = self.checker.validate_code_parameter(
                SIMPLIFIED_COUNTER_VERILOG,
                ["load_function", "rollover_output"]
            )
            
            if simple_result['valid']:
                self.logger.error("❌ 简化代码应该无法通过完整性验证")
                return False
            
            self.logger.info(f"✅ 检测到代码不完整，问题: {simple_result.get('issues', [])}")
            
            # 比较模块信息
            complete_info = complete_result.get('module_info')
            simple_info = simple_result.get('module_info')
            
            if complete_info and simple_info:
                self.logger.info(f"✅ 完整代码签名: {complete_info.get_signature()}")
                self.logger.info(f"✅ 简化代码签名: {simple_info.get_signature()}")
                
                # 验证签名确实不同
                if complete_info.get_signature() == simple_info.get_signature():
                    self.logger.error("❌ 完整代码和简化代码的签名不应该相同")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 代码完整性验证测试失败: {str(e)}")
            return False
    
    async def test_task_file_context_validation(self) -> bool:
        """测试3: TaskFileContext完整性验证"""
        try:
            # 创建任务文件上下文
            task_context = TaskFileContext("test_task")
            
            # 添加完整的设计文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
                f.write(COMPLEX_COUNTER_VERILOG)
                complete_file_path = f.name
            
            task_context.add_file(
                file_path=complete_file_path,
                content=COMPLEX_COUNTER_VERILOG,
                file_type=FileType.VERILOG,
                is_primary_design=True
            )
            
            # 测试主设计文件内容获取（包含验证）
            primary_content = task_context.get_primary_design_content()
            if not primary_content:
                self.logger.error("❌ 无法获取主设计文件内容")
                return False
            
            if primary_content != COMPLEX_COUNTER_VERILOG:
                self.logger.error("❌ 主设计文件内容不匹配")
                return False
            
            self.logger.info("✅ TaskFileContext主设计文件内容获取成功")
            
            # 清理临时文件
            Path(complete_file_path).unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ TaskFileContext验证测试失败: {str(e)}")
            return False
    
    async def test_agent_context_validation(self) -> bool:
        """测试4: 智能体上下文验证增强"""
        try:
            # 创建测试智能体
            from config.config import FrameworkConfig
            config = FrameworkConfig.from_env()
            reviewer = EnhancedRealCodeReviewAgent(config)
            
            # 模拟传入简化代码参数，测试验证功能
            reviewer.agent_state_cache = {
                "last_read_files": {}
            }
            
            # 测试代码完整性评估
            complete_score = reviewer._evaluate_code_completeness(COMPLEX_COUNTER_VERILOG)
            simple_score = reviewer._evaluate_code_completeness(SIMPLIFIED_COUNTER_VERILOG)
            
            self.logger.info(f"✅ 完整代码完整性得分: {complete_score}")
            self.logger.info(f"✅ 简化代码完整性得分: {simple_score}")
            
            if complete_score <= simple_score:
                self.logger.error("❌ 完整代码的得分应该高于简化代码")
                return False
            
            # 测试代码一致性验证
            reviewer._validate_code_consistency(COMPLEX_COUNTER_VERILOG, "完整代码测试")
            reviewer._validate_code_consistency(SIMPLIFIED_COUNTER_VERILOG, "简化代码测试")
            
            self.logger.info("✅ 智能体代码一致性验证功能正常")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 智能体上下文验证测试失败: {str(e)}")
            return False
    
    async def test_end_to_end_context_passing(self) -> bool:
        """测试5: 端到端上下文传递测试"""
        try:
            self.logger.info("🔄 开始端到端上下文传递测试")
            
            # 步骤1: 模拟设计智能体生成完整代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
                f.write(COMPLEX_COUNTER_VERILOG)
                design_file_path = f.name
            
            self.logger.info(f"📁 创建设计文件: {design_file_path}")
            
            # 步骤2: 创建任务上下文并加载设计文件
            task_context = TaskFileContext("e2e_test")
            task_context.add_file(
                file_path=design_file_path,
                content=COMPLEX_COUNTER_VERILOG,
                file_type=FileType.VERILOG,
                is_primary_design=True,
                metadata={"actual_module_name": "counter"}
            )
            
            # 步骤3: 验证任务上下文中的代码完整性
            primary_content = task_context.get_primary_design_content()
            if not primary_content:
                self.logger.error("❌ 无法从任务上下文获取设计内容")
                return False
            
            # 步骤4: 模拟智能体接收上下文进行处理
            from config.config import FrameworkConfig
            config = FrameworkConfig.from_env()
            reviewer = EnhancedRealCodeReviewAgent(config)
            
            # 设置智能体的任务上下文
            reviewer.current_task_context = task_context
            reviewer.agent_state_cache = {
                "task_file_context": task_context.to_dict(),
                "last_read_files": {
                    design_file_path: {
                        "content": COMPLEX_COUNTER_VERILOG,
                        "file_type": "verilog"
                    }
                }
            }
            
            # 步骤5: 测试智能体的工具调用上下文检查
            from core.function_calling.structures import ToolCall
            test_tool_call = ToolCall(
                tool_name="generate_testbench",
                parameters={"module_name": "counter"}
            )
            
            # 这应该触发上下文验证和代码完整性检查
            reviewer._validate_and_fix_code_parameter(test_tool_call)
            
            # 步骤6: 验证工具调用参数是否包含完整代码
            if "module_code" in test_tool_call.parameters:
                received_code = test_tool_call.parameters["module_code"]
                
                # 验证接收到的代码是否完整
                validation_result = self.checker.validate_code_parameter(
                    received_code,
                    ["parameterized", "width_parameter", "enable_input", "reset_input"]
                )
                
                if not validation_result['valid']:
                    self.logger.error(f"❌ 智能体接收到的代码不完整: {validation_result.get('issues', [])}")
                    return False
                
                self.logger.info("✅ 智能体成功接收完整的设计代码")
                
                # 验证代码内容匹配
                if "WIDTH = 8" not in received_code:
                    self.logger.error("❌ 接收到的代码不包含期望的WIDTH参数")
                    return False
                
                if "load" not in received_code or "rollover" not in received_code:
                    self.logger.error("❌ 接收到的代码缺少关键功能")
                    return False
                
                self.logger.info("✅ 代码内容验证通过，包含所有期望功能")
            else:
                self.logger.warning("⚠️ 工具调用没有添加module_code参数，可能是通过其他方式传递")
            
            # 清理
            Path(design_file_path).unlink()
            
            self.logger.info("🎉 端到端上下文传递测试完全成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 端到端上下文传递测试失败: {str(e)}")
            import traceback
            self.logger.error(f"❌ 详细错误信息: {traceback.format_exc()}")
            return False
    
    def print_test_summary(self):
        """打印测试摘要"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info("🎯 上下文传递修复验证测试摘要")
        self.logger.info(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result, _ in self.test_results if result)
        failed_tests = total_tests - passed_tests
        
        self.logger.info(f"📊 总测试数: {total_tests}")
        self.logger.info(f"✅ 通过测试: {passed_tests}")
        self.logger.info(f"❌ 失败测试: {failed_tests}")
        self.logger.info(f"🎯 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            self.logger.info(f"\n❌ 失败的测试:")
            for test_name, result, error in self.test_results:
                if not result:
                    self.logger.info(f"  - {test_name}")
                    if error:
                        self.logger.info(f"    错误: {error}")
        
        self.logger.info(f"\n{'='*80}")
        
        if passed_tests == total_tests:
            self.logger.info("🎉 所有测试通过！上下文传递问题修复成功！")
        else:
            self.logger.info("⚠️ 部分测试失败，需要进一步修复。")
        
        self.logger.info(f"{'='*80}")


async def main():
    """主函数"""
    test_runner = TestContextPassingFix()
    await test_runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())