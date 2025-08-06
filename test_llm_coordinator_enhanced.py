#!/usr/bin/env python3
"""
增强的LLM协调智能体测试入口
==================================================

这个脚本提供了一个完整、易用的LLM协调测试入口，支持：
- 每次实验使用独立文件夹存储结果
- 配置化的实验参数
- 详细的进度跟踪和结果分析
- LLM驱动的智能协调
- 实验报告和文件管理

使用方法:
    python test_llm_coordinator_enhanced.py --design 4bit_adder
    python test_llm_coordinator_enhanced.py --design counter --iterations 3
    python test_llm_coordinator_enhanced.py --design custom --requirements "设计需求文本"
    python test_llm_coordinator_enhanced.py --output-dir "custom_exp_dir"
    python test_llm_coordinator_enhanced.py --design custom --external-testbench "path/to/testbench.v"
"""

import asyncio
import sys
import argparse
import json
import time
import os
import codecs
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# 设置编码环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

def setup_encoding():
    """设置适当的编码以处理不同操作系统的输出"""
    if os.name == 'nt':  # Windows
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
    else:
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')

# 应用编码设置
setup_encoding()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.enhanced_logging_config import get_test_logger


class EnhancedLLMCoordinatorTest:
    """增强的LLM协调智能体测试入口"""
    
    # 预定义的设计模板
    DESIGN_TEMPLATES = {
        "4bit_adder": {
            "description": """
设计一个4位加法器模块，包含：

**基本要求**：
1. 两个4位输入端口：a[3:0], b[3:0]
2. 一个进位输入：cin
3. 一个4位输出端口：sum[3:0]
4. 一个进位输出：cout
5. 使用组合逻辑实现（不包含时钟和复位信号）

**功能要求**：
- 实现基本的二进制加法运算
- 正确处理进位传播
- 输出结果 = a + b + cin

**质量要求**：
- 代码必须符合Verilog-2001标准
- 包含详细的端口注释
- 生成对应的测试台验证功能
""",
            "expected_files": ["four_bit_adder.v", "four_bit_adder_tb.v"]
        },
        
        "8bit_counter": {
            "description": """
设计一个8位二进制计数器模块，包含：

**基本要求**：
1. 时钟输入：clk
2. 复位输入：rst (高电平有效)
3. 使能输入：en
4. 8位输出：count[7:0]

**功能要求**：
- 在时钟上升沿计数
- 复位时输出为0
- 使能有效时递增计数
- 达到最大值后回绕到0

**质量要求**：
- 使用同步复位
- 符合时序设计规范
- 包含完整的测试台
""",
            "expected_files": ["counter_8bit.v", "counter_8bit_tb.v"]
        },
        
        "alu_simple": {
            "description": """
设计一个简单的算术逻辑单元(ALU)，支持基本操作：

**基本要求**：
1. 两个8位数据输入：a[7:0], b[7:0]
2. 3位操作码输入：op[2:0]
3. 8位结果输出：result[7:0]
4. 标志位输出：zero_flag

**操作码定义**：
- 3'b000: 加法 (a + b)
- 3'b001: 减法 (a - b)
- 3'b010: 逻辑与 (a & b)
- 3'b011: 逻辑或 (a | b)
- 3'b100: 异或 (a ^ b)
- 其他: 输出0

**质量要求**：
- 使用组合逻辑实现
- 包含零标志检测
- 完整的功能测试
""",
            "expected_files": ["alu_simple.v", "alu_simple_tb.v"]
        }
    }
    
    # 实验配置模板
    EXPERIMENT_CONFIGS = {
        "fast": {"max_iterations": 1, "timeout_per_iteration": 180},
        "standard": {"max_iterations": 3, "timeout_per_iteration": 300},
        "thorough": {"max_iterations": 5, "timeout_per_iteration": 600}
    }
    
    def __init__(self, 
                design_type: str = "4bit_adder", 
                config_profile: str = "standard",
                custom_requirements: str = None,
                output_dir: str = None,
                max_iterations: int = None,
                external_testbench_path: str = None):
        """初始化增强LLM协调测试"""
        
        self.design_type = design_type
        self.config_profile = config_profile
        self.custom_requirements = custom_requirements
        self.external_testbench_path = external_testbench_path
        
        # 实验配置
        base_config = self.EXPERIMENT_CONFIGS.get(config_profile, self.EXPERIMENT_CONFIGS["standard"])
        self.max_iterations = max_iterations or base_config["max_iterations"]
        self.timeout_per_iteration = base_config["timeout_per_iteration"]
        
        # 生成实验ID和输出目录
        timestamp = int(time.time())
        self.experiment_id = f"llm_coordinator_{design_type}_{timestamp}"
        
        # 创建专用输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = project_root / "llm_experiments" / self.experiment_id
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化实验状态
        self.experiment_state = {
            "start_time": timestamp,
            "generated_files": [],
            "agent_results": {},
            "coordination_history": [],
            "total_iterations": 0
        }
        
        print(f"🧠 增强LLM协调智能体测试")
        print("=" * 60)
        print(f"   设计类型: {design_type}")
        print(f"   配置档案: {config_profile}")
        print(f"   最大迭代: {self.max_iterations}")
        print(f"   实验ID: {self.experiment_id}")
        print(f"   输出目录: {self.output_dir}")
        if self.external_testbench_path:
            print(f"   外部Testbench: {self.external_testbench_path}")
        print("=" * 60)
    
    def get_design_requirements(self) -> str:
        """获取设计需求"""
        if self.custom_requirements:
            return self.custom_requirements
        
        template = self.DESIGN_TEMPLATES.get(self.design_type)
        if not template:
            # 如果没有预定义模板，使用通用模板
            return f"""
请设计一个名为 {self.design_type} 的Verilog模块。

**基本要求**：
1. 生成完整、可编译的Verilog代码
2. 包含适当的端口定义和功能实现
3. 符合Verilog标准语法
4. 生成对应的测试台进行验证

**质量要求**：
- 代码结构清晰，注释完善
- 遵循良好的命名规范
- 确保功能正确性
"""
        
        return template["description"]
    
    async def setup_experiment_environment(self):
        """设置实验环境"""
        try:
            print("\n🔧 设置实验环境...")
            
            # 创建实验目录结构
            subdirs = ["designs", "testbenches", "logs", "artifacts", "reports"]
            for subdir in subdirs:
                (self.output_dir / subdir).mkdir(exist_ok=True)
            
            # 创建实验元数据
            metadata = {
                "experiment_id": self.experiment_id,
                "design_type": self.design_type,
                "config_profile": self.config_profile,
                "max_iterations": self.max_iterations,
                "created_at": datetime.now().isoformat(),
                "status": "running",
                "output_directory": str(self.output_dir),
                "external_testbench_path": self.external_testbench_path
            }
            
            metadata_file = self.output_dir / "experiment_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 初始化框架配置
            self.config = FrameworkConfig.from_env()
            
            print(f"   ✅ 实验目录创建: {self.output_dir}")
            print(f"   ✅ 元数据保存: {metadata_file.name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 环境设置失败: {str(e)}")
            return False
    
    async def create_llm_coordinator(self):
        """创建LLM协调智能体"""
        try:
            print("\n🤖 创建LLM协调智能体...")
            
            # 创建协调智能体
            self.coordinator = LLMCoordinatorAgent(self.config)
            
            # 创建并注册工作智能体
            self.verilog_agent = EnhancedRealVerilogAgent(self.config)
            self.code_reviewer_agent = EnhancedRealCodeReviewAgent(self.config)
            
            await self.coordinator.register_agent(self.verilog_agent)
            await self.coordinator.register_agent(self.code_reviewer_agent)
            
            print(f"   ✅ 协调智能体创建完成")
            print(f"   ✅ 注册智能体: enhanced_real_verilog_agent")
            print(f"   ✅ 注册智能体: enhanced_real_code_review_agent")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 协调智能体创建失败: {str(e)}")
            import traceback
            print(f"   📋 详细错误信息:")
            traceback.print_exc()
            return False
    
    async def run_experiment(self):
        """运行实验"""
        experiment_start = time.time()
        
        try:
            # 1. 设置实验环境
            if not await self.setup_experiment_environment():
                return {"success": False, "error": "实验环境设置失败"}
            
            # 2. 创建LLM协调智能体
            if not await self.create_llm_coordinator():
                return {"success": False, "error": "协调智能体创建失败"}
            
            # 3. 获取设计需求
            requirements = self.get_design_requirements()
            print(f"\n📋 设计需求:")
            print(requirements)
            
            # 4. 执行协调任务
            print(f"\n🚀 开始执行协调任务...")
            print(f"   最大迭代次数: {self.max_iterations}")
            print(f"   超时时间: {self.timeout_per_iteration}秒")
            
            # 生成唯一的对话ID
            conversation_id = f"exp_{self.experiment_id}"
            
            task_start = time.time()
            result = await self.coordinator.coordinate_task(
                user_request=requirements,
                conversation_id=conversation_id,
                max_iterations=self.max_iterations,
                external_testbench_path=self.external_testbench_path
            )
            task_duration = time.time() - task_start
            
            # 5. 分析结果
            analysis = await self.analyze_experiment_result(result, task_duration)
            
            # 6. 保存实验报告
            await self.save_experiment_report(analysis)
            
            # 7. 复制生成的文件
            await self.organize_experiment_files(result)
            
            total_duration = time.time() - experiment_start
            
            # 8. 显示最终结果
            self.display_experiment_summary(analysis, total_duration)
            
            return analysis
            
        except Exception as e:
            error_duration = time.time() - experiment_start
            error_result = {
                "success": False,
                "error": str(e),
                "experiment_id": self.experiment_id,
                "duration": error_duration
            }
            
            print(f"\n❌ 实验执行异常: {str(e)}")
            await self.save_experiment_report(error_result)
            return error_result
    
    async def analyze_experiment_result(self, result: Dict[str, Any], task_duration: float) -> Dict[str, Any]:
        """分析实验结果"""
        print(f"\n📊 分析实验结果...")
        
        success = result.get('success', False)
        
        # 基础分析
        analysis = {
            "experiment_id": self.experiment_id,
            "design_type": self.design_type,
            "config_profile": self.config_profile,
            "success": success,
            "task_duration": task_duration,
            "timestamp": time.time(),
            "detailed_result": result
        }
        
        if success:
            # 成功情况的详细分析
            execution_summary = result.get('execution_summary', {})
            agent_results = result.get('agent_results', {})
            
            # 🆕 获取增强的数据收集字段
            task_context = result.get('task_context', {})
            tool_executions = task_context.get('tool_executions', [])
            agent_interactions = task_context.get('agent_interactions', [])
            performance_metrics = task_context.get('performance_metrics', {})
            workflow_stages = task_context.get('workflow_stages', [])
            file_operations = task_context.get('file_operations', [])
            execution_timeline = task_context.get('execution_timeline', [])
            data_collection_summary = task_context.get('data_collection_summary', {})
            llm_conversations = task_context.get('llm_conversations', [])
            
            # 🆕 增强数据分析
            analysis.update({
                "tool_executions": tool_executions,
                "agent_interactions": agent_interactions,
                "performance_metrics": performance_metrics,
                "workflow_stages": workflow_stages,
                "file_operations": file_operations,
                "execution_timeline": execution_timeline,
                "data_collection_summary": data_collection_summary,
                "llm_conversations": llm_conversations,
                # 🆕 统计信息
                "tool_execution_count": len(tool_executions),
                "agent_interaction_count": len(agent_interactions),
                "workflow_stage_count": len(workflow_stages),
                "file_operation_count": len(file_operations),
                "execution_timeline_count": len(execution_timeline),
                "llm_conversation_count": len(llm_conversations),
                # 🆕 基础统计信息
                "total_iterations": execution_summary.get('total_iterations', 0),
                "agent_count": len(agent_results),
                "coordination_result_length": len(result.get('coordination_result', '')),
                "agent_performance": {}
            })
            
            # 分析每个智能体的表现
            for agent_id, agent_result in agent_results.items():
                agent_exec_time = agent_result.get('execution_time', 0)
                agent_success = agent_result.get('success', False)
                result_length = len(str(agent_result.get('result', '')))
                
                # 🆕 从工具执行记录中计算智能体工具使用统计
                agent_tool_count = len([t for t in tool_executions if t.get('agent_id') == agent_id])
                
                analysis["agent_performance"][agent_id] = {
                    "execution_time": agent_exec_time,
                    "success": agent_success,
                    "result_length": result_length,
                    "efficiency": result_length / max(agent_exec_time, 0.1),  # 字符/秒
                    "tool_usage_count": agent_tool_count  # 🆕 工具使用次数
                }
            
            print(f"   ✅ 实验成功完成")
            print(f"   📈 总迭代次数: {analysis['total_iterations']}")
            print(f"   🤖 参与智能体: {len(agent_results)}")
            print(f"   🔧 工具执行次数: {analysis['tool_execution_count']}")
            print(f"   💬 智能体交互次数: {analysis['agent_interaction_count']}")
            print(f"   📁 文件操作次数: {analysis['file_operation_count']}")
            print(f"   ⏱️ 任务执行时间: {task_duration:.1f}秒")
        else:
            analysis.update({
                "error_message": result.get('error', '未知错误'),
                "failure_stage": "coordination"
            })
            print(f"   ❌ 实验失败")
            print(f"   💥 错误信息: {analysis['error_message']}")
        
        return analysis
    
    async def save_experiment_report(self, analysis: Dict[str, Any]):
        """保存实验报告"""
        try:
            # 保存详细JSON报告
            report_path = self.output_dir / "reports" / "experiment_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存人类可读的摘要
            summary_path = self.output_dir / "reports" / "experiment_summary.txt"
            await self.save_text_summary(analysis, summary_path)
            
            print(f"\n📄 实验报告已保存:")
            print(f"   📊 详细报告: {report_path}")
            print(f"   📝 摘要报告: {summary_path}")
            
        except Exception as e:
            print(f"   ⚠️ 报告保存失败: {str(e)}")
    
    async def save_text_summary(self, analysis: Dict[str, Any], summary_path: Path):
        """保存人类可读的文本摘要"""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LLM协调智能体实验报告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"实验ID: {analysis['experiment_id']}\n")
            f.write(f"设计类型: {analysis['design_type']}\n")
            f.write(f"配置档案: {analysis['config_profile']}\n")
            f.write(f"实验状态: {'✅ 成功' if analysis['success'] else '❌ 失败'}\n")
            f.write(f"任务耗时: {analysis['task_duration']:.2f} 秒\n")
            f.write(f"时间戳: {datetime.fromtimestamp(analysis['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if analysis.get('success'):
                f.write("执行统计:\n")
                f.write(f"- 总迭代次数: {analysis.get('total_iterations', 0)}\n")
                f.write(f"- 参与智能体: {analysis.get('agent_count', 0)} 个\n")
                f.write(f"- 协调结果长度: {analysis.get('coordination_result_length', 0)} 字符\n\n")
                
                # 🆕 数据收集统计
                data_summary = analysis.get('data_collection_summary', {})
                if data_summary:
                    f.write("数据收集统计:\n")
                    
                    tool_stats = data_summary.get('tool_executions', {})
                    f.write(f"- 工具调用: {tool_stats.get('total', 0)} 次 (成功: {tool_stats.get('successful', 0)}, 失败: {tool_stats.get('failed', 0)})\n")
                    f.write(f"- 使用工具: {', '.join(tool_stats.get('unique_tools', []))}\n")
                    f.write(f"- 工具执行总时间: {tool_stats.get('total_execution_time', 0):.2f}秒\n")
                    
                    file_stats = data_summary.get('file_operations', {})
                    f.write(f"- 文件操作: {file_stats.get('total', 0)} 次 (成功: {file_stats.get('successful', 0)}, 失败: {file_stats.get('failed', 0)})\n")
                    f.write(f"- 操作类型: {', '.join(file_stats.get('operation_types', []))}\n")
                    f.write(f"- 总文件大小: {file_stats.get('total_file_size', 0)} 字节\n")
                    
                    workflow_stats = data_summary.get('workflow_stages', {})
                    f.write(f"- 工作流阶段: {workflow_stats.get('total', 0)} 个 (成功: {workflow_stats.get('successful', 0)}, 失败: {workflow_stats.get('failed', 0)})\n")
                    f.write(f"- 工作流总时间: {workflow_stats.get('total_duration', 0):.2f}秒\n")
                    
                    agent_stats = data_summary.get('agent_interactions', {})
                    f.write(f"- 智能体交互: {agent_stats.get('total', 0)} 次 (成功: {agent_stats.get('successful', 0)}, 失败: {agent_stats.get('failed', 0)})\n")
                    f.write(f"- 参与智能体: {', '.join(agent_stats.get('unique_agents', []))}\n")
                    
                    timeline_stats = data_summary.get('execution_timeline', {})
                    f.write(f"- 执行事件: {timeline_stats.get('total_events', 0)} 个\n")
                    f.write(f"- 事件类型: {', '.join(timeline_stats.get('event_types', []))}\n\n")
                    
                    # 🆕 LLM对话统计
                    llm_stats = data_summary.get('llm_conversations', {})
                    f.write(f"- LLM对话: {llm_stats.get('total', 0)} 次 (成功: {llm_stats.get('successful', 0)}, 失败: {llm_stats.get('failed', 0)})\n")
                    f.write(f"- 参与智能体: {', '.join(llm_stats.get('unique_agents', []))}\n")
                    f.write(f"- 使用模型: {', '.join(llm_stats.get('unique_models', []))}\n")
                    f.write(f"- 首次调用: {llm_stats.get('first_calls', 0)} 次\n")
                    f.write(f"- 总对话时间: {llm_stats.get('total_duration', 0):.2f}秒\n")
                    f.write(f"- 总Token数: {llm_stats.get('total_tokens', 0)} 个\n\n")
                
                # 智能体性能分析
                agent_perf = analysis.get('agent_performance', {})
                if agent_perf:
                    f.write("智能体性能:\n")
                    for agent_id, perf in agent_perf.items():
                        f.write(f"- {agent_id}:\n")
                        f.write(f"  执行时间: {perf['execution_time']:.2f}秒\n")
                        f.write(f"  执行状态: {'成功' if perf['success'] else '失败'}\n")
                        f.write(f"  结果长度: {perf['result_length']} 字符\n")
                        f.write(f"  处理效率: {perf['efficiency']:.1f} 字符/秒\n")
                        f.write(f"  工具使用: {perf.get('tool_usage_count', 0)} 次\n\n")
            else:
                f.write(f"失败原因: {analysis.get('error_message', '未知错误')}\n")
                f.write(f"失败阶段: {analysis.get('failure_stage', '未知')}\n")
    
    async def organize_experiment_files(self, result: Dict[str, Any]):
        """整理实验生成的文件"""
        try:
            print(f"\n📁 整理实验文件...")
            
            # 检查当前工作区域的文件
            workspace_dirs = [
                project_root / "file_workspace" / "designs",
                project_root / "file_workspace" / "testbenches",
                self.output_dir / "artifacts"
            ]
            
            copied_files = []
            
            for workspace_dir in workspace_dirs:
                if workspace_dir.exists():
                    # 查找最近生成的文件（基于修改时间）
                    recent_files = []
                    current_time = time.time()
                    
                    for file_path in workspace_dir.glob("*"):
                        if file_path.is_file():
                            # 检查文件是否是最近创建的（1小时内）
                            file_mtime = file_path.stat().st_mtime
                            if current_time - file_mtime < 3600:  # 1小时
                                recent_files.append(file_path)
                    
                    # 复制最近的文件到实验目录
                    for file_path in recent_files:
                        if file_path.suffix in ['.v', '.sv', '.vcd', '.txt', '.md']:
                            # 根据文件类型决定目标目录
                            if 'tb' in file_path.name or 'testbench' in file_path.name:
                                target_dir = self.output_dir / "testbenches"
                            else:
                                target_dir = self.output_dir / "designs"
                            
                            target_path = target_dir / file_path.name
                            
                            try:
                                import shutil
                                shutil.copy2(file_path, target_path)
                                copied_files.append(target_path)
                                print(f"   📄 复制文件: {file_path.name} -> {target_dir.name}/")
                            except Exception as e:
                                print(f"   ⚠️ 文件复制失败 {file_path.name}: {str(e)}")
            
            if copied_files:
                print(f"   ✅ 成功整理 {len(copied_files)} 个文件")
                
                # 更新实验状态
                self.experiment_state["generated_files"] = [str(f) for f in copied_files]
            else:
                print(f"   ℹ️ 未发现需要整理的文件")
                
        except Exception as e:
            print(f"   ⚠️ 文件整理失败: {str(e)}")
    
    def display_experiment_summary(self, analysis: Dict[str, Any], total_duration: float):
        """显示实验摘要"""
        print(f"\n" + "=" * 80)
        print(f"🎯 LLM协调智能体实验完成")
        print("=" * 80)
        
        print(f"📊 实验信息:")
        print(f"   ID: {analysis['experiment_id']}")
        print(f"   类型: {analysis['design_type']}")
        print(f"   状态: {'✅ 成功' if analysis['success'] else '❌ 失败'}")
        print(f"   总耗时: {total_duration:.1f}秒")
        print(f"   任务耗时: {analysis['task_duration']:.1f}秒")
        
        if analysis.get('success'):
            print(f"\n🎉 执行成功:")
            print(f"   迭代次数: {analysis.get('total_iterations', 0)}")
            print(f"   参与智能体: {analysis.get('agent_count', 0)} 个")
            print(f"   生成文件: {len(self.experiment_state.get('generated_files', []))} 个")
            
            # 显示生成的文件
            generated_files = self.experiment_state.get('generated_files', [])
            if generated_files:
                print(f"\n📁 生成的文件:")
                for file_path in generated_files:
                    file_name = Path(file_path).name
                    print(f"   📄 {file_name}")
        else:
            print(f"\n💥 执行失败:")
            print(f"   错误: {analysis.get('error_message', '未知错误')}")
        
        print(f"\n📂 实验目录: {self.output_dir}")
        print("=" * 80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强的LLM协调智能体测试入口')
    
    parser.add_argument('--design', default='4bit_adder', 
                       help='设计类型 (4bit_adder, 8bit_counter, alu_simple, custom)')
    parser.add_argument('--config', default='standard', 
                       help='配置档案 (fast, standard, thorough)')
    parser.add_argument('--iterations', type=int, 
                       help='最大迭代次数 (覆盖配置档案设置)')
    parser.add_argument('--requirements', 
                       help='自定义设计需求 (用于custom设计类型)')
    parser.add_argument('--output-dir', 
                       help='自定义输出目录')
    parser.add_argument('--external-testbench', 
                       help='外部testbench文件路径(.v文件)')
    
    args = parser.parse_args()
    
    # 创建实验实例
    experiment = EnhancedLLMCoordinatorTest(
        design_type=args.design,
        config_profile=args.config,
        custom_requirements=args.requirements,
        output_dir=args.output_dir,
        max_iterations=args.iterations,
        external_testbench_path=args.external_testbench
    )
    
    try:
        # 运行实验
        result = await experiment.run_experiment()
        
        # 返回结果
        if result["success"]:
            print("\n🎉 实验成功完成！")
            return 0
        else:
            print(f"\n💥 实验失败: {result.get('error', '未知错误')}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️ 实验被用户中断")
        return 2
    except Exception as e:
        print(f"\n💥 实验执行异常: {str(e)}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)