# 快速开始指南

本指南将帮助您快速上手使用中心化智能体框架（Centralized Agent Framework）。

## 📋 系统要求

- Python 3.7+
- 8GB+ RAM（推荐）
- 网络连接（用于LLM API调用）

## 🚀 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd CentralizedAgentFramework
```

### 2. 安装依赖

```bash
# 基础安装
pip install -r requirements.txt

# 或者开发安装
pip install -e .[dev]
```

### 3. 环境配置

创建`.env`文件并配置API密钥：

```bash
# LLM配置
CIRCUITPILOT_DASHSCOPE_API_KEY=your_dashscope_api_key
# 或者
CIRCUITPILOT_OPENAI_API_KEY=your_openai_api_key

# 框架配置（可选）
CAF_LLM_PROVIDER=dashscope
CAF_LLM_MODEL=qwen-turbo
CAF_MAX_ITERATIONS=20
CAF_OUTPUT_DIR=./output
```

## 💡 基础使用

### 方式1：使用便捷函数

```python
import asyncio
from CentralizedAgentFramework import create_framework

async def main():
    # 快速创建框架实例
    coordinator, agents = create_framework(
        llm_provider="dashscope",
        model_name="qwen-turbo", 
        api_key="your_api_key"
    )
    
    # 执行任务
    result = await coordinator.coordinate_task_execution(
        "设计一个32位ALU，支持ADD、SUB、AND、OR操作"
    )
    
    print(f"任务完成: {result['success']}")
    print(f"生成文件: {len(result.get('file_references', []))}")

asyncio.run(main())
```

### 方式2：手动配置

```python
import asyncio
from CentralizedAgentFramework import (
    FrameworkConfig, CentralizedCoordinator,
    VerilogDesignAgent, VerilogTestAgent, VerilogReviewAgent,
    EnhancedLLMClient
)

async def main():
    # 1. 加载配置
    config = FrameworkConfig.from_env()
    
    # 2. 创建LLM客户端
    llm_client = EnhancedLLMClient(config.llm)
    
    # 3. 创建协调者
    coordinator = CentralizedCoordinator(config, llm_client)
    
    # 4. 创建并注册智能体
    design_agent = VerilogDesignAgent(llm_client)
    test_agent = VerilogTestAgent(llm_client)
    review_agent = VerilogReviewAgent(llm_client)
    
    coordinator.register_agent(design_agent)
    coordinator.register_agent(test_agent)
    coordinator.register_agent(review_agent)
    
    # 5. 执行任务
    task = "设计一个8位计数器，支持使能和复位"
    result = await coordinator.coordinate_task_execution(task)
    
    # 6. 查看结果
    print(f"执行结果: {result}")

asyncio.run(main())
```

## 🧪 运行测试

```bash
# 运行框架测试
python tests/test_framework.py

# 或使用便捷命令
python -c "from tests import run_framework_tests; run_framework_tests()"
```

## 📖 运行示例

```bash
# 运行基础示例
python examples/basic_usage.py

# 或使用便捷命令  
python -c "from examples import run_basic_example; run_basic_example()"
```

## 🔧 配置说明

### 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `CAF_LLM_PROVIDER` | LLM提供商 | dashscope |
| `CAF_LLM_MODEL` | 模型名称 | qwen-turbo |
| `CAF_LLM_TEMPERATURE` | 温度参数 | 0.7 |
| `CAF_MAX_ITERATIONS` | 最大对话轮次 | 20 |
| `CAF_QUALITY_THRESHOLD` | 质量阈值 | 0.7 |
| `CAF_OUTPUT_DIR` | 输出目录 | ./output |

### API密钥配置

支持以下LLM提供商：

- **DashScope（阿里云）**: `CIRCUITPILOT_DASHSCOPE_API_KEY`
- **OpenAI**: `CIRCUITPILOT_OPENAI_API_KEY`
- **本地Ollama**: 不需要API密钥

## 📁 目录结构

```
CentralizedAgentFramework/
├── core/                    # 核心组件
│   ├── centralized_coordinator.py
│   ├── base_agent.py
│   └── enums.py
├── agents/                  # 专业智能体
│   ├── verilog_design_agent.py
│   ├── verilog_test_agent.py
│   └── verilog_review_agent.py
├── config/                  # 配置管理
│   └── config.py
├── llm_integration/         # LLM集成
│   └── enhanced_llm_client.py
├── tools/                   # 工具系统
│   └── tool_registry.py
├── examples/               # 使用示例
│   └── basic_usage.py
├── tests/                  # 测试脚本
│   └── test_framework.py
└── docs/                   # 文档
    └── GETTING_STARTED.md
```

## 🎯 使用场景

### 1. Verilog代码生成

```python
# 设计任务示例
task = """
设计一个FIFO缓冲器，规格如下：
- 数据位宽: 32位
- 深度: 256
- 支持空/满标志
- 异步复位
"""

result = await coordinator.coordinate_task_execution(task)
```

### 2. 测试用例生成

```python
# 测试任务示例  
task = """
为已有的ALU模块生成完整的testbench，包括：
- 基本功能测试
- 边界条件测试
- 随机测试向量
"""

result = await coordinator.coordinate_task_execution(task)
```

### 3. 代码审查

```python
# 审查任务示例
task = """
审查现有的Verilog代码，检查：
- 语法错误
- 代码风格
- 逻辑问题
- 性能优化建议
"""

result = await coordinator.coordinate_task_execution(task)
```

## 🚧 故障排除

### 常见问题

1. **LLM连接失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证提供商服务状态

2. **文件生成失败**
   - 检查输出目录权限
   - 确认磁盘空间充足
   - 验证路径配置

3. **智能体选择错误**
   - 检查智能体注册状态
   - 验证能力匹配逻辑
   - 查看协调者日志

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查团队状态**
   ```python
   status = coordinator.get_team_status()
   print(status)
   ```

3. **查看对话历史**
   ```python
   stats = coordinator.get_conversation_statistics()
   print(stats)
   ```

## 📞 获取帮助

- 查看完整文档: [docs/](docs/)
- 运行测试用例: `python tests/test_framework.py`
- 查看示例代码: [examples/](examples/)
- 提交问题: GitHub Issues

## 🎉 下一步

恭喜！您已经成功配置了中心化智能体框架。现在您可以：

1. 尝试不同的Verilog设计任务
2. 自定义智能体能力
3. 扩展工具注册表
4. 集成到您的工作流程中

祝您使用愉快！🚀