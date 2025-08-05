#!/usr/bin/env python3
"""
对话配置管理
用于控制对话历史显示和管理行为
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ConversationConfig:
    """对话配置类"""
    
    # 显示优化配置
    enable_display_optimization: bool = True  # 启用显示优化
    max_display_rounds: int = 1  # 最大显示轮数
    enable_compact_mode: bool = True  # 启用紧凑模式
    max_response_display_length: int = 500  # 最大响应显示长度
    
    # 对话历史管理
    max_history_turns: int = 3  # 最大保留历史轮数
    enable_history_compression: bool = True  # 启用历史压缩
    auto_cleanup_history: bool = True  # 自动清理历史
    
    # Ollama适配配置
    optimize_for_ollama: bool = True  # 为Ollama优化
    ollama_max_context_length: int = 4000  # Ollama最大上下文长度
    
    @classmethod
    def from_env(cls) -> 'ConversationConfig':
        """从环境变量创建配置"""
        # 尝试加载.env文件
        try:
            from pathlib import Path
            env_file = Path(__file__).parent.parent / '.env'
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ.setdefault(key.strip(), value.strip())
        except Exception:
            pass  # 忽略.env文件加载错误
        
        return cls(
            enable_display_optimization=os.getenv('CONVERSATION_DISPLAY_OPTIMIZATION', 'true').lower() == 'true',
            max_display_rounds=int(os.getenv('CONVERSATION_MAX_DISPLAY_ROUNDS', '1')),
            enable_compact_mode=os.getenv('CONVERSATION_COMPACT_MODE', 'true').lower() == 'true',
            max_response_display_length=int(os.getenv('CONVERSATION_MAX_RESPONSE_LENGTH', '500')),
            max_history_turns=int(os.getenv('CONVERSATION_MAX_HISTORY_TURNS', '3')),
            enable_history_compression=os.getenv('CONVERSATION_HISTORY_COMPRESSION', 'true').lower() == 'true',
            auto_cleanup_history=os.getenv('CONVERSATION_AUTO_CLEANUP', 'true').lower() == 'true',
            optimize_for_ollama=os.getenv('CONVERSATION_OPTIMIZE_OLLAMA', 'true').lower() == 'true',
            ollama_max_context_length=int(os.getenv('CONVERSATION_OLLAMA_MAX_CONTEXT', '4000'))
        )
    
    def should_optimize_display(self) -> bool:
        """是否应该优化显示"""
        return self.enable_display_optimization
    
    def should_compress_history(self) -> bool:
        """是否应该压缩历史"""
        return self.enable_history_compression
    
    def get_truncated_response(self, response: str) -> str:
        """获取截断的响应"""
        if len(response) <= self.max_response_display_length:
            return response
        return response[:self.max_response_display_length] + "...[已截断]"


# 全局配置实例
conversation_config = ConversationConfig.from_env()


def get_conversation_config() -> ConversationConfig:
    """获取对话配置"""
    return conversation_config


def update_conversation_config(**kwargs) -> None:
    """更新对话配置"""
    global conversation_config
    for key, value in kwargs.items():
        if hasattr(conversation_config, key):
            setattr(conversation_config, key, value)


if __name__ == "__main__":
    # 测试配置
    config = ConversationConfig.from_env()
    print(f"显示优化: {config.enable_display_optimization}")
    print(f"最大显示轮数: {config.max_display_rounds}")
    print(f"紧凑模式: {config.enable_compact_mode}")
    print(f"最大响应长度: {config.max_response_display_length}")
    print(f"最大历史轮数: {config.max_history_turns}")
    print(f"历史压缩: {config.enable_history_compression}")
    print(f"为Ollama优化: {config.optimize_for_ollama}")