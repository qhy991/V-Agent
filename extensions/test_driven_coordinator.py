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
        design_task = self._build_design_task(enhanced_analysis, iteration)
        
        # 🔧 修复：在TDD场景中，强制指定这是设计任务，避免被误判为review任务
        tdd_context = enhanced_analysis.get("context", {}).copy()
        tdd_context["force_task_type"] = "design"  # 强制指定为设计任务
        tdd_context["preferred_agent_role"] = "verilog_designer"  # 优先选择Verilog设计智能体
        
        # 🔍 调试日志：记录强制任务类型
        self.logger.info(f"🔧 DEBUG: TDD设计阶段 - 强制任务类型为design，优先agent: verilog_designer")
        
        # 使用现有协调器执行设计任务（不修改现有功能）
        result = await self.base_coordinator.coordinate_task_execution(
            design_task, tdd_context
        )
        
        return result
    
    async def _execute_test_phase(self, session_id: str, iteration: int,
                                design_result: Dict[str, Any],
                                enhanced_analysis: Dict[str, Any],
                                design_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行测试阶段"""
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
            
            return await self.test_analyzer.run_with_user_testbench(
                design_only_files,
                testbench_to_use
            )
        else:
            # 回退到标准测试流程（生成新的测试台）
            self.logger.info("🔄 未找到测试台文件，使用标准测试流程生成测试台")
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
        
        # 🔍 调试日志：记录enhanced_analysis内容
        if iteration > 1:
            self.logger.info(f"🔍 DEBUG: 构建第{iteration}次迭代设计任务")
            self.logger.info(f"🔍 enhanced_analysis keys: {list(enhanced_analysis.keys())}")
            
            debug_keys = ["last_compilation_errors", "last_failure_reasons", "improvement_suggestions"]
            for key in debug_keys:
                if key in enhanced_analysis:
                    content = enhanced_analysis[key]
                    if isinstance(content, str):
                        self.logger.info(f"🔍 DEBUG: {key}: {content[:150]}...")
                    else:
                        self.logger.info(f"🔍 DEBUG: {key}: {content}")
                else:
                    self.logger.warning(f"🔍 DEBUG: 缺少关键字段: {key}")
        
        if iteration > 1:
            # 添加具体的错误反馈信息
            last_errors = enhanced_analysis.get("last_compilation_errors", "")
            if last_errors:
                task += f"❌ 上次迭代编译错误:\n{last_errors}\n\n"
                
                # 🎯 针对具体错误的特殊处理
                if "rst_n" in last_errors and "not a port" in last_errors:
                    task += "🚨 **【致命错误】接口不匹配 - 必须立即修复**:\n"
                    task += "❌ **错误现象**: 测试台连接 `.rst_n(rst_n)` 但模块定义的是 `input rst`\n"
                    task += "❌ **失败原因**: 端口名称不匹配导致编译失败\n"
                    task += "✅ **强制要求**: \n"
                    task += "   1. 将模块声明中的 `input rst` 改为 `input rst_n`\n"
                    task += "   2. 将复位逻辑中的 `posedge rst` 改为 `negedge rst_n`\n"
                    task += "   3. 将复位条件中的 `if (rst)` 改为 `if (!rst_n)`\n"
                    task += "🔥 **注意**: 这是编译错误，不修复就无法通过测试！\n\n"
                elif "port" in last_errors and "not a port" in last_errors:
                    # 提取端口名
                    import re
                    port_match = re.search(r"port\s+[`'\"]*(\w+)[`'\"]*\s+is not a port", last_errors)
                    if port_match:
                        missing_port = port_match.group(1)
                        task += f"🚨 **端口不匹配错误**:\n"
                        task += f"- 测试台期望端口: `{missing_port}`\n"
                        task += f"- 当前模块接口缺少此端口\n"
                        task += f"- **必须修复**: 在模块接口中添加 `{missing_port}` 端口\n\n"
            
            # 添加错误分析结果
            failure_reasons = enhanced_analysis.get("last_failure_reasons", [])
            if failure_reasons:
                task += "🔍 失败原因分析:\n"
                for reason in failure_reasons:
                    task += f"- {reason}\n"
                task += "\n"
            
            # 添加改进建议
            suggestions = enhanced_analysis.get("improvement_suggestions", [])
            if suggestions:
                task += "💡 改进建议:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    task += f"{i}. {suggestion}\n"
                task += "\n"
            
            # 强调修复要求
            task += "⚠️ **关键要求**: 请严格按照上述错误分析修复接口问题。\n"
            task += "✅ **验证标准**: 确保生成的模块接口与测试台实例化完全匹配。\n\n"
        
        # 🔍 调试日志：输出最终任务内容
        if iteration > 1:
            self.logger.info(f"🔍 DEBUG: 第{iteration}次迭代最终任务内容:")
            self.logger.info(f"🔍 Task length: {len(task)} 字符")
            # 分段输出任务内容，便于查看
            task_lines = task.split('\n')
            for i, line in enumerate(task_lines[:20]):  # 只显示前20行
                self.logger.info(f"🔍 Task L{i+1}: {line}")
            if len(task_lines) > 20:
                self.logger.info(f"🔍 ... (总共 {len(task_lines)} 行)")
        
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