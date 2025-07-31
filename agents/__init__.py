#!/usr/bin/env python3
"""
智能体模块

Agents Module for Centralized Agent Framework
"""

from .real_verilog_agent import RealVerilogDesignAgent
from .real_code_reviewer import RealCodeReviewAgent

__all__ = [
    'RealVerilogDesignAgent',
    'RealCodeReviewAgent'
]