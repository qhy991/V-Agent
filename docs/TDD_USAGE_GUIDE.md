# 🧪 统一测试驱动开发(TDD)工具使用指南

## 📋 工具概述

`unified_tdd_test.py` 是一个基于真实LLM驱动的智能Verilog设计工具，采用测试驱动开发(TDD)方法，能够自动生成、测试和优化硬件设计。

### 🎯 核心特性
- **智能设计生成**: 基于需求描述自动生成Verilog代码
- **自动测试台生成**: 为每个设计创建全面的测试台
- **迭代优化**: 通过测试失败反馈自动改进设计
- **质量保证**: 代码质量分析和覆盖率检测
- **结果追踪**: 完整的实验日志和结果保存

## 🚀 快速开始

### 基本用法
```bash
# 使用预定义模板（推荐新手）
python unified_tdd_test.py --design simple_adder

# 使用标准配置
python unified_tdd_test.py --design counter --config standard

# 快速测试模式
python unified_tdd_test.py --design alu --config quick
```

### 高级用法
```bash
# 自定义设计需求
python unified_tdd_test.py --design custom --requirements "设计一个8位UART发射器模块"

# 提供现有测试台
python unified_tdd_test.py --design custom --requirements "设计需求" --testbench my_testbench.v

# 调试模式（更多迭代次数和详细日志）
python unified_tdd_test.py --design alu --config debug --iterations 15

# 指定输出目录
python unified_tdd_test.py --design counter --output-dir ./my_experiment
```

## 📚 预定义设计模板

### 1. **simple_adder** (推荐入门)
- **功能**: 8位简单加法器
- **接口**: `a[7:0]`, `b[7:0]`, `cin`, `sum[7:0]`, `cout`
- **特点**: 设计简单，快速验证TDD流程
- **用法**: `--design simple_adder`

### 2. **counter** 
- **功能**: 8位双向计数器
- **接口**: `clk`, `rst_n`, `enable`, `up_down`, `count[7:0]`, `overflow`
- **特点**: 时序设计，包含复位逻辑
- **用法**: `--design counter`

### 3. **adder_16bit**
- **功能**: 16位加法器
- **接口**: `a[15:0]`, `b[15:0]`, `cin`, `sum[15:0]`, `cout`, `overflow`
- **特点**: 中等复杂度，包含溢出检测
- **用法**: `--design adder_16bit`

### 4. **alu**
- **功能**: 32位算术逻辑单元
- **接口**: `a[31:0]`, `b[31:0]`, `op[3:0]`, `result[31:0]`, `zero`, `overflow`
- **特点**: 高复杂度，支持多种运算
- **用法**: `--design alu`

### 5. **adder**
- **功能**: 16位超前进位加法器
- **接口**: `a[15:0]`, `b[15:0]`, `cin`, `sum[15:0]`, `cout`
- **特点**: 高性能设计，进位优化
- **用法**: `--design adder`

### 6. **custom**
- **功能**: 自定义设计
- **特点**: 完全自定义需求和接口
- **用法**: `--design custom --requirements "你的设计需求"`

## ⚙️ 配置档案

### quick (快速模式)
- **迭代次数**: 3
- **单次超时**: 120秒
- **深度分析**: 禁用
- **适用场景**: 快速原型验证

### standard (标准模式) - 默认
- **迭代次数**: 2
- **单次超时**: 300秒
- **深度分析**: 启用
- **适用场景**: 日常开发

### thorough (彻底模式)
- **迭代次数**: 8
- **单次超时**: 600秒
- **深度分析**: 启用
- **适用场景**: 复杂设计验证

### debug (调试模式)
- **迭代次数**: 10
- **单次超时**: 900秒
- **深度分析**: 启用
- **适用场景**: 问题诊断和复杂调试

## 📊 命令行参数详解

### 必需参数
- `--design` / `-d`: 设计类型选择
  - 选项: `alu`, `counter`, `adder_16bit`, `simple_adder`, `adder`, `custom`
  - 默认: `simple_adder`

### 可选参数
- `--config` / `-c`: 配置档案
  - 选项: `quick`, `standard`, `thorough`, `debug`
  - 默认: `standard`

- `--testbench` / `-t`: 测试台文件路径
  - 用途: 提供现有测试台而非自动生成

- `--requirements` / `-r`: 自定义设计需求
  - 用途: 使用custom设计时的需求描述

- `--iterations` / `-i`: 最大迭代次数
  - 用途: 覆盖配置档案中的默认值

- `--timeout`: 每次迭代超时时间(秒)
  - 用途: 覆盖配置档案中的默认值

- `--no-deep-analysis`: 禁用深度分析
  - 用途: 加快执行速度

- `--output-dir` / `-o`: 输出目录
  - 默认: `tdd_experiments/unified_tdd_设计类型_时间戳`

## 📁 输出结构

每次实验都会在输出目录中生成：

```
unified_tdd_设计类型_时间戳/
├── artifacts/                 # 设计文件
│   ├── 设计模块.v             # 生成的Verilog设计
│   └── 测试台.v              # 生成的测试台
├── logs/                      # 日志文件
│   ├── simulation_output.log  # 仿真输出
│   └── compile_output.log     # 编译输出
├── experiment_report.json     # 详细JSON报告
└── experiment_summary.txt     # 人类可读摘要
```

## 📝 输出文件说明

### experiment_summary.txt
包含关键信息：
- 实验状态（成功/失败）
- 迭代次数和耗时
- 生成文件数量
- 测试结果摘要

### experiment_report.json
包含完整信息：
- 详细的迭代历史
- 工具调用记录
- 错误诊断信息
- 质量度量数据

## 🛠️ 使用示例

### 示例1: 初学者入门
```bash
# 使用最简单的设计快速体验TDD流程
python unified_tdd_test.py --design simple_adder --config quick

# 查看结果
cat tdd_experiments/unified_tdd_simple_adder_*/experiment_summary.txt
```

### 示例2: 标准开发流程
```bash
# 开发一个计数器，使用标准配置
python unified_tdd_test.py --design counter

# 开发一个ALU，使用更多迭代次数
python unified_tdd_test.py --design alu --iterations 5
```

### 示例3: 自定义设计
```bash
# 设计一个FIFO缓冲器
python unified_tdd_test.py --design custom \
    --requirements "设计一个16深度、8位宽的同步FIFO，包含读写指针、满空标志" \
    --config thorough
```

### 示例4: 使用现有测试台
```bash
# 使用预先准备的测试台
python unified_tdd_test.py --design custom \
    --requirements "设计一个SPI主控制器" \
    --testbench ./my_spi_testbench.v \
    --config debug
```

## 🔍 结果分析

### 成功指标
- ✅ `实验状态: 成功`
- ✅ `迭代次数: 1-2` (理想情况)
- ✅ `生成文件: > 0`
- ✅ `完成原因: tests_passed`

### 失败分析
如果实验失败，检查：
1. `experiment_summary.txt` 中的错误原因
2. `logs/` 目录中的详细日志
3. JSON报告中的迭代历史

## ⚠️ 注意事项

### 设计需求编写
- **明确接口**: 详细指定端口名称和位宽
- **功能描述**: 清楚说明期望的行为
- **约束条件**: 指明时序、复位等要求

### 性能优化
- 使用 `quick` 配置进行初步验证
- 复杂设计使用 `thorough` 或 `debug` 配置
- 适当调整 `--iterations` 和 `--timeout` 参数

### 故障排除
- 检查环境配置（.env文件）
- 确保有足够的磁盘空间
- 网络连接正常（LLM API调用）

## 🎯 最佳实践

1. **从简单开始**: 新用户建议从 `simple_adder` 开始
2. **渐进复杂**: 逐步尝试更复杂的设计类型
3. **保存结果**: 成功的实验结果可作为参考模板
4. **迭代改进**: 根据失败结果调整需求描述
5. **合理配置**: 根据设计复杂度选择合适的配置档案

## 🔧 环境要求

- Python 3.8+
- 依赖包: 按照项目requirements.txt安装
- LLM API配置: 在.env文件中配置
- Verilog仿真器: iverilog (推荐)

## 📞 技术支持

如遇问题，请查看：
1. 实验输出的详细日志
2. 项目README文档
3. CLAUDE.md中的架构说明

## 🎉 验证成功案例

### 16位加法器测试结果
- **命令**: `python unified_tdd_test.py --design adder_16bit --config standard`
- **结果**: ✅ 1次迭代成功
- **质量**: 代码质量100分，覆盖率85%+
- **特点**: 正确实现接口、进位处理和溢出检测

### 8位计数器测试结果  
- **命令**: `python unified_tdd_test.py --design counter --config standard`
- **结果**: ✅ 快速通过所有测试
- **特点**: 准确实现rst_n复位逻辑，无接口错误

### 简单加法器测试结果
- **命令**: `python unified_tdd_test.py --design simple_adder --config quick`
- **结果**: ✅ 入门友好，快速验证TDD流程
- **特点**: 设计简洁，适合新手学习

---

🎉 **现在就开始你的TDD硬件设计之旅吧！**