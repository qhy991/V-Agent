#!/usr/bin/env python3
"""
增强任务解析器 - 完全独立的扩展模块
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class EnhancedTaskParser:
    """增强任务解析器 - 专门处理测试驱动任务"""
    
    def __init__(self):
        # 测试台路径识别模式
        self.testbench_patterns = [
            r'testbench[:\s]+([^\s\n]+)',
            r'测试台[:\s]*[：:]?\s*([^\s\n]+)',
            r'tb[:\s]+([^\s\n]+)',
            r'test.*file[:\s]+([^\s\n]+)',
            r'验证文件[:\s]+([^\s\n]+)',
            r'测试文件[:\s]*[：:]?\s*([^\s\n]+)'
        ]
        
        # 测试驱动关键词
        self.tdd_keywords = [
            '测试台', 'testbench', 'tb', '测试文件',
            '测试失败', '迭代', '优化', '修改', '调试',
            'test', 'iterate', 'optimize', 'fix', 'debug',
            '验证', 'verify', 'validation'
        ]
    
    async def parse_enhanced_task(self, task_description: str,
                                testbench_path: str = None,
                                context: Dict[str, Any] = None,
                                force_tdd: bool = False) -> Dict[str, Any]:
        """
        解析增强任务需求
        
        Args:
            force_tdd: 强制作为TDD任务处理（当从execute_test_driven_task调用时）
        
        返回结构：
        {
            "is_test_driven": bool,
            "design_requirements": str,
            "testbench_path": str,
            "test_requirements": str,
            "iteration_required": bool,
            "validation_criteria": List[str],
            "context": Dict[str, Any]
        }
        """
        
        analysis = {
            "is_test_driven": False,
            "design_requirements": task_description,
            "testbench_path": testbench_path,
            "test_requirements": "",
            "iteration_required": False,
            "validation_criteria": [],
            "context": context or {}
        }
        
        # 1. 检测是否为测试驱动任务
        if force_tdd:
            analysis["is_test_driven"] = True
        else:
            analysis["is_test_driven"] = self._is_test_driven_task(
                task_description, testbench_path
            )
        
        if not analysis["is_test_driven"]:
            return analysis
        
        # 2. 提取测试台路径（如果在描述中指定）
        if not testbench_path:
            extracted_path = self._extract_testbench_path(task_description)
            if extracted_path:
                analysis["testbench_path"] = extracted_path
        
        # 3. 分离设计需求和测试需求
        design_part, test_part = self._separate_requirements(task_description)
        analysis["design_requirements"] = design_part
        analysis["test_requirements"] = test_part
        
        # 4. 检测是否需要迭代
        analysis["iteration_required"] = self._detect_iteration_requirement(task_description)
        
        # 5. 提取验证标准
        analysis["validation_criteria"] = self._extract_validation_criteria(test_part)
        
        return analysis
    
    def _is_test_driven_task(self, task_description: str, testbench_path: str = None) -> bool:
        """判断是否为测试驱动任务"""
        # 显式提供测试台路径
        if testbench_path:
            return True
        
        # 任务描述中包含测试台路径
        if self._extract_testbench_path(task_description):
            return True
        
        # 包含测试驱动关键词
        text_lower = task_description.lower()
        keyword_count = sum(1 for keyword in self.tdd_keywords if keyword in text_lower)
        
        # 如果包含2个或更多TDD关键词，认为是测试驱动任务
        return keyword_count >= 2
    
    def _extract_testbench_path(self, text: str) -> Optional[str]:
        """从文本中提取测试台路径"""
        for pattern in self.testbench_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                path = matches[0].strip('"\',`')
                # 简单验证路径格式
                if any(ext in path.lower() for ext in ['.v', '.sv', '.vhd']):
                    return path
        return None
    
    def _separate_requirements(self, text: str) -> Tuple[str, str]:
        """分离设计需求和测试需求"""
        lines = text.split('\n')
        design_lines = []
        test_lines = []
        
        current_section = "design"
        test_section_indicators = [
            '测试', 'test', '验证', 'verify', 'validation',
            'testbench', '测试台', '仿真', 'simulation'
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # 检查是否进入测试需求部分
            if any(indicator in line_lower for indicator in test_section_indicators):
                # 如果这行明显是测试相关的标题或要求
                if any(marker in line for marker in ['要求', '需求', 'requirement', ':']):
                    current_section = "test"
            
            if current_section == "design":
                design_lines.append(line)
            else:
                test_lines.append(line)
        
        # 清理和整理
        design_text = '\n'.join(design_lines).strip()
        test_text = '\n'.join(test_lines).strip()
        
        # 如果测试部分为空，但设计部分包含测试相关内容，进行重新分配
        if not test_text and any(word in design_text.lower() 
                                for word in ['testbench', '测试台', '测试文件']):
            # 简单重新分配：包含测试台路径的行移动到测试需求
            design_lines_filtered = []
            test_lines_extracted = []
            
            for line in design_lines:
                if self._extract_testbench_path(line):
                    test_lines_extracted.append(line)
                else:
                    design_lines_filtered.append(line)
            
            design_text = '\n'.join(design_lines_filtered).strip()
            test_text = '\n'.join(test_lines_extracted).strip()
        
        return design_text, test_text
    
    def _detect_iteration_requirement(self, text: str) -> bool:
        """检测是否需要迭代"""
        iteration_keywords = [
            '迭代', '重复', '循环', '直到', '直至',
            'iterate', 'repeat', 'until', 'loop',
            '失败.*继续', '失败.*修改', '失败.*改进',
            'fail.*continue', 'fail.*modify', 'fail.*improve'
        ]
        
        text_lower = text.lower()
        return any(re.search(keyword, text_lower) for keyword in iteration_keywords)
    
    def _extract_validation_criteria(self, test_text: str) -> List[str]:
        """提取验证标准"""
        if not test_text:
            return []
        
        criteria = []
        
        # 查找明确的要求
        requirement_patterns = [
            r'必须[通过]?[：:](.+)',
            r'要求[：:](.+)',
            r'需要[：:](.+)',
            r'验证[：:](.+)',
            r'确保[：:](.+)',
            r'should\s+(.+)',
            r'must\s+(.+)',
            r'require[sd]?\s+(.+)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, test_text, re.IGNORECASE)
            criteria.extend([match.strip() for match in matches])
        
        # 查找列表形式的要求
        bullet_patterns = [
            r'[-*]\s*(.+)',
            r'\d+\.\s*(.+)'
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, test_text)
            # 过滤掉过长或过短的匹配
            filtered_matches = [match.strip() for match in matches 
                              if 5 <= len(match.strip()) <= 100]
            criteria.extend(filtered_matches)
        
        # 去重并返回
        return list(set(criteria))


class TaskRequirementExtractor:
    """任务需求提取器 - 辅助工具"""
    
    @staticmethod
    def extract_file_references(text: str) -> List[Dict[str, str]]:
        """提取文件引用"""
        file_patterns = [
            r'文件[：:]([^\s\n]+)',
            r'file[：:]([^\s\n]+)',
            r'路径[：:]([^\s\n]+)',
            r'path[：:]([^\s\n]+)'
        ]
        
        references = []
        for pattern in file_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                path = match.strip('"\',`')
                if Path(path).suffix in ['.v', '.sv', '.vhd', '.verilog']:
                    references.append({
                        "type": "verilog",
                        "path": path,
                        "description": f"Verilog文件: {Path(path).name}"
                    })
        
        return references
    
    @staticmethod
    def extract_design_constraints(text: str) -> Dict[str, Any]:
        """提取设计约束"""
        constraints = {
            "timing": [],
            "area": [],
            "power": [],
            "interface": []
        }
        
        # 时序约束
        timing_keywords = ['频率', 'frequency', 'clock', '时钟', 'timing', '时序']
        for keyword in timing_keywords:
            if keyword in text.lower():
                # 提取相关行
                lines = [line.strip() for line in text.split('\n') 
                        if keyword in line.lower()]
                constraints["timing"].extend(lines)
        
        # 接口约束
        interface_keywords = ['端口', 'port', 'interface', '接口', 'signal', '信号']
        for keyword in interface_keywords:
            if keyword in text.lower():
                lines = [line.strip() for line in text.split('\n') 
                        if keyword in line.lower()]
                constraints["interface"].extend(lines)
        
        return constraints