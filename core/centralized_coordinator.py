#!/usr/bin/env python3
"""
中心化协调智能体

Centralized Coordinator Agent for Multi-Agent Framework
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from .base_agent import BaseAgent, TaskMessage, FileReference
from .enums import AgentCapability, AgentStatus, ConversationState
from config.config import FrameworkConfig, CoordinatorConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    role: str
    capabilities: Set[AgentCapability]
    status: AgentStatus
    specialty_description: str
    last_activity: float = 0.0
    task_count: int = 0
    success_rate: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": [cap.value for cap in self.capabilities],
            "status": self.status.value,
            "specialty_description": self.specialty_description,
            "last_activity": self.last_activity,
            "task_count": self.task_count,
            "success_rate": self.success_rate
        }


@dataclass
class ConversationRecord:
    """对话记录"""
    conversation_id: str
    timestamp: float
    speaker_id: str
    receiver_id: str
    message_content: str
    task_result: Optional[Dict[str, Any]] = None
    file_references: List[FileReference] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp,
            "speaker_id": self.speaker_id,
            "receiver_id": self.receiver_id,
            "message_content": self.message_content,
            "task_result": self.task_result,
            "file_references": [ref.to_dict() for ref in (self.file_references or [])]
        }


class CentralizedCoordinator(BaseAgent):
    """
    中心化协调智能体 - 系统的大脑
    
    职责：
    1. 维护全局状态和团队信息
    2. 分析任务并选择合适的智能体
    3. 动态决策NextSpeaker
    4. 处理智能体返回的信息
    5. 协调整个工作流程
    """
    
    def __init__(self, framework_config: FrameworkConfig, 
                 llm_client: EnhancedLLMClient = None):
        super().__init__(
            agent_id="centralized_coordinator",
            role="coordinator",
            capabilities={AgentCapability.TASK_COORDINATION, 
                         AgentCapability.WORKFLOW_MANAGEMENT}
        )
        
        self.framework_config = framework_config
        self.coordinator_config = framework_config.coordinator
        self.llm_client = llm_client
        
        # 团队管理
        self.registered_agents: Dict[str, AgentInfo] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        
        # 对话管理
        self.conversation_history: List[ConversationRecord] = []
        self.current_conversation_id = None
        self.conversation_state = ConversationState.IDLE
        
        # 任务管理
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_results: Dict[str, List[Dict[str, Any]]] = {}
        
        # 工作流程控制
        self.max_conversation_iterations = self.coordinator_config.max_conversation_iterations
        self.conversation_timeout = self.coordinator_config.conversation_timeout
        
        self.logger.info("🧠 中心化协调智能体初始化完成")
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取协调者能力"""
        return {AgentCapability.TASK_COORDINATION, 
                AgentCapability.WORKFLOW_MANAGEMENT}
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "中心化协调智能体，负责任务分析、智能体选择和工作流程协调"
    
    # ==========================================================================
    # 🤝 团队管理
    # ==========================================================================
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体"""
        try:
            agent_info = AgentInfo(
                agent_id=agent.agent_id,
                role=agent.role,
                capabilities=agent.get_capabilities(),
                status=AgentStatus.IDLE,
                specialty_description=agent.get_specialty_description(),
                last_activity=time.time()
            )
            
            self.registered_agents[agent.agent_id] = agent_info
            self.agent_instances[agent.agent_id] = agent
            
            self.logger.info(f"✅ 智能体注册成功: {agent.agent_id} ({agent.role})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 智能体注册失败 {agent.agent_id}: {str(e)}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            if agent_id in self.agent_instances:
                del self.agent_instances[agent_id]
            self.logger.info(f"🗑️ 智能体注销成功: {agent_id}")
            return True
        return False
    
    def get_team_status(self) -> Dict[str, Any]:
        """获取团队状态"""
        return {
            "total_agents": len(self.registered_agents),
            "active_agents": len([info for info in self.registered_agents.values() 
                                if info.status == AgentStatus.WORKING]),
            "idle_agents": len([info for info in self.registered_agents.values() 
                              if info.status == AgentStatus.IDLE]),
            "agents": {agent_id: info.to_dict() 
                      for agent_id, info in self.registered_agents.items()},
            "conversation_state": self.conversation_state.value,
            "active_tasks": len(self.active_tasks)
        }
    
    # ==========================================================================
    # 🎯 任务分析和智能体选择
    # ==========================================================================
    
    async def analyze_task_requirements(self, task_description: str, 
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析任务需求"""
        if not self.llm_client:
            # 简单的规则分析
            return self._simple_task_analysis(task_description)
        
        # 使用LLM进行深度分析
        analysis_prompt = f"""
请分析以下任务的详细需求：

任务描述: {task_description}

请从以下维度分析任务：
1. 任务类型 (设计/测试/审查/优化等)
2. 复杂度等级 (1-10)
3. 需要的能力 (代码生成/测试生成/代码审查等)
4. 预估工作量 (小时)
5. 优先级 (高/中/低)
6. 依赖关系

请以JSON格式返回分析结果。
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                temperature=self.coordinator_config.analysis_temperature,
                max_tokens=self.coordinator_config.analysis_max_tokens,
                json_mode=True
            )
            
            analysis = json.loads(response)
            self.logger.info(f"📊 任务分析完成: 复杂度={analysis.get('complexity', 'N/A')}")
            return analysis
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM任务分析失败，使用简单分析: {str(e)}")
            return self._simple_task_analysis(task_description)
    
    def _simple_task_analysis(self, task_description: str) -> Dict[str, Any]:
        """简单的任务分析（备用方案）"""
        description_lower = task_description.lower()
        
        # 基本分类
        task_type = "unknown"
        if any(word in description_lower for word in ["设计", "实现", "编写", "生成"]):
            task_type = "design"
        elif any(word in description_lower for word in ["测试", "验证", "testbench"]):
            task_type = "testing"
        elif any(word in description_lower for word in ["审查", "检查", "review"]):
            task_type = "review"
        elif any(word in description_lower for word in ["优化", "改进", "提升"]):
            task_type = "optimization"
        
        # 复杂度评估
        complexity = 5  # 默认中等复杂度
        if len(task_description) > 200:
            complexity += 2
        if any(word in description_lower for word in ["32位", "复杂", "多功能"]):
            complexity += 2
            
        return {
            "task_type": task_type,
            "complexity": min(complexity, 10),
            "required_capabilities": ["code_generation"],
            "estimated_hours": complexity * 0.5,
            "priority": "medium",
            "dependencies": []
        }
    
    async def select_best_agent(self, task_analysis: Dict[str, Any], 
                              exclude_agents: Set[str] = None) -> Optional[str]:
        """选择最适合的智能体"""
        exclude_agents = exclude_agents or set()
        available_agents = {
            agent_id: info for agent_id, info in self.registered_agents.items()
            if agent_id not in exclude_agents and info.status != AgentStatus.FAILED
        }
        
        if not available_agents:
            self.logger.warning("⚠️ 没有可用的智能体")
            return None
        
        if not self.llm_client:
            # 简单选择策略
            return self._simple_agent_selection(task_analysis, available_agents)
        
        # 使用LLM进行智能选择
        return await self._llm_agent_selection(task_analysis, available_agents)
    
    def _simple_agent_selection(self, task_analysis: Dict[str, Any], 
                              available_agents: Dict[str, AgentInfo]) -> str:
        """简单的智能体选择策略"""
        task_type = task_analysis.get("task_type", "unknown")
        
        # 按任务类型选择
        if task_type == "design":
            for agent_id, info in available_agents.items():
                if AgentCapability.CODE_GENERATION in info.capabilities:
                    return agent_id
        elif task_type == "testing":
            for agent_id, info in available_agents.items():
                if AgentCapability.TEST_GENERATION in info.capabilities:
                    return agent_id
        elif task_type == "review":
            for agent_id, info in available_agents.items():
                if AgentCapability.CODE_REVIEW in info.capabilities:
                    return agent_id
        
        # 默认选择第一个可用智能体
        return list(available_agents.keys())[0]
    
    async def _llm_agent_selection(self, task_analysis: Dict[str, Any], 
                                 available_agents: Dict[str, AgentInfo]) -> Optional[str]:
        """使用LLM进行智能体选择"""
        agents_info = "\n".join([
            f"- {agent_id}: {info.role} | 能力: {[cap.value for cap in info.capabilities]} | "
            f"专长: {info.specialty_description} | 成功率: {info.success_rate:.2f}"
            for agent_id, info in available_agents.items()
        ])
        
        selection_prompt = f"""
根据任务分析结果，从可用智能体中选择最适合的一个：

任务分析:
- 类型: {task_analysis.get('task_type', 'unknown')}
- 复杂度: {task_analysis.get('complexity', 5)}
- 需要能力: {task_analysis.get('required_capabilities', [])}

可用智能体:
{agents_info}

请选择最适合的智能体ID，只返回agent_id，不要其他内容。
如果没有合适的智能体，返回"none"。
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=selection_prompt,
                temperature=self.coordinator_config.decision_temperature,
                max_tokens=100
            )
            
            selected_agent = response.strip().lower()
            
            # 验证选择结果
            if selected_agent in available_agents:
                self.logger.info(f"🎯 LLM选择智能体: {selected_agent}")
                return selected_agent
            elif selected_agent == "none":
                self.logger.warning("⚠️ LLM认为没有合适的智能体")
                return None
            else:
                self.logger.warning(f"⚠️ LLM选择了无效智能体: {selected_agent}，使用简单策略")
                return self._simple_agent_selection(task_analysis, available_agents)
                
        except Exception as e:
            self.logger.warning(f"⚠️ LLM智能体选择失败，使用简单策略: {str(e)}")
            return self._simple_agent_selection(task_analysis, available_agents)
    
    # ==========================================================================
    # 💬 对话协调
    # ==========================================================================
    
    async def coordinate_task_execution(self, initial_task: str, 
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """协调任务执行"""
        self.conversation_state = ConversationState.ACTIVE
        conversation_id = f"conv_{int(time.time())}"
        self.current_conversation_id = conversation_id
        
        self.logger.info(f"🚀 开始任务协调: {conversation_id}")
        
        try:
            # 1. 分析任务
            task_analysis = await self.analyze_task_requirements(initial_task, context)
            
            # 2. 选择初始智能体
            selected_agent_id = await self.select_best_agent(task_analysis)
            if not selected_agent_id:
                return {
                    "success": False,
                    "error": "没有找到合适的智能体",
                    "conversation_id": conversation_id
                }
            
            # 3. 开始多轮对话
            conversation_results = await self._execute_multi_round_conversation(
                conversation_id=conversation_id,
                initial_task=initial_task,
                initial_agent_id=selected_agent_id,
                task_analysis=task_analysis
            )
            
            self.conversation_state = ConversationState.COMPLETED
            return conversation_results
            
        except Exception as e:
            self.conversation_state = ConversationState.FAILED
            self.logger.error(f"❌ 任务协调失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    async def _execute_multi_round_conversation(self, conversation_id: str, 
                                              initial_task: str, initial_agent_id: str,
                                              task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行多轮对话"""
        conversation_start = time.time()
        current_speaker = initial_agent_id
        iteration_count = 0
        all_file_references = []
        task_completed = False
        
        self.logger.info(f"💬 启动多轮对话: {conversation_id}")
        
        while (iteration_count < self.max_conversation_iterations and 
               time.time() - conversation_start < self.conversation_timeout and
               not task_completed):
            
            iteration_count += 1
            self.logger.info(f"🔄 对话轮次 {iteration_count}: {current_speaker} 发言")
            
            try:
                # 1. 构建任务消息
                task_message = TaskMessage(
                    task_id=conversation_id,
                    sender_id=self.agent_id,
                    receiver_id=current_speaker,
                    message_type="task_execution",
                    content=initial_task if iteration_count == 1 else "继续处理任务",
                    file_references=all_file_references[-5:] if all_file_references else None,  # 最近5个文件
                    metadata={"iteration": iteration_count, "task_analysis": task_analysis}
                )
                
                # 2. 智能体执行任务
                agent_instance = self.agent_instances[current_speaker]
                task_result = await agent_instance.process_task_with_file_references(task_message)
                
                # 3. 记录对话
                conversation_record = ConversationRecord(
                    conversation_id=conversation_id,
                    timestamp=time.time(),
                    speaker_id=current_speaker,
                    receiver_id=self.agent_id,
                    message_content=task_message.content,
                    task_result=task_result,
                    file_references=task_result.get("file_references", [])
                )
                self.conversation_history.append(conversation_record)
                
                # 4. 收集文件引用
                if task_result.get("file_references"):
                    all_file_references.extend(task_result["file_references"])
                
                # 5. 检查任务是否完成
                if task_result.get("success", False) and task_result.get("task_completed", False):
                    task_completed = True
                    self.logger.info(f"✅ 任务完成: {current_speaker}")
                    break
                
                # 6. 决定下一个发言者
                next_speaker = await self._decide_next_speaker(
                    current_result=task_result,
                    conversation_history=self.conversation_history[-3:],  # 最近3轮
                    task_analysis=task_analysis
                )
                
                if next_speaker == current_speaker or not next_speaker:
                    # 没有更好的选择，继续当前智能体
                    self.logger.info(f"📍 继续使用当前智能体: {current_speaker}")
                else:
                    current_speaker = next_speaker
                    self.logger.info(f"🔄 切换到智能体: {current_speaker}")
                
            except Exception as e:
                self.logger.error(f"❌ 对话轮次 {iteration_count} 失败: {str(e)}")
                break
        
        # 生成最终结果
        total_duration = time.time() - conversation_start
        return {
            "success": task_completed,
            "conversation_id": conversation_id,
            "total_iterations": iteration_count,
            "duration": total_duration,
            "file_references": all_file_references,
            "conversation_history": [record.to_dict() for record in self.conversation_history[-iteration_count:]],
            "final_speaker": current_speaker,
            "task_analysis": task_analysis
        }
    
    async def _decide_next_speaker(self, current_result: Dict[str, Any],
                                 conversation_history: List[ConversationRecord],
                                 task_analysis: Dict[str, Any]) -> Optional[str]:
        """决定下一个发言者"""
        if not self.llm_client:
            return self._simple_next_speaker_decision(current_result)
        
        # 构建上下文信息
        history_summary = "\n".join([
            f"- {record.speaker_id}: {record.message_content[:100]}... "
            f"(成功: {record.task_result.get('success', False) if record.task_result else False})"
            for record in conversation_history
        ])
        
        available_agents = "\n".join([
            f"- {agent_id}: {info.role} | 能力: {[cap.value for cap in info.capabilities]}"
            for agent_id, info in self.registered_agents.items()
            if info.status != AgentStatus.FAILED
        ])
        
        decision_prompt = f"""
基于当前任务执行情况，决定下一个最适合的智能体：

任务分析:
- 类型: {task_analysis.get('task_type', 'unknown')}
- 复杂度: {task_analysis.get('complexity', 5)}

当前执行结果:
- 成功: {current_result.get('success', False)}
- 错误: {current_result.get('error', 'None')}
- 生成文件: {len(current_result.get('file_references', []))}

对话历史:
{history_summary}

可用智能体:
{available_agents}

请选择下一个最适合的智能体ID，只返回agent_id。
如果当前智能体应该继续，返回"continue"。
如果任务已完成，返回"complete"。
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=decision_prompt,
                temperature=self.coordinator_config.decision_temperature,
                max_tokens=self.coordinator_config.decision_max_tokens
            )
            
            decision = response.strip().lower()
            
            if decision == "continue":
                return None  # 继续当前智能体
            elif decision == "complete":
                return None  # 任务完成
            elif decision in self.registered_agents:
                return decision
            else:
                self.logger.warning(f"⚠️ LLM返回无效决策: {decision}")
                return None
                
        except Exception as e:
            self.logger.warning(f"⚠️ NextSpeaker决策失败: {str(e)}")
            return self._simple_next_speaker_decision(current_result)
    
    def _simple_next_speaker_decision(self, current_result: Dict[str, Any]) -> Optional[str]:
        """简单的下一个发言者决策"""
        # 如果当前任务成功，可能需要测试智能体
        if current_result.get("success", False):
            for agent_id, info in self.registered_agents.items():
                if (AgentCapability.TEST_GENERATION in info.capabilities and 
                    info.status == AgentStatus.IDLE):
                    return agent_id
        
        return None  # 继续当前智能体
    
    # ==========================================================================
    # 📊 状态和统计
    # ==========================================================================
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """协调者的增强任务执行"""
        return await self.coordinate_task_execution(
            initial_task=enhanced_prompt,
            context={"original_message": original_message.to_dict(), 
                    "file_contents": file_contents}
        )
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """获取对话统计"""
        total_conversations = len(set(record.conversation_id for record in self.conversation_history))
        total_rounds = len(self.conversation_history)
        
        agent_activity = {}
        for record in self.conversation_history:
            agent_id = record.speaker_id
            if agent_id not in agent_activity:
                agent_activity[agent_id] = {"rounds": 0, "successes": 0}
            agent_activity[agent_id]["rounds"] += 1
            if record.task_result and record.task_result.get("success", False):
                agent_activity[agent_id]["successes"] += 1
        
        return {
            "total_conversations": total_conversations,
            "total_rounds": total_rounds,
            "average_rounds_per_conversation": total_rounds / max(total_conversations, 1),
            "agent_activity": agent_activity,
            "current_state": self.conversation_state.value,
            "team_status": self.get_team_status()
        }
    
    def save_conversation_log(self, output_path: str = None) -> str:
        """保存对话日志"""
        if not output_path:
            timestamp = int(time.time())
            output_path = f"conversation_log_{timestamp}.json"
        
        log_data = {
            "coordinator_id": self.agent_id,
            "timestamp": time.time(),
            "conversation_history": [record.to_dict() for record in self.conversation_history],
            "team_status": self.get_team_status(),
            "statistics": self.get_conversation_statistics()
        }
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"💾 对话日志已保存: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ 保存对话日志失败: {str(e)}")
            raise
