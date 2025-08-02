#!/usr/bin/env python3
"""
🧪 统一测试驱动开发(TDD)入口
==================================================

这个脚本提供了一个完整、易用的TDD测试入口，支持：
✅ 多轮迭代结果完整保存
✅ 配置化的实验参数
✅ 详细的进度跟踪和结果分析
✅ 通用的测试台模板支持

使用方法:
    python unified_tdd_test.py --design alu --iterations 5
    python unified_tdd_test.py --design counter --testbench /path/to/tb.v
    python unified_tdd_test.py --design custom --requirements "设计需求文本"
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
- 算术运算：加法(ADD)、减法(SUB)
- 逻辑运算：与(AND)、或(OR)、异或(XOR)、非(NOT)
- 比较运算：等于(EQ)、小于(LT)、大于(GT)

模块接口：
```verilog
module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero,     // 零标志
    output        overflow  // 溢出标志
);
```
            """,
            "testbench": "test_cases/alu_testbench.v",
            "complexity": "standard"
        },
        
        "counter": {
            "description": """
设计一个8位计数器模块counter_8bit，严格按照以下接口规范实现：

**关键要求 - 接口必须完全匹配**:
```verilog
module counter_8bit (
    input        clk,       // 时钟
    input        rst_n,     // 异步复位（低电平有效） - 注意是rst_n不是rst！
    input        enable,    // 计数使能
    input        up_down,   // 计数方向(1:上计数, 0:下计数)
    output [7:0] count,     // 计数值
    output       overflow   // 溢出标志
);
```

**功能要求**:
- 异步复位：当rst_n为低电平时，count=0, overflow=0
- 同步计数：在时钟上升沿进行计数
- 使能控制：enable为高时计数，为低时保持
- 双向计数：up_down=1上计数，up_down=0下计数
- 溢出检测：上计数255→0时overflow=1，下计数0→255时overflow=1

**警告**：
1. 端口名必须是rst_n，不能是rst！
2. 复位逻辑必须是negedge rst_n，不能是negedge rst！
3. 复位条件必须是if (!rst_n)，不能是if (!rst)！
            """,
            "testbench": None,  # 需要用户提供或生成
            "complexity": "simple"
        },
        
        "adder_16bit": {
            "description": """
设计一个16位加法器模块adder_16bit，严格按照以下接口规范实现：

**关键要求 - 接口必须完全匹配**:
```verilog
module adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数
    input         cin,      // 输入进位
    output [15:0] sum,      // 16位和输出
    output        cout,     // 输出进位
    output        overflow  // 溢出标志（有符号运算）
);
```

**功能要求**:
1. **加法运算**: 实现16位二进制加法 sum = a + b + cin
2. **进位处理**: 正确计算输出进位 cout
3. **溢出检测**: 检测有符号数溢出（当两个同号数相加结果变号时）
4. **全组合覆盖**: 支持所有可能的16位输入组合
5. **边界处理**: 正确处理最大值(0xFFFF)和最小值(0x0000)

**设计要求**:
- 使用组合逻辑实现
- 可以采用行波进位或超前进位结构
- 确保时序性能良好
- 代码结构清晰，易于综合

**严格警告**：
1. 模块名必须是adder_16bit，不能是其他名称！
2. 端口名必须完全匹配上述接口规范！
3. 所有端口位宽必须正确：a[15:0], b[15:0], sum[15:0]
4. overflow信号必须正确实现有符号溢出检测
5. 必须是纯组合逻辑，不能有时钟或复位信号

**测试验证要求**:
设计必须通过以下测试：
- 基本加法运算测试
- 进位传播测试  
- 溢出检测测试
- 边界值测试（0x0000, 0xFFFF等）
- 随机数据测试
            """,
            "testbench": None,  # 将创建专门的测试台
            "complexity": "medium"
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

🎯 功能要求：
1. 实现8位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 支持所有可能的输入组合（0到255）
4. 处理进位传播

💡 设计提示：
- 可以使用简单的行波进位链
- 确保所有边界条件正确处理
- 代码要简洁清晰，易于理解
            """,
            "testbench": "test_cases/simple_8bit_adder_tb.v",
            "complexity": "simple"
        },
        
        "adder": {
            "description": """
设计一个16位超前进位加法器（Carry Lookahead Adder），实现高效的并行加法运算。

模块接口：
```verilog
module carry_lookahead_adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数  
    input         cin,      // 输入进位
    output [15:0] sum,      // 16位和
    output        cout      // 输出进位
);
```

🎯 功能要求：
1. 实现16位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 使用超前进位技术提高性能，而不是简单的行波进位
4. 支持所有可能的输入组合

📊 超前进位加法器设计要点：
1. **进位生成 (Generate)**: Gi = Ai & Bi
2. **进位传播 (Propagate)**: Pi = Ai ^ Bi
3. **超前进位计算**: 
   - C1 = G0 + P0×C0
   - C2 = G1 + P1×G0 + P1×P0×C0
   - C3 = G2 + P2×G1 + P2×P1×G0 + P2×P1×P0×C0
   - ...
4. **求和**: Si = Pi ^ Ci
            """,
            "testbench": "test_cases/carry_lookahead_adder_tb.v",
            "complexity": "advanced"
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
        
        print(f"🧪 统一TDD测试初始化")
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
    
    def get_testbench_path(self) -> Optional[str]:
        """获取测试台路径"""
        if self.testbench_path:
            return self.testbench_path
        
        template = self.DESIGN_TEMPLATES.get(self.design_type)
        if template and template.get("testbench"):
            tb_path = project_root / template["testbench"]
            if tb_path.exists():
                return str(tb_path)
        
        return None
    
    async def setup_framework(self):
        """设置TDD框架"""
        print("🏗️ 初始化TDD框架...")
        
        # 1. 创建增强版标准组件
        config = FrameworkConfig.from_env()
        self.coordinator = EnhancedCentralizedCoordinator(config)
        
        # 2. 注册增强版智能体
        self.verilog_agent = EnhancedRealVerilogAgent(config)
        self.reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        self.coordinator.register_agent(self.verilog_agent)
        self.coordinator.register_agent(self.reviewer_agent)
        
        print("   ✅ 增强版协调器和智能体初始化完成")
        
        # 3. 创建测试驱动配置
        tdd_config = TestDrivenConfig(
            max_iterations=self.experiment_config.get("max_iterations", 2),
            enable_deep_analysis=self.experiment_config.get("deep_analysis", True),
            timeout_per_iteration=self.experiment_config.get("timeout_per_iteration", 300),
            save_iteration_logs=True
        )
        
        # 4. 升级为测试驱动协调器
        self.tdd_coordinator = create_test_driven_coordinator(self.coordinator, tdd_config)
        
        print("   ✅ 测试驱动扩展启用成功")
        
        return True
    
    async def run_experiment(self) -> Dict[str, Any]:
        """运行完整的TDD实验"""
        experiment_start_time = time.time()
        
        print("=" * 80)
        print(f"🚀 开始统一TDD实验: {self.design_type.upper()}")
        print("=" * 80)
        
        try:
            # 1. 设置框架
            await self.setup_framework()
            
            # 2. 获取设计需求和测试台
            design_requirements = self.get_design_requirements()
            testbench_path = self.get_testbench_path()
            
            print(f"📋 设计需求已准备")
            if testbench_path:
                print(f"🎯 测试台: {Path(testbench_path).name}")
            else:
                print("🎯 测试台: 将由AI生成")
            
            print(f"⚙️ 配置: {self.config_profile} ({self.experiment_config})")
            
            # 3. 执行测试驱动任务
            print(f"🔄 启动测试驱动开发循环...")
            print(f"   最大迭代次数: {self.experiment_config.get('max_iterations', 2)}")
            print(f"   每次迭代超时: {self.experiment_config.get('timeout_per_iteration', 300)}秒")
            
            result = await self.tdd_coordinator.execute_test_driven_task(
                task_description=design_requirements,
                testbench_path=testbench_path
            )
            
            # 4. 分析结果
            experiment_duration = time.time() - experiment_start_time
            analysis = await self._analyze_experiment_result(result, experiment_duration)
            
            # 5. 保存实验报告
            await self._save_experiment_report(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ 实验执行异常: {str(e)}")
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
        print("📊 实验结果分析")
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
            print("🎉 实验成功完成！")
            
            iterations = result.get("total_iterations", 0)
            final_design = result.get("final_design", [])
            
            print(f"   📈 总迭代次数: {iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   📁 最终设计文件: {len(final_design)} 个")
            
            analysis["summary"] = {
                "iterations_used": iterations,
                "efficiency": f"成功率: 100%",
                "files_generated": len(final_design),
                "completion_reason": result.get("completion_reason", "tests_passed"),
                "average_iteration_time": duration / max(iterations, 1)
            }
            
            # 显示设计文件信息
            if final_design:
                print(f"📄 生成的设计文件:")
                for i, file_info in enumerate(final_design, 1):
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path', str(file_info))
                    else:
                        file_path = str(file_info)
                    print(f"   {i}. {Path(file_path).name}")
            
        else:
            print("❌ 实验未能完成")
            
            iterations = result.get("total_iterations", 0)
            error = result.get("error", "未知错误")
            
            print(f"   📈 已用迭代次数: {iterations}")
            print(f"   ⏱️ 总耗时: {duration:.2f} 秒")
            print(f"   ❌ 失败原因: {error}")
            
            analysis["summary"] = {
                "iterations_used": iterations,
                "completion_reason": result.get("completion_reason", "failed"),
                "error": error,
                "partial_progress": iterations > 0
            }
            
            # 分析部分结果
            partial_results = result.get("partial_results", [])
            if partial_results:
                print(f"🔍 迭代历史分析:")
                for i, iteration in enumerate(partial_results, 1):
                    iter_result = iteration.get("result", {})
                    success = iter_result.get("all_tests_passed", False)
                    print(f"   第{i}次迭代: {'✅ 通过' if success else '❌ 失败'}")
        
        # 显示会话信息
        session_id = result.get("session_id")
        if session_id:
            session_info = self.tdd_coordinator.get_session_info(session_id)
            if session_info:
                print(f"📋 会话详情:")
                print(f"   会话ID: {session_id}")
                print(f"   状态: {session_info.get('status', 'unknown')}")
        
        print("=" * 80)
        
        # 复制关键文件到输出目录
        await self._copy_experiment_files(result)
        
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
        
        print(f"💾 实验报告已保存到: {self.output_dir}")
        print(f"   📄 详细报告: {report_path.name}")
        print(f"   📋 结果摘要: {summary_path.name}")
    
    async def _save_text_summary(self, analysis: Dict[str, Any], summary_path: Path):
        """保存人类可读的文本摘要"""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("🧪 TDD实验结果摘要\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"实验ID: {analysis['experiment_id']}\n")
            f.write(f"设计类型: {analysis['design_type']}\n")
            f.write(f"配置档案: {analysis['config_profile']}\n")
            f.write(f"实验状态: {'✅ 成功' if analysis['success'] else '❌ 失败'}\n")
            f.write(f"总耗时: {analysis['total_duration']:.2f} 秒\n")
            f.write(f"时间戳: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analysis['timestamp']))}\n\n")
            
            if analysis.get('success'):
                summary = analysis.get('summary', {})
                f.write("📊 成功统计:\n")
                f.write(f"- 迭代次数: {summary.get('iterations_used', 0)}\n")
                f.write(f"- 生成文件: {summary.get('files_generated', 0)} 个\n")
                f.write(f"- 完成原因: {summary.get('completion_reason', 'tests_passed')}\n")
                f.write(f"- 平均迭代时间: {summary.get('average_iteration_time', 0):.2f} 秒\n\n")
                
                # 测试结果
                test_results = analysis.get('detailed_result', {}).get('test_results', {})
                if test_results:
                    f.write("🧪 测试结果:\n")
                    f.write(f"- 测试状态: {'✅ 通过' if test_results.get('all_tests_passed') else '❌ 失败'}\n")
                    f.write(f"- 测试阶段: {test_results.get('stage', 'unknown')}\n")
                    f.write(f"- 返回码: {test_results.get('return_code', -1)}\n")
                    if test_results.get('test_summary'):
                        f.write(f"- 测试摘要: {test_results['test_summary']}\n")
            else:
                f.write("❌ 失败信息:\n")
                error = analysis.get('error', '未知错误')
                f.write(f"- 错误: {error}\n")
    
    async def _copy_experiment_files(self, result: Dict[str, Any]):
        """复制实验生成的文件到输出目录"""
        try:
            # 创建子目录
            artifacts_dir = self.output_dir / "artifacts"
            logs_dir = self.output_dir / "logs"
            artifacts_dir.mkdir(exist_ok=True)
            logs_dir.mkdir(exist_ok=True)
            
            # 复制设计文件
            final_design = result.get('final_design', [])
            for file_ref in final_design:
                if isinstance(file_ref, str):
                    # 从字符串中提取文件路径
                    if "file_path='" in file_ref:
                        start = file_ref.find("file_path='") + len("file_path='")
                        end = file_ref.find("'", start)
                        file_path = file_ref[start:end]
                    else:
                        file_path = file_ref
                else:
                    file_path = str(file_ref)
                
                source_path = Path(file_path)
                if source_path.exists():
                    dest_path = artifacts_dir / source_path.name
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    print(f"   📁 复制文件: {source_path.name}")
            
            # 复制测试结果中的设计文件
            test_results = result.get('test_results', {})
            design_files = test_results.get('design_files', [])
            for file_path in design_files:
                source_path = Path(file_path)
                if source_path.exists():
                    dest_path = artifacts_dir / source_path.name
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    print(f"   📁 复制设计文件: {source_path.name}")
            
            # 保存仿真输出
            if test_results.get('simulation_stdout'):
                sim_output_path = logs_dir / "simulation_output.log"
                with open(sim_output_path, 'w', encoding='utf-8') as f:
                    f.write(test_results['simulation_stdout'])
                print(f"   📝 保存仿真输出: {sim_output_path.name}")
            
            # 保存编译输出
            if test_results.get('compile_stdout'):
                compile_output_path = logs_dir / "compile_output.log"
                with open(compile_output_path, 'w', encoding='utf-8') as f:
                    f.write(test_results['compile_stdout'])
                print(f"   📝 保存编译输出: {compile_output_path.name}")
                
        except Exception as e:
            print(f"⚠️ 复制文件时出现警告: {str(e)}")


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='统一测试驱动开发(TDD)测试入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用预定义的ALU模板，标准配置
  python unified_tdd_test.py --design alu
  
  # 使用超前进位加法器模板，快速测试
  python unified_tdd_test.py --design adder --config quick
  
  # 自定义设计需求
  python unified_tdd_test.py --design custom --requirements "设计一个UART模块" --testbench uart_tb.v
  
  # 调试模式，更多迭代次数
  python unified_tdd_test.py --design alu --config debug --iterations 12
        """
    )
    
    parser.add_argument('--design', '-d', 
                       choices=['alu', 'counter', 'adder_16bit', 'simple_adder', 'adder', 'custom'],
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
    
    print("🧪 统一测试驱动开发(TDD)测试入口")
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
        print(f"🏁 实验完成")
        if result["success"]:
            print("✅ 设计成功完成并通过所有测试！")
            print("🎯 测试驱动开发功能验证成功")
        else:
            print("❌ 设计未能通过所有测试")
            print("🔍 可以查看日志分析迭代改进过程")
            print(f"📊 实验报告: unified_tdd_report_{experiment.experiment_id}.json")
        
        return result["success"]
        
    except Exception as e:
        print(f"💥 实验执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)