#!/usr/bin/env python3
"""
基础智能体类 - 支持工具调用和文件操作

Base Agent with Tool Calling and File Operations
"""

import asyncio
import logging
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .enums import AgentCapability, AgentStatus
from tools.tool_registry import ToolRegistry, ToolPermission
from .agent_prompts import agent_prompt_manager


@dataclass
class FileReference:
    """文件引用"""
    file_path: str
    file_type: str  # "verilog", "testbench", "report", "config"
    description: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "description": self.description,
            "metadata": self.metadata or {}
        }


@dataclass
class TaskMessage:
    """任务消息 - 支持文件路径传递"""
    task_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: str
    file_references: List[FileReference] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "file_references": [ref.to_dict() for ref in (self.file_references or [])],
            "metadata": self.metadata or {}
        }


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, agent_id: str, role: str = None, capabilities: Set[AgentCapability] = None):
        self.agent_id = agent_id
        self.role = role or "base_agent"
        self._capabilities = capabilities or set()
        self.status = AgentStatus.IDLE
        
        # 设置日志
        self.logger = logging.getLogger(f"Agent.{self.agent_id}")
        
        # 工具调用系统
        self.tool_registry = ToolRegistry()
        self.enable_tool_calling()
        
        # 文件缓存
        self.file_cache: Dict[str, str] = {}
        self.file_metadata_cache: Dict[str, Dict] = {}
        
        # 任务历史
        self.task_history: List[Dict[str, Any]] = []
        
        # 生成system prompt
        self.system_prompt = agent_prompt_manager.get_system_prompt(self.role, self._capabilities)
        
        self.logger.info(f"✅ {self.__class__.__name__} 初始化完成")
        self.logger.debug(f"📝 System prompt 长度: {len(self.system_prompt)} 字符")
    
    def enable_tool_calling(self):
        """启用工具调用能力"""
        # 根据能力设置权限
        permissions = {ToolPermission.READ_ONLY}
        
        if AgentCapability.CODE_GENERATION in self._capabilities:
            permissions.add(ToolPermission.WRITE_FILES)
            permissions.add(ToolPermission.EXECUTE_SAFE)
            permissions.add(ToolPermission.DATABASE_READ)
        
        if AgentCapability.TASK_COORDINATION in self._capabilities:
            permissions.add(ToolPermission.WRITE_FILES)
            permissions.add(ToolPermission.EXECUTE_SAFE)
            permissions.add(ToolPermission.DATABASE_READ)
            permissions.add(ToolPermission.DATABASE_WRITE)
        
        if AgentCapability.TEST_GENERATION in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
            
        if AgentCapability.CODE_REVIEW in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
        
        if AgentCapability.SPECIFICATION_ANALYSIS in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
        
        self.allowed_permissions = permissions
        self.logger.info(f"🛠️ 工具调用已启用: 权限={len(permissions)}")
    
    @abstractmethod
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力"""
        return self._capabilities
    
    @abstractmethod
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        pass
    
    @abstractmethod
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强任务"""
        pass
    
    # ==========================================================================
    # 🗂️ 文件操作方法
    # ==========================================================================
    
    async def autonomous_file_read(self, file_ref: FileReference) -> Optional[str]:
        """自主读取文件内容"""
        file_path = file_ref.file_path
        
        # 检查缓存
        if file_path in self.file_cache:
            self.logger.debug(f"📋 使用缓存文件: {file_path}")
            return self.file_cache[file_path]
        
        try:
            # 读取文件
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 缓存内容
                self.file_cache[file_path] = content
                self.file_metadata_cache[file_path] = {
                    "size": len(content),
                    "read_time": time.time()
                }
                
                self.logger.info(f"✅ 成功读取文件: {file_path} ({len(content)} bytes)")
                return content
            else:
                self.logger.warning(f"⚠️ 文件不存在: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 读取文件失败 {file_path}: {str(e)}")
            return None
    
    async def save_result_to_file(self, content: str, file_path: str, 
                                file_type: str = "unknown") -> FileReference:
        """保存结果到文件"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 创建文件引用
            file_ref = FileReference(
                file_path=file_path,
                file_type=file_type,
                description=f"{self.agent_id}生成的{file_type}文件",
                metadata={
                    "size": len(content),
                    "created_by": self.agent_id,
                    "creation_time": time.time()
                }
            )
            
            self.logger.info(f"💾 成功保存文件: {file_path}")
            return file_ref
            
        except Exception as e:
            self.logger.error(f"❌ 保存文件失败 {file_path}: {str(e)}")
            raise
    
    # ==========================================================================
    # 🎯 任务处理方法
    # ==========================================================================
    
    async def process_task_with_file_references(self, task_message: TaskMessage) -> Dict[str, Any]:
        """处理带文件引用的任务消息"""
        self.logger.info(f"📨 收到任务消息: {task_message.message_type}")
        self.status = AgentStatus.WORKING
        
        try:
            # 1. 自主读取所有引用的文件
            file_contents = {}
            if task_message.file_references:
                self.logger.info(f"📁 开始读取 {len(task_message.file_references)} 个引用文件")
                
                for file_ref in task_message.file_references:
                    content = await self.autonomous_file_read(file_ref)
                    if content:
                        file_contents[file_ref.file_path] = {
                            "content": content,
                            "type": file_ref.file_type,
                            "description": file_ref.description
                        }
            
            # 2. 生成增强的prompt
            enhanced_prompt = self.create_file_enhanced_prompt(
                base_message=task_message.content,
                file_contents=file_contents
            )
            
            # 3. 执行任务处理
            result = await self.execute_enhanced_task(
                enhanced_prompt=enhanced_prompt,
                original_message=task_message,
                file_contents=file_contents
            )
            
            # 4. 记录任务历史
            self.task_history.append({
                "timestamp": time.time(),
                "task_id": task_message.task_id,
                "message_type": task_message.message_type,
                "result": result
            })
            
            self.status = AgentStatus.COMPLETED if result.get("success", False) else AgentStatus.FAILED
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 任务处理失败: {str(e)}")
            self.status = AgentStatus.FAILED
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    def create_file_enhanced_prompt(self, base_message: str, 
                                  file_contents: Dict[str, Dict]) -> str:
        """基于文件内容创建增强prompt"""
        if not file_contents:
            return base_message
        
        enhanced_prompt = f"{base_message}\n\n## 相关文件信息:\n"
        
        for file_path, content_info in file_contents.items():
            file_type = content_info.get("type", "unknown")
            description = content_info.get("description", "No description")
            content = content_info.get("content", "")
            
            enhanced_prompt += f"\n### {file_path} ({file_type})\n"
            enhanced_prompt += f"描述: {description}\n"
            enhanced_prompt += f"内容预览: {content[:500]}...\n"
        
        return enhanced_prompt
    
    # ==========================================================================
    # 🛠️ 工具调用方法
    # ==========================================================================
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用工具的便捷方法"""
        return await self.tool_registry.call_tool(
            name=tool_name,
            agent_id=self.agent_id,
            allowed_permissions=self.allowed_permissions,
            **kwargs
        )
    
    async def search_database_modules(self, module_name: str = "", description: str = "",
                                    limit: int = 10) -> Dict[str, Any]:
        """搜索数据库中的模块"""
        return await self.call_tool(
            "database_search_modules",
            module_name=module_name,
            description=description,
            limit=limit
        )
    
    async def get_database_module(self, module_id: int) -> Dict[str, Any]:
        """根据ID获取模块详情"""
        return await self.call_tool("database_get_module", module_id=module_id)
    
    async def search_by_functionality(self, functionality: str, tags: str = "",
                                    limit: int = 10) -> Dict[str, Any]:
        """按功能搜索模块"""
        return await self.call_tool(
            "database_search_by_functionality",
            functionality=functionality,
            tags=tags,
            limit=limit
        )
    
    async def get_similar_modules(self, bit_width: int, functionality: str,
                                limit: int = 5) -> Dict[str, Any]:
        """获取相似模块"""
        return await self.call_tool(
            "database_get_similar_modules",
            bit_width=bit_width,
            functionality=functionality,
            limit=limit
        )
    
    async def get_test_cases(self, module_id: int = None, module_name: str = "") -> Dict[str, Any]:
        """获取测试用例"""
        return await self.call_tool(
            "database_get_test_cases",
            module_id=module_id,
            module_name=module_name
        )
    
    async def search_design_patterns(self, pattern_type: str = "", description: str = "",
                                   limit: int = 10) -> Dict[str, Any]:
        """搜索设计模式"""
        return await self.call_tool(
            "database_search_design_patterns",
            pattern_type=pattern_type,
            description=description,
            limit=limit
        )
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """获取数据库架构信息"""
        return await self.call_tool("database_get_schema")
    
    async def save_database_result_to_file(self, query_result: Dict[str, Any], 
                                         file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """保存数据库查询结果到文件"""
        return await self.call_tool(
            "database_save_result_to_file",
            query_result=query_result,
            file_path=file_path,
            format_type=format_type
        )
    
    # ==========================================================================
    # 🔧 工具方法
    # ==========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self._capabilities],
            "task_count": len(self.task_history),
            "cache_size": len(self.file_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.file_cache.clear()
        self.file_metadata_cache.clear()
        self.logger.info("🧹 缓存已清空")