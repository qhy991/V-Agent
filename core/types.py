#!/usr/bin/env python3
"""
共享类型定义
===========

定义在多个模块间共享的数据类型，避免循环导入问题。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


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