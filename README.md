# CentralizedAgentFramework

**中心化协调多智能体框架 - 新一代AI Agent协作系统**

## 🎯 框架概述

CentralizedAgentFramework是一个先进的多智能体协作框架，采用中心化协调架构，实现了智能的任务分配、动态对话流程控制和无缝的信息回流机制。

### 🏗️ 核心特性

- **🧠 中心化协调者** - 掌握全局状态，智能管理团队
- **🤖 专业智能体** - 各有专长，支持工具调用
- **🎯 动态NextSpeaker** - LLM驱动的智能发言者选择
- **🔄 信息回流机制** - 任务完成后自动向协调者汇报
- **🛠️ 工具调用集成** - 每个智能体都有独立的工具能力
- **📝 对话历史管理** - 完整的多轮对话记录和上下文管理

### 🎪 工作流程

```
1. 用户提交任务 → 中心协调者
2. 协调者分析任务 → 选择合适的智能体
3. 智能体执行任务 → 使用工具调用能力
4. 任务完成后 → 信息回流到协调者
5. 协调者决策 → 选择下一个发言者
6. 继续协作直到 → 任务完全完成
```

## 🚀 快速开始

### 安装依赖

```bash
pip install aiohttp python-dotenv
```

### 基本使用

```python
import asyncio
from core.centralized_coordinator import CentralizedCoordinator
from agents.verilog_agents import VerilogDesignAgent, VerilogTestAgent

async def main():
    # 创建协调者
    coordinator = CentralizedCoordinator()
    
    # 创建智能体团队
    design_agent = VerilogDesignAgent()
    test_agent = VerilogTestAgent()
    
    # 注册智能体
    coordinator.register_agent(design_agent)
    coordinator.register_agent(test_agent)
    
    # 启动协调任务
    task = "设计一个8位ALU模块"
    conversation_id = await coordinator.start_conversation(task)
    
    print(f"协调任务已启动: {conversation_id}")

asyncio.run(main())
```

## 📁 目录结构

```
CentralizedAgentFramework/
├── core/                   # 核心框架
│   ├── centralized_coordinator.py  # 中心协调者
│   ├── base_agent.py              # 智能体基类
│   └── enums.py                   # 枚举和常量
├── agents/                 # 智能体实现
│   ├── verilog_agents.py          # Verilog专业智能体
│   └── custom_agents.py           # 自定义智能体
├── llm_integration/        # LLM集成
│   └── enhanced_llm_client.py     # LLM客户端
├── config/                 # 配置管理
│   └── config.py                  # 配置类
├── tools/                  # 工具调用
│   └── tool_registry.py           # 工具注册表
├── tests/                  # 测试
│   └── test_coordinator.py        # 协调者测试
├── examples/               # 示例
│   └── simple_example.py          # 简单示例
└── docs/                   # 文档
    └── architecture.md             # 架构文档
```

## 🎯 核心组件

### CentralizedCoordinator 
- 团队管理和智能体注册
- 任务分析和复杂度评估
- 动态NextSpeaker决策
- 对话流程控制
- 结果聚合和状态管理

### BaseAgent
- 工具调用能力
- 文件读写操作
- LLM交互接口
- 任务执行框架

### AgentCapability
- CODE_GENERATION: 代码生成
- TEST_GENERATION: 测试生成
- CODE_REVIEW: 代码评审
- TASK_COORDINATION: 任务协调

## 🔧 扩展开发

### 添加新智能体

```python
from core.base_agent import BaseAgent
from core.enums import AgentCapability

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="custom_agent",
            role="自定义专家",
            capabilities={AgentCapability.CUSTOM_TASK}
        )
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        # 实现您的任务逻辑
        return {"success": True, "message": "任务完成"}
```

### 自定义协调策略

您可以继承CentralizedCoordinator并重写决策方法来实现自定义的协调策略。

## 📊 性能特点

- **高并发**: 异步架构支持大量智能体并发
- **可伸缩**: 轻松添加新的智能体类型
- **智能化**: LLM驱动的决策机制
- **容错性**: 完善的错误处理和恢复机制

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个框架！

## 📄 许可证

MIT License

---

*由CircuitPilot团队开发维护*