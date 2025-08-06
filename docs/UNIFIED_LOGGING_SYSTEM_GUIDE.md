# 🎯 统一日志系统使用指南

## 概述

统一日志系统（UnifiedLoggingSystem）是一个专门为多智能体系统设计的标准化日志记录系统，用于规范化所有agent的工具调用和对话记录，确保：

- 统一的数据格式
- 完整的执行轨迹
- 清晰的层次结构
- 易于可视化的数据结构

## 系统架构

### 核心组件

1. **UnifiedLogEvent**: 统一事件数据结构
2. **UnifiedLoggingSystem**: 统一日志记录系统
3. **GradioAgentVisualizer**: Gradio可视化界面

### 事件类型

- **TASK**: 任务开始/结束
- **AGENT**: 智能体开始/结束
- **TOOL**: 工具调用/结果
- **LLM**: LLM调用
- **FILE**: 文件操作
- **ERROR**: 错误信息
- **WARNING**: 警告信息

## 集成状态

### ✅ 已完成集成

1. **工具执行记录** (`core/base_agent.py`)
   - `_execute_tool_call_with_retry()` 方法已集成
   - 自动记录工具调用结果

2. **LLM调用记录**
   - `_call_llm_optimized()` 方法已集成 (`core/base_agent.py`)
   - `_call_llm_traditional()` 方法已集成 (`core/llm_coordinator_agent.py`)
   - `_call_llm_traditional()` 方法已集成 (`agents/enhanced_real_verilog_agent.py`)
   - `_call_llm_traditional()` 方法已集成 (`agents/enhanced_real_code_reviewer.py`)

3. **文件操作记录**
   - `_tool_write_file()` 方法已集成 (`core/base_agent.py`)
   - `_tool_read_file()` 方法已集成 (`core/base_agent.py`)

### 🔧 自动集成

统一日志系统通过以下方式自动集成到现有代码中：

1. **全局实例**: 使用 `get_global_logging_system()` 获取全局实例
2. **自动记录**: 在关键方法中自动记录事件
3. **向后兼容**: 不影响现有功能

## 使用方法

### 1. 基本使用

```python
from core.unified_logging_system import UnifiedLoggingSystem, set_global_logging_system

# 创建日志系统实例
session_id = f"session_{int(time.time())}"
logging_system = UnifiedLoggingSystem(session_id)

# 设置为全局实例
set_global_logging_system(logging_system)

# 开始任务
task_id = logging_system.start_task("task_001", "设计Verilog模块")

# 记录智能体开始
logging_system.log_agent_start("agent_001", "开始设计工作")

# 记录工具调用
logging_system.log_tool_call("agent_001", "generate_verilog_code", {"module": "counter"})

# 记录LLM调用
logging_system.log_llm_call("agent_001", "claude-3.5-sonnet", 
                           prompt_length=100, response_length=200, duration=1.5)

# 记录文件操作
logging_system.log_file_operation("agent_001", "write", "counter.v", file_size=512)

# 结束任务
logging_system.end_task(True, "任务完成")
```

### 2. 在现有代码中使用

由于已经集成到核心方法中，现有代码会自动记录日志：

```python
# 这些调用会自动记录到统一日志系统
await agent._call_llm_optimized("设计一个计数器")
await agent._tool_write_file(filename="counter.v", content="module counter...")
await agent._tool_read_file("counter.v")
```

### 3. 查看日志数据

```python
# 获取执行时间线
timeline = logging_system.get_execution_timeline()

# 获取智能体性能摘要
agent_summary = logging_system.get_agent_performance_summary()

# 获取工具使用摘要
tool_summary = logging_system.get_tool_usage_summary()

# 导出数据
logging_system.export_data("log_data.json")
```

## Gradio可视化

### 启动可视化界面

```python
from gradio_agent_visualizer import GradioAgentVisualizer

# 创建可视化界面
visualizer = GradioAgentVisualizer()
interface = visualizer.create_interface()

# 启动界面
interface.launch(server_port=7860)
```

### 界面功能

1. **实时执行时间线**: 显示所有事件的时序图
2. **智能体性能统计**: 各智能体的执行统计
3. **工具使用分析**: 工具调用频率和成功率
4. **文件操作追踪**: 文件读写操作记录
5. **错误和警告**: 系统错误和警告信息
6. **数据导出**: 导出完整的日志数据

## 运行示例

### 1. 基础演示

```bash
python examples/unified_logging_demo.py
```

### 2. 使用真实Agent

```python
# 在现有代码中，统一日志系统会自动工作
from core.llm_coordinator_agent import LLMCoordinatorAgent
from config.config import FrameworkConfig

config = FrameworkConfig()
coordinator = LLMCoordinatorAgent(config)

# 执行任务时会自动记录日志
result = await coordinator.coordinate_task("设计一个4位加法器")
```

### 3. 启动可视化

```bash
# 运行演示并启动Gradio界面
python examples/unified_logging_demo.py
```

## 数据格式

### UnifiedLogEvent结构

```python
@dataclass
class UnifiedLogEvent:
    event_id: str                    # 事件ID
    timestamp: float                 # 时间戳
    level: LogLevel                  # 日志级别
    category: EventCategory          # 事件类别
    session_id: str                  # 会话ID
    task_id: str                     # 任务ID
    agent_id: str                    # 智能体ID
    title: str                       # 事件标题
    message: str                     # 事件消息
    details: Dict[str, Any]          # 详细信息
    duration: Optional[float]        # 执行时长
    success: bool                    # 是否成功
    error_info: Optional[Dict]       # 错误信息
    parent_event_id: Optional[str]   # 父事件ID
```

### 导出数据格式

```json
{
  "session_id": "session_1234567890",
  "events": [
    {
      "event_id": "task_1234567890",
      "timestamp": 1234567890.123,
      "level": "info",
      "category": "task",
      "title": "任务开始",
      "message": "设计Verilog模块",
      "success": true,
      "duration": 10.5
    }
  ],
  "summary": {
    "total_events": 50,
    "success_rate": 0.95,
    "total_duration": 120.5
  }
}
```

## 配置选项

### 日志级别

```python
from core.unified_logging_system import LogLevel

# 设置日志级别
logging_system.log_event(
    level=LogLevel.INFO,
    category=EventCategory.TOOL,
    title="工具调用",
    message="执行工具",
    agent_id="agent_001"
)
```

### 事件类别

```python
from core.unified_logging_system import EventCategory

# 可用的事件类别
EventCategory.TASK      # 任务相关
EventCategory.AGENT     # 智能体相关
EventCategory.TOOL      # 工具相关
EventCategory.LLM       # LLM相关
EventCategory.FILE      # 文件相关
EventCategory.ERROR     # 错误相关
EventCategory.WARNING   # 警告相关
```

## 最佳实践

### 1. 会话管理

```python
# 为每个任务创建独立的会话
session_id = f"task_{task_id}_{int(time.time())}"
logging_system = UnifiedLoggingSystem(session_id)
set_global_logging_system(logging_system)
```

### 2. 错误处理

```python
try:
    result = await agent.execute_task()
    logging_system.log_tool_result(agent_id, tool_name, success=True, result=result)
except Exception as e:
    logging_system.log_error(agent_id, "任务执行失败", {"error": str(e)})
```

### 3. 性能监控

```python
# 记录执行时间
start_time = time.time()
result = await agent.execute_task()
duration = time.time() - start_time

logging_system.log_tool_result(
    agent_id=agent.agent_id,
    tool_name="execute_task",
    success=True,
    result=result,
    duration=duration
)
```

## 故障排除

### 常见问题

1. **日志系统未初始化**
   ```python
   # 确保在使用前初始化
   from core.unified_logging_system import get_global_logging_system
   logging_system = get_global_logging_system()
   ```

2. **事件记录失败**
   ```python
   # 检查事件参数
   try:
       logging_system.log_event(...)
   except Exception as e:
       print(f"事件记录失败: {e}")
   ```

3. **Gradio界面无法启动**
   ```python
   # 检查端口是否被占用
   interface.launch(server_port=7861)  # 尝试其他端口
   ```

### 调试模式

```python
# 启用调试模式
logging_system.logger.setLevel(logging.DEBUG)

# 查看详细日志
for event in logging_system.events:
    print(f"{event.timestamp}: {event.title} - {event.message}")
```

## 总结

统一日志系统已经完全集成到您的主代码中，提供了：

1. **自动记录**: 所有关键操作都会自动记录
2. **标准化格式**: 统一的事件数据结构
3. **可视化支持**: Gradio界面实时展示
4. **数据导出**: 支持JSON格式导出
5. **性能监控**: 详细的执行时间统计

现在您可以运行 `python examples/unified_logging_demo.py` 来体验完整的日志系统功能！ 