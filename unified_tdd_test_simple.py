#!/usr/bin/env python3
"""
统一测试驱动开发(TDD)入口 - 简化版本
==================================================

这个脚本提供了一个完整、易用的TDD测试入口，支持多轮对话功能。
"""

import asyncio
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from extensions import create_test_driven_coordinator, TestDrivenConfig


class UnifiedTDDTest:
    """统一的测试驱动开发测试入口"""
    
    # 预定义的设计模板
    DESIGN_TEMPLATES = {
        "alu": {
            "description": """
设计一个32位算术逻辑单元(ALU)，支持以下操作：

**操作码定义（必须严格按照以下映射）**：
- 4'b0000: 加法(ADD) - result = a + b
- 4'b0001: 减法(SUB) - result = a - b  
- 4'b0010: 逻辑与(AND) - result = a & b
- 4'b0011: 逻辑或(OR) - result = a | b
- 4'b0100: 异或(XOR) - result = a ^ b
- 4'b0101: 逻辑左移(SLL) - result = a << b[4:0]
- 4'b0110: 逻辑右移(SRL) - result = a >> b[4:0]
- 其他操作码: result = 32'h00000000

**模块接口（必须完全匹配）**：
```verilog
module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);
```

**功能要求**：
1. 实现所有7种基本运算（ADD, SUB, AND, OR, XOR, SLL, SRL）
2. 移位操作使用b的低5位作为移位量
3. zero信号在result为0时输出1，否则输出0
4. 使用组合逻辑实现，无时钟和复位信号
5. 对于无效操作码，输出全0结果

**严格警告**：
- 模块名必须是alu_32bit
- 端口名和位宽必须完全匹配
- 操作码映射必须严格按照上述定义
- 移位操作必须使用b[4:0]作为移位量
            """,
            "complexity": "standard"
        },
        
        "simple_adder": {
            "description": """
设计一个简单的8位加法器，支持基本的二进制加法运算。

模块接口：
```verilog
module simple_8bit_adder (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);
```

功能要求：
1. 实现8位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 支持所有可能的输入组合（0到255）
4. 处理进位传播

设计提示：
- 可以使用简单的行波进位链
- 确保所有边界条件正确处理
- 代码要简洁清晰，易于理解
            """,
            "complexity": "simple"
        }
    }
    
    # 预定义的实验配置
    EXPERIMENT_CONFIGS = {
        "quick": {"max_iterations": 3, "timeout_per_iteration": 120, "deep_analysis": False},
        "standard": {"max_iterations": 2, "timeout_per_iteration": 300, "deep_analysis": True},
        "thorough": {"max_iterations": 8, "timeout_per_iteration": 600, "deep_analysis": True},
        "debug": {"max_iterations": 10, "timeout_per_iteration": 900, "deep_analysis": True}
    }
    
    def __init__(self, design_type: str = "alu", 
                 config_profile: str = "standard",
                 custom_config: Dict[str, Any] = None,
                 testbench_path: str = None,
                 custom_requirements: str = None,
                 output_dir: str = None):
        """初始化统一TDD测试"""
        self.design_type = design_type
        self.config_profile = config_profile
        self.testbench_path = testbench_path
        self.custom_requirements = custom_requirements
        
        # 实验配置
        base_config = self.EXPERIMENT_CONFIGS.get(config_profile, self.EXPERIMENT_CONFIGS["standard"])
        if custom_config:
            base_config.update(custom_config)
        self.experiment_config = base_config
        
        # 生成实验ID和输出目录
        self.experiment_id = f"unified_tdd_{design_type}_{int(time.time())}"
        
        # 创建专用输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = project_root / "tdd_experiments" / self.experiment_id
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[TDD] 统一TDD测试初始化")
        print(f"   设计类型: {design_type}")
        print(f"   配置档案: {config_profile}")
        print(f"   实验ID: {self.experiment_id}")
        print(f"   输出目录: {self.output_dir}")
    
    def get_design_requirements(self) -> str:
        """获取设计需求"""
        if self.custom_requirements:
            return self.custom_requirements
        
        template = self.DESIGN_TEMPLATES.get(self.design_type)
        if not template:
            raise ValueError(f"未知的设计类型: {self.design_type}")
        
        return template["description"]
    
    async def setup_framework(self):
        """设置框架和智能体"""
        try:
            print("设置框架和智能体...")
            
            # 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            artifacts_dir = self.output_dir / "artifacts"
            logs_dir = self.output_dir / "logs"
            artifacts_dir.mkdir(exist_ok=True)
            logs_dir.mkdir(exist_ok=True)
            
            # 设置实验管理器
            from core.experiment_manager import ExperimentManager
            exp_manager = ExperimentManager(base_workspace=Path("tdd_experiments"))
            
            # 直接设置当前实验为已存在的目录
            experiment_name = self.output_dir.name
            exp_manager.current_experiment = experiment_name
            exp_manager.current_experiment_path = self.output_dir
            
            # 确保实验目录结构存在
            subdirs = ["designs", "testbenches", "outputs", "logs", "artifacts", "dependencies"]
            for subdir in subdirs:
                (self.output_dir / subdir).mkdir(exist_ok=True)
            
            # 创建实验元数据
            metadata_file = self.output_dir / "experiment_metadata.json"
            if not metadata_file.exists():
                import json
                from datetime import datetime
                metadata = {
                    "experiment_name": experiment_name,
                    "description": f"统一TDD实验: {self.design_type} 设计",
                    "created_at": datetime.now().isoformat(),
                    "status": "active",
                    "iterations": 0,
                    "files_created": 0,
                    "last_updated": datetime.now().isoformat()
                }
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            exp_path = self.output_dir
            
            # 初始化文件管理器
            from core.file_manager import initialize_file_manager
            self.file_manager = initialize_file_manager(workspace_root=artifacts_dir)
            
            # 设置全局实验管理器实例
            import core.experiment_manager as exp_module
            exp_module._experiment_manager = exp_manager
            
            # 验证实验管理器设置
            print(f"实验管理器设置完成:")
            print(f"   - 基础路径: {exp_manager.base_workspace}")
            print(f"   - 当前实验: {exp_manager.current_experiment}")
            print(f"   - 实验路径: {exp_manager.current_experiment_path}")
            print(f"   - 创建路径: {exp_path}")
            
            # 确保实验目录存在
            if exp_path.exists():
                print(f"[OK] 实验目录创建成功: {exp_path}")
            else:
                print(f"[ERROR] 实验目录创建失败: {exp_path}")
            
            # 从环境变量创建配置
            self.config = FrameworkConfig.from_env()
            
            # 如果API密钥没有设置，手动设置
            if not self.config.llm.api_key:
                self.config.llm.api_key = "sk-66ed80a639194920a3840f7013960171"
                print("API密钥已手动设置")
            
            # 创建智能体
            self.verilog_agent = EnhancedRealVerilogAgent(self.config)
            self.review_agent = EnhancedRealCodeReviewAgent(self.config)
            
            # 确保智能体知道实验路径
            print(f"智能体实验路径设置:")
            print(f"   - Verilog Agent ID: {self.verilog_agent.agent_id}")
            print(f"   - Review Agent ID: {self.review_agent.agent_id}")
            print(f"   - 实验路径: {exp_manager.current_experiment_path}")
            
            # 创建基础协调器
            from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
            base_coordinator = EnhancedCentralizedCoordinator(self.config)
            base_coordinator.register_agent(self.verilog_agent)
            base_coordinator.register_agent(self.review_agent)
            
            # 创建测试驱动协调器 - 启用多轮对话
            self.coordinator = create_test_driven_coordinator(
                base_coordinator=base_coordinator,
                config=TestDrivenConfig(
                    max_iterations=self.experiment_config.get('max_iterations', 5),
                    timeout_per_iteration=self.experiment_config.get('timeout_per_iteration', 300),
                    enable_deep_analysis=True,
                    auto_fix_suggestions=True,
                    save_iteration_logs=True,
                    enable_persistent_conversation=True,  # 启用持续对话
                    max_conversation_history=50
                )
            )
            
            print("框架设置完成")
            
        except Exception as e:
            print(f"[ERROR] 框架设置失败: {str(e)}")
            raise
    
    async def run_experiment(self) -> Dict[str, Any]:
        """运行完整的TDD实验"""
        experiment_start_time = time.time()
        
        print("=" * 80)
        print(f"[START] 开始统一TDD实验: {self.design_type.upper()}")
        print("=" * 80)
        
        try:
            # 1. 设置框架
            await self.setup_framework()
            
            # 2. 获取设计需求
            design_requirements = self.get_design_requirements()
            
            print(f"设计需求已准备")
            print(f"配置: {self.config_profile} ({self.experiment_config})")
            
            # 3. 执行测试驱动任务
            print(f"启动测试驱动开发循环...")
            print(f"   最大迭代次数: {self.experiment_config.get('max_iterations', 2)}")
            print(f"   每次迭代超时: {self.experiment_config.get('timeout_per_iteration', 300)}秒")
            print(f"   持续对话模式: 已启用")
            
            result = await self.coordinator.execute_test_driven_task(
                task_description=design_requirements,
                testbench_path=self.testbench_path
            )
            
            # 4. 分析结果
            experiment_duration = time.time() - experiment_start_time
            analysis = await self._analyze_experiment_result(result, experiment_duration)
            
            # 5. 保存实验报告
            await self._save_experiment_report(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"[ERROR] 实验执行异常: {str(e)}")
            error_result = {
                "success": False,
                "error": str(e),
                "experiment_id": self.experiment_id,
                "duration": time.time() - experiment_start_time
            }
            await self._save_experiment_report(error_result)
            return error_result
    
    async def _analyze_experiment_result(self, result: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """分析实验结果"""
        print("=" * 80)
        print("实验结果分析")
        print("=" * 80)
        
        analysis = {
            "experiment_id": self.experiment_id,
            "design_type": self.design_type,
            "config_profile": self.config_profile,
            "success": result.get("success", False),
            "total_duration": duration,
            "timestamp": time.time(),
            "detailed_result": result
        }
        
        if result.get("success"):
            print("实验成功完成！")
            
            iterations = result.get("total_iterations", 0)
            final_design = result.get("final_design", [])
            
            print(f"   总迭代次数: {iterations}")
            print(f"   总耗时: {duration:.2f} 秒")
            print(f"   最终设计文件: {len(final_design)} 个")
            
            # 分析对话历史
            conversation_history = result.get("conversation_history", [])
            if conversation_history:
                print(f"   对话历史长度: {len(conversation_history)} 轮")
                user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
                assistant_messages = [msg for msg in conversation_history if msg.get('role') == 'assistant']
                print(f"   - 用户消息: {len(user_messages)} 轮")
                print(f"   - AI响应: {len(assistant_messages)} 轮")
            
            analysis["summary"] = {
                "iterations_used": iterations,
                "efficiency": f"成功率: 100%",
                "files_generated": len(final_design),
                "completion_reason": result.get("completion_reason", "tests_passed"),
                "average_iteration_time": duration / max(iterations, 1),
                "conversation_rounds": len(conversation_history)
            }
            
            # 显示设计文件信息
            if final_design:
                print(f"生成的设计文件:")
                for i, file_info in enumerate(final_design, 1):
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path', str(file_info))
                    else:
                        file_path = str(file_info)
                    print(f"   {i}. {Path(file_path).name}")
            
        else:
            print("实验未能完成")
            
            iterations = result.get("total_iterations", 0)
            error = result.get("error", "未知错误")
            
            print(f"   已用迭代次数: {iterations}")
            print(f"   总耗时: {duration:.2f} 秒")
            print(f"   失败原因: {error}")
            
            analysis["summary"] = {
                "iterations_used": iterations,
                "completion_reason": result.get("completion_reason", "failed"),
                "error": error,
                "partial_progress": iterations > 0
            }
            
            # 分析部分结果
            partial_results = result.get("partial_results", [])
            if partial_results:
                print(f"迭代历史分析:")
                for i, iteration in enumerate(partial_results, 1):
                    iter_result = iteration.get("result", {})
                    success = iter_result.get("all_tests_passed", False)
                    print(f"   第{i}次迭代: {'通过' if success else '失败'}")
        
        print("=" * 80)
        
        return analysis
    
    async def _save_experiment_report(self, analysis: Dict[str, Any]):
        """保存实验报告到专用目录"""
        # 保存详细的实验报告
        report_path = self.output_dir / "experiment_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存简化的结果摘要
        summary_path = self.output_dir / "experiment_summary.txt"
        await self._save_text_summary(analysis, summary_path)
        
        print(f"实验报告已保存到: {self.output_dir}")
        print(f"   详细报告: {report_path.name}")
        print(f"   结果摘要: {summary_path.name}")
    
    async def _save_text_summary(self, analysis: Dict[str, Any], summary_path: Path):
        """保存人类可读的文本摘要"""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("TDD实验结果摘要\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"实验ID: {analysis['experiment_id']}\n")
            f.write(f"设计类型: {analysis['design_type']}\n")
            f.write(f"配置档案: {analysis['config_profile']}\n")
            f.write(f"实验状态: {'成功' if analysis['success'] else '失败'}\n")
            f.write(f"总耗时: {analysis['total_duration']:.2f} 秒\n")
            f.write(f"时间戳: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analysis['timestamp']))}\n\n")
            
            if analysis.get('success'):
                summary = analysis.get('summary', {})
                f.write("成功统计:\n")
                f.write(f"- 迭代次数: {summary.get('iterations_used', 0)}\n")
                f.write(f"- 生成文件: {summary.get('files_generated', 0)} 个\n")
                f.write(f"- 完成原因: {summary.get('completion_reason', 'tests_passed')}\n")
                f.write(f"- 平均迭代时间: {summary.get('average_iteration_time', 0):.2f} 秒\n")
                f.write(f"- 对话轮数: {summary.get('conversation_rounds', 0)}\n\n")
                
                # 测试结果
                test_results = analysis.get('detailed_result', {}).get('test_results', {})
                if test_results:
                    f.write("测试结果:\n")
                    f.write(f"- 测试状态: {'通过' if test_results.get('all_tests_passed') else '失败'}\n")
                    f.write(f"- 测试阶段: {test_results.get('stage', 'unknown')}\n")
                    f.write(f"- 返回码: {test_results.get('return_code', -1)}\n")
                    if test_results.get('test_summary'):
                        f.write(f"- 测试摘要: {test_results['test_summary']}\n")
            else:
                f.write("失败信息:\n")
                error = analysis.get('error', '未知错误')
                f.write(f"- 错误: {error}\n")


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='统一测试驱动开发(TDD)测试入口 - 简化版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用预定义的ALU模板，标准配置
  python unified_tdd_test_simple.py --design alu
  
  # 使用简单加法器模板，快速测试
  python unified_tdd_test_simple.py --design simple_adder --config quick
  
  # 调试模式，更多迭代次数
  python unified_tdd_test_simple.py --design alu --config debug --iterations 12
        """
    )
    
    parser.add_argument('--design', '-d', 
                       choices=['alu', 'simple_adder'],
                       default='simple_adder',
                       help='设计类型 (默认: simple_adder)')
    
    parser.add_argument('--config', '-c',
                       choices=['quick', 'standard', 'thorough', 'debug'],
                       default='standard',
                       help='配置档案 (默认: standard)')
    
    parser.add_argument('--testbench', '-t',
                       help='测试台文件路径')
    
    parser.add_argument('--requirements', '-r',
                       help='自定义设计需求文本')
    
    parser.add_argument('--iterations', '-i',
                       type=int,
                       help='最大迭代次数 (覆盖配置档案)')
    
    parser.add_argument('--timeout',
                       type=int,
                       help='每次迭代超时秒数 (覆盖配置档案)')
    
    parser.add_argument('--no-deep-analysis',
                       action='store_true',
                       help='禁用深度分析')
    
    parser.add_argument('--output-dir', '-o',
                       help='实验输出目录路径 (默认: tdd_experiments/实验ID)')
    
    return parser


async def main():
    """主程序入口"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("统一测试驱动开发(TDD)测试入口 - 简化版本")
    print("=" * 50)
    
    # 构建自定义配置
    custom_config = {}
    if args.iterations:
        custom_config['max_iterations'] = args.iterations
    if args.timeout:
        custom_config['timeout_per_iteration'] = args.timeout
    if args.no_deep_analysis:
        custom_config['deep_analysis'] = False
    
    # 创建并运行实验
    experiment = UnifiedTDDTest(
        design_type=args.design,
        config_profile=args.config,
        custom_config=custom_config if custom_config else None,
        testbench_path=args.testbench,
        custom_requirements=args.requirements,
        output_dir=args.output_dir
    )
    
    try:
        result = await experiment.run_experiment()
        
        # 显示最终结果
        print(f"实验完成")
        if result["success"]:
            print("设计成功完成并通过所有测试！")
            print("测试驱动开发功能验证成功")
            print("多轮对话功能工作正常")
        else:
            print("设计未能通过所有测试")
            print("可以查看日志分析迭代改进过程")
            print(f"实验报告: {experiment.output_dir}/experiment_report.json")
        
        return result["success"]
        
    except Exception as e:
        print(f"实验执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 