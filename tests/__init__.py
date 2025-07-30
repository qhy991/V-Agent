#!/usr/bin/env python3
"""
测试模块

Tests Module for Centralized Agent Framework
"""

# 测试模块通常不需要导出特定内容
# 但可以提供测试工具函数

def run_framework_tests():
    """运行框架测试的便捷函数"""
    import asyncio
    from .test_framework import FrameworkTester
    
    async def _run_tests():
        tester = FrameworkTester()
        await tester.run_all_tests()
        return tester.print_test_summary()
    
    return asyncio.run(_run_tests())

__all__ = [
    'run_framework_tests'
]