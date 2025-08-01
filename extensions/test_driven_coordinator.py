#!/usr/bin/env python3
"""
测试驱动协调器 - 完全独立的扩展功能

这是一个完全独立的扩展模块，不修改任何现有代码
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 导入现有框架组件 - 只读取，不修改
from core.centralized_coordinator import CentralizedCoordinator
from core.enums import AgentCapability, AgentStatus
from config.config import FrameworkConfig


@dataclass
class TestDrivenConfig:
    """测试驱动配置"""
    max_iterations: int = 5
    enable_deep_analysis: bool = True
    auto_fix_suggestions: bool = True
    save_iteration_logs: bool = True
    timeout_per_iteration: int = 300  # 5分钟


class TestDrivenCoordinator:
    """
    测试驱动协调器 - 扩展功能
    
    这是一个装饰器模式的实现，包装现有的CentralizedCoordinator
    而不是继承或修改它
    """
    
    def __init__(self, base_coordinator: CentralizedCoordinator, 
                 config: TestDrivenConfig = None):
        """
        初始化测试驱动协调器
        
        Args:
            base_coordinator: 现有的协调器实例（不会被修改）
            config: 测试驱动配置
        """
        self.base_coordinator = base_coordinator
        self.config = config or TestDrivenConfig()
        self.logger = logging.getLogger(f"{__name__}.TestDrivenCoordinator")
        
        # 扩展功能状态
        self.test_driven_sessions = {}
        self.iteration_history = {}
        
        # 导入扩展解析器
        from .enhanced_task_parser import EnhancedTaskParser
        from .test_analyzer import TestAnalyzer
        
        self.task_parser = EnhancedTaskParser()
        self.test_analyzer = TestAnalyzer()
        
        self.logger.info("🧪 测试驱动协调器扩展已初始化")
    
    # ==========================================
    # 🎯 新增的测试驱动功能（完全独立）
    # ==========================================
    
    async def execute_test_driven_task(self, task_description: str,
                                     testbench_path: str = None,
                                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行测试驱动任务 - 新增功能入口
        
        这是完全新的功能，不会影响现有的coordinate_task_execution
        """
        session_id = f"tdd_{int(time.time())}"
        self.logger.info(f"🚀 开始测试驱动任务: {session_id}")
        
        try:
            # 1. 解析增强任务需求
            enhanced_analysis = await self._parse_test_driven_requirements(
                task_description, testbench_path, context
            )
            
            if not enhanced_analysis["is_test_driven"]:
                # 如果不是测试驱动任务，回退到标准流程
                self.logger.info("📋 非测试驱动任务，使用标准流程")
                return await self.base_coordinator.coordinate_task_execution(
                    task_description, context
                )
            
            # 2. 验证测试台（如果提供）
            if enhanced_analysis.get("testbench_path"):
                validation = await self._validate_testbench(
                    enhanced_analysis["testbench_path"]
                )
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": f"测试台验证失败: {validation['error']}",
                        "session_id": session_id
                    }
                enhanced_analysis["testbench_validation"] = validation
            
            # 3. 执行测试驱动循环
            result = await self._execute_tdd_loop(session_id, enhanced_analysis)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 测试驱动任务执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "fallback_suggested": True
            }
    
    async def _parse_test_driven_requirements(self, task_description: str,
                                            testbench_path: str = None,
                                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """解析测试驱动需求"""
        return await self.task_parser.parse_enhanced_task(
            task_description, testbench_path, context
        )
    
    async def _validate_testbench(self, testbench_path: str) -> Dict[str, Any]:
        """验证测试台文件"""
        return await self.test_analyzer.validate_testbench_file(testbench_path)
    
    async def _execute_tdd_loop(self, session_id: str, 
                              enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试驱动开发循环"""
        self.test_driven_sessions[session_id] = {
            "start_time": time.time(),
            "analysis": enhanced_analysis,
            "iterations": [],
            "status": "running"
        }
        
        max_iterations = self.config.max_iterations
        current_iteration = 0
        final_result = None
        
        self.logger.info(f"🔄 开始TDD循环，最大迭代次数: {max_iterations}")
        
        while current_iteration < max_iterations:
            current_iteration += 1
            iteration_start = time.time()
            
            self.logger.info(f"🔄 第 {current_iteration}/{max_iterations} 次迭代")
            
            # 执行单次迭代
            iteration_result = await self._execute_single_tdd_iteration(
                session_id, current_iteration, enhanced_analysis
            )
            
            # 记录迭代结果
            self.test_driven_sessions[session_id]["iterations"].append({
                "iteration": current_iteration,
                "start_time": iteration_start,
                "duration": time.time() - iteration_start,
                "result": iteration_result
            })
            
            # 检查是否成功
            if iteration_result.get("all_tests_passed", False):
                self.logger.info(f"✅ 第 {current_iteration} 次迭代成功！")
                final_result = {
                    "success": True,
                    "session_id": session_id,
                    "total_iterations": current_iteration,
                    "final_design": iteration_result.get("design_files", []),
                    "test_results": iteration_result.get("test_results", {}),
                    "completion_reason": "tests_passed"
                }
                break
            
            # 如果不是最后一次迭代，准备改进建议
            if current_iteration < max_iterations:
                improvement_analysis = await self._analyze_for_improvement(
                    iteration_result, enhanced_analysis
                )
                enhanced_analysis["improvement_suggestions"] = improvement_analysis.get("suggestions", [])
        
        # 如果循环结束仍未成功
        if final_result is None:
            self.logger.warning(f"⚠️ 达到最大迭代次数 {max_iterations}")
            
            # 从最后一次迭代中获取设计文件
            last_iteration = self.test_driven_sessions[session_id]["iterations"][-1] if self.test_driven_sessions[session_id]["iterations"] else {}
            final_design_files = last_iteration.get("result", {}).get("design_files", [])
            
            final_result = {
                "success": False,
                "session_id": session_id,
                "total_iterations": max_iterations,
                "final_design": final_design_files,
                "completion_reason": "max_iterations_reached",
                "error": "达到最大迭代次数，但测试仍未全部通过",
                "partial_results": self.test_driven_sessions[session_id]["iterations"]
            }
        
        # 更新会话状态
        self.test_driven_sessions[session_id]["status"] = "completed"
        self.test_driven_sessions[session_id]["final_result"] = final_result
        
        return final_result
    
    async def _execute_single_tdd_iteration(self, session_id: str, iteration: int,
                                          enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行单次TDD迭代"""
        self.logger.info(f"🎯 执行第 {iteration} 次迭代")
        
        try:
            # 阶段1: 设计生成/修改
            design_result = await self._execute_design_phase(
                session_id, iteration, enhanced_analysis
            )
            
            if not design_result.get("success", False):
                return {
                    "success": False,
                    "phase": "design",
                    "error": design_result.get("error", "设计阶段失败"),
                    "all_tests_passed": False
                }
            
            # 阶段2: 测试执行
            test_result = await self._execute_test_phase(
                session_id, iteration, design_result, enhanced_analysis
            )
            
            # 从设计结果中提取文件引用
            design_files = design_result.get("file_references", design_result.get("design_files", []))
            
            # 合并结果
            return {
                "success": True,
                "design_files": design_files,
                "test_results": test_result,
                "all_tests_passed": test_result.get("all_tests_passed", False),
                "iteration": iteration
            }
            
        except Exception as e:
            self.logger.error(f"❌ 第 {iteration} 次迭代异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "all_tests_passed": False,
                "iteration": iteration
            }
    
    async def _execute_design_phase(self, session_id: str, iteration: int,
                                  enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行设计阶段 - 使用现有协调器功能"""
        self.logger.info(f"🎨 设计阶段 - 迭代 {iteration}")
        
        # 构建设计任务
        design_task = self._build_design_task(enhanced_analysis, iteration)
        
        # 使用现有协调器执行设计任务（不修改现有功能）
        result = await self.base_coordinator.coordinate_task_execution(
            design_task, enhanced_analysis.get("context", {})
        )
        
        return result
    
    async def _execute_test_phase(self, session_id: str, iteration: int,
                                design_result: Dict[str, Any],
                                enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试阶段"""
        self.logger.info(f"🧪 测试阶段 - 迭代 {iteration}")
        
        # 如果有用户指定的测试台，使用扩展测试功能
        if enhanced_analysis.get("testbench_path"):
            # 提取设计文件引用
            design_files = design_result.get("file_references", design_result.get("design_files", []))
            
            return await self.test_analyzer.run_with_user_testbench(
                design_files,
                enhanced_analysis["testbench_path"]
            )
        else:
            # 使用标准测试流程
            test_task = self._build_test_task(design_result, enhanced_analysis)
            result = await self.base_coordinator.coordinate_task_execution(
                test_task, enhanced_analysis.get("context", {})
            )
            return result
    
    async def _analyze_for_improvement(self, iteration_result: Dict[str, Any],
                                     enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析并生成改进建议"""
        return await self.test_analyzer.analyze_test_failures(
            iteration_result.get("test_results", {}),
            enhanced_analysis
        )
    
    def _build_design_task(self, enhanced_analysis: Dict[str, Any], iteration: int) -> str:
        """构建设计任务描述"""
        base_requirements = enhanced_analysis.get("design_requirements", "")
        
        task = f"设计任务 (迭代 {iteration}):\n\n{base_requirements}\n\n"
        
        if iteration > 1:
            suggestions = enhanced_analysis.get("improvement_suggestions", [])
            if suggestions:
                task += "改进建议:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    task += f"{i}. {suggestion}\n"
        
        return task
    
    def _build_test_task(self, design_result: Dict[str, Any],
                        enhanced_analysis: Dict[str, Any]) -> str:
        """构建测试任务描述"""
        design_files = design_result.get("design_files", [])
        testbench_path = enhanced_analysis.get("testbench_path")
        
        task = "测试验证任务:\n\n"
        task += f"设计文件: {[f.get('file_path', str(f)) for f in design_files]}\n"
        
        if testbench_path:
            task += f"使用指定测试台: {testbench_path}\n"
        else:
            task += "生成适当的测试台并进行验证\n"
        
        task += "\n请运行测试并报告结果。"
        
        return task
    
    # ==========================================
    # 🔍 会话管理和查询功能
    # ==========================================
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取测试驱动会话信息"""
        return self.test_driven_sessions.get(session_id)
    
    def list_active_sessions(self) -> List[str]:
        """列出活跃的测试驱动会话"""
        return [sid for sid, info in self.test_driven_sessions.items() 
                if info.get("status") == "running"]
    
    def get_iteration_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取迭代历史"""
        session = self.test_driven_sessions.get(session_id)
        return session.get("iterations", []) if session else []
    
    # ==========================================
    # 🎭 代理方法 - 保持与现有协调器的完全兼容
    # ==========================================
    
    async def coordinate_task_execution(self, initial_task: str,
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        代理原有的coordinate_task_execution方法
        
        保持完全向后兼容，现有代码无需任何修改
        """
        return await self.base_coordinator.coordinate_task_execution(initial_task, context)
    
    def register_agent(self, agent):
        """代理智能体注册"""
        return self.base_coordinator.register_agent(agent)
    
    def get_registered_agents(self):
        """代理获取已注册智能体"""
        return self.base_coordinator.get_registered_agents()
    
    # 可以根据需要添加更多代理方法...


# ==========================================
# 🏭 工厂函数 - 便于集成
# ==========================================

def create_test_driven_coordinator(base_coordinator: CentralizedCoordinator,
                                 config: TestDrivenConfig = None) -> TestDrivenCoordinator:
    """
    创建测试驱动协调器的工厂函数
    
    Usage:
        # 现有代码
        coordinator = CentralizedCoordinator(config)
        
        # 升级为测试驱动功能（可选）
        enhanced_coordinator = create_test_driven_coordinator(coordinator)
        
        # 现有功能完全不变
        result = await enhanced_coordinator.coordinate_task_execution(task)
        
        # 新增测试驱动功能
        tdd_result = await enhanced_coordinator.execute_test_driven_task(task, testbench_path)
    """
    return TestDrivenCoordinator(base_coordinator, config)