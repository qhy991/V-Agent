#!/usr/bin/env python3
"""
测试驱动协调器 - 完全独立的扩展功能

这是一个完全独立的扩展模块，不修改任何现有代码
"""

import asyncio
import json
import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 导入现有框架组件 - 只读取，不修改
from core.centralized_coordinator import CentralizedCoordinator
from core.enums import AgentCapability, AgentStatus
from config.config import FrameworkConfig
from core.context_manager import get_context_manager, FullContextManager
from core.base_agent import TaskMessage


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
        
        # 🔗 持续对话机制：每个TDD会话使用同一个对话ID
        self.persistent_conversation_id = None
        self.current_session_agents = {}  # 记录每个会话中使用的智能体
        
        # 🧠 完整上下文管理器
        self.context_manager: Optional[FullContextManager] = None
        
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
        
        # 🧠 初始化完整上下文管理器
        self.context_manager = get_context_manager(session_id)
        self.context_manager.global_context.update({
            "task_description": task_description,
            "testbench_path": testbench_path,
            "design_requirements": task_description
        })
        
        try:
            # 1. 解析增强任务需求（强制作为TDD任务）
            enhanced_analysis = await self._parse_test_driven_requirements(
                task_description, testbench_path, context, force_tdd=True
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
                                            context: Dict[str, Any] = None,
                                            force_tdd: bool = False) -> Dict[str, Any]:
        """解析测试驱动需求"""
        return await self.task_parser.parse_enhanced_task(
            task_description, testbench_path, context, force_tdd
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
            
            # 🧠 开始新的迭代，初始化上下文
            if self.context_manager:
                iteration_id = self.context_manager.start_new_iteration(current_iteration)
                self.logger.info(f"🧠 初始化迭代上下文: {iteration_id}")
            
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
            
            # 🎯 新增：从每次迭代中提取经验教训（无论成功还是失败）
            if self.context_manager:
                # 从编译错误中学习
                test_results = iteration_result.get("test_results", {})
                if test_results.get("compile_stderr"):
                    # 解析编译错误并提取教训
                    compilation_errors = self._parse_compilation_errors(test_results["compile_stderr"])
                    self.context_manager.add_compilation_errors(compilation_errors)
                    self.logger.info(f"🎯 从迭代{current_iteration}提取了{len(compilation_errors)}个编译错误教训")
                
                # 如果成功，提取成功模式
                if iteration_result.get("all_tests_passed", False):
                    self.context_manager.extract_success_patterns(iteration_result)
                    self.logger.info(f"🎯 从迭代{current_iteration}提取了成功模式")
            
            # 检查是否成功
            if iteration_result.get("all_tests_passed", False):
                self.logger.info(f"✅ 第 {current_iteration} 次迭代成功！")
                
                # 🎯 新增：提取成功经验
                if self.context_manager:
                    self.context_manager.extract_success_patterns(iteration_result)
                    self.logger.info("🎯 成功经验已提取并累积")
                
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
                
                # 保存具体的错误信息以传递给下次迭代
                test_results = iteration_result.get("test_results", {})
                if not test_results.get("all_tests_passed", False):
                    # 🔍 调试日志：分析测试结果内容
                    self.logger.info(f"🔍 DEBUG: 测试失败，分析错误信息传递")
                    self.logger.info(f"🔍 test_results keys: {list(test_results.keys())}")
                    
                    # 保存编译错误信息
                    if "compile_stderr" in test_results:
                        stderr_content = test_results["compile_stderr"]
                        enhanced_analysis["last_compilation_errors"] = stderr_content
                        self.logger.info(f"🔍 DEBUG: 保存编译错误信息: {stderr_content[:200]}...")
                        
                        # 🧠 解析并保存编译错误到上下文管理器
                        if self.context_manager:
                            compilation_errors = self._parse_compilation_errors(stderr_content)
                            self.context_manager.add_compilation_errors(compilation_errors)
                            self.logger.info(f"🧠 上下文管理器: 保存了{len(compilation_errors)}个编译错误")
                    
                    # 保存失败原因
                    if "failure_reasons" in test_results:
                        failure_reasons = test_results["failure_reasons"]
                        enhanced_analysis["last_failure_reasons"] = failure_reasons
                        self.logger.info(f"🔍 DEBUG: 保存失败原因: {failure_reasons}")
                    
                    # 保存错误类别
                    if "error_category" in test_results:
                        error_category = test_results["error_category"]
                        enhanced_analysis["last_error_category"] = error_category
                        self.logger.info(f"🔍 DEBUG: 保存错误类别: {error_category}")
                    
                    # 🧠 保存测试结果到上下文管理器
                    if self.context_manager and self.context_manager.current_iteration:
                        self.context_manager.current_iteration.simulation_results = test_results
                        self.context_manager.current_iteration.compilation_success = test_results.get("compile_success", False)
                        self.context_manager.current_iteration.simulation_success = test_results.get("simulation_success", False)
                        self.context_manager.current_iteration.all_tests_passed = test_results.get("all_tests_passed", False)
                    
                    # 🔍 调试：检查improved_analysis内容
                    self.logger.info(f"🔍 DEBUG: improvement_analysis keys: {list(improvement_analysis.keys())}")
                    if "suggestions" in improvement_analysis:
                        self.logger.info(f"🔍 DEBUG: 改进建议数量: {len(improvement_analysis['suggestions'])}")
                        for i, suggestion in enumerate(improvement_analysis["suggestions"][:3]):
                            self.logger.info(f"🔍 DEBUG: 建议{i+1}: {suggestion[:100]}...")
        
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
        
        # 🧠 保存完整上下文到文件
        if self.context_manager:
            context_file_path = f"tdd_context_{session_id}.json"
            try:
                self.context_manager.save_to_file(context_file_path)
                self.logger.info(f"🧠 保存完整上下文到: {context_file_path}")
                
                # 将上下文文件路径添加到最终结果中
                final_result["context_file"] = context_file_path
            except Exception as e:
                self.logger.error(f"❌ 保存上下文文件失败: {str(e)}")
        
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
            
            # 从设计结果中提取文件引用（增强版）
            design_files = self._extract_file_references(design_result)
            
            # 阶段2: 测试执行
            test_result = await self._execute_test_phase(
                session_id, iteration, design_result, enhanced_analysis, design_files
            )
            
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
        design_task = await self._build_design_task(enhanced_analysis, iteration)
        
        # 🔧 修复：在TDD场景中，强制指定这是设计任务，避免被误判为review任务
        tdd_context = enhanced_analysis.get("context", {}).copy()
        tdd_context["force_task_type"] = "design"  # 强制指定为设计任务
        tdd_context["preferred_agent_role"] = "verilog_designer"  # 优先选择Verilog设计智能体
        
        # 🔍 调试日志：记录强制任务类型
        self.logger.info(f"🔧 DEBUG: TDD设计阶段 - 强制任务类型为design，优先agent: verilog_designer")
        
        # 🔗 使用持续对话机制
        if iteration == 1:
            # 第一次迭代：创建新的持续对话
            self.persistent_conversation_id = f"tdd_{session_id}_{int(time.time())}"
            self.logger.info(f"🔗 创建持续对话ID: {self.persistent_conversation_id}")
            
            # 使用现有协调器执行设计任务
            result = await self.base_coordinator.coordinate_task_execution(
                design_task, tdd_context
            )
            
            # 记录本次会话使用的智能体，用于后续迭代
            if result.get("success", False):
                # 从协调器获取选择的智能体信息
                if hasattr(self.base_coordinator, 'current_conversation_participants'):
                    participants = self.base_coordinator.current_conversation_participants
                    self.current_session_agents = {
                        'verilog_designer': participants.get('primary_agent_id', 'enhanced_real_verilog_agent')
                    }
                    self.logger.info(f"🔗 记录会话智能体: {self.current_session_agents}")
                else:
                    # 默认使用verilog设计智能体
                    self.current_session_agents = {
                        'verilog_designer': 'enhanced_real_verilog_agent'
                    }
        else:
            # 后续迭代：继续现有对话
            self.logger.info(f"🔗 继续持续对话: {self.persistent_conversation_id}")
            
            # 直接向已选择的智能体发送任务，而不是重新选择
            result = await self._continue_persistent_conversation(
                design_task, tdd_context, iteration
            )
        
        return result
    
    async def _execute_test_phase(self, session_id: str, iteration: int,
                                design_result: Dict[str, Any],
                                enhanced_analysis: Dict[str, Any],
                                design_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行测试阶段 - 增强版：使用完整上下文管理器"""
        self.logger.info(f"🧪 测试阶段 - 迭代 {iteration}")
        
        # 智能选择测试执行方式
        user_testbench_path = enhanced_analysis.get("testbench_path")
        
        # 从当前迭代的文件中查找生成的测试台
        current_iteration_testbench = None
        if design_files:
            for file_ref in design_files:
                if (isinstance(file_ref, dict) and 
                    file_ref.get("file_type") == "testbench" and 
                    file_ref.get("file_path")):
                    current_iteration_testbench = file_ref["file_path"]
                    self.logger.info(f"🎯 找到当前迭代测试台: {current_iteration_testbench}")
                    break
        
        # 统一的智能testbench选择策略
        testbench_strategy = self._determine_testbench_strategy(
            iteration, user_testbench_path, current_iteration_testbench
        )
        
        testbench_to_use = testbench_strategy["selected_testbench"]
        self.logger.info(f"🎯 第{iteration}次迭代，testbench策略: {testbench_strategy['strategy']}")
        self.logger.info(f"📝 策略说明: {testbench_strategy['reason']}")
        
        if testbench_to_use:
            # 使用指定的测试台（用户指定或当前迭代生成）
            self.logger.info(f"🧪 使用测试台文件: {testbench_to_use}")
            
            # 严格准备设计文件列表（排除测试台文件，确保文件存在）
            design_only_files = []
            if design_files is None:
                design_files = design_result.get("file_references", design_result.get("design_files", []))
            
            self.logger.info(f"🔍 准备设计文件，输入文件总数: {len(design_files) if design_files else 0}")
            
            for i, file_ref in enumerate(design_files):
                if isinstance(file_ref, dict):
                    file_path = file_ref.get("file_path")
                    file_type = file_ref.get("file_type")
                    filename = Path(file_path).name if file_path else "unknown"
                    
                    self.logger.info(f"  文件{i+1}: {filename} (类型: {file_type}, 路径: {file_path})")
                    
                    # 验证是设计文件（非测试台）且文件存在
                    if (file_type == "verilog" and 
                        file_path and 
                        Path(file_path).exists() and
                        not any(keyword in filename.lower() for keyword in ['_tb.v', 'testbench', '_test'])):
                        
                        design_only_files.append(file_ref)
                        self.logger.info(f"  ✅ 选择设计文件: {filename}")
                        
                        # 🧠 将设计文件添加到上下文管理器
                        if self.context_manager:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    module_name = self._extract_module_name(content)
                                    self.context_manager.add_code_file(
                                        file_path=file_path,
                                        content=content,
                                        module_name=module_name or "unknown",
                                        file_type="design"
                                    )
                                    self.logger.info(f"🧠 上下文管理器: 添加设计文件 {file_path} (模块: {module_name})")
                            except Exception as e:
                                self.logger.error(f"❌ 读取设计文件失败 {file_path}: {str(e)}")
                    else:
                        reason = "未知原因"
                        if file_type != "verilog":
                            reason = f"文件类型不是verilog ({file_type})"
                        elif not file_path:
                            reason = "文件路径为空"
                        elif not Path(file_path).exists():
                            reason = "文件不存在"
                        elif any(keyword in filename.lower() for keyword in ['_tb.v', 'testbench', '_test']):
                            reason = "是测试台文件"
                        self.logger.info(f"  ⏭️ 跳过文件: {filename} ({reason})")
            
            self.logger.info(f"🎯 最终选择的设计文件数量: {len(design_only_files)}")
            
            # 🧠 为测试分析器传递完整上下文
            if self.context_manager:
                test_context = self.context_manager.get_full_context_for_agent(
                    "code_reviewer", 
                    "测试验证任务"
                )
                self.logger.info(f"🧠 为测试分析器传递完整上下文: "
                               f"{len(test_context.get('complete_conversation_history', []))}轮对话历史")
                
                # 将上下文添加到测试分析器的参数中
                enhanced_analysis["full_test_context"] = test_context
            
            return await self.test_analyzer.run_with_user_testbench(
                design_only_files,
                testbench_to_use
            )
        else:
            # 回退到标准测试流程（生成新的测试台）
            self.logger.info("🔄 未找到测试台文件，使用标准测试流程生成测试台")
            test_task = self._build_test_task(design_result, enhanced_analysis)
            
            # 🧠 为测试Agent传递完整上下文
            test_context = enhanced_analysis.get("context", {}).copy()
            if self.context_manager:
                full_context = self.context_manager.get_full_context_for_agent(
                    "code_reviewer", 
                    "测试验证任务"
                )
                test_context["full_conversation_context"] = full_context
                self.logger.info(f"🧠 为测试Agent传递完整上下文: "
                               f"{len(full_context.get('complete_conversation_history', []))}轮对话历史")
            
            result = await self.base_coordinator.coordinate_task_execution(
                test_task, test_context
            )
            return result
    
    async def _analyze_for_improvement(self, iteration_result: Dict[str, Any],
                                     enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析并生成改进建议 - 增强版：使用完整上下文管理器"""
        
        # 🧠 使用上下文管理器提供的历史信息进行智能分析
        if self.context_manager:
            full_context = self.context_manager.get_full_context_for_agent(
                "analyzer", 
                "错误分析任务"
            )
            
            # 将完整上下文添加到分析参数中
            enhanced_analysis["full_analysis_context"] = full_context
            
            # 记录上下文信息用于分析
            conversation_history = full_context.get("complete_conversation_history", [])
            previous_iterations = full_context.get("previous_iterations_summary", [])
            error_context = full_context.get("detailed_error_context", {})
            
            self.logger.info(f"🧠 错误分析使用完整上下文: "
                           f"{len(conversation_history)}轮对话历史, "
                           f"{len(previous_iterations)}次历史迭代, "
                           f"{len(error_context.get('compilation_errors', []))}个编译错误")
            
            # 基于历史模式进行智能分析
            if previous_iterations:
                # 分析历史失败模式
                failure_patterns = self._analyze_failure_patterns(previous_iterations)
                enhanced_analysis["failure_patterns"] = failure_patterns
                self.logger.info(f"🧠 识别到失败模式: {failure_patterns}")
            
            # 基于对话历史分析AI行为模式
            if conversation_history:
                behavior_patterns = self._analyze_ai_behavior_patterns(conversation_history)
                enhanced_analysis["behavior_patterns"] = behavior_patterns
                self.logger.info(f"🧠 识别到AI行为模式: {behavior_patterns}")
        
        return await self.test_analyzer.analyze_test_failures(
            iteration_result.get("test_results", {}),
            enhanced_analysis
        )
    
    def _analyze_failure_patterns(self, previous_iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析历史失败模式"""
        patterns = {
            "repeated_errors": [],
            "error_evolution": [],
            "success_patterns": [],
            "common_fixes": []
        }
        
        for iteration in previous_iterations:
            failures = iteration.get("main_failures", [])
            lessons = iteration.get("lessons_learned", [])
            
            # 记录重复错误
            for failure in failures:
                if failure not in patterns["repeated_errors"]:
                    patterns["repeated_errors"].append(failure)
            
            # 记录错误演进
            patterns["error_evolution"].append({
                "iteration": iteration["iteration_number"],
                "failures": failures,
                "lessons": lessons
            })
            
            # 记录成功模式
            if iteration.get("all_tests_passed", False):
                patterns["success_patterns"].append({
                    "iteration": iteration["iteration_number"],
                    "key_factors": lessons
                })
        
        return patterns
    
    def _analyze_ai_behavior_patterns(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析AI行为模式"""
        patterns = {
            "tool_usage_patterns": {},
            "decision_patterns": [],
            "error_response_patterns": [],
            "success_strategies": []
        }
        
        for turn in conversation_history:
            tool_calls = turn.get("tool_calls", [])
            ai_response = turn.get("ai_response", "")
            
            # 分析工具使用模式
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool_name", "unknown")
                if tool_name not in patterns["tool_usage_patterns"]:
                    patterns["tool_usage_patterns"][tool_name] = 0
                patterns["tool_usage_patterns"][tool_name] += 1
            
            # 分析决策模式
            if any(keyword in ai_response for keyword in ["决定", "选择", "采用", "修改"]):
                patterns["decision_patterns"].append({
                    "iteration": turn.get("iteration_number", 0),
                    "decision": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                })
            
            # 分析错误响应模式
            if not turn.get("success", True):
                patterns["error_response_patterns"].append({
                    "iteration": turn.get("iteration_number", 0),
                    "error_type": turn.get("error_info", {}).get("type", "unknown"),
                    "response": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                })
        
        return patterns
    
    async def _build_design_task(self, enhanced_analysis: Dict[str, Any], iteration: int) -> str:
        """构建设计任务描述 - 使用完整上下文管理器"""
        base_requirements = enhanced_analysis.get("design_requirements", "")
        
        task = f"设计任务 (迭代 {iteration}):\n\n{base_requirements}\n\n"
        
        # 🎯 新增：注入成功经验指导
        if self.context_manager and iteration > 1:
            success_context = self.context_manager.build_success_context_for_agent()
            task += success_context
        
        # 🧠 使用完整上下文管理器获取全量信息
        if self.context_manager and iteration > 1:
            full_context = self.context_manager.get_full_context_for_agent(
                "verilog_designer", 
                f"设计任务迭代{iteration}"
            )
            
            # 1. 完整代码内容传递
            code_content = full_context.get("complete_code_content", {})
            if code_content.get("design_files"):
                task += "📄 **完整DUT代码内容** (包含所有历史版本和错误定位):\n"
                for file_path, file_info in code_content["design_files"].items():
                    task += f"\n### 文件: {file_path} (模块: {file_info['module_name']})\n"
                    task += f"```verilog\n{file_info['content_with_line_numbers']}\n```\n"
                    
                    # 如果有错误行，特别标注
                    if file_info.get("error_lines"):
                        task += "\n🚨 **错误行标注**:\n"
                        for line_num, line_content in file_info["error_lines"].items():
                            task += f"  行 {line_num}: {line_content}\n"
                    task += "\n"
            
            # 2. 完整对话历史传递
            conversation_history = full_context.get("complete_conversation_history", [])
            if conversation_history:
                task += "🗣️ **完整对话历史** (包含所有AI推理过程):\n"
                for turn in conversation_history[-3:]:  # 只显示最近3轮对话
                    task += f"\n#### 迭代{turn['iteration_number']} - {turn['agent_id']}:\n"
                    task += f"**AI响应**: {turn['ai_response'][:300]}...\n"
                    if turn.get('reasoning_notes'):
                        task += f"**推理笔记**: {turn['reasoning_notes']}\n"
                    if turn.get('tool_calls'):
                        task += f"**工具调用**: {len(turn['tool_calls'])}个工具\n"
                task += "\n"
            
            # 3. 详细错误上下文
            error_context = full_context.get("detailed_error_context", {})
            if error_context.get("compilation_errors"):
                task += "🔍 **详细错误分析** (包含代码上下文):\n"
                for error in error_context["compilation_errors"]:
                    task += f"\n- 错误: {error.get('message', 'Unknown')}\n"
                    task += f"  文件: {error.get('file', 'Unknown')}, 行: {error.get('line', 'Unknown')}\n"
                    if error.get('error_line_content'):
                        task += f"  错误行内容: {error['error_line_content']}\n"
                    if error.get('error_context'):
                        task += f"  上下文:\n{error['error_context']}\n"
                task += "\n"
            
            # 4. 多agent协作历史
            collaboration_history = full_context.get("agent_collaboration_history", {})
            if collaboration_history.get("agent_interactions"):
                task += "🤝 **Agent协作历史**:\n"
                for interaction in collaboration_history["agent_interactions"]:
                    task += f"- 迭代{interaction['iteration_number']}: {', '.join(interaction['agents'])}\n"
                    task += f"  结果: {interaction['context']['outcome']}\n"
                task += "\n"
            
            # 5. 历史迭代经验教训
            previous_iterations = full_context.get("previous_iterations_summary", [])
            if previous_iterations:
                task += "📚 **历史迭代经验教训**:\n"
                for prev_iter in previous_iterations[-2:]:  # 最近2次迭代
                    task += f"\n### 迭代{prev_iter['iteration_number']}:\n"
                    task += f"- 编译成功: {prev_iter['compilation_success']}\n"
                    task += f"- 主要失败原因: {', '.join(prev_iter.get('main_failures', []))}\n"
                    task += f"- 经验教训: {'; '.join(prev_iter.get('lessons_learned', []))}\n"
                task += "\n"
            
            # 6. 🧠 基于历史模式的智能建议
            failure_patterns = enhanced_analysis.get("failure_patterns", {})
            behavior_patterns = enhanced_analysis.get("behavior_patterns", {})
            
            if failure_patterns:
                task += "🎯 **基于历史模式的智能建议**:\n"
                
                # 重复错误警告
                repeated_errors = failure_patterns.get("repeated_errors", [])
                if repeated_errors:
                    task += f"\n⚠️ **重复错误警告**: 以下错误在历史迭代中重复出现:\n"
                    for error in repeated_errors:
                        task += f"   - {error}\n"
                    task += "   请特别注意避免这些错误！\n"
                
                # 成功模式建议
                success_patterns = failure_patterns.get("success_patterns", [])
                if success_patterns:
                    task += f"\n✅ **成功模式建议**: 参考以下成功策略:\n"
                    for pattern in success_patterns:
                        task += f"   - 迭代{pattern['iteration']}: {', '.join(pattern.get('key_factors', []))}\n"
            
            if behavior_patterns:
                task += "\n🤖 **AI行为模式分析**:\n"
                
                # 工具使用模式
                tool_patterns = behavior_patterns.get("tool_usage_patterns", {})
                if tool_patterns:
                    task += f"- 常用工具: {', '.join([f'{tool}({count})' for tool, count in tool_patterns.items()])}\n"
                
                # 决策模式
                decision_patterns = behavior_patterns.get("decision_patterns", [])
                if decision_patterns:
                    task += f"- 历史决策数量: {len(decision_patterns)}\n"
                    for decision in decision_patterns[-2:]:  # 最近2个决策
                        task += f"  - 迭代{decision['iteration']}: {decision['decision']}\n"
            
            self.logger.info(f"🧠 完整上下文传递: 包含{len(conversation_history)}轮对话，{len(code_content.get('design_files', {}))}个代码文件")
        
        else:
            # 第一次迭代，添加基础指导
            task += "✨ **首次设计指导**:\n"
            task += "- 请仔细分析需求，设计符合接口规范的代码\n"
            task += "- 注意使用正确的Verilog语法，避免SystemVerilog特性\n"
            task += "- 确保所有端口定义正确匹配\n\n"
        
        if iteration > 1:
            # 🔧 增强错误修复指导：代码验证 + 深度分析
            task += "\n\n🔧 **严格代码验证要求**:\n"
            task += "1. **编译器兼容性 (iverilog - Verilog-2001标准)**:\n"
            task += "   ❌ 禁止：logic类型、interface、generate内复杂逻辑、assert语句\n"
            task += "   ✅ 只用：wire、reg、assign、always@(*)\n"
            task += "2. **纯组合逻辑验证**:\n"
            task += "   ❌ 严禁：clk、rst、@(posedge)、output reg配合always@(posedge)\n"
            task += "   ✅ 必须：output wire配合assign，或output reg配合always@(*)\n"
            task += "3. **接口严格匹配**:\n"
            task += f"   - 模块名必须完全匹配测试台实例化\n"
            task += f"   - 端口名必须与测试台连接一致\n\n"
                
            # 添加深度分析的错误反馈信息
            last_errors = enhanced_analysis.get("last_compilation_errors", "")
            last_test_results = enhanced_analysis.get("last_test_results", "")
            
            if last_errors:
                # 显示原始错误信息（保持完整上下文）
                task += "🚨 **上次编译错误详情**:\n"
                task += f"```\n{last_errors}\n```\n\n"
            
            if last_test_results:
                # 显示测试失败详情
                task += "🧪 **上次测试失败详情**:\n"
                task += f"```\n{last_test_results}\n```\n\n"
            
            # 添加改进建议
            improvement_suggestions = enhanced_analysis.get("improvement_suggestions", [])
            if improvement_suggestions:
                task += "💡 **改进建议**:\n"
                for i, suggestion in enumerate(improvement_suggestions, 1):
                    task += f"{i}. {suggestion}\n"
                task += "\n"
        
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
        return self.test_driven_sessions.get(session_id, {}).get("iterations", [])
    
    def load_context_from_file(self, context_file_path: str) -> bool:
        """从文件加载上下文"""
        try:
            if self.context_manager:
                self.context_manager.load_from_file(context_file_path)
                self.logger.info(f"🧠 成功加载上下文文件: {context_file_path}")
                return True
            else:
                self.logger.error("❌ 上下文管理器未初始化")
                return False
        except Exception as e:
            self.logger.error(f"❌ 加载上下文文件失败: {str(e)}")
            return False
    
    def get_context_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取上下文统计信息"""
        if not self.context_manager:
            return {"error": "上下文管理器未初始化"}
        
        stats = {
            "session_id": session_id,
            "total_iterations": len(self.context_manager.iterations),
            "current_iteration": self.context_manager.current_iteration.iteration_number if self.context_manager.current_iteration else 0,
            "total_conversation_turns": 0,
            "total_code_files": 0,
            "total_testbench_files": 0,
            "compilation_errors_count": 0,
            "successful_iterations": 0,
            "failed_iterations": 0
        }
        
        # 统计所有迭代的信息
        for iteration_id, iteration in self.context_manager.iterations.items():
            stats["total_conversation_turns"] += len(iteration.conversation_turns)
            stats["total_code_files"] += len(iteration.code_files)
            stats["total_testbench_files"] += len(iteration.testbench_files)
            
            if iteration.compilation_errors:
                stats["compilation_errors_count"] += len(iteration.compilation_errors)
            
            if iteration.all_tests_passed:
                stats["successful_iterations"] += 1
            else:
                stats["failed_iterations"] += 1
        
        return stats
    
    def export_context_summary(self, session_id: str) -> Dict[str, Any]:
        """导出上下文摘要"""
        if not self.context_manager:
            return {"error": "上下文管理器未初始化"}
        
        summary = {
            "session_id": session_id,
            "statistics": self.get_context_statistics(session_id),
            "key_insights": [],
            "recommendations": []
        }
        
        # 分析关键洞察
        if self.context_manager.current_iteration:
            current_iter = self.context_manager.current_iteration
            
            # 分析失败模式
            if current_iter.compilation_errors:
                error_types = set()
                for error in current_iter.compilation_errors:
                    if 'type' in error:
                        error_types.add(error['type'])
                
                if error_types:
                    summary["key_insights"].append({
                        "type": "compilation_errors",
                        "message": f"主要错误类型: {', '.join(error_types)}",
                        "count": len(current_iter.compilation_errors)
                    })
            
            # 分析对话模式
            if current_iter.conversation_turns:
                agents_used = set(turn.agent_id for turn in current_iter.conversation_turns)
                summary["key_insights"].append({
                    "type": "agent_collaboration",
                    "message": f"使用的智能体: {', '.join(agents_used)}",
                    "turn_count": len(current_iter.conversation_turns)
                })
        
        # 生成建议
        stats = summary["statistics"]
        if stats["failed_iterations"] > stats["successful_iterations"]:
            summary["recommendations"].append({
                "priority": "high",
                "message": "失败迭代较多，建议检查错误模式和修复策略"
            })
        
        if stats["compilation_errors_count"] > 0:
            summary["recommendations"].append({
                "priority": "medium",
                "message": f"存在{stats['compilation_errors_count']}个编译错误，需要语法检查"
            })
        
        return summary
    
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
    
    def _extract_file_references(self, agent_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从智能体结果中提取文件引用（统一策略版）"""
        file_references = []
        
        # 🎯 策略1：优先从工具调用结果中提取文件引用（最高优先级）
        if "tool_results" in agent_result:
            for tool_result in agent_result["tool_results"]:
                if isinstance(tool_result, dict) and tool_result.get("success"):
                    # 检查是否包含文件引用信息
                    if "file_reference" in tool_result:
                        file_references.append(tool_result["file_reference"])
                        self.logger.info(f"✅ 从工具结果提取文件引用: {tool_result['file_reference'].get('file_path', 'unknown')}")
                    elif "file_path" in tool_result and tool_result.get("file_path"):
                        # 构建完整的文件引用格式
                        file_ref = {
                            "file_path": tool_result["file_path"],
                            "file_type": tool_result.get("file_type", "verilog"),
                            "file_id": tool_result.get("file_id"),
                            "created_by": tool_result.get("created_by"),
                            "created_at": tool_result.get("created_at"),
                            "description": tool_result.get("description", "")
                        }
                        file_references.append(file_ref)
                        self.logger.info(f"✅ 构建文件引用: {file_ref['file_path']} (类型: {file_ref['file_type']})")
        
        # 🎯 策略2：从传统格式中提取（中等优先级）
        legacy_formats = ["file_references", "design_files"]
        for format_key in legacy_formats:
            if format_key in agent_result and agent_result[format_key]:
                file_references.extend(agent_result[format_key])
                self.logger.info(f"✅ 从{format_key}提取 {len(agent_result[format_key])} 个文件引用")
        
        # 🎯 策略3：智能从中央文件管理器获取（仅在前两种策略都失败时使用）
        if not file_references:
            self.logger.warning("⚠️ 工具结果中未找到文件引用，尝试从中央文件管理器获取")
            file_references = self._intelligent_file_retrieval_from_manager()
        
        # 🎯 策略4：文件引用去重和验证
        validated_references = self._validate_and_deduplicate_file_references(file_references)
        
        # 🧠 将设计文件添加到上下文管理器
        if self.context_manager:
            for file_ref in validated_references:
                if isinstance(file_ref, dict) and 'file_path' in file_ref:
                    file_path = file_ref['file_path']
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            module_name = self._extract_module_name(content)
                            self.context_manager.add_code_file(
                                file_path=file_path,
                                content=content,
                                module_name=module_name or "unknown",
                                file_type="design"
                            )
                            self.logger.info(f"🧠 上下文管理器: 添加设计文件 {file_path} (模块: {module_name})")
                    except Exception as e:
                        self.logger.error(f"❌ 读取设计文件失败 {file_path}: {str(e)}")
        
        self.logger.info(f"📄 最终提取到 {len(validated_references)} 个有效文件引用")
        return validated_references
    
    def _intelligent_file_retrieval_from_manager(self) -> List[Dict[str, Any]]:
        """智能从中央文件管理器获取文件（备用策略）"""
        file_references = []
        
        try:
            from core.file_manager import get_file_manager
            file_manager = get_file_manager()
            
            # 🎯 精确策略：只获取最近5分钟内创建的文件，避免历史污染
            import datetime
            recent_cutoff = (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat()
            
            # 🎯 重点关注当前TDD迭代相关的智能体
            priority_agents = ["enhanced_real_verilog_agent", "real_verilog_agent"]
            current_iteration_files = []
            
            for agent_id in priority_agents:
                try:
                    agent_files = file_manager.get_files_by_creator(agent_id)
                    # 只取最近5分钟的文件
                    recent_files = [f for f in agent_files if f.created_at > recent_cutoff]
                    current_iteration_files.extend(recent_files)
                    self.logger.debug(f"从 {agent_id} 获取到 {len(recent_files)} 个最近文件")
                except Exception as e:
                    self.logger.debug(f"获取 {agent_id} 文件时出错: {e}")
            
            # 按创建时间排序，最新的在前
            current_iteration_files.sort(key=lambda x: x.created_at, reverse=True)
            
            # 🎯 严格选择：每种类型只选择1个最新的、文件名不重复的文件
            selected_designs = {}  # module_name -> file_ref
            selected_testbenches = {}  # module_name -> file_ref
            
            for file_ref in current_iteration_files:
                filename = Path(file_ref.file_path).name
                module_name = Path(file_ref.file_path).stem
                
                # 移除常见的后缀来获取核心模块名
                for suffix in ['_tb', '_test', '_testbench']:
                    if module_name.endswith(suffix):
                        module_name = module_name[:-len(suffix)]
                        break
                
                # 分类处理
                is_testbench = any(keyword in filename.lower() for keyword in ['_tb.v', 'testbench', '_test'])
                
                if not is_testbench and file_ref.file_type == "verilog":
                    # 设计文件：每个模块只保留最新的
                    if module_name not in selected_designs:
                        selected_designs[module_name] = file_ref
                        self.logger.info(f"🎯 选择设计文件: {filename} (模块: {module_name})")
                elif is_testbench and file_ref.file_type in ["verilog", "testbench"]:
                    # 测试台文件：每个模块只保留最新的
                    if module_name not in selected_testbenches:
                        selected_testbenches[module_name] = file_ref
                        self.logger.info(f"🎯 选择测试台文件: {filename} (模块: {module_name})")
            
            # 转换为统一格式
            for file_ref in list(selected_designs.values()) + list(selected_testbenches.values()):
                file_references.append({
                    "file_id": file_ref.file_id,
                    "file_path": file_ref.file_path,
                    "file_type": file_ref.file_type,
                    "created_by": file_ref.created_by,
                    "created_at": file_ref.created_at,
                    "description": file_ref.description
                })
            
            self.logger.info(f"🔍 智能选择: {len(selected_designs)} 个设计文件, {len(selected_testbenches)} 个测试台文件")
            
        except Exception as e:
            self.logger.error(f"❌ 从中央文件管理器获取文件失败: {e}")
        
        return file_references
    
    def _validate_and_deduplicate_file_references(self, file_references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证并去重文件引用，智能选择最新版本"""
        validated_refs = []
        seen_paths = set()
        seen_file_ids = set()
        
        # 🎯 按模块名分组，每个模块只保留最新的设计文件
        module_files = {}  # module_name -> [file_refs]
        
        for file_ref in file_references:
            if not isinstance(file_ref, dict):
                continue
                
            file_path = file_ref.get("file_path")
            file_id = file_ref.get("file_id")
            
            # 跳过无效的文件引用
            if not file_path:
                self.logger.warning("⚠️ 跳过无效文件引用（缺少file_path）")
                continue
            
            # 文件存在性检查
            if not Path(file_path).exists():
                self.logger.warning(f"⚠️ 文件不存在，跳过: {file_path}")
                continue
            
            # 提取模块名
            filename = Path(file_path).name
            module_name = Path(file_path).stem
            
            # 检查是否是设计文件（非测试台）
            is_testbench = any(keyword in filename.lower() for keyword in ['_tb.v', 'testbench', '_test'])
            
            if not is_testbench and file_ref.get("file_type") == "verilog":
                # 设计文件：按模块名分组
                base_module_name = module_name.split('_')[0]  # 去除版本后缀，如 counter_8bit_2 -> counter
                
                if base_module_name not in module_files:
                    module_files[base_module_name] = []
                module_files[base_module_name].append(file_ref)
            else:
                # 测试台文件和其他文件直接添加（不需要版本控制）
                if file_path not in seen_paths and (not file_id or file_id not in seen_file_ids):
                    validated_refs.append(file_ref)
                    seen_paths.add(file_path)
                    if file_id:
                        seen_file_ids.add(file_id)
                    self.logger.debug(f"✅ 验证通过（测试台/其他）: {filename}")
        
        # 🎯 对每个模块，只选择最新的设计文件
        for module_name, files in module_files.items():
            if not files:
                continue
            
            # 按创建时间排序，选择最新的
            files_sorted = sorted(files, key=lambda x: x.get("created_at", ""), reverse=True)
            latest_file = files_sorted[0]
            
            file_path = latest_file.get("file_path")
            file_id = latest_file.get("file_id")
            
            # 避免重复
            if file_path not in seen_paths and (not file_id or file_id not in seen_file_ids):
                validated_refs.append(latest_file)
                seen_paths.add(file_path)
                if file_id:
                    seen_file_ids.add(file_id)
                
                self.logger.info(f"🎯 选择最新设计文件: {Path(file_path).name} (模块: {module_name})")
                
                # 记录被跳过的旧版本
                if len(files) > 1:
                    skipped_files = [Path(f.get("file_path", "")).name for f in files_sorted[1:]]
                    self.logger.debug(f"⏭️ 跳过旧版本: {', '.join(skipped_files)}")
        
        return validated_refs
    
    def _determine_testbench_strategy(self, iteration: int, user_testbench_path: str, 
                                     current_iteration_testbench: str) -> Dict[str, str]:
        """统一的testbench选择策略"""
        strategy_info = {
            "selected_testbench": None,
            "strategy": "未定义",
            "reason": "无可用测试台"
        }
        
        # 检查可用的testbench选项
        has_user_testbench = user_testbench_path and Path(user_testbench_path).exists()
        has_generated_testbench = current_iteration_testbench and Path(current_iteration_testbench).exists()
        
        self.logger.debug(f"testbench可用性: 用户提供={has_user_testbench}, 智能体生成={has_generated_testbench}")
        
        if iteration == 1:
            # 第一次迭代：优先使用用户提供的，建立基准
            if has_user_testbench:
                strategy_info.update({
                    "selected_testbench": user_testbench_path,
                    "strategy": "用户基准",
                    "reason": "第1次迭代使用用户提供的测试台作为功能基准"
                })
            elif has_generated_testbench:
                strategy_info.update({
                    "selected_testbench": current_iteration_testbench,
                    "strategy": "智能体生成",
                    "reason": "用户未提供测试台，使用智能体生成的测试台"
                })
        else:
            # 后续迭代：🎯 优先使用智能体生成的测试台
            if has_generated_testbench:
                # ✨ 智能体生成了测试台，优先使用（推动TDD循环）
                strategy_info.update({
                    "selected_testbench": current_iteration_testbench,
                    "strategy": "智能体优化",
                    "reason": f"第{iteration}次迭代，优先使用智能体生成的最新测试台推动TDD循环"
                })
            elif has_user_testbench:
                # 只有用户测试台可用时才使用
                strategy_info.update({
                    "selected_testbench": user_testbench_path,
                    "strategy": "用户备用",
                    "reason": f"第{iteration}次迭代，智能体未生成测试台，使用用户测试台"
                })
        
        return strategy_info
    
    def _should_use_generated_testbench(self, iteration: int) -> bool:
        """决定是否应该使用智能体生成的测试台"""
        # ✨ 积极策略：从第2次迭代开始，优先使用智能体生成的测试台
        # 这确保了 TDD 循环中测试台可以随着设计一起迭代改进
        # 第1次迭代建立基准，第2次及以后迭代优化
        return iteration >= 2
    
    def _analyze_code_violations(self, error_text: str, enhanced_analysis: Dict[str, Any]) -> str:
        """分析代码违规问题"""
        analysis = ""
        
        # 检查SystemVerilog语法违规
        if "logic" in error_text.lower():
            analysis += "🚨 **SystemVerilog语法违规**:\n"
            analysis += "- 检测到 `logic` 类型，iverilog不支持\n"
            analysis += "- 必须改用 `wire` 或 `reg`\n\n"
        
        # 检查时序逻辑违规
        last_code = enhanced_analysis.get("last_generated_code", "")
        if last_code:
            if "posedge" in last_code and ("clk" in last_code or "rst" in last_code):
                analysis += "🚨 **时序逻辑违规**:\n"
                analysis += "- 检测到时钟/复位信号，违反纯组合逻辑要求\n"
                analysis += "- 必须移除 clk、rst 信号\n"
                analysis += "- 将 always @(posedge clk) 改为 always @(*)\n\n"
        
        # 检查端口匹配问题
        if "not a port" in error_text:
            import re
            port_match = re.search(r"port\s+[`'\"]*(\w+)[`'\"]*\s+is not a port", error_text)
            if port_match:
                missing_port = port_match.group(1)
                analysis += f"🚨 **端口匹配错误**:\n"
                analysis += f"- 测试台期望端口: `{missing_port}`\n"
                analysis += f"- 当前模块缺少此端口\n"
                analysis += f"- **立即修复**: 在模块中添加 `{missing_port}` 端口\n\n"
        
        return analysis
    
    def _analyze_test_failures(self, test_results: str, enhanced_analysis: Dict[str, Any]) -> str:
        """深度分析测试失败原因"""
        analysis = ""
        
        # 解析测试结果
        import re
        
        # 查找失败的测试用例
        test_cases = re.findall(r"Test Case (\d+).*?Failed.*?Expected.*?got\s+(.*?)(?=\n|$)", test_results, re.DOTALL)
        
        for case_num, details in test_cases:
            analysis += f"📊 **测试用例 {case_num} 失败分析**:\n"
            
            # 提取具体数值
            values = re.findall(r"(\w+)=([0-9a-fA-F]+)", details)
            if values:
                analysis += "- 实际结果: " + ", ".join([f"{k}={v}" for k, v in values]) + "\n"
            
            # 特定错误模式分析
            if "overflow" in details and "overflow=0" in details:
                analysis += "🔍 **溢出检测逻辑错误**:\n"
                analysis += "- 溢出检测输出为0，但应该为1\n"
                analysis += "- 检查公式: `overflow = (a[15] == b[15]) && (a[15] != sum[15])`\n"
                analysis += "- 验证: 两个同号数相加结果变号时应该溢出\n\n"
            
            if "cout" in details:
                analysis += "🔍 **进位逻辑检查**:\n"
                analysis += "- 验证进位计算: 最高位是否正确传播\n"
                analysis += "- 检查: `cout = (a[15] & b[15]) | ((a[15] ^ b[15]) & carry[14])`\n\n"
        
        return analysis
    
    async def _llm_analyze_failures(self, error_text: str, enhanced_analysis: Dict[str, Any], iteration: int) -> str:
        """使用LLM智能分析编译失败原因"""
        if not error_text.strip():
            return ""
        
        # 准备LLM分析的context
        last_code = enhanced_analysis.get("last_generated_code", "")
        design_requirements = enhanced_analysis.get("design_requirements", "")
        
        analysis_prompt = f"""作为Verilog专家，请分析以下编译错误并提供精准的修复指导：

🎯 **设计要求**:
{design_requirements}

📄 **生成的代码**:
```verilog
{last_code[:1000] if last_code else "代码不可用"}
```

❌ **编译错误**:
```
{error_text}
```

🔍 **迭代信息**: 第{iteration}次迭代

请提供以下分析：
1. **根本原因**: 错误的本质是什么？
2. **违反的约束**: 违反了哪些设计要求？
3. **具体修复**: 提供3-5个具体的修复步骤
4. **验证方法**: 如何验证修复是否正确？

格式要求：
- 使用markdown格式
- 重点内容用**加粗**
- 修复步骤要具体可操作
- 避免一般性建议，要针对具体错误"""

        try:
            # 调用LLM进行分析
            from core.llm_integration.enhanced_llm_client import EnhancedLLMClient
            from config.config import FrameworkConfig
            
            config = FrameworkConfig.from_env()
            llm_client = EnhancedLLMClient(config.llm)
            
            analysis_result = await llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是资深的Verilog设计专家，专门分析和修复硬件描述语言的问题。",
                temperature=0.1,  # 低温度确保分析准确性
                max_tokens=1000
            )
            
            return f"🤖 **LLM智能失败分析**:\n{analysis_result}\n\n"
            
        except Exception as e:
            self.logger.error(f"❌ LLM失败分析异常: {str(e)}")
            # 降级到简化的规则分析
            return self._analyze_code_violations(error_text, enhanced_analysis)
    
    async def _llm_analyze_test_failures(self, test_results: str, enhanced_analysis: Dict[str, Any], iteration: int) -> str:
        """使用LLM智能分析测试失败原因"""
        if not test_results.strip():
            return ""
        
        last_code = enhanced_analysis.get("last_generated_code", "")
        design_requirements = enhanced_analysis.get("design_requirements", "")
        
        analysis_prompt = f"""作为数字电路验证专家，请分析以下测试失败原因：

🎯 **设计要求**:
{design_requirements}

📄 **被测代码**:
```verilog
{last_code[:1000] if last_code else "代码不可用"}
```

🧪 **测试结果**:
```
{test_results}
```

🔍 **迭代信息**: 第{iteration}次迭代

请提供以下分析：
1. **失败模式**: 测试失败的具体模式是什么？
2. **数学分析**: 从数学角度分析为什么会失败？
3. **逻辑错误**: 指出具体的逻辑实现错误
4. **修复建议**: 提供具体的代码修改建议
5. **验证策略**: 如何验证修复后的正确性？

特别关注：
- 溢出检测逻辑的数学正确性
- 进位传播的实现方式
- 边界条件的处理

格式要求：
- 使用markdown格式
- 包含具体的数值例子
- 提供可操作的修复代码片段"""

        try:
            from core.llm_integration.enhanced_llm_client import EnhancedLLMClient
            from config.config import FrameworkConfig
            
            config = FrameworkConfig.from_env()
            llm_client = EnhancedLLMClient(config.llm)
            
            analysis_result = await llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是资深的数字电路验证专家，专门分析测试失败原因并提供精确的修复方案。",
                temperature=0.1,
                max_tokens=1000
            )
            
            return f"🤖 **LLM智能测试分析**:\n{analysis_result}\n\n"
            
        except Exception as e:
            self.logger.error(f"❌ LLM测试分析异常: {str(e)}")
            # 降级到简化的规则分析
            return self._analyze_test_failures(test_results, enhanced_analysis)
    
    async def _build_detailed_error_context(self, error_text: str, enhanced_analysis: Dict[str, Any]) -> str:
        """构建详细的错误上下文信息"""
        context = "🔍 **详细错误上下文分析**:\n"
        
        # 解析错误信息，提取文件名和行号
        import re
        error_matches = re.findall(r'([^:\s]+\.s?v):(\d+):\s*(.+)', error_text)
        
        last_code = enhanced_analysis.get("last_generated_code", "")
        
        for file_path, line_num, error_msg in error_matches:
            context += f"\n📍 **错误位置**: {file_path}:{line_num}\n"
            context += f"📝 **错误描述**: {error_msg}\n"
            
            if last_code:
                try:
                    lines = last_code.split('\n')
                    line_idx = int(line_num) - 1
                    
                    if 0 <= line_idx < len(lines):
                        # 显示错误行及其上下文
                        context += f"\n💡 **错误代码上下文**:\n```verilog\n"
                        
                        # 显示前后3行代码
                        start = max(0, line_idx - 3)
                        end = min(len(lines), line_idx + 4)
                        
                        for i in range(start, end):
                            marker = ">>> " if i == line_idx else "    "
                            context += f"{marker}{i+1:3d}: {lines[i]}\n"
                        
                        context += "```\n"
                        
                        # 分析具体错误
                        error_line = lines[line_idx].strip()
                        context += f"\n🔍 **问题代码**: `{error_line}`\n"
                        
                        # 基于错误类型提供具体分析
                        if "syntax error" in error_msg.lower():
                            context += await self._analyze_syntax_error(error_line, error_msg)
                        elif "not a port" in error_msg.lower():
                            context += await self._analyze_port_error(error_line, error_msg, last_code)
                        
                except Exception as e:
                    self.logger.error(f"❌ 构建错误上下文失败: {str(e)}")
        
        return context + "\n"
    
    async def _analyze_syntax_error(self, error_line: str, error_msg: str) -> str:
        """分析语法错误"""
        analysis = "\n🚨 **语法错误分析**:\n"
        
        # 检查常见语法问题
        if "for (" in error_line and "int " in error_line:
            analysis += "- 检测到SystemVerilog `for (int i...)` 语法\n"
            analysis += "- iverilog不支持此语法，需要改为Verilog-2001语法\n"
            analysis += "- **修复建议**: 在模块顶部声明 `integer i;`，然后使用 `for (i = 0; ...)`\n"
        elif "logic" in error_line:
            analysis += "- 检测到SystemVerilog `logic` 类型\n"
            analysis += "- iverilog不支持此类型，需要改为 `wire` 或 `reg`\n"
            analysis += "- **修复建议**: 将 `logic` 改为 `wire`（组合逻辑）或 `reg`（时序逻辑）\n"
        elif "assert" in error_line:
            analysis += "- 检测到SystemVerilog `assert` 语句\n"
            analysis += "- iverilog不支持此功能，需要删除或改为普通验证\n"
            analysis += "- **修复建议**: 删除assert语句或改为if语句进行检查\n"
        else:
            analysis += f"- 语法错误: {error_msg}\n"
            analysis += "- **建议**: 检查括号匹配、分号、关键字拼写\n"
        
        return analysis
    
    async def _analyze_port_error(self, error_line: str, error_msg: str, full_code: str) -> str:
        """分析端口匹配错误"""
        analysis = "\n🔌 **端口匹配错误分析**:\n"
        
        # 提取错误的端口名
        import re
        port_match = re.search(r"port\s+[`'\"]*(\w+)[`'\"]*\s+is not a port", error_msg)
        
        if port_match:
            missing_port = port_match.group(1)
            analysis += f"- 测试台期望端口: `{missing_port}`\n"
            
            # 分析模块实际端口
            module_match = re.search(r'module\s+\w+\s*\([^)]*\)', full_code, re.DOTALL)
            if module_match:
                module_ports = module_match.group(0)
                analysis += f"- 当前模块端口: {module_ports}\n"
            
            analysis += f"- **修复建议**: 在模块端口列表中添加 `{missing_port}` 端口\n"
            
            # 分析可能的原因
            if missing_port in ["clk", "rst", "rst_n"]:
                analysis += f"- **问题原因**: 设计要求纯组合逻辑，但模块仍包含时钟/复位信号\n"
                analysis += f"- **解决方案**: 完全移除时钟和复位相关的端口和逻辑\n"
        
        return analysis
    
    async def _build_test_failure_context(self, test_results: str, enhanced_analysis: Dict[str, Any]) -> str:
        """构建详细的测试失败上下文"""
        context = "🧪 **详细测试失败上下文**:\n"
        
        # 解析测试结果，提取失败的测试用例
        import re
        
        # 查找失败的测试用例
        test_case_matches = re.findall(r'Test[^\n]*?failed[^\n]*', test_results, re.IGNORECASE)
        
        if test_case_matches:
            context += f"\n📊 **失败的测试用例** ({len(test_case_matches)}个):\n"
            
            for i, test_case in enumerate(test_case_matches, 1):
                context += f"\n🔍 **失败用例 {i}**: {test_case}\n"
                
                # 提取具体的输入输出值
                values = re.findall(r'(\w+)=([0-9a-fA-FxX]+)', test_case)
                if values:
                    context += "📋 **实际结果**:\n"
                    for var, val in values:
                        context += f"  - {var} = {val}\n"
        
        # 查找期望值信息
        expected_matches = re.findall(r'Expected[^\n]*', test_results, re.IGNORECASE)
        if expected_matches:
            context += f"\n✅ **期望结果**:\n"
            for expected in expected_matches:
                context += f"  - {expected}\n"
        
        # 分析具体的数值差异
        last_code = enhanced_analysis.get("last_generated_code", "")
        if last_code:
            context += await self._analyze_test_value_differences(test_results, last_code)
        
        return context + "\n"
    
    async def _analyze_test_value_differences(self, test_results: str, dut_code: str) -> str:
        """分析测试值差异"""
        analysis = "\n🔍 **数值差异分析**:\n"
        
        # 特定测试用例的深度分析
        if "overflow=0" in test_results and "expected" in test_results.lower():
            analysis += "\n🚨 **溢出检测错误分析**:\n"
            
            # 提取溢出检测逻辑
            overflow_match = re.search(r'(assign\s+overflow[^;]+;)', dut_code, re.IGNORECASE)
            if overflow_match:
                overflow_logic = overflow_match.group(1)
                analysis += f"📋 **当前溢出逻辑**: `{overflow_logic}`\n"
                
                # 分析常见的溢出检测错误
                if "(a[15] == b[15]) && (a[15] != sum[15])" in overflow_logic:
                    analysis += "✅ 溢出检测公式正确\n"
                    analysis += "⚠️ 可能问题：sum的计算时序或位置\n"
                    analysis += "🔍 **建议检查**: sum计算是否在overflow检测之前完成\n"
                else:
                    analysis += "❌ 溢出检测公式可能有误\n"
                    analysis += "✅ **正确公式**: `overflow = (a[15] == b[15]) && (a[15] != sum[15])`\n"
        
        # 进位逻辑分析
        if "cout=" in test_results:
            analysis += "\n🔗 **进位逻辑分析**:\n"
            cout_match = re.search(r'(assign\s+cout[^;]+;)', dut_code, re.IGNORECASE)
            if cout_match:
                cout_logic = cout_match.group(1)
                analysis += f"📋 **当前进位逻辑**: `{cout_logic}`\n"
        
        return analysis
    
    def _parse_compilation_errors(self, stderr_content: str) -> List[Dict[str, Any]]:
        """解析编译错误信息"""
        errors = []
        if not stderr_content:
            return errors
        
        # 常见的编译错误模式
        error_patterns = [
            r'(.+?):(\d+):\s*error:\s*(.+)',  # file:line: error: message
            r'(.+?):(\d+):\s*(.+error.+)',   # file:line: error message
            r'Error.*?in\s+(.+?)\s+at\s+line\s+(\d+)',  # Error in file at line
        ]
        
        lines = stderr_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in error_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 3:
                        file_path = match.group(1).strip()
                        line_number = match.group(2).strip()
                        message = match.group(3).strip()
                    else:
                        file_path = match.group(1).strip() if len(match.groups()) >= 1 else "unknown"
                        line_number = match.group(2).strip() if len(match.groups()) >= 2 else "0"
                        message = line
                    
                    errors.append({
                        "file": file_path,
                        "line": line_number,
                        "message": message,
                        "type": "compilation_error",
                        "raw_line": line
                    })
                    break
        
        # 如果没有匹配到特定模式，但包含错误关键词，添加为通用错误
        if not errors and any(keyword in stderr_content.lower() for keyword in ['error', 'failed', 'cannot']):
            errors.append({
                "file": "unknown",
                "line": "0",
                "message": stderr_content.strip(),
                "type": "general_error",
                "raw_line": stderr_content.strip()
            })
        
        return errors
    
    def _extract_module_name(self, verilog_content: str) -> Optional[str]:
        """从Verilog代码中提取模块名"""
        if not verilog_content:
            return None
        
        # 查找 module 声明
        module_pattern = r'module\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[#(]'
        match = re.search(module_pattern, verilog_content)
        if match:
            return match.group(1)
        
        # 简化版模式
        simple_pattern = r'module\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        match = re.search(simple_pattern, verilog_content)
        if match:
            return match.group(1)
        
        return None

    async def _continue_persistent_conversation(self, task: str, context: Dict[str, Any], iteration: int) -> Dict[str, Any]:
        """继续持续对话，不重新选择智能体 - 使用完整上下文管理器"""
        try:
            # 获取之前使用的智能体
            if not hasattr(self, 'current_session_agents') or 'verilog_designer' not in self.current_session_agents:
                # 如果没有记录，回退到标准流程
                self.logger.warning("⚠️ 没有找到持续对话的智能体，回退到标准流程")
                return await self.base_coordinator.coordinate_task_execution(task, context)
            
            design_agent_id = self.current_session_agents['verilog_designer']
            self.logger.info(f"🔗 向持续对话智能体发送任务: {design_agent_id}")
            
            # 直接向智能体发送任务，保持对话上下文
            design_agent = self.base_coordinator.agent_instances.get(design_agent_id)
            if not design_agent:
                self.logger.error(f"❌ 智能体不存在: {design_agent_id}")
                return {"success": False, "error": f"智能体不存在: {design_agent_id}"}
            
            # 🧠 使用完整上下文管理器构建全量上下文
            enhanced_context = context.copy()
            if self.context_manager:
                full_context = self.context_manager.get_full_context_for_agent(design_agent_id, task)
                enhanced_context["full_conversation_context"] = full_context
                self.logger.info(f"🧠 传递完整上下文给{design_agent_id}: "
                               f"{len(full_context.get('complete_conversation_history', []))}轮对话历史")
            
            # 🧠 记录对话开始（AI接收到的prompt）
            if self.context_manager:
                self.context_manager.add_conversation_turn(
                    agent_id=design_agent_id,
                    user_prompt=task,
                    system_prompt="TDD迭代设计任务",
                    ai_response="",  # 稍后更新
                    reasoning_notes=f"迭代{iteration}的持续对话"
                )
            
            # 创建任务消息
            task_message = TaskMessage(
                task_id=f"{self.persistent_conversation_id}_iter_{iteration}",
                sender_id="test_driven_coordinator",
                receiver_id=design_agent_id,
                message_type="task_execution",
                content=task,
                metadata=enhanced_context
            )
            
            # 直接调用智能体的增强任务执行方法
            result = await design_agent.execute_enhanced_task(task, task_message, {})
            
            # 🧠 记录对话结果（AI的完整响应）
            if self.context_manager and self.context_manager.current_iteration:
                # 更新最后一个对话轮次的AI响应
                last_turn = self.context_manager.current_iteration.conversation_turns[-1]
                last_turn.ai_response = str(result.get("content", ""))
                last_turn.success = result.get("success", False)
                last_turn.error_info = result.get("error") if not result.get("success") else None
                last_turn.tool_calls = result.get("tool_calls", [])
                last_turn.tool_results = result.get("tool_results", [])
            
            # 记录本次迭代的结果
            if result.get("success", False):
                self.logger.info(f"✅ 持续对话任务完成: 迭代 {iteration}")
            else:
                self.logger.error(f"❌ 持续对话任务失败: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 持续对话异常: {str(e)}")
            # 出错时回退到标准流程
            return await self.base_coordinator.coordinate_task_execution(task, context)
    


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