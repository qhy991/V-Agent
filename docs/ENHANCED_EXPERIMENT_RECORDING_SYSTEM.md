# 增强实验记录系统

## 问题分析

您提出的问题非常准确：**当前的实验记录格式确实存在混乱的问题**。通过分析现有的 `experiment_report.json` 文件，我发现了以下问题：

### 当前问题

1. **对话内容、工具调用和不同agent信息混在一起**
   - 所有信息都存储在 `conversation_history` 数组中
   - 没有清晰的消息类型区分
   - 工具调用信息嵌入在对话内容中，难以提取

2. **缺乏结构化分类**
   - 无法按消息类型过滤（用户消息、助手响应、工具调用等）
   - 无法按智能体分类查看对话
   - 工具执行记录分散在对话中

3. **信息冗余和重复**
   - 相同的用户请求被重复记录多次
   - 日志信息与对话内容混合
   - 缺乏去重机制

4. **难以分析**
   - 无法快速统计工具使用情况
   - 无法分析智能体性能
   - 无法追踪文件操作历史

## 解决方案

我创建了一个**增强实验记录系统**，能够清晰地区分和记录不同类型的信息：

### 核心组件

#### 1. 增强实验记录器 (`EnhancedExperimentRecorder`)

```python
class EnhancedExperimentRecorder:
    """增强实验记录器 - 清晰区分对话内容、工具调用和不同agent的信息"""
```

**主要特性：**
- **消息类型分类**：用户消息、助手响应、系统消息、工具调用、工具结果、智能体切换、错误、信息
- **智能体类型分类**：协调器、Verilog智能体、代码审查智能体、用户、系统
- **结构化记录**：每种类型的信息都有专门的数据结构
- **会话管理**：为每个智能体维护独立的会话记录

#### 2. 集成模块 (`EnhancedExperimentIntegration`)

```python
class EnhancedExperimentIntegration:
    """增强实验记录集成器 - 将增强实验记录器集成到现有系统中"""
```

**主要功能：**
- **智能体包装**：自动包装现有智能体以记录其活动
- **工具调用追踪**：记录工具调用的参数、结果和执行时间
- **文件操作记录**：追踪文件生成和修改操作
- **错误处理**：记录错误信息和上下文

#### 3. 上下文管理器 (`ExperimentContextManager`)

```python
class ExperimentContextManager:
    """实验上下文管理器 - 提供便捷的实验记录接口"""
```

**使用方式：**
```python
async with context_manager.experiment_context(user_request) as integration:
    # 自动开始和停止记录
    result = await run_experiment(integration)
```

### 数据结构设计

#### 消息类型枚举
```python
class MessageType(Enum):
    USER_PROMPT = "user_prompt"           # 用户消息
    ASSISTANT_RESPONSE = "assistant_response"  # 助手响应
    SYSTEM_PROMPT = "system_prompt"       # 系统消息
    TOOL_CALL = "tool_call"               # 工具调用
    TOOL_RESULT = "tool_result"           # 工具结果
    AGENT_SWITCH = "agent_switch"         # 智能体切换
    ERROR = "error"                       # 错误信息
    INFO = "info"                         # 信息消息
```

#### 智能体类型枚举
```python
class AgentType(Enum):
    COORDINATOR = "coordinator"           # 协调智能体
    VERILOG_AGENT = "verilog_agent"       # Verilog智能体
    CODE_REVIEW_AGENT = "code_review_agent"  # 代码审查智能体
    USER = "user"                         # 用户
    SYSTEM = "system"                     # 系统
```

#### 工具调用记录
```python
@dataclass
class ToolCallRecord:
    tool_name: str                        # 工具名称
    parameters: Dict[str, Any]            # 调用参数
    timestamp: float                      # 时间戳
    agent_id: str                         # 调用智能体
    success: bool                         # 是否成功
    result: Optional[Dict[str, Any]]      # 执行结果
    error_message: Optional[str]          # 错误信息
    execution_time: float                 # 执行时间
```

## 使用方法

### 1. 基础使用

```python
from core.enhanced_experiment_integration import ExperimentContextManager

async def run_experiment(user_request: str):
    context_manager = ExperimentContextManager("my_experiment", Path("experiments/"))
    
    async with context_manager.experiment_context(user_request) as integration:
        # 创建并包装智能体
        coordinator = LLMCoordinatorAgent(config)
        enhanced_coordinator = integration.wrap_coordinator(coordinator)
        
        # 执行任务
        result = await enhanced_coordinator.coordinate_task(user_request)
        
        return result
```

### 2. 使用装饰器

```python
from core.enhanced_experiment_integration import record_experiment

@record_experiment("decorated_experiment", Path("experiments/"))
async def my_experiment(user_request: str, experiment_recorder=None):
    # 自动记录所有活动
    coordinator = experiment_recorder.wrap_coordinator(LLMCoordinatorAgent(config))
    return await coordinator.coordinate_task(user_request)
```

### 3. 手动记录

```python
# 记录用户消息
integration.record_user_message("请设计一个计数器")

# 记录工具调用
integration.record_tool_call(
    agent_id="verilog_agent",
    tool_name="generate_verilog_code",
    parameters={"module_name": "counter"},
    success=True,
    result={"code": "module counter..."},
    execution_time=2.5
)

# 记录文件操作
integration.record_file_operation("generate", "counter.v", "verilog_agent")

# 记录错误
integration.record_error("verilog_agent", "编译失败", {"error_code": "E001"})
```

## 输出文件结构

新的实验记录系统会生成以下文件：

### 1. 主报告文件
- `experiment_report.json` - 完整的实验报告
- `experiment_summary.txt` - 人类可读的摘要

### 2. 分类报告文件
- `conversation_history.json` - 按类型分类的对话历史
- `tool_executions.json` - 工具执行记录
- `agent_sessions.json` - 智能体会话记录
- `analysis_summary.json` - 分析摘要

### 3. 报告内容示例

#### conversation_history.json
```json
[
  {
    "message_id": "msg_0_1234567890",
    "timestamp": 1234567890.123,
    "agent_id": "user",
    "agent_type": "user",
    "message_type": "user_prompt",
    "content": "请设计一个计数器",
    "metadata": {},
    "conversation_round": 0
  },
  {
    "message_id": "msg_1_1234567891",
    "timestamp": 1234567891.123,
    "agent_id": "llm_coordinator_agent",
    "agent_type": "coordinator",
    "message_type": "tool_call",
    "content": "调用工具: identify_task_type",
    "metadata": {
      "tool_name": "identify_task_type",
      "parameters": {"user_request": "请设计一个计数器"},
      "success": true,
      "execution_time": 1.2
    },
    "conversation_round": 0
  }
]
```

#### tool_executions.json
```json
[
  {
    "tool_name": "identify_task_type",
    "agent_id": "llm_coordinator_agent",
    "timestamp": 1234567891.123,
    "parameters": {"user_request": "请设计一个计数器"},
    "success": true,
    "result": {"task_type": "design", "confidence": 0.8},
    "error_message": null,
    "execution_time": 1.2
  }
]
```

#### agent_sessions.json
```json
{
  "llm_coordinator_agent": {
    "agent_id": "llm_coordinator_agent",
    "agent_type": "coordinator",
    "start_time": 1234567890.0,
    "end_time": 1234567900.0,
    "total_execution_time": 10.0,
    "success_count": 1,
    "failure_count": 0,
    "message_count": 5,
    "tool_call_count": 3,
    "messages": [...],
    "tool_calls": [...]
  }
}
```

## 优势对比

### 旧系统 vs 新系统

| 特性 | 旧系统 | 新系统 |
|------|--------|--------|
| **消息分类** | ❌ 混合在一起 | ✅ 按类型清晰分类 |
| **智能体区分** | ❌ 难以区分 | ✅ 按智能体类型分类 |
| **工具调用追踪** | ❌ 嵌入在对话中 | ✅ 独立记录结构 |
| **文件操作记录** | ❌ 无专门记录 | ✅ 专门的文件操作记录 |
| **错误处理** | ❌ 混合在日志中 | ✅ 独立的错误记录 |
| **统计分析** | ❌ 难以分析 | ✅ 内置统计分析 |
| **去重机制** | ❌ 重复记录 | ✅ 智能去重 |
| **查询能力** | ❌ 难以查询 | ✅ 丰富的查询接口 |

### 查询示例

```python
# 获取所有工具调用
tool_calls = recorder.get_tool_calls_by_name("generate_verilog_code")

# 获取特定智能体的对话
agent_conversation = recorder.get_agent_conversation("verilog_agent")

# 获取所有错误消息
error_messages = recorder.get_conversation_by_type(MessageType.ERROR)

# 获取特定智能体的工具调用
agent_tools = recorder.get_tool_calls_by_agent("verilog_agent")
```

## 迁移指南

### 从旧系统迁移

1. **替换实验记录调用**
   ```python
   # 旧方式
   task_context.add_conversation_message(role, content, agent_id)
   
   # 新方式
   integration.add_assistant_message(agent_id, content, metadata)
   ```

2. **更新工具调用记录**
   ```python
   # 旧方式 - 混合在对话中
   conversation.append({"role": "assistant", "content": tool_result})
   
   # 新方式 - 独立记录
   integration.record_tool_call(agent_id, tool_name, parameters, success, result)
   ```

3. **添加文件操作记录**
   ```python
   # 新功能
   integration.record_file_operation("generate", file_path, agent_id)
   ```

## 总结

新的增强实验记录系统解决了您提出的所有问题：

1. ✅ **清晰区分对话内容、工具调用和不同agent信息**
2. ✅ **提供结构化的数据分类**
3. ✅ **消除信息冗余和重复**
4. ✅ **提供强大的分析能力**
5. ✅ **保持向后兼容性**

这个系统不仅解决了当前的问题，还为未来的实验分析提供了强大的基础。您可以轻松地：

- 分析每个智能体的性能
- 追踪工具使用模式
- 识别系统瓶颈
- 生成详细的实验报告
- 进行对比分析

建议您逐步迁移到新的实验记录系统，这将大大改善实验数据的可读性和可分析性。 