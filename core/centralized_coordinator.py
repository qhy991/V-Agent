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
from .response_format import ResponseFormat, StandardizedResponse
from .response_parser import ResponseParser, ResponseParseError
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
        
        # 响应解析器
        self.response_parser = ResponseParser()
        self.preferred_response_format = ResponseFormat.JSON
        
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
Analyze the following task requirements and return a detailed analysis in JSON format.

Task Description: {task_description}

Please analyze the task from the following dimensions:
1. task_type: Type of task (design/testing/review/optimization)
2. complexity: Complexity level (1-10)
3. required_capabilities: Required capabilities (code_generation, test_generation, code_review, etc.)
4. estimated_hours: Estimated work hours
5. priority: Priority level (high/medium/low)
6. dependencies: Task dependencies

Return the analysis in this exact JSON format:
{{
    "task_type": "design",
    "complexity": 7,
    "required_capabilities": ["code_generation", "module_design"],
    "estimated_hours": 12,
    "priority": "high",
    "dependencies": []
}}

Task to analyze: {task_description}
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                temperature=self.coordinator_config.analysis_temperature,
                max_tokens=self.coordinator_config.analysis_max_tokens,
                json_mode=True
            )
            
            analysis = json.loads(response)
            
            # 规范化分析结果，处理可能的中文字段名
            normalized_analysis = self._normalize_task_analysis(analysis)
            
            self.logger.info(f"📊 任务分析完成: 复杂度={normalized_analysis.get('complexity', 'N/A')}")
            return normalized_analysis
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM任务分析失败，使用简单分析: {str(e)}")
            return self._simple_task_analysis(task_description)
    
    def _normalize_task_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """规范化任务分析结果，处理中英文字段名"""
        # 中英文字段名映射
        field_mapping = {
            "任务类型": "task_type",
            "复杂度等级": "complexity", 
            "复杂度": "complexity",
            "需要的能力": "required_capabilities",
            "所需能力": "required_capabilities",
            "预估工作量": "estimated_hours",
            "工作量": "estimated_hours",
            "优先级": "priority",
            "依赖关系": "dependencies"
        }
        
        # 创建规范化的结果
        normalized = {}
        
        for key, value in analysis.items():
            # 检查是否需要映射
            if key in field_mapping:
                normalized[field_mapping[key]] = value
                self.logger.debug(f"🔄 映射字段: {key} -> {field_mapping[key]}")
            else:
                normalized[key] = value
        
        # 确保必需字段存在
        if "task_type" not in normalized:
            normalized["task_type"] = "unknown"
        if "complexity" not in normalized:
            normalized["complexity"] = 5
        if "required_capabilities" not in normalized:
            # 根据任务类型推断能力
            task_type = normalized.get("task_type", "unknown")
            if task_type == "design" or "设计" in str(analysis):
                normalized["required_capabilities"] = ["code_generation", "module_design"]
            elif task_type == "review" or "审查" in str(analysis):
                normalized["required_capabilities"] = ["code_review", "quality_analysis"]
            elif task_type == "testing" or "测试" in str(analysis):
                normalized["required_capabilities"] = ["test_generation", "verification"]
            else:
                normalized["required_capabilities"] = ["code_generation"]
        
        self.logger.info(f"🔧 规范化任务分析: {json.dumps(normalized, ensure_ascii=False)}")
        return normalized
    
    def _simple_task_analysis(self, task_description: str) -> Dict[str, Any]:
        """简单的任务分析（备用方案）"""
        description_lower = task_description.lower()
        
        # DEBUG: Log task description analysis
        self.logger.info(f"🔍 DEBUG: Simple Task Analysis")
        self.logger.info(f"🔍 DEBUG: Task description: '{task_description}'")
        self.logger.info(f"🔍 DEBUG: Description (lowercase): '{description_lower}'")
        
        # 基本分类 - 更精确的任务类型检测，优先级顺序很重要
        task_type = "unknown"
        
        # 审查类关键词优先 - 避免被设计类关键词误识别
        review_keywords = ["审查", "检查", "review", "check", "analyze", "inspect", "examine"]
        testing_keywords = ["测试", "验证", "testbench", "test", "verify", "validation", "simulation"]
        opt_keywords = ["优化", "改进", "提升", "optimize", "improve", "enhance", "refactor"]
        design_keywords = ["设计", "实现", "编写", "生成", "design", "implement", "write", "generate", "create", "build"]
        
        # 优先检测更具体的任务类型
        if any(word in description_lower for word in review_keywords):
            task_type = "review"
            self.logger.info(f"🔍 DEBUG: Detected review keywords: {[w for w in review_keywords if w in description_lower]}")
        elif any(word in description_lower for word in testing_keywords):
            task_type = "testing"
            self.logger.info(f"🔍 DEBUG: Detected testing keywords: {[w for w in testing_keywords if w in description_lower]}")
        elif any(word in description_lower for word in opt_keywords):
            task_type = "optimization"
            self.logger.info(f"🔍 DEBUG: Detected optimization keywords: {[w for w in opt_keywords if w in description_lower]}")
        elif any(word in description_lower for word in design_keywords):
            task_type = "design"
            self.logger.info(f"🔍 DEBUG: Detected design keywords: {[w for w in design_keywords if w in description_lower]}")
        
        self.logger.info(f"🔍 DEBUG: Determined task type: {task_type}")
        
        # 复杂度评估
        complexity = 5  # 默认中等复杂度
        if len(task_description) > 200:
            complexity += 2
        if any(word in description_lower for word in ["32位", "复杂", "多功能", "32bit", "complex", "multi"]):
            complexity += 2
        
        self.logger.info(f"🔍 DEBUG: Calculated complexity: {complexity}")
        
        # 能力需求推断 - 匹配实际存在的能力枚举
        required_capabilities = []
        if task_type == "design":
            required_capabilities = ["code_generation", "module_design"]
        elif task_type == "testing":
            required_capabilities = ["test_generation", "verification"]
        elif task_type == "review":
            required_capabilities = ["code_review", "quality_analysis"]
        elif task_type == "optimization":
            required_capabilities = ["performance_optimization"]
        else:
            required_capabilities = ["code_generation"]  # Default fallback
        
        self.logger.info(f"🔍 DEBUG: Required capabilities: {required_capabilities}")
            
        result = {
            "task_type": task_type,
            "complexity": min(complexity, 10),
            "required_capabilities": required_capabilities,
            "estimated_hours": complexity * 0.5,
            "priority": "medium",
            "dependencies": []
        }
        
        self.logger.info(f"🔍 DEBUG: Final task analysis: {json.dumps(result, indent=2)}")
        return result
    
    async def select_best_agent(self, task_analysis: Dict[str, Any], 
                              exclude_agents: Set[str] = None) -> Optional[str]:
        """选择最适合的智能体"""
        exclude_agents = exclude_agents or set()
        
        self.logger.info(f"🔍 DEBUG: Agent Selection Process Started")
        self.logger.info(f"🔍 DEBUG: Total registered agents: {len(self.registered_agents)}")
        self.logger.info(f"🔍 DEBUG: Excluded agents: {exclude_agents}")
        
        available_agents = {
            agent_id: info for agent_id, info in self.registered_agents.items()
            if agent_id not in exclude_agents and info.status != AgentStatus.FAILED
        }
        
        self.logger.info(f"🔍 DEBUG: Available agents after filtering: {len(available_agents)}")
        self.logger.info(f"🔍 DEBUG: Available agent details:")
        for agent_id, info in available_agents.items():
            self.logger.info(f"  - {agent_id}: status={info.status.value}, capabilities={[cap.value for cap in info.capabilities]}")
        
        if not available_agents:
            self.logger.warning("⚠️ 没有可用的智能体")
            return None
        
        self.logger.info(f"🔍 DEBUG: LLM client available: {self.llm_client is not None}")
        
        if not self.llm_client:
            # 简单选择策略
            self.logger.info(f"🔍 DEBUG: Using simple agent selection strategy")
            return self._simple_agent_selection(task_analysis, available_agents)
        
        # 使用LLM进行智能选择
        self.logger.info(f"🔍 DEBUG: Using LLM agent selection strategy")
        return await self._llm_agent_selection(task_analysis, available_agents)
    
    def _simple_agent_selection(self, task_analysis: Dict[str, Any], 
                              available_agents: Dict[str, AgentInfo]) -> str:
        """简单的智能体选择策略"""
        task_type = task_analysis.get("task_type", "unknown")
        
        self.logger.info(f"🔍 DEBUG: Simple Agent Selection")
        self.logger.info(f"🔍 DEBUG: Task type: {task_type}")
        self.logger.info(f"🔍 DEBUG: Available agents: {list(available_agents.keys())}")
        
        # 按任务类型选择
        if task_type == "design":
            self.logger.info(f"🔍 DEBUG: Looking for agents with CODE_GENERATION capability")
            for agent_id, info in available_agents.items():
                self.logger.info(f"🔍 DEBUG: Checking {agent_id}: {[cap.value for cap in info.capabilities]}")
                if AgentCapability.CODE_GENERATION in info.capabilities:
                    self.logger.info(f"🔍 DEBUG: Selected {agent_id} for design task")
                    return agent_id
        elif task_type == "testing":
            self.logger.info(f"🔍 DEBUG: Looking for agents with TEST_GENERATION capability")
            for agent_id, info in available_agents.items():
                self.logger.info(f"🔍 DEBUG: Checking {agent_id}: {[cap.value for cap in info.capabilities]}")
                if AgentCapability.TEST_GENERATION in info.capabilities:
                    self.logger.info(f"🔍 DEBUG: Selected {agent_id} for testing task")
                    return agent_id
        elif task_type == "review":
            self.logger.info(f"🔍 DEBUG: Looking for agents with CODE_REVIEW capability")
            for agent_id, info in available_agents.items():
                self.logger.info(f"🔍 DEBUG: Checking {agent_id}: {[cap.value for cap in info.capabilities]}")
                if AgentCapability.CODE_REVIEW in info.capabilities:
                    self.logger.info(f"🔍 DEBUG: Selected {agent_id} for review task")
                    return agent_id
        
        # 默认选择第一个可用智能体
        first_agent = list(available_agents.keys())[0]
        self.logger.info(f"🔍 DEBUG: No specific match found, selecting first available agent: {first_agent}")
        return first_agent
    
    async def _llm_agent_selection(self, task_analysis: Dict[str, Any], 
                                 available_agents: Dict[str, AgentInfo]) -> Optional[str]:
        """使用LLM进行智能体选择"""
        agents_info = "\n".join([
            f"- {agent_id}: {info.role} | 能力: {[cap.value for cap in info.capabilities]} | "
            f"专长: {info.specialty_description} | 成功率: {info.success_rate:.2f}"
            for agent_id, info in available_agents.items()
        ])
        
        selection_prompt = f"""
You are a task coordinator selecting the best agent for a specific task. 

TASK ANALYSIS:
- Task Type: {task_analysis.get('task_type', 'unknown')}
- Complexity: {task_analysis.get('complexity', 5)}/10
- Required Capabilities: {task_analysis.get('required_capabilities', [])}

AVAILABLE AGENTS:
{agents_info}

SELECTION RULES:
1. For "design" tasks: Select agents with "code_generation" or "module_design" capabilities
2. For "testing" tasks: Select agents with "test_generation" or "verification" capabilities  
3. For "review" tasks: Select agents with "code_review" or "quality_analysis" capabilities
4. For "optimization" tasks: Select agents with "performance_optimization" capabilities
5. Consider agent success rate (higher is better)
6. Match capabilities to task requirements as closely as possible

RESPONSE FORMAT:
Return ONLY the exact agent_id (case-sensitive) from the available agents list above.
If no agent is suitable, return exactly "none".

Examples:
- If real_verilog_design_agent is available for a design task: real_verilog_design_agent
- If no suitable agent exists: none

Your selection:"""
        
        # DEBUG: Log detailed information before LLM call
        self.logger.info("🔍 DEBUG: LLM Agent Selection Details")
        self.logger.info(f"🔍 DEBUG: Available agents count: {len(available_agents)}")
        self.logger.info(f"🔍 DEBUG: Available agent IDs: {list(available_agents.keys())}")
        
        for agent_id, info in available_agents.items():
            self.logger.info(f"🔍 DEBUG: Agent {agent_id}:")
            self.logger.info(f"  - Role: {info.role}")
            self.logger.info(f"  - Capabilities: {[cap.value for cap in info.capabilities]}")
            self.logger.info(f"  - Status: {info.status.value}")
            self.logger.info(f"  - Specialty: {info.specialty_description}")
            self.logger.info(f"  - Success Rate: {info.success_rate:.2f}")
        
        self.logger.info(f"🔍 DEBUG: Task Analysis: {json.dumps(task_analysis, indent=2)}")
        self.logger.info(f"🔍 DEBUG: Agents Info String:\n{agents_info}")
        self.logger.info(f"🔍 DEBUG: Full Selection Prompt:\n{selection_prompt}")
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=selection_prompt,
                temperature=self.coordinator_config.decision_temperature,
                max_tokens=100
            )
            
            # DEBUG: Log raw LLM response
            self.logger.info(f"🔍 DEBUG: Raw LLM response: '{response}'")
            self.logger.info(f"🔍 DEBUG: Response length: {len(response)}")
            self.logger.info(f"🔍 DEBUG: Response type: {type(response)}")
            
            selected_agent = response.strip().lower()
            self.logger.info(f"🔍 DEBUG: Processed response: '{selected_agent}'")
            
            # DEBUG: Check each available agent ID against the response
            for agent_id in available_agents.keys():
                self.logger.info(f"🔍 DEBUG: Checking '{selected_agent}' == '{agent_id.lower()}': {selected_agent == agent_id.lower()}")
            
            # 验证选择结果
            if selected_agent in available_agents:
                self.logger.info(f"🎯 LLM选择智能体: {selected_agent}")
                return selected_agent
            elif any(selected_agent == agent_id.lower() for agent_id in available_agents.keys()):
                # Handle case-insensitive matching
                for agent_id in available_agents.keys():
                    if selected_agent == agent_id.lower():
                        self.logger.info(f"🎯 LLM选择智能体 (case-insensitive match): {agent_id}")
                        return agent_id
            elif selected_agent == "none":
                self.logger.warning("⚠️ LLM认为没有合适的智能体")
                self.logger.info(f"🔍 DEBUG: This indicates the LLM doesn't think any available agents are suitable for the task")
                return None
            else:
                self.logger.warning(f"⚠️ LLM选择了无效智能体: '{selected_agent}' (Available: {list(available_agents.keys())})")
                self.logger.info(f"🔍 DEBUG: Falling back to simple agent selection")
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
                
                # 3. 解析和处理标准化响应
                parsed_response = await self._process_agent_response(
                    agent_id=current_speaker,
                    raw_response=task_result,
                    task_id=conversation_id
                )
                
                # 4. 记录对话
                conversation_record = ConversationRecord(
                    conversation_id=conversation_id,
                    timestamp=time.time(),
                    speaker_id=current_speaker,
                    receiver_id=self.agent_id,
                    message_content=task_message.content,
                    task_result=parsed_response,
                    file_references=parsed_response.get("file_references", [])
                )
                self.conversation_history.append(conversation_record)
                
                # 5. 收集文件引用
                if parsed_response.get("file_references"):
                    all_file_references.extend(parsed_response["file_references"])
                
                # 6. 检查任务是否完成
                if parsed_response.get("success", False) and parsed_response.get("task_completed", False):
                    task_completed = True
                    self.logger.info(f"✅ 任务完成: {current_speaker}")
                    break
                
                # 7. 决定下一个发言者
                next_speaker = await self._decide_next_speaker(
                    current_result=parsed_response,
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
    
    # ==========================================================================
    # 📝 标准化响应处理
    # ==========================================================================
    
    async def _process_agent_response(self, agent_id: str, raw_response: Dict[str, Any], 
                                    task_id: str) -> Dict[str, Any]:
        """处理智能体响应"""
        try:
            # 1. 检查是否包含标准化响应格式
            standardized_response = None
            response_content = None
            
            # 尝试从响应中提取标准化格式内容
            if "standardized_response" in raw_response:
                response_content = raw_response["standardized_response"]
            elif "formatted_response" in raw_response:
                response_content = raw_response["formatted_response"]
            elif isinstance(raw_response.get("response"), str):
                # 检查响应字符串是否是标准化格式
                response_str = raw_response["response"]
                if self._is_standardized_format(response_str):
                    response_content = response_str
            
            # 2. 解析标准化响应
            if response_content:
                try:
                    standardized_response = self.response_parser.parse_response(response_content)
                    self.logger.info(f"✅ 成功解析标准化响应: {agent_id}")
                except ResponseParseError as e:
                    self.logger.warning(f"⚠️ 标准化响应解析失败 {agent_id}: {str(e)}")
                    standardized_response = None
            
            # 3. 转换为统一格式
            if standardized_response:
                return self._convert_standardized_to_internal(standardized_response, raw_response)
            else:
                return self._convert_legacy_to_internal(raw_response, agent_id, task_id)
                
        except Exception as e:
            self.logger.error(f"❌ 响应处理失败 {agent_id}: {str(e)}")
            return self._create_error_response(raw_response, str(e))
    
    def _is_standardized_format(self, content: str) -> bool:
        """检查内容是否是标准化格式"""
        content_stripped = content.strip()
        
        # 检查JSON格式
        if content_stripped.startswith('{') and '"agent_name"' in content:
            return True
        
        # 检查XML格式
        if content_stripped.startswith('<agent_response>'):
            return True
        
        # 检查Markdown格式
        if '# Agent Response:' in content:
            return True
        
        return False
    
    def _convert_standardized_to_internal(self, standardized_response: StandardizedResponse, 
                                        raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """将标准化响应转换为内部格式"""
        # 转换文件引用
        file_references = []
        for file_ref in (standardized_response.generated_files + 
                        standardized_response.modified_files + 
                        standardized_response.reference_files):
            file_references.append(FileReference(
                file_path=file_ref.path,
                file_type=file_ref.file_type,
                description=file_ref.description,
                metadata={
                    "created_at": file_ref.created_at,
                    "size_bytes": file_ref.size_bytes
                }
            ))
        
        # 确定任务状态
        success = standardized_response.status.value in ['success', 'partial_success']
        task_completed = standardized_response.status.value == 'success' and standardized_response.completion_percentage >= 100.0
        
        return {
            "success": success,
            "task_completed": task_completed,
            "agent_id": standardized_response.agent_id,
            "agent_name": standardized_response.agent_name,
            "message": standardized_response.message,
            "status": standardized_response.status.value,
            "completion_percentage": standardized_response.completion_percentage,
            "file_references": file_references,
            "issues": [issue.to_dict() for issue in standardized_response.issues],
            "quality_metrics": standardized_response.quality_metrics.to_dict() if standardized_response.quality_metrics else None,
            "next_steps": standardized_response.next_steps,
            "metadata": standardized_response.metadata,
            "error": None if success else f"Task failed: {standardized_response.message}",
            "raw_response": raw_response,
            "response_type": standardized_response.response_type.value,
            "timestamp": standardized_response.timestamp
        }
    
    def _convert_legacy_to_internal(self, raw_response: Dict[str, Any], 
                                  agent_id: str, task_id: str) -> Dict[str, Any]:
        """将传统响应转换为内部格式"""
        self.logger.info(f"📄 使用传统响应格式: {agent_id}")
        
        # 提取基本信息
        success = raw_response.get("success", False)
        message = raw_response.get("message", raw_response.get("response", "No message"))
        error = raw_response.get("error")
        
        # 处理文件引用
        file_references = []
        if "file_references" in raw_response:
            for ref in raw_response["file_references"]:
                if isinstance(ref, dict):
                    file_references.append(FileReference(
                        file_path=ref.get("file_path", ""),
                        file_type=ref.get("file_type", "unknown"),
                        description=ref.get("description", ""),
                        metadata=ref.get("metadata", {})
                    ))
        
        # 检查生成的文件
        if "generated_files" in raw_response:
            for file_path in raw_response["generated_files"]:
                file_references.append(FileReference(
                    file_path=file_path,
                    file_type=self._detect_file_type(file_path),
                    description=f"Generated file by {agent_id}",
                    metadata={"generated_by": agent_id}
                ))
        
        return {
            "success": success,
            "task_completed": success,  # 简单假设成功即完成
            "agent_id": agent_id,
            "agent_name": raw_response.get("agent_name", agent_id),
            "message": message,
            "status": "success" if success else "failed",
            "completion_percentage": 100.0 if success else 0.0,
            "file_references": file_references,
            "issues": [],
            "quality_metrics": None,
            "next_steps": [],
            "metadata": {"legacy_response": True},
            "error": error,
            "raw_response": raw_response,
            "response_type": "task_completion",
            "timestamp": str(time.time())
        }
    
    def _create_error_response(self, raw_response: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "task_completed": False,
            "agent_id": "unknown",
            "agent_name": "Unknown",
            "message": f"Response processing failed: {error_message}",
            "status": "failed",
            "completion_percentage": 0.0,
            "file_references": [],
            "issues": [{"issue_type": "error", "severity": "high", "description": error_message}],
            "quality_metrics": None,
            "next_steps": ["Fix response format"],
            "metadata": {"processing_error": True},
            "error": error_message,
            "raw_response": raw_response,
            "response_type": "error_report",
            "timestamp": str(time.time())
        }
    
    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        if file_path.endswith('.v'):
            return 'verilog'
        elif file_path.endswith('_tb.v') or 'testbench' in file_path.lower():
            return 'testbench'
        elif file_path.endswith('.json'):
            return 'json'
        elif file_path.endswith('.md'):
            return 'documentation'
        elif file_path.endswith('.txt'):
            return 'text'
        else:
            return 'unknown'
    
    def set_preferred_response_format(self, format_type: ResponseFormat):
        """设置首选响应格式"""
        self.preferred_response_format = format_type
        self.logger.info(f"📝 设置首选响应格式: {format_type.value}")
    
    def get_response_format_instructions(self) -> str:
        """获取响应格式说明"""
        if self.preferred_response_format == ResponseFormat.JSON:
            return """
请使用以下JSON格式返回响应：
{
  "agent_name": "your_agent_class_name",
  "agent_id": "your_agent_id", 
  "status": "success|failed|in_progress",
  "completion_percentage": 0-100,
  "message": "main response message",
  "generated_files": [{"path": "...", "file_type": "...", "description": "..."}],
  "issues": [{"issue_type": "...", "severity": "...", "description": "..."}],
  "next_steps": ["step1", "step2"]
}
"""
        elif self.preferred_response_format == ResponseFormat.MARKDOWN:
            return """
请使用以下Markdown格式返回响应：
# Agent Response: YourAgentName
## 📋 Basic Information
- **Agent**: YourAgentName (`agent_id`)
- **Status**: success/failed/in_progress
- **Progress**: X.X%
## 💬 Message
Your main response message here
## 📁 Files
### Generated Files
- **path/to/file.v** (verilog): Description
"""
        else:
            return "请返回结构化的响应信息"
    
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
