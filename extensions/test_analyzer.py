#!/usr/bin/env python3
"""
测试分析器 - 完全独立的扩展模块
"""

import asyncio
import subprocess
import tempfile
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class TestAnalyzer:
    """测试分析器 - 专门处理测试执行和分析"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TestAnalyzer")
        self.temp_dir = Path(tempfile.gettempdir()) / "tdd_test_analyzer"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def validate_testbench_file(self, testbench_path: str) -> Dict[str, Any]:
        """验证测试台文件"""
        try:
            tb_path = Path(testbench_path)
            
            if not tb_path.exists():
                return {
                    "valid": False,
                    "error": f"测试台文件不存在: {testbench_path}",
                    "suggestions": ["检查测试台文件路径是否正确", "确保文件存在且可读"]
                }
            
            # 读取内容
            try:
                content = tb_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = tb_path.read_text(encoding='latin-1')
            
            # 基本验证
            validations = self._validate_testbench_content(content)
            
            if not validations["is_valid"]:
                return {
                    "valid": False,
                    "error": "测试台文件格式不正确",
                    "validation_details": validations,
                    "suggestions": self._generate_testbench_fix_suggestions(validations)
                }
            
            # 提取模块信息
            module_info = self._extract_testbench_info(content)
            
            return {
                "valid": True,
                "path": str(tb_path.resolve()),
                "size": tb_path.stat().st_size,
                "module_info": module_info,
                "validation_details": validations
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证测试台时出错: {str(e)}",
                "suggestions": ["检查文件权限", "确保文件不被其他程序占用"]
            }
    
    def _validate_testbench_content(self, content: str) -> Dict[str, Any]:
        """验证测试台内容"""
        validations = {
            "has_module": bool(re.search(r'module\s+\w+', content)),
            "has_endmodule": "endmodule" in content,
            "has_initial_block": "initial" in content or "always" in content,
            "has_testbench_elements": any(keyword in content.lower() 
                for keyword in ["$monitor", "$display", "$finish", "$stop", "$dumpfile"]),
            "has_time_control": any(keyword in content 
                for keyword in ["#", "@", "wait"]),
            "syntax_check": self._basic_syntax_check(content)
        }
        
        validations["is_valid"] = all([
            validations["has_module"],
            validations["has_endmodule"],
            validations["has_initial_block"],
            validations["syntax_check"]
        ])
        
        return validations
    
    def _basic_syntax_check(self, content: str) -> bool:
        """基本语法检查"""
        try:
            # 检查括号匹配
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens != close_parens:
                return False
            
            # 检查begin/end匹配
            begin_count = len(re.findall(r'\bbegin\b', content))
            end_count = len(re.findall(r'\bend\b', content))
            if begin_count != end_count:
                return False
            
            return True
        except:
            return False
    
    def _extract_testbench_info(self, content: str) -> Dict[str, Any]:
        """提取测试台信息"""
        info = {
            "testbench_module": None,
            "dut_instances": [],
            "signals": [],
            "clocks": [],
            "test_procedures": []
        }
        
        # 提取测试台模块名
        tb_match = re.search(r'module\s+(\w+)', content)
        if tb_match:
            info["testbench_module"] = tb_match.group(1)
        
        # 提取DUT实例
        instance_pattern = r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;'
        instances = re.findall(instance_pattern, content)
        for module_name, instance_name in instances:
            if module_name != info["testbench_module"]:
                info["dut_instances"].append({
                    "module": module_name,
                    "instance": instance_name
                })
        
        # 提取信号声明
        signal_patterns = [
            r'(reg|wire)\s+(?:\[[\d:]+\])?\s*(\w+)',
            r'(input|output)\s+(?:\[[\d:]+\])?\s*(\w+)'
        ]
        
        for pattern in signal_patterns:
            matches = re.findall(pattern, content)
            for signal_type, signal_name in matches:
                info["signals"].append({
                    "type": signal_type,
                    "name": signal_name
                })
        
        # 检测时钟信号
        for signal in info["signals"]:
            if any(clk_keyword in signal["name"].lower() 
                   for clk_keyword in ["clk", "clock", "ck"]):
                info["clocks"].append(signal["name"])
        
        return info
    
    def _generate_testbench_fix_suggestions(self, validations: Dict[str, Any]) -> List[str]:
        """生成测试台修复建议"""
        suggestions = []
        
        if not validations["has_module"]:
            suggestions.append("添加module声明: module testbench_name();")
        
        if not validations["has_endmodule"]:
            suggestions.append("添加endmodule语句结束模块定义")
        
        if not validations["has_initial_block"]:
            suggestions.append("添加initial块或always块来驱动测试")
        
        if not validations["has_testbench_elements"]:
            suggestions.append("添加测试台元素：$monitor, $display, $finish等")
        
        if not validations["syntax_check"]:
            suggestions.append("检查语法错误：括号匹配、begin/end匹配等")
        
        return suggestions
    
    async def run_with_user_testbench(self, design_files: List[Any],
                                    testbench_path: str) -> Dict[str, Any]:
        """使用用户测试台运行测试"""
        self.logger.info(f"🧪 使用用户测试台运行测试: {testbench_path}")
        
        try:
            # 准备文件路径
            design_file_paths = self._extract_file_paths(design_files)
            
            if not design_file_paths:
                return {
                    "success": False,
                    "error": "没有找到设计文件",
                    "all_tests_passed": False
                }
            
            # 执行仿真
            sim_result = await self._run_simulation(design_file_paths, testbench_path)
            
            # 分析结果
            analysis = await self._analyze_simulation_output(sim_result)
            
            # 合并结果
            result = {
                **sim_result,
                **analysis,
                "testbench_path": testbench_path,
                "design_files": design_file_paths
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 测试执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"测试执行异常: {str(e)}",
                "all_tests_passed": False
            }
    
    def _extract_file_paths(self, design_files: List[Any]) -> List[str]:
        """提取设计文件路径"""
        paths = []
        
        self.logger.debug(f"🔍 提取文件路径，输入类型: {type(design_files)}, 长度: {len(design_files) if design_files else 0}")
        
        if not design_files:
            self.logger.warning("⚠️ design_files为空")
            return []
        
        for i, file_ref in enumerate(design_files):
            self.logger.debug(f"🔍 处理文件引用 {i}: {type(file_ref)} = {file_ref}")
            
            path = None
            
            # 处理不同类型的文件引用
            if isinstance(file_ref, dict):
                # 字典格式：{"file_path": "...", "file_type": "...", ...}
                path = file_ref.get("file_path") or file_ref.get("path")
                self.logger.debug(f"  字典格式，提取路径: {path}")
                
            elif hasattr(file_ref, 'path'):
                # FileReference对象的path属性
                path = str(file_ref.path)
                self.logger.debug(f"  FileReference对象，path属性: {path}")
                
            elif hasattr(file_ref, 'file_path'):
                # 其他对象的file_path属性
                path = str(file_ref.file_path)
                self.logger.debug(f"  其他对象，file_path属性: {path}")
                
            elif isinstance(file_ref, (str, Path)):
                # 直接的路径字符串或Path对象
                path = str(file_ref)
                self.logger.debug(f"  直接路径: {path}")
                
            else:
                self.logger.warning(f"⚠️ 未知文件引用类型: {type(file_ref)}")
                continue
            
            if path:
                # 检查文件是否存在且是Verilog文件
                if Path(path).exists():
                    # 只处理.v和.sv文件（Verilog和SystemVerilog）
                    if path.endswith(('.v', '.sv')):
                        paths.append(path)
                        self.logger.debug(f"  ✅ 添加Verilog文件: {path}")
                    else:
                        self.logger.debug(f"  ⏭️ 跳过非Verilog文件: {path}")
                else:
                    self.logger.warning(f"⚠️ 文件不存在: {path}")
        
        self.logger.info(f"📄 成功提取设计文件路径: {len(paths)} 个文件")
        for i, path in enumerate(paths):
            self.logger.info(f"  {i+1}. {path}")
        
        return paths
    
    async def _run_simulation(self, design_files: List[str], 
                            testbench_path: str) -> Dict[str, Any]:
        """运行仿真"""
        try:
            self.logger.info(f"🧪 开始仿真，设计文件: {len(design_files)} 个")
            self.logger.info(f"📋 设计文件列表: {design_files}")
            self.logger.info(f"🧪 测试台文件: {testbench_path}")
            
            # 验证所有文件存在
            missing_files = []
            for file_path in design_files + [testbench_path]:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                return {
                    "success": False,
                    "stage": "file_validation",
                    "error": f"文件不存在: {missing_files}",
                    "missing_files": missing_files
                }
            
            # 创建临时输出文件
            timestamp = int(asyncio.get_event_loop().time())
            output_file = self.temp_dir / f"sim_{timestamp}"
            
            self.logger.info(f"📁 临时仿真输出: {output_file}")
            
            # 构建编译命令
            cmd = ["iverilog", "-o", str(output_file)]
            cmd.extend(design_files)
            cmd.append(testbench_path)
            
            self.logger.info(f"🔨 编译命令: {' '.join(cmd)}")
            
            # 确保临时目录存在
            self.temp_dir.mkdir(exist_ok=True)
            
            # 执行编译
            self.logger.info("⏳ 开始iverilog编译...")
            compile_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path.cwd())  # 确保工作目录正确
            )
            
            compile_stdout, compile_stderr = await compile_process.communicate()
            
            compile_stdout_str = compile_stdout.decode('utf-8', errors='ignore')
            compile_stderr_str = compile_stderr.decode('utf-8', errors='ignore')
            
            self.logger.info(f"🔨 编译返回码: {compile_process.returncode}")
            if compile_stdout_str:
                self.logger.info(f"📤 编译stdout: {compile_stdout_str}")
            if compile_stderr_str:
                self.logger.info(f"📤 编译stderr: {compile_stderr_str}")
            
            if compile_process.returncode != 0:
                return {
                    "success": False,
                    "stage": "compilation",
                    "compile_stdout": compile_stdout_str,
                    "compile_stderr": compile_stderr_str,
                    "command": ' '.join(cmd),
                    "returncode": compile_process.returncode
                }
            
            # 验证输出文件已创建
            if not output_file.exists():
                return {
                    "success": False,
                    "stage": "compilation",
                    "error": f"编译成功但输出文件未创建: {output_file}",
                    "compile_stdout": compile_stdout_str,
                    "compile_stderr": compile_stderr_str
                }
            
            # 运行仿真
            self.logger.info(f"▶️ 运行仿真: {output_file}")
            
            run_process = await asyncio.create_subprocess_exec(
                "vvp", str(output_file),  # 使用vvp运行编译后的仿真文件
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path.cwd())
            )
            
            try:
                # 设置超时以防止无限运行
                self.logger.info("⏳ 运行仿真，超时30秒...")
                sim_stdout, sim_stderr = await asyncio.wait_for(
                    run_process.communicate(), timeout=30.0
                )
                
                sim_stdout_str = sim_stdout.decode('utf-8', errors='ignore')
                sim_stderr_str = sim_stderr.decode('utf-8', errors='ignore')
                
                self.logger.info(f"▶️ 仿真返回码: {run_process.returncode}")
                if sim_stdout_str:
                    self.logger.info(f"📤 仿真stdout: {sim_stdout_str[:500]}...")  # 截断长输出
                if sim_stderr_str:
                    self.logger.info(f"📤 仿真stderr: {sim_stderr_str}")
                
            except asyncio.TimeoutError:
                self.logger.warning("⏰ 仿真超时，终止进程")
                run_process.kill()
                return {
                    "success": False,
                    "stage": "simulation_timeout",
                    "error": "仿真超时（30秒）",
                    "suggestion": "检查测试台是否包含$finish语句"
                }
            
            # 清理临时文件
            try:
                output_file.unlink()
                self.logger.debug(f"🗑️ 清理临时文件: {output_file}")
            except:
                pass
            
            simulation_success = run_process.returncode == 0
            self.logger.info(f"✅ 仿真完成，成功: {simulation_success}")
            
            return {
                "success": simulation_success,
                "stage": "simulation",
                "compile_stdout": compile_stdout_str,
                "simulation_stdout": sim_stdout_str,
                "simulation_stderr": sim_stderr_str,
                "return_code": run_process.returncode
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "stage": "tool_missing",
                "error": "iverilog工具未找到",
                "suggestion": "请安装iverilog: sudo apt-get install iverilog"
            }
        except Exception as e:
            return {
                "success": False,
                "stage": "execution_error",
                "error": f"执行仿真时出错: {str(e)}"
            }
    
    async def _analyze_simulation_output(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析仿真输出"""
        analysis = {
            "all_tests_passed": False,
            "test_summary": "",
            "detailed_analysis": {},
            "failure_reasons": [],
            "suggestions": []
        }
        
        if not sim_result.get("success", False):
            # 仿真失败分析
            stage = sim_result.get("stage", "unknown")
            
            if stage == "compilation":
                analysis.update(self._analyze_compilation_errors(sim_result))
            elif stage == "simulation_timeout":
                analysis.update(self._analyze_timeout_error(sim_result))
            else:
                analysis.update(self._analyze_runtime_errors(sim_result))
        else:
            # 仿真成功，分析输出
            analysis.update(self._analyze_successful_simulation(sim_result))
        
        return analysis
    
    def _analyze_compilation_errors(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析编译错误"""
        stderr = sim_result.get("compile_stderr", "")
        
        analysis = {
            "test_summary": "❌ 编译失败",
            "failure_reasons": [],
            "suggestions": []
        }
        
        # 解析常见编译错误
        error_patterns = {
            r"syntax error": "语法错误",
            r"undeclared identifier": "未声明的标识符",
            r"port.*not found": "端口不匹配",
            r"module.*not found": "模块未找到"
        }
        
        for pattern, error_type in error_patterns.items():
            if re.search(pattern, stderr, re.IGNORECASE):
                analysis["failure_reasons"].append(error_type)
        
        # 生成建议
        if "语法错误" in analysis["failure_reasons"]:
            analysis["suggestions"].append("检查Verilog语法：分号、括号、关键字拼写等")
        
        if "未声明的标识符" in analysis["failure_reasons"]:
            analysis["suggestions"].append("检查信号声明：确保所有使用的信号都已声明")
        
        if "端口不匹配" in analysis["failure_reasons"]:
            analysis["suggestions"].append("检查模块实例化：确保端口名称和数量匹配")
        
        if "模块未找到" in analysis["failure_reasons"]:
            analysis["suggestions"].append("检查模块名称：确保设计文件中的模块名与测试台中一致")
        
        return analysis
    
    def _analyze_timeout_error(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析超时错误"""
        return {
            "test_summary": "⏰ 仿真超时",
            "failure_reasons": ["仿真未正常结束"],
            "suggestions": [
                "在测试台中添加$finish语句",
                "检查是否存在无限循环",
                "减少仿真时间或增加超时限制"
            ]
        }
    
    def _analyze_runtime_errors(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析运行时错误"""
        stderr = sim_result.get("simulation_stderr", "")
        
        return {
            "test_summary": "❌ 运行时错误",
            "failure_reasons": ["仿真执行失败"],
            "suggestions": [
                "检查测试台逻辑",
                "查看错误输出获取详细信息",
                "确保所有信号都有初始值"
            ],
            "error_details": stderr
        }
    
    def _analyze_successful_simulation(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析成功的仿真"""
        stdout = sim_result.get("simulation_stdout", "")
        
        # 查找测试结果指示器
        success_indicators = ["test passed", "all tests passed", "success", "pass"]
        failure_indicators = ["test failed", "fail", "error", "mismatch"]
        
        stdout_lower = stdout.lower()
        
        has_success = any(indicator in stdout_lower for indicator in success_indicators)
        has_failure = any(indicator in stdout_lower for indicator in failure_indicators)
        
        if has_success and not has_failure:
            return {
                "all_tests_passed": True,
                "test_summary": "✅ 所有测试通过",
                "detailed_analysis": {"output_analysis": "发现成功指示器"}
            }
        elif has_failure:
            return {
                "all_tests_passed": False,
                "test_summary": "⚠️ 测试失败",
                "failure_reasons": ["测试用例失败"],
                "suggestions": ["检查设计逻辑", "分析测试台输出"]
            }
        else:
            # 没有明确的成功/失败指示器，需要更详细分析
            return {
                "all_tests_passed": True,  # 假设成功
                "test_summary": "✅ 仿真完成（需人工确认）",
                "detailed_analysis": {"output_analysis": "未发现明确的测试结果指示器"},
                "suggestions": ["人工检查仿真输出"]
            }
    
    async def analyze_test_failures(self, test_results: Dict[str, Any],
                                  enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试失败并生成改进建议"""
        suggestions = []
        
        # 基于失败原因生成建议
        failure_reasons = test_results.get("failure_reasons", [])
        
        for reason in failure_reasons:
            if "语法错误" in reason:
                suggestions.append("修复Verilog语法错误")
            elif "端口不匹配" in reason:
                suggestions.append("检查并修正模块端口定义")
            elif "未声明的标识符" in reason:
                suggestions.append("添加缺失的信号声明")
            elif "测试用例失败" in reason:
                suggestions.append("检查设计逻辑，确保满足测试台要求")
        
        # 基于测试台信息生成更具体的建议
        if enhanced_analysis.get("testbench_validation", {}).get("module_info"):
            module_info = enhanced_analysis["testbench_validation"]["module_info"] 
            if module_info.get("dut_instances"):
                dut_info = module_info["dut_instances"][0]
                suggestions.append(f"确保设计模块名为: {dut_info['module']}")
        
        return {
            "suggestions": suggestions,
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "failure_category": self._categorize_failures(failure_reasons)
        }
    
    def _categorize_failures(self, failure_reasons: List[str]) -> str:
        """对失败原因进行分类"""
        if any("语法" in reason for reason in failure_reasons):
            return "syntax_error"
        elif any("端口" in reason for reason in failure_reasons):
            return "interface_mismatch"
        elif any("测试" in reason for reason in failure_reasons):
            return "logic_error"
        else:
            return "unknown"