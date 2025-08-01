#!/usr/bin/env python3
"""
增强的任务分析功能 - 支持用户指定测试台路径
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class EnhancedTaskAnalyzer:
    """增强的任务分析器，支持测试台路径解析"""
    
    def __init__(self):
        self.testbench_patterns = [
            r'testbench[:\s]+([^\s]+)',
            r'测试台[:\s]+([^\s]+)', 
            r'tb[:\s]+([^\s]+)',
            r'test.*file[:\s]+([^\s]+)',
            r'验证文件[:\s]+([^\s]+)'
        ]
    
    def analyze_enhanced_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析增强任务需求，提取设计要求和测试台信息"""
        
        analysis = {
            "design_requirements": "",
            "testbench_path": None,
            "testbench_required": False,
            "test_driven_development": False,
            "iteration_required": False,
            "validation_criteria": []
        }
        
        # 1. 提取测试台路径
        testbench_path = self._extract_testbench_path(task_description)
        if testbench_path:
            analysis["testbench_path"] = testbench_path
            analysis["testbench_required"] = True
            analysis["test_driven_development"] = True
            analysis["iteration_required"] = True
            
        # 2. 分离设计需求和测试要求
        design_part, test_part = self._separate_design_and_test_requirements(task_description)
        analysis["design_requirements"] = design_part
        
        # 3. 检测是否需要迭代优化
        if any(keyword in task_description.lower() for keyword in [
            "测试失败", "迭代", "优化", "修改", "调试", "fix", "iterate", "optimize"
        ]):
            analysis["iteration_required"] = True
            
        # 4. 提取验证标准
        analysis["validation_criteria"] = self._extract_validation_criteria(test_part)
        
        return analysis
    
    def _extract_testbench_path(self, text: str) -> Optional[str]:
        """提取测试台文件路径"""
        for pattern in self.testbench_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                path = matches[0].strip('"`\'')
                # 验证路径是否存在
                if Path(path).exists():
                    return str(Path(path).resolve())
                else:
                    # 即使路径不存在也返回，可能是相对路径或需要后续处理
                    return path
        return None
    
    def _separate_design_and_test_requirements(self, text: str) -> tuple:
        """分离设计需求和测试需求"""
        # 使用关键词分离
        test_keywords = ["testbench", "测试台", "验证", "仿真", "测试"]
        
        lines = text.split('\n')
        design_lines = []
        test_lines = []
        
        current_section = "design"  # 默认是设计需求
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in test_keywords):
                current_section = "test"
            
            if current_section == "design":
                design_lines.append(line)
            else:
                test_lines.append(line)
        
        return '\n'.join(design_lines).strip(), '\n'.join(test_lines).strip()
    
    def _extract_validation_criteria(self, test_text: str) -> List[str]:
        """提取验证标准"""
        criteria = []
        
        # 查找具体的测试要求
        criteria_patterns = [
            r'必须通过[：:](.+)',
            r'要求[：:](.+)',
            r'验证[：:](.+)',
            r'测试[：:](.+)'
        ]
        
        for pattern in criteria_patterns:
            matches = re.findall(pattern, test_text, re.IGNORECASE)
            criteria.extend([match.strip() for match in matches])
        
        return criteria


# 示例使用
if __name__ == "__main__":
    analyzer = EnhancedTaskAnalyzer()
    
    sample_task = """
    请设计一个32位ALU模块，支持加减法和逻辑运算。
    
    测试要求：
    - 使用提供的测试台: /path/to/alu_testbench.v
    - 必须通过所有测试用例
    - 如果测试失败，请分析原因并迭代修改设计
    """
    
    result = analyzer.analyze_enhanced_task(sample_task)
    print(json.dumps(result, indent=2, ensure_ascii=False))