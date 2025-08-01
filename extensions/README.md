# 🧪 测试驱动扩展模块

## ✨ 功能概述

这是一个**完全增量**的扩展模块，为 CentralizedAgentFramework 添加测试驱动开发功能，**不影响任何现有功能**。

### 🎯 核心特性

1. **用户指定测试台支持**：允许用户提供测试台文件路径
2. **自动迭代优化**：测试失败时自动分析并改进设计（最多5次）
3. **智能错误分析**：深度分析编译错误和运行时错误
4. **零影响集成**：装饰器模式，不修改任何现有代码

## 🏗️ 架构设计

### 装饰器模式（Decorator Pattern）
```
现有协调器 (CentralizedCoordinator)
          ↓ 包装/装饰
测试驱动协调器 (TestDrivenCoordinator)
          ↓ 保持完全兼容
     所有现有功能不变 + 新增测试驱动功能
```

### 模块结构
```
extensions/
├── __init__.py                    # 扩展模块入口
├── test_driven_coordinator.py     # 主协调器扩展
├── enhanced_task_parser.py        # 任务解析增强
├── test_analyzer.py              # 测试分析器
└── README.md                     # 本文档
```

## 🚀 使用方法

### 方式1：最小化集成（推荐）

```python
from core.centralized_coordinator import CentralizedCoordinator
from extensions import create_test_driven_coordinator

# 创建标准协调器
coordinator = CentralizedCoordinator(config)

# 升级为测试驱动协调器（可选）
enhanced_coordinator = create_test_driven_coordinator(coordinator)

# 现有功能完全不变
standard_result = await enhanced_coordinator.coordinate_task_execution(task)

# 新增测试驱动功能
tdd_result = await enhanced_coordinator.execute_test_driven_task(
    task_description="设计32位ALU...",
    testbench_path="/path/to/alu_tb.v"
)
```

### 方式2：直接使用扩展

```python
from extensions.test_driven_coordinator import TestDrivenCoordinator

# 包装现有协调器
tdd_coordinator = TestDrivenCoordinator(existing_coordinator)

# 使用新功能
result = await tdd_coordinator.execute_test_driven_task(
    "设计一个计数器，测试台: /path/to/counter_tb.v"
)
```

## 📝 完整使用示例

### 示例1：基本测试驱动任务

```python
#!/usr/bin/env python3
import asyncio
from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from extensions import create_test_driven_coordinator

async def test_driven_example():
    # 1. 标准初始化（不变）
    config = FrameworkConfig.from_env()
    coordinator = CentralizedCoordinator(config)
    
    # 注册智能体（不变）
    verilog_agent = RealVerilogDesignAgent(config)
    reviewer_agent = RealCodeReviewAgent(config)
    coordinator.register_agent(verilog_agent)
    coordinator.register_agent(reviewer_agent)
    
    # 2. 升级为测试驱动功能
    enhanced_coordinator = create_test_driven_coordinator(coordinator)
    
    # 3. 执行测试驱动任务
    task = '''
    请设计一个32位ALU模块，支持：
    - 加法运算 (ADD)
    - 减法运算 (SUB)
    - 逻辑与 (AND)
    - 逻辑或 (OR)
    
    测试要求：
    - 使用我提供的测试台进行验证
    - 如果测试失败，请自动分析并迭代改进
    '''
    
    result = await enhanced_coordinator.execute_test_driven_task(
        task_description=task,
        testbench_path="/home/user/projects/alu_testbench.v"
    )
    
    # 4. 处理结果
    if result["success"]:
        print(f"✅ 经过 {result['total_iterations']} 次迭代，所有测试通过！")
        print(f"最终设计文件: {result['final_design']}")
    else:
        print(f"❌ 经过 {result['total_iterations']} 次迭代仍有问题")
        print(f"错误: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_driven_example())
```

### 示例2：兼容性验证

```python
async def compatibility_test():
    """验证现有功能完全不受影响"""
    
    # 原有的使用方式
    coordinator = CentralizedCoordinator(config)
    enhanced_coordinator = create_test_driven_coordinator(coordinator)
    
    # 所有现有API完全相同
    standard_task = "设计一个简单的8位计数器"
    
    # 这两个调用完全等价
    result1 = await coordinator.coordinate_task_execution(standard_task)
    result2 = await enhanced_coordinator.coordinate_task_execution(standard_task)
    
    # 结果应该完全相同
    assert result1.keys() == result2.keys()
    print("✅ 现有功能完全兼容")
```

## 🔄 工作流程

### 测试驱动工作流程
```
用户输入
    ↓
解析任务（检测是否为测试驱动任务）
    ↓
如果是标准任务 → 使用原有协调器流程
    ↓
如果是测试驱动任务 ↓
    ↓
验证测试台文件
    ↓
开始迭代循环（最多5次）
    ├─ 第N次迭代
    │  ├─ 🎨 设计阶段：生成/改进设计
    │  ├─ 🧪 测试阶段：运行用户测试台
    │  └─ 🔍 分析阶段：分析失败原因
    │
    ├─ 测试通过？ → 成功完成
    └─ 测试失败？ → 继续下一次迭代
    ↓
返回结果（包含完整迭代历史）
```

## 📊 API 参考

### TestDrivenCoordinator 主要方法

#### `execute_test_driven_task(task_description, testbench_path=None, context=None)`
执行测试驱动任务的主入口

**参数：**
- `task_description` (str): 任务描述
- `testbench_path` (str, 可选): 测试台文件路径
- `context` (dict, 可选): 上下文信息

**返回：**
```python
{
    "success": bool,
    "session_id": str,
    "total_iterations": int,
    "final_design": List[FileReference],
    "completion_reason": str,  # "tests_passed" 或 "max_iterations_reached"
    "error": str  # 如果失败
}
```

#### `coordinate_task_execution(initial_task, context=None)`
保持与原协调器完全相同的接口

#### 会话管理方法
- `get_session_info(session_id)`: 获取会话信息
- `list_active_sessions()`: 列出活跃会话
- `get_iteration_history(session_id)`: 获取迭代历史

## ⚙️ 配置选项

### TestDrivenConfig

```python
@dataclass
class TestDrivenConfig:
    max_iterations: int = 5           # 最大迭代次数
    enable_deep_analysis: bool = True # 启用深度错误分析
    auto_fix_suggestions: bool = True # 自动生成修复建议
    save_iteration_logs: bool = True  # 保存迭代日志
    timeout_per_iteration: int = 300  # 每次迭代超时（秒）
```

**使用方式：**
```python
from extensions.test_driven_coordinator import TestDrivenConfig

config = TestDrivenConfig(
    max_iterations=3,
    timeout_per_iteration=600
)

enhanced_coordinator = TestDrivenCoordinator(coordinator, config)
```

## 🎯 任务识别规则

### 自动识别测试驱动任务

系统会自动识别以下情况为测试驱动任务：

1. **显式提供测试台路径**
2. **任务描述包含测试台路径**
3. **包含2个或更多TDD关键词**：
   - 测试台, testbench, tb, 测试文件
   - 测试失败, 迭代, 优化, 修改, 调试
   - test, iterate, optimize, fix, debug
   - 验证, verify, validation

### 测试台路径识别模式

- `testbench: /path/to/file.v`
- `测试台: /path/to/file.v`
- `tb: /path/to/file.v`
- `测试文件: /path/to/file.v`

## 🔧 错误分析能力

### 编译错误分析
- 语法错误检测和修复建议
- 未声明标识符处理
- 端口不匹配分析
- 模块未找到问题

### 运行时错误分析
- 仿真超时处理
- 信号状态分析（X/Z状态）
- 时序问题检测

### 智能修复建议
- 基于错误类型的针对性建议
- 测试台兼容性分析
- 设计改进方向指导

## 🚀 优势特性

### 1. 零影响集成
- **不修改任何现有文件**
- **不改变任何现有API**
- **完全向后兼容**
- **可选功能，按需使用**

### 2. 智能化程度高
- 自动任务类型识别
- 智能错误分析
- 自动改进建议生成
- 多轮迭代优化

### 3. 完整可追溯
- 详细的迭代历史记录
- 每次测试的完整输出
- 失败原因和改进建议
- 会话管理和查询

### 4. 高度可配置
- 可调整迭代次数
- 可配置超时时间
- 可选择分析深度
- 灵活的日志记录

## 📋 注意事项

1. **系统依赖**：需要安装 `iverilog` 仿真工具
2. **文件权限**：确保测试台文件可读，工作目录可写
3. **路径格式**：建议使用绝对路径指定测试台
4. **仿真超时**：默认30秒超时，可通过配置调整

## 🎉 立即开始

1. **复制扩展模块**到您的项目
2. **无需修改任何现有代码**
3. **按需使用新功能**

```python
# 最简单的集成方式
from extensions import create_test_driven_coordinator

enhanced_coordinator = create_test_driven_coordinator(your_existing_coordinator)

# 开始使用测试驱动功能！
result = await enhanced_coordinator.execute_test_driven_task(
    "您的设计需求 + 测试台路径"
)
```

**完全增量，完全兼容，立即可用！** ✨