#!/usr/bin/env python3
"""
数据库检索工具

Database Retrieval Tools for Agent Framework
"""

import json
import logging
import sqlite3
import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from .tool_registry import ToolPermission


@dataclass
class QueryResult:
    """查询结果数据类"""
    success: bool
    data: List[Dict[str, Any]] = None
    error: str = None
    execution_time: float = 0.0
    row_count: int = 0
    query: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data or [],
            "error": self.error,
            "execution_time": self.execution_time,
            "row_count": self.row_count,
            "query": self.query
        }


class DatabaseConnector(ABC):
    """数据库连接器抽象基类"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.logger = logging.getLogger(f"DatabaseConnector.{self.__class__.__name__}")
    
    @abstractmethod
    async def connect(self):
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: tuple = None) -> QueryResult:
        """执行查询"""
        pass
    
    @abstractmethod
    async def get_schema_info(self) -> Dict[str, Any]:
        """获取数据库架构信息"""
        pass


class SQLiteConnector(DatabaseConnector):
    """SQLite数据库连接器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.db_path = connection_config.get("db_path", ":memory:")
        self.connection = None
        
    async def connect(self):
        """建立SQLite连接"""
        try:
            # 确保数据库文件目录存在
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问
            self.logger.info(f"✅ SQLite连接成功: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ SQLite连接失败: {str(e)}")
            raise
    
    async def disconnect(self):
        """关闭SQLite连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("🔌 SQLite连接已关闭")
    
    async def execute_query(self, query: str, params: tuple = None) -> QueryResult:
        """执行SQLite查询"""
        if not self.connection:
            await self.connect()
        
        start_time = time.time()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 获取结果
            if query.strip().upper().startswith(('SELECT', 'WITH', 'PRAGMA')):
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                row_count = len(data)
            else:
                # INSERT, UPDATE, DELETE等操作
                self.connection.commit()
                data = []
                row_count = cursor.rowcount
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"🗄️ 查询执行成功: {row_count} 行, {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data=data,
                execution_time=execution_time,
                row_count=row_count,
                query=query
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"数据库查询失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            return QueryResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                query=query
            )
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """获取SQLite数据库架构信息"""
        if not self.connection:
            await self.connect()
        
        schema_info = {
            "database_type": "sqlite",
            "database_path": self.db_path,
            "tables": {},
            "views": {},
            "indexes": []
        }
        
        try:
            # 获取表信息
            tables_result = await self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            if tables_result.success:
                for table_row in tables_result.data:
                    table_name = table_row["name"]
                    
                    # 获取表结构
                    columns_result = await self.execute_query(f"PRAGMA table_info({table_name})")
                    if columns_result.success:
                        schema_info["tables"][table_name] = {
                            "columns": columns_result.data,
                            "row_count": 0  # 可以额外查询获取行数
                        }
                        
                        # 获取行数
                        count_result = await self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                        if count_result.success and count_result.data:
                            schema_info["tables"][table_name]["row_count"] = count_result.data[0]["count"]
            
            # 获取视图信息
            views_result = await self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='view'"
            )
            
            if views_result.success:
                for view_row in views_result.data:
                    view_name = view_row["name"]
                    schema_info["views"][view_name] = {"type": "view"}
            
            # 获取索引信息
            indexes_result = await self.execute_query(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            
            if indexes_result.success:
                schema_info["indexes"] = indexes_result.data
            
            self.logger.info(f"📊 架构信息获取完成: {len(schema_info['tables'])} 表, {len(schema_info['views'])} 视图")
            
        except Exception as e:
            self.logger.error(f"❌ 获取架构信息失败: {str(e)}")
        
        return schema_info


class DatabaseToolManager:
    """数据库工具管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("DatabaseToolManager")
        self.connectors: Dict[str, DatabaseConnector] = {}
        self.default_connector = None
        
        # 预定义的安全查询模板
        self.safe_query_templates = {
            "search_modules": """
                SELECT * FROM verilog_modules 
                WHERE name LIKE ? OR description LIKE ? 
                ORDER BY created_at DESC LIMIT ?
            """,
            "get_module_by_id": """
                SELECT * FROM verilog_modules WHERE id = ?
            """,
            "search_by_functionality": """
                SELECT * FROM verilog_modules 
                WHERE functionality LIKE ? OR tags LIKE ?
                ORDER BY quality_score DESC LIMIT ?
            """,
            "get_similar_modules": """
                SELECT * FROM verilog_modules 
                WHERE bit_width = ? AND functionality = ?
                ORDER BY quality_score DESC LIMIT ?
            """,
            "get_test_cases": """
                SELECT * FROM test_cases 
                WHERE module_id = ? OR module_name LIKE ?
                ORDER BY created_at DESC
            """,
            "search_design_patterns": """
                SELECT * FROM design_patterns 
                WHERE pattern_type = ? OR description LIKE ?
                ORDER BY usage_count DESC LIMIT ?
            """
        }
    
    def register_connector(self, name: str, connector: DatabaseConnector, 
                          is_default: bool = False):
        """注册数据库连接器"""
        self.connectors[name] = connector
        if is_default or not self.default_connector:
            self.default_connector = connector
        
        self.logger.info(f"📝 数据库连接器注册: {name} ({'默认' if is_default else ''})")
    
    async def connect_all(self):
        """连接所有数据库"""
        for name, connector in self.connectors.items():
            try:
                await connector.connect()
            except Exception as e:
                self.logger.error(f"❌ 连接器 {name} 连接失败: {str(e)}")
    
    async def disconnect_all(self):
        """断开所有数据库连接"""
        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
            except Exception as e:
                self.logger.error(f"❌ 连接器 {name} 断开失败: {str(e)}")
    
    async def execute_safe_query(self, template_name: str, params: tuple = None,
                                connector_name: str = None) -> QueryResult:
        """执行安全的预定义查询"""
        if template_name not in self.safe_query_templates:
            return QueryResult(
                success=False,
                error=f"未找到查询模板: {template_name}"
            )
        
        query = self.safe_query_templates[template_name]
        connector = self.connectors.get(connector_name) or self.default_connector
        
        if not connector:
            return QueryResult(
                success=False,
                error="没有可用的数据库连接器"
            )
        
        return await connector.execute_query(query, params)
    
    async def execute_custom_query(self, query: str, params: tuple = None,
                                 connector_name: str = None) -> QueryResult:
        """执行自定义查询（需要权限检查）"""
        # 基本的SQL注入防护
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE'
        ]
        
        query_upper = query.upper().strip()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return QueryResult(
                    success=False,
                    error=f"禁止执行包含 {keyword} 的查询，请使用安全查询模板"
                )
        
        connector = self.connectors.get(connector_name) or self.default_connector
        
        if not connector:
            return QueryResult(
                success=False,
                error="没有可用的数据库连接器"
            )
        
        return await connector.execute_query(query, params)
    
    async def get_database_schema(self, connector_name: str = None) -> Dict[str, Any]:
        """获取数据库架构信息"""
        connector = self.connectors.get(connector_name) or self.default_connector
        
        if not connector:
            return {"error": "没有可用的数据库连接器"}
        
        return await connector.get_schema_info()
    
    async def save_query_result_to_file(self, result: QueryResult, 
                                      file_path: str, format_type: str = "json") -> str:
        """将查询结果保存到文件"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format_type.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            
            elif format_type.lower() == "csv":
                import csv
                if result.success and result.data:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        if result.data:
                            writer = csv.DictWriter(f, fieldnames=result.data[0].keys())
                            writer.writeheader()
                            writer.writerows(result.data)
            
            elif format_type.lower() == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"查询执行结果\\n")
                    f.write(f"成功: {result.success}\\n")
                    f.write(f"执行时间: {result.execution_time:.3f}s\\n")
                    f.write(f"行数: {result.row_count}\\n")
                    f.write(f"查询: {result.query}\\n\\n")
                    
                    if result.success and result.data:
                        f.write("数据:\\n")
                        for i, row in enumerate(result.data):
                            f.write(f"Row {i+1}: {row}\\n")
                    elif result.error:
                        f.write(f"错误: {result.error}\\n")
            
            self.logger.info(f"💾 查询结果已保存: {file_path}")
            return file_path
            
        except Exception as e:
            error_msg = f"保存查询结果失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)


# 全局数据库工具管理器实例
db_tool_manager = DatabaseToolManager()


# ==========================================================================
# 🛠️ 工具函数 - 供ToolRegistry调用
# ==========================================================================

async def database_search_modules(module_name: str = "", description: str = "",
                                limit: int = 10) -> Dict[str, Any]:
    """搜索Verilog模块"""
    search_term = f"%{module_name}%"
    desc_term = f"%{description}%"
    
    result = await db_tool_manager.execute_safe_query(
        "search_modules", 
        (search_term, desc_term, limit)
    )
    
    return {
        "tool": "database_search_modules",
        "success": result.success,
        "result": result.to_dict(),
        "summary": f"找到 {result.row_count} 个模块" if result.success else result.error
    }


async def database_get_module(module_id: int) -> Dict[str, Any]:
    """根据ID获取模块详情"""
    result = await db_tool_manager.execute_safe_query(
        "get_module_by_id", 
        (module_id,)
    )
    
    return {
        "tool": "database_get_module",
        "success": result.success,
        "result": result.to_dict(),
        "summary": f"获取模块 ID={module_id}" if result.success else result.error
    }


async def database_search_by_functionality(functionality: str, tags: str = "",
                                         limit: int = 10) -> Dict[str, Any]:
    """按功能搜索模块"""
    func_term = f"%{functionality}%"
    tags_term = f"%{tags}%"
    
    result = await db_tool_manager.execute_safe_query(
        "search_by_functionality",
        (func_term, tags_term, limit)
    )
    
    return {
        "tool": "database_search_by_functionality", 
        "success": result.success,
        "result": result.to_dict(),
        "summary": f"按功能找到 {result.row_count} 个模块" if result.success else result.error
    }


async def database_get_similar_modules(bit_width: int, functionality: str,
                                     limit: int = 5) -> Dict[str, Any]:
    """获取相似模块"""
    result = await db_tool_manager.execute_safe_query(
        "get_similar_modules",
        (bit_width, functionality, limit)
    )
    
    return {
        "tool": "database_get_similar_modules",
        "success": result.success, 
        "result": result.to_dict(),
        "summary": f"找到 {result.row_count} 个相似模块" if result.success else result.error
    }


async def database_get_test_cases(module_id: int = None, module_name: str = "") -> Dict[str, Any]:
    """获取测试用例"""
    name_term = f"%{module_name}%"
    
    result = await db_tool_manager.execute_safe_query(
        "get_test_cases",
        (module_id, name_term)
    )
    
    return {
        "tool": "database_get_test_cases",
        "success": result.success,
        "result": result.to_dict(), 
        "summary": f"找到 {result.row_count} 个测试用例" if result.success else result.error
    }


async def database_search_design_patterns(pattern_type: str = "", description: str = "",
                                        limit: int = 10) -> Dict[str, Any]:
    """搜索设计模式"""
    desc_term = f"%{description}%"
    
    result = await db_tool_manager.execute_safe_query(
        "search_design_patterns",
        (pattern_type, desc_term, limit)
    )
    
    return {
        "tool": "database_search_design_patterns",
        "success": result.success,
        "result": result.to_dict(),
        "summary": f"找到 {result.row_count} 个设计模式" if result.success else result.error
    }


async def database_get_schema() -> Dict[str, Any]:
    """获取数据库架构信息"""
    try:
        schema = await db_tool_manager.get_database_schema()
        return {
            "tool": "database_get_schema",
            "success": True,
            "result": schema,
            "summary": f"数据库包含 {len(schema.get('tables', {}))} 个表"
        }
    except Exception as e:
        return {
            "tool": "database_get_schema",
            "success": False,
            "error": str(e),
            "summary": f"获取架构失败: {str(e)}"
        }


async def database_save_result_to_file(query_result: Dict[str, Any], file_path: str,
                                     format_type: str = "json") -> Dict[str, Any]:
    """将查询结果保存到文件"""
    try:
        # 重构QueryResult对象
        result = QueryResult(
            success=query_result.get("success", False),
            data=query_result.get("data", []),
            error=query_result.get("error"),
            execution_time=query_result.get("execution_time", 0.0),
            row_count=query_result.get("row_count", 0),
            query=query_result.get("query", "")
        )
        
        saved_path = await db_tool_manager.save_query_result_to_file(
            result, file_path, format_type
        )
        
        return {
            "tool": "database_save_result_to_file",
            "success": True,
            "file_path": saved_path,
            "summary": f"结果已保存到 {saved_path}"
        }
        
    except Exception as e:
        return {
            "tool": "database_save_result_to_file", 
            "success": False,
            "error": str(e),
            "summary": f"保存失败: {str(e)}"
        }