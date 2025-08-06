#!/usr/bin/env python3
"""
Conversation Manager - 对话管理器
=====================================

从BaseAgent中提取的对话管理功能，负责管理智能体的对话历史和上下文。
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 导入增强的日志系统
try:
    from ..unified_logging_system import get_global_logging_system
except ImportError:
    get_global_logging_system = None


@dataclass
class ConversationMessage:
    """对话消息"""
    role: str
    content: str
    timestamp: float
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, agent_id: str, logger: Optional[logging.Logger] = None):
        self.agent_id = agent_id
        self.logger = logger or logging.getLogger(__name__)
        
        # 对话存储 - 支持多个对话ID
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        
        # 当前活跃的对话ID
        self.current_conversation_id: Optional[str] = None
        
        # LLM上下文优化相关
        self.llm_optimization_enabled = False
        self.llm_context_cache: Dict[str, Any] = {}
        self.llm_stats = {
            'total_calls': 0,
            'total_tokens': 0,
            'context_hits': 0,
            'context_misses': 0
        }
        
        # 增强日志系统集成
        self.enhanced_logging_enabled = get_global_logging_system is not None
        if self.enhanced_logging_enabled:
            try:
                self.logging_system = get_global_logging_system()
            except:
                self.enhanced_logging_enabled = False
                self.logging_system = None
    
    def start_conversation(self, conversation_id: str) -> None:
        """开始一个新的对话"""
        self.current_conversation_id = conversation_id
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            self.logger.debug(f"📝 [CONV] 开始新对话: {conversation_id}")
            
            # 记录到增强日志系统
            if self.enhanced_logging_enabled and self.logging_system:
                try:
                    from ..unified_logging_system import EventCategory, LogLevel
                    self.logging_system.log_event(
                        level=LogLevel.INFO,
                        category=EventCategory.CONVERSATION,
                        title=f"开始新对话",
                        message=f"对话ID: {conversation_id}",
                        agent_id=self.agent_id,
                        conversation_id=conversation_id,
                        details={"conversation_id": conversation_id, "action": "start"}
                    )
                except Exception as e:
                    self.logger.warning(f"⚠️ 增强日志记录失败: {e}")
        else:
            self.logger.debug(f"📝 [CONV] 恢复对话: {conversation_id} (已有 {len(self.conversations[conversation_id])} 条消息)")
    
    def add_message(self, role: str, content: str, agent_id: str = None, 
                   conversation_id: str = None, metadata: Dict[str, Any] = None) -> None:
        """添加对话消息"""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id:
            raise ValueError("No active conversation. Call start_conversation() first.")
        
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            agent_id=agent_id or self.agent_id,
            metadata=metadata or {}
        )
        
        self.conversations[conv_id].append(message)
        
        self.logger.debug(f"📝 [CONV] 添加消息: {role} ({len(content)} 字符) 到对话 {conv_id}")
        
        # 记录到增强日志系统
        if self.enhanced_logging_enabled and self.logging_system:
            try:
                from ..unified_logging_system import EventCategory, LogLevel
                self.logging_system.log_event(
                    level=LogLevel.INFO,
                    category=EventCategory.CONVERSATION,
                    title=f"消息添加: {role}",
                    message=f"内容长度: {len(content)}字符",
                    agent_id=agent_id or self.agent_id,
                    conversation_id=conv_id,
                    details={
                        "role": role,
                        "content_length": len(content),
                        "content_preview": content[:100] + "..." if len(content) > 100 else content,
                        "metadata": metadata or {},
                        "message_count": len(self.conversations[conv_id])
                    }
                )
            except Exception as e:
                self.logger.warning(f"⚠️ 消息日志记录失败: {e}")
    
    def get_conversation_history(self, conversation_id: str = None, 
                               as_dict: bool = True) -> List[Any]:
        """获取对话历史"""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id or conv_id not in self.conversations:
            return []
        
        messages = self.conversations[conv_id]
        
        if as_dict:
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'agent_id': msg.agent_id,
                    'metadata': msg.metadata
                }
                for msg in messages
            ]
        else:
            return messages
    
    def get_conversation_for_llm(self, conversation_id: str = None) -> List[Dict[str, str]]:
        """获取用于LLM的对话格式"""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id or conv_id not in self.conversations:
            return []
        
        return [
            {
                'role': msg.role,
                'content': msg.content
            }
            for msg in self.conversations[conv_id]
        ]
    
    def clear_conversation(self, conversation_id: str = None) -> None:
        """清除指定对话"""
        conv_id = conversation_id or self.current_conversation_id
        if conv_id and conv_id in self.conversations:
            message_count = len(self.conversations[conv_id])
            del self.conversations[conv_id]
            self.logger.debug(f"📝 [CONV] 清除对话: {conv_id}")
            
            # 记录到增强日志系统
            if self.enhanced_logging_enabled and self.logging_system:
                try:
                    from ..unified_logging_system import EventCategory, LogLevel
                    self.logging_system.log_event(
                        level=LogLevel.INFO,
                        category=EventCategory.CONVERSATION,
                        title=f"清除对话",
                        message=f"对话ID: {conv_id}",
                        agent_id=self.agent_id,
                        conversation_id=conv_id,
                        details={"conversation_id": conv_id, "message_count": message_count, "action": "clear"}
                    )
                except Exception as e:
                    self.logger.warning(f"⚠️ 清除对话日志记录失败: {e}")
            
            if conv_id == self.current_conversation_id:
                self.current_conversation_id = None
    
    def clear_all_conversations(self) -> None:
        """清除所有对话"""
        self.conversations.clear()
        self.current_conversation_id = None
        self.logger.debug(f"📝 [CONV] 清除所有对话")
    
    def get_conversation_summary(self, conversation_id: str = None) -> Dict[str, Any]:
        """获取对话摘要"""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id or conv_id not in self.conversations:
            return {
                'conversation_id': conv_id,
                'message_count': 0,
                'agent_count': 0,
                'total_length': 0,
                'start_time': None,
                'end_time': None,
                'duration': 0
            }
        
        messages = self.conversations[conv_id]
        if not messages:
            return {
                'conversation_id': conv_id,
                'message_count': 0,
                'agent_count': 0,
                'total_length': 0,
                'start_time': None,
                'end_time': None,
                'duration': 0
            }
        
        agent_ids = set(msg.agent_id for msg in messages if msg.agent_id)
        total_length = sum(len(msg.content) for msg in messages)
        start_time = min(msg.timestamp for msg in messages)
        end_time = max(msg.timestamp for msg in messages)
        
        return {
            'conversation_id': conv_id,
            'message_count': len(messages),
            'agent_count': len(agent_ids),
            'total_length': total_length,
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'participating_agents': list(agent_ids)
        }
    
    def get_all_conversations_summary(self) -> Dict[str, Any]:
        """获取所有对话的摘要"""
        summary = {
            'total_conversations': len(self.conversations),
            'current_conversation': self.current_conversation_id,
            'enhanced_logging_enabled': self.enhanced_logging_enabled,
            'conversations': {
                conv_id: self.get_conversation_summary(conv_id)
                for conv_id in self.conversations
            }
        }
        
        # 如果启用了增强日志，添加详细信息
        if self.enhanced_logging_enabled and self.logging_system:
            try:
                enhanced_data = self.logging_system.export_data()
                summary['enhanced_conversation_data'] = {
                    'total_llm_conversations': enhanced_data.get('conversation_summary', {}).get('total_llm_calls', 0),
                    'total_conversation_threads': enhanced_data.get('conversation_summary', {}).get('total_conversations', 0),
                    'content_logging_enabled': enhanced_data.get('conversation_summary', {}).get('content_logging_enabled', False)
                }
            except Exception as e:
                self.logger.warning(f"⚠️ 获取增强数据失败: {e}")
                
        return summary
    
    # LLM优化相关方法
    def enable_llm_optimization(self) -> None:
        """启用LLM上下文优化"""
        self.llm_optimization_enabled = True
        self.logger.debug(f"🚀 [CONV] 启用LLM上下文优化")
    
    def clear_llm_context(self, conversation_id: str = None) -> None:
        """清除LLM上下文缓存"""
        if conversation_id:
            self.llm_context_cache.pop(conversation_id, None)
        else:
            self.llm_context_cache.clear()
        self.logger.debug(f"🧹 [CONV] 清除LLM上下文缓存: {conversation_id or 'all'}")
    
    def get_llm_optimization_stats(self) -> Dict[str, Any]:
        """获取LLM优化统计信息"""
        return self.llm_stats.copy()
    
    def update_llm_stats(self, total_calls: int = None, total_tokens: int = None,
                        context_hits: int = None, context_misses: int = None) -> None:
        """更新LLM统计信息"""
        if total_calls is not None:
            self.llm_stats['total_calls'] = total_calls
        if total_tokens is not None:
            self.llm_stats['total_tokens'] = total_tokens
        if context_hits is not None:
            self.llm_stats['context_hits'] = context_hits
        if context_misses is not None:
            self.llm_stats['context_misses'] = context_misses
            
    def log_conversation_decision(self, conversation_id: str, decision_type: str,
                                 options: List[str], chosen_option: str, 
                                 reasoning: str, confidence: float = None) -> None:
        """记录对话中的决策点"""
        if self.enhanced_logging_enabled and self.logging_system:
            try:
                self.logging_system.log_decision_point(
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    decision_type=decision_type,
                    options=options,
                    chosen_option=chosen_option,
                    reasoning=reasoning,
                    confidence=confidence
                )
            except Exception as e:
                self.logger.warning(f"⚠️ 决策点记录失败: {e}")
                
    def get_conversation_thread_data(self, conversation_id: str = None) -> Dict[str, Any]:
        """获取对话线程数据（与增强日志系统集成）"""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id:
            return {}
            
        # 从增强日志系统获取线程数据
        if self.enhanced_logging_enabled and self.logging_system:
            try:
                thread_data = self.logging_system.get_conversation_thread(conv_id)
                if thread_data:
                    return thread_data
            except Exception as e:
                self.logger.warning(f"⚠️ 获取线程数据失败: {e}")
                
        # 回退到本地数据
        return self.get_conversation_summary(conv_id)