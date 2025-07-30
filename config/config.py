#!/usr/bin/env python3
"""
配置管理

Configuration Management for Centralized Agent Framework
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "dashscope"
    model_name: str = "qwen-turbo"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """后初始化处理"""
        # 从环境变量读取API密钥
        if not self.api_key:
            if self.provider == "dashscope":
                self.api_key = os.getenv("CIRCUITPILOT_DASHSCOPE_API_KEY", "")
            elif self.provider == "openai":
                self.api_key = os.getenv("CIRCUITPILOT_OPENAI_API_KEY", "")
        
        # 设置默认API URL
        if not self.api_base_url:
            if self.provider == "dashscope":
                self.api_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif self.provider == "openai":
                self.api_base_url = "https://api.openai.com/v1"


@dataclass
class CoordinatorConfig:
    """协调者配置"""
    max_conversation_iterations: int = 20
    conversation_timeout: int = 600  # 10分钟
    max_workflow_iterations: int = 5
    quality_threshold: float = 0.7
    
    # NextSpeaker决策配置
    decision_temperature: float = 0.4
    decision_max_tokens: int = 1000
    
    # 任务分析配置
    analysis_temperature: float = 0.3
    analysis_max_tokens: int = 1500


@dataclass
class AgentConfig:
    """智能体配置"""
    default_timeout: float = 120.0
    max_file_cache_size: int = 100
    enable_file_cache: bool = True
    
    # 工具调用配置
    tool_call_timeout: float = 30.0
    max_tool_retries: int = 3


@dataclass 
class FrameworkConfig:
    """框架总配置"""
    # 子配置
    llm: LLMConfig
    coordinator: CoordinatorConfig
    agent: AgentConfig
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 输出配置
    output_dir: str = "./output"
    enable_detailed_logging: bool = True
    
    def __init__(self, 
                 llm_config: Optional[LLMConfig] = None,
                 coordinator_config: Optional[CoordinatorConfig] = None,
                 agent_config: Optional[AgentConfig] = None,
                 **kwargs):
        """初始化框架配置"""
        self.llm = llm_config or LLMConfig()
        self.coordinator = coordinator_config or CoordinatorConfig()
        self.agent = agent_config or AgentConfig()
        
        # 设置其他配置
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def from_env(cls) -> 'FrameworkConfig':
        """从环境变量创建配置"""
        # LLM配置
        llm_config = LLMConfig(
            provider=os.getenv("CAF_LLM_PROVIDER", "dashscope"),
            model_name=os.getenv("CAF_LLM_MODEL", "qwen-turbo"),
            temperature=float(os.getenv("CAF_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("CAF_LLM_MAX_TOKENS", "4096"))
        )
        
        # 协调者配置
        coordinator_config = CoordinatorConfig(
            max_conversation_iterations=int(os.getenv("CAF_MAX_ITERATIONS", "20")),
            quality_threshold=float(os.getenv("CAF_QUALITY_THRESHOLD", "0.7"))
        )
        
        # 智能体配置
        agent_config = AgentConfig(
            default_timeout=float(os.getenv("CAF_AGENT_TIMEOUT", "120.0")),
            enable_file_cache=os.getenv("CAF_ENABLE_CACHE", "true").lower() == "true"
        )
        
        return cls(
            llm_config=llm_config,
            coordinator_config=coordinator_config,
            agent_config=agent_config,
            log_level=os.getenv("CAF_LOG_LEVEL", "INFO"),
            output_dir=os.getenv("CAF_OUTPUT_DIR", "./output")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "llm": self.llm.__dict__,
            "coordinator": self.coordinator.__dict__,
            "agent": self.agent.__dict__,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "output_dir": self.output_dir,
            "enable_detailed_logging": self.enable_detailed_logging
        }