#!/usr/bin/env python3
"""
协调器增强方法 - 支持测试驱动的迭代开发
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import asyncio


class EnhancedCoordinatorMethods:
    """协调器增强方法集合"""
    
    async def coordinate_test_driven_task(self, initial_task: str, 
                                        testbench_path: str = None,
                                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """协调测试驱动的任务执行"""
        self.conversation_state = ConversationState.ACTIVE
        conversation_id = f"tdd_conv_{int(time.time())}"
        self.current_conversation_id = conversation_id
        
        self.logger.info(f"🧪 开始测试驱动任务协调: {conversation_id}")
        
        try:
            # 1. 增强任务分析
            enhanced_analysis = await self.analyze_test_driven_requirements(
                initial_task, testbench_path, context
            )
            
            # 2. 验证测试台文件
            if testbench_path:
                tb_validation = await self.validate_testbench_file(testbench_path)
                if not tb_validation["valid"]:
                    return {
                        "success": False,
                        "error": f"测试台验证失败: {tb_validation['error']}",
                        "conversation_id": conversation_id
                    }
                enhanced_analysis["testbench_info"] = tb_validation
            
            # 3. 执行测试驱动的多轮对话
            results = await self._execute_test_driven_conversation(
                conversation_id=conversation_id,
                enhanced_analysis=enhanced_analysis
            )
            
            self.conversation_state = ConversationState.COMPLETED
            return results
            
        except Exception as e:
            self.conversation_state = ConversationState.FAILED
            self.logger.error(f"❌ 测试驱动任务协调失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    async def analyze_test_driven_requirements(self, task_description: str, 
                                             testbench_path: str = None,
                                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析测试驱动的任务需求"""
        from enhanced_task_analysis import EnhancedTaskAnalyzer
        
        analyzer = EnhancedTaskAnalyzer()
        basic_analysis = analyzer.analyze_enhanced_task(task_description, context)
        
        # 如果用户显式提供了测试台路径，优先使用
        if testbench_path:
            basic_analysis["testbench_path"] = testbench_path
            basic_analysis["testbench_required"] = True
            basic_analysis["test_driven_development"] = True
        
        # 增加测试驱动特定的分析
        basic_analysis.update({
            "workflow_type": "test_driven_development",
            "max_iterations": 5,  # 最大迭代次数
            "iteration_strategy": "test_fail_analyze_fix",
            "success_criteria": "all_tests_pass"
        })
        
        return basic_analysis
    
    async def validate_testbench_file(self, testbench_path: str) -> Dict[str, Any]:
        """验证测试台文件"""
        try:
            tb_path = Path(testbench_path)
            
            if not tb_path.exists():
                return {
                    "valid": False,
                    "error": f"测试台文件不存在: {testbench_path}",
                    "path": testbench_path
                }
            
            # 读取测试台内容进行基本验证
            content = tb_path.read_text(encoding='utf-8')
            
            # 检查是否是有效的Verilog测试台
            validation_checks = {
                "has_module": "module" in content,
                "has_testbench_keywords": any(keyword in content.lower() 
                    for keyword in ["testbench", "tb", "test"]),
                "has_initial_block": "initial" in content,
                "has_endmodule": "endmodule" in content
            }
            
            if not all(validation_checks.values()):
                return {
                    "valid": False,
                    "error": f"测试台文件格式不正确: {validation_checks}",
                    "path": testbench_path
                }
            
            return {
                "valid": True,
                "path": str(tb_path.resolve()),
                "size": tb_path.stat().st_size,
                "validation_checks": validation_checks,
                "content_preview": content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证测试台文件时出错: {str(e)}",
                "path": testbench_path
            }
    
    async def _execute_test_driven_conversation(self, conversation_id: str,
                                              enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试驱动的对话流程"""
        max_iterations = enhanced_analysis.get("max_iterations", 5)
        current_iteration = 0
        design_files = []
        test_results = []
        
        self.logger.info(f"🔄 开始测试驱动迭代，最大迭代次数: {max_iterations}")
        
        while current_iteration < max_iterations:
            current_iteration += 1
            iteration_id = f"{conversation_id}_iter_{current_iteration}"
            
            self.logger.info(f"🔄 第 {current_iteration}/{max_iterations} 次迭代")
            
            # 阶段1: 设计生成
            design_result = await self._execute_design_phase(
                iteration_id, enhanced_analysis, design_files
            )
            
            if not design_result["success"]:
                self.logger.error(f"❌ 设计阶段失败: {design_result.get('error')}")
                continue
            
            design_files = design_result["design_files"]
            
            # 阶段2: 测试验证
            test_result = await self._execute_test_phase(
                iteration_id, enhanced_analysis, design_files
            )
            
            test_results.append({
                "iteration": current_iteration,
                "test_result": test_result,
                "design_files": design_files
            })
            
            # 检查测试是否通过
            if test_result.get("all_tests_passed", False):
                self.logger.info(f"✅ 第 {current_iteration} 次迭代测试通过！")
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "total_iterations": current_iteration,
                    "final_design_files": design_files,
                    "all_test_results": test_results,
                    "status": "completed_successfully"
                }
            
            # 阶段3: 分析和改进建议
            if current_iteration < max_iterations:
                analysis_result = await self._execute_analysis_phase(
                    iteration_id, test_result, enhanced_analysis
                )
                enhanced_analysis["improvement_suggestions"] = analysis_result.get("suggestions", [])
        
        # 达到最大迭代次数
        self.logger.warning(f"⚠️ 达到最大迭代次数 {max_iterations}，测试仍未全部通过")
        return {
            "success": False,
            "conversation_id": conversation_id,
            "total_iterations": max_iterations,
            "final_design_files": design_files,
            "all_test_results": test_results,
            "status": "max_iterations_reached",
            "error": "达到最大迭代次数，但测试仍有失败"
        }
    
    async def _execute_design_phase(self, iteration_id: str, analysis: Dict[str, Any], 
                                  previous_designs: List = None) -> Dict[str, Any]:
        """执行设计阶段"""
        self.logger.info(f"🎨 执行设计阶段: {iteration_id}")
        
        # 选择设计智能体
        design_agent = await self.select_agent_by_capability(AgentCapability.CODE_GENERATION)
        if not design_agent:
            return {"success": False, "error": "未找到设计智能体"}
        
        # 构建设计任务消息
        design_task = self._build_design_task_message(analysis, previous_designs)
        
        # 执行设计任务
        result = await design_agent.process_with_function_calling(
            user_request=design_task,
            max_iterations=3
        )
        
        return result
    
    async def _execute_test_phase(self, iteration_id: str, analysis: Dict[str, Any],
                                design_files: List) -> Dict[str, Any]:
        """执行测试阶段"""
        self.logger.info(f"🧪 执行测试阶段: {iteration_id}")
        
        # 选择测试智能体
        test_agent = await self.select_agent_by_capability(AgentCapability.VERIFICATION)
        if not test_agent:
            return {"success": False, "error": "未找到测试智能体"}
        
        # 构建测试任务消息
        test_task = self._build_test_task_message(analysis, design_files)
        
        # 执行测试任务
        result = await test_agent.process_with_function_calling(
            user_request=test_task,
            max_iterations=2
        )
        
        return result
    
    async def _execute_analysis_phase(self, iteration_id: str, test_result: Dict[str, Any],
                                    analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析阶段"""
        self.logger.info(f"🔍 执行分析阶段: {iteration_id}")
        
        # 选择分析智能体（可以是代码审查智能体）
        analysis_agent = await self.select_agent_by_capability(AgentCapability.CODE_REVIEW)
        if not analysis_agent:
            return {"success": False, "error": "未找到分析智能体"}
        
        # 构建分析任务消息
        analysis_task = self._build_analysis_task_message(test_result, analysis)
        
        # 执行分析任务
        result = await analysis_agent.process_with_function_calling(
            user_request=analysis_task,
            max_iterations=2
        )
        
        return result
    
    def _build_design_task_message(self, analysis: Dict[str, Any], 
                                 previous_designs: List = None) -> str:
        """构建设计任务消息"""
        message = f"""
请根据以下需求设计Verilog模块：

设计需求：
{analysis.get('design_requirements', '')}

测试台信息：
- 测试台路径: {analysis.get('testbench_path', '未指定')}
- 需要通过指定测试台: {'是' if analysis.get('testbench_required') else '否'}

"""
        
        if previous_designs:
            message += f"""
前一次设计的文件：
{[f['file_path'] for f in previous_designs]}

改进建议：
{analysis.get('improvement_suggestions', [])}
"""
        
        return message
    
    def _build_test_task_message(self, analysis: Dict[str, Any],
                               design_files: List) -> str:
        """构建测试任务消息"""
        return f"""
请使用指定的测试台对设计进行验证：

测试台路径: {analysis.get('testbench_path')}
设计文件: {[f.get('file_path') for f in design_files]}

请运行仿真并报告：
1. 测试是否通过
2. 如果失败，详细的错误信息
3. 失败原因分析
"""
    
    def _build_analysis_task_message(self, test_result: Dict[str, Any],
                                   analysis: Dict[str, Any]) -> str:
        """构建分析任务消息"""
        return f"""
请分析测试失败的原因并提供改进建议：

测试结果：
{json.dumps(test_result, indent=2, ensure_ascii=False)}

请提供：
1. 失败原因的深度分析  
2. 具体的代码改进建议
3. 可能的设计方案调整
"""


# 这些方法需要集成到现有的 CentralizedCoordinator 类中