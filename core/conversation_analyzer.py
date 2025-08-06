#!/usr/bin/env python3
"""
对话分析工具
Conversation Analyzer
====================

用于分析LLM对话记录，识别模式、问题和改进机会。
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging


@dataclass
class ConversationPattern:
    """对话模式"""
    pattern_type: str
    frequency: int
    examples: List[str]
    impact_score: float
    description: str


@dataclass
class ProblemDiagnosis:
    """问题诊断"""
    problem_type: str
    severity: str  # low, medium, high, critical
    affected_agents: List[str]
    frequency: int
    symptoms: List[str]
    suggested_fixes: List[str]
    confidence: float


@dataclass 
class ConversationAnalysisReport:
    """对话分析报告"""
    experiment_id: str
    analysis_timestamp: float
    
    # 对话统计
    conversation_stats: Dict[str, Any]
    
    # 发现的模式
    identified_patterns: List[ConversationPattern]
    
    # 问题诊断
    problem_diagnosis: List[ProblemDiagnosis]
    
    # 性能分析
    performance_insights: Dict[str, Any]
    
    # 改进建议
    improvement_recommendations: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "analysis_timestamp": self.analysis_timestamp,
            "conversation_stats": self.conversation_stats,
            "identified_patterns": [p.__dict__ for p in self.identified_patterns],
            "problem_diagnosis": [p.__dict__ for p in self.problem_diagnosis],
            "performance_insights": self.performance_insights,
            "improvement_recommendations": self.improvement_recommendations
        }


class ConversationAnalyzer:
    """对话分析器"""
    
    def __init__(self, experiment_report_path: str):
        self.report_path = Path(experiment_report_path)
        self.logger = logging.getLogger("ConversationAnalyzer")
        
        # 加载实验报告数据
        self.experiment_data = self._load_experiment_data()
        self.experiment_id = self.experiment_data.get("experiment_id", "unknown")
        
        # 分析结果存储
        self.conversation_stats = {}
        self.identified_patterns = []
        self.problems = []
        
    def _load_experiment_data(self) -> Dict[str, Any]:
        """加载实验数据"""
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载实验数据失败: {e}")
            return {}
            
    def analyze(self) -> ConversationAnalysisReport:
        """执行完整分析"""
        # 1. 基础统计分析
        self._analyze_conversation_stats()
        
        # 2. 模式识别
        self._identify_patterns()
        
        # 3. 问题诊断
        self._diagnose_problems()
        
        # 4. 性能分析
        performance_insights = self._analyze_performance()
        
        # 5. 生成改进建议
        recommendations = self._generate_recommendations()
        
        return ConversationAnalysisReport(
            experiment_id=self.experiment_id,
            analysis_timestamp=__import__('time').time(),
            conversation_stats=self.conversation_stats,
            identified_patterns=self.identified_patterns,
            problem_diagnosis=self.problems,
            performance_insights=performance_insights,
            improvement_recommendations=recommendations
        )
        
    def _analyze_conversation_stats(self) -> None:
        """分析对话统计信息"""
        llm_conversations = self.experiment_data.get("llm_conversations", [])
        agent_conversations = self.experiment_data.get("agent_conversations", {})
        
        self.conversation_stats = {
            "total_llm_calls": len(llm_conversations),
            "unique_agents": len(agent_conversations),
            "successful_calls": len([c for c in llm_conversations if c.get("success", True)]),
            "failed_calls": len([c for c in llm_conversations if not c.get("success", True)]),
            "total_duration": sum(c.get("duration", 0) for c in llm_conversations),
            "average_call_duration": 0,
            "total_tokens": sum(c.get("total_tokens", 0) for c in llm_conversations if c.get("total_tokens")),
            "agent_activity": {},
            "conversation_length_distribution": {},
            "model_usage": Counter()
        }
        
        # 计算平均时长
        if llm_conversations:
            self.conversation_stats["average_call_duration"] = (
                self.conversation_stats["total_duration"] / len(llm_conversations)
            )
            
        # 分析智能体活动
        for agent_id, conversations in agent_conversations.items():
            self.conversation_stats["agent_activity"][agent_id] = {
                "total_conversations": len(conversations),
                "total_duration": sum(c.get("duration", 0) for c in conversations),
                "average_duration": sum(c.get("duration", 0) for c in conversations) / len(conversations) if conversations else 0,
                "success_rate": len([c for c in conversations if c.get("success", True)]) / len(conversations) if conversations else 0
            }
            
        # 分析对话长度分布
        length_buckets = {"short": 0, "medium": 0, "long": 0, "very_long": 0}
        for conversation in llm_conversations:
            length = conversation.get("conversation_length", 0)
            if length <= 2:
                length_buckets["short"] += 1
            elif length <= 5:
                length_buckets["medium"] += 1
            elif length <= 10:
                length_buckets["long"] += 1
            else:
                length_buckets["very_long"] += 1
                
        self.conversation_stats["conversation_length_distribution"] = length_buckets
        
        # 模型使用统计
        for conversation in llm_conversations:
            model = conversation.get("model_name", "unknown")
            self.conversation_stats["model_usage"][model] += 1
            
    def _identify_patterns(self) -> None:
        """识别对话模式"""
        llm_conversations = self.experiment_data.get("llm_conversations", [])
        
        # 1. 识别重复的用户输入模式
        self._identify_repetitive_patterns(llm_conversations)
        
        # 2. 识别失败模式
        self._identify_failure_patterns(llm_conversations)
        
        # 3. 识别效率模式
        self._identify_efficiency_patterns(llm_conversations)
        
        # 4. 识别工具调用模式
        self._identify_tool_calling_patterns()
        
    def _identify_repetitive_patterns(self, conversations: List[Dict[str, Any]]) -> None:
        """识别重复模式"""
        user_messages = []
        response_patterns = []
        
        for conv in conversations:
            user_msg = conv.get("user_message_preview", "")
            response_msg = conv.get("assistant_response_preview", "")
            
            if user_msg:
                user_messages.append(user_msg.lower())
            if response_msg:
                response_patterns.append(response_msg.lower())
                
        # 寻找重复的用户消息
        user_counter = Counter(user_messages)
        repetitive_user_messages = [(msg, count) for msg, count in user_counter.items() if count > 2]
        
        if repetitive_user_messages:
            self.identified_patterns.append(ConversationPattern(
                pattern_type="repetitive_user_input",
                frequency=len(repetitive_user_messages),
                examples=[msg for msg, _ in repetitive_user_messages[:3]],
                impact_score=0.7,
                description=f"发现 {len(repetitive_user_messages)} 个重复的用户输入模式，可能表明系统在循环执行相同操作"
            ))
            
        # 寻找重复的响应模式
        response_keywords = []
        for response in response_patterns:
            # 提取关键词（简单实现）
            words = re.findall(r'\w+', response.lower())
            common_words = ["工具", "调用", "执行", "成功", "失败", "错误", "完成"]
            keywords = [w for w in words if w in common_words]
            response_keywords.extend(keywords)
            
        keyword_counter = Counter(response_keywords)
        if keyword_counter:
            most_common = keyword_counter.most_common(3)
            self.identified_patterns.append(ConversationPattern(
                pattern_type="common_response_keywords",
                frequency=sum(count for _, count in most_common),
                examples=[keyword for keyword, _ in most_common],
                impact_score=0.3,
                description=f"常见响应关键词: {', '.join([f'{k}({c})' for k, c in most_common])}"
            ))
            
    def _identify_failure_patterns(self, conversations: List[Dict[str, Any]]) -> None:
        """识别失败模式"""
        failed_conversations = [c for c in conversations if not c.get("success", True)]
        
        if failed_conversations:
            failure_reasons = []
            affected_agents = set()
            
            for conv in failed_conversations:
                agent_id = conv.get("agent_id")
                if agent_id:
                    affected_agents.add(agent_id)
                    
                # 尝试从响应中提取失败原因
                response = conv.get("assistant_response_preview", "").lower()
                if "timeout" in response or "超时" in response:
                    failure_reasons.append("timeout")
                elif "compilation" in response or "编译" in response:
                    failure_reasons.append("compilation_error")
                elif "tool" in response and ("failed" in response or "失败" in response):
                    failure_reasons.append("tool_execution_failure")
                else:
                    failure_reasons.append("unknown_error")
                    
            failure_counter = Counter(failure_reasons)
            most_common_failure = failure_counter.most_common(1)[0] if failure_counter else ("unknown", 0)
            
            self.identified_patterns.append(ConversationPattern(
                pattern_type="failure_pattern",
                frequency=len(failed_conversations),
                examples=list(affected_agents)[:3],
                impact_score=0.9,
                description=f"失败率: {len(failed_conversations)/len(conversations)*100:.1f}%, 主要原因: {most_common_failure[0]}"
            ))
            
    def _identify_efficiency_patterns(self, conversations: List[Dict[str, Any]]) -> None:
        """识别效率模式"""
        durations = [c.get("duration", 0) for c in conversations if c.get("duration", 0) > 0]
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            slow_conversations = [d for d in durations if d > avg_duration * 2]
            
            if slow_conversations:
                self.identified_patterns.append(ConversationPattern(
                    pattern_type="slow_response_pattern",
                    frequency=len(slow_conversations),
                    examples=[f"{d:.2f}s" for d in slow_conversations[:3]],
                    impact_score=0.6,
                    description=f"发现 {len(slow_conversations)} 次异常缓慢的响应（超过平均时间2倍）"
                ))
                
        # 分析token使用效率
        token_usage = [c.get("total_tokens", 0) for c in conversations if c.get("total_tokens")]
        if token_usage:
            avg_tokens = sum(token_usage) / len(token_usage)
            high_token_usage = [t for t in token_usage if t > avg_tokens * 1.5]
            
            if high_token_usage:
                self.identified_patterns.append(ConversationPattern(
                    pattern_type="high_token_usage_pattern",
                    frequency=len(high_token_usage),
                    examples=[f"{t} tokens" for t in high_token_usage[:3]],
                    impact_score=0.4,
                    description=f"发现 {len(high_token_usage)} 次高token使用（超过平均值1.5倍）"
                ))
                
    def _identify_tool_calling_patterns(self) -> None:
        """识别工具调用模式"""
        detailed_tool_executions = self.experiment_data.get("detailed_tool_executions", [])
        
        if detailed_tool_executions:
            # 分析工具失败模式
            failed_tools = [t for t in detailed_tool_executions if not t.get("success", True)]
            if failed_tools:
                tool_failure_counter = Counter([t.get("tool_name", "unknown") for t in failed_tools])
                most_failed_tool = tool_failure_counter.most_common(1)[0] if tool_failure_counter else ("unknown", 0)
                
                self.identified_patterns.append(ConversationPattern(
                    pattern_type="tool_failure_pattern",
                    frequency=len(failed_tools),
                    examples=[f"{tool}: {count}次" for tool, count in tool_failure_counter.most_common(3)],
                    impact_score=0.8,
                    description=f"工具执行失败率: {len(failed_tools)/len(detailed_tool_executions)*100:.1f}%, 最常失败: {most_failed_tool[0]}"
                ))
                
    def _diagnose_problems(self) -> None:
        """诊断问题"""
        # 1. 高失败率问题
        self._diagnose_high_failure_rate()
        
        # 2. 性能问题
        self._diagnose_performance_issues()
        
        # 3. 工具执行问题
        self._diagnose_tool_execution_issues()
        
        # 4. 对话质量问题
        self._diagnose_conversation_quality_issues()
        
    def _diagnose_high_failure_rate(self) -> None:
        """诊断高失败率问题"""
        stats = self.conversation_stats
        failure_rate = stats.get("failed_calls", 0) / max(stats.get("total_llm_calls", 1), 1)
        
        if failure_rate > 0.1:  # 失败率超过10%
            severity = "critical" if failure_rate > 0.3 else "high" if failure_rate > 0.2 else "medium"
            
            affected_agents = []
            for agent_id, activity in stats.get("agent_activity", {}).items():
                if activity.get("success_rate", 1.0) < 0.9:
                    affected_agents.append(agent_id)
                    
            self.problems.append(ProblemDiagnosis(
                problem_type="high_failure_rate",
                severity=severity,
                affected_agents=affected_agents,
                frequency=stats.get("failed_calls", 0),
                symptoms=[
                    f"总失败率: {failure_rate*100:.1f}%",
                    f"受影响智能体: {len(affected_agents)}个"
                ],
                suggested_fixes=[
                    "检查LLM客户端配置和网络连接",
                    "增加重试机制和错误处理",
                    "优化system prompt以减少不确定性",
                    "检查智能体工具调用逻辑"
                ],
                confidence=0.8
            ))
            
    def _diagnose_performance_issues(self) -> None:
        """诊断性能问题"""
        stats = self.conversation_stats
        avg_duration = stats.get("average_call_duration", 0)
        
        if avg_duration > 10:  # 平均响应时间超过10秒
            severity = "high" if avg_duration > 30 else "medium"
            
            slow_agents = []
            for agent_id, activity in stats.get("agent_activity", {}).items():
                if activity.get("average_duration", 0) > avg_duration * 1.5:
                    slow_agents.append(agent_id)
                    
            self.problems.append(ProblemDiagnosis(
                problem_type="slow_response_time",
                severity=severity,
                affected_agents=slow_agents,
                frequency=int(stats.get("total_llm_calls", 0)),
                symptoms=[
                    f"平均响应时间: {avg_duration:.2f}秒",
                    f"缓慢的智能体: {len(slow_agents)}个"
                ],
                suggested_fixes=[
                    "优化system prompt长度",
                    "减少不必要的上下文传递",
                    "使用更快的模型或增加超时配置",
                    "并行化工具执行"
                ],
                confidence=0.7
            ))
            
    def _diagnose_tool_execution_issues(self) -> None:
        """诊断工具执行问题"""
        tool_executions = self.experiment_data.get("detailed_tool_executions", [])\n        tool_summary = self.experiment_data.get("tool_execution_summary", {})\n        \n        failed_calls = tool_summary.get("failed_calls", 0)\n        total_calls = tool_summary.get("total_tool_calls", 1)\n        \n        if failed_calls > 0 and failed_calls / total_calls > 0.1:\n            severity = "high" if failed_calls / total_calls > 0.3 else "medium"\n            \n            # 找出问题工具\n            problem_tools = []\n            tool_stats = tool_summary.get("tool_usage_stats", {})\n            for tool_name, stats in tool_stats.items():\n                failure_rate = stats.get("failed_calls", 0) / max(stats.get("total_calls", 1), 1)\n                if failure_rate > 0.2:\n                    problem_tools.append(tool_name)\n                    \n            self.problems.append(ProblemDiagnosis(\n                problem_type="tool_execution_failure",\n                severity=severity,\n                affected_agents=list(set([t.get("agent_id") for t in tool_executions if not t.get("success")])),\n                frequency=failed_calls,\n                symptoms=[\n                    f"工具失败率: {failed_calls/total_calls*100:.1f}%",\n                    f"问题工具: {', '.join(problem_tools[:3])}"\n                ],\n                suggested_fixes=[\n                    "检查工具参数验证逻辑",\n                    "改进错误处理和重试机制",\n                    "验证工具依赖和环境配置",\n                    "添加工具执行前的预检查"\n                ],\n                confidence=0.9\n            ))\n            \n    def _diagnose_conversation_quality_issues(self) -> None:\n        """诊断对话质量问题"""\n        # 检查对话长度分布\n        length_dist = self.conversation_stats.get("conversation_length_distribution", {})\n        very_long_conversations = length_dist.get("very_long", 0)\n        total_conversations = sum(length_dist.values()) if length_dist else 1\n        \n        if very_long_conversations / total_conversations > 0.2:\n            self.problems.append(ProblemDiagnosis(\n                problem_type="excessive_conversation_length",\n                severity="medium",\n                affected_agents=[],  # TODO: 识别具体智能体\n                frequency=very_long_conversations,\n                symptoms=[\n                    f"超长对话比例: {very_long_conversations/total_conversations*100:.1f}%",\n                    "可能存在循环对话或低效的任务分解"\n                ],\n                suggested_fixes=[\n                    "优化任务分解逻辑",\n                    "添加对话长度监控和截断",\n                    "改进循环检测机制",\n                    "优化智能体间的任务传递"\n                ],\n                confidence=0.6\n            ))\n            \n        # 检查token使用效率\n        total_tokens = self.conversation_stats.get("total_tokens", 0)\n        total_calls = self.conversation_stats.get("total_llm_calls", 1)\n        avg_tokens_per_call = total_tokens / total_calls\n        \n        if avg_tokens_per_call > 5000:\n            self.problems.append(ProblemDiagnosis(\n                problem_type="high_token_consumption",\n                severity="medium",\n                affected_agents=[],\n                frequency=total_calls,\n                symptoms=[\n                    f"平均每次调用使用: {avg_tokens_per_call:.0f} tokens",\n                    "可能存在冗余的上下文传递"\n                ],\n                suggested_fixes=[\n                    "优化system prompt长度",\n                    "实现智能上下文修剪",\n                    "减少不必要的历史对话保留",\n                    "使用更高效的prompt模板"\n                ],\n                confidence=0.5\n            ))\n            \n    def _analyze_performance(self) -> Dict[str, Any]:\n        """分析性能"""\n        performance_data = self.experiment_data.get("performance_metrics", {})\n        bottlenecks = self.experiment_data.get("bottleneck_analysis", {})\n        \n        insights = {\n            "overall_efficiency": self._calculate_overall_efficiency(),\n            "bottleneck_identification": bottlenecks,\n            "resource_utilization": self._analyze_resource_utilization(),\n            "scalability_assessment": self._assess_scalability()\n        }\n        \n        return insights\n        \n    def _calculate_overall_efficiency(self) -> Dict[str, Any]:\n        """计算整体效率"""\n        stats = self.conversation_stats\n        total_duration = stats.get("total_duration", 0)\n        total_calls = stats.get("total_llm_calls", 1)\n        success_rate = stats.get("successful_calls", 0) / total_calls\n        \n        efficiency_score = success_rate * (1 / max(stats.get("average_call_duration", 1), 0.1))\n        \n        return {\n            "efficiency_score": min(efficiency_score * 10, 100),  # 标准化到0-100\n            "success_rate": success_rate,\n            "average_response_time": stats.get("average_call_duration", 0),\n            "total_processing_time": total_duration,\n            "calls_per_minute": total_calls / max(total_duration / 60, 0.1) if total_duration > 0 else 0\n        }\n        \n    def _analyze_resource_utilization(self) -> Dict[str, Any]:\n        """分析资源利用率"""\n        stats = self.conversation_stats\n        \n        return {\n            "token_efficiency": {\n                "total_tokens_used": stats.get("total_tokens", 0),\n                "average_tokens_per_call": stats.get("total_tokens", 0) / max(stats.get("total_llm_calls", 1), 1),\n                "estimated_cost": stats.get("total_tokens", 0) * 0.00001  # 假设价格\n            },\n            "agent_utilization": {\n                agent_id: {\n                    "utilization_rate": activity.get("total_conversations", 0) / max(stats.get("total_llm_calls", 1), 1),\n                    "efficiency": activity.get("success_rate", 0) / max(activity.get("average_duration", 1), 0.1)\n                }\n                for agent_id, activity in stats.get("agent_activity", {}).items()\n            }\n        }\n        \n    def _assess_scalability(self) -> Dict[str, Any]:\n        """评估可扩展性"""\n        stats = self.conversation_stats\n        \n        # 简单的可扩展性评估\n        agent_count = len(stats.get("agent_activity", {}))\n        avg_duration = stats.get("average_call_duration", 0)\n        success_rate = stats.get("successful_calls", 0) / max(stats.get("total_llm_calls", 1), 1)\n        \n        scalability_score = min((success_rate * 100) - (avg_duration * 2) + (agent_count * 5), 100)\n        \n        return {\n            "scalability_score": max(scalability_score, 0),\n            "current_agent_count": agent_count,\n            "recommended_max_agents": min(agent_count * 2, 10),\n            "performance_degradation_risk": "high" if avg_duration > 15 else "medium" if avg_duration > 8 else "low"\n        }\n        \n    def _generate_recommendations(self) -> List[Dict[str, Any]]:\n        """生成改进建议"""\n        recommendations = []\n        \n        # 基于识别的问题生成建议\n        for problem in self.problems:\n            recommendations.extend([\n                {\n                    "category": "problem_resolution",\n                    "priority": self._severity_to_priority(problem.severity),\n                    "title": f"解决{problem.problem_type}问题",\n                    "description": f"当前{problem.problem_type}影响了{len(problem.affected_agents)}个智能体",\n                    "actions": problem.suggested_fixes,\n                    "expected_impact": "high" if problem.severity in ["high", "critical"] else "medium"\n                }\n            ])\n            \n        # 基于模式生成建议\n        for pattern in self.identified_patterns:\n            if pattern.impact_score > 0.5:\n                recommendations.append({\n                    "category": "pattern_optimization",\n                    "priority": "medium",\n                    "title": f"优化{pattern.pattern_type}",\n                    "description": pattern.description,\n                    "actions": self._get_pattern_optimization_actions(pattern.pattern_type),\n                    "expected_impact": "medium"\n                })\n                \n        # 性能优化建议\n        efficiency = self._calculate_overall_efficiency()\n        if efficiency["efficiency_score"] < 70:\n            recommendations.append({\n                "category": "performance_optimization",\n                "priority": "high",\n                "title": "提升整体效率",\n                "description": f"当前效率得分: {efficiency['efficiency_score']:.1f}/100",\n                "actions": [\n                    "优化最慢的智能体响应时间",\n                    "提高任务成功率",\n                    "并行化可并行的操作",\n                    "实现智能缓存机制"\n                ],\n                "expected_impact": "high"\n            })\n            \n        return sorted(recommendations, key=lambda x: self._priority_score(x["priority"]), reverse=True)\n        \n    def _severity_to_priority(self, severity: str) -> str:\n        """将严重性转换为优先级"""\n        mapping = {\n            "critical": "critical",\n            "high": "high",\n            "medium": "medium", \n            "low": "low"\n        }\n        return mapping.get(severity, "medium")\n        \n    def _priority_score(self, priority: str) -> int:\n        """优先级评分"""\n        scores = {\n            "critical": 4,\n            "high": 3,\n            "medium": 2,\n            "low": 1\n        }\n        return scores.get(priority, 0)\n        \n    def _get_pattern_optimization_actions(self, pattern_type: str) -> List[str]:\n        """获取模式优化建议"""\n        actions_map = {\n            "repetitive_user_input": [\n                "检查循环逻辑，避免重复执行相同操作",\n                "改进任务完成检测机制",\n                "添加状态记录和去重机制"\n            ],\n            "failure_pattern": [\n                "分析失败根本原因",\n                "改进错误处理和恢复机制",\n                "添加预检查和验证步骤"\n            ],\n            "slow_response_pattern": [\n                "优化慢响应的system prompt",\n                "减少上下文长度",\n                "考虑使用更快的模型"\n            ],\n            "tool_failure_pattern": [\n                "检查工具配置和依赖",\n                "改进参数验证",\n                "添加工具健康检查机制"\n            ]\n        }\n        return actions_map.get(pattern_type, ["分析该模式的具体原因", "制定针对性的优化策略"])\n        \n    def save_analysis(self, report: ConversationAnalysisReport, output_path: str = None) -> Path:\n        """保存分析结果"""\n        if output_path is None:\n            output_dir = self.report_path.parent\n            output_path = output_dir / f"conversation_analysis_{self.experiment_id}.json"\n        else:\n            output_path = Path(output_path)\n            \n        try:\n            with open(output_path, 'w', encoding='utf-8') as f:\n                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)\n                \n            self.logger.info(f"对话分析报告已保存: {output_path}")\n            return output_path\n            \n        except Exception as e:\n            self.logger.error(f"保存分析报告失败: {e}")\n            raise\n            \n    def generate_summary_text(self, report: ConversationAnalysisReport) -> str:\n        """生成文本摘要"""\n        stats = report.conversation_stats\n        \n        summary = f"""# 对话分析摘要 - {report.experiment_id}\n        \n## 基础统计\n- 总LLM调用: {stats.get('total_llm_calls', 0)}次\n- 成功率: {stats.get('successful_calls', 0) / max(stats.get('total_llm_calls', 1), 1) * 100:.1f}%\n- 平均响应时间: {stats.get('average_call_duration', 0):.2f}秒\n- 参与智能体: {stats.get('unique_agents', 0)}个\n- 总Token使用: {stats.get('total_tokens', 0):,}\n        \n## 识别的模式 ({len(report.identified_patterns)}个)\n"""\n        \n        for i, pattern in enumerate(report.identified_patterns, 1):\n            summary += f"{i}. **{pattern.pattern_type}**: {pattern.description}\\n"\n            \n        summary += f"\\n## 问题诊断 ({len(report.problem_diagnosis)}个)\\n"\n        \n        for i, problem in enumerate(report.problem_diagnosis, 1):\n            summary += f"{i}. **{problem.problem_type}** ({problem.severity}): 影响{len(problem.affected_agents)}个智能体\\n"\n            \n        summary += f"\\n## 改进建议 ({len(report.improvement_recommendations)}个)\\n"\n        \n        for i, rec in enumerate(report.improvement_recommendations[:5], 1):\n            summary += f"{i}. **{rec['title']}** ({rec['priority']}): {rec['description']}\\n"\n            \n        return summary