# V-Agent HTML可视化器使用指南

## 📖 概述

V-Agent HTML可视化器是一个强大的工具，用于将实验数据转换为交互式的HTML报告。它完全消除了硬编码，支持动态配置和批量处理。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install plotly numpy
```

### 2. 基本使用

#### 自动发现最新实验
```bash
python html_visualizer.py
```

#### 指定实验路径
```bash
python html_visualizer.py --experiment-path "llm_experiments/my_experiment"
```

#### 指定输出目录
```bash
python html_visualizer.py --output-dir "./reports"
```

#### 使用自定义配置
```bash
python html_visualizer.py --config-file "my_config.json"
```

## 📁 文件结构

```
V-Agent/
├── html_visualizer.py          # 主可视化器
├── batch_visualizer.py         # 批量处理脚本
├── visualizer_config.json      # 默认配置文件
├── README_Visualizer.md        # 本说明文档
├── llm_experiments/            # 实验数据目录
│   ├── experiment_1/
│   ├── experiment_2/
│   └── ...
└── reports/                    # 输出目录
    ├── experiment_1.html
    ├── experiment_2.html
    └── ...
```

## ⚙️ 配置选项

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--experiment-path` | 实验路径 | `./llm_experiments/my_experiment` |
| `--output-dir` | 输出目录 | `./reports` |
| `--config-file` | 配置文件 | `my_config.json` |

### 配置文件选项

```json
{
    "file_patterns": {
        "experiment_reports": ["*.json", "reports/*.json"],
        "experiment_summaries": ["*.txt", "reports/*.txt"],
        "design_files": ["*.v", "designs/*.v"],
        "testbench_files": ["*testbench*.v", "*tb*.v"],
        "log_files": ["*.txt", "*.log", "logs/*.txt"]
    },
    "experiment_discovery": {
        "patterns": ["llm_experiments/*", "experiments/*"],
        "sort_by": "mtime"
    },
    "chart_settings": {
        "colors": {
            "user": "#4CAF50",
            "assistant": "#2196F3"
        },
        "chart_height": 500
    },
    "html_template": {
        "title": "V-Agent 实验可视化报告",
        "subtitle": "基于统一日志系统的实验结果可视化展示"
    }
}
```

## 🔄 批量处理

### 基本批量处理
```bash
python batch_visualizer.py
```

### 限制处理数量
```bash
python batch_visualizer.py --max-experiments 5
```

### 指定搜索模式
```bash
python batch_visualizer.py --pattern "llm_coordinator_*"
```

### 干运行模式（预览）
```bash
python batch_visualizer.py --dry-run
```

### 批量处理参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--base-dir` | 基础目录 | `.` |
| `--pattern` | 实验目录模式 | `llm_coordinator_*` |
| `--output-dir` | 输出目录 | `./batch_reports` |
| `--max-experiments` | 最大处理数量 | 无限制 |
| `--verbose` | 详细输出 | False |
| `--dry-run` | 干运行模式 | False |

## 📊 可视化内容

### 1. 实验概览
- 执行状态
- 任务耗时
- 智能体交互次数
- 工作流阶段数量

### 2. 对话内容分析
- 对话时间线图表
- 详细对话记录
- 交互记录

### 3. 工作流分析
- 工作流执行时间线
- 阶段执行情况

### 4. 性能分析
- 智能体性能对比
- 工作流阶段时间分布

### 5. 代码展示
- Verilog设计代码
- 测试台代码

### 6. 错误分析
- 错误类型统计
- 错误详情分析

### 7. 文件结构
- 实验文件结构
- 文件大小信息

## 🎨 自定义主题

可以通过配置文件自定义HTML报告的主题：

```json
{
    "html_template": {
        "theme": {
            "primary_color": "#667eea",
            "secondary_color": "#764ba2",
            "background_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        }
    }
}
```

## 🔧 高级功能

### 1. 动态文件发现
- 自动查找实验报告、摘要、设计文件等
- 支持多种文件命名模式
- 智能文件排序（按修改时间）

### 2. 错误处理
- 优雅处理缺失文件
- 详细的错误报告
- 批量处理中的错误隔离

### 3. 配置合并
- 支持默认配置和用户配置的深度合并
- 配置文件验证
- 配置热重载

### 4. 输出管理
- 自动创建输出目录
- 实验特定的输出目录
- 汇总报告生成

## 📝 使用示例

### 示例1：处理单个实验
```bash
# 自动发现最新实验
python html_visualizer.py

# 指定特定实验
python html_visualizer.py --experiment-path "llm_experiments/llm_coordinator_counter_1754487994"

# 使用自定义配置和输出目录
python html_visualizer.py \
    --experiment-path "llm_experiments/my_experiment" \
    --config-file "my_config.json" \
    --output-dir "./custom_reports"
```

### 示例2：批量处理
```bash
# 处理所有实验
python batch_visualizer.py

# 只处理前5个实验
python batch_visualizer.py --max-experiments 5

# 使用自定义配置批量处理
python batch_visualizer.py \
    --config-file "my_config.json" \
    --output-dir "./batch_reports" \
    --verbose
```

### 示例3：自定义配置
```json
{
    "file_patterns": {
        "experiment_reports": ["my_report.json", "reports/*.json"],
        "design_files": ["designs/*.v", "**/module*.v"]
    },
    "html_template": {
        "title": "我的实验报告",
        "subtitle": "自定义实验分析"
    },
    "chart_settings": {
        "colors": {
            "user": "#FF6B6B",
            "assistant": "#4ECDC4"
        }
    }
}
```

## 🐛 故障排除

### 常见问题

1. **找不到实验目录**
   - 检查实验目录是否存在
   - 确认搜索模式是否正确
   - 使用 `--dry-run` 预览将要处理的实验

2. **文件读取失败**
   - 检查文件权限
   - 确认文件编码（推荐UTF-8）
   - 查看详细错误信息

3. **依赖包缺失**
   ```bash
   pip install plotly numpy
   ```

4. **配置文件错误**
   - 检查JSON格式是否正确
   - 确认配置文件路径
   - 使用默认配置测试

### 调试模式

启用详细输出：
```bash
python html_visualizer.py --verbose
python batch_visualizer.py --verbose
```

## 📈 性能优化

1. **批量处理优化**
   - 使用 `--max-experiments` 限制处理数量
   - 分批处理大量实验

2. **文件查找优化**
   - 优化文件模式匹配
   - 使用更具体的文件路径

3. **内存优化**
   - 大文件分块读取
   - 及时释放不需要的数据

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 支持

如有问题或建议，请：
1. 查看本文档
2. 检查故障排除部分
3. 提交 Issue
4. 联系维护者 