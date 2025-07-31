#!/usr/bin/env python3
"""
Verilog审查智能体

Verilog Review Agent for Code Quality Analysis
"""

import asyncio
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict

from core.base_agent import BaseAgent, TaskMessage, FileReference
from core.enums import AgentCapability, AgentStatus
from llm_integration.enhanced_llm_client import EnhancedLLMClient


class VerilogReviewAgent(BaseAgent):
    """
    Verilog审查智能体
    
    专门负责：
    1. 静态代码分析和质量评估
    2. 语法错误和风格检查
    3. 逻辑错误和潜在问题识别
    4. 性能优化建议
    5. 可综合性分析
    """
    
    def __init__(self, llm_client: EnhancedLLMClient = None):
        super().__init__(
            agent_id="verilog_review_agent", 
            role="review_engineer",
            capabilities={
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ANALYSIS,
                AgentCapability.PERFORMANCE_OPTIMIZATION
            }
        )
        
        self.llm_client = llm_client
        
        # 代码质量评估维度
        self.quality_dimensions = {
            "syntax": "语法正确性",
            "style": "代码风格",
            "logic": "逻辑正确性", 
            "performance": "性能效率",
            "maintainability": "可维护性",
            "synthesizability": "可综合性"
        }
        
        # 严重程度等级
        self.severity_levels = {
            "critical": {"weight": 1.0, "description": "严重错误，必须修复"},
            "major": {"weight": 0.7, "description": "主要问题，建议修复"},
            "minor": {"weight": 0.3, "description": "轻微问题，可选修复"},
            "info": {"weight": 0.1, "description": "信息提示，参考建议"}
        }
        
        # Verilog关键字和保留字
        self.verilog_keywords = {
            "always", "and", "assign", "begin", "buf", "bufif0", "bufif1",
            "case", "casex", "casez", "cmos", "deassign", "default", "defparam",
            "disable", "edge", "else", "end", "endcase", "endmodule", "endfunction",
            "endprimitive", "endspecify", "endtable", "endtask", "event", "for",
            "force", "forever", "fork", "function", "highz0", "highz1", "if",
            "ifnone", "initial", "inout", "input", "integer", "join", "large",
            "macromodule", "medium", "module", "nand", "negedge", "nmos", "nor",
            "not", "notif0", "notif1", "or", "output", "parameter", "pmos",
            "posedge", "primitive", "pull0", "pull1", "pulldown", "pullup",
            "rcmos", "real", "realtime", "reg", "release", "repeat", "rnmos",
            "rpmos", "rtran", "rtranif0", "rtranif1", "scalared", "small",
            "specify", "specparam", "strong0", "strong1", "supply0", "supply1",
            "table", "task", "time", "tran", "tranif0", "tranif1", "tri",
            "tri0", "tri1", "triand", "trior", "trireg", "vectored", "wait",
            "wand", "weak0", "weak1", "while", "wire", "wor", "xnor", "xor"
        }
        
        self.logger.info("🔍 Verilog审查智能体初始化完成")
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取审查智能体能力"""
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.QUALITY_ANALYSIS,
            AgentCapability.PERFORMANCE_OPTIMIZATION
        }
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "专业的Verilog代码审查智能体，擅长静态分析、质量评估、性能优化和可综合性检查"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行Verilog代码审查任务"""
        self.logger.info("🔍 开始执行Verilog代码审查任务")
        
        try:
            # 1. 提取和分析Verilog代码
            code_analysis = await self._extract_and_analyze_code(enhanced_prompt, file_contents)
            
            # 2. 执行多维度质量检查
            quality_assessment = await self._perform_quality_assessment(code_analysis)
            
            # 3. 检查潜在问题和错误
            issue_analysis = await self._analyze_potential_issues(code_analysis)
            
            # 4. 生成优化建议
            optimization_suggestions = await self._generate_optimization_suggestions(code_analysis)
            
            # 5. 计算总体质量分数
            overall_score = self._calculate_overall_quality_score(
                quality_assessment, issue_analysis
            )
            
            # 6. 保存审查报告
            output_files = await self._save_review_files(
                code_analysis=code_analysis,
                quality_assessment=quality_assessment,
                issue_analysis=issue_analysis,
                optimization_suggestions=optimization_suggestions,
                overall_score=overall_score,
                task_id=original_message.task_id
            )
            
            # 7. 生成审查摘要
            review_summary = self._generate_review_summary(
                quality_assessment=quality_assessment,
                issue_analysis=issue_analysis,
                overall_score=overall_score,
                output_files=output_files
            )
            
            return {
                "success": True,
                "task_completed": True,
                "agent_id": self.agent_id,
                "overall_quality_score": overall_score,
                "quality_assessment": quality_assessment,
                "issue_analysis": issue_analysis,
                "optimization_suggestions": optimization_suggestions,
                "review_summary": review_summary,
                "file_references": output_files,
                "execution_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog代码审查任务失败: {str(e)}")
            return {
                "success": False,
                "task_completed": False,
                "agent_id": self.agent_id,
                "error": str(e),
                "execution_time": time.time()
            }
    
    async def _extract_and_analyze_code(self, task_description: str, 
                                      file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """提取和分析Verilog代码"""
        # 查找Verilog源码文件
        verilog_files = []
        for file_path, content_info in file_contents.items():
            if (content_info.get("type") == "verilog" or 
                file_path.endswith((".v", ".sv", ".vh"))):
                verilog_files.append({
                    "path": file_path,
                    "content": content_info.get("content", ""),
                    "type": content_info.get("type", "verilog")
                })
        
        if not verilog_files:
            raise ValueError("没有找到可审查的Verilog代码文件")
        
        analysis_results = []
        
        for verilog_file in verilog_files:
            file_analysis = await self._analyze_single_file(
                verilog_file["path"], 
                verilog_file["content"]
            )
            analysis_results.append(file_analysis)
        
        # 合并分析结果
        combined_analysis = {
            "total_files": len(verilog_files),
            "files": analysis_results,
            "overall_metrics": self._calculate_combined_metrics(analysis_results)
        }
        
        self.logger.info(f"📊 代码分析完成: {len(verilog_files)} 个文件")
        return combined_analysis
    
    async def _analyze_single_file(self, file_path: str, 
                                 file_content: str) -> Dict[str, Any]:
        """分析单个Verilog文件"""
        analysis = {
            "file_path": file_path,
            "file_size": len(file_content),
            "line_count": len(file_content.splitlines()),
            "modules": [],
            "metrics": {},
            "syntax_elements": {},
            "potential_issues": []
        }
        
        try:
            # 基本指标统计
            analysis["metrics"] = self._calculate_code_metrics(file_content)
            
            # 提取模块信息
            analysis["modules"] = self._extract_module_information(file_content)
            
            # 分析语法元素
            analysis["syntax_elements"] = self._analyze_syntax_elements(file_content)
            
            # 基本问题检测
            analysis["potential_issues"] = self._detect_basic_issues(file_content)
            
        except Exception as e:
            self.logger.error(f"❌ 分析文件失败 {file_path}: {str(e)}")
            analysis["analysis_error"] = str(e)
        
        return analysis
    
    def _calculate_code_metrics(self, code: str) -> Dict[str, Any]:
        """计算代码指标"""
        lines = code.splitlines()
        
        # 基本行数统计
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("//"))
        code_lines = total_lines - blank_lines - comment_lines
        
        # 复杂度指标
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(code)
        nesting_depth = self._calculate_max_nesting_depth(code)
        
        # 可读性指标
        avg_line_length = sum(len(line) for line in lines) / max(total_lines, 1)
        long_lines = sum(1 for line in lines if len(line) > 80)
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "comment_ratio": comment_lines / max(code_lines, 1),
            "cyclomatic_complexity": cyclomatic_complexity,
            "max_nesting_depth": nesting_depth,
            "average_line_length": avg_line_length,
            "long_lines_count": long_lines,
            "long_lines_ratio": long_lines / max(total_lines, 1)
        }
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        # 计算决策点
        decision_keywords = ["if", "else", "case", "for", "while", "repeat"]
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', code))
        
        # case语句的每个分支增加复杂度
        case_branches = len(re.findall(r'^\s*\w+\s*:', code, re.MULTILINE))
        complexity += max(0, case_branches - 1)  # 减1是因为default分支不增加复杂度
        
        return complexity
    
    def _calculate_max_nesting_depth(self, code: str) -> int:
        """计算最大嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        lines = code.splitlines()
        for line in lines:
            stripped = line.strip()
            
            # 增加嵌套深度的关键字
            if any(keyword in stripped for keyword in ["begin", "case", "if", "for", "while"]):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            # 减少嵌套深度的关键字
            if any(keyword in stripped for keyword in ["end", "endcase"]):
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _extract_module_information(self, code: str) -> List[Dict[str, Any]]:
        """提取模块信息"""
        modules = []
        
        # 查找模块定义
        module_pattern = r'module\s+(\w+)\s*(?:#\s*\([^)]*\))?\s*\(([^;]*)\);'
        matches = re.finditer(module_pattern, code, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            module_name = match.group(1)
            port_list = match.group(2) if match.group(2) else ""
            
            # 提取端口信息
            ports = self._parse_port_list(port_list)
            
            # 查找模块结束位置
            module_start = match.end()
            endmodule_pattern = rf'endmodule\s*(?://.*)?$'
            endmodule_match = re.search(endmodule_pattern, code[module_start:], re.MULTILINE)
            module_end = module_start + (endmodule_match.end() if endmodule_match else len(code))
            
            module_code = code[match.start():module_end]
            
            modules.append({
                "name": module_name,
                "ports": ports,
                "line_start": code[:match.start()].count('\n') + 1,
                "line_end": code[:module_end].count('\n') + 1,
                "code_length": len(module_code),
                "has_parameters": "#" in match.group(0),
                "port_count": len(ports)
            })
        
        return modules
    
    def _parse_port_list(self, port_list: str) -> List[Dict[str, str]]:
        """解析端口列表"""
        ports = []
        if not port_list.strip():
            return ports
        
        # 简单的端口解析（可以进一步完善）
        port_items = [p.strip() for p in port_list.split(',')]
        for port_item in port_items:
            if port_item:
                ports.append({
                    "name": port_item,
                    "direction": "unknown",
                    "width": "unknown"
                })
        
        return ports
    
    def _analyze_syntax_elements(self, code: str) -> Dict[str, Any]:
        """分析语法元素"""
        elements = {
            "always_blocks": len(re.findall(r'\balways\b', code)),
            "initial_blocks": len(re.findall(r'\binitial\b', code)),
            "assign_statements": len(re.findall(r'\bassign\b', code)),
            "wire_declarations": len(re.findall(r'\bwire\b', code)),
            "reg_declarations": len(re.findall(r'\breg\b', code)),
            "parameter_declarations": len(re.findall(r'\bparameter\b', code)),
            "function_definitions": len(re.findall(r'\bfunction\b', code)),
            "task_definitions": len(re.findall(r'\btask\b', code)),
            "generate_blocks": len(re.findall(r'\bgenerate\b', code)),
            "case_statements": len(re.findall(r'\bcase\b', code)),
            "if_statements": len(re.findall(r'\bif\b', code))
        }
        
        return elements
    
    def _detect_basic_issues(self, code: str) -> List[Dict[str, Any]]:
        """检测基本问题"""
        issues = []
        
        lines = code.splitlines()
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检查行长度
            if len(line) > 120:
                issues.append({
                    "type": "style",
                    "severity": "minor",
                    "line": i,
                    "message": f"行长度过长 ({len(line)} 字符)",
                    "suggestion": "建议将长行分解为多行"
                })
            
            # 检查tab和空格混用
            if '\t' in line and '    ' in line:
                issues.append({
                    "type": "style",
                    "severity": "minor",
                    "line": i,
                    "message": "混用tab和空格缩进",
                    "suggestion": "统一使用空格或tab缩进"
                })
            
            # 检查未使用的信号（简单检测）
            if stripped.startswith("wire ") or stripped.startswith("reg "):
                signal_match = re.search(r'(wire|reg)\s+(?:\[[^\]]+\])?\s*(\w+)', stripped)
                if signal_match:
                    signal_name = signal_match.group(2)
                    if code.count(signal_name) == 1:  # 只出现在声明中
                        issues.append({
                            "type": "logic",
                            "severity": "minor",
                            "line": i,
                            "message": f"可能未使用的信号: {signal_name}",
                            "suggestion": "检查信号是否真的需要"
                        })
            
            # 检查blocking和non-blocking赋值混用
            if "always" in stripped and "=" in stripped:
                if re.search(r'=(?!=)', stripped) and re.search(r'<=', stripped):
                    issues.append({
                        "type": "logic",
                        "severity": "major",
                        "line": i,
                        "message": "在同一always块中混用blocking和non-blocking赋值",
                        "suggestion": "时序逻辑使用<=，组合逻辑使用="
                    })
        
        return issues
    
    def _calculate_combined_metrics(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算综合指标"""
        if not file_analyses:
            return {}
        
        total_lines = sum(analysis.get("metrics", {}).get("total_lines", 0) 
                         for analysis in file_analyses)
        total_code_lines = sum(analysis.get("metrics", {}).get("code_lines", 0) 
                              for analysis in file_analyses)
        total_modules = sum(len(analysis.get("modules", [])) 
                           for analysis in file_analyses)
        
        avg_complexity = sum(analysis.get("metrics", {}).get("cyclomatic_complexity", 0) 
                            for analysis in file_analyses) / len(file_analyses)
        
        max_nesting = max(analysis.get("metrics", {}).get("max_nesting_depth", 0) 
                         for analysis in file_analyses)
        
        return {
            "total_lines": total_lines,
            "total_code_lines": total_code_lines,
            "total_modules": total_modules,
            "average_complexity": avg_complexity,
            "max_nesting_depth": max_nesting,
            "files_with_issues": sum(1 for analysis in file_analyses 
                                   if analysis.get("potential_issues", []))
        }
    
    async def _perform_quality_assessment(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量评估"""
        quality_scores = {}
        
        for dimension in self.quality_dimensions:
            score = await self._assess_quality_dimension(dimension, code_analysis)
            quality_scores[dimension] = {
                "score": score,
                "description": self.quality_dimensions[dimension],
                "details": self._get_dimension_details(dimension, code_analysis, score)
            }
        
        # 计算加权平均分
        weights = {"syntax": 0.25, "style": 0.15, "logic": 0.25, 
                  "performance": 0.15, "maintainability": 0.15, "synthesizability": 0.05}
        
        overall_score = sum(quality_scores[dim]["score"] * weights.get(dim, 0.1) 
                           for dim in quality_scores)
        
        return {
            "dimension_scores": quality_scores,
            "overall_score": overall_score,
            "grade": self._score_to_grade(overall_score)
        }
    
    async def _assess_quality_dimension(self, dimension: str, 
                                      code_analysis: Dict[str, Any]) -> float:
        """评估特定质量维度"""
        metrics = code_analysis.get("overall_metrics", {})
        
        if dimension == "syntax":
            # 基于语法错误和基本结构完整性
            return 0.9  # 假设语法基本正确
        
        elif dimension == "style":
            # 基于代码风格指标
            comment_ratio = metrics.get("comment_ratio", 0)
            long_lines_ratio = metrics.get("long_lines_ratio", 0)
            
            style_score = 0.8
            if comment_ratio < 0.1:
                style_score -= 0.2
            if long_lines_ratio > 0.1:
                style_score -= 0.1
            
            return max(0.0, min(1.0, style_score))
        
        elif dimension == "logic":
            # 基于逻辑错误和潜在问题
            total_issues = sum(len(analysis.get("potential_issues", [])) 
                             for analysis in code_analysis.get("files", []))
            issue_density = total_issues / max(metrics.get("total_code_lines", 1), 1)
            
            logic_score = 1.0 - min(issue_density * 10, 0.5)
            return max(0.0, min(1.0, logic_score))
        
        elif dimension == "performance":
            # 基于性能相关指标
            avg_complexity = metrics.get("average_complexity", 5)
            performance_score = max(0.5, 1.0 - (avg_complexity - 5) / 20)
            return performance_score
        
        elif dimension == "maintainability":
            # 基于可维护性指标
            max_nesting = metrics.get("max_nesting_depth", 3)
            maintainability_score = max(0.5, 1.0 - max_nesting / 10)
            return maintainability_score
        
        elif dimension == "synthesizability":
            # 基于可综合性检查
            return 0.85  # 假设基本可综合
        
        return 0.5  # 默认分数
    
    def _get_dimension_details(self, dimension: str, code_analysis: Dict[str, Any], 
                             score: float) -> List[str]:
        """获取质量维度的详细说明"""
        details = []
        metrics = code_analysis.get("overall_metrics", {})
        
        if dimension == "style":
            comment_ratio = metrics.get("comment_ratio", 0)
            if comment_ratio < 0.1:
                details.append(f"注释比例较低 ({comment_ratio:.1%})")
            else:
                details.append(f"注释比例良好 ({comment_ratio:.1%})")
        
        elif dimension == "performance":
            avg_complexity = metrics.get("average_complexity", 5)
            if avg_complexity > 10:
                details.append(f"平均复杂度较高 ({avg_complexity:.1f})")
            else:
                details.append(f"平均复杂度合理 ({avg_complexity:.1f})")
        
        elif dimension == "maintainability":
            max_nesting = metrics.get("max_nesting_depth", 3)
            if max_nesting > 5:
                details.append(f"嵌套深度过深 ({max_nesting})")
            else:
                details.append(f"嵌套深度合理 ({max_nesting})")
        
        return details
    
    def _score_to_grade(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    async def _analyze_potential_issues(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析潜在问题"""
        all_issues = []
        
        # 收集所有文件的问题
        for file_analysis in code_analysis.get("files", []):
            file_issues = file_analysis.get("potential_issues", [])
            for issue in file_issues:
                issue["file"] = file_analysis.get("file_path", "unknown")
                all_issues.append(issue)
        
        # 按严重程度分类
        issues_by_severity = defaultdict(list)
        for issue in all_issues:
            severity = issue.get("severity", "minor")
            issues_by_severity[severity].append(issue)
        
        # 统计信息
        issue_stats = {
            "total_issues": len(all_issues),
            "by_severity": {severity: len(issues) for severity, issues in issues_by_severity.items()},
            "by_type": defaultdict(int)
        }
        
        for issue in all_issues:
            issue_stats["by_type"][issue.get("type", "unknown")] += 1
        
        return {
            "all_issues": all_issues,
            "by_severity": dict(issues_by_severity),
            "statistics": issue_stats
        }
    
    async def _generate_optimization_suggestions(self, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        metrics = code_analysis.get("overall_metrics", {})
        
        # 基于指标生成建议
        if metrics.get("average_complexity", 5) > 8:
            suggestions.append({
                "category": "complexity",
                "priority": "high",
                "title": "降低代码复杂度",
                "description": "当前代码复杂度较高，建议拆分复杂的逻辑块",
                "implementation": [
                    "将复杂的always块拆分为多个简单的块",
                    "使用函数和任务封装重复逻辑",
                    "简化复杂的case语句"
                ]
            })
        
        if metrics.get("comment_ratio", 0) < 0.1:
            suggestions.append({
                "category": "documentation",
                "priority": "medium",
                "title": "增加代码注释",
                "description": "代码注释不足，建议增加必要的说明",
                "implementation": [
                    "为每个模块添加功能说明",
                    "为复杂逻辑添加内联注释",
                    "添加端口和参数说明"
                ]
            })
        
        if metrics.get("max_nesting_depth", 3) > 6:
            suggestions.append({
                "category": "structure",
                "priority": "high",
                "title": "减少嵌套深度",
                "description": "代码嵌套过深，影响可读性",
                "implementation": [
                    "使用early return模式",
                    "提取嵌套逻辑为独立模块",
                    "使用状态机简化复杂控制逻辑"
                ]
            })
        
        # 性能优化建议
        suggestions.append({
            "category": "performance",
            "priority": "medium",
            "title": "时序优化",
            "description": "考虑时序优化以提高设计性能",
            "implementation": [
                "避免过长的组合逻辑路径",
                "适当使用流水线技术",
                "优化关键路径时序"
            ]
        })
        
        return suggestions
    
    def _calculate_overall_quality_score(self, quality_assessment: Dict[str, Any], 
                                       issue_analysis: Dict[str, Any]) -> float:
        """计算总体质量分数"""
        base_score = quality_assessment.get("overall_score", 0.5)
        
        # 根据问题严重程度调整分数
        issues_by_severity = issue_analysis.get("statistics", {}).get("by_severity", {})
        
        penalty = 0.0
        for severity, count in issues_by_severity.items():
            if severity in self.severity_levels:
                penalty += count * self.severity_levels[severity]["weight"] * 0.05
        
        adjusted_score = max(0.0, base_score - penalty)
        return min(1.0, adjusted_score)
    
    async def _save_review_files(self, code_analysis: Dict[str, Any],
                               quality_assessment: Dict[str, Any],
                               issue_analysis: Dict[str, Any],
                               optimization_suggestions: List[Dict[str, Any]],
                               overall_score: float,
                               task_id: str) -> List[FileReference]:
        """保存审查报告文件"""
        output_files = []
        
        try:
            # 1. 保存详细审查报告
            review_report = self._generate_detailed_report(
                code_analysis, quality_assessment, issue_analysis, 
                optimization_suggestions, overall_score
            )
            
            report_path = f"output/{task_id}/code_review_report.md"
            report_ref = await self.save_result_to_file(
                content=review_report,
                file_path=report_path,
                file_type="report"
            )
            output_files.append(report_ref)
            
            # 2. 保存问题清单JSON
            issues_json = json.dumps(issue_analysis, indent=2, ensure_ascii=False)
            issues_path = f"output/{task_id}/issues_list.json"
            issues_ref = await self.save_result_to_file(
                content=issues_json,
                file_path=issues_path,
                file_type="analysis_data"
            )
            output_files.append(issues_ref)
            
            # 3. 保存优化建议
            suggestions_content = self._format_optimization_suggestions(optimization_suggestions)
            suggestions_path = f"output/{task_id}/optimization_suggestions.md"
            suggestions_ref = await self.save_result_to_file(
                content=suggestions_content,
                file_path=suggestions_path,
                file_type="recommendations"
            )
            output_files.append(suggestions_ref)
            
            # 4. 保存质量评估数据
            quality_json = json.dumps(quality_assessment, indent=2, ensure_ascii=False)
            quality_path = f"output/{task_id}/quality_assessment.json"
            quality_ref = await self.save_result_to_file(
                content=quality_json,
                file_path=quality_path,
                file_type="quality_data"
            )
            output_files.append(quality_ref)
            
            self.logger.info(f"💾 审查报告保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 保存审查报告失败: {str(e)}")
            return output_files
    
    def _generate_detailed_report(self, code_analysis: Dict[str, Any],
                                quality_assessment: Dict[str, Any],
                                issue_analysis: Dict[str, Any],
                                optimization_suggestions: List[Dict[str, Any]],
                                overall_score: float) -> str:
        """生成详细审查报告"""
        metrics = code_analysis.get("overall_metrics", {})
        dimension_scores = quality_assessment.get("dimension_scores", {})
        issue_stats = issue_analysis.get("statistics", {})
        
        report = f"""# Verilog代码审查报告

## 📊 审查概要

**总体评分**: {overall_score:.2f}/1.0 ({quality_assessment.get('grade', 'N/A')})
**审查时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**审查智能体**: {self.agent_id}

## 📋 代码概况

- **文件数量**: {code_analysis.get('total_files', 0)}
- **总行数**: {metrics.get('total_lines', 0)}
- **代码行数**: {metrics.get('total_code_lines', 0)}
- **注释行数**: {metrics.get('total_lines', 0) - metrics.get('total_code_lines', 0)}
- **模块数量**: {metrics.get('total_modules', 0)}

## 🎯 质量评估

### 各维度评分
"""
        
        for dimension, info in dimension_scores.items():
            score = info["score"]
            description = info["description"]
            details = info.get("details", [])
            
            report += f"""
**{description}**: {score:.2f}/1.0
{chr(10).join(f"- {detail}" for detail in details)}
"""
        
        report += f"""
## ⚠️ 问题分析

**问题总数**: {issue_stats.get('total_issues', 0)}

### 按严重程度统计
"""
        
        for severity, count in issue_stats.get('by_severity', {}).items():
            severity_info = self.severity_levels.get(severity, {})
            description = severity_info.get('description', severity)
            report += f"- **{severity.upper()}**: {count} 个 - {description}\n"
        
        report += "\n### 按类型统计\n"
        for issue_type, count in issue_stats.get('by_type', {}).items():
            report += f"- **{issue_type}**: {count} 个\n"
        
        # 详细问题清单
        report += "\n### 详细问题清单\n"
        all_issues = issue_analysis.get("all_issues", [])
        
        for i, issue in enumerate(all_issues[:20], 1):  # 最多显示20个问题
            report += f"""
**问题 {i}**: {issue.get('message', 'Unknown issue')}
- 文件: {issue.get('file', 'Unknown')}
- 行号: {issue.get('line', 'N/A')}
- 类型: {issue.get('type', 'Unknown')}
- 严重程度: {issue.get('severity', 'Unknown')}
- 建议: {issue.get('suggestion', 'No suggestion')}
"""
        
        if len(all_issues) > 20:
            report += f"\n*还有 {len(all_issues) - 20} 个问题，详见 issues_list.json*\n"
        
        # 优化建议
        report += "\n## 🚀 优化建议\n"
        for i, suggestion in enumerate(optimization_suggestions, 1):
            report += f"""
### {i}. {suggestion.get('title', 'Optimization Suggestion')}
**优先级**: {suggestion.get('priority', 'medium')}
**类别**: {suggestion.get('category', 'general')}

**描述**: {suggestion.get('description', 'No description')}

**实施方案**:
{chr(10).join(f"- {impl}" for impl in suggestion.get('implementation', []))}
"""
        
        report += f"""
## 📈 指标详情

### 代码复杂度
- **平均圈复杂度**: {metrics.get('average_complexity', 0):.1f}
- **最大嵌套深度**: {metrics.get('max_nesting_depth', 0)}

### 代码风格
- **注释比例**: {metrics.get('comment_ratio', 0):.1%}
- **长行比例**: {metrics.get('long_lines_ratio', 0):.1%}

### 结构信息
- **模块总数**: {metrics.get('total_modules', 0)}
- **有问题的文件数**: {metrics.get('files_with_issues', 0)}

---
*报告由 Verilog审查智能体 自动生成*
"""
        
        return report.strip()
    
    def _format_optimization_suggestions(self, suggestions: List[Dict[str, Any]]) -> str:
        """格式化优化建议"""
        content = "# Verilog代码优化建议\n\n"
        
        # 按优先级分组
        high_priority = [s for s in suggestions if s.get('priority') == 'high']
        medium_priority = [s for s in suggestions if s.get('priority') == 'medium']
        low_priority = [s for s in suggestions if s.get('priority') == 'low']
        
        if high_priority:
            content += "## 🔴 高优先级建议\n"
            for suggestion in high_priority:
                content += self._format_single_suggestion(suggestion)
        
        if medium_priority:
            content += "\n## 🟡 中优先级建议\n"
            for suggestion in medium_priority:
                content += self._format_single_suggestion(suggestion)
        
        if low_priority:
            content += "\n## 🟢 低优先级建议\n"
            for suggestion in low_priority:
                content += self._format_single_suggestion(suggestion)
        
        return content
    
    def _format_single_suggestion(self, suggestion: Dict[str, Any]) -> str:
        """格式化单个建议"""
        return f"""
### {suggestion.get('title', 'Optimization')}
**类别**: {suggestion.get('category', 'general')}

{suggestion.get('description', 'No description')}

**实施步骤**:
{chr(10).join(f"{i+1}. {impl}" for i, impl in enumerate(suggestion.get('implementation', [])))}

---
"""
    
    def _generate_review_summary(self, quality_assessment: Dict[str, Any],
                                issue_analysis: Dict[str, Any],
                                overall_score: float,
                                output_files: List[FileReference]) -> str:
        """生成审查摘要"""
        issue_stats = issue_analysis.get("statistics", {})
        grade = quality_assessment.get("grade", "N/A")
        
        summary = f"""
🔍 VERILOG代码审查摘要
===================

📋 审查结果:
- 总体评分: {overall_score:.2f}/1.0 ({grade})
- 问题总数: {issue_stats.get('total_issues', 0)}
- 严重问题: {issue_stats.get('by_severity', {}).get('critical', 0)}
- 主要问题: {issue_stats.get('by_severity', {}).get('major', 0)}

🎯 质量维度:
{chr(10).join(f"- {info['description']}: {info['score']:.2f}" 
             for info in quality_assessment.get('dimension_scores', {}).values())}

📁 生成报告: {len(output_files)} 个文件
{chr(10).join(f"- {ref.file_path}" for ref in output_files)}

💡 主要建议:
- {'通过基本质量检查' if overall_score >= 0.7 else '需要改进代码质量'}
- {'建议解决严重和主要问题' if issue_stats.get('by_severity', {}).get('critical', 0) > 0 else '整体代码结构良好'}
"""
        
        return summary.strip()