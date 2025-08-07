#!/usr/bin/env python3
"""
增强的LLM客户端 - 适配版本

Enhanced LLM Client for Centralized Agent Framework
"""

import asyncio
import aiohttp
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager
from config.config import LLMConfig


class ConversationContext:
    """对话上下文管理类"""
    
    def __init__(self, conversation_id: str, system_prompt: str = None):
        self.conversation_id = conversation_id
        self.system_prompt = system_prompt
        self.system_prompt_hash = self._hash_prompt(system_prompt) if system_prompt else None
        self.messages: List[Dict[str, str]] = []
        self.total_tokens = 0
        self.created_at = time.time()
        self.last_accessed = time.time()
        
    def _hash_prompt(self, prompt: str) -> str:
        """计算prompt的哈希值用于快速比较"""
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()
    
    def add_message(self, role: str, content: str, tokens: int = 0):
        """添加消息到上下文"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "tokens": tokens
        })
        self.total_tokens += tokens
        self.last_accessed = time.time()
    
    def get_optimized_messages(self, max_tokens: int = 8000, 
                             preserve_system: bool = True) -> List[Dict[str, str]]:
        """获取优化后的消息列表"""
        if not self.messages:
            return []
        
        # 如果总token数在限制内，直接返回
        if self.total_tokens <= max_tokens:
            return [{"role": msg["role"], "content": msg["content"]} 
                   for msg in self.messages]
        
        # 需要压缩上下文
        optimized_messages = []
        current_tokens = 0
        
        # 保留system prompt（如果需要）
        if preserve_system and self.messages[0]["role"] == "system":
            system_msg = self.messages[0]
            optimized_messages.append({
                "role": system_msg["role"], 
                "content": system_msg["content"]
            })
            current_tokens += system_msg.get("tokens", len(system_msg["content"]) // 4)
        
        # 从最新的消息开始，保留尽可能多的上下文
        for msg in reversed(self.messages):
            if msg["role"] == "system":
                continue  # system prompt已经处理过了
            
            msg_tokens = msg.get("tokens", len(msg["content"]) // 4)
            if current_tokens + msg_tokens <= max_tokens:
                optimized_messages.insert(1, {  # 插入到system prompt之后
                    "role": msg["role"], 
                    "content": msg["content"]
                })
                current_tokens += msg_tokens
            else:
                break
        
        return optimized_messages
    
    def update_system_prompt(self, new_system_prompt: str):
        """更新system prompt"""
        self.system_prompt = new_system_prompt
        self.system_prompt_hash = self._hash_prompt(new_system_prompt)
        # 清除旧消息，因为system prompt改变了
        self.messages = []
        self.total_tokens = 0


class OptimizedLLMClient:
    """优化的LLM客户端，支持智能缓存和上下文管理"""
    
    def __init__(self, config: LLMConfig, parent_client=None):
        self.config = config
        self.parent_client = parent_client  # 引用父客户端以调用其方法
        provider_name = getattr(config, 'provider', 'unknown')
        self.logger = logging.getLogger(f"OptimizedLLMClient-{provider_name}")
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "errors": 0,
            "connection_errors": 0,
            "retries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "context_optimizations": 0,
            "token_savings": 0
        }
        
        # 连接重试配置
        self.retry_config = {
            "max_retries": config.retry_attempts,
            "base_delay": config.retry_delay,
            "max_delay": 10.0,
            "exponential_base": 2.0
        }
        
        # 智能缓存系统
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.system_prompt_cache: Dict[str, str] = {}  # hash -> prompt
        self.max_contexts = 100  # 最大缓存对话数
        self.max_context_age = 3600  # 最大缓存时间（秒）
        
        # 优化配置
        self.optimization_config = {
            "enable_system_cache": True,
            "enable_context_compression": True,
            "max_context_tokens": 8000,
            "preserve_system_in_compression": True,
            "min_context_messages": 3  # 最少保留的消息数
        }
        
        self.logger.debug(f"🚀 优化LLM客户端初始化: {provider_name}, {config.model_name}")
    
    @asynccontextmanager
    async def _get_session(self) -> aiohttp.ClientSession:
        """提供一个临时的、安全关闭的aiohttp会话"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            yield session
    
    def _get_conversation_context(self, conversation_id: str) -> ConversationContext:
        """获取或创建对话上下文"""
        if conversation_id not in self.conversation_contexts:
            # 清理过期上下文
            self._cleanup_expired_contexts()
            
            # 如果达到最大数量，删除最旧的
            if len(self.conversation_contexts) >= self.max_contexts:
                oldest_id = min(self.conversation_contexts.keys(), 
                              key=lambda k: self.conversation_contexts[k].last_accessed)
                del self.conversation_contexts[oldest_id]
                self.logger.debug(f"🗑️ 删除最旧对话上下文: {oldest_id}")
            
            self.conversation_contexts[conversation_id] = ConversationContext(conversation_id)
            self.logger.debug(f"🆕 创建新对话上下文: {conversation_id}")
        
        return self.conversation_contexts[conversation_id]
    
    def _cleanup_expired_contexts(self):
        """清理过期的对话上下文"""
        current_time = time.time()
        expired_ids = [
            conv_id for conv_id, context in self.conversation_contexts.items()
            if current_time - context.last_accessed > self.max_context_age
        ]
        
        for conv_id in expired_ids:
            del self.conversation_contexts[conv_id]
            self.logger.debug(f"🗑️ 清理过期对话上下文: {conv_id}")
    
    def _should_include_system_prompt(self, context: ConversationContext, 
                                    new_system_prompt: str = None) -> bool:
        """判断是否需要在当前调用中包含system prompt"""
        if not self.optimization_config["enable_system_cache"]:
            return True
        
        # 如果没有system prompt，不需要包含
        if not new_system_prompt and not context.system_prompt:
            return False
        
        # 如果system prompt发生了变化，需要包含
        if new_system_prompt:
            new_hash = context._hash_prompt(new_system_prompt)
            if new_hash != context.system_prompt_hash:
                return True
        
        # 如果是第一次调用，需要包含
        if not context.messages:
            return True
        
        # 其他情况不需要重复包含
        return False
    
    async def send_prompt_optimized(self, 
                                  conversation_id: str,
                                  user_message: str,
                                  system_prompt: str = None,
                                  temperature: float = None,
                                  max_tokens: int = None,
                                  json_mode: bool = False,
                                  force_refresh_system: bool = False) -> str:
        """优化的提示发送方法，支持智能缓存和上下文管理"""
        start_time = time.time()
        
        # 简化日志输出 - 只记录关键信息
        self.logger.info(f"🚀 优化LLM调用 - 对话ID: {conversation_id}")
        
        # 获取对话上下文
        context = self._get_conversation_context(conversation_id)
        
        # 检查是否需要更新system prompt
        if system_prompt and (force_refresh_system or 
                             context.system_prompt_hash != context._hash_prompt(system_prompt)):
            context.update_system_prompt(system_prompt)
            self.logger.info(f"🔄 更新system prompt: {len(system_prompt)} 字符")
        
        # 判断是否包含system prompt
        include_system = force_refresh_system or self._should_include_system_prompt(context, system_prompt)
        
        # 构建消息列表
        messages = []
        
        if include_system and context.system_prompt:
            messages.append({"role": "system", "content": context.system_prompt})
            self.stats["cache_misses"] += 1
            self.logger.info(f"📋 包含system prompt: {len(context.system_prompt)} 字符")
        else:
            self.stats["cache_hits"] += 1
            self.logger.info(f"⚡ 使用缓存的system prompt")
        
        # 添加历史消息（如果启用上下文压缩）
        if self.optimization_config["enable_context_compression"]:
            optimized_messages = context.get_optimized_messages(
                max_tokens=self.optimization_config["max_context_tokens"],
                preserve_system=self.optimization_config["preserve_system_in_compression"]
            )
            
            # 🎯 新增：去重逻辑，避免重复的对话内容
            deduplicated_messages = []
            seen_contents = set()
            
            for msg in optimized_messages:
                content = msg.get("content", "")
                # 对于用户消息，检查是否包含重复的任务描述
                if msg.get("role") == "user" and "📋 协调智能体分配的任务" in content:
                    # 提取任务描述的核心部分（去除重复的上下文信息）
                    lines = content.split('\n')
                    core_content = []
                    in_task_section = False
                    
                    for line in lines:
                        if "📋 协调智能体分配的任务" in line:
                            if not in_task_section:
                                core_content.append(line)
                                in_task_section = True
                        elif in_task_section and line.strip().startswith("**"):
                            core_content.append(line)
                        elif in_task_section and line.strip() and not line.strip().startswith("**"):
                            core_content.append(line)
                        elif in_task_section and not line.strip():
                            break
                    
                    content = '\n'.join(core_content)
                
                # 检查是否已经见过相同的内容
                content_hash = hash(content)
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    deduplicated_messages.append(msg)
                else:
                    self.logger.info(f"🔄 [DEDUP_DEBUG] 跳过重复内容: {content[:50]}...")
            
            messages.extend(deduplicated_messages)
            
            if len(deduplicated_messages) < len(optimized_messages):
                self.stats["context_optimizations"] += 1
                self.logger.debug(f"🗜️ 上下文压缩和去重: {len(optimized_messages)} -> {len(deduplicated_messages)} 消息")
        else:
            # 即使不启用压缩，也要进行去重
            deduplicated_messages = []
            seen_contents = set()
            
            for msg in context.messages:
                content = msg.get("content", "")
                content_hash = hash(content)
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    deduplicated_messages.append(msg)
            
            messages.extend(deduplicated_messages)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 记录最终发送的消息结构
        self.logger.info(f"📤 [SYSTEM_PROMPT_DEBUG] 最终消息结构: {len(messages)} 条消息")
        for i, msg in enumerate(messages):
            self.logger.info(f"📤 [SYSTEM_PROMPT_DEBUG] 消息 {i}: role={msg['role']}, 长度={len(msg['content'])}")
        
        # 记录token使用情况
        total_tokens = sum(len(msg["content"]) // 4 for msg in messages)
        self.stats["total_tokens"] += total_tokens
        
        # 调用原始发送方法
        try:
            response = await self._send_prompt_internal(messages, temperature, max_tokens, json_mode)
            
            # 更新上下文
            context.add_message("user", user_message, len(user_message) // 4)
            context.add_message("assistant", response, len(response) // 4)
            
            # 记录性能统计
            duration = time.time() - start_time
            self.stats["total_requests"] += 1
            self.stats["total_time"] += duration
            
            self.logger.info(f"✅ 优化请求完成 - Token: {total_tokens}, 时间: {duration:.2f}s")
            
            return response
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"❌ 优化请求失败: {str(e)}")
            raise
    
    async def _send_prompt_internal(self, messages: List[Dict[str, str]],
                                  temperature: float = None,
                                  max_tokens: int = None,
                                  json_mode: bool = False) -> str:
        """内部发送方法，复用原有的发送逻辑"""
        # 构建prompt和system_prompt
        system_prompt = None
        user_prompt = ""
        
        for msg in messages:
            # 🔧 修复：安全处理None值
            if msg is None or "role" not in msg:
                continue
                
            content = msg.get("content", "")
            if content is None:
                content = ""
                
            if msg["role"] == "system":
                system_prompt = content
            elif msg["role"] == "user":
                user_prompt += f"User: {content}\n\n"
            elif msg["role"] == "assistant":
                user_prompt += f"Assistant: {content}\n\n"
        
        # 🔧 修复：确保user_prompt不为None
        user_prompt_str = user_prompt if user_prompt is not None else ""
        return await self._send_prompt_direct(user_prompt_str.strip(), system_prompt, 
                                            temperature, max_tokens, json_mode)
    
    async def _send_prompt_direct(self, prompt: str, system_prompt: str = None,
                                temperature: float = None, max_tokens: int = None,
                                json_mode: bool = False) -> str:
        """直接发送提示，委托给父客户端"""
        if not self.parent_client:
            raise Exception("父客户端未设置，无法发送请求")
        
        # 委托给父客户端的send_prompt方法
        return await self.parent_client.send_prompt(
            prompt, system_prompt, temperature, max_tokens, json_mode
        )
    
    def _get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        return self.stats["cache_hits"] / total if total > 0 else 0.0
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            **self.stats,
            "cache_hit_rate": self._get_cache_hit_rate(),
            "active_contexts": len(self.conversation_contexts),
            "average_time": self.stats["total_time"] / max(1, self.stats["total_requests"]),
            "success_rate": 1 - (self.stats["errors"] / max(1, self.stats["total_requests"]))
        }
    
    def clear_conversation_context(self, conversation_id: str):
        """清除特定对话的上下文"""
        if conversation_id in self.conversation_contexts:
            del self.conversation_contexts[conversation_id]
            self.logger.info(f"🗑️ 清除对话上下文: {conversation_id}")
    
    def clear_all_contexts(self):
        """清除所有对话上下文"""
        self.conversation_contexts.clear()
        self.logger.info("🗑️ 清除所有对话上下文")


class EnhancedLLMClient:
    """
    增强的LLM客户端，支持异步请求和多种提供商
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        provider_name = getattr(config, 'provider', 'unknown')
        self.logger = logging.getLogger(f"LLMClient-{provider_name}")
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "errors": 0,
            "connection_errors": 0,
            "retries": 0
        }
        
        # 连接重试配置
        self.retry_config = {
            "max_retries": config.retry_attempts,
            "base_delay": config.retry_delay,
            "max_delay": 10.0,
            "exponential_base": 2.0
        }
        
        # 创建优化客户端实例，传入自身作为父客户端
        self.optimized_client = OptimizedLLMClient(config, parent_client=self)
        
        self.logger.debug(f"🚀 LLM客户端初始化: {provider_name}, {config.model_name}")
    
    @asynccontextmanager
    async def _get_session(self) -> aiohttp.ClientSession:
        """提供一个临时的、安全关闭的aiohttp会话"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            yield session
    
    async def generate_async(self, prompt: str, system_prompt: str = None,
                           temperature: float = None, max_tokens: int = None) -> str:
        """异步生成响应"""
        return await self.send_prompt(prompt, system_prompt, temperature, max_tokens)
    
    async def send_prompt(self, prompt: str, system_prompt: str = None,
                         temperature: float = None, max_tokens: int = None,
                         json_mode: bool = False) -> str:
        """发送提示到LLM并返回响应"""
        start_time = time.time()
        max_retries = self.retry_config["max_retries"]
        base_delay = self.retry_config["base_delay"]
        last_exception = None
        
        # 记录请求开始 - 简化输出
        self.logger.info(f"🤖 LLM调用 - 模型: {self.config.model_name}")
        
        # 只记录关键信息
        if system_prompt:
            self.logger.info(f"📋 System Prompt: {len(system_prompt)} 字符")
        
        self.logger.info(f"👤 User Prompt: {len(prompt)} 字符")
        self.logger.info("="*50)
        
        for attempt in range(max_retries):
            try:
                async with self._get_session() as session:
                    # 使用配置中的默认值
                    temperature = temperature or self.config.temperature
                    max_tokens = max_tokens or self.config.max_tokens
                    
                    self.logger.debug(f"🔧 LLM参数 - 温度: {temperature}, 最大Token: {max_tokens}")
                    
                    # 判断提供商
                    provider_name = self.config.provider
                    base_url = self.config.api_base_url
                    
                    if (provider_name.lower() in ["local", "ollama"] or
                        "11434" in str(base_url) or
                        "ollama" in str(base_url).lower()):
                        response_content = await self._send_ollama_request(
                            session, prompt, system_prompt, temperature, max_tokens, json_mode)
                    else:
                        response_content = await self._send_openai_compatible_request(
                            session, prompt, system_prompt, temperature, max_tokens, json_mode)
                    
                    # 更新统计
                    duration = time.time() - start_time
                    self.stats["total_requests"] += 1
                    self.stats["total_time"] += duration
                    self.stats["total_tokens"] += len(prompt) + len(response_content)
                    if attempt > 0:
                        self.stats["retries"] += 1
                    
                    # 记录响应内容 - 简化输出
                    self.logger.info(f"🤖 LLM响应: {len(response_content)} 字符, {duration:.2f}s")
                    self.logger.info(f"🤖 响应内容: {response_content[:200]}{'...' if len(response_content) > 200 else ''}")
                    self.logger.info("="*50)
                    
                    return response_content
                    
            except aiohttp.ClientError as e:
                last_exception = e
                self.stats["connection_errors"] += 1
                self.logger.warning(f"⚠️ 连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    delay = min(base_delay * (self.retry_config["exponential_base"] ** attempt), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
                else:
                    break
                    
            except Exception as e:
                last_exception = e
                self.stats["errors"] += 1
                self.logger.error(f"❌ 请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    delay = min(base_delay * (self.retry_config["exponential_base"] ** attempt), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
                else:
                    break
        
        # 所有重试都失败了
        error_msg = f"LLM请求失败，已重试 {max_retries} 次。最后错误: {str(last_exception)}"
        self.logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    async def _send_openai_compatible_request(self, session: aiohttp.ClientSession, 
                                            prompt: str, system_prompt: str,
                                            temperature: float, max_tokens: int, 
                                            json_mode: bool) -> str:
        """发送OpenAI兼容请求"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
            
            response_data = await response.json()
            return response_data["choices"][0]["message"]["content"]
    
    async def _send_ollama_request(self, session: aiohttp.ClientSession,
                                 prompt: str, system_prompt: str,
                                 temperature: float, max_tokens: int,
                                 json_mode: bool) -> str:
        """发送Ollama请求"""
        
        # 构建Ollama格式的prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        payload = {
            "model": self.config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        url = f"{self.config.api_base_url.rstrip('/')}/api/generate"
        
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
            
            response_data = await response.json()
            return response_data.get("response", "")
    
    async def close(self):
        """关闭客户端并记录统计信息"""
        self.logger.info(f"LLM客户端已关闭 - 统计: {self.get_stats()}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_requests = max(1, self.stats["total_requests"])
        return {
            **self.stats,
            "average_time": self.stats["total_time"] / total_requests,
            "success_rate": 1 - (self.stats["errors"] / total_requests)
        }
    
    # 新增：优化方法接口
    async def send_prompt_optimized(self, 
                                  conversation_id: str,
                                  user_message: str,
                                  system_prompt: str = None,
                                  temperature: float = None,
                                  max_tokens: int = None,
                                  json_mode: bool = False,
                                  force_refresh_system: bool = False) -> str:
        """优化的提示发送方法"""
        return await self.optimized_client.send_prompt_optimized(
            conversation_id, user_message, system_prompt, 
            temperature, max_tokens, json_mode, force_refresh_system
        )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return self.optimized_client.get_optimization_stats()
    
    def clear_conversation_context(self, conversation_id: str):
        """清除特定对话的上下文"""
        self.optimized_client.clear_conversation_context(conversation_id)
    
    def clear_all_contexts(self):
        """清除所有对话上下文"""
        self.optimized_client.clear_all_contexts()