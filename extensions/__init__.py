#!/usr/bin/env python3
"""
CentralizedAgentFramework Extensions

增量功能扩展模块，不影响核心框架功能
"""

__version__ = "1.0.0"
__description__ = "Test-driven development extensions for CentralizedAgentFramework"

# 扩展功能导入
from .test_driven_coordinator import TestDrivenCoordinator, TestDrivenConfig, create_test_driven_coordinator
from .enhanced_task_parser import EnhancedTaskParser
from .test_analyzer import TestAnalyzer

__all__ = [
    'TestDrivenCoordinator',
    'TestDrivenConfig',
    'create_test_driven_coordinator',
    'EnhancedTaskParser', 
    'TestAnalyzer'
]