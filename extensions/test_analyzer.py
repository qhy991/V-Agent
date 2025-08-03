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

from .verilog_dependency_analyzer import VerilogDependencyAnalyzer


class TestAnalyzer:
    """测试分析器 - 专门处理测试执行和分析"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TestAnalyzer")
        self.temp_dir = Path(tempfile.gettempdir()) / "tdd_test_analyzer"
        self.temp_dir.mkdir(exist_ok=True)
        self.dependency_analyzer = VerilogDependencyAnalyzer()
    
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
    
    def _parse_compiler_errors(self, error_output: str) -> Dict[str, Any]:
        """解析编译器错误，提取文件名和行号"""
        errors = []
        
        # iverilog错误格式：filename:line: message
        # 示例：simple_adder.v:12: syntax error
        error_pattern = r'(.+?):(\d+):\s*(.+)'
        
        lines = error_output.split('\n')
        for line in lines:
            match = re.match(error_pattern, line.strip())
            if match:
                filename, line_num, message = match.groups()
                errors.append({
                    "file": filename,
                    "line": int(line_num),
                    "message": message.strip(),
                    "type": self._categorize_error(message)
                })
        
        return {
            "error_count": len(errors),
            "precise_errors": errors,
            "summary": self._generate_error_summary(errors)
        }
    
    def _categorize_error(self, error_message: str) -> str:
        """对错误类型进行分类"""
        message_lower = error_message.lower()
        
        if "syntax" in message_lower:
            return "syntax_error"
        elif "undeclared" in message_lower:
            return "undeclared_identifier"
        elif "module" in message_lower and "not found" in message_lower:
            return "module_not_found"
        elif "port" in message_lower:
            return "port_error"
        elif "wire" in message_lower or "reg" in message_lower:
            return "signal_declaration_error"
        else:
            return "other_error"
    
    def _generate_error_summary(self, errors: List[Dict[str, Any]]) -> str:
        """生成错误摘要"""
        if not errors:
            return "无编译错误"
        
        summary = f"发现 {len(errors)} 个编译错误:\n"
        for i, error in enumerate(errors[:3], 1):  # 最多显示前3个
            summary += f"{i}. 文件: {error['file']}, 行: {error['line']}\n"
            summary += f"   错误: {error['message']}\n"
        
        if len(errors) > 3:
            summary += f"... 还有 {len(errors) - 3} 个错误\n"
        
        return summary
    
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
        """使用用户测试台运行测试 - 增强依赖分析"""
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
            
            # 🔍 进行依赖分析和兼容性检查
            dependency_analysis = await self._analyze_dependencies(design_file_paths, testbench_path)
            
            if not dependency_analysis["success"]:
                return {
                    "success": False,
                    "error": f"依赖分析失败: {dependency_analysis['error']}",
                    "all_tests_passed": False,
                    "dependency_analysis": dependency_analysis
                }
            
            # 使用依赖分析的结果来确定编译文件
            compilation_files = dependency_analysis.get("compilation_files", design_file_paths)
            
            self.logger.info(f"🔍 依赖分析完成，需要编译 {len(compilation_files)} 个文件")
            
            # 执行仿真
            sim_result = await self._run_simulation(compilation_files, testbench_path)
            
            # 分析结果
            analysis = await self._analyze_simulation_output(sim_result)
            
            # 如果编译失败，确保智能错误分析结果被包含
            if not sim_result.get("success", False) and "detailed_analysis" in analysis:
                # 将智能分析结果合并到主结果中
                analysis["intelligent_error_analysis"] = True
                
                # 确保suggestions被正确传递
                if "suggestions" in analysis and analysis["suggestions"]:
                    analysis["has_intelligent_suggestions"] = True
            
            # 合并结果
            result = {
                **sim_result,
                **analysis,
                "testbench_path": testbench_path,
                "design_files": design_file_paths,
                "compilation_files": compilation_files,
                "dependency_analysis": dependency_analysis
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 测试执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"测试执行异常: {str(e)}",
                "all_tests_passed": False
            }
    
    async def _analyze_dependencies(self, design_file_paths: List[str], testbench_path: str) -> Dict[str, Any]:
        """分析Verilog文件依赖关系"""
        try:
            self.logger.info("🔍 开始Verilog依赖分析...")
            
            # 分析所有相关文件
            all_files = design_file_paths + [testbench_path]
            
            for file_path in all_files:
                self.dependency_analyzer.analyze_file(file_path)
            
            # 检查兼容性
            if len(design_file_paths) == 1:
                compatibility = self.dependency_analyzer.analyze_compatibility(
                    design_file_paths[0], testbench_path
                )
                
                self.logger.info(f"📊 兼容性分析: 兼容={compatibility['compatible']}")
                if compatibility["issues"]:
                    for issue in compatibility["issues"]:
                        self.logger.warning(f"⚠️ 兼容性问题: {issue}")
                
                # 获取修复建议
                suggestions = self.dependency_analyzer.suggest_fixes(compatibility)
                
                # 如果有缺失的依赖，尝试从文件管理器中查找
                missing_deps = compatibility.get("missing_dependencies", [])
                additional_files = []
                
                if missing_deps:
                    self.logger.info(f"🔍 查找缺失的依赖模块: {missing_deps}")
                    additional_files = await self._find_missing_dependencies(missing_deps)
                
                # 确定最终的编译文件列表
                compilation_files = design_file_paths + additional_files
                
                return {
                    "success": True,
                    "compatible": compatibility["compatible"],
                    "issues": compatibility["issues"],
                    "suggestions": suggestions,
                    "missing_dependencies": missing_deps,
                    "additional_files": additional_files,
                    "compilation_files": compilation_files,
                    "design_modules": compatibility.get("design_modules", []),
                    "testbench_modules": compatibility.get("testbench_modules", [])
                }
            else:
                # 多个设计文件的情况
                self.logger.warning("⚠️ 多个设计文件，跳过详细兼容性分析")
                return {
                    "success": True,
                    "compatible": True,
                    "issues": ["多个设计文件，未进行详细兼容性分析"],
                    "suggestions": [],
                    "compilation_files": design_file_paths
                }
                
        except Exception as e:
            self.logger.error(f"❌ 依赖分析异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "compilation_files": design_file_paths
            }
    
    async def _find_missing_dependencies(self, missing_modules: List[str]) -> List[str]:
        """智能搜索缺失的依赖模块（增强版）"""
        additional_files = []
        
        try:
            from core.file_manager import get_file_manager
            file_manager = get_file_manager()
            
            # 🎯 策略1：从文件管理器获取所有相关文件
            all_verilog_files = file_manager.get_files_by_type("verilog")
            
            # 🎯 策略2：智能模块匹配，支持多种命名模式
            for missing_module in missing_modules:
                self.logger.info(f"🔍 智能搜索缺失模块: {missing_module}")
                found = False
                
                # 按优先级搜索
                search_patterns = [
                    missing_module.lower(),                    # 完全匹配
                    f"{missing_module.lower()}.v",            # 带扩展名
                    f"{missing_module.lower()}_module",       # 后缀模式
                    f"module_{missing_module.lower()}",       # 前缀模式
                ]
                
                for file_ref in all_verilog_files:
                    if found:
                        break
                        
                    file_path = file_ref.file_path
                    filename = Path(file_path).stem.lower()
                    
                    # 模式匹配
                    for pattern in search_patterns:
                        if pattern in filename or filename in pattern:
                            # 🔍 深度验证：检查文件内容是否真的包含该模块
                            if self._verify_module_in_file(file_path, missing_module):
                                if file_path not in additional_files:
                                    additional_files.append(file_path)
                                    self.logger.info(f"✅ 找到依赖文件: {Path(file_path).name} (匹配模式: {pattern})")
                                    found = True
                                    break
                
                if not found:
                    # 🎯 策略3：内容搜索作为最后手段
                    self.logger.warning(f"⚠️ 文件名匹配失败，尝试内容搜索: {missing_module}")
                    content_match_file = await self._search_module_in_content(missing_module, all_verilog_files)
                    if content_match_file and content_match_file not in additional_files:
                        additional_files.append(content_match_file)
                        self.logger.info(f"✅ 通过内容搜索找到: {Path(content_match_file).name}")
            
            # 🎯 策略4：依赖顺序优化
            if additional_files:
                # 使用依赖分析器确定正确的编译顺序
                ordered_files = self._optimize_compilation_order(additional_files)
                self.logger.info(f"🔄 优化编译顺序，文件数: {len(ordered_files)}")
                return ordered_files
            
        except Exception as e:
            self.logger.error(f"❌ 搜索依赖模块时出错: {str(e)}")
        
        return additional_files
    
    def _verify_module_in_file(self, file_path: str, module_name: str) -> bool:
        """验证文件中是否真正包含指定模块"""
        try:
            if not Path(file_path).exists():
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找模块定义
            module_pattern = rf'module\s+{re.escape(module_name)}\s*[\(;]'
            return bool(re.search(module_pattern, content, re.IGNORECASE))
            
        except Exception as e:
            self.logger.debug(f"验证模块时出错 {file_path}: {e}")
            return False
    
    async def _search_module_in_content(self, module_name: str, verilog_files: List) -> Optional[str]:
        """在文件内容中搜索模块定义"""
        for file_ref in verilog_files:
            if self._verify_module_in_file(file_ref.file_path, module_name):
                return file_ref.file_path
        return None
    
    def _optimize_compilation_order(self, file_list: List[str]) -> List[str]:
        """使用依赖分析器优化编译顺序"""
        try:
            # 分析所有文件的依赖关系
            for file_path in file_list:
                self.dependency_analyzer.analyze_file(file_path)
            
            # 查找顶层模块
            top_modules = self.dependency_analyzer.find_top_level_modules(exclude_testbenches=True)
            
            if top_modules:
                # 为每个顶层模块生成编译顺序
                all_ordered_files = []
                for top_module in top_modules:
                    ordered = self.dependency_analyzer.generate_compilation_order(top_module)
                    all_ordered_files.extend(ordered)
                
                # 去重并保持顺序
                seen = set()
                final_order = []
                for file_path in all_ordered_files:
                    if file_path not in seen and file_path in file_list:
                        seen.add(file_path)
                        final_order.append(file_path)
                
                # 添加剩余文件
                for file_path in file_list:
                    if file_path not in seen:
                        final_order.append(file_path)
                
                return final_order
            
        except Exception as e:
            self.logger.debug(f"编译顺序优化失败: {e}")
        
        # 回退到原始顺序
        return file_list
    
    def _extract_file_paths(self, design_files: List[Any]) -> List[str]:
        """提取设计文件路径 - 增强错误处理和文件搜索"""
        paths = []
        
        self.logger.debug(f"🔍 提取文件路径，输入类型: {type(design_files)}, 长度: {len(design_files) if design_files else 0}")
        
        if not design_files:
            self.logger.error("❌ design_files为空，无法继续执行")
            return []
        
        for i, file_ref in enumerate(design_files):
            self.logger.info(f"🔍 处理文件引用 {i}: {type(file_ref)} = {file_ref}")
            
            path = None
            
            # 处理不同类型的文件引用
            if isinstance(file_ref, dict):
                # 字典格式：{"file_path": "...", "file_type": "...", ...}
                path = (file_ref.get("file_path") or 
                       file_ref.get("path") or 
                       (file_ref.get("result", {}).get("file_path") if isinstance(file_ref.get("result"), dict) else None))
                self.logger.info(f"  字典格式，提取路径: {path}")
                
            elif hasattr(file_ref, 'path'):
                # FileReference对象的path属性
                path = str(file_ref.path)
                self.logger.info(f"  FileReference对象，path属性: {path}")
                
            elif hasattr(file_ref, 'file_path'):
                # 其他对象的file_path属性 
                path = str(file_ref.file_path)
                self.logger.info(f"  其他对象，file_path属性: {path}")
                
            elif isinstance(file_ref, (str, Path)):
                # 直接的路径字符串或Path对象
                path = str(file_ref)
                self.logger.info(f"  直接路径: {path}")
                
            else:
                self.logger.warning(f"⚠️ 未知文件引用类型: {type(file_ref)}")
                # 尝试将对象转换为字符串，看是否包含路径信息
                str_repr = str(file_ref)
                if '.v' in str_repr or '.sv' in str_repr:
                    # 尝试从字符串表示中提取路径
                    import re
                    path_matches = re.findall(r'[^\s]+\.s?v', str_repr)
                    if path_matches:
                        path = path_matches[0]
                        self.logger.info(f"  从字符串表示中提取路径: {path}")
                continue
            
            if path:
                self.logger.info(f"  📁 检查路径: {path}")
                # 检查文件是否存在且是Verilog文件
                path_obj = Path(path)
                if path_obj.exists():
                    self.logger.info(f"  ✅ 文件存在: {path}")
                    # 只处理.v和.sv文件（Verilog和SystemVerilog）
                    if path.endswith(('.v', '.sv')):
                        resolved_path = str(path_obj.resolve())
                        paths.append(resolved_path)
                        self.logger.info(f"  ✅ 添加Verilog文件: {resolved_path}")
                    else:
                        self.logger.info(f"  ⏭️ 跳过非Verilog文件: {path}")
                else:
                    self.logger.warning(f"⚠️ 文件不存在: {path}")
                    # 尝试在常见目录中搜索同名文件
                    found_path = self._search_file_in_common_dirs(Path(path).name)
                    if found_path:
                        paths.append(found_path)
                        self.logger.info(f"  🔍 在备用位置找到文件: {found_path}")
            else:
                self.logger.warning(f"  ⚠️ 无法提取路径信息")
        
        # 如果仍然没有找到文件，记录错误但不搜索工作目录
        if not paths:
            self.logger.error("❌ 未找到任何有效的设计文件")
        
        self.logger.info(f"📄 成功提取设计文件路径: {len(paths)} 个文件")
        for i, path in enumerate(paths):
            self.logger.info(f"  {i+1}. {path}")
        
        # 🧹 代码清理：检查并修复设计文件中的格式问题
        cleaned_paths = self._clean_design_files(paths)
        
        return cleaned_paths
    

    def _search_verilog_files_in_working_dir(self) -> List[str]:
        """在工作目录中搜索Verilog文件"""
        paths = []
        search_dirs = [
            Path.cwd(),
            Path.cwd() / "artifacts",
            Path.cwd() / "logs" / "experiment_files",
            Path.cwd() / "design_files"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for verilog_file in search_dir.glob("*.v"):
                    if verilog_file.is_file() and not verilog_file.name.endswith("_tb.v"):
                        paths.append(str(verilog_file.resolve()))
                        self.logger.info(f"🔍 发现设计文件: {verilog_file}")
                        
                for sv_file in search_dir.glob("*.sv"):
                    if sv_file.is_file() and not sv_file.name.endswith("_tb.sv"):
                        paths.append(str(sv_file.resolve()))
                        self.logger.info(f"🔍 发现SystemVerilog设计文件: {sv_file}")
        
        return paths
    
    def _search_file_in_common_dirs(self, filename: str) -> Optional[str]:
        """在常见目录中搜索文件"""
        search_dirs = [
            Path.cwd(),
            Path.cwd() / "artifacts", 
            Path.cwd() / "logs" / "experiment_files",
            Path.cwd() / "design_files"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                file_path = search_dir / filename
                if file_path.exists():
                    return str(file_path.resolve())
        
        return None
    
    async def _run_simulation(self, design_files: List[str], 
                            testbench_path: str) -> Dict[str, Any]:
        """运行仿真"""
        try:
            self.logger.info(f"🧪 开始仿真，设计文件: {len(design_files)} 个")
            self.logger.info(f"🧪 测试台文件: {testbench_path}")
            
            # 详细验证和记录每个文件
            all_files = design_files + [testbench_path]
            missing_files = []
            valid_design_files = []
            
            self.logger.info("📋 验证文件存在性:")
            for i, file_path in enumerate(design_files):
                filename = Path(file_path).name
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    self.logger.info(f"  ✅ 设计文件{i+1}: {filename} ({file_size} bytes)")
                    valid_design_files.append(file_path)
                else:
                    self.logger.error(f"  ❌ 设计文件{i+1}不存在: {filename}")
                    missing_files.append(file_path)
            
            # 验证测试台文件
            if Path(testbench_path).exists():
                tb_size = Path(testbench_path).stat().st_size
                tb_filename = Path(testbench_path).name
                self.logger.info(f"  ✅ 测试台文件: {tb_filename} ({tb_size} bytes)")
            else:
                self.logger.error(f"  ❌ 测试台文件不存在: {Path(testbench_path).name}")
                missing_files.append(testbench_path)
            
            if missing_files:
                return {
                    "success": False,
                    "stage": "file_validation",
                    "error": f"发现 {len(missing_files)} 个缺失文件: {[Path(f).name for f in missing_files]}",
                    "missing_files": missing_files,
                    "valid_files": valid_design_files
                }
            
            # 检查是否有重复或冲突的文件
            if len(valid_design_files) > 1:
                self.logger.warning(f"⚠️ 发现多个设计文件，这可能导致模块冲突:")
                for f in valid_design_files:
                    self.logger.warning(f"    - {Path(f).name}")
            
            # 创建临时输出文件
            timestamp = int(asyncio.get_event_loop().time())
            output_file = self.temp_dir / f"sim_{timestamp}"
            
            self.logger.info(f"📁 临时仿真输出: {output_file}")
            
            # 智能构建编译命令 - 确保文件顺序正确
            cmd = ["iverilog", "-o", str(output_file)]
            
            # 首先添加设计文件（按字母顺序，确保一致性）
            sorted_design_files = sorted(valid_design_files, key=lambda x: Path(x).name)
            cmd.extend(sorted_design_files)
            
            # 最后添加测试台文件
            cmd.append(testbench_path)
            
            self.logger.info(f"🔨 编译命令文件顺序:")
            for i, file_path in enumerate(sorted_design_files + [testbench_path]):
                file_type = "测试台" if file_path == testbench_path else "设计"
                self.logger.info(f"  {i+1}. {Path(file_path).name} ({file_type})")
            
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
                # 解析编译错误，提取文件名和行号
                error_details = self._parse_compiler_errors(compile_stderr_str)
                return {
                    "success": False,
                    "stage": "compilation",
                    "compile_stdout": compile_stdout_str,
                    "compile_stderr": compile_stderr_str,
                    "command": ' '.join(cmd),
                    "returncode": compile_process.returncode,
                    "error_details": error_details,
                    "precise_errors": error_details.get("precise_errors", [])
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
                    self.logger.info(f"📤 仿真stdout: {sim_stdout_str}")  # 截断长输出
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
        """分析编译错误 - 增强对依赖问题的理解"""
        stderr = sim_result.get("compile_stderr", "")
        
        analysis = {
            "test_summary": "❌ 编译失败",
            "failure_reasons": [],
            "suggestions": [],
            "error_category": "unknown",
            "detailed_analysis": {}
        }
        
        # 🔍 调试日志：分析编译错误
        self.logger.info(f"🔍 DEBUG: 分析编译错误，stderr长度: {len(stderr)}")
        if stderr:
            self.logger.info(f"🔍 DEBUG: stderr内容: {stderr[:300]}...")
        
        # 增强的错误模式匹配
        error_patterns = {
            r"No top level modules": {
                "type": "缺少顶层模块",
                "category": "dependency_issue",
                "priority": "high"
            },
            r"syntax error": {
                "type": "语法错误", 
                "category": "syntax_issue",
                "priority": "medium"
            },
            r"undeclared identifier": {
                "type": "未声明的标识符",
                "category": "declaration_issue", 
                "priority": "medium"
            },
            r"port.*not.*port|port.*not found": {
                "type": "端口不匹配",
                "category": "interface_issue",
                "priority": "high"
            },
            r"module.*not found": {
                "type": "模块未找到",
                "category": "dependency_issue",
                "priority": "high"
            }
        }
        
        # 分析错误类型
        detected_errors = []
        for pattern, error_info in error_patterns.items():
            if re.search(pattern, stderr, re.IGNORECASE):
                detected_errors.append(error_info)
                analysis["failure_reasons"].append(error_info["type"])
                # 🔍 调试日志：匹配到的错误模式
                self.logger.info(f"🔍 DEBUG: 匹配错误模式: {pattern} -> {error_info['type']}")
        
        # 根据检测到的错误确定类别
        if detected_errors:
            # 按优先级排序，选择最重要的错误类别
            detected_errors.sort(key=lambda x: x["priority"] == "high", reverse=True)
            analysis["error_category"] = detected_errors[0]["category"]
        
        # 生成智能建议
        analysis["suggestions"] = self._generate_intelligent_suggestions(
            analysis["failure_reasons"], 
            analysis["error_category"],
            stderr
        )
        
        # 详细分析
        analysis["detailed_analysis"] = self._perform_detailed_error_analysis(stderr)
        
        return analysis
    
    def _generate_intelligent_suggestions(self, failure_reasons: List[str], 
                                        error_category: str, stderr: str) -> List[str]:
        """生成智能修复建议"""
        suggestions = []
        
        if "缺少顶层模块" in failure_reasons:
            suggestions.extend([
                "🔍 检查是否缺少子模块定义（如full_adder等）",
                "🔧 确保所有被实例化的模块都有对应的模块定义",
                "📁 验证所有依赖文件都已包含在编译命令中",
                "🎯 使用iverilog的-s选项明确指定顶层模块"
            ])
            
            # 从stderr中提取可能的模块名
            module_matches = re.findall(r'(\w+)\s+\w+\s*\([^)]*\)\s*;', stderr)
            if module_matches:
                unique_modules = list(set(module_matches))
                suggestions.append(f"💡 可能缺少的模块定义: {', '.join(unique_modules[:3])}")
        
        if "语法错误" in failure_reasons:
            suggestions.extend([
                "📝 检查Verilog语法：分号、括号、关键字拼写等",
                "🔤 验证标识符命名规则和保留字使用"
            ])
        
        if "未声明的标识符" in failure_reasons:
            suggestions.extend([
                "📋 检查信号声明：确保所有使用的信号都已声明",
                "🔍 验证变量作用域和可见性"
            ])
        
        if "端口不匹配" in failure_reasons:
            suggestions.extend([
                "🔌 检查模块实例化：确保端口名称和数量匹配",
                "📊 验证端口类型和位宽兼容性"
            ])
        
        if "模块未找到" in failure_reasons:
            suggestions.extend([
                "📂 检查模块名称：确保设计文件中的模块名与测试台中一致",
                "🔗 验证模块文件路径和包含关系"
            ])
        
        # 基于错误类别的建议
        if error_category == "dependency_issue":
            suggestions.append("🔍 建议运行依赖分析以识别缺失的模块文件")
        
        return suggestions
    
    def _extract_condensed_error_info(self, stderr: str) -> Dict[str, Any]:
        """提取并精简错误信息"""
        condensed = {
            "key_errors": [],
            "error_count_by_type": {},
            "critical_files": [],
            "summary": ""
        }
        
        if not stderr:
            return condensed
        
        # 按行分割错误信息
        error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
        
        # 提取关键错误（前10个最重要的）
        key_errors = []
        error_types = {}
        critical_files = set()
        
        for line in error_lines:
            # 跳过重复的错误信息
            if any(skip in line.lower() for skip in ['it was declared here', 'error: malformed statement']):
                continue
            
            # 提取文件名和错误类型
            file_match = re.search(r'([^\s]+\.s?v):(\d+):', line)
            if file_match:
                file_path, line_num = file_match.groups()
                critical_files.add(Path(file_path).name)
            
            # 分类错误类型
            if 'syntax error' in line.lower():
                error_types['语法错误'] = error_types.get('语法错误', 0) + 1
                if len(key_errors) < 5:  # 只保留前5个语法错误
                    key_errors.append(line)
            elif 'undeclared' in line.lower():
                error_types['未声明标识符'] = error_types.get('未声明标识符', 0) + 1
                if len(key_errors) < 8:
                    key_errors.append(line)
            elif 'port' in line.lower() and 'not' in line.lower():
                error_types['端口错误'] = error_types.get('端口错误', 0) + 1
                if len(key_errors) < 10:
                    key_errors.append(line)
        
        condensed["key_errors"] = key_errors[:10]  # 最多10个关键错误
        condensed["error_count_by_type"] = error_types
        condensed["critical_files"] = list(critical_files)[:5]  # 最多5个文件
        
        # 生成摘要
        if error_types:
            summary_parts = []
            for error_type, count in error_types.items():
                summary_parts.append(f"{error_type}({count}个)")
            condensed["summary"] = f"主要错误: {', '.join(summary_parts)}"
        
        return condensed
    
    def _generate_focused_suggestions(self, failure_reasons: List[str], 
                                    error_category: str, 
                                    condensed_errors: Dict[str, Any]) -> List[str]:
        """生成精准的修复建议"""
        suggestions = []
        
        # 基于错误类型的具体建议
        error_counts = condensed_errors.get("error_count_by_type", {})
        
        if "语法错误" in error_counts:
            count = error_counts["语法错误"]
            suggestions.append(f"🔧 修复{count}个语法错误：检查分号、括号匹配、关键字拼写")
            
            # 从关键错误中提取具体的行号信息
            syntax_errors = [e for e in condensed_errors.get("key_errors", []) 
                           if "syntax error" in e.lower()]
            if syntax_errors:
                first_error = syntax_errors[0]
                line_match = re.search(r':(\d+):', first_error)
                if line_match:
                    line_num = line_match.group(1)
                    suggestions.append(f"📍 从第{line_num}行开始检查语法问题")
        
        if "端口错误" in error_counts:
            count = error_counts["端口错误"]
            suggestions.append(f"🔌 修复{count}个端口连接错误：检查模块实例化和端口名称")
        
        if "未声明标识符" in error_counts:
            count = error_counts["未声明标识符"]
            suggestions.append(f"📋 修复{count}个未声明变量：添加信号声明语句")
        
        # 基于错误类别的策略建议
        if error_category == "dependency_issue":
            suggestions.append("🔍 检查模块依赖：确保所有子模块都已定义")
        elif error_category == "syntax_issue":
            suggestions.append("📝 推荐：使用Verilog语法检查器验证代码")
        elif error_category == "interface_issue":
            suggestions.append("🔌 推荐：检查模块端口定义与测试台实例化是否匹配")
        
        # 基于涉及的文件数量给出建议
        critical_files = condensed_errors.get("critical_files", [])
        if len(critical_files) > 1:
            file_names = ", ".join(critical_files[:3])
            suggestions.append(f"📂 涉及多个文件的错误，重点检查: {file_names}")
        
        return suggestions[:5]  # 限制建议数量为5个
    
    def _perform_detailed_error_analysis(self, stderr: str) -> Dict[str, Any]:
        """执行详细的错误分析"""
        analysis = {
            "error_lines": [],
            "module_references": [],
            "file_references": [],
            "suggestions_context": {}
        }
        
        # 提取错误行
        error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
        analysis["error_lines"] = error_lines[:10]  # 保留前10行错误
        
        # 提取模块引用
        module_pattern = r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;'
        modules = re.findall(module_pattern, stderr)
        analysis["module_references"] = list(set([m[0] for m in modules]))
        
        # 提取文件引用
        file_pattern = r'([^\s]+\.s?v):'
        files = re.findall(file_pattern, stderr)
        analysis["file_references"] = list(set(files))
        
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
        """分析测试失败并生成改进建议 - 增强错误处理"""
        suggestions = []
        
        # 检查测试是否成功执行
        if not test_results.get("success", False):
            error_msg = test_results.get("error", "")
            
            # 分析具体的失败原因
            if "没有找到设计文件" in error_msg:
                suggestions.append("确保Verilog设计文件已正确生成并保存")
                suggestions.append("检查文件写入操作是否成功完成")
                suggestions.append("验证设计文件路径是否正确")
            elif "仿真编译失败" in error_msg or "编译错误" in error_msg:
                # 检查具体的编译错误信息
                compile_stderr = test_results.get("compile_stderr", "")
                if "rst_n" in compile_stderr and "not a port" in compile_stderr:
                    suggestions.append("❌ 关键错误：模块接口定义错误 - rst_n端口不存在")
                    suggestions.append("🔧 修复方案：将模块中的'rst'端口改为'rst_n'（负电平异步复位）")
                    suggestions.append("⚠️ 确保复位逻辑使用negedge rst_n和!rst_n条件")
                elif "port" in compile_stderr and "not a port" in compile_stderr:
                    suggestions.append("❌ 端口不匹配错误：检查模块端口定义与测试台实例化")
                    suggestions.append("🔧 仔细比对模块声明和测试台连接的端口名称")
                else:
                    suggestions.append("修复Verilog代码中的语法错误")
                    suggestions.append("检查模块端口定义是否与测试台匹配")
                    suggestions.append("确保所有信号都已正确声明")
            elif "仿真执行失败" in error_msg:
                suggestions.append("检查测试台与设计模块的连接")
                suggestions.append("验证时钟和复位信号的正确性")
                suggestions.append("确保测试激励的完整性")
            elif "测试执行异常" in error_msg:
                suggestions.append("检查系统环境和仿真工具配置")
                suggestions.append("确保所有依赖文件都存在")
            else:
                # 通用失败处理
                suggestions.append("检查上一阶段的工具执行结果")
                suggestions.append("确保所有必需的文件都已正确生成")
                suggestions.append("验证设计与测试台的兼容性")
        
        # 基于具体失败原因生成建议
        failure_reasons = test_results.get("failure_reasons", [])
        for reason in failure_reasons:
            if "语法错误" in reason:
                suggestions.append("修复Verilog语法错误")
            elif "端口不匹配" in reason:
                suggestions.append("🔧 检查并修正模块端口定义")
                suggestions.append("📋 确保所有端口名称与测试台完全一致")
            elif "未声明的标识符" in reason:
                suggestions.append("添加缺失的信号声明")
            elif "测试用例失败" in reason:
                suggestions.append("检查设计逻辑，确保满足测试台要求")
        
        # 只在测试实际运行成功但有失败时，才基于测试台信息生成建议
        if (test_results.get("success", False) and 
            not test_results.get("all_tests_passed", False) and
            enhanced_analysis.get("testbench_validation", {}).get("module_info")):
            
            module_info = enhanced_analysis["testbench_validation"]["module_info"] 
            if module_info.get("dut_instances"):
                dut_info = module_info["dut_instances"][0]
                # 只有当模块名是有效的标识符时才添加建议
                module_name = dut_info.get('module', '')
                if module_name and module_name.isidentifier() and not module_name.startswith('_'):
                    suggestions.append(f"确保设计模块名为: {module_name}")
        
        # 去重并过滤无效建议
        suggestions = list(dict.fromkeys(suggestions))  # 去重
        suggestions = [s for s in suggestions if s and len(s.strip()) > 5]  # 过滤无效建议
        
        result = {
            "suggestions": suggestions,
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "failure_category": self._categorize_failures(failure_reasons),
            "has_actionable_suggestions": len(suggestions) > 0,
            "test_execution_success": test_results.get("success", False)
        }
        
        # 🔍 调试日志：改进建议分析结果
        self.logger.info(f"🔍 DEBUG: 分析测试失败，生成改进建议")
        self.logger.info(f"🔍 DEBUG: 建议数量: {len(suggestions)}")
        self.logger.info(f"🔍 DEBUG: 失败类别: {result['failure_category']}")
        for i, suggestion in enumerate(suggestions[:3]):
            self.logger.info(f"🔍 DEBUG: 建议{i+1}: {suggestion[:100]}...")
        
        return result
    
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
    
    def _clean_design_files(self, file_paths: List[str]) -> List[str]:
        """清理设计文件中的格式问题，修复log-16.log中发现的根本缺陷"""
        cleaned_paths = []
        
        for original_path in file_paths:
            try:
                path_obj = Path(original_path)
                if not path_obj.exists():
                    self.logger.warning(f"⚠️ 文件不存在，跳过清理: {original_path}")
                    cleaned_paths.append(original_path)
                    continue
                
                # 读取原始文件内容
                with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                
                # 检查是否需要清理
                if self._needs_cleaning(original_content):
                    self.logger.info(f"🧹 发现格式问题，清理文件: {path_obj.name}")
                    
                    # 执行清理
                    cleaned_content = self._clean_verilog_content(original_content)
                    
                    # 创建清理后的文件
                    cleaned_path = self._create_cleaned_file(path_obj, cleaned_content)
                    
                    if cleaned_path:
                        cleaned_paths.append(str(cleaned_path))
                        self.logger.info(f"✅ 文件清理完成: {cleaned_path}")
                    else:
                        cleaned_paths.append(original_path)
                else:
                    # 文件无需清理
                    cleaned_paths.append(original_path)
                    
            except Exception as e:
                self.logger.error(f"❌ 清理文件失败: {original_path}, 错误: {e}")
                cleaned_paths.append(original_path)  # 使用原始文件
        
        return cleaned_paths
    
    def _needs_cleaning(self, content: str) -> bool:
        """检查内容是否需要清理"""
        # 检查是否包含Markdown代码块标记
        if "```verilog" in content or "```" in content:
            return True
        
        # 检查是否包含非Verilog的说明性文字
        problem_patterns = [
            r"以下是.*的.*代码",
            r"符合.*标准",
            r"### 说明：",
            r"### 注意事项：",
            r"模块名称.*：",
            r"输入端口.*：",
            r"输出端口.*：",
            r"实现方式.*：",
        ]
        
        for pattern in problem_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _clean_verilog_content(self, content: str) -> str:
        """清理Verilog内容，移除非Verilog语法"""
        lines = content.split('\n')
        cleaned_lines = []
        in_verilog_block = False
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                if in_verilog_block:
                    cleaned_lines.append('')
                continue
            
            # 检测Verilog代码块开始
            if line.startswith('```verilog'):
                in_verilog_block = True
                continue
            
            # 检测代码块结束
            if line.startswith('```'):
                in_verilog_block = False
                continue
            
            # 如果在Verilog代码块中，或者是有效的Verilog语法，则保留
            if in_verilog_block or self._is_valid_verilog_line(line):
                cleaned_lines.append(line)
            else:
                # 跳过说明性文字
                self.logger.debug(f"跳过非Verilog行: {line[:50]}...")
        
        return '\n'.join(cleaned_lines)
    
    def _is_valid_verilog_line(self, line: str) -> bool:
        """检查是否是有效的Verilog代码行"""
        line = line.strip()
        
        # 空行或注释行
        if not line or line.startswith('//'):
            return True
        
        # Verilog关键字开头的行
        verilog_keywords = [
            'module', 'endmodule', 'input', 'output', 'wire', 'reg',
            'always', 'initial', 'assign', 'if', 'else', 'begin', 'end',
            'for', 'while', 'case', 'endcase', 'function', 'endfunction',
            'task', 'endtask', 'generate', 'endgenerate', 'genvar',
            'parameter', 'localparam', 'integer'
        ]
        
        for keyword in verilog_keywords:
            if line.startswith(keyword):
                return True
        
        # 赋值语句或实例化
        if any(op in line for op in ['=', '<=', '(', ')', ';']):
            return True
        
        # 预处理指令
        if line.startswith('`'):
            return True
        
        return False
    
    def _create_cleaned_file(self, original_path: Path, cleaned_content: str) -> Optional[Path]:
        """创建清理后的文件"""
        try:
            # 生成新的文件名
            stem = original_path.stem
            suffix = original_path.suffix
            new_name = f"{stem}_cleaned{suffix}"
            cleaned_path = original_path.parent / new_name
            
            # 写入清理后的内容
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            # 验证清理后的文件是否有效
            if self._validate_cleaned_file(cleaned_path):
                return cleaned_path
            else:
                self.logger.warning(f"⚠️ 清理后的文件验证失败: {cleaned_path}")
                cleaned_path.unlink()  # 删除无效文件
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 创建清理文件失败: {e}")
            return None
    
    def _validate_cleaned_file(self, file_path: Path) -> bool:
        """验证清理后的文件是否有效"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本检查：必须包含module和endmodule
            if 'module ' not in content or 'endmodule' not in content:
                return False
            
            # 检查是否还有Markdown残留
            if '```' in content or '###' in content:
                return False
            
            # 检查是否有基本的Verilog结构
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if len(lines) < 3:  # 至少要有module声明、一些内容、endmodule
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 验证文件失败: {e}")
            return False
    
    async def _check_design_files_separately(self, design_files: List[str]) -> Dict[str, Any]:
        """独立检查设计文件"""
        self.logger.info(f"🔍 独立检查设计文件 ({len(design_files)} 个)...")
        
        check_result = {
            "valid": True,
            "files_checked": len(design_files),
            "syntax_errors": [],
            "modules_found": [],
            "compilation_errors": [],
            "critical_issues": []
        }
        
        try:
            for design_file in design_files:
                self.logger.info(f"  🔍 检查设计文件: {Path(design_file).name}")
                
                # 基本语法检查
                syntax_check = await self._basic_syntax_check_file(design_file)
                if not syntax_check["valid"]:
                    check_result["syntax_errors"].extend(syntax_check["errors"])
                    check_result["valid"] = False
                
                # 模块提取
                modules = self._extract_modules_from_file(design_file)
                check_result["modules_found"].extend(modules)
                
                # 独立编译检查
                compile_check = await self._compile_single_file(design_file)
                if not compile_check["success"]:
                    check_result["compilation_errors"].extend(compile_check["errors"])
                    if compile_check.get("critical", False):
                        check_result["critical_issues"].extend(compile_check["errors"])
                        check_result["valid"] = False
            
            self.logger.info(f"  📊 设计文件检查完成: 有效={check_result['valid']}, 模块数={len(check_result['modules_found'])}")
            return check_result
            
        except Exception as e:
            self.logger.error(f"❌ 设计文件检查异常: {str(e)}")
            check_result["valid"] = False
            check_result["critical_issues"].append(f"检查异常: {str(e)}")
            return check_result
    
    async def _check_testbench_file_separately(self, testbench_path: str) -> Dict[str, Any]:
        """独立检查测试台文件"""
        self.logger.info(f"🔍 独立检查测试台文件: {Path(testbench_path).name}")
        
        check_result = {
            "valid": True,
            "syntax_errors": [],
            "modules_found": [],
            "dut_instances": [],
            "compilation_errors": [],
            "critical_issues": []
        }
        
        try:
            # 基本语法检查
            syntax_check = await self._basic_syntax_check_file(testbench_path)
            if not syntax_check["valid"]:
                check_result["syntax_errors"].extend(syntax_check["errors"])
                check_result["valid"] = False
            
            # 模块和DUT实例提取
            modules = self._extract_modules_from_file(testbench_path)
            check_result["modules_found"].extend(modules)
            
            dut_instances = self._extract_dut_instances_from_file(testbench_path)
            check_result["dut_instances"].extend(dut_instances)
            
            # 测试台独立编译检查（忽略外部模块引用）
            compile_check = await self._compile_testbench_only(testbench_path)
            if not compile_check["success"]:
                # 过滤掉外部模块引用错误
                filtered_errors = self._filter_testbench_errors(compile_check["errors"])
                check_result["compilation_errors"].extend(filtered_errors)
                
                # 只有严重的语法错误才标记为无效
                critical_errors = [e for e in filtered_errors if "syntax" in e.lower()]
                if critical_errors:
                    check_result["critical_issues"].extend(critical_errors)
                    check_result["valid"] = False
            
            self.logger.info(f"  📊 测试台检查完成: 有效={check_result['valid']}, DUT实例数={len(check_result['dut_instances'])}")
            return check_result
            
        except Exception as e:
            self.logger.error(f"❌ 测试台文件检查异常: {str(e)}")
            check_result["valid"] = False
            check_result["critical_issues"].append(f"检查异常: {str(e)}")
            return check_result
    
    async def _basic_syntax_check_file(self, file_path: str) -> Dict[str, Any]:
        """对单个文件进行基本语法检查"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            errors = []
            
            # 检查基本结构
            if not re.search(r'module\s+\w+', content):
                errors.append("缺少module声明")
            
            if "endmodule" not in content:
                errors.append("缺少endmodule")
            
            # 检查括号匹配
            if content.count('(') != content.count(')'):
                errors.append("括号不匹配")
            
            # 检查begin/end匹配
            begin_count = len(re.findall(r'\bbegin\b', content))
            end_count = len(re.findall(r'\bend\b', content))
            if begin_count != end_count:
                errors.append(f"begin/end不匹配 (begin: {begin_count}, end: {end_count})")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"文件读取错误: {str(e)}"]
            }
    
    def _extract_modules_from_file(self, file_path: str) -> List[str]:
        """从文件中提取模块名称"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modules = []
            module_matches = re.findall(r'module\s+(\w+)', content)
            modules.extend(module_matches)
            
            return modules
            
        except Exception as e:
            self.logger.error(f"提取模块名称失败: {e}")
            return []
    
    def _extract_dut_instances_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """从测试台文件中提取DUT实例"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            instances = []
            # 匹配模块实例化：module_name instance_name (port_connections);
            instance_pattern = r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;'
            matches = re.findall(instance_pattern, content)
            
            for module_name, instance_name in matches:
                # 排除测试台模块自身
                if not any(tb_keyword in module_name.lower() 
                          for tb_keyword in ['tb_', 'test', 'bench']):
                    instances.append({
                        "module": module_name,
                        "instance": instance_name
                    })
            
            return instances
            
        except Exception as e:
            self.logger.error(f"提取DUT实例失败: {e}")
            return []
    
    async def _compile_single_file(self, file_path: str) -> Dict[str, Any]:
        """独立编译单个设计文件"""
        try:
            timestamp = int(asyncio.get_event_loop().time())
            output_file = self.temp_dir / f"design_check_{timestamp}"
            
            # 使用iverilog进行语法检查，不生成可执行文件
            cmd = ["iverilog", "-t", "null", file_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            errors = []
            critical = False
            
            if process.returncode != 0:
                error_lines = [line.strip() for line in stderr_str.split('\n') if line.strip()]
                errors.extend(error_lines)
                
                # 检查是否有严重错误
                for error in error_lines:
                    if any(critical_keyword in error.lower() 
                          for critical_keyword in ['syntax error', 'parse error', 'malformed']):
                        critical = True
                        break
            
            return {
                "success": process.returncode == 0,
                "errors": errors,
                "critical": critical
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [f"编译检查异常: {str(e)}"],
                "critical": True
            }
    
    async def _compile_testbench_only(self, testbench_path: str) -> Dict[str, Any]:
        """仅编译测试台文件（忽略外部模块引用）"""
        try:
            # 对于测试台，我们主要关注语法错误，而不是模块引用错误
            timestamp = int(asyncio.get_event_loop().time())
            
            # 使用iverilog进行语法检查
            cmd = ["iverilog", "-t", "null", testbench_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            errors = []
            if process.returncode != 0:
                error_lines = [line.strip() for line in stderr_str.split('\n') if line.strip()]
                errors.extend(error_lines)
            
            return {
                "success": process.returncode == 0,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [f"测试台编译检查异常: {str(e)}"]
            }
    
    def _filter_testbench_errors(self, errors: List[str]) -> List[str]:
        """过滤测试台错误，移除外部模块引用错误"""
        filtered = []
        
        for error in errors:
            # 跳过外部模块未找到的错误
            if any(skip_keyword in error.lower() 
                  for skip_keyword in ['module', 'not found', 'undeclared']):
                continue
            
            # 保留语法错误和其他严重错误
            if any(keep_keyword in error.lower() 
                  for keep_keyword in ['syntax', 'malformed', 'parse error']):
                filtered.append(error)
        
        return filtered
    
    async def _check_interface_compatibility(self, design_files: List[str], 
                                           testbench_path: str,
                                           design_check: Dict[str, Any],
                                           testbench_check: Dict[str, Any]) -> Dict[str, Any]:
        """检查接口兼容性"""
        self.logger.info("🔍 检查接口兼容性...")
        
        compatibility_result = {
            "compatible": True,
            "issues": [],
            "design_modules": design_check.get("modules_found", []),
            "testbench_modules": testbench_check.get("modules_found", []),
            "dut_instances": testbench_check.get("dut_instances", []),
            "module_matching": {}
        }
        
        try:
            design_modules = design_check.get("modules_found", [])
            dut_instances = testbench_check.get("dut_instances", [])
            
            # 检查DUT实例是否能找到对应的设计模块
            for dut in dut_instances:
                dut_module = dut.get("module", "")
                if dut_module in design_modules:
                    compatibility_result["module_matching"][dut_module] = "found"
                else:
                    compatibility_result["module_matching"][dut_module] = "missing"
                    compatibility_result["issues"].append(
                        f"测试台中的模块 '{dut_module}' 在设计文件中未找到"
                    )
                    compatibility_result["compatible"] = False
            
            # 检查是否有设计模块但没有对应的测试台实例
            used_modules = [dut.get("module", "") for dut in dut_instances]
            for design_module in design_modules:
                if design_module not in used_modules:
                    compatibility_result["issues"].append(
                        f"设计模块 '{design_module}' 在测试台中未被实例化"
                    )
            
            self.logger.info(f"  📊 兼容性检查完成: 兼容={compatibility_result['compatible']}, 问题数={len(compatibility_result['issues'])}")
            return compatibility_result
            
        except Exception as e:
            self.logger.error(f"❌ 接口兼容性检查异常: {str(e)}")
            compatibility_result["compatible"] = False
            compatibility_result["issues"].append(f"兼容性检查异常: {str(e)}")
            return compatibility_result
    
    def _generate_diagnosis_summary(self, design_check: Dict[str, Any], 
                                  testbench_check: Dict[str, Any],
                                  interface_check: Dict[str, Any]) -> Tuple[str, List[str], bool]:
        """生成诊断摘要和建议"""
        summary_parts = []
        suggestions = []
        should_proceed = True
        
        # 设计文件诊断
        if not design_check.get("valid", True):
            summary_parts.append(f"❌ 设计文件存在{len(design_check.get('critical_issues', []))}个严重问题")
            suggestions.extend([
                "🔧 优先修复设计文件中的语法错误",
                "📝 检查模块定义和endmodule匹配"
            ])
            should_proceed = False
        else:
            summary_parts.append(f"✅ 设计文件语法检查通过（{len(design_check.get('modules_found', []))}个模块）")
        
        # 测试台文件诊断
        if not testbench_check.get("valid", True):
            summary_parts.append(f"❌ 测试台文件存在{len(testbench_check.get('critical_issues', []))}个严重问题")
            suggestions.extend([
                "🔧 修复测试台文件中的语法错误",
                "🔍 检查测试台结构和DUT实例化"
            ])
            should_proceed = False
        else:
            summary_parts.append(f"✅ 测试台文件语法检查通过（{len(testbench_check.get('dut_instances', []))}个DUT实例）")
        
        # 接口兼容性诊断
        if interface_check and not interface_check.get("compatible", True):
            issue_count = len(interface_check.get("issues", []))
            summary_parts.append(f"⚠️ 接口兼容性存在{issue_count}个问题")
            suggestions.extend([
                "🔌 检查模块名称匹配",
                "📋 验证端口连接正确性"
            ])
            # 接口问题不阻止执行，但需要修复
        elif interface_check:
            summary_parts.append("✅ 接口兼容性检查通过")
        
        # 生成具体建议
        if design_check.get("critical_issues"):
            for issue in design_check["critical_issues"][:2]:  # 只显示前2个
                suggestions.append(f"🔧 设计文件: {issue}")
        
        if testbench_check.get("critical_issues"):
            for issue in testbench_check["critical_issues"][:2]:  # 只显示前2个
                suggestions.append(f"🔧 测试台文件: {issue}")
        
        summary = " | ".join(summary_parts)
        
        return summary, suggestions[:5], should_proceed  # 限制建议数量
    
    def _extract_failure_reasons(self, design_check: Dict[str, Any], 
                               testbench_check: Dict[str, Any]) -> List[str]:
        """从诊断结果中提取失败原因"""
        reasons = []
        
        if design_check.get("syntax_errors"):
            reasons.append("设计文件语法错误")
        
        if testbench_check.get("syntax_errors"):
            reasons.append("测试台语法错误")
        
        if design_check.get("critical_issues"):
            reasons.append("设计文件严重问题")
        
        if testbench_check.get("critical_issues"):
            reasons.append("测试台严重问题")
        
        return reasons