# 🧪 测试驱动开发(TDD)功能使用指南

## 📋 功能概述

本框架提供完整的测试驱动开发功能，支持：
- ✅ **多轮迭代**：AI智能体根据测试结果自动改进设计
- ✅ **完整保存**：每次迭代的结果、日志、文件都完整保存
- ✅ **易用入口**：统一的命令行接口，支持多种配置
- ✅ **结果分析**：详细的实验报告和迭代历史追踪

## 🚀 快速开始

### 1. 统一测试入口

```bash
# 基本使用 - ALU设计
python unified_tdd_test.py --design alu

# 超前进位加法器 - 快速测试
python unified_tdd_test.py --design adder --config quick

# 自定义设计
python unified_tdd_test.py --design custom --requirements "设计一个UART模块" --testbench uart_tb.v
```

### 2. 配置档案

| 档案 | 迭代次数 | 超时(秒) | 深度分析 | 适用场景 |
|------|----------|----------|----------|----------|
| `quick` | 3 | 120 | ❌ | 快速验证 |
| `standard` | 5 | 300 | ✅ | 标准开发 |
| `thorough` | 8 | 600 | ✅ | 复杂设计 |
| `debug` | 10 | 900 | ✅ | 问题调试 |

### 3. 预定义设计模板

- **alu**: 32位算术逻辑单元
- **counter**: 8位可控计数器  
- **adder**: 16位超前进位加法器
- **custom**: 自定义设计需求

## 💾 结果保存机制

### 实验日志结构
```
logs/experiment_YYYYMMDD_HHMMSS/
├── experiment_summary.log          # 实验总结
├── artifacts/                      # 生成的文件
│   ├── debug_iterations/           # 迭代历史
│   │   ├── iteration_1_*.v        # 第1次迭代设计
│   │   ├── iteration_2_*.v        # 第2次迭代设计
│   │   └── ...                     # 每次迭代都保存
│   └── debug_validation/           # 验证文件
├── [agent_name].log                # 各智能体详细日志
└── all_errors.log                  # 错误汇总
```

### 实验报告
```
unified_tdd_report_[实验ID].json    # 完整实验分析报告
```

## 🔧 高级用法

### 1. 编程接口
```python
from extensions import create_test_driven_coordinator, TestDrivenConfig

# 创建TDD协调器
tdd_config = TestDrivenConfig(max_iterations=5, enable_deep_analysis=True)
tdd_coordinator = create_test_driven_coordinator(your_coordinator, tdd_config)

# 执行测试驱动任务
result = await tdd_coordinator.execute_test_driven_task(
    task_description="设计需求",
    testbench_path="path/to/testbench.v"
)
```

### 2. 查看迭代历史
```python
# 获取会话信息
session_info = tdd_coordinator.get_session_info(session_id)

# 获取迭代历史
history = tdd_coordinator.get_iteration_history(session_id)
```

### 3. 自定义配置
```bash
# 完全自定义配置
python unified_tdd_test.py --design alu --iterations 10 --timeout 600 --no-deep-analysis
```

## 📊 结果分析

### 成功指标
- **功能正确性**: 通过所有测试用例
- **迭代效率**: 较少迭代次数达到目标
- **设计质量**: AI生成的设计符合最佳实践

### 失败分析
- **编译错误**: 语法错误、模块接口问题
- **功能错误**: 逻辑实现不正确
- **性能问题**: 不满足时序要求

### 查看详细结果
```bash
# 查看最新实验日志
ls -la logs/experiment_*/

# 查看具体迭代设计
cat logs/experiment_*/artifacts/debug_iterations/iteration_2_*.v

# 查看实验报告
cat unified_tdd_report_*.json
```

## 🎯 最佳实践

### 1. 测试台设计
- 覆盖所有功能点
- 包含边界条件测试
- 清晰的错误提示信息
- 明确的成功标准

### 2. 设计需求描述
- 明确模块接口规格
- 详细功能要求说明
- 性能和约束条件
- 预期的测试标准

### 3. 配置选择
- **开发阶段**: 使用 `standard` 配置
- **问题调试**: 使用 `debug` 配置
- **快速验证**: 使用 `quick` 配置
- **复杂项目**: 使用 `thorough` 配置

## 🔍 故障排除

### 常见问题
1. **测试台文件不存在**: 检查路径，或使用预定义模板
2. **LLM调用失败**: 检查API配置和网络连接
3. **编译错误**: 查看 `all_errors.log` 了解详情
4. **超时问题**: 调整 `--timeout` 参数或使用更高级的配置档案

### 调试技巧
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 使用调试配置
python unified_tdd_test.py --design alu --config debug

# 查看特定智能体日志
tail -f logs/experiment_*/real_verilog_agent.log
```

## 🎉 成功案例

### 超前进位加法器
- **测试**: `python unified_tdd_test.py --design adder`
- **结果**: 2次迭代成功，通过20个测试用例
- **特点**: AI正确实现超前进位逻辑

### 32位ALU
- **测试**: `python unified_tdd_test.py --design alu --config standard`
- **结果**: 支持8种运算，完整标志位输出
- **验证**: 通过算术、逻辑、比较运算全覆盖测试

这个TDD功能为硬件设计提供了强大的迭代改进能力，显著提高设计质量和开发效率！🚀