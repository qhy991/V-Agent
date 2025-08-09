#!/usr/bin/env python3
"""
中心化智能体框架

Centralized Agent Framework (CAF)
A centralized coordination system for multi-agent collaboration in Verilog design tasks.
"""

__version__ = "1.0.0"
__author__ = "CircuitPilot Team"
__description__ = "中心化智能体协调框架，用于Verilog设计任务的多智能体协作"

# 核心组件导入
from config.config import FrameworkConfig, LLMConfig, CoordinatorConfig, AgentConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.base_agent import BaseAgent
from core.types import TaskMessage, FileReference
from core.enums import AgentCapability, AgentStatus, ConversationState

# 专业智能体导入
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# LLM集成
from llm_integration.enhanced_llm_client import EnhancedLLMClient

# 工具系统
from tools.tool_registry import ToolRegistry, ToolPermission

__all__ = [
    # 版本信息
    "__version__",
    "__author__", 
    "__description__",
    
    # 配置类
    "FrameworkConfig",
    "LLMConfig", 
    "CoordinatorConfig",
    "AgentConfig",
    
    # 核心组件
    "LLMCoordinatorAgent",
    "BaseAgent",
    "TaskMessage",
    "FileReference",
    
    # 枚举类型
    "AgentCapability",
    "AgentStatus", 
    "ConversationState",
    
    # 专业智能体
    "RealVerilogDesignAgent",
    "RealCodeReviewAgent",
    
    # LLM集成
    "EnhancedLLMClient",
    
    # 工具系统
    "ToolRegistry",
    "ToolPermission"
]

# 框架信息
def get_framework_info():
    """获取框架信息"""
    return {
        "name": "CentralizedAgentFramework",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "components": {
            "coordinator": "LLMCoordinatorAgent - LLM驱动的协调智能体",
            "agents": [
                "RealVerilogDesignAgent - 真实LLM驱动的Verilog设计智能体", 
                "RealCodeReviewAgent - 真实LLM驱动的代码审查智能体"
            ],
            "llm_integration": "EnhancedLLMClient - 增强LLM客户端",
            "tools": "ToolRegistry - 工具注册系统"
        }
    }

# 快捷创建函数
def create_framework(llm_provider: str = "dashscope", 
                    model_name: str = "qwen-turbo",
                    api_key: str = None) -> tuple:
    """
    快捷创建框架实例
    
    Args:
        llm_provider: LLM提供商
        model_name: 模型名称
        api_key: API密钥
    
    Returns:
        (coordinator, agents) - 协调者和智能体列表
    """
    # 创建配置
    llm_config = LLMConfig(
        provider=llm_provider,
        model_name=model_name,
        api_key=api_key
    )
    config = FrameworkConfig(llm_config=llm_config)
    
    # 创建LLM客户端
    llm_client = None
    if api_key:
        llm_client = EnhancedLLMClient(llm_config)
    
    # 创建协调者
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建智能体
    agents = [
        RealVerilogDesignAgent(config),
        RealCodeReviewAgent(config)
    ]
    
    # 注册智能体
    for agent in agents:
        coordinator.register_agent(agent)
    
    return coordinator, agents