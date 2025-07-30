#!/usr/bin/env python3
"""
核心组件模块

Core Components Module for Centralized Agent Framework
"""

from .centralized_coordinator import CentralizedCoordinator, AgentInfo, ConversationRecord
from .base_agent import BaseAgent, TaskMessage, FileReference
from .enums import AgentCapability, AgentStatus, ConversationState

__all__ = [
    'CentralizedCoordinator',
    'AgentInfo', 
    'ConversationRecord',
    'BaseAgent',
    'TaskMessage',
    'FileReference', 
    'AgentCapability',
    'AgentStatus',
    'ConversationState'
]