#!/usr/bin/env python3
"""
Agent Context - 智能体上下文
===========================

集中管理智能体的上下文信息，包括身份、能力、配置等。
"""

from typing import Set, Dict, Any, Optional
from dataclasses import dataclass, field
from core.enums import AgentCapability


@dataclass
class AgentContext:
    """智能体上下文信息"""
    
    # 基本身份信息
    agent_id: str
    role: Optional[str] = None
    capabilities: Set[AgentCapability] = field(default_factory=set)
    
    # 运行时配置
    max_tool_retry_attempts: int = 3
    enable_conversation_optimization: bool = False
    enable_parallel_tool_calls: bool = False
    enable_tool_validation: bool = True
    
    # 工作目录配置
    default_artifacts_dir: Optional[str] = None
    default_workspace_dir: Optional[str] = None
    
    # 任务上下文
    current_task_context: Optional[Any] = None
    current_conversation_id: Optional[str] = None
    
    # 性能统计
    stats: Dict[str, Any] = field(default_factory=lambda: {
        'total_tasks': 0,
        'successful_tasks': 0,
        'failed_tasks': 0,
        'total_tool_calls': 0,
        'successful_tool_calls': 0,
        'failed_tool_calls': 0
    })
    
    # 其他配置
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.capabilities:
            self.capabilities = set()
        
        if not self.role:
            self.role = self.agent_id.replace('_agent', '').replace('_', ' ').title()
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取能力集合"""
        return self.capabilities.copy()
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """检查是否具有特定能力"""
        return capability in self.capabilities
    
    def add_capability(self, capability: AgentCapability) -> None:
        """添加能力"""
        self.capabilities.add(capability)
    
    def remove_capability(self, capability: AgentCapability) -> None:
        """移除能力"""
        self.capabilities.discard(capability)
    
    def get_specialty_description(self) -> str:
        """获取专业能力描述"""
        if not self.capabilities:
            return f"通用智能体 ({self.role})"
        
        capability_names = [cap.value for cap in self.capabilities]
        return f"{self.role} - 专长: {', '.join(capability_names)}"
    
    def update_stats(self, **kwargs) -> None:
        """更新统计信息"""
        for key, value in kwargs.items():
            if key in self.stats:
                if isinstance(value, (int, float)) and isinstance(self.stats[key], (int, float)):
                    self.stats[key] += value
                else:
                    self.stats[key] = value
    
    def get_success_rate(self) -> float:
        """获取任务成功率"""
        total = self.stats.get('total_tasks', 0)
        if total == 0:
            return 0.0
        successful = self.stats.get('successful_tasks', 0)
        return successful / total
    
    def get_tool_success_rate(self) -> float:
        """获取工具调用成功率"""
        total = self.stats.get('total_tool_calls', 0)
        if total == 0:
            return 0.0
        successful = self.stats.get('successful_tool_calls', 0)
        return successful / total
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'capabilities': [cap.value for cap in self.capabilities],
            'max_tool_retry_attempts': self.max_tool_retry_attempts,
            'enable_conversation_optimization': self.enable_conversation_optimization,
            'enable_parallel_tool_calls': self.enable_parallel_tool_calls,
            'enable_tool_validation': self.enable_tool_validation,
            'default_artifacts_dir': self.default_artifacts_dir,
            'default_workspace_dir': self.default_workspace_dir,
            'current_conversation_id': self.current_conversation_id,
            'stats': self.stats.copy(),
            'success_rate': self.get_success_rate(),
            'tool_success_rate': self.get_tool_success_rate(),
            'metadata': self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """从字典创建"""
        # 转换能力
        capabilities = set()
        for cap_value in data.get('capabilities', []):
            try:
                capabilities.add(AgentCapability(cap_value))
            except ValueError:
                pass  # 忽略无效的能力值
        
        context = cls(
            agent_id=data['agent_id'],
            role=data.get('role'),
            capabilities=capabilities,
            max_tool_retry_attempts=data.get('max_tool_retry_attempts', 3),
            enable_conversation_optimization=data.get('enable_conversation_optimization', False),
            enable_parallel_tool_calls=data.get('enable_parallel_tool_calls', False),
            enable_tool_validation=data.get('enable_tool_validation', True),
            default_artifacts_dir=data.get('default_artifacts_dir'),
            default_workspace_dir=data.get('default_workspace_dir'),
            current_conversation_id=data.get('current_conversation_id'),
            stats=data.get('stats', {}),
            metadata=data.get('metadata', {})
        )
        
        return context