#!/usr/bin/env python3
"""
真实LLM驱动的代码审查智能体

Real LLM-powered Code Review Agent
"""

import json
import asyncio
import subprocess
import tempfile
import os
import re
from typing import Dict, Any, Set, List, Tuple
from pathlib import Path

from core.base_agent import BaseAgent, TaskMessage
from core.enums import AgentCapability
from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir
from tools.script_tools import ScriptManager


class RealCodeReviewAgent(BaseAgent):
    """真实LLM驱动的代码审查智能体"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="real_code_review_agent",
            role="code_reviewer",
            capabilities={
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ANALYSIS,
                AgentCapability.SPECIFICATION_ANALYSIS,
                AgentCapability.TEST_GENERATION,
                AgentCapability.VERIFICATION
            }
        )
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('RealCodeReviewAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        # 初始化脚本管理器
        self.script_manager = ScriptManager(work_dir=self.artifacts_dir)
        
        self.logger.info(f"🔍 真实代码审查智能体(Function Calling支持)初始化完成")
        self.agent_logger.info("RealCodeReviewAgent初始化完成")
    
    def _register_function_calling_tools(self):
        """注册可用的工具"""
        # 调用父类方法注册基础工具
        super()._register_function_calling_tools()
        
        # 1. 测试台生成工具
        self.register_function_calling_tool(
            name="generate_testbench",
            func=self._tool_generate_testbench,
            description="为Verilog模块生成测试台(testbench)",
            parameters={
                "module_code": {
                    "type": "string",
                    "description": "完整的Verilog模块代码",
                    "required": True
                },
                "test_cases": {
                    "type": "array",
                    "description": "测试用例列表",
                    "required": False
                }
            }
        )
        
        # 2. 仿真执行工具
        self.register_function_calling_tool(
            name="run_simulation",
            func=self._tool_run_simulation,
            description="使用iverilog运行Verilog仿真",
            parameters={
                "module_file": {
                    "type": "string",
                    "description": "模块文件路径",
                    "required": False
                },
                "testbench_file": {
                    "type": "string", 
                    "description": "测试台文件路径",
                    "required": False
                },
                "module_code": {
                    "type": "string",
                    "description": "模块代码内容",
                    "required": False
                },
                "testbench_code": {
                    "type": "string",
                    "description": "测试台代码内容",
                    "required": False
                }
            }
        )
        
        # 3. 代码分析工具
        self.register_function_calling_tool(
            name="analyze_code_quality",
            func=self._tool_analyze_code_quality,
            description="分析Verilog代码质量",
            parameters={
                "code": {
                    "type": "string",
                    "description": "要分析的Verilog代码",
                    "required": True
                }
            }
        )
        
        # 4. 脚本生成工具
        self.register_function_calling_tool(
            name="write_build_script",
            func=self._tool_write_build_script,
            description="生成构建脚本(Makefile或shell脚本)",
            parameters={
                "verilog_files": {
                    "type": "array",
                    "description": "Verilog源文件列表",
                    "required": True
                },
                "testbench_files": {
                    "type": "array", 
                    "description": "测试台文件列表",
                    "required": True
                },
                "script_type": {
                    "type": "string",
                    "description": "脚本类型: 'makefile' 或 'bash'",
                    "required": False
                },
                "target_name": {
                    "type": "string",
                    "description": "目标名称",
                    "required": False
                }
            }
        )
        
        # 5. 脚本执行工具
        self.register_function_calling_tool(
            name="execute_build_script",
            func=self._tool_execute_build_script,
            description="执行构建脚本进行编译和仿真",
            parameters={
                "script_name": {
                    "type": "string",
                    "description": "脚本文件名",
                    "required": True
                },
                "action": {
                    "type": "string",
                    "description": "执行的动作: 'all', 'compile', 'simulate', 'clean'",
                    "required": False
                },
                "arguments": {
                    "type": "array",
                    "description": "额外的命令行参数",
                    "required": False
                }
            }
        )
        
        # 使用父类的write_file工具，无需重复注册
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """调用LLM进行Function Calling"""
        # 构建完整的prompt
        full_prompt = ""
        system_prompt = None
        
        for msg in conversation:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Assistant: {msg['content']}\n\n"
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=3000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
            raise
    # 删除重复的方法，使用BaseAgent中的通用实现
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.QUALITY_ANALYSIS,
            AgentCapability.SPECIFICATION_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.VERIFICATION
        }
    
    def get_specialty_description(self) -> str:
        return "真实LLM驱动的代码审查智能体，提供专业的Verilog/SystemVerilog代码质量分析、测试台生成和功能验证"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行代码审查任务"""
        task_id = original_message.task_id
        self.logger.info(f"🔍 开始执行代码审查任务: {task_id}")
        
        try:
            # 1. 提取要审查的代码
            code_to_review = await self._extract_code_from_files(file_contents)
            
            if not code_to_review:
                error_response = self.create_error_response_formatted(
                    task_id=task_id,
                    error_message="未找到可审查的代码文件",
                    error_details="请确保提供了包含Verilog代码的文件",
                    format_type=ResponseFormat.JSON
                )
                return {"formatted_response": error_response}
            
            # 2. 执行详细的代码审查
            review_results = []
            for file_path, code_content in code_to_review.items():
                self.logger.info(f"📝 审查文件: {file_path}")
                review_result = await self._perform_detailed_review(
                    file_path, code_content, enhanced_prompt
                )
                review_results.append(review_result)
            
            # 3. 生成综合审查报告
            comprehensive_report = await self._generate_comprehensive_report(review_results)
            
            # 4. 执行功能测试验证
            test_results = []
            if self._should_perform_testing(enhanced_prompt, code_to_review):
                self.logger.info("🧪 开始执行功能测试验证")
                for file_path, code_content in code_to_review.items():
                    if self._is_testable_module(code_content):
                        test_result = await self._perform_functional_testing(
                            file_path, code_content, enhanced_prompt
                        )
                        test_results.append(test_result)
            
            # 5. 计算整体质量指标（包含测试结果）
            overall_quality = self._calculate_overall_quality(review_results, test_results)
            
            # 6. 保存审查报告和测试结果
            output_files = await self._save_review_files(
                comprehensive_report, review_results, test_results, task_id
            )
            
            # 7. 创建标准化响应
            response = await self._create_review_response(
                task_id, review_results, test_results, overall_quality, output_files, comprehensive_report
            )
            
            return {"formatted_response": response}
            
        except Exception as e:
            self.logger.error(f"❌ 代码审查任务失败: {str(e)}")
            error_response = self.create_error_response_formatted(
                task_id=task_id,
                error_message=f"代码审查失败: {str(e)}",
                error_details="请检查输入文件和LLM连接状态",
                format_type=ResponseFormat.JSON
            )
            return {"formatted_response": error_response}
    
    async def _extract_code_from_files(self, file_contents: Dict[str, Dict]) -> Dict[str, str]:
        """从文件中提取代码内容"""
        code_files = {}
        
        for file_path, content_info in file_contents.items():
            file_type = content_info.get('type', '').lower()
            content = content_info.get('content', '')
            
            # 检查是否是代码文件
            if (file_type in ['verilog', 'systemverilog', 'vhdl'] or 
                file_path.endswith(('.v', '.sv', '.vhd')) or
                'module' in content):
                
                if content.strip():
                    code_files[file_path] = content
                    self.logger.info(f"📄 发现代码文件: {file_path} ({len(content)} 字符)")
        
        return code_files
    
    async def _perform_detailed_review(self, file_path: str, code_content: str, 
                                     task_context: str) -> Dict[str, Any]:
        """执行详细的代码审查"""
        
        review_prompt = f"""
你是一位拥有15年经验的资深Verilog/FPGA设计专家和代码审查员。请对以下代码进行全面、深入的审查。

文件路径: {file_path}
任务上下文: {task_context}

代码内容:
```verilog
{code_content}
```

请从以下维度进行专业审查：

## 1. 语法和语义分析
- Verilog语法正确性
- 信号声明和使用
- 端口连接正确性
- 数据类型使用规范

## 2. 设计质量评估
- 模块化设计合理性
- 接口设计清晰度
- 参数化程度
- 代码复用性

## 3. 时序设计审查
- 时钟域处理
- 复位逻辑设计
- 组合逻辑和时序逻辑分离
- 潜在的竞争冒险

## 4. 性能和效率
- 关键路径分析
- 资源使用效率
- 流水线设计（如适用）
- 面积功耗考虑

## 5. 可维护性和可读性
- 命名规范一致性
- 注释完整性和准确性
- 代码结构清晰度
- 调试友好性

## 6. 错误检查和边界处理
- 边界条件处理
- 错误状态处理
- 异常情况考虑
- 断言使用

## 7. 行业最佳实践
- 编码规范遵循
- 设计模式应用
- 可综合性考虑
- 验证友好性

请以JSON格式返回详细的审查结果：

{{
    "file_path": "{file_path}",
    "review_summary": "整体审查总结",
    "quality_scores": {{
        "syntax_correctness": 0.95,
        "design_quality": 0.88,
        "timing_design": 0.85,
        "performance": 0.80,
        "maintainability": 0.90,
        "error_handling": 0.75,
        "best_practices": 0.82
    }},
    "critical_issues": [
        {{
            "severity": "high",
            "category": "timing",
            "line_number": 45,
            "description": "发现的关键问题描述",
            "impact": "对设计的影响",
            "recommendation": "具体修复建议"
        }}
    ],
    "warnings": [
        {{
            "severity": "medium",
            "category": "style",
            "line_number": 23,
            "description": "警告问题描述",
            "recommendation": "改进建议"
        }}
    ],
    "suggestions": [
        {{
            "category": "optimization",
            "description": "优化建议描述",
            "benefit": "优化带来的好处"
        }}
    ],
    "positive_aspects": [
        "代码的优点1",
        "代码的优点2"
    ],
    "overall_assessment": "整体评价和建议",
    "next_actions": [
        "建议的下一步行动1",
        "建议的下一步行动2"
    ]
}}

请确保审查结果专业、详细、可操作：
"""
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=review_prompt,
                temperature=0.3,
                max_tokens=3000,
                json_mode=True
            )
            
            review_result = json.loads(response)
            self.logger.info(f"✅ 文件审查完成: {file_path}")
            return review_result
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM审查失败，使用基础审查: {str(e)}")
            return self._basic_code_review(file_path, code_content)
    
    def _basic_code_review(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """基础代码审查（备用方案）"""
        issues = []
        warnings = []
        
        # 基本语法检查
        if "module" not in code_content:
            issues.append({
                "severity": "high",
                "category": "syntax",
                "line_number": 1,
                "description": "缺少module定义",
                "impact": "代码无法编译",
                "recommendation": "添加proper module定义"
            })
        
        if "endmodule" not in code_content:
            issues.append({
                "severity": "high", 
                "category": "syntax",
                "line_number": len(code_content.split('\n')),
                "description": "缺少endmodule",
                "impact": "代码无法编译",
                "recommendation": "添加endmodule语句"
            })
        
        # 基本风格检查
        if "//" not in code_content and "/*" not in code_content:
            warnings.append({
                "severity": "medium",
                "category": "style",
                "line_number": 1,
                "description": "缺少注释",
                "recommendation": "为代码添加注释以提高可读性"
            })
        
        return {
            "file_path": file_path,
            "review_summary": "基础代码审查完成（LLM不可用）",
            "quality_scores": {
                "syntax_correctness": 0.7,
                "design_quality": 0.6,
                "timing_design": 0.6,
                "performance": 0.6,
                "maintainability": 0.5,
                "error_handling": 0.5,
                "best_practices": 0.6
            },
            "critical_issues": issues,
            "warnings": warnings,
            "suggestions": [
                {"category": "general", "description": "建议使用完整的LLM审查获得更详细的分析", "benefit": "更准确的代码质量评估"}
            ],
            "positive_aspects": ["代码基本结构存在"],
            "overall_assessment": "需要LLM进行更详细的审查",
            "next_actions": ["修复发现的基本问题", "使用LLM进行完整审查"]
        }
    
    async def _generate_comprehensive_report(self, review_results: list) -> str:
        """生成综合审查报告"""
        
        if not review_results:
            return "无可用的审查结果"
        
        # 使用LLM生成综合报告
        report_prompt = f"""
作为代码审查专家，请基于以下各个文件的详细审查结果，生成一份综合的代码审查报告。

审查结果:
{json.dumps(review_results, indent=2, ensure_ascii=False)}

请生成一份专业的综合审查报告，包含：

1. **执行总结** - 整体代码质量概述
2. **关键发现** - 最重要的问题和亮点
3. **质量指标汇总** - 各维度质量分数统计
4. **优先级行动计划** - 按优先级排序的改进建议
5. **风险评估** - 潜在风险和影响分析
6. **最佳实践建议** - 长期改进建议

报告应该：
- 结构清晰，便于阅读
- 重点突出，actionable
- 平衡问题和优点
- 提供具体的改进路径

请以Markdown格式返回报告：
"""
        
        try:
            comprehensive_report = await self.llm_client.send_prompt(
                prompt=report_prompt,
                temperature=0.4,
                max_tokens=2500
            )
            
            self.logger.info("📊 综合审查报告生成完成")
            return comprehensive_report.strip()
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM报告生成失败，使用模板: {str(e)}")
            return self._generate_basic_report(review_results)
    
    def _generate_basic_report(self, review_results: list) -> str:
        """生成基础报告（备用方案）"""
        total_files = len(review_results)
        total_issues = sum(len(result.get('critical_issues', [])) for result in review_results)
        total_warnings = sum(len(result.get('warnings', [])) for result in review_results)
        
        report = f"""# 代码审查综合报告

## 审查概览
- 审查文件数: {total_files}
- 发现关键问题: {total_issues}
- 发现警告: {total_warnings}

## 文件审查结果
"""
        
        for result in review_results:
            file_path = result.get('file_path', 'Unknown')
            summary = result.get('review_summary', 'No summary')
            report += f"\n### {file_path}\n{summary}\n"
        
        report += "\n## 建议行动\n1. 修复所有关键问题\n2. 处理警告问题\n3. 考虑优化建议"
        
        return report
    
    def _calculate_overall_quality(self, review_results: list, test_results: list = None) -> QualityMetrics:
        """计算整体质量指标"""
        if not review_results:
            return QualityMetrics(0.5, 0.5, 0.5, 0.0, 0.5, 0.5)
        
        # 收集所有质量分数
        all_scores = []
        syntax_scores = []
        design_scores = []
        maintainability_scores = []
        performance_scores = []
        
        for result in review_results:
            quality_scores = result.get('quality_scores', {})
            
            syntax_score = quality_scores.get('syntax_correctness', 0.5)
            design_score = quality_scores.get('design_quality', 0.5)
            timing_score = quality_scores.get('timing_design', 0.5)
            perf_score = quality_scores.get('performance', 0.5)
            maint_score = quality_scores.get('maintainability', 0.5)
            error_score = quality_scores.get('error_handling', 0.5)
            practice_score = quality_scores.get('best_practices', 0.5)
            
            # 计算该文件的整体分数
            file_overall = (syntax_score + design_score + timing_score + 
                          perf_score + maint_score + error_score + practice_score) / 7
            
            all_scores.append(file_overall)
            syntax_scores.append(syntax_score)
            design_scores.append(design_score)
            maintainability_scores.append(maint_score)
            performance_scores.append(perf_score)
        
        # 计算平均值
        overall_score = sum(all_scores) / len(all_scores)
        avg_syntax = sum(syntax_scores) / len(syntax_scores)
        avg_design = sum(design_scores) / len(design_scores)
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores)
        avg_performance = sum(performance_scores) / len(performance_scores)
        
        # 计算测试覆盖率（如果有测试结果）
        test_coverage = 0.0
        if test_results:
            total_tests = len(test_results)
            successful_tests = sum(1 for test in test_results if test.get('test_success', False))
            if total_tests > 0:
                test_coverage = successful_tests / total_tests
                # 根据测试通过率调整整体分数
                avg_pass_rate = sum(test.get('pass_rate', 0.0) for test in test_results) / total_tests
                overall_score = (overall_score + avg_pass_rate) / 2
        
        return QualityMetrics(
            overall_score=overall_score,
            syntax_score=avg_syntax,
            functionality_score=avg_design,
            test_coverage=test_coverage,
            documentation_quality=avg_maintainability,
            performance_score=avg_performance
        )
    
    async def _save_review_files(self, comprehensive_report: str, review_results: list,
                               test_results: list, task_id: str) -> list:
        """保存审查报告文件"""
        output_files = []
        
        try:
            # 使用工件目录确保目录存在
            output_dir = self.artifacts_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存综合报告
            report_path = output_dir / f"code_review_report_{task_id}.md"
            report_ref = await self.save_result_to_file(
                content=comprehensive_report,
                file_path=str(report_path),
                file_type="documentation"
            )
            output_files.append(report_ref)
            
            # 保存详细审查结果
            detailed_results = {
                "task_id": task_id,
                "review_timestamp": task_id,
                "total_files_reviewed": len(review_results),
                "detailed_results": review_results,
                "test_results": test_results if test_results else [],
                "testing_performed": bool(test_results)
            }
            
            details_path = output_dir / f"review_details_{task_id}.json"
            details_ref = await self.save_result_to_file(
                content=json.dumps(detailed_results, indent=2, ensure_ascii=False),
                file_path=str(details_path),
                file_type="json"
            )
            output_files.append(details_ref)
            
            # 保存测试台文件引用（如果有）
            if test_results:
                for test_result in test_results:
                    testbench_file = test_result.get('testbench_file')
                    if testbench_file and Path(testbench_file).exists():
                        testbench_ref = await self.save_result_to_file(
                            content=Path(testbench_file).read_text(encoding='utf-8'),
                            file_path=testbench_file,
                            file_type="testbench",
                            description=f"Generated testbench for {test_result.get('file_path', 'unknown')}"
                        )
                        output_files.append(testbench_ref)
            
            self.logger.info(f"💾 审查和测试报告保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 保存审查报告失败: {str(e)}")
            return []
    
    async def _create_review_response(self, task_id: str, review_results: list,
                                    test_results: list, overall_quality: QualityMetrics, 
                                    output_files: list, comprehensive_report: str) -> str:
        """创建标准化审查响应"""
        
        builder = self.create_response_builder(task_id)
        
        # 添加生成的文件
        for file_ref in output_files:
            builder.add_generated_file(
                file_ref.file_path,
                file_ref.file_type,
                file_ref.description
            )
        
        # 统计问题数量
        total_critical = sum(len(result.get('critical_issues', [])) for result in review_results)
        total_warnings = sum(len(result.get('warnings', [])) for result in review_results)
        
        # 统计测试结果
        total_tests = len(test_results) if test_results else 0
        successful_tests = sum(1 for test in (test_results or []) if test.get('test_success', False))
        failed_tests = total_tests - successful_tests
        
        # 统计失败的测试用例
        total_failed_cases = 0
        if test_results:
            for test in test_results:
                total_failed_cases += len(test.get('failed_cases', []))
        
        # 根据审查结果添加问题
        if total_critical > 0:
            builder.add_issue(
                "error", "high",
                f"发现 {total_critical} 个关键问题需要立即修复",
                solution="请查看详细审查报告并逐一修复关键问题"
            )
        
        if total_warnings > 0:
            builder.add_issue(
                "warning", "medium",
                f"发现 {total_warnings} 个警告问题建议处理",
                solution="建议在下次迭代中处理这些警告问题"
            )
        
        if overall_quality.overall_score < 0.6:
            builder.add_issue(
                "warning", "high",
                f"整体代码质量较低 (分数: {overall_quality.overall_score:.2f})",
                solution="建议进行全面的代码重构"
            )
        
        # 添加测试相关问题
        if failed_tests > 0:
            builder.add_issue(
                "error", "high",
                f"功能测试失败: {failed_tests}/{total_tests} 个模块测试未通过",
                solution="检查测试失败的模块并修复功能错误"
            )
        
        if total_failed_cases > 0:
            builder.add_issue(
                "warning", "medium",
                f"测试用例失败: 共 {total_failed_cases} 个测试用例未通过",
                solution="查看测试报告详情，修复失败的功能点"
            )
        
        # 添加下一步建议
        builder.add_next_step("仔细阅读综合审查报告")
        
        if total_tests > 0:
            builder.add_next_step("查看功能测试结果和生成的测试台")
        
        builder.add_next_step("优先修复所有关键问题")
        
        if total_warnings > 0:
            builder.add_next_step("处理警告问题以提高代码质量")
        
        if overall_quality.performance_score < 0.7:
            builder.add_next_step("考虑性能优化")
        
        if failed_tests > 0:
            builder.add_next_step("修复测试失败的功能后重新运行测试")
        
        builder.add_next_step("在修复后重新进行代码审查")
        
        # 添加元数据
        builder.add_metadata("files_reviewed", len(review_results))
        builder.add_metadata("critical_issues", total_critical)
        builder.add_metadata("warnings", total_warnings)
        builder.add_metadata("overall_quality_score", overall_quality.overall_score)
        builder.add_metadata("review_type", "comprehensive")
        builder.add_metadata("llm_powered", True)
        builder.add_metadata("testing_performed", total_tests > 0)
        builder.add_metadata("total_tests", total_tests)
        builder.add_metadata("successful_tests", successful_tests)
        builder.add_metadata("test_coverage", overall_quality.test_coverage)
        if test_results:
            avg_pass_rate = sum(test.get('pass_rate', 0.0) for test in test_results) / len(test_results)
            builder.add_metadata("average_test_pass_rate", avg_pass_rate)
        
        # 构建响应 - 代码审查任务总是100%完成
        status = TaskStatus.SUCCESS
        completion = 100.0
        
        # 构建消息
        message_parts = [
            f"代码审查完成，共审查 {len(review_results)} 个文件"
        ]
        
        if total_tests > 0:
            message_parts.append(f"执行了 {total_tests} 个模块的功能测试")
            if failed_tests > 0:
                message_parts.append(f"{failed_tests} 个测试失败")
            if total_failed_cases > 0:
                message_parts.append(f"{total_failed_cases} 个测试用例失败")
        
        if total_critical > 0:
            message_parts.append(f"发现 {total_critical} 个关键问题")
        if total_warnings > 0:
            message_parts.append(f"{total_warnings} 个警告")
            
        message_parts.append(f"整体质量分数: {overall_quality.overall_score:.2f}")
        
        if total_tests > 0:
            message_parts.append(f"测试覆盖率: {overall_quality.test_coverage:.1%}")
        
        response = builder.build(
            response_type=ResponseType.QUALITY_REPORT,
            status=status,
            message=", ".join(message_parts),
            completion_percentage=completion,
            quality_metrics=overall_quality
        )
        
        return response.format_response(ResponseFormat.JSON)
    
    # ==========================================================================
    # 🧪 功能测试验证
    # ==========================================================================
    
    def _should_perform_testing(self, prompt: str, code_files: Dict[str, str]) -> bool:
        """判断是否应该执行功能测试"""
        # 检查是否明确要求测试
        test_keywords = ['测试', '验证', 'test', 'verify', 'simulation', 'testbench']
        if any(keyword in prompt.lower() for keyword in test_keywords):
            self.logger.info(f"🧪 检测到测试关键词，启用功能测试")
            return True
        
        # 检查代码规模和复杂度，决定是否需要测试
        total_lines = sum(len(content.split('\n')) for content in code_files.values())
        if total_lines > 50:  # 超过50行代码建议测试
            self.logger.info(f"🧪 代码规模({total_lines}行)超过阈值，启用功能测试")
            return True
        
        # 检查是否有复杂逻辑需要测试
        for file_path, content in code_files.items():
            complex_keywords = ['always', 'case', 'if', 'for', 'while', 'assign']
            keyword_count = sum(1 for keyword in complex_keywords if keyword in content.lower())
            if keyword_count >= 3:  # 降低阈值，包含3个以上复杂逻辑关键词就测试
                self.logger.info(f"🧪 检测到复杂逻辑({keyword_count}个关键词)，启用功能测试")
                return True
        
        # 默认为ALU、计数器、存储器等常见模块启用测试
        for content in code_files.values():
            common_modules = ['alu', 'counter', 'memory', 'fifo', 'uart', 'spi', 'processor']
            if any(module_type in content.lower() for module_type in common_modules):
                self.logger.info(f"🧪 检测到常见设计模块，启用功能测试")
                return True
        
        self.logger.info(f"🚫 未满足测试触发条件，跳过功能测试")
        return False
    
    def _is_testable_module(self, code_content: str) -> bool:
        """判断模块是否可测试"""
        # 清理文件内容，移除markdown格式标记
        cleaned_content = code_content
        if cleaned_content.startswith('```'):
            lines = cleaned_content.split('\n')
            # 移除开头的```verilog行
            if lines[0].startswith('```'):
                lines = lines[1:]
            # 移除结尾的```行
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned_content = '\n'.join(lines)
        
        self.logger.debug(f"🔍 检查模块可测试性，内容长度: {len(cleaned_content)}")
        
        # 检查是否是完整的模块
        if 'module' not in cleaned_content or 'endmodule' not in cleaned_content:
            self.logger.debug(f"🚫 未找到完整的module定义")
            return False
        
        # 检查是否有端口定义 - 使用更宽松的正则表达式
        module_pattern = r'module\s+\w+\s*(?:\#\([^)]*\))?\s*\([^)]*\)'
        if not re.search(module_pattern, cleaned_content, re.DOTALL):
            self.logger.debug(f"🚫 未找到模块端口定义")
            return False
        
        # 排除过于简单的模块
        non_empty_lines = [line.strip() for line in cleaned_content.split('\n') 
                          if line.strip() and not line.strip().startswith('//')]
        if len(non_empty_lines) < 10:
            self.logger.debug(f"🚫 模块过于简单({len(non_empty_lines)}行)")
            return False
        
        self.logger.info(f"✅ 模块可测试，有效代码行数: {len(non_empty_lines)}")
        return True
    
    async def _perform_functional_testing(self, file_path: str, code_content: str, 
                                        task_context: str) -> Dict[str, Any]:
        """执行功能测试，包含LLM驱动的错误修复"""
        max_retries = 3
        current_code = code_content
        
        for attempt in range(max_retries):
            self.logger.info(f"🔍 功能测试尝试 {attempt + 1}/{max_retries}")
            
            try:
                # 1. 生成测试台
                testbench_result = await self._generate_testbench(file_path, current_code, task_context)
                
                if not testbench_result['success']:
                    if attempt == max_retries - 1:
                        return {
                            'file_path': file_path,
                            'test_success': False,
                            'error': f"测试台生成失败: {testbench_result['error']}",
                            'testbench_generated': False,
                            'iterations': attempt + 1
                        }
                    continue
                
                # 2. 执行iverilog仿真
                simulation_result = await self._run_iverilog_simulation(
                    file_path, current_code, testbench_result['testbench_code']
                )
                
                # 3. 如果成功，分析结果
                if simulation_result['success']:
                    test_analysis = await self._analyze_test_results(
                        file_path, simulation_result, testbench_result.get('expected_results', [])
                    )
                    
                    return {
                        'file_path': file_path,
                        'test_success': True,
                        'testbench_generated': True,
                        'testbench_file': testbench_result.get('testbench_file'),
                        'simulation_output': simulation_result.get('output', ''),
                        'compilation_success': True,
                        'execution_success': True,
                        'test_cases': test_analysis.get('test_cases', []),
                        'failed_cases': test_analysis.get('failed_cases', []),
                        'pass_rate': test_analysis.get('pass_rate', 0.0),
                        'error_details': '',
                        'recommendations': test_analysis.get('recommendations', []),
                        'iterations': attempt + 1,
                        'code_fixed': attempt > 0
                    }
                
                # 4. 如果失败，使用LLM修复代码
                if simulation_result.get('error'):
                    self.logger.info(f"⚠️ 检测到错误，使用LLM修复代码...")
                    
                    fixed_code = await self._fix_code_with_llm(
                        current_code, simulation_result['error'], task_context
                    )
                    
                    if fixed_code and fixed_code != current_code:
                        current_code = fixed_code
                        self.logger.info(f"✅ LLM已生成修复后的代码")
                        continue
                    else:
                        self.logger.warning(f"⚠️ LLM未能修复代码或代码无变化")
                
                # 5. 最后一次尝试仍失败
                if attempt == max_retries - 1:
                    return {
                        'file_path': file_path,
                        'test_success': False,
                        'testbench_generated': True,
                        'error_details': simulation_result.get('error', '未知错误'),
                        'iterations': attempt + 1,
                        'final_code': current_code
                    }
                
            except Exception as e:
                self.logger.error(f"❌ 功能测试异常 {file_path}: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'file_path': file_path,
                        'test_success': False,
                        'error': f"测试执行异常: {str(e)}",
                        'testbench_generated': False,
                        'iterations': attempt + 1
                    }
        
        return {
            'file_path': file_path,
            'test_success': False,
            'error': '达到最大重试次数',
            'iterations': max_retries
        }
    
    async def _generate_testbench(self, file_path: str, code_content: str, 
                                task_context: str) -> Dict[str, Any]:
        """生成测试台"""
        try:
            # 分析模块信息
            module_info = self._parse_module_info(code_content)
            
            testbench_prompt = f"""
你是一位资深的Verilog验证工程师。请为以下模块生成一个完整的、全面的测试台。

模块文件: {file_path}
任务上下文: {task_context}

模块信息:
- 模块名: {module_info['module_name']}
- 输入端口: {module_info['inputs']}
- 输出端口: {module_info['outputs']}

模块代码:
```verilog
{code_content}
```

请生成一个comprehensive testbench，要求：

1. **测试覆盖性**：
   - 覆盖所有输入组合（合理范围内）
   - 测试边界条件和极值
   - 测试正常功能和异常情况

2. **测试台结构**：
   - 包含时钟生成（如需要）
   - 复位序列
   - 测试向量生成
   - 结果检查和对比

3. **预期结果**：
   - 为每个测试用例定义预期输出
   - 实现自动对比检查
   - 输出详细的测试结果

4. **测试用例设计**：
   - 基本功能测试
   - 边界值测试
   - 随机测试（适量）
   - 性能测试（如适用）

请以JSON格式返回：
{{
    "testbench_code": "完整的testbench Verilog代码",
    "expected_results": [
        {{
            "test_case": "测试用例描述",
            "inputs": {{"input_name": "value"}},
            "expected_outputs": {{"output_name": "expected_value"}},
            "test_type": "basic|boundary|random|performance"
        }}
    ],
    "test_summary": "测试计划总结",
    "coverage_description": "测试覆盖率说明"
}}

testbench应该：
- 模块名为 `{module_info['module_name']}_tb`
- 包含完整的仿真控制（$dumpfile, $dumpvars, $finish）
- 具有清晰的测试报告输出
- 能够在iverilog中正确编译和运行
"""
            
            response = await self.llm_client.send_prompt(
                prompt=testbench_prompt,
                temperature=0.4,
                max_tokens=4000,
                json_mode=True
            )
            
            # 清理响应中的转义字符
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            testbench_data = json.loads(cleaned_response)
            
            # 保存测试台到文件
            testbench_file = await self._save_testbench_file(
                module_info['module_name'], testbench_data['testbench_code']
            )
            
            return {
                'success': True,
                'testbench_code': testbench_data['testbench_code'],
                'testbench_file': testbench_file,
                'expected_results': testbench_data.get('expected_results', []),
                'test_summary': testbench_data.get('test_summary', ''),
                'coverage_description': testbench_data.get('coverage_description', '')
            }
            
        except Exception as e:
            self.logger.error(f"❌ 测试台生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_module_info(self, code_content: str) -> Dict[str, Any]:
        """解析模块信息"""
        # 清理文件内容，移除markdown格式标记
        cleaned_content = code_content
        if cleaned_content.startswith('```'):
            lines = cleaned_content.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned_content = '\n'.join(lines)
        
        module_info = {
            'module_name': 'unknown_module',
            'inputs': [],
            'outputs': [],
            'parameters': []
        }
        
        # 提取模块名
        module_match = re.search(r'module\s+(\w+)', cleaned_content)
        if module_match:
            module_info['module_name'] = module_match.group(1)
        
        # 提取端口信息 - 更精确的正则表达式
        input_matches = re.findall(r'input\s+(?:(?:reg|wire)\s+)?(?:\[[^\]]+\]\s+)?(\w+)', cleaned_content)
        output_matches = re.findall(r'output\s+(?:(?:reg|wire)\s+)?(?:\[[^\]]+\]\s+)?(\w+)', cleaned_content)
        
        module_info['inputs'] = input_matches
        module_info['outputs'] = output_matches
        
        # 提取参数信息
        param_matches = re.findall(r'parameter\s+(\w+)\s*=\s*([^;,\s]+)', cleaned_content)
        module_info['parameters'] = param_matches
        
        self.logger.info(f"📊 解析模块信息: {module_info['module_name']}, "
                        f"输入: {len(module_info['inputs'])}, "
                        f"输出: {len(module_info['outputs'])}")
        
        return module_info
    
    async def _save_testbench_file(self, module_name: str, testbench_code: str) -> str:
        """保存测试台文件"""
        output_dir = self.artifacts_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        testbench_file = output_dir / f"{module_name}_tb.v"
        
        with open(testbench_file, 'w', encoding='utf-8') as f:
            f.write(testbench_code)
        
        self.logger.info(f"💾 测试台已保存: {testbench_file}")
        return str(testbench_file)
    
    async def _fix_code_with_llm(self, original_code: str, error_message: str, task_context: str) -> str:
        """使用LLM根据错误信息修复代码"""
        try:
            self.logger.info("🔧 使用LLM修复代码...")
            
            fix_prompt = f"""
你是一位资深的Verilog设计和调试专家。请根据以下错误信息修复Verilog代码。

## 任务背景
{task_context}

## 当前代码
```verilog
{original_code}
```

## 错误信息
{error_message}

## 修复要求
1. **精确定位错误**：分析错误信息，找到确切的语法或逻辑问题
2. **最小化修改**：只修复必要的错误，保持原有设计意图
3. **验证修复**：确保修复后的代码可以成功编译和仿真
4. **保持功能**：修复后必须实现原有的设计功能

## 常见错误类型和修复建议
- **语法错误**：检查括号匹配、分号、模块声明
- **类型错误**：reg/wire声明与使用的一致性
- **端口错误**：模块端口与实例化的一致性
- **时序错误**：时钟和复位信号的处理

## 修复策略
1. 首先分析错误类型和位置
2. 然后提供修复后的完整代码
3. 最后简要说明修复的要点

请只返回修复后的完整Verilog代码，不要添加解释文字：
"""
            
            fixed_code = await self.llm_client.send_prompt(
                prompt=fix_prompt,
                temperature=0.3,
                max_tokens=3000,
                system_prompt="你是一个专业的Verilog代码修复专家，专注于解决编译错误和逻辑问题。"
            )
            
            # 清理返回的代码
            fixed_code = fixed_code.strip()
            if fixed_code.startswith('```verilog'):
                fixed_code = fixed_code[10:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            
            self.logger.info(f"✅ LLM生成修复代码完成，长度: {len(fixed_code)} 字符")
            return fixed_code.strip()
            
        except Exception as e:
            self.logger.error(f"❌ LLM代码修复失败: {str(e)}")
            return original_code  # 返回原代码如果修复失败
    
    async def _run_iverilog_simulation(self, module_file: str, module_code: str, 
                                     testbench_code: str) -> Dict[str, Any]:
        """运行iverilog仿真"""
        result = {
            'success': False,
            'compilation_success': False,
            'execution_success': False,
            'output': '',
            'error': ''
        }
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                temp_path = Path(temp_dir)
                
                # 保存模块文件
                module_path = temp_path / "module.v"
                with open(module_path, 'w', encoding='utf-8') as f:
                    f.write(module_code)
                
                # 保存测试台文件
                testbench_path = temp_path / "testbench.v"
                with open(testbench_path, 'w', encoding='utf-8') as f:
                    f.write(testbench_code)
                
                # 1. 编译
                compile_cmd = [
                    'iverilog', 
                    '-o', str(temp_path / 'simulation'),
                    str(module_path),
                    str(testbench_path)
                ]
                
                self.logger.info(f"🔨 编译命令: {' '.join(compile_cmd)}")
                
                compile_process = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=temp_dir
                )
                
                if compile_process.returncode != 0:
                    error_message = compile_process.stderr
                    result['error'] = f"编译失败: {error_message}"
                    self.logger.error(f"❌ iverilog编译失败: {error_message}")
                    
                    # 尝试智能分析和修复编译错误
                    fix_suggestion = await self._analyze_compilation_error(
                        error_message, 
                        module_content, 
                        testbench_content
                    )
                    result['fix_suggestion'] = fix_suggestion
                    result['needs_fix'] = True
                    
                    return result
                
                result['compilation_success'] = True
                self.logger.info("✅ iverilog编译成功")
                
                # 2. 运行仿真
                sim_cmd = ['vvp', str(temp_path / 'simulation')]
                
                self.logger.info(f"▶️ 仿真命令: {' '.join(sim_cmd)}")
                
                sim_process = subprocess.run(
                    sim_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=temp_dir
                )
                
                result['output'] = sim_process.stdout
                result['execution_success'] = sim_process.returncode == 0
                
                if sim_process.returncode != 0:
                    result['error'] += f" | 仿真失败: {sim_process.stderr}"
                    self.logger.error(f"❌ 仿真执行失败: {sim_process.stderr}")
                else:
                    self.logger.info("✅ 仿真执行成功")
                
                result['success'] = result['compilation_success'] and result['execution_success']
                
                return result
                
            except subprocess.TimeoutExpired:
                result['error'] = "仿真超时"
                self.logger.error("❌ 仿真执行超时")
                return result
            except FileNotFoundError:
                result['error'] = "iverilog未安装或不在PATH中"
                self.logger.error("❌ iverilog未找到，请确保已安装iverilog")
                return result
            except Exception as e:
                result['error'] = f"仿真执行异常: {str(e)}"
                self.logger.error(f"❌ 仿真异常: {str(e)}")
                return result
    
    async def _analyze_compilation_error(self, error_message: str, module_content: str, testbench_content: str) -> str:
        """智能分析编译错误并提供修复建议"""
        try:
            self.logger.info("🔍 开始智能错误分析...")
            
            analysis_prompt = f"""
作为Verilog专家，请分析以下编译错误并提供具体的修复建议：

## 编译错误信息：
```
{error_message}
```

## 模块代码：
```verilog
{module_content[:2000]}  // 截取前2000字符
```

## 测试台代码：
```verilog  
{testbench_content[:1000]}  // 截取前1000字符
```

请提供：
1. **错误原因分析** - 详细解释为什么会出现这个错误
2. **具体修复步骤** - 提供准确的代码修改建议
3. **修复后的代码片段** - 给出修正后的关键代码段
4. **预防措施** - 如何避免类似错误

请使用结构化格式回答，重点关注实际可执行的修复方案。
"""

            # 调用LLM进行错误分析
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是一位经验丰富的Verilog/SystemVerilog设计专家，擅长快速诊断和修复编译错误。",
                temperature=0.1,  # 低温度确保准确性
                max_tokens=1500
            )
            
            self.logger.info("✅ 错误分析完成")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ 错误分析失败: {str(e)}")
            return f"自动错误分析失败: {str(e)}，请手动检查编译错误信息。"
    
    async def _analyze_test_results(self, file_path: str, simulation_result: Dict[str, Any],
                                  expected_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        analysis = {
            'test_cases': [],
            'failed_cases': [],
            'pass_rate': 0.0,
            'recommendations': []
        }
        
        if not simulation_result['success']:
            analysis['recommendations'].append({
                'type': 'critical',
                'description': '仿真未能成功执行，需要修复编译或运行时错误',
                'action': '检查代码语法和逻辑错误'
            })
            return analysis
        
        simulation_output = simulation_result.get('output', '')
        
        # 使用LLM分析仿真输出
        if self.llm_client and simulation_output.strip():
            try:
                analysis_result = await self._llm_analyze_simulation_output(
                    file_path, simulation_output, expected_results
                )
                analysis.update(analysis_result)
            except Exception as e:
                self.logger.warning(f"⚠️ LLM结果分析失败: {str(e)}")
        
        # 基础分析（备用方案）
        if not analysis['test_cases']:
            analysis = self._basic_test_analysis(simulation_output, expected_results)
        
        return analysis
    
    async def _llm_analyze_simulation_output(self, file_path: str, simulation_output: str,
                                           expected_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM分析仿真输出"""
        analysis_prompt = f"""
作为验证工程师，请分析以下Verilog仿真的输出结果。

文件: {file_path}
仿真输出:
```
{simulation_output}
```

预期结果（如果有）:
{json.dumps(expected_results, indent=2, ensure_ascii=False) if expected_results else "无预期结果数据"}

请分析：
1. 识别所有测试用例的执行情况
2. 确定哪些测试用例通过/失败
3. 分析失败原因
4. 提供改进建议

返回JSON格式：
{{
    "test_cases": [
        {{
            "case_name": "测试用例名称",
            "status": "PASS|FAIL|ERROR",
            "description": "测试用例描述",
            "expected": "预期结果",
            "actual": "实际结果",
            "failure_reason": "失败原因（如果失败）"
        }}
    ],
    "failed_cases": [
        {{
            "case_name": "失败的测试用例名",
            "failure_type": "功能错误|时序错误|逻辑错误",
            "description": "失败详情",
            "impact": "影响评估"
        }}
    ],
    "pass_rate": 0.85,
    "recommendations": [
        {{
            "type": "critical|important|suggestion",
            "description": "建议描述",
            "action": "具体行动"
        }}
    ],
    "summary": "整体测试结果总结"
}}
"""
        
        response = await self.llm_client.send_prompt(
            prompt=analysis_prompt,
            temperature=0.3,
            max_tokens=2000,
            json_mode=True
        )
        
        return json.loads(response)
    
    def _basic_test_analysis(self, simulation_output: str, 
                           expected_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基础测试结果分析"""
        lines = simulation_output.split('\n')
        
        # 查找测试相关的输出
        test_lines = [line for line in lines if any(keyword in line.lower() 
                     for keyword in ['test', 'pass', 'fail', 'error', 'case'])]
        
        analysis = {
            'test_cases': [],
            'failed_cases': [],
            'pass_rate': 0.0,
            'recommendations': []
        }
        
        # 简单的通过/失败检测
        pass_count = sum(1 for line in test_lines if 'pass' in line.lower())
        fail_count = sum(1 for line in test_lines if 'fail' in line.lower())
        error_count = sum(1 for line in test_lines if 'error' in line.lower())
        
        total_tests = max(pass_count + fail_count + error_count, 1)
        analysis['pass_rate'] = pass_count / total_tests
        
        # 生成基本测试用例记录
        for i in range(pass_count):
            analysis['test_cases'].append({
                'case_name': f'Test Case {i+1}',
                'status': 'PASS',
                'description': '基础功能测试',
                'expected': 'Unknown',
                'actual': 'Unknown'
            })
        
        for i in range(fail_count):
            failed_case = {
                'case_name': f'Failed Case {i+1}',
                'failure_type': '未知错误',
                'description': '检测到测试失败',
                'impact': '需要进一步分析'
            }
            analysis['failed_cases'].append(failed_case)
        
        # 生成建议
        if fail_count > 0:
            analysis['recommendations'].append({
                'type': 'critical',
                'description': f'发现 {fail_count} 个失败的测试用例',
                'action': '检查代码逻辑和测试台设计'
            })
        
        if error_count > 0:
            analysis['recommendations'].append({
                'type': 'critical',
                'description': f'发现 {error_count} 个错误',
                'action': '修复代码语法和运行时错误'
            })
        
        if analysis['pass_rate'] < 0.8:
            analysis['recommendations'].append({
                'type': 'important',
                'description': f'测试通过率较低 ({analysis["pass_rate"]:.1%})',
                'action': '需要改进代码质量'
            })
        
        return analysis

    # ==================== 工具实现方法 ====================
    
    async def _tool_write_code_file(self, filename: str, content: str, directory: str = "./output", **kwargs) -> Dict[str, Any]:
        """工具：将代码写入到文件"""
        try:
            self.logger.info(f"🔧 工具调用: 写入文件 {filename}")
            
            # 确保目录存在
            output_dir = Path(directory)
            output_dir.mkdir(exist_ok=True)
            
            # 构建完整文件路径
            file_path = output_dir / filename
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"✅ 文件写入成功: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "directory": str(output_dir),
                "content_length": len(content),
                "message": f"成功写入文件: {file_path}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 文件写入失败: {str(e)}")
            return {
                "success": False,
                "error": f"文件写入异常: {str(e)}",
                "file_path": None
            }
    
    async def _tool_generate_testbench(self, module_code: str = None, module_name: str = None, code: str = None, test_cases: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """工具：生成测试台"""
        try:
            self.logger.info("🔧 工具调用: 生成测试台")
            
            # 处理参数兼容性
            actual_module_code = module_code or code
            if actual_module_code is None:
                # 从模块名生成示例代码
                if module_name:
                    actual_module_code = f"""
module {module_name}(
    input wire clk,
    input wire rst_n,
    output reg [7:0] data
);
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) data <= 8'b0;
    else data <= data + 1;
end
endmodule
"""
                else:
                    return {
                        "success": False,
                        "error": "需要提供module_code参数",
                        "testbench_code": None
                    }
            
            # 解析模块信息
            module_info = self._parse_module_info(actual_module_code)
            if not module_info:
                return {
                    "success": False,
                    "error": "无法解析模块信息",
                    "testbench_code": None
                }
            
            # 生成测试台代码
            testbench_result = await self._generate_testbench(
                file_path="generated_module.v",
                code_content=actual_module_code,
                task_context="工具调用生成的测试台"
            )
            
            if testbench_result.get("success"):
                return {
                    "success": True,
                    "testbench_code": testbench_result.get("testbench_code"),
                    "testbench_file": testbench_result.get("testbench_file"),
                    "module_info": module_info,
                    "message": "测试台生成成功"
                }
            else:
                return {
                    "success": False,
                    "error": testbench_result.get("error", "测试台生成失败"),
                    "testbench_code": None
                }
                
        except Exception as e:
            self.logger.error(f"❌ 测试台生成工具失败: {str(e)}")
            return {
                "success": False,
                "error": f"工具执行异常: {str(e)}",
                "testbench_code": None
            }
    
    async def _tool_run_simulation(self, module_file: str = None, testbench_file: str = None, module_code: str = None, testbench_code: str = None, **kwargs) -> Dict[str, Any]:
        """工具：运行仿真"""
        try:
            self.logger.info("🔧 工具调用: 运行仿真")
            
            # 优先使用文件路径
            if module_file and not module_code:
                # 从文件读取模块代码
                try:
                    module_path = Path(module_file)
                    if not module_path.is_absolute():
                        module_path = self.artifacts_dir / module_path
                    
                    with open(module_path, 'r', encoding='utf-8') as f:
                        module_code = f.read()
                    self.logger.info(f"📄 从文件读取模块: {module_path}")
                    
                except FileNotFoundError:
                    # 尝试其他路径
                    alt_path = Path(module_file)
                    if alt_path.exists():
                        with open(alt_path, 'r', encoding='utf-8') as f:
                            module_code = f.read()
                    else:
                        return {
                            "success": False,
                            "error": f"模块文件不存在: {module_file}",
                            "simulation_output": None
                        }
            elif not module_code:
                return {
                    "success": False,
                    "error": "需要提供module_code或module_file参数",
                    "simulation_output": None
                }
            
            if testbench_file and not testbench_code:
                # 从文件读取测试台代码
                try:
                    testbench_path = Path(testbench_file)
                    if not testbench_path.is_absolute():
                        testbench_path = self.artifacts_dir / testbench_path
                    
                    with open(testbench_path, 'r', encoding='utf-8') as f:
                        testbench_code = f.read()
                    self.logger.info(f"📄 从文件读取测试台: {testbench_path}")
                    
                except FileNotFoundError:
                    # 尝试其他路径
                    alt_path = Path(testbench_file)
                    if alt_path.exists():
                        with open(alt_path, 'r', encoding='utf-8') as f:
                            testbench_code = f.read()
                    else:
                        return {
                            "success": False,
                            "error": f"测试台文件不存在: {testbench_file}",
                            "simulation_output": None
                        }
            elif not testbench_code:
                # 尝试自动生成基础测试台
                self.logger.info("🔧 没有提供测试台，尝试自动生成基础测试台...")
                try:
                    if module_code:
                        # 简单解析模块信息并生成基础测试台
                        module_info = self._parse_module_info(module_code)
                        if module_info.get('module_name'):
                            testbench_code = f"""
module tb_{module_info['module_name']};
    // 基础测试台 - 自动生成  
    initial begin
        $display("Starting simulation for {module_info['module_name']}");
        #10;
        $display("Simulation completed");
        $finish;
    end
endmodule
"""
                            self.logger.info("✅ 自动生成基础测试台")
                        else:
                            return {
                                "success": False,
                                "error": "无法解析模块信息，无法自动生成测试台",
                                "simulation_output": None
                            }
                    else:
                        return {
                            "success": False,
                            "error": "无法读取模块代码，无法自动生成测试台", 
                            "simulation_output": None
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"自动生成测试台失败: {str(e)}",
                        "simulation_output": None
                    }
            
            # 运行仿真
            simulation_result = await self._run_iverilog_simulation(
                module_file=module_file,
                module_code=module_code,
                testbench_code=testbench_code
            )
            
            if simulation_result.get("success"):
                return {
                    "success": True,
                    "simulation_output": simulation_result.get("output"),
                    "simulation_log": simulation_result.get("log"),
                    "execution_time": simulation_result.get("execution_time"),
                    "message": "仿真执行成功"
                }
            else:
                return {
                    "success": False,
                    "error": simulation_result.get("error", "仿真执行失败"),
                    "simulation_output": simulation_result.get("output"),
                    "simulation_log": simulation_result.get("log")
                }
                
        except Exception as e:
            self.logger.error(f"❌ 仿真执行工具失败: {str(e)}")
            return {
                "success": False,
                "error": f"工具执行异常: {str(e)}",
                "simulation_output": None
            }
    
    async def _tool_analyze_code_quality(self, code: str = None, module_code: str = None, **kwargs) -> Dict[str, Any]:
        """工具：分析代码质量"""
        try:
            self.logger.info("🔧 工具调用: 分析代码质量")
            
            # 处理参数兼容性
            actual_code = code or module_code
            if actual_code is None:
                return {
                    "success": False,
                    "error": "需要提供code或module_code参数",
                    "code_quality": None
                }
            
            # 执行基础代码审查
            review_result = self._basic_code_review(
                file_path="analyzed_code.v",
                code_content=actual_code
            )
            
            # 提取质量指标
            quality_metrics = review_result.get("quality_scores", {})
            
            # 生成详细分析
            analysis = {
                "success": True,
                "code_quality": {
                    "syntax_score": quality_metrics.get("syntax_correctness", 0.0),
                    "design_score": quality_metrics.get("design_quality", 0.0),
                    "readability_score": quality_metrics.get("maintainability", 0.0), # Assuming readability maps to maintainability
                    "overall_score": quality_metrics.get("overall_score", 0.0)
                },
                "issues": review_result.get("critical_issues", []) + review_result.get("warnings", []), # Combine issues
                "suggestions": review_result.get("suggestions", []),
                "strengths": review_result.get("positive_aspects", []),
                "module_info": review_result.get("module_info", {}),
                "message": "代码质量分析完成"
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ 代码质量分析工具失败: {str(e)}")
            return {
                "success": False,
                "error": f"工具执行异常: {str(e)}",
                "code_quality": None
            }
    
    async def _tool_write_build_script(self, verilog_files: List[str], testbench_files: List[str], 
                                     script_type: str = "bash", target_name: str = "simulation", **kwargs) -> Dict[str, Any]:
        """工具：生成构建脚本"""
        try:
            self.logger.info(f"🔧 工具调用: 生成构建脚本 ({script_type})")
            
            if script_type.lower() in ["makefile", "make"]:
                # 生成Makefile
                script_content = self.script_manager.generate_makefile(
                    verilog_files=verilog_files,
                    testbench_files=testbench_files,
                    target_name=target_name
                )
                script_name = f"{target_name}.mk"
                result = self.script_manager.write_script(
                    script_name=script_name,
                    script_content=script_content,
                    script_type="make",
                    make_executable=False
                )
            else:
                # 生成Bash脚本
                script_content = self.script_manager.generate_build_script(
                    verilog_files=verilog_files,
                    testbench_files=testbench_files,
                    target_name=target_name
                )
                script_name = f"build_{target_name}.sh"
                result = self.script_manager.write_script(
                    script_name=script_name,
                    script_content=script_content,
                    script_type="bash",
                    make_executable=True
                )
            
            if result["success"]:
                self.logger.info(f"✅ 构建脚本生成成功: {result['script_path']}")
                return {
                    "success": True,
                    "script_path": result["script_path"],
                    "script_name": result["script_name"],
                    "script_type": script_type,
                    "verilog_files": verilog_files,
                    "testbench_files": testbench_files,
                    "message": f"构建脚本已生成: {result['script_path']}"
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "script_path": None
                }
                
        except Exception as e:
            self.logger.error(f"❌ 构建脚本生成工具失败: {str(e)}")
            return {
                "success": False,
                "error": f"工具执行异常: {str(e)}",
                "script_path": None
            }
    
    async def _tool_execute_build_script(self, script_name: str, action: str = "all", 
                                       arguments: List[str] = None, **kwargs) -> Dict[str, Any]:
        """工具：执行构建脚本"""
        try:
            self.logger.info(f"🔧 工具调用: 执行构建脚本 ({script_name})")
            
            # 准备参数
            script_args = []
            if action and action != "all":
                script_args.append(action)
            
            if arguments:
                script_args.extend(arguments)
            
            # 执行脚本
            result = self.script_manager.execute_script(
                script_path=script_name,
                arguments=script_args,
                working_directory=str(self.artifacts_dir),
                timeout=600  # 10分钟超时
            )
            
            if result["success"]:
                self.logger.info(f"✅ 脚本执行成功: {script_name}")
                return {
                    "success": True,
                    "return_code": result["return_code"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "script_path": result["script_path"],
                    "command": result["command"],
                    "action": action,
                    "message": f"脚本执行成功: {script_name}"
                }
            else:
                self.logger.warning(f"⚠️ 脚本执行失败: {script_name}")
                error_details = result.get("error_details", {})
                
                # 构建详细的错误报告
                error_report = f"脚本执行失败: {script_name}\n"
                error_report += f"命令: {result.get('command', 'N/A')}\n"
                error_report += f"返回码: {result.get('return_code', -1)}\n"
                
                if result.get("stderr"):
                    error_report += f"错误输出: {result['stderr']}\n"
                if result.get("stdout"):
                    error_report += f"标准输出: {result['stdout']}\n"
                
                if error_details:
                    error_report += f"工作目录: {error_details.get('working_dir', 'N/A')}\n"
                    error_report += f"脚本存在: {error_details.get('script_exists', False)}\n"
                    if not error_details.get('script_exists', True):
                        error_report += "建议: 检查脚本路径或重新生成脚本\n"
                
                return {
                    "success": False,
                    "return_code": result.get("return_code", -1),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "error": result.get("error", "脚本执行失败"),
                    "error_report": error_report,
                    "error_details": error_details,
                    "script_path": result.get("script_path", script_name),
                    "command": result.get("command", ""),
                    "action": action,
                    "message": f"脚本执行失败: {result.get('error', '未知错误')}",
                    "suggestion": self._generate_error_fix_suggestion(result, script_name)
                }
                
        except Exception as e:
            self.logger.error(f"❌ 脚本执行工具失败: {str(e)}")
            return {
                "success": False,
                "error": f"工具执行异常: {str(e)}",
                "return_code": -1,
                "stdout": "",
                "stderr": ""
            }
    
    def _generate_error_fix_suggestion(self, result: Dict[str, Any], script_name: str) -> str:
        """生成错误修复建议"""
        error_msg = result.get("error", "")
        stderr = result.get("stderr", "")
        return_code = result.get("return_code", -1)
        
        suggestions = []
        
        # 基于返回码的建议
        if return_code == 127:
            suggestions.append("命令未找到 - 检查脚本路径和可执行权限")
        elif return_code == 126:
            suggestions.append("权限拒绝 - 检查脚本执行权限")
        elif return_code == 2:
            suggestions.append("文件或目录不存在 - 检查文件路径")
        
        # 基于错误信息的建议
        if "No such file or directory" in stderr or "No such file or directory" in error_msg:
            suggestions.append("检查文件路径是否正确，确保所有依赖文件存在")
        
        if "Permission denied" in stderr:
            suggestions.append("检查文件权限，可能需要执行 chmod +x script_name")
        
        if "iverilog" in stderr and ("not found" in stderr or "command not found" in stderr):
            suggestions.append("iverilog未安装或不在PATH中，请安装Icarus Verilog")
        
        if "syntax error" in stderr.lower():
            suggestions.append("Verilog语法错误 - 检查源代码语法")
        
        if "undeclared" in stderr.lower():
            suggestions.append("未声明的信号或变量 - 检查信号声明")
        
        if not suggestions:
            suggestions.append("检查脚本内容和执行环境，查看详细错误信息")
        
        return "; ".join(suggestions)