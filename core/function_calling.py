#!/usr/bin/env python3
"""
Function Calling数据类定义

Function Calling Data Classes
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "call_id": self.call_id
        }


@dataclass
class ToolResult:
    """工具调用结果"""
    call_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "call_id": self.call_id,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }