#!/usr/bin/env python3
"""
增强中心化协调智能体 - 支持Schema系统

Enhanced Centralized Coordinator Agent with Schema System Support
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass
from pathlib import Path

from .centralized_coordinator import CentralizedCoordinator, AgentInfo, ConversationRecord
from .base_agent import BaseAgent
from .types import TaskMessage, FileReference
from .schema_system.enhanced_base_agent import EnhancedBaseAgent
from .enums import AgentCapability, AgentStatus, ConversationState
from .response_format import ResponseFormat, StandardizedResponse
from .response_parser import ResponseParser, ResponseParseError
from config.config import FrameworkConfig, CoordinatorConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient


@dataclass
class EnhancedAgentInfo(AgentInfo):
    """增强智能体信息 - 包含Schema系统信息"""
    schema_enabled: bool = False
    enhanced_tools_count: int = 0
    validation_statistics: Dict[str, Any] = None
    schema_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schema_enabled": self.schema_enabled,
            "enhanced_tools_count": self.enhanced_tools_count,
            "validation_statistics": self.validation_statistics or {},
            "schema_version": self.schema_version
        })
        return base_dict


class EnhancedCentralizedCoordinator(CentralizedCoordinator):
    """
    增强中心化协调智能体 - 支持Schema系统
    
    新增功能：
    1. 支持增强智能体(EnhancedBaseAgent)的注册和管理
    2. Schema系统统计和监控
    3. 智能体选择时考虑Schema能力
    4. 增强的任务分发和结果处理
    """
    
    def __init__(self, framework_config: FrameworkConfig, 
                 llm_client: EnhancedLLMClient = None):
        super().__init__(framework_config, llm_client)
        
        # Schema系统支持
        self.schema_system_enabled = getattr(framework_config, 'schema', {}).get('enabled', True)
        self.enhanced_agents: Dict[str, EnhancedAgentInfo] = {}
        
        # Schema统计信息
        self.global_schema_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "total_repairs": 0,
            "successful_repairs": 0,
            "cache_hits": 0,
            "last_updated": time.time()
        }
        
        self.logger.info("🧠⚡ 增强中心化协调智能体初始化完成 - Schema系统支持已启用")
    
    # ==========================================================================
    # 🤝 增强团队管理
    # ==========================================================================
    
    def register_agent(self, agent: Union[BaseAgent, EnhancedBaseAgent]) -> bool:
        """注册智能体 - 支持增强智能体"""
        try:
            # 检测是否为增强智能体
            is_enhanced = isinstance(agent, EnhancedBaseAgent)
            
            # 获取基本信息
            base_info = {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "capabilities": agent.get_capabilities(),
                "status": AgentStatus.IDLE,
                "specialty_description": agent.get_specialty_description(),
                "last_activity": time.time()
            }
            
            if is_enhanced:
                # 获取Schema相关信息
                try:
                    validation_stats = agent.get_validation_statistics()
                    enhanced_tools = agent.list_enhanced_tools()
                    
                    agent_info = EnhancedAgentInfo(
                        **base_info,
                        schema_enabled=True,
                        enhanced_tools_count=len(enhanced_tools),
                        validation_statistics=validation_stats,
                        schema_version="1.0"
                    )
                    
                    self.enhanced_agents[agent.agent_id] = agent_info
                    self.logger.info(f"✅⚡ 增强智能体注册成功: {agent.agent_id} ({agent.role}) - Schema工具: {len(enhanced_tools)}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 增强智能体 {agent.agent_id} Schema信息获取失败: {str(e)}")
                    # 降级到普通智能体注册
                    is_enhanced = False
            
            if not is_enhanced:
                # 普通智能体注册
                agent_info = AgentInfo(**base_info)
                self.logger.info(f"✅ 普通智能体注册成功: {agent.agent_id} ({agent.role})")
            
            # 通用注册逻辑
            self.registered_agents[agent.agent_id] = agent_info
            self.agent_instances[agent.agent_id] = agent
            
            # 更新全局统计
            self._update_global_schema_stats()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 智能体注册失败 {agent.agent_id}: {str(e)}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体 - 增强版本"""
        success = super().unregister_agent(agent_id)
        
        if success and agent_id in self.enhanced_agents:
            del self.enhanced_agents[agent_id]
            self.logger.info(f"🗑️⚡ 增强智能体注销成功: {agent_id}")
            self._update_global_schema_stats()
        
        return success
    
    def get_enhanced_team_status(self) -> Dict[str, Any]:
        """获取增强团队状态 - 包含Schema信息"""
        base_status = self.get_team_status()
        
        # 增强统计信息
        enhanced_count = len(self.enhanced_agents)
        total_enhanced_tools = sum(info.enhanced_tools_count for info in self.enhanced_agents.values())
        
        # Schema系统统计
        schema_stats = self.global_schema_stats.copy()
        
        base_status.update({
            "enhanced_agents_count": enhanced_count,
            "total_enhanced_tools": total_enhanced_tools,
            "schema_system_enabled": self.schema_system_enabled,
            "schema_statistics": schema_stats,
            "enhanced_agents": {
                agent_id: info.to_dict() 
                for agent_id, info in self.enhanced_agents.items()
            }
        })
        
        return base_status
    
    # ==========================================================================
    # 🎯 增强任务分析和智能体选择
    # ==========================================================================
    
    async def select_best_agent_enhanced(self, task_analysis: Dict[str, Any], 
                                       exclude_agents: Set[str] = None,
                                       prefer_enhanced: bool = True,
                                       context: Dict[str, Any] = None) -> Optional[str]:
        """选择最适合的智能体 - 增强版本，优先考虑Schema能力"""
        exclude_agents = exclude_agents or set()
        context = context or {}
        
        # 处理强制任务类型和首选智能体角色
        if "force_task_type" in context and "preferred_agent_role" in context:
            preferred_role = context["preferred_agent_role"]
            self.logger.info(f"🎯 强制任务类型: {context['force_task_type']}, 首选角色: {preferred_role}")
            
            # 查找具有首选角色的智能体
            for agent_id, agent_info in self.registered_agents.items():
                if agent_id not in exclude_agents and agent_info.role == preferred_role:
                    self.logger.info(f"✅⚡ 选择首选角色智能体: {agent_id} (角色: {preferred_role})")
                    return agent_id
        
        self.logger.info(f"🔍⚡ 增强智能体选择开始")
        self.logger.info(f"🔍 总注册智能体: {len(self.registered_agents)}, 增强智能体: {len(self.enhanced_agents)}")
        self.logger.info(f"🔍 优先选择增强智能体: {prefer_enhanced}")
        
        available_agents = {
            agent_id: info for agent_id, info in self.registered_agents.items()
            if agent_id not in exclude_agents and info.status != AgentStatus.FAILED
        }
        
        if not available_agents:
            self.logger.warning("⚠️ 没有可用的智能体")
            return None
        
        # 如果优先选择增强智能体且存在增强智能体
        if prefer_enhanced and self.enhanced_agents:
            enhanced_available = {
                agent_id: info for agent_id, info in available_agents.items()
                if agent_id in self.enhanced_agents
            }
            
            if enhanced_available:
                self.logger.info(f"🔍⚡ 在 {len(enhanced_available)} 个增强智能体中选择")
                selected = await self._select_from_enhanced_agents(task_analysis, enhanced_available)
                if selected:
                    return selected
        
        # 降级到普通选择逻辑
        self.logger.info(f"🔍 降级到普通智能体选择")
        return await super().select_best_agent(task_analysis, exclude_agents)
    
    async def _select_from_enhanced_agents(self, task_analysis: Dict[str, Any], 
                                         enhanced_agents: Dict[str, AgentInfo]) -> Optional[str]:
        """从增强智能体中选择"""
        task_type = task_analysis.get("task_type", "unknown")
        
        # 智能体评分系统
        agent_scores = {}
        
        for agent_id, agent_info in enhanced_agents.items():
            score = 0.0
            enhanced_info = self.enhanced_agents.get(agent_id)
            
            # 基础能力匹配分数
            required_capabilities = set(task_analysis.get("required_capabilities", []))
            agent_capabilities = {cap.value for cap in agent_info.capabilities}
            
            capability_match = len(required_capabilities.intersection(agent_capabilities))
            if required_capabilities:
                score += (capability_match / len(required_capabilities)) * 40
            
            # Schema系统加分
            if enhanced_info and enhanced_info.schema_enabled:
                score += 20  # Schema系统加分
                
                # 工具丰富度加分
                if enhanced_info.enhanced_tools_count > 0:
                    score += min(enhanced_info.enhanced_tools_count * 2, 15)
                
                # 验证成功率加分
                if enhanced_info.validation_statistics:
                    success_rate = enhanced_info.validation_statistics.get('success_rate', 0)
                    score += success_rate * 10
            
            # 成功率加分
            score += agent_info.success_rate * 15
            
            agent_scores[agent_id] = score
            
            self.logger.info(f"🔍 智能体评分: {agent_id} = {score:.1f}")
        
        # 选择得分最高的智能体
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            self.logger.info(f"✅⚡ 选择增强智能体: {best_agent[0]} (得分: {best_agent[1]:.1f})")
            return best_agent[0]
        
        return None
    
    # ==========================================================================
    # 🔄 增强任务执行
    # ==========================================================================
    
    async def execute_task_with_enhanced_agent(self, task_message: TaskMessage, 
                                             agent_id: str = None) -> Dict[str, Any]:
        """使用增强智能体执行任务"""
        try:
            # 任务分析
            task_analysis = await self.analyze_task_requirements(task_message.content)
            
            # 选择智能体
            if not agent_id:
                agent_id = await self.select_best_agent_enhanced(task_analysis)
            
            if not agent_id:
                return {
                    "success": False,
                    "error": "没有可用的智能体",
                    "task_id": task_message.task_id
                }
            
            # 获取智能体实例
            agent = self.agent_instances.get(agent_id)
            if not agent:
                return {
                    "success": False,
                    "error": f"智能体 {agent_id} 未找到",
                    "task_id": task_message.task_id
                }
            
            # 更新智能体状态
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.WORKING
                self.registered_agents[agent_id].last_activity = time.time()
            
            self.logger.info(f"🚀⚡ 开始执行增强任务: {task_message.task_id} -> {agent_id}")
            
            # 根据智能体类型选择执行方法
            if isinstance(agent, EnhancedBaseAgent):
                # 使用增强执行方法
                result = await agent.execute_enhanced_task(
                    enhanced_prompt=task_message.content,
                    original_message=task_message,
                    file_contents={}
                )
                
                # 更新Schema统计
                self._update_agent_schema_stats(agent_id, agent)
                
            else:
                # 降级到普通执行方法
                result = await agent.execute_task(task_message)
            
            # 更新智能体状态
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.IDLE
                self.registered_agents[agent_id].task_count += 1
                
                # 更新成功率
                if result and result.get("success", False):
                    current_success_rate = self.registered_agents[agent_id].success_rate
                    task_count = self.registered_agents[agent_id].task_count
                    new_success_rate = ((current_success_rate * (task_count - 1)) + 1.0) / task_count
                    self.registered_agents[agent_id].success_rate = new_success_rate
                else:
                    current_success_rate = self.registered_agents[agent_id].success_rate
                    task_count = self.registered_agents[agent_id].task_count
                    new_success_rate = (current_success_rate * (task_count - 1)) / task_count
                    self.registered_agents[agent_id].success_rate = new_success_rate
            
            self.logger.info(f"✅⚡ 增强任务执行完成: {task_message.task_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 增强任务执行失败: {str(e)}")
            
            # 恢复智能体状态
            if agent_id and agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.IDLE
            
            return {
                "success": False,
                "error": str(e),
                "task_id": task_message.task_id
            }
    
    # ==========================================================================
    # 📊 Schema系统监控和统计
    # ==========================================================================
    
    def _update_global_schema_stats(self):
        """更新全局Schema统计"""
        try:
            total_validations = 0
            successful_validations = 0
            total_repairs = 0
            successful_repairs = 0
            cache_hits = 0
            
            for agent_id, enhanced_info in self.enhanced_agents.items():
                if enhanced_info.validation_statistics:
                    stats = enhanced_info.validation_statistics
                    total_validations += stats.get('total_validations', 0)
                    successful_validations += stats.get('successful_validations', 0)
                    # 注意：这里假设统计中有repair相关字段，实际可能需要调整
                    # total_repairs += stats.get('total_repairs', 0)
                    # successful_repairs += stats.get('successful_repairs', 0)
                    cache_hits += stats.get('cache_size', 0)  # 使用cache_size作为代理
            
            self.global_schema_stats.update({
                "total_validations": total_validations,
                "successful_validations": successful_validations,
                "failed_validations": total_validations - successful_validations,
                "total_repairs": total_repairs,
                "successful_repairs": successful_repairs,
                "cache_hits": cache_hits,
                "last_updated": time.time()
            })
            
        except Exception as e:
            self.logger.warning(f"⚠️ 全局Schema统计更新失败: {str(e)}")
    
    def _update_agent_schema_stats(self, agent_id: str, agent: EnhancedBaseAgent):
        """更新智能体Schema统计"""
        try:
            if agent_id in self.enhanced_agents:
                stats = agent.get_validation_statistics()
                self.enhanced_agents[agent_id].validation_statistics = stats
                
                # 更新全局统计
                self._update_global_schema_stats()
                
        except Exception as e:
            self.logger.warning(f"⚠️ 智能体 {agent_id} Schema统计更新失败: {str(e)}")
    
    def get_schema_system_report(self) -> Dict[str, Any]:
        """获取Schema系统报告"""
        try:
            # 基础统计
            total_agents = len(self.registered_agents)
            enhanced_agents_count = len(self.enhanced_agents)
            
            # 工具统计
            total_enhanced_tools = sum(info.enhanced_tools_count for info in self.enhanced_agents.values())
            
            # 性能统计
            success_rates = [info.validation_statistics.get('success_rate', 0) 
                           for info in self.enhanced_agents.values() 
                           if info.validation_statistics]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
            
            return {
                "schema_system_enabled": self.schema_system_enabled,
                "deployment_status": {
                    "total_agents": total_agents,
                    "enhanced_agents": enhanced_agents_count,
                    "enhancement_rate": enhanced_agents_count / total_agents if total_agents > 0 else 0,
                    "total_enhanced_tools": total_enhanced_tools
                },
                "performance_metrics": {
                    "global_statistics": self.global_schema_stats,
                    "average_success_rate": avg_success_rate,
                    "top_performing_agents": self._get_top_performing_agents()
                },
                "agent_details": {
                    agent_id: info.to_dict() 
                    for agent_id, info in self.enhanced_agents.items()
                },
                "recommendations": self._get_schema_recommendations()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Schema系统报告生成失败: {str(e)}")
            return {"error": str(e)}
    
    def _get_top_performing_agents(self) -> List[Dict[str, Any]]:
        """获取表现最佳的智能体"""
        try:
            agents_performance = []
            
            for agent_id, info in self.enhanced_agents.items():
                if info.validation_statistics:
                    success_rate = info.validation_statistics.get('success_rate', 0)
                    agents_performance.append({
                        "agent_id": agent_id,
                        "role": info.role,
                        "success_rate": success_rate,
                        "tools_count": info.enhanced_tools_count,
                        "total_validations": info.validation_statistics.get('total_validations', 0)
                    })
            
            # 按成功率排序，取前5名
            agents_performance.sort(key=lambda x: x['success_rate'], reverse=True)
            return agents_performance[:5]
            
        except Exception as e:
            self.logger.warning(f"⚠️ 获取表现最佳智能体失败: {str(e)}")
            return []
    
    def _get_schema_recommendations(self) -> List[str]:
        """获取Schema系统优化建议"""
        recommendations = []
        
        try:
            total_agents = len(self.registered_agents)
            enhanced_count = len(self.enhanced_agents)
            
            if enhanced_count == 0:
                recommendations.append("建议将现有智能体迁移到Schema系统")
            elif enhanced_count / total_agents < 0.5:
                recommendations.append("建议继续迁移更多智能体到Schema系统")
            elif enhanced_count == total_agents:
                recommendations.append("所有智能体已成功迁移到Schema系统")
            
            # 检查成功率
            success_rates = [info.validation_statistics.get('success_rate', 0) 
                           for info in self.enhanced_agents.values() 
                           if info.validation_statistics]
            
            if success_rates:
                avg_rate = sum(success_rates) / len(success_rates)
                if avg_rate < 0.8:
                    recommendations.append("建议优化Schema验证规则以提高成功率")
                elif avg_rate > 0.95:
                    recommendations.append("Schema验证性能优秀，可考虑扩展更多功能")
            
            # 检查工具数量
            total_tools = sum(info.enhanced_tools_count for info in self.enhanced_agents.values())
            if total_tools < enhanced_count * 3:
                recommendations.append("建议为智能体添加更多Schema验证工具")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 生成Schema建议失败: {str(e)}")
            recommendations.append("Schema系统监控出现问题，建议检查日志")
        
        return recommendations
    
    # ==========================================================================
    # 🎯 向后兼容性方法
    # ==========================================================================
    
    async def select_best_agent(self, task_analysis: Dict[str, Any], 
                              exclude_agents: Set[str] = None,
                              context: Dict[str, Any] = None) -> Optional[str]:
        """向后兼容的智能体选择方法"""
        return await self.select_best_agent_enhanced(task_analysis, exclude_agents, prefer_enhanced=True, context=context)
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "增强中心化协调智能体，支持Schema系统，负责任务分析、智能体选择和工作流程协调"