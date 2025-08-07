#!/usr/bin/env python3
"""
统一测试驱动开发(TDD)入口
==================================================

这个脚本提供了一个完整、易用的TDD测试入口，支持：
- 多轮迭代结果完整保存
- 配置化的实验参数
- 详细的进度跟踪和结果分析
- 通用的测试台模板支持
- 动态上下文传递机制

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
import os
import codecs
import locale
from pathlib import Path
from typing import Dict, Any, Optional, List

# 设置编码环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 检测操作系统并设置适当的编码
def setup_encoding():
    """设置适当的编码以处理不同操作系统的输出"""
    if os.name == 'nt':  # Windows
        # Windows系统特殊处理
        try:
            # 尝试设置控制台代码页为UTF-8
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 对于Python 3.7+，使用reconfigure
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        else:
            # 对于较老的Python版本，使用codecs包装
            try:
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            except:
                pass
    else:
        # Unix/Linux系统
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
            "testbench": "/home/haiyan/Research/CentralizedAgentFramework/test_cases/alu_testbench.v",
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
            "testbench": "/home/haiyan/Research/CentralizedAgentFramework/tdd_experiments/unified_tdd_adder_16bit_1754187911/testbenches/testbench_adder_16bit.v",  # 将创建专门的测试台
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
            "testbench": None,
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

功能要求：
1. 实现16位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 使用超前进位技术提高性能，而不是简单的行波进位
4. 支持所有可能的输入组合

超前进位加法器设计要点：
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
        "quick": {"max_iterations": 5, "timeout_per_iteration": 120, "deep_analysis": False},
        "standard": {"max_iterations": 10, "timeout_per_iteration": 300, "deep_analysis": True},
        "thorough": {"max_iterations": 20, "timeout_per_iteration": 600, "deep_analysis": True},
        "debug": {"max_iterations": 30, "timeout_per_iteration": 900, "deep_analysis": True}
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
        self.custom_config = custom_config  # 保存自定义配置
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
        
        # 初始化上下文状态管理
        self.context_state = {
            "generated_files": [],
            "current_design": None,
            "file_mapping": {},
            "iteration_history": [],
            "session_info": {}
        }
        
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
    
    def update_context_state(self, file_info: Dict[str, Any]):
        """更新上下文状态，记录生成的文件信息"""
        self.context_state["generated_files"].append(file_info)
        
        # 更新文件映射
        if "filename" in file_info:
            self.context_state["file_mapping"][file_info["filename"]] = file_info
        
        # 如果是设计文件，更新当前设计
        if file_info.get("file_type") == "verilog" and "design" in file_info.get("description", "").lower():
            self.context_state["current_design"] = file_info
        
        print(f"[CONTEXT] 更新上下文状态: {file_info.get('filename', 'unknown')}")
    
    def get_design_files_context(self) -> str:
        """获取设计文件的上下文信息，用于传递给测试阶段"""
        design_files = [f for f in self.context_state["generated_files"] 
                       if f.get("file_type") == "verilog" and "design" in f.get("description", "").lower()]
        
        if not design_files:
            return "设计文件: 无（需要先生成设计文件）"
        
        context_lines = ["设计文件:"]
        for file_info in design_files:
            filename = file_info.get("filename", "unknown")
            filepath = file_info.get("filepath", "unknown")
            description = file_info.get("description", "")
            
            context_lines.append(f"  - 文件名: {filename}")
            context_lines.append(f"  - 路径: {filepath}")
            if description:
                context_lines.append(f"  - 描述: {description}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def create_dynamic_task_description(self, base_description: str, stage: str = "design") -> str:
        """创建动态任务描述，根据当前上下文状态"""
        if stage == "design":
            # 设计阶段：强制生成代码文件
            return f"""
🎨 强制设计阶段

{base_description}

强制要求：
1. 必须使用 generate_verilog_code 工具生成完整的Verilog代码
2. 必须保存代码文件到实验目录
3. 必须确保代码符合所有需求规范
4. 必须生成可编译的代码文件
5. 不要只分析需求，必须实际生成代码

请立即执行代码生成，不要跳过此步骤。
"""
        elif stage == "test":
            # 测试阶段：添加文件上下文信息
            design_context = self.get_design_files_context()
            return f"""
🧪 测试生成和验证阶段

请为以下设计生成测试台并进行验证：

{design_context}

测试要求：
1. 生成全面的测试台文件
2. 包含边界条件测试
3. 验证所有功能点
4. 运行仿真验证
5. 提供详细的测试报告

请生成测试台并执行完整的测试验证流程。
"""
        else:
            return base_description
    
    def update_context_state(self, file_info: Dict[str, Any]):
        """更新上下文状态，记录生成的文件信息"""
        self.context_state["generated_files"].append(file_info)
        
        # 更新文件映射
        if "filename" in file_info:
            self.context_state["file_mapping"][file_info["filename"]] = file_info
        
        # 如果是设计文件，更新当前设计
        if file_info.get("file_type") == "verilog" and "design" in file_info.get("description", "").lower():
            self.context_state["current_design"] = file_info
        
        print(f"[CONTEXT] 更新上下文状态: {file_info.get('filename', 'unknown')}")
    
    def get_design_files_context(self) -> str:
        """获取设计文件的上下文信息，用于传递给测试阶段"""
        design_files = [f for f in self.context_state["generated_files"] 
                       if f.get("file_type") == "verilog" and "design" in f.get("description", "").lower()]
        
        if not design_files:
            return "设计文件: 无（需要先生成设计文件）"
        
        context_lines = ["设计文件:"]
        for file_info in design_files:
            filename = file_info.get("filename", "unknown")
            filepath = file_info.get("filepath", "unknown")
            description = file_info.get("description", "")
            
            context_lines.append(f"  - 文件名: {filename}")
            context_lines.append(f"  - 路径: {filepath}")
            if description:
                context_lines.append(f"  - 描述: {description}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
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
            
            # 设置实验管理器 - 使用已创建的实验目录
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
            
            # 创建实验元数据（如果不存在）
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
            
            # 优化：初始化文件管理器时直接设置目标路径
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
            
            # 创建测试驱动协调器
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
            
            # 2. 获取设计需求和测试台
            design_requirements = self.get_design_requirements()
            testbench_path = self.get_testbench_path()
            
            print(f"设计需求已准备")
            if testbench_path:
                print(f"测试台: {Path(testbench_path).name}")
                # 复制测试台文件到实验目录
                from core.experiment_manager import get_experiment_manager
                exp_manager = get_experiment_manager()
                if exp_manager.current_experiment_path:
                    copied_path = exp_manager.copy_dependency(
                        testbench_path, 
                        f"用户提供的{self.design_type}测试台文件"
                    )
                    if copied_path:
                        print(f"测试台已复制到: {copied_path.name}")
                    else:
                        print(f"[WARNING] 测试台复制失败")
            else:
                print("测试台: 将由AI生成")
            
            print(f"配置: {self.config_profile} ({self.experiment_config})")
            
            # 3. 验证实验配置
            print("🔍 验证实验配置...")
            self._validate_experiment_config()
            print("✅ 实验配置验证完成")
            
            # 4. 执行测试驱动任务 - 使用强制TDD流程
            print(f"启动测试驱动开发循环...")
            print(f"   最大迭代次数: {self.experiment_config.get('max_iterations', 2)}")
            print(f"   每次迭代超时: {self.experiment_config.get('timeout_per_iteration', 300)}秒")
            print(f"   持续对话模式: 已启用")
            print(f"   强制测试台生成: 已启用")
            print(f"   强制仿真验证: 已启用")
            print(f"   智能参数处理: 已启用")
            
            # 创建增强的任务描述，包含上下文传递机制
            enhanced_task_description = self.create_dynamic_task_description(design_requirements, "design")
            
            # 设置文件监控回调（通过实验管理器）
            from core.experiment_manager import get_experiment_manager
            exp_manager = get_experiment_manager()
            if hasattr(exp_manager, 'set_file_callback'):
                exp_manager.set_file_callback(self.update_context_state)
            
            # 🎯 强制TDD流程执行
            result = await self.coordinator.execute_test_driven_task(
                task_description=enhanced_task_description,
                testbench_path=testbench_path
            )
            
            # 4. 分析结果
            experiment_duration = time.time() - experiment_start_time
            analysis = await self._analyze_experiment_result(result, experiment_duration)
            
            # 5. 保存实验报告
            await self._save_experiment_report(analysis)
            
            # 6. 检查实验目录中的文件
            from core.experiment_manager import get_experiment_manager
            exp_manager = get_experiment_manager()
            if exp_manager.current_experiment_path:
                print(f"\n实验目录检查: {exp_manager.current_experiment_path}")
                if exp_manager.current_experiment_path.exists():
                    for subdir in ["designs", "testbenches", "artifacts", "logs"]:
                        subdir_path = exp_manager.current_experiment_path / subdir
                        if subdir_path.exists():
                            files = list(subdir_path.glob("*"))
                            print(f"   {subdir}: {len(files)} 个文件")
                            for file in files:
                                print(f"      - {file.name}")
                        else:
                            print(f"   {subdir}: 目录不存在")
                else:
                    print(f"   [ERROR] 实验目录不存在: {exp_manager.current_experiment_path}")
            
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
            "detailed_result": result,
            "context_state": self.context_state  # 包含上下文状态信息
        }
        
        if result.get("success"):
            print("实验成功完成！")
            
            iterations = result.get("total_iterations", 0)
            final_design = result.get("final_design", [])
            
            print(f"   总迭代次数: {iterations}")
            print(f"   总耗时: {duration:.2f} 秒")
            print(f"   最终设计文件: {len(final_design)} 个")
            print(f"   上下文文件数: {len(self.context_state['generated_files'])} 个")
            
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
                "context_files": len(self.context_state['generated_files']),
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
            print(f"   上下文文件数: {len(self.context_state['generated_files'])} 个")
            
            analysis["summary"] = {
                "iterations_used": iterations,
                "completion_reason": result.get("completion_reason", "failed"),
                "error": error,
                "partial_progress": iterations > 0,
                "context_files": len(self.context_state['generated_files'])
            }
            
            # 分析部分结果
            partial_results = result.get("partial_results", [])
            if partial_results:
                print(f"迭代历史分析:")
                for i, iteration in enumerate(partial_results, 1):
                    iter_result = iteration.get("result", {})
                    success = iter_result.get("all_tests_passed", False)
                    print(f"   第{i}次迭代: {'通过' if success else '失败'}")
        
        # 显示会话信息
        session_id = result.get("session_id")
        if session_id and hasattr(self, 'coordinator'):
            try:
                session_info = self.coordinator.get_session_info(session_id)
                if session_info:
                    print(f"会话详情:")
                    print(f"   会话ID: {session_id}")
                    print(f"   状态: {session_info.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARNING] 无法获取会话信息: {e}")
        
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
                f.write(f"- 上下文文件: {summary.get('context_files', 0)} 个\n")
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
                f.write(f"- 上下文文件: {analysis.get('summary', {}).get('context_files', 0)} 个\n")
    
    async def _copy_experiment_files(self, result: Dict[str, Any]):
        """复制实验生成的文件到输出目录（优化版本）"""
        try:
            # 创建子目录
            artifacts_dir = self.output_dir / "artifacts"
            logs_dir = self.output_dir / "logs"
            artifacts_dir.mkdir(exist_ok=True)
            logs_dir.mkdir(exist_ok=True)
            
            copied_files = []
            
            # 优化：文件已经直接保存在artifacts_dir，只需要处理日志文件
            print("   文件已直接保存在实验目录，无需复制")
            
            # 1. 复制标准result中的文件引用（如果存在）
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
                if source_path.exists() and source_path.parent != artifacts_dir:
                    # 只有当文件不在artifacts_dir时才复制
                    dest_path = artifacts_dir / source_path.name
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(source_path.name)
                    print(f"   复制外部文件: {source_path.name}")
            
            # 2. 保存仿真输出
            test_results = result.get('test_results', {})
            if test_results.get('simulation_stdout'):
                sim_output_path = logs_dir / "simulation_output.log"
                with open(sim_output_path, 'w', encoding='utf-8') as f:
                    f.write(test_results['simulation_stdout'])
                print(f"   保存仿真输出: {sim_output_path.name}")
            
            # 保存编译输出
            if test_results.get('compile_stdout'):
                compile_output_path = logs_dir / "compile_output.log"
                with open(compile_output_path, 'w', encoding='utf-8') as f:
                    f.write(test_results['compile_stdout'])
                print(f"   保存编译输出: {compile_output_path.name}")
            
            # 保存错误输出
            if test_results.get('simulation_stderr'):
                error_output_path = logs_dir / "simulation_errors.log"
                with open(error_output_path, 'w', encoding='utf-8') as f:
                    f.write(test_results['simulation_stderr'])
                print(f"   保存错误输出: {error_output_path.name}")
            
            # 总结复制结果
            if copied_files:
                print(f"   [OK] 成功复制 {len(copied_files)} 个外部文件到实验目录")
            else:
                print(f"   [OK] 所有文件已直接保存在实验目录中")
                
        except Exception as e:
            print(f"[WARNING] 复制文件时出现警告: {str(e)}")

    def _validate_experiment_config(self):
        """验证实验配置"""
        print("🔍 验证实验配置...")
        
        # 验证设计类型
        if self.design_type not in self.DESIGN_TEMPLATES:
            raise ValueError(f"不支持的设计类型: {self.design_type}")
        
        # 验证配置档案
        if self.config_profile not in self.EXPERIMENT_CONFIGS:
            raise ValueError(f"不支持的配置档案: {self.config_profile}")
        
        # 验证自定义配置
        if hasattr(self, 'custom_config') and self.custom_config:
            for key, value in self.custom_config.items():
                if key == 'max_iterations' and (not isinstance(value, int) or value < 1):
                    raise ValueError(f"max_iterations必须是正整数，当前值: {value}")
                elif key == 'timeout_per_iteration' and (not isinstance(value, int) or value < 30):
                    raise ValueError(f"timeout_per_iteration必须至少30秒，当前值: {value}")
                elif key == 'deep_analysis' and not isinstance(value, bool):
                    raise ValueError(f"deep_analysis必须是布尔值，当前值: {value}")
        
        # 验证测试台路径
        if self.testbench_path and not Path(self.testbench_path).exists():
            print(f"[WARNING] 测试台文件不存在: {self.testbench_path}")
        
        # 验证自定义需求
        if self.custom_requirements and len(self.custom_requirements.strip()) < 10:
            print(f"[WARNING] 自定义需求可能过于简短: {len(self.custom_requirements)} 字符")
        
        print("✅ 实验配置验证通过")


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
    
    print("统一测试驱动开发(TDD)测试入口")
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
        else:
            print("设计未能通过所有测试")
            print("可以查看日志分析迭代改进过程")
            print(f"实验报告: unified_tdd_report_{experiment.experiment_id}.json")
        
        return result["success"]
        
    except Exception as e:
        print(f"实验执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)