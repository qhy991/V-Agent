"""
🧠 完整上下文管理系统
==================================================

该系统负责管理TDD迭代过程中的完整上下文信息，确保每个agent都能访问：
- 完整的代码内容（包括具体出错行）
- 完整的对话历史（包括AI推理过程）
- 多agent协作的全量上下文
- 关键字段的完整保存和传递
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CodeContext:
    """代码上下文信息"""
    file_path: str
    content: str
    content_with_line_numbers: str
    module_name: str
    last_modified: float
    syntax_errors: List[Dict[str, Any]] = None
    error_lines: Dict[int, str] = None  # 错误行号 -> 具体内容
    
    def get_error_context(self, error_line: int, context_lines: int = 5) -> str:
        """获取错误行的上下文"""
        lines = self.content.split('\n')
        start = max(0, error_line - context_lines - 1)
        end = min(len(lines), error_line + context_lines)
        
        context = []
        for i in range(start, end):
            marker = ">>> " if i == error_line - 1 else "    "
            context.append(f"{marker}{i+1:3d}: {lines[i]}")
        
        return "\n".join(context)


@dataclass
class ConversationTurn:
    """对话轮次信息"""
    turn_id: str
    agent_id: str
    timestamp: float
    user_prompt: str
    system_prompt: str
    ai_response: str
    tool_calls: List[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = None
    reasoning_notes: str = ""
    success: bool = False
    error_info: Dict[str, Any] = None


@dataclass
class IterationContext:
    """迭代上下文信息"""
    iteration_id: str
    iteration_number: int
    timestamp: float
    code_files: Dict[str, CodeContext]
    testbench_files: Dict[str, CodeContext]
    conversation_turns: List[ConversationTurn]
    # 🎯 新增：端口信息管理
    port_info: Dict[str, Dict[str, Any]] = None  # module_name -> port_info
    agent_assignments: Dict[str, str] = None  # role -> agent_id
    # 🎯 修复：添加缺失的compilation_errors属性
    compilation_errors: List[Dict[str, Any]] = None
    simulation_errors: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.port_info is None:
            self.port_info = {}
        if self.agent_assignments is None:
            self.agent_assignments = {}
        if self.compilation_errors is None:
            self.compilation_errors = []
        if self.simulation_errors is None:
            self.simulation_errors = []


class FullContextManager:
    """完整上下文管理器"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.iterations: Dict[str, IterationContext] = {}
        self.current_iteration: Optional[IterationContext] = None
        self.global_context: Dict[str, Any] = {
            "session_start_time": time.time(),
            "task_description": "",
            "testbench_path": "",
            "design_requirements": "",
            "persistent_conversation_id": None,
            "agent_selections": {},  # 记录每个阶段选择的agent
            
            # 🎯 新增：全局成功经验累积
            "success_patterns": {
                "verilog_syntax": {
                    "correct_patterns": [],
                    "avoid_patterns": []
                },
                "interface_compliance": {
                    "correct_patterns": [],
                    "avoid_patterns": []
                },
                "overflow_detection": {
                    "correct_patterns": [],
                    "avoid_patterns": []
                }
            },
            "error_lessons": [],
            "successful_code_snippets": [],
            "failure_patterns": [],
            # 🎯 新增：端口信息全局缓存
            "global_port_info": {}  # module_name -> port_info
        }
    
    def add_port_info(self, module_name: str, port_info: Dict[str, Any]) -> None:
        """添加端口信息到当前迭代和全局缓存"""
        if self.current_iteration:
            self.current_iteration.port_info[module_name] = port_info
        
        # 同时更新全局缓存
        self.global_context["global_port_info"][module_name] = port_info
    
    def get_port_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """获取模块的端口信息"""
        # 优先从当前迭代获取
        if self.current_iteration and module_name in self.current_iteration.port_info:
            return self.current_iteration.port_info[module_name]
        
        # 从全局缓存获取
        return self.global_context["global_port_info"].get(module_name)
    
    def get_all_port_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有端口信息"""
        all_ports = {}
        
        # 合并当前迭代和全局缓存的端口信息
        if self.current_iteration:
            all_ports.update(self.current_iteration.port_info)
        
        all_ports.update(self.global_context["global_port_info"])
        
        return all_ports
    
    def validate_port_consistency(self, module_name: str, testbench_content: str) -> Dict[str, Any]:
        """验证测试台端口与设计端口的一致性"""
        design_ports = self.get_port_info(module_name)
        if not design_ports:
            return {"valid": False, "error": f"未找到模块 {module_name} 的端口信息"}
        
        import re
        
        # 提取测试台中的模块实例化
        instance_pattern = rf'{module_name}\s+\w+\s*\(([^)]+)\);'
        match = re.search(instance_pattern, testbench_content, re.DOTALL)
        
        if not match:
            return {"valid": False, "error": f"未找到模块 {module_name} 的实例化"}
        
        instance_ports = match.group(1)
        port_connections = []
        
        # 解析端口连接
        for line in instance_ports.split(','):
            line = line.strip()
            if not line:
                continue
            
            port_match = re.search(r'\.(\w+)\s*\(\s*(\w+)\s*\)', line)
            if port_match:
                port_name = port_match.group(1)
                signal_name = port_match.group(2)
                port_connections.append({"port": port_name, "signal": signal_name})
        
        # 验证端口连接
        design_port_names = {port["name"] for port in design_ports["ports"]}
        testbench_port_names = {conn["port"] for conn in port_connections}
        
        missing_ports = design_port_names - testbench_port_names
        extra_ports = testbench_port_names - design_port_names
        
        return {
            "valid": len(missing_ports) == 0 and len(extra_ports) == 0,
            "missing_ports": list(missing_ports),
            "extra_ports": list(extra_ports),
            "design_ports": design_ports,
            "testbench_connections": port_connections
        }
    
    def start_new_iteration(self, iteration_number: int) -> str:
        """开始新的迭代"""
        iteration_id = f"{self.session_id}_iter_{iteration_number}"
        
        self.current_iteration = IterationContext(
            iteration_id=iteration_id,
            iteration_number=iteration_number,
            timestamp=time.time(),
            code_files={},
            testbench_files={},
            conversation_turns=[]
        )
        
        self.iterations[iteration_id] = self.current_iteration
        return iteration_id
    
    def add_conversation_turn(self, agent_id: str, user_prompt: str, 
                            system_prompt: str, ai_response: str,
                            tool_calls: List[Dict] = None, 
                            tool_results: List[Dict] = None,
                            reasoning_notes: str = "") -> str:
        """添加对话轮次"""
        if not self.current_iteration:
            raise ValueError("没有活跃的迭代")
        
        turn_id = f"{self.current_iteration.iteration_id}_turn_{len(self.current_iteration.conversation_turns) + 1}"
        
        turn = ConversationTurn(
            turn_id=turn_id,
            agent_id=agent_id,
            timestamp=time.time(),
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            ai_response=ai_response,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            reasoning_notes=reasoning_notes
        )
        
        self.current_iteration.conversation_turns.append(turn)
        return turn_id
    
    def add_code_file(self, file_path: str, content: str, module_name: str, 
                     file_type: str = "design") -> None:
        """添加代码文件"""
        if not self.current_iteration:
            raise ValueError("没有活跃的迭代")
        
        # 生成带行号的内容
        lines = content.split('\n')
        content_with_line_numbers = "\n".join([
            f"{i+1:4d}→{line}" for i, line in enumerate(lines)
        ])
        
        code_context = CodeContext(
            file_path=file_path,
            content=content,
            content_with_line_numbers=content_with_line_numbers,
            module_name=module_name,
            last_modified=time.time()
        )
        
        if file_type == "design":
            self.current_iteration.code_files[file_path] = code_context
        else:
            self.current_iteration.testbench_files[file_path] = code_context
    
    def add_compilation_errors(self, errors: List[Dict[str, Any]]) -> None:
        """添加编译错误信息"""
        if not self.current_iteration:
            return
        
        self.current_iteration.compilation_errors = errors
        self.current_iteration.compilation_success = len(errors) == 0
        
        # 为每个代码文件标记错误行
        for error in errors:
            if 'file' in error and 'line' in error:
                file_path = error['file']
                line_number = int(error['line'])
                
                # 找到对应的代码文件
                code_context = None
                if file_path in self.current_iteration.code_files:
                    code_context = self.current_iteration.code_files[file_path]
                elif file_path in self.current_iteration.testbench_files:
                    code_context = self.current_iteration.testbench_files[file_path]
                
                if code_context:
                    if not code_context.error_lines:
                        code_context.error_lines = {}
                    
                    # 获取错误行的具体内容
                    lines = code_context.content.split('\n')
                    if 0 <= line_number - 1 < len(lines):
                        code_context.error_lines[line_number] = lines[line_number - 1]
        
        # 🎯 新增：从错误中学习经验教训
        self._extract_error_lessons(errors)
    
    def get_full_context_for_agent(self, agent_id: str, current_task: str) -> Dict[str, Any]:
        """为agent构建完整上下文信息"""
        context = {
            "session_info": {
                "session_id": self.session_id,
                "total_iterations": len(self.iterations),
                "current_iteration_number": self.current_iteration.iteration_number if self.current_iteration else 0,
                "task_description": self.global_context["task_description"],
                "current_task": current_task
            },
            
            "complete_code_content": self._get_complete_code_content(),
            "complete_conversation_history": self._get_complete_conversation_history(),
            "detailed_error_context": self._get_detailed_error_context(),
            "previous_iterations_summary": self._get_previous_iterations_summary(),
            "agent_collaboration_history": self._get_agent_collaboration_history(),
            # 🎯 新增：端口信息传递
            "port_info": self.get_all_port_info(),
            "current_iteration_port_info": self.current_iteration.port_info if self.current_iteration else {}
        }
        
        return context
    
    # 🎯 新增：成功经验累积方法
    
    def extract_success_patterns(self, iteration_result: Dict[str, Any]) -> None:
        """从成功的迭代中提取成功模式"""
        if not self.current_iteration:
            return
        
        # 检查是否成功
        if iteration_result.get("all_tests_passed", False):
            self._extract_verilog_success_patterns()
            self._extract_interface_success_patterns()
            self._extract_code_improvements()
    
    def _extract_error_lessons(self, errors: List[Dict[str, Any]]) -> None:
        """从编译错误中提取经验教训"""
        if not self.current_iteration:
            return
        
        lessons = []
        
        for error in errors:
            error_message = error.get('message', '')
            error_type = error.get('type', '')
            
            # 分析常见错误模式
            if 'Index' in error_message and 'out of range' in error_message:
                lessons.append("数组越界：确保数组大小足够支持所有索引访问")
            elif 'syntax error' in error_message.lower():
                lessons.append("语法错误：检查Verilog语法兼容性，避免使用不兼容的特性")
            elif 'Incomprehensible for loop' in error_message:
                lessons.append("循环语法错误：在generate块中使用简单的assign语句，避免复杂逻辑")
            elif 'Malformed statement' in error_message:
                lessons.append("语句格式错误：检查语句语法，确保符合Verilog-2001标准")
            elif 'logic' in error_message.lower():
                lessons.append("类型错误：使用wire和reg类型，避免使用logic类型")
            elif 'clk' in error_message.lower() or 'rst' in error_message.lower():
                lessons.append("接口违规：纯组合逻辑模块不应包含时钟或复位信号")
        
        # 添加到当前迭代和全局上下文
        if not self.current_iteration.error_lessons:
            self.current_iteration.error_lessons = []
        self.current_iteration.error_lessons.extend(lessons)
        
        # 更新全局错误教训（去重）
        for lesson in lessons:
            if lesson not in self.global_context["error_lessons"]:
                self.global_context["error_lessons"].append(lesson)
    
    def _extract_verilog_success_patterns(self) -> None:
        """提取Verilog语法成功模式"""
        if not self.current_iteration or not self.current_iteration.code_files:
            return
        
        correct_patterns = []
        avoid_patterns = []
        
        for file_path, code_context in self.current_iteration.code_files.items():
            content = code_context.content
            
            # 分析成功的语法模式
            if 'wire [16:0] carry' in content:
                correct_patterns.append("16位加法器使用17位进位数组：wire [16:0] carry")
            if 'assign overflow = (a[15] == b[15]) && (a[15] != sum[15])' in content:
                correct_patterns.append("有符号溢出检测：overflow = (a[15] == b[15]) && (a[15] != sum[15])")
            if 'assign' in content and 'always @(posedge' not in content:
                correct_patterns.append("纯组合逻辑使用assign语句，避免时序结构")
            
            # 分析需要避免的模式
            if 'logic' in content:
                avoid_patterns.append("避免使用logic类型，使用wire和reg")
            if 'always @(posedge clk' in content:
                avoid_patterns.append("纯组合逻辑不应包含时钟信号")
            if 'generate' in content and 'for' in content:
                avoid_patterns.append("generate块中避免复杂的for循环逻辑")
        
        # 更新全局成功模式
        self.global_context["success_patterns"]["verilog_syntax"]["correct_patterns"].extend(correct_patterns)
        self.global_context["success_patterns"]["verilog_syntax"]["avoid_patterns"].extend(avoid_patterns)
        
        # 去重
        self.global_context["success_patterns"]["verilog_syntax"]["correct_patterns"] = list(set(
            self.global_context["success_patterns"]["verilog_syntax"]["correct_patterns"]
        ))
        self.global_context["success_patterns"]["verilog_syntax"]["avoid_patterns"] = list(set(
            self.global_context["success_patterns"]["verilog_syntax"]["avoid_patterns"]
        ))
    
    def _extract_interface_success_patterns(self) -> None:
        """提取接口合规性成功模式"""
        if not self.current_iteration or not self.current_iteration.code_files:
            return
        
        correct_patterns = []
        
        for file_path, code_context in self.current_iteration.code_files.items():
            content = code_context.content
            
            # 检查模块名
            if 'module adder_16bit' in content:
                correct_patterns.append("模块名严格匹配：adder_16bit")
            
            # 检查端口定义
            if 'input [15:0] a' in content and 'input [15:0] b' in content:
                correct_patterns.append("输入端口位宽正确：input [15:0] a, b")
            if 'output [15:0] sum' in content:
                correct_patterns.append("输出端口位宽正确：output [15:0] sum")
            if 'output cout' in content and 'output overflow' in content:
                correct_patterns.append("输出端口完整：cout, overflow")
            
            # 检查无额外信号
            if 'clk' not in content and 'rst' not in content:
                correct_patterns.append("纯组合逻辑：无时钟和复位信号")
        
        # 更新全局成功模式
        self.global_context["success_patterns"]["interface_compliance"]["correct_patterns"].extend(correct_patterns)
        self.global_context["success_patterns"]["interface_compliance"]["correct_patterns"] = list(set(
            self.global_context["success_patterns"]["interface_compliance"]["correct_patterns"]
        ))
    
    def _extract_code_improvements(self) -> None:
        """提取代码改进点"""
        if not self.current_iteration:
            return
        
        improvements = []
        
        # 从对话历史中提取改进点
        for turn in self.current_iteration.conversation_turns:
            if turn.success and turn.reasoning_notes:
                improvements.append(f"推理改进：{turn.reasoning_notes}")
        
        # 从工具调用中提取改进点
        for turn in self.current_iteration.conversation_turns:
            if turn.tool_calls:
                for tool_call in turn.tool_calls:
                    if tool_call.get("success", False):
                        tool_name = tool_call.get("tool_name", "")
                        improvements.append(f"工具使用成功：{tool_name}")
        
        if not self.current_iteration.code_improvements:
            self.current_iteration.code_improvements = []
        self.current_iteration.code_improvements.extend(improvements)
    
    def get_success_guidance(self) -> Dict[str, Any]:
        """获取成功经验指导"""
        return {
            "success_patterns": self.global_context["success_patterns"],
            "error_lessons": self.global_context["error_lessons"],
            "successful_code_snippets": self.global_context["successful_code_snippets"],
            "failure_patterns": self.global_context["failure_patterns"]
        }
    
    def build_success_context_for_agent(self) -> str:
        """为agent构建成功经验上下文"""
        guidance = self.get_success_guidance()
        
        context = "\n\n🎯 **基于历史迭代的成功经验指导**:\n\n"
        
        # 成功模式
        if guidance["success_patterns"]["verilog_syntax"]["correct_patterns"]:
            context += "### ✅ 已验证的正确实现模式:\n"
            context += "```verilog\n"
            context += "// 正确的16位加法器结构\n"
            context += "module adder_16bit (\n"
            context += "    input  [15:0] a,\n"
            context += "    input  [15:0] b, \n"
            context += "    input         cin,\n"
            context += "    output [15:0] sum,\n"
            context += "    output        cout,\n"
            context += "    output        overflow\n"
            context += ");\n\n"
            context += "    // 正确的进位数组大小\n"
            context += "    wire [16:0] carry;  // 17位，支持16位加法器的进位链\n\n"
            context += "    // 正确的组合逻辑实现\n"
            context += "    assign carry[0] = cin;\n"
            context += "    assign sum[0] = a[0] ^ b[0] ^ carry[0];\n"
            context += "    assign carry[1] = (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);\n\n"
            context += "    // 正确的溢出检测\n"
            context += "    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);\n"
            context += "    assign cout = carry[16];\n\n"
            context += "endmodule\n"
            context += "```\n\n"
        
        # 避免的错误模式
        if guidance["error_lessons"]:
            context += "### ❌ 避免的错误模式:\n"
            for lesson in guidance["error_lessons"][:5]:  # 最多显示5个
                context += f"1. {lesson}\n"
            context += "\n"
        
        # 成功模式总结
        for category, patterns in guidance["success_patterns"].items():
            if patterns["correct_patterns"]:
                context += f"### ✅ {category} 成功模式:\n"
                for pattern in patterns["correct_patterns"][:3]:  # 最多显示3个
                    context += f"- {pattern}\n"
                context += "\n"
        
        context += "### 🎯 本次迭代要求:\n"
        context += "请严格按照上述成功模式生成代码，确保：\n"
        context += "1. 使用正确的数组大小\n"
        context += "2. 实现纯组合逻辑\n"
        context += "3. 严格匹配接口规范\n"
        
        return context
    
    def _get_complete_code_content(self) -> Dict[str, Any]:
        """获取完整代码内容"""
        if not self.current_iteration:
            return {}
        
        result = {
            "design_files": {},
            "testbench_files": {}
        }
        
        # 设计文件
        for file_path, code_context in self.current_iteration.code_files.items():
            result["design_files"][file_path] = {
                "module_name": code_context.module_name,
                "content": code_context.content,
                "content_with_line_numbers": code_context.content_with_line_numbers,
                "error_lines": code_context.error_lines or {},
                "last_modified": code_context.last_modified
            }
        
        # 测试台文件
        for file_path, code_context in self.current_iteration.testbench_files.items():
            result["testbench_files"][file_path] = {
                "module_name": code_context.module_name,
                "content": code_context.content,
                "content_with_line_numbers": code_context.content_with_line_numbers,
                "error_lines": code_context.error_lines or {},
                "last_modified": code_context.last_modified
            }
        
        return result
    
    def _get_complete_conversation_history(self) -> List[Dict[str, Any]]:
        """获取完整对话历史"""
        history = []
        
        # 遍历所有迭代的对话
        for iteration_id in sorted(self.iterations.keys()):
            iteration = self.iterations[iteration_id]
            
            for turn in iteration.conversation_turns:
                history.append({
                    "iteration_number": iteration.iteration_number,
                    "turn_id": turn.turn_id,
                    "agent_id": turn.agent_id,
                    "timestamp": turn.timestamp,
                    "user_prompt": turn.user_prompt,
                    "system_prompt": turn.system_prompt,
                    "ai_response": turn.ai_response,
                    "tool_calls": turn.tool_calls,
                    "tool_results": turn.tool_results,
                    "reasoning_notes": turn.reasoning_notes,
                    "success": turn.success,
                    "error_info": turn.error_info
                })
        
        return history
    
    def _get_detailed_error_context(self) -> Dict[str, Any]:
        """获取详细错误上下文"""
        if not self.current_iteration or not self.current_iteration.compilation_errors:
            return {}
        
        detailed_errors = []
        
        for error in self.current_iteration.compilation_errors:
            detailed_error = dict(error)  # 复制原错误信息
            
            # 添加错误行的上下文
            if 'file' in error and 'line' in error:
                file_path = error['file']
                line_number = int(error['line'])
                
                # 查找代码文件
                code_context = None
                if file_path in self.current_iteration.code_files:
                    code_context = self.current_iteration.code_files[file_path]
                elif file_path in self.current_iteration.testbench_files:
                    code_context = self.current_iteration.testbench_files[file_path]
                
                if code_context:
                    detailed_error["error_line_content"] = code_context.error_lines.get(line_number, "")
                    detailed_error["error_context"] = code_context.get_error_context(line_number)
            
            detailed_errors.append(detailed_error)
        
        return {
            "compilation_errors": detailed_errors,
            "compilation_success": self.current_iteration.compilation_success,
            "simulation_success": self.current_iteration.simulation_success,
            "all_tests_passed": self.current_iteration.all_tests_passed,
            "failure_analysis": self.current_iteration.failure_analysis,
            "improvement_suggestions": self.current_iteration.improvement_suggestions
        }
    
    def _get_previous_iterations_summary(self) -> List[Dict[str, Any]]:
        """获取之前迭代的摘要"""
        summaries = []
        
        for iteration_id in sorted(self.iterations.keys()):
            iteration = self.iterations[iteration_id]
            if iteration == self.current_iteration:
                continue  # 跳过当前迭代
            
            summary = {
                "iteration_number": iteration.iteration_number,
                "timestamp": iteration.timestamp,
                "compilation_success": iteration.compilation_success,
                "simulation_success": iteration.simulation_success,
                "all_tests_passed": iteration.all_tests_passed,
                "conversation_turns_count": len(iteration.conversation_turns),
                "code_files_count": len(iteration.code_files),
                "key_decisions": self._extract_key_decisions(iteration),
                "main_failures": self._extract_main_failures(iteration),
                "lessons_learned": self._extract_lessons_learned(iteration)
            }
            
            summaries.append(summary)
        
        return summaries
    
    def _get_agent_collaboration_history(self) -> Dict[str, Any]:
        """获取多agent协作历史"""
        collaboration = {
            "agent_interactions": [],
            "handoff_points": [],
            "shared_decisions": []
        }
        
        # 分析agent之间的交互
        for iteration_id in sorted(self.iterations.keys()):
            iteration = self.iterations[iteration_id]
            
            agents_in_iteration = set(turn.agent_id for turn in iteration.conversation_turns)
            
            if len(agents_in_iteration) > 1:
                collaboration["agent_interactions"].append({
                    "iteration_number": iteration.iteration_number,
                    "agents": list(agents_in_iteration),
                    "interaction_type": "multi_agent_collaboration",
                    "context": self._analyze_agent_interaction(iteration)
                })
        
        return collaboration
    
    def _extract_key_decisions(self, iteration: IterationContext) -> List[str]:
        """提取关键决策"""
        decisions = []
        
        for turn in iteration.conversation_turns:
            # 分析AI响应中的关键决策点
            if "决定" in turn.ai_response or "选择" in turn.ai_response:
                # 提取决策相关的句子
                sentences = turn.ai_response.split('。')
                for sentence in sentences:
                    if any(keyword in sentence for keyword in ["决定", "选择", "采用", "修改"]):
                        decisions.append(sentence.strip())
        
        return decisions[:3]  # 最多返回3个关键决策
    
    def _extract_main_failures(self, iteration: IterationContext) -> List[str]:
        """提取主要失败原因"""
        failures = []
        
        if iteration.compilation_errors:
            error_types = set()
            for error in iteration.compilation_errors:
                if 'type' in error:
                    error_types.add(error['type'])
            failures.extend(list(error_types))
        
        return failures
    
    def _extract_lessons_learned(self, iteration: IterationContext) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        if iteration.improvement_suggestions:
            lessons.extend(iteration.improvement_suggestions[:2])
        
        return lessons
    
    def _analyze_agent_interaction(self, iteration: IterationContext) -> Dict[str, Any]:
        """分析agent交互"""
        return {
            "turns_count": len(iteration.conversation_turns),
            "main_topics": ["设计生成", "代码审查", "错误修复"],  # 简化版本
            "outcome": "协作完成" if iteration.all_tests_passed else "需要继续迭代"
        }
    
    def save_to_file(self, file_path: str) -> None:
        """保存上下文到文件"""
        context_data = {
            "session_id": self.session_id,
            "global_context": self.global_context,
            "iterations": {}
        }
        
        # 序列化迭代数据
        for iteration_id, iteration in self.iterations.items():
            context_data["iterations"][iteration_id] = asdict(iteration)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_from_file(self, file_path: str) -> None:
        """从文件加载上下文"""
        with open(file_path, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        self.session_id = context_data["session_id"]
        self.global_context = context_data["global_context"]
        
        # 反序列化迭代数据
        for iteration_id, iteration_data in context_data["iterations"].items():
            # 这里需要更复杂的反序列化逻辑，暂时简化
            self.iterations[iteration_id] = iteration_data


# 全局上下文管理器实例
_context_managers: Dict[str, FullContextManager] = {}


def get_context_manager(session_id: str) -> FullContextManager:
    """获取或创建上下文管理器"""
    if session_id not in _context_managers:
        _context_managers[session_id] = FullContextManager(session_id)
    return _context_managers[session_id]


def cleanup_context_manager(session_id: str) -> None:
    """清理上下文管理器"""
    if session_id in _context_managers:
        del _context_managers[session_id]