"""
V-Agent 协调智能体核心缺陷修复实现

基于 counter_test_utf8-27.txt 分析的核心问题修复
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TaskDecomposition:
    """任务分解结果"""
    design_task: str
    testbench_task: str
    needs_decomposition: bool
    original_task: str

@dataclass
class CompletionStatus:
    """任务完成状态"""
    is_completed: bool
    completion_score: float
    missing_requirements: List[str]
    quality_assessment: str
    detailed_analysis: Dict[str, Any]

class CoordinatorCoreFix:
    """协调智能体核心修复类"""
    
    def __init__(self, logger=None):
        self.logger = logger or self._create_logger()
    
    def _create_logger(self):
        """创建日志记录器"""
        import logging
        logger = logging.getLogger("CoordinatorCoreFix")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def decompose_task(self, task_description: str) -> TaskDecomposition:
        """
        任务分解机制 - 修复1
        
        将包含测试台要求的任务分解为设计任务和测试台任务
        """
        self.logger.info(f"🔍 分析任务是否需要分解: {task_description[:100]}...")
        
        # 检查是否包含测试台要求
        testbench_keywords = [
            "testbench", "测试台", "test bench", "验证", "verification",
            "仿真", "simulation", "测试", "test"
        ]
        
        needs_decomposition = any(keyword in task_description.lower() for keyword in testbench_keywords)
        
        if not needs_decomposition:
            return TaskDecomposition(
                design_task=task_description,
                testbench_task="",
                needs_decomposition=False,
                original_task=task_description
            )
        
        # 分解任务
        design_task = self._extract_design_requirements(task_description)
        testbench_task = self._extract_testbench_requirements(task_description)
        
        self.logger.info(f"✅ 任务分解完成:")
        self.logger.info(f"  设计任务: {design_task[:100]}...")
        self.logger.info(f"  测试台任务: {testbench_task[:100]}...")
        
        return TaskDecomposition(
            design_task=design_task,
            testbench_task=testbench_task,
            needs_decomposition=True,
            original_task=task_description
        )
    
    def _extract_design_requirements(self, task_description: str) -> str:
        """提取设计需求"""
        # 移除测试台相关的要求
        design_keywords = [
            "设计", "design", "模块", "module", "verilog", "hdl",
            "功能", "function", "端口", "port", "参数", "parameter"
        ]
        
        # 保留设计相关的部分
        lines = task_description.split('\n')
        design_lines = []
        
        for line in lines:
            line_lower = line.lower()
            # 如果包含设计关键词且不包含测试台关键词，则保留
            if any(keyword in line_lower for keyword in design_keywords) and \
               not any(keyword in line_lower for keyword in ["testbench", "测试台", "test", "验证"]):
                design_lines.append(line)
        
        design_task = '\n'.join(design_lines) if design_lines else task_description
        
        # 确保包含基本的设计要求
        if "设计" not in design_task and "design" not in design_task.lower():
            design_task = f"设计{design_task}"
        
        return design_task
    
    def _extract_testbench_requirements(self, task_description: str) -> str:
        """提取测试台需求"""
        testbench_keywords = [
            "testbench", "测试台", "test bench", "验证", "verification",
            "仿真", "simulation", "测试", "test"
        ]
        
        lines = task_description.split('\n')
        testbench_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in testbench_keywords):
                testbench_lines.append(line)
        
        testbench_task = '\n'.join(testbench_lines) if testbench_lines else "生成对应的测试台进行验证"
        
        return testbench_task
    
    def validate_agent_capabilities(self, agent_id: str, task_description: str) -> Dict[str, Any]:
        """
        智能体能力边界验证 - 修复3
        
        验证任务是否超出智能体的能力范围
        """
        self.logger.info(f"🔍 验证智能体 {agent_id} 的能力边界")
        
        # 设计智能体的能力边界
        if agent_id == "enhanced_real_verilog_agent":
            testbench_keywords = ["testbench", "测试台", "test bench", "验证", "verification"]
            
            if any(keyword in task_description.lower() for keyword in testbench_keywords):
                return {
                    "valid": False,
                    "error": "设计智能体不支持测试台生成",
                    "suggested_agent": "enhanced_real_code_review_agent",
                    "task_decomposition_needed": True,
                    "violation_type": "capability_boundary"
                }
        
        # 审查智能体的能力边界
        elif agent_id == "enhanced_real_code_review_agent":
            design_keywords = ["设计", "design", "模块", "module"]
            
            if any(keyword in task_description.lower() for keyword in design_keywords) and \
               "testbench" not in task_description.lower() and "测试台" not in task_description:
                return {
                    "valid": False,
                    "error": "审查智能体主要负责测试台生成和代码审查",
                    "suggested_agent": "enhanced_real_verilog_agent",
                    "task_decomposition_needed": False,
                    "violation_type": "capability_boundary"
                }
        
        return {
            "valid": True,
            "error": None,
            "suggested_agent": None,
            "task_decomposition_needed": False,
            "violation_type": None
        }
    
    def detect_task_hallucination(self, agent_result: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        任务幻觉检测机制 - 修复4
        
        检测智能体是否产生了任务幻觉
        """
        self.logger.info(f"🔍 检测智能体 {agent_id} 的任务幻觉")
        
        hallucination_indicators = {
            "file_claims": [],
            "capability_violations": [],
            "inconsistencies": [],
            "false_assertions": []
        }
        
        # 检查声称生成的文件是否真实存在
        claimed_files = agent_result.get("generated_files", [])
        for file_path in claimed_files:
            if isinstance(file_path, str) and not os.path.exists(file_path):
                hallucination_indicators["file_claims"].append(file_path)
                self.logger.warning(f"⚠️ 声称生成的文件不存在: {file_path}")
        
        # 检查是否违反了能力边界
        if agent_id == "enhanced_real_verilog_agent":
            result_content = str(agent_result.get("result", ""))
            
            # 检查是否声称生成了测试台
            if "testbench" in result_content.lower() or "测试台" in result_content:
                # 检查是否真的包含测试台代码
                if "module" not in result_content.lower() or "endmodule" not in result_content.lower():
                    hallucination_indicators["capability_violations"].append("声称生成测试台但实际没有")
                    self.logger.warning(f"⚠️ 设计智能体声称生成测试台但实际没有")
        
        # 检查结果内容的一致性
        result_content = str(agent_result.get("result", ""))
        if "成功生成" in result_content or "successfully generated" in result_content.lower():
            # 检查是否有实际的文件生成证据
            if not claimed_files and not result_content.strip():
                hallucination_indicators["false_assertions"].append("声称成功但没有实际输出")
                self.logger.warning(f"⚠️ 声称成功但没有实际输出")
        
        has_hallucination = any(len(indicators) > 0 for indicators in hallucination_indicators.values())
        
        return {
            "has_hallucination": has_hallucination,
            "indicators": hallucination_indicators,
            "confidence": self._calculate_hallucination_confidence(hallucination_indicators)
        }
    
    def _calculate_hallucination_confidence(self, indicators: Dict[str, List[str]]) -> float:
        """计算幻觉检测的置信度"""
        total_indicators = sum(len(indicators[key]) for key in indicators)
        
        if total_indicators == 0:
            return 0.0
        
        # 不同指标类型的权重
        weights = {
            "file_claims": 0.4,  # 文件声称不存在权重最高
            "capability_violations": 0.3,  # 能力边界违反
            "inconsistencies": 0.2,  # 内容不一致
            "false_assertions": 0.1  # 虚假声明
        }
        
        weighted_score = sum(
            len(indicators[key]) * weights.get(key, 0.1)
            for key in indicators
        )
        
        # 归一化到0-1范围
        return min(weighted_score / 2.0, 1.0)
    
    def force_task_completion_check(self, all_results: Dict[str, Any], 
                                  original_requirements: str) -> CompletionStatus:
        """
        强制任务完成检查 - 修复2
        
        强制检查任务是否真正完成，不允许忽略
        """
        self.logger.info(f"🔍 强制检查任务完成状态")
        
        # 分析原始需求
        requirements = original_requirements.lower()
        
        # 检查各项完成指标
        completion_metrics = self._analyze_completion_metrics(all_results, requirements)
        
        # 计算完成分数
        completion_score = self._calculate_completion_score(completion_metrics)
        
        # 识别缺失项
        missing_requirements = self._identify_missing_requirements(completion_metrics, requirements)
        
        # 判断是否完成
        is_completed = self._determine_completion_status(completion_score, missing_requirements)
        
        # 质量评估
        quality_assessment = self._assess_overall_quality(completion_metrics, completion_score)
        
        self.logger.info(f"📊 任务完成检查结果:")
        self.logger.info(f"  完成状态: {'✅ 完成' if is_completed else '❌ 未完成'}")
        self.logger.info(f"  完成分数: {completion_score:.1f}/100")
        self.logger.info(f"  缺失项: {missing_requirements}")
        self.logger.info(f"  质量评估: {quality_assessment}")
        
        return CompletionStatus(
            is_completed=is_completed,
            completion_score=completion_score,
            missing_requirements=missing_requirements,
            quality_assessment=quality_assessment,
            detailed_analysis=completion_metrics
        )
    
    def _analyze_completion_metrics(self, all_results: Dict[str, Any], requirements: str) -> Dict[str, Any]:
        """分析完成指标"""
        metrics = {
            "design_complete": False,
            "verification_complete": False,
            "documentation_complete": False,
            "testing_complete": False,
            "quality_checks_passed": False,
            "agent_performance": {},
            "execution_time": 0.0,
            "total_iterations": 0
        }
        
        # 检查设计完成情况
        if "design" in requirements or "模块" in requirements or "设计" in requirements:
            design_results = []
            for agent_id, result in all_results.items():
                if agent_id == "enhanced_real_verilog_agent":
                    design_results.append(result)
            
            if design_results:
                for result in design_results:
                    if isinstance(result, dict) and result.get("success", False):
                        # 检查是否生成了Verilog文件
                        generated_files = result.get("generated_files", [])
                        if any(".v" in file for file in generated_files):
                            metrics["design_complete"] = True
                            break
                        # 检查结果内容是否包含模块定义
                        result_content = str(result.get("result", ""))
                        if "module" in result_content.lower() and "endmodule" in result_content.lower():
                            metrics["design_complete"] = True
                            break
        
        # 检查验证完成情况
        if "test" in requirements or "验证" in requirements or "testbench" in requirements:
            verification_results = []
            for agent_id, result in all_results.items():
                if agent_id == "enhanced_real_code_review_agent":
                    verification_results.append(result)
            
            if verification_results:
                for result in verification_results:
                    if isinstance(result, dict) and result.get("success", False):
                        # 检查是否生成了测试台文件
                        generated_files = result.get("generated_files", [])
                        if any("tb" in file.lower() or "testbench" in file.lower() for file in generated_files):
                            metrics["verification_complete"] = True
                            break
                        # 检查结果内容是否包含测试台
                        result_content = str(result.get("result", ""))
                        if "testbench" in result_content.lower() or "simulation" in result_content.lower():
                            metrics["verification_complete"] = True
                            break
        
        return metrics
    
    def _calculate_completion_score(self, metrics: Dict[str, Any]) -> float:
        """计算完成分数"""
        score = 0.0
        
        # 权重配置
        weights = {
            "design_complete": 0.4,
            "verification_complete": 0.4,
            "documentation_complete": 0.1,
            "testing_complete": 0.05,
            "quality_checks_passed": 0.05
        }
        
        for metric, weight in weights.items():
            if metrics.get(metric, False):
                score += weight * 100
        
        return score
    
    def _identify_missing_requirements(self, metrics: Dict[str, Any], requirements: str) -> List[str]:
        """识别缺失的需求"""
        missing_items = []
        
        if "设计" in requirements or "design" in requirements:
            if not metrics.get("design_complete", False):
                missing_items.append("缺少Verilog模块设计")
        
        if "测试台" in requirements or "testbench" in requirements or "验证" in requirements:
            if not metrics.get("verification_complete", False):
                missing_items.append("缺少测试台和验证")
        
        if "文档" in requirements or "documentation" in requirements:
            if not metrics.get("documentation_complete", False):
                missing_items.append("缺少文档")
        
        if "测试" in requirements or "test" in requirements:
            if not metrics.get("testing_complete", False):
                missing_items.append("缺少测试")
        
        return missing_items
    
    def _determine_completion_status(self, completion_score: float, missing_requirements: List[str]) -> bool:
        """判断完成状态"""
        # 如果完成分数低于80分，认为未完成
        if completion_score < 80.0:
            return False
        
        # 如果有关键缺失项，认为未完成
        critical_missing = ["缺少Verilog模块设计", "缺少测试台和验证"]
        if any(item in missing_requirements for item in critical_missing):
            return False
        
        return True
    
    def _assess_overall_quality(self, metrics: Dict[str, Any], completion_score: float) -> str:
        """评估整体质量"""
        if completion_score >= 90:
            return "优秀"
        elif completion_score >= 80:
            return "良好"
        elif completion_score >= 60:
            return "一般"
        else:
            return "较差"
    
    def optimize_coordination_loop(self, task_context: Dict[str, Any], 
                                 max_coordination_attempts: int = 5) -> Dict[str, Any]:
        """
        协调循环终止条件优化 - 修复5
        
        基于任务完成状态的智能终止
        """
        self.logger.info(f"🔄 优化协调循环，最大尝试次数: {max_coordination_attempts}")
        
        coordination_attempts = 0
        
        while coordination_attempts < max_coordination_attempts:
            coordination_attempts += 1
            self.logger.info(f"🔄 协调尝试 {coordination_attempts}/{max_coordination_attempts}")
            
            # 强制检查任务完成状态
            completion_status = self.force_task_completion_check(
                task_context.get("agent_results", {}),
                task_context.get("original_request", "")
            )
            
            if completion_status.is_completed:
                self.logger.info("✅ 任务真正完成，结束协调循环")
                return {
                    "success": True,
                    "completion_status": "completed",
                    "completion_score": completion_status.completion_score,
                    "coordination_attempts": coordination_attempts
                }
            
            # 如果未完成，记录缺失项并继续
            self.logger.warning(f"⚠️ 任务未完成，缺失项: {completion_status.missing_requirements}")
            
            # 这里应该触发新的任务分配逻辑
            # 为了简化，我们只记录状态
        
        # 达到最大协调尝试次数
        self.logger.warning(f"⏰ 达到最大协调尝试次数: {max_coordination_attempts}")
        return {
            "success": False,
            "error": "达到最大协调尝试次数，任务部分完成",
            "completion_status": "partial",
            "missing_requirements": completion_status.missing_requirements,
            "completion_score": completion_status.completion_score,
            "coordination_attempts": coordination_attempts
        }

# 使用示例
def demonstrate_fixes():
    """演示修复效果"""
    fix = CoordinatorCoreFix()
    
    # 测试任务分解
    task = "设计一个名为counter的Verilog模块，生成完整、可编译的Verilog代码，包含适当的端口定义和功能实现，符合Verilog标准语法，并生成对应的测试台进行验证。"
    
    print("=== 修复1：任务分解机制 ===")
    decomposition = fix.decompose_task(task)
    print(f"需要分解: {decomposition.needs_decomposition}")
    print(f"设计任务: {decomposition.design_task}")
    print(f"测试台任务: {decomposition.testbench_task}")
    
    # 测试能力边界验证
    print("\n=== 修复3：智能体能力边界验证 ===")
    validation = fix.validate_agent_capabilities("enhanced_real_verilog_agent", task)
    print(f"验证结果: {validation}")
    
    # 测试任务幻觉检测
    print("\n=== 修复4：任务幻觉检测机制 ===")
    fake_result = {
        "success": True,
        "generated_files": ["counter.v", "counter_tb.v"],  # 第二个文件不存在
        "result": "成功生成了Verilog模块和测试台"
    }
    hallucination = fix.detect_task_hallucination(fake_result, "enhanced_real_verilog_agent")
    print(f"幻觉检测结果: {hallucination}")
    
    # 测试强制任务完成检查
    print("\n=== 修复2：强制任务完成检查 ===")
    incomplete_results = {
        "enhanced_real_verilog_agent": {
            "success": True,
            "generated_files": ["counter.v"]
        }
        # 缺少测试台结果
    }
    completion = fix.force_task_completion_check(incomplete_results, task)
    print(f"完成状态: {completion.is_completed}")
    print(f"完成分数: {completion.completion_score}")
    print(f"缺失项: {completion.missing_requirements}")

if __name__ == "__main__":
    demonstrate_fixes() 