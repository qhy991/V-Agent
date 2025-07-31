# CentralizedAgentFramework 实验日志摘要

**实验ID**: 20250731_111540
**开始时间**: 2025-07-31 11:17:07
**日志目录**: logs/experiment_20250731_111540
**工件目录**: logs/experiment_20250731_111540/artifacts

## 📁 日志文件说明

- **framework.log** (framework): 0 bytes
- **centralized_coordinator.log** (coordinator): 13527 bytes
- **base_agent.log** (base_agent): 8940 bytes
- **verilog_design_agent.log** (verilog_agent): 0 bytes
- **code_review_agent.log** (code_reviewer): 0 bytes
- **real_verilog_agent.log** (real_verilog_agent): 92 bytes
- **real_code_reviewer.log** (real_code_reviewer): 86 bytes
- **function_calling.log** (function_calling): 0 bytes
- **llm_client.log** (llm_client): 0 bytes
- **enhanced_llm_client.log** (enhanced_llm_client): 0 bytes
- **database.log** (database): 0 bytes
- **tools.log** (tools): 0 bytes
- **verilog_tools.log** (verilog_tools): 0 bytes
- **test_runner.log** (test_runner): 0 bytes
- **test_framework.log** (test_framework): 80 bytes
- **validation.log** (validation): 0 bytes
- **workflow.log** (workflow): 0 bytes
- **config.log** (config): 0 bytes
- **debug.log** (debug): 0 bytes
- **performance.log** (performance): 0 bytes
- **error.log** (error): 0 bytes

## 🛠️ 生成的工件

- **task_report_task_1753931774367.json**: 4111 bytes
- **adder_4bit_tb.v**: 1358 bytes
- **coordination_report_conv_1753931740580.json**: 17131 bytes
- **task_report_task_1753931744465.json**: 2568 bytes
- **adder_4bit.v**: 487 bytes
- **code_quality_report.md**: 409 bytes

## 🔍 快速查看命令

```bash
# 查看实验摘要
tail -f logs/experiment_20250731_111540/experiment_summary.log

# 查看所有错误
cat logs/experiment_20250731_111540/all_errors.log

# 查看特定组件日志
tail -f logs/experiment_20250731_111540/coordinator.log
tail -f logs/experiment_20250731_111540/real_verilog_agent.log
tail -f logs/experiment_20250731_111540/real_code_reviewer.log

# 查看生成的工件
ls -la logs/experiment_20250731_111540/artifacts
```
