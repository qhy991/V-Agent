#!/usr/bin/env python3
"""
中心化智能体框架安装脚本

Setup Script for Centralized Agent Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取版本信息
version = {}
with open(this_directory / "__init__.py") as f:
    exec(f.read(), version)

# 依赖包列表
install_requires = [
    "aiohttp>=3.8.0",
    "asyncio>=3.4.3",
    "dataclasses>=0.6;python_version<'3.7'",
    "typing-extensions>=3.7.4;python_version<'3.8'",
    "pathlib>=1.0.1;python_version<'3.4'",
]

# 开发依赖
dev_requires = [
    "pytest>=6.0.0",
    "pytest-asyncio>=0.18.0", 
    "pytest-cov>=2.10.0",
    "black>=21.0.0",
    "flake8>=3.8.0",
    "mypy>=0.800",
]

# 完整安装（包含开发工具）
all_requires = install_requires + dev_requires

setup(
    name="centralized-agent-framework",
    version=version.get("__version__", "1.0.0"),
    author=version.get("__author__", "CircuitPilot Team"),
    author_email="support@circuitpilot.ai",
    description=version.get("__description__", "中心化智能体协调框架"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/circuitpilot/centralized-agent-framework",
    project_urls={
        "Bug Tracker": "https://github.com/circuitpilot/centralized-agent-framework/issues",
        "Documentation": "https://docs.circuitpilot.ai/caf",
        "Source Code": "https://github.com/circuitpilot/centralized-agent-framework",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8", 
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "all": all_requires,
    },
    entry_points={
        "console_scripts": [
            "caf-test=tests:run_framework_tests",
            "caf-example=examples:run_basic_example",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
    },
    keywords=[
        "ai", "agent", "framework", "verilog", "hdl",
        "coordination", "multi-agent", "llm", "automation",
        "digital-design", "eda", "circuit-design"
    ],
    zip_safe=False,
)