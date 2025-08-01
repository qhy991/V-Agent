#!/usr/bin/env python3
"""
增强的测试方法 - 支持用户指定测试台和失败分析
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class EnhancedTestMethods:
    """增强的测试方法集合"""
    
    async def run_simulation_with_user_testbench(self, module_file: str, 
                                               user_testbench_path: str,
                                               max_retries: int = 3) -> Dict[str, Any]:
        """使用用户指定的测试台运行仿真"""
        self.logger.info(f"🧪 使用用户测试台运行仿真: {user_testbench_path}")
        
        try:
            # 1. 验证测试台文件
            tb_validation = await self._validate_user_testbench(user_testbench_path)
            if not tb_validation["valid"]:
                return {
                    "success": False,
                    "error": f"用户测试台验证失败: {tb_validation['error']}",
                    "testbench_path": user_testbench_path
                }
            
            # 2. 运行仿真
            sim_result = await self._execute_simulation_with_testbench(
                module_file, user_testbench_path
            )
            
            # 3. 分析结果
            if sim_result["success"]:
                analysis = await self._analyze_simulation_results(sim_result)
                sim_result.update(analysis)
            else:
                # 测试失败，进行深度分析
                failure_analysis = await self._analyze_test_failures(
                    sim_result, module_file, user_testbench_path
                )
                sim_result.update(failure_analysis)
            
            return sim_result
            
        except Exception as e:
            self.logger.error(f"❌ 仿真执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"仿真执行异常: {str(e)}",
                "exception_type": type(e).__name__
            }
    
    async def _validate_user_testbench(self, testbench_path: str) -> Dict[str, Any]:
        """验证用户提供的测试台"""
        try:
            tb_path = Path(testbench_path)
            
            if not tb_path.exists():
                return {
                    "valid": False,
                    "error": f"测试台文件不存在: {testbench_path}"
                }
            
            # 读取内容进行验证
            content = tb_path.read_text(encoding='utf-8')
            
            # 验证项目
            validations = {
                "has_module": bool(re.search(r'module\s+\w+', content)),
                "has_endmodule": "endmodule" in content,
                "has_initial_block": "initial" in content,
                "has_testbench_structure": any(keyword in content.lower() 
                    for keyword in ["testbench", "tb", "$monitor", "$display", "$finish"])
            }
            
            missing_items = [k for k, v in validations.items() if not v]
            
            if missing_items:
                return {
                    "valid": False,
                    "error": f"测试台缺少必要元素: {missing_items}",
                    "validations": validations
                }
            
            # 提取模块信息
            module_info = self._extract_testbench_module_info(content)
            
            return {
                "valid": True,
                "path": str(tb_path.resolve()),
                "module_info": module_info,
                "validations": validations
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证测试台时出错: {str(e)}"
            }
    
    def _extract_testbench_module_info(self, content: str) -> Dict[str, Any]:
        """从测试台中提取模块信息"""
        info = {
            "testbench_module_name": None,
            "dut_instance_name": None,
            "dut_module_name": None,
            "signals": []
        }
        
        # 提取测试台模块名
        tb_module_match = re.search(r'module\s+(\w+)', content)
        if tb_module_match:
            info["testbench_module_name"] = tb_module_match.group(1)
        
        # 提取DUT实例化信息
        dut_instance_matches = re.findall(
            r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;', content
        )
        
        if dut_instance_matches:
            # 假设第一个实例化就是DUT
            info["dut_module_name"] = dut_instance_matches[0][0]
            info["dut_instance_name"] = dut_instance_matches[0][1]
        
        # 提取信号声明
        signal_matches = re.findall(r'(reg|wire)\s+(?:\[\d+:\d+\])?\s*(\w+)', content)
        info["signals"] = [{"type": match[0], "name": match[1]} for match in signal_matches]
        
        return info
    
    async def _execute_simulation_with_testbench(self, module_file: str, 
                                               testbench_path: str) -> Dict[str, Any]:
        """执行仿真并收集详细结果"""
        try:
            # 使用iverilog执行仿真
            module_path = Path(module_file)
            testbench_path_obj = Path(testbench_path)
            output_file = module_path.parent / f"{module_path.stem}_sim"
            
            # 编译命令
            compile_cmd = [
                "iverilog", 
                "-o", str(output_file),
                str(module_path),
                str(testbench_path_obj)
            ]
            
            # 执行编译
            compile_result = await self._run_command(compile_cmd)
            
            if compile_result["returncode"] != 0:
                return {
                    "success": False,
                    "stage": "compilation",
                    "error": compile_result["stderr"],
                    "compile_output": compile_result["stdout"],
                    "command": " ".join(compile_cmd)
                }
            
            # 运行仿真
            run_cmd = [str(output_file)]
            run_result = await self._run_command(run_cmd)
            
            # 分析运行结果
            success = run_result["returncode"] == 0
            
            return {
                "success": success,
                "stage": "simulation" if success else "runtime_error",
                "compile_output": compile_result["stdout"],
                "simulation_output": run_result["stdout"],
                "error_output": run_result["stderr"],
                "return_code": run_result["returncode"],
                "command": " ".join(run_cmd)
            }
            
        except Exception as e:
            return {
                "success": False,
                "stage": "execution",
                "error": f"执行仿真时出错: {str(e)}"
            }
    
    async def _analyze_simulation_results(self, sim_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析仿真结果"""
        analysis = {
            "test_passed": sim_result["success"],
            "test_summary": "",
            "detailed_analysis": {}
        }
        
        if sim_result["success"]:
            # 分析成功的仿真输出
            output = sim_result.get("simulation_output", "")
            
            # 查找测试结果指示器
            if any(keyword in output.lower() for keyword in ["test passed", "all tests passed", "success"]):
                analysis["test_summary"] = "✅ 所有测试通过"
                analysis["all_tests_passed"] = True
            elif any(keyword in output.lower() for keyword in ["test failed", "error", "fail"]):
                analysis["test_summary"] = "⚠️ 仿真成功但测试可能失败"
                analysis["all_tests_passed"] = False
                analysis["potential_issues"] = self._extract_potential_issues(output)
            else:
                analysis["test_summary"] = "✅ 仿真完成，需要人工确认结果"
                analysis["all_tests_passed"] = True  # 假设成功
        
        return analysis
    
    async def _analyze_test_failures(self, sim_result: Dict[str, Any], 
                                   module_file: str, testbench_path: str) -> Dict[str, Any]:
        """深度分析测试失败原因"""
        analysis = {
            "failure_analysis": {},
            "suggested_fixes": [],
            "all_tests_passed": False
        }
        
        stage = sim_result.get("stage", "unknown")
        error_output = sim_result.get("error_output", "")
        
        if stage == "compilation":
            # 编译错误分析
            analysis["failure_analysis"] = await self._analyze_compilation_errors(
                error_output, module_file, testbench_path
            )
        elif stage == "runtime_error":
            # 运行时错误分析
            analysis["failure_analysis"] = await self._analyze_runtime_errors(
                error_output, sim_result.get("simulation_output", "")
            )
        
        # 生成修复建议
        analysis["suggested_fixes"] = await self._generate_fix_suggestions(
            analysis["failure_analysis"], module_file
        )
        
        return analysis
    
    async def _analyze_compilation_errors(self, error_output: str, 
                                        module_file: str, testbench_path: str) -> Dict[str, Any]:
        """分析编译错误"""
        analysis = {
            "error_type": "compilation",
            "specific_errors": [],
            "common_issues": []
        }
        
        # 解析具体错误
        error_patterns = [
            (r"error: (.+)", "general_error"),
            (r"syntax error (.+)", "syntax_error"),
            (r"undeclared identifier (.+)", "undeclared_identifier"),
            (r"port (.+) not found", "port_mismatch"),
            (r"module (.+) not found", "module_not_found")
        ]
        
        for pattern, error_type in error_patterns:
            matches = re.findall(pattern, error_output, re.IGNORECASE)
            for match in matches:
                analysis["specific_errors"].append({
                    "type": error_type,
                    "message": match,
                    "line": self._extract_line_number(error_output, match)
                })
        
        # 识别常见问题
        if "port" in error_output.lower() and "not found" in error_output.lower():
            analysis["common_issues"].append("端口名称不匹配")
        if "undeclared" in error_output.lower():
            analysis["common_issues"].append("信号未声明")
        if "module" in error_output.lower() and "not found" in error_output.lower():
            analysis["common_issues"].append("模块名称不匹配")
        
        return analysis
    
    async def _analyze_runtime_errors(self, error_output: str, 
                                     simulation_output: str) -> Dict[str, Any]:
        """分析运行时错误"""
        analysis = {
            "error_type": "runtime",
            "runtime_issues": [],
            "simulation_problems": []
        }
        
        # 检查常见运行时问题
        if "x" in simulation_output.lower() or "z" in simulation_output.lower():
            analysis["simulation_problems"].append("信号存在未知状态(X)或高阻态(Z)")
        
        if "$finish" not in simulation_output and "$stop" not in simulation_output:
            analysis["simulation_problems"].append("仿真可能未正常结束")
        
        # 检查时序问题
        if "time" in error_output.lower():
            analysis["runtime_issues"].append("可能存在时序相关问题")
        
        return analysis
    
    async def _generate_fix_suggestions(self, failure_analysis: Dict[str, Any], 
                                      module_file: str) -> List[str]:
        """生成修复建议"""
        suggestions = []
        error_type = failure_analysis.get("error_type", "")
        
        if error_type == "compilation":
            for error in failure_analysis.get("specific_errors", []):
                if error["type"] == "port_mismatch":
                    suggestions.append(f"检查模块端口定义，确保测试台中的端口连接正确")
                elif error["type"] == "undeclared_identifier":
                    suggestions.append(f"声明缺失的信号: {error['message']}")
                elif error["type"] == "module_not_found":
                    suggestions.append(f"确保模块名称匹配: {error['message']}")
        
        elif error_type == "runtime":
            for issue in failure_analysis.get("simulation_problems", []):
                if "未知状态" in issue:
                    suggestions.append("检查信号初始化，确保所有信号都有明确的初始值")
                elif "未正常结束" in issue:
                    suggestions.append("在测试台中添加$finish语句以正常结束仿真")
        
        return suggestions
    
    def _extract_line_number(self, error_output: str, error_message: str) -> Optional[int]:
        """从错误输出中提取行号"""
        # 查找行号模式
        line_patterns = [
            rf"{re.escape(error_message)}.*:(\d+):",
            rf":(\d+):.*{re.escape(error_message)}"
        ]
        
        for pattern in line_patterns:
            match = re.search(pattern, error_output)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_potential_issues(self, output: str) -> List[str]:
        """从输出中提取潜在问题"""
        issues = []
        
        # 查找警告信息
        warning_patterns = [
            r"WARNING: (.+)",
            r"Warning: (.+)",
            r"注意: (.+)"
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            issues.extend(matches)
        
        return issues


# 这些方法需要添加到 RealCodeReviewAgent 类中