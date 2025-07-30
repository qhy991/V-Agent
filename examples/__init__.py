#!/usr/bin/env python3
"""
示例模块

Examples Module for Centralized Agent Framework
"""

# 示例模块通常不需要导出特定内容
# 但可以提供运行示例的便捷函数

def run_basic_example():
    """运行基础示例的便捷函数"""
    import asyncio
    import sys
    from pathlib import Path
    
    # 添加父目录到路径
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from .basic_usage import main
    return asyncio.run(main())

__all__ = [
    'run_basic_example'
]