# 🎯 V-Agent 实验可视化使用指南

## 📋 概述

本指南介绍如何使用 `counter_test_utf8_fixed_20250806_145707.txt` 和相关的实验文件进行Gradio可视化展示。

## 🗂️ 关键文件说明

### 1. 主要数据源文件

| 文件路径 | 用途 | 大小 | 格式 |
|---------|------|------|------|
| `llm_experiments/llm_coordinator_counter_1754463430/reports/experiment_report.json` | 核心数据源 | 26KB | JSON |
| `llm_experiments/llm_coordinator_counter_1754463430/reports/experiment_summary.txt` | 实验摘要 | 476B | 文本 |
| `llm_experiments/llm_coordinator_counter_1754463430/designs/counter_v2.v` | 设计代码 | 279B | Verilog |
| `llm_experiments/llm_coordinator_counter_1754463430/testbenches/testbench_counter.v` | 测试台代码 | 5.3KB | Verilog |

### 2. 日志文件

| 文件路径 | 用途 | 大小 | 格式 |
|---------|------|------|------|
| `counter_test_utf8_fixed_20250806_145707.txt` | 详细执行日志 | 467行 | 文本 |

## 🚀 使用方法

### 方法1：使用实验可视化器（推荐）

```bash
# 1. 安装依赖
pip install gradio plotly

# 2. 运行可视化器
python experiment_visualizer.py
```

### 方法2：手动解析数据

```python
import json
from pathlib import Path

# 加载实验报告
report_path = Path("llm_experiments/llm_coordinator_counter_1754463430/reports/experiment_report.json")
with open(report_path, 'r', encoding='utf-8') as f:
    experiment_data = json.load(f)

# 提取关键信息
experiment_id = experiment_data['experiment_id']
task_duration = experiment_data['task_duration']
agent_interactions = experiment_data['agent_interactions']
workflow_stages = experiment_data['workflow_stages']
```

## 📊 可视化内容

### 1. 实验概览
- 实验基本信息（ID、类型、状态）
- 性能指标（耗时、交互次数、工具执行次数）
- 文件结构展示

### 2. 工作流分析
- 执行时间线图表
- 智能体性能对比
- 工具调用统计

### 3. 代码展示
- Verilog设计代码（语法高亮）
- 测试台代码（语法高亮）
- 代码质量分析

### 4. 错误分析
- 仿真失败原因
- 错误恢复建议
- 改进方案

### 5. 原始数据
- 完整JSON报告
- 实验摘要文本
- 结构化数据展示

## 🔧 自定义可视化

### 修改实验ID
```python
class ExperimentVisualizer:
    def __init__(self):
        # 修改为你的实验ID
        self.experiment_id = "your_experiment_id"
        self.base_path = Path("llm_experiments") / self.experiment_id
```

### 添加新的图表
```python
def create_custom_chart(self):
    """创建自定义图表"""
    # 使用 plotly 创建图表
    fig = go.Figure()
    # ... 图表配置
    return fig
```

### 扩展数据源
```python
def load_additional_data(self):
    """加载额外数据"""
    # 加载日志文件
    log_path = Path("counter_test_utf8_fixed_20250806_145707.txt")
    with open(log_path, 'r', encoding='utf-8') as f:
        self.log_data = f.read()
```

## 📈 数据解析示例

### 解析智能体交互数据
```python
def parse_agent_interactions(self):
    """解析智能体交互数据"""
    interactions = self.experiment_report.get('agent_interactions', [])
    
    for interaction in interactions:
        agent_id = interaction['target_agent_id']
        execution_time = interaction['execution_time']
        response_length = interaction['response_length']
        
        print(f"智能体: {agent_id}")
        print(f"执行时间: {execution_time:.2f}秒")
        print(f"响应长度: {response_length}字符")
```

### 解析工作流阶段
```python
def parse_workflow_stages(self):
    """解析工作流阶段"""
    stages = self.experiment_report.get('workflow_stages', [])
    
    for stage in stages:
        stage_name = stage['stage_name']
        duration = stage['duration']
        success = stage['success']
        
        print(f"阶段: {stage_name}")
        print(f"耗时: {duration:.2f}秒")
        print(f"状态: {'成功' if success else '失败'}")
```

## 🎨 界面定制

### 修改主题
```python
# 使用不同的Gradio主题
interface = gr.Blocks(
    title="V-Agent 实验可视化器", 
    theme=gr.themes.Soft()  # 或 gr.themes.Default()
)
```

### 添加交互功能
```python
def filter_by_agent(agent_id):
    """按智能体筛选数据"""
    # 实现筛选逻辑
    pass

# 在界面中添加筛选器
gr.Dropdown(
    choices=["enhanced_real_verilog_agent", "enhanced_real_code_review_agent"],
    label="选择智能体",
    value=filter_by_agent
)
```

## 🔍 故障排除

### 常见问题

1. **文件路径错误**
   ```
   错误: 无法加载实验数据
   解决: 检查文件路径是否正确
   ```

2. **编码问题**
   ```
   错误: UnicodeDecodeError
   解决: 确保使用UTF-8编码打开文件
   ```

3. **依赖缺失**
   ```
   错误: ModuleNotFoundError
   解决: pip install gradio plotly
   ```

### 调试模式
```python
# 启用调试模式
interface.launch(debug=True)
```

## 📝 扩展建议

1. **添加实时监控**：集成WebSocket实现实时数据更新
2. **多实验对比**：支持同时展示多个实验的结果对比
3. **导出功能**：添加PDF报告导出功能
4. **交互式分析**：添加数据钻取和详细分析功能
5. **性能优化**：对大数据集进行分页和懒加载

## 🎯 总结

通过这个可视化系统，你可以：

- ✅ 直观地查看实验执行结果
- ✅ 分析智能体性能和交互模式
- ✅ 识别工作流中的瓶颈和问题
- ✅ 展示生成的代码和文件结构
- ✅ 进行错误分析和改进建议

这个可视化工具充分利用了统一日志系统收集的结构化数据，为V-Agent的实验结果提供了专业、美观的展示界面。 