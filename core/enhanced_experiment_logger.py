#!/usr/bin/env python3
"""
增强实验日志记录器
Enhanced Experiment Logger
==========================

专门用于生成详细的实验分析报告，包含完整的LLM对话、工具调用和智能体交互记录。
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

from .unified_logging_system import get_global_logging_system


@dataclass
class DetailedExperimentReport:
    """详细实验报告"""
    # 基本信息
    experiment_id: str
    design_type: str
    config_profile: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    
    # 任务信息
    task_description: str
    task_status: str
    coordination_result: str
    
    # 智能体执行详情
    agent_executions: List[Dict[str, Any]]
    agent_conversations: Dict[str, List[Dict[str, Any]]]  # agent_id -> conversations
    agent_decisions: Dict[str, List[Dict[str, Any]]]     # agent_id -> decisions
    
    # 工具执行详情
    detailed_tool_executions: List[Dict[str, Any]]
    tool_execution_summary: Dict[str, Any]
    
    # LLM对话详情
    llm_conversations: List[Dict[str, Any]]
    conversation_analysis: Dict[str, Any]
    
    # 智能体交互网络
    agent_interaction_network: Dict[str, Any]
    coordination_flow: List[Dict[str, Any]]
    
    # 性能分析
    performance_metrics: Dict[str, Any]
    bottleneck_analysis: Dict[str, Any]
    
    # 文件操作记录
    file_operations: List[Dict[str, Any]]
    generated_artifacts: List[str]
    
    # 错误和警告
    errors_and_warnings: List[Dict[str, Any]]
    failure_analysis: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EnhancedExperimentLogger:
    """增强实验日志记录器"""
    
    def __init__(self, experiment_id: str, output_dir: Path):
        self.experiment_id = experiment_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"ExperimentLogger_{experiment_id}")
        
        # 实验数据收集
        self.start_time = time.time()
        self.end_time = None
        self.task_description = ""
        self.success = False
        
        # 收集的数据
        self.agent_executions = []
        self.coordination_events = []
        self.errors_warnings = []
        
    def set_task_description(self, description: str) -> None:
        """设置任务描述"""
        self.task_description = description
        
    def mark_success(self, success: bool) -> None:
        """标记实验成功状态"""
        self.success = success
        
    def mark_completion(self) -> None:
        """标记实验完成"""
        self.end_time = time.time()
        
    def add_agent_execution(self, agent_id: str, execution_data: Dict[str, Any]) -> None:
        """添加智能体执行记录"""
        self.agent_executions.append({
            "timestamp": time.time(),
            "agent_id": agent_id,
            **execution_data
        })
        
    def add_coordination_event(self, event_data: Dict[str, Any]) -> None:
        """添加协调事件"""
        self.coordination_events.append({
            "timestamp": time.time(),
            **event_data
        })
        
    def add_error_warning(self, level: str, message: str, details: Dict[str, Any] = None) -> None:
        """添加错误或警告"""
        self.errors_warnings.append({
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "details": details or {}
        })
        
    def generate_detailed_report(self) -> DetailedExperimentReport:
        """生成详细的实验报告"""
        if self.end_time is None:
            self.mark_completion()
            
        # 从统一日志系统获取数据
        unified_data = self._collect_unified_logging_data()
        
        # 分析对话数据
        conversation_analysis = self._analyze_conversations(unified_data)
        
        # 分析智能体交互
        interaction_analysis = self._analyze_agent_interactions(unified_data)
        
        # 分析工具执行
        tool_analysis = self._analyze_tool_executions(unified_data)
        
        # 性能分析
        performance_analysis = self._analyze_performance(unified_data)
        
        # 构建详细报告
        return DetailedExperimentReport(
            experiment_id=self.experiment_id,
            design_type=self._extract_design_type(),
            config_profile="enhanced_logging",
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.end_time - self.start_time,
            success=self.success,
            
            task_description=self.task_description,
            task_status="success" if self.success else "failed",
            coordination_result=self._get_coordination_summary(),
            
            agent_executions=self.agent_executions,
            agent_conversations=conversation_analysis.get("agent_conversations", {}),
            agent_decisions=conversation_analysis.get("agent_decisions", {}),
            
            detailed_tool_executions=tool_analysis.get("detailed_executions", []),
            tool_execution_summary=tool_analysis.get("summary", {}),
            
            llm_conversations=conversation_analysis.get("llm_conversations", []),
            conversation_analysis=conversation_analysis.get("analysis", {}),
            
            agent_interaction_network=interaction_analysis.get("network", {}),
            coordination_flow=interaction_analysis.get("flow", []),
            
            performance_metrics=performance_analysis.get("metrics", {}),
            bottleneck_analysis=performance_analysis.get("bottlenecks", {}),
            
            file_operations=unified_data.get("file_operations", []),
            generated_artifacts=self._extract_generated_files(unified_data),
            
            errors_and_warnings=self.errors_warnings,
            failure_analysis=self._analyze_failures() if not self.success else None
        )
        
    def _collect_unified_logging_data(self) -> Dict[str, Any]:
        """从统一日志系统收集数据"""
        try:
            logging_system = get_global_logging_system()
            return logging_system.export_data()
        except Exception as e:
            self.logger.warning(f"无法获取统一日志数据: {e}")
            return {}
            
    def _analyze_conversations(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析对话数据"""
        analysis = {
            "agent_conversations": {},
            "agent_decisions": {},
            "llm_conversations": [],
            "analysis": {}
        }
        
        try:
            # 处理LLM对话记录
            llm_conversations = unified_data.get("llm_conversations", {})
            for call_id, conversation in llm_conversations.items():
                analysis["llm_conversations"].append({
                    "call_id": call_id,
                    "agent_id": conversation.get("agent_id"),
                    "timestamp": conversation.get("timestamp"),
                    "model_name": conversation.get("model_name"),
                    "duration": conversation.get("duration"),
                    "success": conversation.get("success"),
                    "conversation_length": conversation.get("conversation_length", 0),
                    "system_prompt_preview": conversation.get("system_prompt", "")[:200],
                    "user_message_preview": conversation.get("user_message", "")[:200],
                    "assistant_response_preview": conversation.get("assistant_response", "")[:200],
                    "prompt_tokens": conversation.get("prompt_tokens"),
                    "completion_tokens": conversation.get("completion_tokens"),
                    "total_tokens": conversation.get("total_tokens")
                })
                
            # 按智能体分组对话
            for conversation in analysis["llm_conversations"]:
                agent_id = conversation["agent_id"]
                if agent_id not in analysis["agent_conversations"]:
                    analysis["agent_conversations"][agent_id] = []
                analysis["agent_conversations"][agent_id].append(conversation)
                
            # 处理对话线程
            conversation_threads = unified_data.get("conversation_threads", {})
            for thread_id, thread_data in conversation_threads.items():
                agent_id = thread_data.get("agent_id")
                if agent_id and agent_id not in analysis["agent_decisions"]:
                    analysis["agent_decisions"][agent_id] = []
                    
                # 添加决策点
                for decision in thread_data.get("decision_points", []):
                    analysis["agent_decisions"][agent_id].append(decision)
                    
            # 生成分析统计
            analysis["analysis"] = {
                "total_llm_calls": len(analysis["llm_conversations"]),
                "total_agents_with_conversations": len(analysis["agent_conversations"]),
                "average_conversation_duration": self._calculate_average_duration(analysis["llm_conversations"]),
                "successful_calls": len([c for c in analysis["llm_conversations"] if c.get("success", True)]),
                "failed_calls": len([c for c in analysis["llm_conversations"] if not c.get("success", True)]),
                "total_tokens_used": sum(c.get("total_tokens", 0) for c in analysis["llm_conversations"] if c.get("total_tokens")),
                "agents_activity": {agent_id: len(convs) for agent_id, convs in analysis["agent_conversations"].items()}
            }
            
        except Exception as e:
            self.logger.error(f"对话分析失败: {e}")
            
        return analysis
        
    def _analyze_agent_interactions(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析智能体交互"""
        analysis = {
            "network": {},
            "flow": []
        }
        
        try:
            # 分析事件中的智能体交互
            events = unified_data.get("events", [])
            agent_interactions = {}
            coordination_flow = []
            
            for event in events:
                if event.get("category") == "agent":
                    agent_id = event.get("agent_id")
                    details = event.get("details", {})
                    
                    # 记录智能体活动
                    if agent_id not in agent_interactions:
                        agent_interactions[agent_id] = {
                            "total_events": 0,
                            "successful_events": 0,
                            "failed_events": 0,
                            "total_duration": 0.0,
                            "event_types": {}
                        }
                        
                    interaction = agent_interactions[agent_id]
                    interaction["total_events"] += 1
                    
                    if event.get("success", True):
                        interaction["successful_events"] += 1
                    else:
                        interaction["failed_events"] += 1
                        
                    if event.get("duration"):
                        interaction["total_duration"] += event["duration"]
                        
                    # 记录事件类型
                    event_title = event.get("title", "unknown")
                    if event_title not in interaction["event_types"]:
                        interaction["event_types"][event_title] = 0
                    interaction["event_types"][event_title] += 1
                    
                    # 记录协调流程
                    if "任务分配" in event_title or "任务完成" in event_title:
                        coordination_flow.append({
                            "timestamp": event.get("timestamp"),
                            "event_type": event_title,
                            "agent_id": agent_id,
                            "details": details,
                            "success": event.get("success", True)
                        })
                        
            analysis["network"] = agent_interactions
            analysis["flow"] = sorted(coordination_flow, key=lambda x: x["timestamp"])
            
        except Exception as e:
            self.logger.error(f"智能体交互分析失败: {e}")
            
        return analysis
        
    def _analyze_tool_executions(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析工具执行"""
        analysis = {
            "detailed_executions": [],
            "summary": {}
        }
        
        try:
            events = unified_data.get("events", [])
            tool_executions = []
            tool_stats = {}
            
            for event in events:
                if event.get("category") == "tool":
                    tool_name = event.get("details", {}).get("tool_name", "unknown")
                    
                    execution_record = {
                        "timestamp": event.get("timestamp"),
                        "agent_id": event.get("agent_id"),
                        "tool_name": tool_name,
                        "title": event.get("title"),
                        "success": event.get("success", True),
                        "duration": event.get("duration"),
                        "details": event.get("details", {}),
                        "error_info": event.get("error_info")
                    }
                    
                    tool_executions.append(execution_record)
                    
                    # 统计工具使用情况
                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = {
                            "total_calls": 0,
                            "successful_calls": 0,
                            "failed_calls": 0,
                            "total_duration": 0.0,
                            "average_duration": 0.0,
                            "agents_used": set()
                        }
                        
                    stats = tool_stats[tool_name]
                    stats["total_calls"] += 1
                    stats["agents_used"].add(event.get("agent_id"))
                    
                    if event.get("success", True):
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1
                        
                    if event.get("duration"):
                        stats["total_duration"] += event["duration"]
                        
            # 计算平均持续时间
            for tool_name, stats in tool_stats.items():
                if stats["total_calls"] > 0:
                    stats["average_duration"] = stats["total_duration"] / stats["total_calls"]
                stats["agents_used"] = list(stats["agents_used"])  # 转换为列表以便JSON序列化
                
            analysis["detailed_executions"] = tool_executions
            analysis["summary"] = {
                "total_tool_calls": len(tool_executions),
                "unique_tools_used": len(tool_stats),
                "successful_calls": len([e for e in tool_executions if e["success"]]),
                "failed_calls": len([e for e in tool_executions if not e["success"]]),
                "tool_usage_stats": tool_stats,
                "most_used_tools": sorted(tool_stats.items(), key=lambda x: x[1]["total_calls"], reverse=True)[:5]
            }
            
        except Exception as e:
            self.logger.error(f"工具执行分析失败: {e}")
            
        return analysis
        
    def _analyze_performance(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能"""
        analysis = {
            "metrics": {},
            "bottlenecks": {}
        }
        
        try:
            events = unified_data.get("events", [])
            
            # 计算性能指标
            total_duration = self.end_time - self.start_time if self.end_time else 0
            
            # 分析各类事件的耗时
            category_durations = {}
            agent_durations = {}
            
            for event in events:
                category = event.get("category")
                agent_id = event.get("agent_id")
                duration = event.get("duration", 0)
                
                if duration > 0:
                    if category not in category_durations:
                        category_durations[category] = []
                    category_durations[category].append(duration)
                    
                    if agent_id not in agent_durations:
                        agent_durations[agent_id] = []
                    agent_durations[agent_id].append(duration)
                    
            # 计算统计信息
            metrics = {
                "total_experiment_duration": total_duration,
                "total_events": len(events),
                "category_performance": {},
                "agent_performance": {}
            }
            
            for category, durations in category_durations.items():
                metrics["category_performance"][category] = {
                    "total_time": sum(durations),
                    "average_time": sum(durations) / len(durations),
                    "max_time": max(durations),
                    "min_time": min(durations),
                    "event_count": len(durations)
                }
                
            for agent_id, durations in agent_durations.items():
                metrics["agent_performance"][agent_id] = {
                    "total_time": sum(durations),
                    "average_time": sum(durations) / len(durations),
                    "max_time": max(durations),
                    "min_time": min(durations),
                    "event_count": len(durations)
                }
                
            # 识别瓶颈
            bottlenecks = {
                "slowest_category": max(category_durations.items(), key=lambda x: sum(x[1]))[0] if category_durations else None,
                "slowest_agent": max(agent_durations.items(), key=lambda x: sum(x[1]))[0] if agent_durations else None,
                "longest_single_event": max(events, key=lambda x: x.get("duration", 0)) if events else None
            }
            
            analysis["metrics"] = metrics
            analysis["bottlenecks"] = bottlenecks
            
        except Exception as e:
            self.logger.error(f"性能分析失败: {e}")
            
        return analysis
        
    def _calculate_average_duration(self, conversations: List[Dict[str, Any]]) -> float:
        """计算平均持续时间"""
        durations = [c.get("duration", 0) for c in conversations if c.get("duration")]
        return sum(durations) / len(durations) if durations else 0.0
        
    def _extract_design_type(self) -> str:
        """提取设计类型"""
        if "counter" in self.task_description.lower():
            return "counter"
        elif "adder" in self.task_description.lower():
            return "adder"
        elif "multiplexer" in self.task_description.lower():
            return "multiplexer"
        else:
            return "unknown"
            
    def _get_coordination_summary(self) -> str:
        """获取协调摘要"""
        return f"Experiment {self.experiment_id} {'completed successfully' if self.success else 'failed'} with {len(self.agent_executions)} agent executions and {len(self.coordination_events)} coordination events."
        
    def _extract_generated_files(self, unified_data: Dict[str, Any]) -> List[str]:
        """提取生成的文件"""
        files = []
        events = unified_data.get("events", [])
        
        for event in events:
            if event.get("category") == "file" and "write" in event.get("title", "").lower():
                file_path = event.get("details", {}).get("file_path")
                if file_path and file_path not in files:
                    files.append(file_path)
                    
        return files
        
    def _analyze_failures(self) -> Dict[str, Any]:
        """分析失败原因"""
        failure_analysis = {
            "primary_failure_category": "unknown",
            "error_count": len([e for e in self.errors_warnings if e["level"] == "error"]),
            "warning_count": len([e for e in self.errors_warnings if e["level"] == "warning"]),
            "failure_timeline": [],
            "root_cause_analysis": "需要进一步调查"
        }
        
        # 分析错误模式
        error_categories = {}
        for error in self.errors_warnings:
            if error["level"] == "error":
                # 简单的错误分类
                message = error["message"].lower()
                if "compilation" in message or "compile" in message:
                    category = "compilation_error"
                elif "tool" in message:
                    category = "tool_execution_error"
                elif "llm" in message or "model" in message:
                    category = "llm_error"
                else:
                    category = "general_error"
                    
                if category not in error_categories:
                    error_categories[category] = 0
                error_categories[category] += 1
                
                failure_analysis["failure_timeline"].append({
                    "timestamp": error["timestamp"],
                    "category": category,
                    "message": error["message"]
                })
                
        if error_categories:
            failure_analysis["primary_failure_category"] = max(error_categories.items(), key=lambda x: x[1])[0]
            failure_analysis["error_distribution"] = error_categories
            
        return failure_analysis
        
    def save_report(self, report: DetailedExperimentReport) -> Path:
        """保存详细报告"""
        report_path = self.output_dir / "enhanced_experiment_report.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)
                
            self.logger.info(f"详细实验报告已保存: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            raise