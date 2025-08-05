#!/usr/bin/env python3
"""
改进的LLM协调智能体实现
"""

import json
import time
import logging
import re
from typing import Dict, Any, List, Optional, Set
from enum import Enum

# 导入修复模块
from fixes.improved_tool_detection import ImprovedToolDetection
from fixes.dynamic_system_prompt import DynamicSystemPromptGenerator

class CoordinatorState(Enum):
    """协调器状态"""
    INITIALIZING = "initializing"
    ANALYZING_TASK = "analyzing_task"
    ASSIGNING_TASK = "assigning_task"
    MONITORING_EXECUTION = "monitoring_execution"
    ANALYZING_RESULTS = "analyzing_results"
    PROVIDING_ANSWER = "providing_answer"
    COMPLETED = "completed"
    ERROR = "error"

class ImprovedLLMCoordinator:
    """改进的LLM协调智能体"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.tool_detector = ImprovedToolDetection()
        self.prompt_generator = DynamicSystemPromptGenerator()
        
        # 状态管理
        self.current_state = CoordinatorState.INITIALIZING
        self.task_context = {}
        self.registered_agents = {}
        self.available_tools = {}
        
        # 性能统计
        self.stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "tool_call_successes": 0,
            "tool_call_failures": 0
        }
        
        self.logger.info("🚀 改进的LLM协调智能体初始化完成")
    
    def register_agent(self, agent_id: str, agent_info: Any):
        """注册智能体"""
        self.registered_agents[agent_id] = agent_info
        self.logger.info(f"✅ 注册智能体: {agent_id}")
    
    def register_tool(self, tool_name: str, tool_info: Dict[str, Any]):
        """注册工具"""
        self.available_tools[tool_name] = tool_info
        self.logger.info(f"🔧 注册工具: {tool_name}")
    
    async def coordinate_task(self, user_request: str, **kwargs) -> Dict[str, Any]:
        """
        协调任务执行 - 改进版本
        
        主要改进：
        1. 更robust的工具调用检测
        2. 更好的错误恢复机制
        3. 状态跟踪和监控
        4. 动态System Prompt生成
        """
        task_id = f"task_{int(time.time())}"
        self.current_state = CoordinatorState.ANALYZING_TASK
        
        try:
            self.logger.info(f"🎯 开始协调任务: {task_id}")
            self.stats["total_tasks"] += 1
            
            # 初始化任务上下文
            self.task_context = {
                "task_id": task_id,
                "user_request": user_request,
                "start_time": time.time(),
                "state_history": [CoordinatorState.ANALYZING_TASK],
                "tool_calls": [],
                "agent_results": {},
                "iteration_count": 0,
                "max_iterations": kwargs.get("max_iterations", 10)
            }
            
            # 生成动态System Prompt
            system_prompt = self.prompt_generator.generate_coordination_prompt(
                self.available_tools, 
                self.registered_agents
            )
            
            # 验证System Prompt一致性
            validation = self.prompt_generator.validate_prompt_consistency(
                system_prompt, 
                self.available_tools
            )
            
            if not validation["is_consistent"]:
                self.logger.warning(f"⚠️ System Prompt一致性问题: {validation['issues']}")
            
            # 执行协调循环
            result = await self._execute_coordination_loop(
                user_request, 
                system_prompt,
                **kwargs
            )
            
            # 更新统计
            if result.get("success", False):
                self.stats["successful_tasks"] += 1
                self.current_state = CoordinatorState.COMPLETED
            else:
                self.stats["failed_tasks"] += 1
                self.current_state = CoordinatorState.ERROR
            
            self.logger.info(f"✅ 任务协调完成: {task_id}, 成功: {result.get('success', False)}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 协调任务失败: {str(e)}")
            self.current_state = CoordinatorState.ERROR
            self.stats["failed_tasks"] += 1
            
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "debug_info": {
                    "state": self.current_state.value,
                    "task_context": self.task_context
                }
            }
    
    async def _execute_coordination_loop(self, user_request: str, system_prompt: str, **kwargs) -> Dict[str, Any]:
        """执行协调循环"""
        max_iterations = self.task_context["max_iterations"]
        
        for iteration in range(max_iterations):
            self.task_context["iteration_count"] = iteration + 1
            self.logger.info(f"🔄 协调循环第 {iteration + 1}/{max_iterations} 次迭代")
            
            # 构建当前的协调请求
            coordination_request = self._build_coordination_request(
                user_request, 
                iteration == 0
            )
            
            # 获取LLM响应
            llm_response = await self._get_llm_response(
                system_prompt,
                coordination_request,
                **kwargs
            )
            
            # 改进的工具调用检测
            if not self.tool_detector.has_executed_tools(llm_response):
                self.logger.warning(f"⚠️ 第{iteration + 1}次迭代未检测到有效工具调用")
                
                # 如果是最后一次迭代，尝试强制执行
                if iteration == max_iterations - 1:
                    forced_result = await self._force_tool_execution(user_request)
                    if forced_result:
                        return forced_result
                
                continue
            
            # 提取和执行工具调用
            tool_calls = self.tool_detector.extract_tool_calls(llm_response)
            if not tool_calls:
                self.logger.warning(f"⚠️ 无法提取工具调用: {llm_response[:200]}...")
                continue
            
            # 执行工具调用
            execution_results = await self._execute_tool_calls(tool_calls)
            
            # 分析执行结果
            analysis_result = self._analyze_execution_results(execution_results)
            
            # 检查是否完成任务
            if analysis_result.get("task_completed", False):
                return {
                    "success": True,
                    "task_id": self.task_context["task_id"],
                    "results": execution_results,
                    "analysis": analysis_result,
                    "iterations": iteration + 1
                }
            
            # 更新任务上下文
            self.task_context["tool_calls"].extend(tool_calls)
            self.task_context["agent_results"].update(execution_results)
        
        # 所有迭代完成但任务未完成
        return {
            "success": False,
            "error": "达到最大迭代次数但任务未完成",
            "task_id": self.task_context["task_id"],
            "partial_results": self.task_context["agent_results"],
            "iterations": max_iterations
        }
    
    def _build_coordination_request(self, user_request: str, is_first_iteration: bool) -> str:
        """构建协调请求"""
        if is_first_iteration:
            return f"""
🎯 新任务协调

**用户需求**: {user_request}

**任务ID**: {self.task_context['task_id']}
**当前状态**: {self.current_state.value}

请分析任务需求并开始协调执行。首先调用适当的工具来识别任务类型。
"""
        else:
            # 后续迭代，包含更多上下文
            previous_results = self._summarize_previous_results()
            return f"""
🔄 继续任务协调

**原始需求**: {user_request}
**任务ID**: {self.task_context['task_id']}
**当前迭代**: {self.task_context['iteration_count']}
**当前状态**: {self.current_state.value}

**前期执行情况**:
{previous_results}

请基于前期结果继续协调任务执行。
"""
    
    def _summarize_previous_results(self) -> str:
        """总结前期执行结果"""
        if not self.task_context["agent_results"]:
            return "暂无执行结果"
        
        summary = []
        for agent_id, result in self.task_context["agent_results"].items():
            success = result.get("success", False)
            status = "✅ 成功" if success else "❌ 失败"
            summary.append(f"- {agent_id}: {status}")
            
            if not success and "error" in result:
                summary.append(f"  错误: {result['error'][:100]}...")
        
        return "\n".join(summary)
    
    async def _get_llm_response(self, system_prompt: str, user_request: str, **kwargs) -> str:
        """获取LLM响应（模拟实现）"""
        # 这里应该调用实际的LLM客户端
        # 为了演示，我们返回一个模拟响应
        
        self.logger.info("🤖 发送请求到LLM...")
        
        # 模拟LLM响应时间
        await asyncio.sleep(1)
        
        # 返回模拟的工具调用响应
        return json.dumps({
            "tool_calls": [
                {
                    "tool_name": "identify_task_type",
                    "parameters": {
                        "user_request": user_request
                    }
                }
            ]
        })
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行工具调用"""
        results = {}
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            parameters = tool_call.get("parameters", {})
            
            try:
                self.logger.info(f"🔧 执行工具: {tool_name}")
                
                # 执行工具（这里需要实际的工具执行逻辑）
                result = await self._execute_single_tool(tool_name, parameters)
                results[tool_name] = result
                
                if result.get("success", False):
                    self.stats["tool_call_successes"] += 1
                else:
                    self.stats["tool_call_failures"] += 1
                
            except Exception as e:
                self.logger.error(f"❌ 工具执行失败 {tool_name}: {str(e)}")
                results[tool_name] = {
                    "success": False,
                    "error": str(e)
                }
                self.stats["tool_call_failures"] += 1
        
        return results
    
    async def _execute_single_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具（模拟实现）"""
        # 这里应该调用实际的工具实现
        # 为了演示，我们返回模拟结果
        
        if tool_name == "identify_task_type":
            return {
                "success": True,
                "task_type": "design",
                "confidence": 0.9,
                "suggested_agent": "enhanced_real_verilog_agent"
            }
        elif tool_name == "assign_task_to_agent":
            return {
                "success": True,
                "agent_id": parameters.get("agent_id"),
                "task_assigned": True
            }
        else:
            return {
                "success": False,
                "error": f"未知工具: {tool_name}"
            }
    
    def _analyze_execution_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行结果"""
        analysis = {
            "task_completed": False,
            "success_count": 0,
            "failure_count": 0,
            "next_action": "continue",
            "recommendations": []
        }
        
        for tool_name, result in results.items():
            if result.get("success", False):
                analysis["success_count"] += 1
            else:
                analysis["failure_count"] += 1
        
        # 简单的完成条件检查
        if analysis["success_count"] > 0 and analysis["failure_count"] == 0:
            # 如果所有工具调用都成功，可能需要检查更多条件
            if "assign_task_to_agent" in results:
                analysis["task_completed"] = True
                analysis["next_action"] = "provide_final_answer"
        
        return analysis
    
    async def _force_tool_execution(self, user_request: str) -> Optional[Dict[str, Any]]:
        """强制工具执行（最后的尝试）"""
        self.logger.warning("🚨 尝试强制工具执行")
        
        # 构建最简单的工具调用
        forced_tool_call = {
            "tool_name": "identify_task_type",
            "parameters": {
                "user_request": user_request
            }
        }
        
        try:
            result = await self._execute_single_tool(
                forced_tool_call["tool_name"],
                forced_tool_call["parameters"]
            )
            
            if result.get("success", False):
                return {
                    "success": True,
                    "task_id": self.task_context["task_id"],
                    "results": {"forced_execution": result},
                    "note": "通过强制执行完成"
                }
        except Exception as e:
            self.logger.error(f"❌ 强制执行也失败: {str(e)}")
        
        return None
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        return {
            "current_state": self.current_state.value,
            "task_context": self.task_context,
            "registered_agents": len(self.registered_agents),
            "available_tools": len(self.available_tools),
            "statistics": self.stats,
            "health_score": self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """计算系统健康分数"""
        total_tasks = self.stats["total_tasks"]
        if total_tasks == 0:
            return 1.0
        
        success_rate = self.stats["successful_tasks"] / total_tasks
        tool_call_total = self.stats["tool_call_successes"] + self.stats["tool_call_failures"]
        
        if tool_call_total == 0:
            tool_success_rate = 0.5
        else:
            tool_success_rate = self.stats["tool_call_successes"] / tool_call_total
        
        # 综合评分
        health_score = (success_rate * 0.7) + (tool_success_rate * 0.3)
        return health_score


# 使用示例和测试
async def demonstrate_improved_coordinator():
    """演示改进的协调器使用方法"""
    import asyncio
    
    # 创建协调器
    coordinator = ImprovedLLMCoordinator()
    
    # 注册模拟智能体
    coordinator.register_agent("enhanced_real_verilog_agent", {
        "specialty": "Verilog HDL设计",
        "capabilities": ["code_generation", "module_design"],
        "status": type('Status', (), {'value': 'idle'})()
    })
    
    # 注册模拟工具
    coordinator.register_tool("identify_task_type", {
        "name": "identify_task_type",
        "description": "识别任务类型"
    })
    
    coordinator.register_tool("assign_task_to_agent", {
        "name": "assign_task_to_agent", 
        "description": "分配任务给智能体"
    })
    
    # 执行任务协调
    result = await coordinator.coordinate_task(
        "设计一个4位计数器模块",
        max_iterations=3
    )
    
    print("协调结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 获取状态报告
    status = coordinator.get_status_report()
    print("\n状态报告:")
    print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_improved_coordinator())