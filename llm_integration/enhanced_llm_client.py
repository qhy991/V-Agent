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
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from config.config import LLMConfig


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
        
        self.logger.info(f"🚀 初始化LLM客户端 - 提供商: {provider_name}, 模型: {config.model_name}")
    
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
        
        # 记录请求开始
        self.logger.info(f"🤖 开始LLM请求 - 模型: {self.config.model_name}, JSON模式: {json_mode}")
        
        # 详细记录对话内容
        if system_prompt:
            self.logger.info(f"📋 System Prompt ({len(system_prompt)} 字符):")
            self.logger.info(f"📋 {system_prompt}")
        
        self.logger.info(f"👤 User Prompt ({len(prompt)} 字符):")
        self.logger.info(f"👤 {prompt}")
        
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
                    
                    # 详细记录响应内容
                    self.logger.info(f"🤖 LLM响应 ({len(response_content)} 字符, {duration:.2f}s):")
                    self.logger.info(f"🤖 {response_content}")
                    
                    self.logger.debug(f"📊 LLM统计 - 耗时: {duration:.2f}s, 尝试次数: {attempt + 1}, 总Token: {len(prompt) + len(response_content)}")
                    return response_content
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                self.stats["connection_errors"] += 1
                delay = min(base_delay * (self.retry_config["exponential_base"] ** attempt), 
                          self.retry_config["max_delay"])
                self.logger.warning(f"LLM连接失败 (尝试 {attempt + 1}/{max_retries}): {type(e).__name__}, 将在 {delay:.1f}s后重试")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
            except Exception as e:
                last_exception = e
                self.stats["errors"] += 1
                self.logger.error(f"LLM请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay)
        
        # 所有重试都失败了
        self.stats["errors"] += 1
        error_msg = f"LLM请求最终失败，已尝试 {max_retries} 次: {str(last_exception)}"
        self.logger.error(error_msg)
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