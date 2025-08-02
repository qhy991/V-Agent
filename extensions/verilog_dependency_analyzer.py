#!/usr/bin/env python3
"""
Verilog依赖关系分析器
解决模块间依赖关系导致的编译问题
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

@dataclass
class VerilogModule:
    """Verilog模块信息"""
    name: str
    file_path: str
    dependencies: Set[str]  # 依赖的其他模块
    is_testbench: bool = False
    ports: List[str] = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []


class VerilogDependencyAnalyzer:
    """Verilog依赖关系分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.VerilogDependencyAnalyzer")
        self.modules: Dict[str, VerilogModule] = {}  # module_name -> VerilogModule
        
    def analyze_file(self, file_path: str) -> List[VerilogModule]:
        """分析单个Verilog文件中的模块"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                self.logger.warning(f"文件不存在: {file_path}")
                return []
            
            content = path_obj.read_text(encoding='utf-8')
            modules = self._extract_modules_from_content(content, file_path)
            
            for module in modules:
                self.modules[module.name] = module
            
            return modules
        except Exception as e:
            self.logger.error(f"分析文件失败 {file_path}: {str(e)}")
            return []
    
    def _extract_modules_from_content(self, content: str, file_path: str) -> List[VerilogModule]:
        """从内容中提取模块信息"""
        modules = []
        
        # 改进的模块定义匹配模式
        # 支持多种模块定义格式
        module_patterns = [
            # 标准格式: module name (...);
            r'module\s+(\w+)\s*\([^)]*\)\s*;',
            # 参数化格式: module name #(...) (...);
            r'module\s+(\w+)\s*#\s*\([^)]*\)\s*\([^)]*\)\s*;',
            # 无端口格式: module name;
            r'module\s+(\w+)\s*;'
        ]
        
        for pattern in module_patterns:
            module_matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in module_matches:
                module_name = match.group(1)
                
                # 跳过已经处理过的模块
                if any(m.name == module_name for m in modules):
                    continue
                
                # 判断是否为测试台
                is_testbench = any(keyword in module_name.lower() 
                                 for keyword in ['tb', 'testbench', 'test'])
                
                # 提取模块内容
                module_start = match.start()
                module_content = self._extract_module_content(content, module_start)
                
                # 分析依赖关系
                dependencies = self._find_dependencies(module_content)
                
                # 提取端口信息
                ports = self._extract_ports(match.group(0), module_content)
                
                module = VerilogModule(
                    name=module_name,
                    file_path=file_path,
                    dependencies=dependencies,
                    is_testbench=is_testbench,
                    ports=ports
                )
                
                modules.append(module)
                self.logger.info(f"发现模块: {module_name} (依赖: {list(dependencies) if dependencies else '无'})")
        
        return modules
    
    def _extract_module_content(self, content: str, start_pos: int) -> str:
        """提取模块的完整内容"""
        # 简单的括号匹配来找到模块结束位置
        lines = content[start_pos:].split('\n')
        module_lines = []
        depth = 0
        in_module = False
        
        for line in lines:
            if 'module' in line and not in_module:
                in_module = True
                depth = 1
            
            if in_module:
                module_lines.append(line)
                
                # 简单的begin/end匹配
                depth += line.count('begin')
                depth -= line.count('end')
                
                if 'endmodule' in line:
                    break
        
        return '\n'.join(module_lines)
    
    def _find_dependencies(self, module_content: str) -> Set[str]:
        """查找模块实例化，确定依赖关系"""
        dependencies = set()
        
        # 预处理：移除注释
        content_lines = []
        for line in module_content.split('\n'):
            # 简单移除单行注释
            if '//' in line:
                line = line[:line.find('//')]
            content_lines.append(line)
        clean_content = '\n'.join(content_lines)
        
        # 多种实例化模式匹配
        instance_patterns = [
            # 标准实例化: module_name instance_name (ports);
            r'(\w+)\s+(\w+)\s*\(\s*\..*?\)\s*;',
            # 位置端口实例化: module_name instance_name (signal1, signal2, ...);
            r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;',
            # 参数化实例化: module_name #(params) instance_name (ports);
            r'(\w+)\s*#\s*\([^)]*\)\s+(\w+)\s*\([^)]*\)\s*;'
        ]
        
        # 过滤掉Verilog内置类型和关键字
        builtin_types = {
            # 数据类型
            'wire', 'reg', 'input', 'output', 'inout', 'logic', 'bit',
            'parameter', 'localparam', 'integer', 'real', 'time', 'realtime',
            'supply0', 'supply1', 'tri', 'triand', 'trior', 'trireg', 'wand', 'wor',
            # 关键字
            'module', 'endmodule', 'always', 'initial', 'assign', 'generate', 'endgenerate',
            'genvar', 'for', 'if', 'else', 'case', 'casex', 'casez', 'default',
            'begin', 'end', 'function', 'task', 'return', 'repeat', 'while',
            # 系统任务和函数
            'display', 'monitor', 'finish', 'stop', 'dumpfile', 'dumpvars'
        }
        
        for pattern in instance_patterns:
            matches = re.finditer(pattern, clean_content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                if match.groups() and len(match.groups()) >= 2:
                    module_name = match.group(1)
                    instance_name = match.group(2)
                    
                    # 严格过滤条件
                    if (module_name not in builtin_types and 
                        not module_name.startswith('$') and  # 系统任务
                        module_name.isidentifier() and  # 有效标识符
                        not module_name.isupper() and  # 避免参数常量
                        len(module_name) > 1 and  # 长度检查
                        module_name != instance_name):  # 模块名不等于实例名
                        
                        dependencies.add(module_name)
                        self.logger.debug(f"  发现依赖: {module_name} (实例: {instance_name})")
        
        return dependencies
    
    def _extract_ports(self, module_declaration: str, module_content: str) -> List[str]:
        """提取模块端口信息"""
        ports = []
        
        # 从模块声明中提取端口
        port_pattern = r'\(\s*([^)]+)\s*\)'
        port_match = re.search(port_pattern, module_declaration)
        
        if port_match:
            port_list = port_match.group(1)
            # 简单分割端口名（忽略复杂的端口声明）
            port_names = [p.strip() for p in port_list.split(',') if p.strip()]
            ports.extend(port_names)
        
        return ports
    
    def resolve_dependencies(self, target_modules: List[str]) -> Tuple[List[str], List[str]]:
        """解析依赖关系，返回编译所需的所有文件"""
        required_files = []
        missing_modules = []
        processed = set()
        
        def resolve_module(module_name: str):
            if module_name in processed:
                return
            
            processed.add(module_name)
            
            if module_name not in self.modules:
                missing_modules.append(module_name)
                self.logger.warning(f"缺失模块: {module_name}")
                return
            
            module = self.modules[module_name]
            
            # 先处理依赖
            for dep in module.dependencies:
                resolve_module(dep)
            
            # 再添加当前模块
            if module.file_path not in required_files:
                required_files.append(module.file_path)
                self.logger.info(f"添加文件: {Path(module.file_path).name} (模块: {module_name})")
        
        # 解析所有目标模块
        for module_name in target_modules:
            resolve_module(module_name)
        
        return required_files, missing_modules
    
    def find_top_level_modules(self, exclude_testbenches: bool = True) -> List[str]:
        """查找顶层模块（没有被其他模块实例化的模块）"""
        all_modules = set(self.modules.keys())
        instantiated_modules = set()
        
        # 收集所有被实例化的模块
        for module in self.modules.values():
            instantiated_modules.update(module.dependencies)
        
        # 顶层模块 = 所有模块 - 被实例化的模块
        top_level = all_modules - instantiated_modules
        
        if exclude_testbenches:
            top_level = {name for name in top_level 
                        if not self.modules[name].is_testbench}
        
        return list(top_level)
    
    def generate_compilation_order(self, target_module: str) -> List[str]:
        """生成编译顺序（依赖优先）"""
        files, missing = self.resolve_dependencies([target_module])
        
        if missing:
            self.logger.warning(f"编译 {target_module} 时发现缺失模块: {missing}")
        
        return files
    
    def analyze_compatibility(self, design_file: str, testbench_file: str) -> Dict[str, any]:
        """分析设计文件和测试台的兼容性"""
        result = {
            "compatible": False,
            "issues": [],
            "design_modules": [],
            "testbench_modules": [],
            "missing_dependencies": []
        }
        
        try:
            # 分析两个文件
            design_modules = self.analyze_file(design_file)
            testbench_modules = self.analyze_file(testbench_file)
            
            result["design_modules"] = [m.name for m in design_modules]
            result["testbench_modules"] = [m.name for m in testbench_modules]
            
            # 查找测试台试图实例化的设计模块
            instantiated_design_modules = set()
            for tb_module in testbench_modules:
                if tb_module.is_testbench:
                    for dep in tb_module.dependencies:
                        if dep in result["design_modules"]:
                            instantiated_design_modules.add(dep)
            
            if not instantiated_design_modules:
                result["issues"].append("测试台没有实例化任何设计模块")
            else:
                result["compatible"] = True
                self.logger.info(f"测试台实例化的设计模块: {instantiated_design_modules}")
            
            # 检查缺失的依赖
            all_files, missing = self.resolve_dependencies(
                result["design_modules"] + result["testbench_modules"]
            )
            result["missing_dependencies"] = missing
            
            if missing:
                result["issues"].append(f"缺失依赖模块: {missing}")
                result["compatible"] = False
            
        except Exception as e:
            result["issues"].append(f"兼容性分析失败: {str(e)}")
        
        return result
    
    def suggest_fixes(self, compatibility_result: Dict[str, any]) -> List[str]:
        """根据兼容性分析结果提供修复建议"""
        suggestions = []
        
        if not compatibility_result["compatible"]:
            for issue in compatibility_result["issues"]:
                if "没有实例化任何设计模块" in issue:
                    suggestions.append("确保测试台中实例化了正确的设计模块")
                    suggestions.append("检查模块名称是否匹配")
                elif "缺失依赖模块" in issue:
                    missing = compatibility_result["missing_dependencies"]
                    suggestions.append(f"需要提供缺失的模块定义: {missing}")
                    suggestions.append("确保所有子模块都在同一文件中或提供单独的文件")
        
        return suggestions