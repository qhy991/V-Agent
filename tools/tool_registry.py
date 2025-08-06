#!/usr/bin/env python3
"""
工具注册表 - 简化版本

Tool Registry for Agent Framework
"""

import logging
import os
import asyncio
from enum import Enum
from typing import Dict, Any, Set, Callable, Optional
from pathlib import Path


class ToolPermission(Enum):
    """工具权限枚举"""
    READ_ONLY = "read_only"
    WRITE_FILES = "write_files"
    EXECUTE_SAFE = "execute_safe"
    EXECUTE_SYSTEM = "execute_system"
    NETWORK_ACCESS = "network_access"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.logger = logging.getLogger("ToolRegistry")
        self.tools: Dict[str, Callable] = {}
        self.permissions: Dict[str, Set[ToolPermission]] = {}
        
        # 注册基础工具
        self._register_basic_tools()
    
    def _register_basic_tools(self):
        """注册基础工具"""
        # 文件读取
        self.register_tool(
            name="read_file",
            func=self._read_file,
            permissions={ToolPermission.READ_ONLY}
        )
        
        # 文件写入
        self.register_tool(
            name="write_file",
            func=self._write_file,
            permissions={ToolPermission.WRITE_FILES}
        )
        
        # 列出目录
        self.register_tool(
            name="list_directory",
            func=self._list_directory,
            permissions={ToolPermission.READ_ONLY}
        )
        
        # 注册数据库工具
        self._register_database_tools()
        
        self.logger.debug("🛠️ 基础工具注册完成")
    
    def _register_database_tools(self):
        """注册数据库工具"""
        from .database_tools import (
            database_search_modules, database_get_module, database_search_by_functionality,
            database_get_similar_modules, database_get_test_cases, database_search_design_patterns,
            database_get_schema, database_save_result_to_file
        )
        
        # 模块搜索工具
        self.register_tool(
            name="database_search_modules",
            func=database_search_modules,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 获取模块详情
        self.register_tool(
            name="database_get_module",
            func=database_get_module,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 按功能搜索
        self.register_tool(
            name="database_search_by_functionality", 
            func=database_search_by_functionality,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 获取相似模块
        self.register_tool(
            name="database_get_similar_modules",
            func=database_get_similar_modules,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 获取测试用例
        self.register_tool(
            name="database_get_test_cases",
            func=database_get_test_cases,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 搜索设计模式
        self.register_tool(
            name="database_search_design_patterns",
            func=database_search_design_patterns,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 获取数据库架构
        self.register_tool(
            name="database_get_schema",
            func=database_get_schema,
            permissions={ToolPermission.DATABASE_READ}
        )
        
        # 保存查询结果到文件
        self.register_tool(
            name="database_save_result_to_file",
            func=database_save_result_to_file,
            permissions={ToolPermission.DATABASE_READ, ToolPermission.WRITE_FILES}
        )
        
        self.logger.debug("🗄️ 数据库工具注册完成")
    
    def register_tool(self, name: str, func: Callable, 
                     permissions: Set[ToolPermission]):
        """注册工具"""
        self.tools[name] = func
        self.permissions[name] = permissions
        self.logger.debug(f"注册工具: {name}")
    
    async def call_tool(self, name: str, agent_id: str, 
                       allowed_permissions: Set[ToolPermission],
                       **kwargs) -> Dict[str, Any]:
        """调用工具"""
        if name not in self.tools:
            return {"success": False, "error": f"工具不存在: {name}"}
        
        # 检查权限
        required_permissions = self.permissions[name]
        if not required_permissions.issubset(allowed_permissions):
            return {"success": False, "error": f"权限不足: {name}"}
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 调用工具
            func = self.tools[name]
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.logger.info(f"Tool call: {name} by {agent_id} - SUCCESS ({execution_time:.3f}s)")
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            self.logger.error(f"Tool call: {name} by {agent_id} - FAILED: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==========================================================================
    # 🛠️ 基础工具实现
    # ==========================================================================
    
    def _read_file(self, file_path: str) -> str:
        """读取文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")
    
    def _write_file(self, file_path: str, content: str) -> str:
        """写入文件"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"文件已保存: {file_path}"
        except Exception as e:
            raise Exception(f"写入文件失败: {str(e)}")
    
    def _list_directory(self, directory_path: str) -> list:
        """列出目录内容"""
        try:
            path = Path(directory_path)
            if not path.exists():
                raise Exception(f"目录不存在: {directory_path}")
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return items
        except Exception as e:
            raise Exception(f"列出目录失败: {str(e)}")
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取可用工具列表"""
        tools_info = {}
        for name, permissions in self.permissions.items():
            tools_info[name] = {
                "name": name,
                "permissions": [p.value for p in permissions]
            }
        return tools_info