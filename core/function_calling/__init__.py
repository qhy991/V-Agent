"""
Function Calling Package - Function Calling 包
===========================================

提供智能体Function Calling功能的核心组件。
"""

from .parser import ToolCallParser, ToolCall, ToolResult

__all__ = ['ToolCallParser', 'ToolCall', 'ToolResult']