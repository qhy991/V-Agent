#!/usr/bin/env python3
"""
真实LLM驱动的代码审查智能体

Real LLM-powered Code Review Agent
"""

import json
import asyncio
from typing import Dict, Any, Set
from pathlib import Path

from core.base_agent import BaseAgent, TaskMessage
from core.enums import AgentCapability
from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from config.config import FrameworkConfig


class RealCodeReviewAgent(BaseAgent):
    """真实LLM驱动的代码审查智能体"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="real_code_review_agent",
            role="code_reviewer",
            capabilities={
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ANALYSIS,
                AgentCapability.SPECIFICATION_ANALYSIS
            }
        )
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        self.logger.info(f"🔍 真实代码审查智能体初始化完成")
    
    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_REVIEW,
            AgentCapability.QUALITY_ANALYSIS,
            AgentCapability.SPECIFICATION_ANALYSIS
        }
    
    def get_specialty_description(self) -> str:
        return "真实LLM驱动的代码审查智能体，提供专业的Verilog/SystemVerilog代码质量分析和改进建议"
    
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
            
            # 4. 计算整体质量指标
            overall_quality = self._calculate_overall_quality(review_results)
            
            # 5. 保存审查报告
            output_files = await self._save_review_files(
                comprehensive_report, review_results, task_id
            )
            
            # 6. 创建标准化响应
            response = await self._create_review_response(
                task_id, review_results, overall_quality, output_files, comprehensive_report
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
    
    def _calculate_overall_quality(self, review_results: list) -> QualityMetrics:
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
        
        return QualityMetrics(
            overall_score=overall_score,
            syntax_score=avg_syntax,
            functionality_score=avg_design,
            test_coverage=0.0,  # 审查阶段无测试覆盖率
            documentation_quality=avg_maintainability,
            performance_score=avg_performance
        )
    
    async def _save_review_files(self, comprehensive_report: str, review_results: list,
                               task_id: str) -> list:
        """保存审查报告文件"""
        output_files = []
        
        try:
            # 确保输出目录存在
            output_dir = Path("./output")
            output_dir.mkdir(exist_ok=True)
            
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
                "detailed_results": review_results
            }
            
            details_path = output_dir / f"review_details_{task_id}.json"
            details_ref = await self.save_result_to_file(
                content=json.dumps(detailed_results, indent=2, ensure_ascii=False),
                file_path=str(details_path),
                file_type="json"
            )
            output_files.append(details_ref)
            
            self.logger.info(f"💾 审查报告保存完成: {len(output_files)} 个文件")
            return output_files
            
        except Exception as e:
            self.logger.error(f"❌ 保存审查报告失败: {str(e)}")
            return []
    
    async def _create_review_response(self, task_id: str, review_results: list,
                                    overall_quality: QualityMetrics, output_files: list,
                                    comprehensive_report: str) -> str:
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
        
        # 添加下一步建议
        builder.add_next_step("仔细阅读综合审查报告")
        builder.add_next_step("优先修复所有关键问题")
        
        if total_warnings > 0:
            builder.add_next_step("处理警告问题以提高代码质量")
        
        if overall_quality.performance_score < 0.7:
            builder.add_next_step("考虑性能优化")
        
        builder.add_next_step("在修复后重新进行代码审查")
        
        # 添加元数据
        builder.add_metadata("files_reviewed", len(review_results))
        builder.add_metadata("critical_issues", total_critical)
        builder.add_metadata("warnings", total_warnings)
        builder.add_metadata("overall_quality_score", overall_quality.overall_score)
        builder.add_metadata("review_type", "comprehensive")
        builder.add_metadata("llm_powered", True)
        
        # 构建响应 - 代码审查任务总是100%完成
        status = TaskStatus.SUCCESS
        completion = 100.0
        
        # 构建消息
        message_parts = [
            f"代码审查完成，共审查 {len(review_results)} 个文件"
        ]
        
        if total_critical > 0:
            message_parts.append(f"发现 {total_critical} 个关键问题")
        if total_warnings > 0:
            message_parts.append(f"{total_warnings} 个警告")
            
        message_parts.append(f"整体质量分数: {overall_quality.overall_score:.2f}")
        
        response = builder.build(
            response_type=ResponseType.QUALITY_REPORT,
            status=status,
            message=", ".join(message_parts),
            completion_percentage=completion,
            quality_metrics=overall_quality
        )
        
        return response.format_response(ResponseFormat.JSON)