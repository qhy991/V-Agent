"""
统一的LLM客户端管理器
整合所有智能体的LLM调用逻辑，消除重复代码
"""

import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.schema_system.framework_config import FrameworkConfig
from llm_integration.enhanced_llm_client import OptimizedLLMClient


class LLMCallType(Enum):
    """LLM调用类型"""
    FUNCTION_CALLING = "function_calling"
    TRADITIONAL = "traditional"
    OPTIMIZED = "optimized"


@dataclass
class LLMCallContext:
    """LLM调用上下文"""
    conversation_id: str
    agent_id: str
    role: str
    is_first_call: bool
    conversation_length: int
    total_length: int
    system_prompt_hash: Optional[str] = None


class LLMClientManager:
    """统一的LLM客户端管理器"""
    
    def __init__(self, agent_id: str, role: str, config: FrameworkConfig):
        self.agent_id = agent_id
        self.role = role
        self.config = config
        self.llm_client = OptimizedLLMClient(config.llm)
        self.logger = logging.getLogger(f"LLMClientManager.{agent_id}")
        
        # 性能统计
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_duration": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def call_llm_for_function_calling(self, conversation: List[Dict[str, str]], 
                                          system_prompt_builder=None) -> str:
        """统一的LLM调用方法 - 提取自三个智能体的共同逻辑"""
        start_time = time.time()
        self.stats["total_calls"] += 1
        
        try:
            # 生成对话ID
            conversation_id = f"{self.agent_id}_{int(time.time())}"
            
            # 构建用户消息
            user_message = self._build_user_message(conversation)
            
            # 判断是否首次调用
            assistant_messages = [msg for msg in conversation if msg["role"] == "assistant"]
            is_first_call = len(assistant_messages) == 0
            
            # 构建调用上下文
            context = LLMCallContext(
                conversation_id=conversation_id,
                agent_id=self.agent_id,
                role=self.role,
                is_first_call=is_first_call,
                conversation_length=len(conversation),
                total_length=sum(len(msg.get('content', '')) for msg in conversation)
            )
            
            self.logger.info(f"🔄 [{self.role.upper()}] 准备LLM调用 - 对话历史长度: {len(conversation)}, assistant消息数: {len(assistant_messages)}, 是否首次调用: {is_first_call}")
            
            # 获取System Prompt
            system_prompt = None
            if is_first_call and system_prompt_builder:
                system_prompt = system_prompt_builder()
                self.logger.debug(f"📝 [{self.role.upper()}] 首次调用 - 构建System Prompt - 长度: {len(system_prompt)}")
            
            # 调用优化的LLM客户端
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=conversation_id,
                user_message=user_message.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
            
            # 记录成功
            duration = time.time() - start_time
            self.stats["successful_calls"] += 1
            self.stats["total_duration"] += duration
            
            self.logger.info(f"🔍 [{self.role.upper()}] LLM响应长度: {len(response)}")
            
            return response
            
        except Exception as e:
            # 记录失败
            duration = time.time() - start_time
            self.stats["failed_calls"] += 1
            self.stats["total_duration"] += duration
            
            self.logger.error(f"❌ [{self.role.upper()}] 优化LLM调用失败: {str(e)}")
            
            # 回退到传统方式
            self.logger.warning("⚠️ 回退到传统LLM调用方式")
            return await self._call_llm_traditional(conversation, system_prompt_builder)
    
    async def _call_llm_traditional(self, conversation: List[Dict[str, str]], 
                                   system_prompt_builder=None) -> str:
        """传统LLM调用方法 - 统一实现"""
        llm_start_time = time.time()
        
        try:
            # 使用统一日志系统记录LLM调用开始
            from core.unified_logging_system import get_global_logging_system
            logging_system = get_global_logging_system()
            
            # 计算对话总长度
            total_length = sum(len(msg.get('content', '')) for msg in conversation)
            conversation_id = f"{self.agent_id}_{int(time.time())}"
            
            # 记录LLM调用开始
            logging_system.log_llm_call(
                agent_id=self.agent_id,
                model_name="claude-3.5-sonnet",
                prompt_length=total_length,
                conversation_length=len(conversation),
                conversation_id=conversation_id
            )
            
            # 构建完整的prompt
            full_prompt = ""
            system_prompt = system_prompt_builder() if system_prompt_builder else ""
            
            for msg in conversation:
                if msg["role"] == "system":
                    system_prompt = msg["content"]  # 覆盖默认system prompt
                elif msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    full_prompt += f"Assistant: {msg['content']}\n\n"
            
            # 调用传统LLM客户端
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000
            )
            
            # 记录LLM调用成功
            duration = time.time() - llm_start_time
            logging_system.log_llm_call(
                agent_id=self.agent_id,
                model_name="claude-3.5-sonnet",
                prompt_length=total_length,
                response_length=len(response),
                duration=duration,
                success=True,
                conversation_id=conversation_id
            )
            
            return response
            
        except Exception as e:
            # 记录LLM调用失败
            duration = time.time() - llm_start_time
            logging_system.log_llm_call(
                agent_id=self.agent_id,
                model_name="claude-3.5-sonnet",
                prompt_length=total_length,
                duration=duration,
                success=False,
                error_info={"error": str(e)},
                conversation_id=conversation_id
            )
            
            self.logger.error(f"❌ [{self.role.upper()}] 传统LLM调用失败: {str(e)}")
            raise
    
    def _build_user_message(self, conversation: List[Dict[str, str]]) -> str:
        """构建用户消息"""
        user_message = ""
        for msg in conversation:
            if msg["role"] == "user":
                user_message += f"{msg['content']}\n\n"
            elif msg["role"] == "assistant":
                user_message += f"Assistant: {msg['content']}\n\n"
        return user_message
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_calls = self.stats["total_calls"]
        if total_calls == 0:
            return self.stats
        
        return {
            **self.stats,
            "success_rate": self.stats["successful_calls"] / total_calls,
            "average_duration": self.stats["total_duration"] / total_calls,
            "cache_hit_rate": self.stats["cache_hits"] / max(total_calls, 1)
        } 