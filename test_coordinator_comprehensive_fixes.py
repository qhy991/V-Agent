#!/usr/bin/env python3
"""
V-Agent系统协调器修复综合测试

这个测试脚本验证协调器的所有修复功能，包括：
1. 复合任务识别和分解
2. 智能体能力边界验证 
3. 任务分配冲突检测
4. 智能体幻觉检测和恢复
5. 串行工作流管理 (design→review→verification)
6. 质量门控机制
7. 任务完成强制检查

基于日志文件 counter_test_utf8-28.txt 中发现的问题进行修复验证
"""

import asyncio
import sys
import logging
import tempfile
import os
from pathlib import Path
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext, TaskType
from core.task_file_context import TaskFileContext, set_task_context
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试数据：复杂的counter设计（模拟真实设计智能体输出）
COMPLEX_COUNTER_DESIGN = """module counter #(
    parameter WIDTH = 8,
    parameter MAX_COUNT = 255,
    parameter MIN_COUNT = 0
)(
    input wire clk,
    input wire rst_n,
    input wire en,
    input wire up,
    input wire load,
    input wire clear,
    input wire [WIDTH-1:0] preset_value,
    output reg [WIDTH-1:0] count,
    output wire full,
    output wire empty,
    output wire carry_out,
    output wire borrow_out,
    output reg overflow,
    output reg underflow
);

// Internal signals
reg [WIDTH-1:0] next_count;
wire at_max, at_min;
reg prev_full, prev_empty;

// Status flags
assign full = (count == MAX_COUNT);
assign empty = (count == MIN_COUNT);
assign at_max = (count == MAX_COUNT);
assign at_min = (count == MIN_COUNT);
assign carry_out = en & up & at_max;
assign borrow_out = en & (~up) & at_min;

// Next state logic
always @(*) begin
    if (!rst_n || clear) begin
        next_count = MIN_COUNT;
    end else if (load) begin
        next_count = preset_value;
    end else if (en) begin
        if (up) begin
            next_count = at_max ? MIN_COUNT : count + 1'b1;
        end else begin
            next_count = at_min ? MAX_COUNT : count - 1'b1;
        end
    end else begin
        next_count = count;
    end
end

// Sequential logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= MIN_COUNT;
        overflow <= 1'b0;
        underflow <= 1'b0;
        prev_full <= 1'b0;
        prev_empty <= 1'b1;
    end else begin
        count <= next_count;
        
        // Edge detection for overflow/underflow
        prev_full <= full;
        prev_empty <= empty;
        overflow <= (~prev_full) & full & en & up;
        underflow <= (~prev_empty) & empty & en & (~up);
    end
end

endmodule"""

class CoordinatorFixesTest:
    """协调器修复功能综合测试"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.coordinator = None
        self.test_results = {}
        self.temp_files = []
    
    async def setup_coordinator(self):
        """设置协调器实例"""
        self.coordinator = LLMCoordinatorAgent(self.config)
        logger.info("🚀 协调器实例已创建")
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")
    
    async def test_composite_task_detection(self):
        """测试1: 复合任务识别和分解"""
        logger.info("🧪 测试1: 复合任务识别和分解")
        
        test_cases = [
            {
                "name": "标准复合任务",
                "request": "设计一个8位计数器，包含完整的端口定义、功能实现和测试台",
                "expected_composite": True,
                "expected_subtasks": ["design", "verification"]
            },
            {
                "name": "隐含复合任务", 
                "request": "实现counter模块并验证其功能",
                "expected_composite": True,
                "expected_subtasks": ["design", "verification"]
            },
            {
                "name": "单一设计任务",
                "request": "仅生成counter模块的Verilog代码",
                "expected_composite": False,
                "expected_subtasks": ["design"]
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                is_composite, details = self.coordinator._detect_composite_task(case["request"])
                
                # 验证复合任务识别
                assert is_composite == case["expected_composite"], \
                    f"复合任务识别错误: 期望{case['expected_composite']}, 实际{is_composite}"
                
                # 验证子任务分解
                if is_composite:
                    subtasks = details.get("subtasks", [])
                    for expected_subtask in case["expected_subtasks"]:
                        assert expected_subtask in subtasks, \
                            f"缺失子任务 {expected_subtask}: {subtasks}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "details": details
                })
                
            except Exception as e:
                results.append({
                    "case": case["name"], 
                    "passed": False,
                    "error": str(e)
                })
        
        self.test_results["composite_task_detection"] = results
        logger.info(f"✅ 复合任务识别测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def test_capability_boundary_verification(self):
        """测试2: 智能体能力边界验证"""
        logger.info("🧪 测试2: 智能体能力边界验证")
        
        test_cases = [
            {
                "name": "设计智能体分配测试台任务 (应被阻止)",
                "agent_id": "enhanced_real_verilog_agent",
                "task_type": "verification",
                "task_description": "生成counter模块的testbench文件",
                "expected_valid": False,
                "expected_reason_contains": "测试台生成"
            },
            {
                "name": "设计智能体分配设计任务 (应允许)",
                "agent_id": "enhanced_real_verilog_agent", 
                "task_type": "design",
                "task_description": "设计counter模块的Verilog代码",
                "expected_valid": True
            },
            {
                "name": "审查智能体分配测试台任务 (应允许)",
                "agent_id": "enhanced_real_code_review_agent",
                "task_type": "verification", 
                "task_description": "生成counter模块的testbench并执行仿真",
                "expected_valid": True
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                boundary_check = self.coordinator._verify_task_assignment_boundary(
                    case["agent_id"], case["task_type"], case["task_description"]
                )
                
                is_valid = boundary_check["valid"]
                reason = boundary_check.get("reason", "")
                
                # 验证边界检查结果
                assert is_valid == case["expected_valid"], \
                    f"边界检查错误: 期望valid={case['expected_valid']}, 实际valid={is_valid}, 原因: {reason}"
                
                # 如果期望被阻止，检查阻止原因是否正确
                if not case["expected_valid"] and "expected_reason_contains" in case:
                    assert case["expected_reason_contains"] in reason, \
                        f"阻止原因不正确: 期望包含'{case['expected_reason_contains']}', 实际: {reason}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "boundary_check": boundary_check
                })
                
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "passed": False, 
                    "error": str(e)
                })
        
        self.test_results["capability_boundary_verification"] = results
        logger.info(f"✅ 能力边界验证测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def test_hallucination_detection(self):
        """测试3: 智能体幻觉检测"""
        logger.info("🧪 测试3: 智能体幻觉检测")
        
        test_cases = [
            {
                "name": "设计智能体声称生成testbench (幻觉)",
                "agent_id": "enhanced_real_verilog_agent",
                "result": {
                    "success": True,
                    "generated_files": ["counter.v", "counter_tb.v"],
                    "status": "success"
                },
                "expected_hallucination": True,
                "expected_type": "capability_boundary_hallucination"
            },
            {
                "name": "设计智能体正常完成设计 (无幻觉)",
                "agent_id": "enhanced_real_verilog_agent", 
                "result": {
                    "success": True,
                    "generated_files": ["counter.v"],
                    "status": "success"
                },
                "expected_hallucination": False
            },
            {
                "name": "智能体声称生成不存在的文件 (幻觉)",
                "agent_id": "enhanced_real_code_review_agent",
                "result": {
                    "success": True,
                    "generated_files": ["/nonexistent/path/fake_file.v"],
                    "status": "success"
                },
                "expected_hallucination": True,
                "expected_type": "file_existence_hallucination"
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                hallucination_check = self.coordinator._detect_task_hallucination(
                    case["agent_id"], case["result"]
                )
                
                has_hallucination = hallucination_check.get("has_hallucination", False)
                hallucination_type = hallucination_check.get("hallucination_type", "")
                
                # 验证幻觉检测结果
                assert has_hallucination == case["expected_hallucination"], \
                    f"幻觉检测错误: 期望{case['expected_hallucination']}, 实际{has_hallucination}"
                
                # 如果期望检测到幻觉，验证幻觉类型
                if case["expected_hallucination"] and "expected_type" in case:
                    assert hallucination_type == case["expected_type"], \
                        f"幻觉类型错误: 期望{case['expected_type']}, 实际{hallucination_type}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "hallucination_check": hallucination_check
                })
                
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        self.test_results["hallucination_detection"] = results
        logger.info(f"✅ 幻觉检测测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def test_serial_workflow_management(self):
        """测试4: 串行工作流管理"""
        logger.info("🧪 测试4: 串行工作流管理")
        
        # 创建模拟任务上下文
        task_context = TaskContext(
            task_id="test_workflow_001", 
            original_request="设计counter模块并生成测试台验证功能"
        )
        
        test_cases = [
            {
                "name": "初始阶段 - 应推荐设计任务",
                "agent_results": {},
                "expected_stage": "initial",
                "expected_next_agent": "enhanced_real_verilog_agent"
            },
            {
                "name": "设计完成 - 应推荐审查任务", 
                "agent_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "generated_files": ["counter.v"],
                        "status": "success"
                    }
                },
                "expected_stage": "design_completed",
                "expected_next_agent": "enhanced_real_code_review_agent"
            },
            {
                "name": "两阶段完成 - 应完成工作流",
                "agent_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "generated_files": ["counter.v"],
                        "status": "success"
                    },
                    "enhanced_real_code_review_agent": {
                        "success": True,
                        "generated_files": ["counter_tb.v"],
                        "status": "success"
                    }
                },
                "expected_stage": "verification_completed",
                "expected_workflow_complete": True
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                # 设置任务上下文
                task_context.agent_results = case["agent_results"]
                
                # 模拟复合任务分析
                task_analysis = {
                    "is_composite": True,
                    "subtasks": ["design", "verification"]
                }
                
                # 测试工作流管理
                workflow_result = self.coordinator._manage_serial_workflow(task_context, task_analysis)
                
                # 验证工作流阶段
                current_stage = workflow_result.get("current_stage")
                assert current_stage == case["expected_stage"], \
                    f"工作流阶段错误: 期望{case['expected_stage']}, 实际{current_stage}"
                
                # 验证下一个智能体推荐
                if "expected_next_agent" in case:
                    next_action = workflow_result.get("next_action", {})
                    next_agent = next_action.get("agent_id")
                    assert next_agent == case["expected_next_agent"], \
                        f"下一个智能体推荐错误: 期望{case['expected_next_agent']}, 实际{next_agent}"
                
                # 验证工作流完成状态
                if "expected_workflow_complete" in case:
                    workflow_complete = workflow_result.get("workflow_complete", False)
                    assert workflow_complete == case["expected_workflow_complete"], \
                        f"工作流完成状态错误: 期望{case['expected_workflow_complete']}, 实际{workflow_complete}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "workflow_result": workflow_result
                })
                
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        self.test_results["serial_workflow_management"] = results
        logger.info(f"✅ 串行工作流管理测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def test_quality_gate_mechanism(self):
        """测试5: 质量门控机制"""
        logger.info("🧪 测试5: 质量门控机制")
        
        # 创建临时设计文件用于测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
            f.write(COMPLEX_COUNTER_DESIGN)
            temp_design_file = f.name
        self.temp_files.append(temp_design_file)
        
        # 创建模拟任务上下文
        task_context = TaskContext(
            task_id="test_quality_gate_001",
            original_request="设计counter模块并生成测试台验证功能"
        )
        
        test_cases = [
            {
                "name": "高质量设计阶段 - 应通过质量门控",
                "agent_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "result": {
                            "generated_files": [temp_design_file],
                            "status": "success"
                        },
                        "analysis": {
                            "quality_score": 85.0,
                            "hallucination_detected": False
                        }
                    }
                },
                "expected_design_passed": True
            },
            {
                "name": "低质量设计阶段 - 不应通过质量门控",
                "agent_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "result": {
                            "generated_files": [],
                            "status": "failed"
                        },
                        "analysis": {
                            "quality_score": 30.0,
                            "hallucination_detected": True
                        }
                    }
                },
                "expected_design_passed": False
            },
            {
                "name": "完整工作流 - 两个阶段都通过",
                "agent_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "result": {
                            "generated_files": [temp_design_file],
                            "status": "success"
                        },
                        "analysis": {
                            "quality_score": 85.0,
                            "hallucination_detected": False
                        }
                    },
                    "enhanced_real_code_review_agent": {
                        "success": True,
                        "result": {
                            "generated_files": ["counter_tb.v"],
                            "status": "success",
                            "verification": "completed"
                        },
                        "analysis": {
                            "quality_score": 90.0,
                            "hallucination_detected": False
                        }
                    }
                },
                "expected_design_passed": True,
                "expected_verification_passed": True
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                # 设置任务上下文
                task_context.agent_results = case["agent_results"]
                
                # 测试设计质量门控
                design_quality = self.coordinator._evaluate_design_quality_gate(task_context)
                design_passed = design_quality.get("passed", False)
                
                assert design_passed == case["expected_design_passed"], \
                    f"设计质量门控错误: 期望{case['expected_design_passed']}, 实际{design_passed}"
                
                # 如果有验证阶段，测试验证质量门控
                if "expected_verification_passed" in case:
                    verification_quality = self.coordinator._evaluate_verification_quality_gate(task_context)
                    verification_passed = verification_quality.get("passed", False)
                    
                    assert verification_passed == case["expected_verification_passed"], \
                        f"验证质量门控错误: 期望{case['expected_verification_passed']}, 实际{verification_passed}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "design_quality": design_quality,
                    "verification_quality": verification_quality if "expected_verification_passed" in case else None
                })
                
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        self.test_results["quality_gate_mechanism"] = results
        logger.info(f"✅ 质量门控机制测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def test_task_completion_enforcement(self):
        """测试6: 任务完成强制检查"""
        logger.info("🧪 测试6: 任务完成强制检查")
        
        test_cases = [
            {
                "name": "任务未完成 - 低分数阻止结束",
                "all_results": {
                    "enhanced_real_verilog_agent": {
                        "success": False,
                        "generated_files": []
                    }
                },
                "expected_completion": False,
                "expected_score_range": (0, 30)
            },
            {
                "name": "部分完成 - 中等分数需要继续",
                "all_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "generated_files": ["counter.v"]
                    }
                },
                "expected_completion": False,
                "expected_score_range": (40, 70)
            },
            {
                "name": "完全完成 - 高分数允许结束",
                "all_results": {
                    "enhanced_real_verilog_agent": {
                        "success": True,
                        "generated_files": ["counter.v"]
                    },
                    "enhanced_real_code_review_agent": {
                        "success": True, 
                        "generated_files": ["counter_tb.v"]
                    }
                },
                "expected_completion": True,
                "expected_score_range": (80, 100)
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                # 创建临时任务上下文
                task_id = f"test_completion_{hash(case['name'])}"
                task_context = TaskContext(
                    task_id=task_id,
                    original_request="设计counter模块并生成测试台验证功能"
                )
                task_context.agent_results = case["all_results"]
                self.coordinator.active_tasks[task_id] = task_context
                
                # 调用任务完成检查
                completion_result = await self.coordinator._tool_check_task_completion(
                    task_id=task_id,
                    all_results=case["all_results"], 
                    original_requirements="设计counter模块并生成测试台验证功能"
                )
                
                assert completion_result.get("success", False), \
                    f"任务完成检查失败: {completion_result.get('error')}"
                
                # 验证完成状态
                is_completed = completion_result.get("is_completed", False)
                completion_score = completion_result.get("completion_score", 0)
                
                assert is_completed == case["expected_completion"], \
                    f"完成状态错误: 期望{case['expected_completion']}, 实际{is_completed}"
                
                # 验证分数范围
                min_score, max_score = case["expected_score_range"]
                assert min_score <= completion_score <= max_score, \
                    f"完成分数超出范围: 期望[{min_score}, {max_score}], 实际{completion_score}"
                
                results.append({
                    "case": case["name"],
                    "passed": True,
                    "completion_result": completion_result
                })
                
                # 清理任务上下文
                if task_id in self.coordinator.active_tasks:
                    del self.coordinator.active_tasks[task_id]
                
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        self.test_results["task_completion_enforcement"] = results
        logger.info(f"✅ 任务完成强制检查测试完成: {len([r for r in results if r['passed']])}/{len(results)} 通过")
        return all(r["passed"] for r in results)
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始V-Agent协调器修复功能综合测试")
        
        try:
            await self.setup_coordinator()
            
            tests = [
                ("复合任务识别和分解", self.test_composite_task_detection),
                ("智能体能力边界验证", self.test_capability_boundary_verification), 
                ("智能体幻觉检测", self.test_hallucination_detection),
                ("串行工作流管理", self.test_serial_workflow_management),
                ("质量门控机制", self.test_quality_gate_mechanism),
                ("任务完成强制检查", self.test_task_completion_enforcement)
            ]
            
            test_results = []
            for test_name, test_func in tests:
                logger.info(f"\n{'='*60}")
                logger.info(f"开始测试: {test_name}")
                logger.info(f"{'='*60}")
                
                try:
                    result = await test_func()
                    test_results.append((test_name, result))
                    
                    if result:
                        logger.info(f"✅ {test_name} - 通过")
                    else:
                        logger.error(f"❌ {test_name} - 失败")
                        
                except Exception as e:
                    logger.error(f"❌ {test_name} - 异常: {e}")
                    test_results.append((test_name, False))
            
            # 生成测试报告
            return self.generate_test_report(test_results)
            
        finally:
            self.cleanup_temp_files()
    
    def generate_test_report(self, test_results):
        """生成测试报告"""
        logger.info(f"\n{'='*60}")
        logger.info("V-Agent协调器修复功能测试报告") 
        logger.info(f"{'='*60}")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总计测试: {total}")
        logger.info(f"通过测试: {passed}")
        logger.info(f"失败测试: {total - passed}")
        logger.info(f"通过率: {passed/total*100:.1f}%")
        
        logger.info("\n详细测试结果:")
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{status} - {test_name}")
        
        # 生成详细报告文件
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "pass_rate": passed/total*100,
            "test_results": dict(test_results),
            "detailed_results": self.test_results
        }
        
        report_file = f"coordinator_fixes_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n详细测试报告已保存到: {report_file}")
        
        if passed == total:
            logger.info("\n🎉 所有测试通过！V-Agent协调器修复功能正常运行。")
            return True
        else:
            logger.error(f"\n⚠️ {total - passed} 个测试失败，需要进一步调试。")
            return False

async def main():
    """主函数"""
    tester = CoordinatorFixesTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 V-Agent协调器修复功能测试完成 - 所有功能正常")
        sys.exit(0)
    else:
        print("\n⚠️ V-Agent协调器修复功能测试完成 - 发现问题")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())