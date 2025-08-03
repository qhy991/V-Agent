"""
增强的BaseAgent - 集成JSON Schema验证和智能修复
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import logging

# 导入现有的基础类
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.base_agent import BaseAgent
from core.function_calling import ToolCall, ToolResult
from .schema_validator import SchemaValidator, ValidationResult
from .parameter_repairer import ParameterRepairer, RepairResult
from .flexible_schema_adapter import FlexibleSchemaAdapter, SchemaAdaptationResult

logger = logging.getLogger(__name__)

@dataclass
class EnhancedToolDefinition:
    """增强的工具定义"""
    name: str
    func: Callable
    description: str
    schema: Dict[str, Any]
    security_level: str = "normal"  # low, normal, high
    category: str = "general"
    version: str = "1.0"
    deprecated: bool = False

class EnhancedBaseAgent(BaseAgent):
    """集成Schema验证的增强BaseAgent"""
    
    def __init__(self, agent_id: str, role: str, capabilities: set, config=None):
        super().__init__(agent_id, role, capabilities)
        
        # Schema系统组件
        self.schema_validator = SchemaValidator()
        self.parameter_repairer = ParameterRepairer()
        self.schema_adapter = FlexibleSchemaAdapter()
        
        # 增强的工具注册表
        self.enhanced_tools: Dict[str, EnhancedToolDefinition] = {}
        self.validation_cache: Dict[str, ValidationResult] = {}
        
        # 配置选项
        self.auto_repair_threshold = 0.8  # 自动修复的置信度阈值
        self.max_repair_attempts = 3  # 最大修复尝试次数
        self.enable_validation_cache = True
        
        logger.info(f"✅ 增强BaseAgent初始化完成: {agent_id}")
    
    def register_enhanced_tool(self, name: str, func: Callable, description: str,
                              schema: Dict[str, Any], security_level: str = "normal",
                              category: str = "general", version: str = "1.0") -> None:
        """
        注册增强工具（支持Schema验证）
        
        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            schema: JSON Schema定义
            security_level: 安全级别 (low/normal/high)
            category: 工具分类
            version: 工具版本
        """
        try:
            # 验证Schema格式
            self._validate_tool_schema(schema)
            
            # 创建增强工具定义
            tool_def = EnhancedToolDefinition(
                name=name,
                func=func,
                description=description,
                schema=schema,
                security_level=security_level,
                category=category,
                version=version
            )
            
            # 注册到增强注册表
            self.enhanced_tools[name] = tool_def
            
            # 同时注册到父类（向后兼容）
            self.register_function_calling_tool(
                name=name,
                func=func,
                description=description,
                parameters=self._convert_schema_to_legacy_format(schema)
            )
            
            logger.info(f"🔧 增强工具注册成功: {name} (安全级别: {security_level})")
            
        except Exception as e:
            logger.error(f"❌ 增强工具注册失败 {name}: {str(e)}")
            raise
    
    async def process_with_enhanced_validation(self, user_request: str, 
                                             max_iterations: int = 10) -> Dict[str, Any]:
        """
        使用增强验证处理用户请求
        
        Args:
            user_request: 用户请求
            max_iterations: 最大迭代次数
            
        Returns:
            处理结果
        """
        conversation_history = []
        iteration_count = 0
        
        # 跟踪失败的工具，区分参数验证失败和真正的执行失败
        permanently_failed_tools = set()  # 真正失败的工具（执行错误等）
        param_validation_failed_tools = set()  # 参数验证失败的工具（可在下次迭代重试）
        
        logger.info(f"🚀 开始增强验证处理: {user_request[:100]}...")
        
        while iteration_count < max_iterations:
            iteration_count += 1
            logger.info(f"🔄 第 {iteration_count}/{max_iterations} 次迭代")
            
            try:
                # 1. 调用LLM获取响应
                conversation = self._build_conversation_with_history(user_request, conversation_history)
                llm_response = await self._call_llm_for_function_calling(conversation)
                
                conversation_history.append({
                    "role": "assistant", 
                    "content": llm_response,
                    "iteration": iteration_count
                })
                
                # 2. 解析工具调用
                tool_calls = self._parse_tool_calls_from_response(llm_response)
                
                if not tool_calls:
                    # 没有工具调用，直接返回响应
                    return {
                        "success": True,
                        "response": llm_response,
                        "iterations": iteration_count,
                        "conversation_history": conversation_history
                    }
                
                # 3. 执行工具调用（带智能重试机制）
                all_tools_successful = True
                tool_results = []
                current_iteration_failed_tools = set()
                
                # 在新迭代开始时，清空参数验证失败的工具（给它们重试机会）
                if iteration_count > 1:
                    logger.info(f"🔄 第{iteration_count}次迭代：清空参数验证失败工具，允许重试")
                    param_validation_failed_tools.clear()
                
                for i, tool_call in enumerate(tool_calls):
                    # 只跳过真正永久失败的工具的依赖工具
                    if self._should_skip_tool_due_to_dependencies(tool_call, permanently_failed_tools):
                        logger.warning(f"⚠️ 跳过工具 {tool_call.tool_name}，因为依赖的关键工具已永久失败")
                        skipped_result = ToolResult(
                            call_id=tool_call.call_id,
                            success=False,
                            error=f"跳过执行：关键工具 {', '.join(permanently_failed_tools)} 已永久失败",
                            result=None
                        )
                        tool_results.append(skipped_result)
                        all_tools_successful = False
                        continue
                    
                    result = await self._execute_enhanced_tool_call(tool_call)
                    tool_results.append(result)
                    
                    if not result.success:
                        all_tools_successful = False
                        current_iteration_failed_tools.add(tool_call.tool_name)
                        
                        # 区分参数验证失败和其他执行失败
                        if "参数验证失败" in result.error:
                            param_validation_failed_tools.add(tool_call.tool_name)
                            logger.warning(f"⚠️ {tool_call.tool_name} 参数验证失败，将在下次迭代重试")
                        else:
                            # 真正的执行失败
                            permanently_failed_tools.add(tool_call.tool_name)
                            logger.error(f"❌ {tool_call.tool_name} 执行失败，标记为永久失败")
                            
                            # 如果是关键工具的真正失败，停止执行后续工具
                            if self._is_critical_tool(tool_call.tool_name):
                                logger.error(f"❌ 关键工具永久失败: {tool_call.tool_name}，停止后续工具执行")
                                remaining_tools = tool_calls[i+1:]
                                for remaining_tool in remaining_tools:
                                    skipped_result = ToolResult(
                                        call_id=remaining_tool.call_id,
                                        success=False,
                                        error=f"跳过执行：关键工具 {tool_call.tool_name} 已永久失败",
                                        result=None
                                    )
                                    tool_results.append(skipped_result)
                                break
                
                # 4. 处理工具调用结果
                results_summary = self._format_tool_results(tool_calls, tool_results)
                self.logger.info(f"🔨 工具执行结果: {results_summary}")
                
                # 提取仿真结果和错误信息（包括成功和失败的情况）
                simulation_info = self._extract_simulation_and_error_info(tool_results)
                self.logger.info(f"🔨 仿真结果: {simulation_info}")
                
                # 检查是否有仿真成功完成
                simulation_success = self._check_simulation_success(tool_results)
                
                if simulation_success:
                    # 仿真成功完成，立即结束任务
                    logger.info("🎯 仿真成功完成，任务结束")
                    return {
                        "success": True,
                        "response": f"🎉 **任务完成**！\n\n仿真成功通过，所有测试用例执行完成。\n\n工具执行结果:\n{results_summary}\n\n🎯 **仿真结果分析**:\n{simulation_info}",
                        "iterations": iteration_count,
                        "conversation_history": conversation_history,
                        "completion_reason": "simulation_success"
                    }
                elif simulation_info:
                    # 有仿真相关信息，传递给agent进行分析
                    conversation_history.append({
                        "role": "user",
                        "content": f"工具执行结果:\n{results_summary}\n\n🎯 **仿真结果分析**:\n{simulation_info}\n\n⚠️ **重要指导**：\n\n如果仿真失败，你必须按照以下步骤执行：\n\n1. **第一步：调用 analyze_test_failures 分析错误**\n   - 将编译错误、仿真错误等信息传递给该工具\n   - 获取详细的错误分析和修复建议\n\n2. **第二步：根据分析结果修复代码**\n   - 如果测试台有语法错误，重新生成测试台\n   - 如果设计代码有问题，修改设计代码\n   - 不要只是重新执行相同的工具\n\n3. **第三步：验证修复效果**\n   - 重新运行仿真验证修复是否成功\n   - 如果仍有问题，重复分析-修复-验证流程\n\n请严格按照这个流程执行，确保进行实际的代码修复而不是简单的工具重试。"
                    })
                elif all_tools_successful:
                    # 所有工具成功但没有仿真信息
                    conversation_history.append({
                        "role": "user",
                        "content": f"工具执行结果:\n{results_summary}\n\n请分析工具执行结果并决定下一步操作。"
                    })
                else:
                    # 有工具调用失败，构建错误反馈
                    error_feedback = self._build_enhanced_error_feedback(
                        tool_calls, tool_results, 
                        param_validation_failed_tools, 
                        permanently_failed_tools,
                        iteration_count
                    )
                    conversation_history.append({
                        "role": "user", 
                        "content": error_feedback
                    })
                
            except Exception as e:
                logger.error(f"❌ 迭代 {iteration_count} 处理异常: {str(e)}")
                return {
                    "success": False,
                    "error": f"处理异常: {str(e)}",
                    "iterations": iteration_count,
                    "conversation_history": conversation_history
                }
        
        # 达到最大迭代次数
        logger.warning(f"⚠️ 达到最大迭代次数 {max_iterations}")
        return {
            "success": False,
            "error": f"达到最大迭代次数 {max_iterations}",
            "iterations": max_iterations,
            "conversation_history": conversation_history
        }
    
    async def _execute_enhanced_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """
        执行增强的工具调用（带Schema验证和智能修复）
        
        Args:
            tool_call: 工具调用
            
        Returns:
            工具执行结果
        """
        tool_name = tool_call.tool_name
        
        # 检查工具是否存在
        if tool_name not in self.enhanced_tools:
            logger.warning(f"⚠️ 工具 {tool_name} 未在增强注册表中，回退到传统方式")
            return await self._execute_tool_call_with_retry(tool_call)
        
        tool_def = self.enhanced_tools[tool_name]
        
        # 1. 智能参数适配（使用统一Schema系统）
        from .unified_schemas import UnifiedSchemas
        
        # 首先使用统一Schema系统进行标准化
        try:
            normalized_parameters = UnifiedSchemas.validate_and_normalize_parameters(
                tool_name, tool_call.parameters
            )
            logger.info(f"🎯 {tool_name} 使用统一Schema标准化参数")
        except Exception as e:
            logger.debug(f"统一Schema处理失败，使用原参数: {e}")
            normalized_parameters = tool_call.parameters
        
        # 然后进行传统的适配
        adaptation_result = self.schema_adapter.adapt_parameters(
            normalized_parameters, tool_def.schema, tool_name
        )
        
        if not adaptation_result.success:
            logger.warning(f"⚠️ {tool_name} 参数适配失败: {adaptation_result.warnings}")
            parameters_to_validate = tool_call.parameters  # 使用原参数
        else:
            parameters_to_validate = adaptation_result.adapted_data
            if adaptation_result.transformations:
                logger.info(f"🔄 {tool_name} 参数适配成功: {', '.join(adaptation_result.transformations)}")
        
        # 2. Schema验证（使用适配后的参数）
        validation_result = await self._validate_tool_parameters(
            parameters_to_validate, tool_def.schema, tool_name
        )
        
        if validation_result.is_valid:
            # 验证通过，使用适配后的参数执行
            logger.info(f"✅ {tool_name} 参数验证通过")
            adapted_tool_call = ToolCall(
                tool_name=tool_call.tool_name,
                parameters=parameters_to_validate,
                call_id=tool_call.call_id
            )
            return await self._execute_validated_tool(adapted_tool_call, tool_def)
        
        # 3. 验证失败，尝试智能修复（使用适配后的参数）
        logger.warning(f"⚠️ {tool_name} 参数验证失败，尝试智能修复")
        adapted_tool_call_for_repair = ToolCall(
            tool_name=tool_call.tool_name,
            parameters=parameters_to_validate,
            call_id=tool_call.call_id
        )
        repair_result = await self._attempt_parameter_repair(
            adapted_tool_call_for_repair, tool_def, validation_result
        )
        
        if repair_result.success and repair_result.repaired_data:
            # 修复成功，使用修复后的参数执行
            logger.info(f"🔧 {tool_name} 参数修复成功")
            repaired_tool_call = ToolCall(
                tool_name=tool_call.tool_name,
                parameters=repair_result.repaired_data,
                call_id=tool_call.call_id
            )
            return await self._execute_validated_tool(repaired_tool_call, tool_def)
        
        # 3. 修复失败，返回详细错误信息给Agent
        logger.error(f"❌ {tool_name} 参数修复失败")
        return ToolResult(
            call_id=tool_call.call_id,
            success=False,
            error=self._build_validation_error_message(validation_result, repair_result),
            result=None
        )
    
    async def _validate_tool_parameters(self, parameters: Dict[str, Any], 
                                       schema: Dict[str, Any], 
                                       tool_name: str) -> ValidationResult:
        """验证工具参数"""
        # 检查缓存
        if self.enable_validation_cache:
            cache_key = f"{tool_name}:{hash(json.dumps(parameters, sort_keys=True))}"
            if cache_key in self.validation_cache:
                return self.validation_cache[cache_key]
        
        # 执行验证
        validation_result = self.schema_validator.validate(parameters, schema)
        
        # 缓存结果
        if self.enable_validation_cache:
            self.validation_cache[cache_key] = validation_result
        
        return validation_result
    
    async def _attempt_parameter_repair(self, tool_call: ToolCall, 
                                       tool_def: EnhancedToolDefinition,
                                       validation_result: ValidationResult) -> RepairResult:
        """尝试参数修复"""
        repair_result = self.parameter_repairer.repair_parameters(
            tool_call.parameters, tool_def.schema, validation_result
        )
        
        # 如果有高置信度的修复建议，再次验证修复后的参数
        if repair_result.success and repair_result.repaired_data:
            re_validation = await self._validate_tool_parameters(
                repair_result.repaired_data, tool_def.schema, tool_def.name
            )
            
            if not re_validation.is_valid:
                repair_result.success = False
                logger.warning(f"⚠️ 修复后的参数仍然无效: {tool_def.name}")
        
        return repair_result
    
    async def _execute_validated_tool(self, tool_call: ToolCall, 
                                     tool_def: EnhancedToolDefinition) -> ToolResult:
        """执行已验证的工具"""
        start_time = time.time()
        
        try:
            # 执行工具函数
            if asyncio.iscoroutinefunction(tool_def.func):
                result = await tool_def.func(**tool_call.parameters)
            else:
                result = tool_def.func(**tool_call.parameters)
            
            execution_time = time.time() - start_time
            
            # 检查工具返回的结果
            if isinstance(result, dict):
                # 如果工具返回字典，检查success字段
                tool_success = result.get('success', True)
                tool_error = result.get('error', None)
                
                # 构建完整的错误信息
                error_message = None
                if not tool_success:
                    # 收集所有可能的错误信息
                    error_parts = []
                    if tool_error:
                        error_parts.append(f"错误: {tool_error}")
                    
                    # 添加编译错误
                    compilation_errors = result.get('compilation_errors', '')
                    if compilation_errors:
                        error_parts.append(f"编译错误:\n{compilation_errors}")
                    
                    # 添加仿真错误
                    simulation_errors = result.get('simulation_errors', '')
                    if simulation_errors:
                        error_parts.append(f"仿真错误:\n{simulation_errors}")
                    
                    # 添加错误消息
                    error_msg = result.get('error_message', '')
                    if error_msg:
                        error_parts.append(f"错误消息: {error_msg}")
                    
                    # 如果没有具体错误信息，使用默认消息
                    if not error_parts:
                        error_parts.append("工具执行失败，但未提供具体错误信息")
                    
                    error_message = "\n\n".join(error_parts)
                
                if tool_success:
                    logger.info(f"🎯 {tool_def.name} 执行成功 ({execution_time:.2f}s)")
                    return ToolResult(
                        call_id=tool_call.call_id,
                        success=True,
                        error=None,
                        result=result
                    )
                else:
                    logger.error(f"❌ {tool_def.name} 执行失败 ({execution_time:.2f}s): {error_message}")
                    return ToolResult(
                        call_id=tool_call.call_id,
                        success=False,
                        error=error_message,
                        result=result
                    )
            else:
                # 如果工具返回非字典，假设成功
                logger.info(f"🎯 {tool_def.name} 执行成功 ({execution_time:.2f}s)")
                return ToolResult(
                    call_id=tool_call.call_id,
                    success=True,
                    error=None,
                    result=result
                )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {tool_def.name} 执行异常 ({execution_time:.2f}s): {str(e)}")
            
            return ToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"工具执行异常: {str(e)}",
                result=None
            )
    
    def _build_validation_error_message(self, validation_result: ValidationResult,
                                       repair_result: RepairResult) -> str:
        """构建增强的验证错误消息，包含详细的修复指令"""
        message = "🚨 参数验证失败，请根据以下指导修正参数:\n\n"
        
        # 添加验证错误详情
        message += "📋 **错误详情**:\n"
        message += validation_result.get_error_summary()
        
        # 添加智能修复建议
        if repair_result.suggestions:
            message += "\n" + "="*60 + "\n"
            message += "🔧 **智能修复建议**:\n\n"
            
            for i, suggestion in enumerate(repair_result.suggestions, 1):
                message += f"{i}. 参数 `{suggestion.field_path}`:\n"
                message += f"   ❌ 问题: {suggestion.explanation}\n"
                message += f"   ✅ 建议值: `{suggestion.suggested_value}`\n"
                message += f"   🔍 置信度: {suggestion.confidence:.1%}\n\n"
        
        # 添加给Agent的详细修复指令
        message += "\n" + "="*60 + "\n"
        message += "📝 **修复指令**:\n\n"
        
        # 如果有LLM修复提示，使用它
        if repair_result.llm_prompt:
            message += repair_result.llm_prompt
        else:
            # 否则生成通用修复指令
            message += self._generate_generic_repair_instructions(validation_result)
        
        # 添加具体的修复示例
        message += "\n\n" + "="*60 + "\n"
        message += "📚 **修复示例**:\n\n"
        message += self._generate_repair_examples(validation_result, repair_result)
        
        # 添加重新调用指令
        message += "\n\n🎯 **请重新调用工具，使用修复后的参数**。\n"
        message += "确保所有参数都符合Schema要求，然后重新执行相同的工具调用。"
        
        return message
    
    def _generate_generic_repair_instructions(self, validation_result: ValidationResult) -> str:
        """生成通用修复指令"""
        instructions = "请根据以下规则修正参数:\n\n"
        
        # 分析常见错误类型并提供指导
        error_summary = validation_result.get_error_summary()
        
        if "required" in error_summary.lower():
            instructions += "• **缺少必需参数**: 请确保提供所有标记为'required'的参数\n"
        
        if "type" in error_summary.lower():
            instructions += "• **参数类型错误**: 请检查参数类型，确保与Schema定义一致\n"
            instructions += "  - string类型: 使用双引号包围文本\n"
            instructions += "  - array类型: 使用方括号[]包围列表\n"
            instructions += "  - object类型: 使用花括号{}包围对象\n"
        
        if "pattern" in error_summary.lower():
            instructions += "• **格式不符合要求**: 请检查参数格式，确保符合正则表达式规则\n"
        
        if "minimum" in error_summary.lower() or "maximum" in error_summary.lower():
            instructions += "• **数值范围错误**: 请确保数值在允许的范围内\n"
        
        if "additional" in error_summary.lower():
            instructions += "• **包含未知参数**: 请移除Schema中未定义的参数\n"
        
        instructions += "\n💡 **提示**: 仔细阅读上述错误详情，逐项修正每个参数。"
        
        return instructions
    
    def _generate_repair_examples(self, validation_result: ValidationResult, 
                                repair_result: RepairResult) -> str:
        """生成具体的修复示例"""
        examples = ""
        
        # 如果有智能修复建议，使用它们生成示例
        if repair_result.suggestions:
            examples += "根据上述修复建议，这里是具体的修复示例:\n\n"
            
            for suggestion in repair_result.suggestions:
                examples += f"🔧 修复 `{suggestion.field_path}`:\n"
                examples += f"```json\n"
                examples += f'"{suggestion.field_path}": {json.dumps(suggestion.suggested_value, ensure_ascii=False, indent=2)}\n'
                examples += f"```\n\n"
        else:
            # 生成通用示例
            error_summary = validation_result.get_error_summary()
            
            if "input_ports" in error_summary or "output_ports" in error_summary:
                examples += "端口参数修复示例:\n"
                examples += "```json\n"
                examples += '"input_ports": [\n'
                examples += '  {"name": "clk", "width": 1, "description": "时钟信号"},\n'
                examples += '  {"name": "data_in", "width": 8, "description": "输入数据"}\n'
                examples += '],\n'
                examples += '"output_ports": [\n'
                examples += '  {"name": "data_out", "width": 8, "description": "输出数据"}\n'
                examples += ']\n'
                examples += "```\n\n"
            
            if "clock_domain" in error_summary:
                examples += "时钟域参数修复示例:\n"
                examples += "```json\n"
                examples += '"clock_domain": {\n'
                examples += '  "clock_name": "clk",\n'
                examples += '  "reset_name": "rst_n",\n'
                examples += '  "reset_active": "low"\n'
                examples += '}\n'
                examples += "```\n\n"
            
            if "requirements" in error_summary:
                examples += "需求描述修复示例:\n"
                examples += "```json\n"
                examples += '"requirements": "设计一个8位计数器，具有同步复位功能，在时钟上升沿时递增计数值"\n'
                examples += "```\n\n"
        
        if not examples:
            examples = "请参考工具的Schema定义，确保所有参数格式正确。"
        
        return examples
    
    def _build_error_feedback(self, tool_calls: List[ToolCall], 
                             tool_results: List[ToolResult]) -> str:
        """构建增强的错误反馈，包含教学信息"""
        feedback = "🔧 **工具调用结果分析**:\n\n"
        
        has_validation_errors = False
        successful_tools = []
        failed_tools = []
        
        for tool_call, result in zip(tool_calls, tool_results):
            if result.success:
                successful_tools.append(tool_call.tool_name)
                feedback += f"✅ **{tool_call.tool_name}**: 执行成功\n"
            else:
                failed_tools.append(tool_call.tool_name)
                if "参数验证失败" in result.error:
                    has_validation_errors = True
                    feedback += f"❌ **{tool_call.tool_name}**: 参数验证失败\n"
                    feedback += f"{result.error}\n\n"
                else:
                    feedback += f"❌ **{tool_call.tool_name}**: 执行失败\n"
                    feedback += f"   错误: {result.error}\n\n"
        
        # 添加总结和下一步指导
        if has_validation_errors:
            feedback += "\n" + "="*70 + "\n"
            feedback += "📋 **总结与建议**:\n\n"
            feedback += f"• 成功工具: {', '.join(successful_tools) if successful_tools else '无'}\n"
            feedback += f"• 失败工具: {', '.join(failed_tools)}\n\n"
            feedback += "💡 **下一步操作**:\n"
            feedback += "1. 仔细阅读上述每个失败工具的详细错误信息和修复示例\n"
            feedback += "2. 根据提供的修复指令修正参数格式\n"
            feedback += "3. 重新构造完整的JSON工具调用，包含所有成功和修复后的工具\n"
            feedback += "4. 确保所有参数都符合Schema要求\n\n"
            feedback += "⚠️ **重要提醒**: 请在下次调用中修正所有参数，系统将重新验证并执行。"
        
        return feedback
    
    def _build_enhanced_error_feedback(self, tool_calls: List[ToolCall], 
                                     tool_results: List[ToolResult],
                                     param_validation_failed_tools: set,
                                     permanently_failed_tools: set,
                                     iteration_count: int) -> str:
        """构建增强的错误反馈，支持智能重试指导"""
        feedback = f"🔧 **第{iteration_count}次迭代 - 工具调用结果分析**:\n\n"
        
        successful_tools = []
        param_failed_tools = []
        execution_failed_tools = []
        
        for tool_call, result in zip(tool_calls, tool_results):
            if result.success:
                successful_tools.append(tool_call.tool_name)
                feedback += f"✅ **{tool_call.tool_name}**: 执行成功\n"
            else:
                if "参数验证失败" in result.error:
                    param_failed_tools.append(tool_call.tool_name)
                    feedback += f"⚠️ **{tool_call.tool_name}**: 参数验证失败（可重试）\n"
                    feedback += f"{result.error}\n\n"
                else:
                    execution_failed_tools.append(tool_call.tool_name)
                    feedback += f"❌ **{tool_call.tool_name}**: 执行失败\n"
                    feedback += f"   错误: {result.error}\n\n"
        
        # 添加智能重试指导
        feedback += "\n" + "="*70 + "\n"
        feedback += "📊 **状态总结**:\n\n"
        feedback += f"• ✅ 成功工具: {', '.join(successful_tools) if successful_tools else '无'}\n"
        feedback += f"• ⚠️ 参数验证失败（可重试）: {', '.join(param_failed_tools) if param_failed_tools else '无'}\n"
        feedback += f"• ❌ 执行失败（永久失败）: {', '.join(execution_failed_tools) if execution_failed_tools else '无'}\n\n"
        
        if param_failed_tools:
            feedback += "🚀 **重试机会**:\n"
            feedback += f"系统检测到 {len(param_failed_tools)} 个工具的参数验证失败。这些工具在下次迭代中可以重试！\n\n"
            feedback += "💡 **下一步操作**:\n"
            feedback += "1. 仔细阅读上述每个失败工具的详细错误信息和修复示例\n"
            feedback += "2. 根据提供的修复指令修正参数格式\n"
            feedback += "3. 重新构造JSON工具调用，**包含所有工具**（成功的和修复后的）\n"
            feedback += "4. 系统将重新验证参数并允许重新执行\n\n"
            feedback += "⭐ **重要**: 请修正参数后重新调用，不要因为失败就放弃！\n"
        
        if execution_failed_tools:
            feedback += "\n⚠️ **永久失败的工具**: 以下工具遇到执行错误，将不会重试:\n"
            for tool in execution_failed_tools:
                feedback += f"• {tool}: 执行错误（非参数问题）\n"
        
        return feedback
    
    def _validate_tool_schema(self, schema: Dict[str, Any]):
        """验证工具Schema格式"""
        required_fields = ["type", "properties"]
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Schema缺少必需字段: {field}")
        
        if schema["type"] != "object":
            raise ValueError("工具Schema的根类型必须是object")
    
    def _convert_schema_to_legacy_format(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """将Schema转换为遗留格式（向后兼容）"""
        legacy_params = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for param_name, param_schema in properties.items():
            legacy_params[param_name] = {
                "type": param_schema.get("type", "string"),
                "description": param_schema.get("description", ""),
                "required": param_name in required
            }
        
        return legacy_params
    
    def _is_final_result(self, tool_results: List[ToolResult]) -> bool:
        """判断是否为最终结果"""
        # 检查是否有测试成功的结果
        for result in tool_results:
            if result.success and result.result:
                # 检查run_simulation工具是否成功
                if isinstance(result.result, dict):
                    # 检查仿真是否成功完成
                    if result.result.get('success', False):
                        # 检查是否有仿真输出，表明测试已完成
                        simulation_output = result.result.get('simulation_output', '')
                        if simulation_output:
                            # 检查多种可能的完成标志
                            completion_flags = [
                                'Simulation Finished',
                                'Testbench Finished', 
                                '$finish called',
                                '=== Testbench Finished ===',
                                '=== Simulation Finished ==='
                            ]
                            
                            for flag in completion_flags:
                                if flag in simulation_output:
                                    logger.info(f"🎯 检测到测试成功完成标志: {flag}")
                                    return True
                        
                        # 检查是否有成功的仿真结果
                        if result.result.get('return_code', 1) == 0:
                            logger.info("🎯 检测到仿真成功完成（返回码为0）")
                            return True
        
        # 简单的启发式规则：如果所有工具都成功执行，可能是最终结果
        return all(result.success for result in tool_results)
    
    def get_enhanced_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取增强工具信息"""
        if tool_name not in self.enhanced_tools:
            return None
        
        tool_def = self.enhanced_tools[tool_name]
        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "schema": tool_def.schema,
            "security_level": tool_def.security_level,
            "category": tool_def.category,
            "version": tool_def.version,
            "deprecated": tool_def.deprecated
        }
    
    def list_enhanced_tools(self, category: str = None, 
                           security_level: str = None) -> List[Dict[str, Any]]:
        """列出增强工具"""
        tools = []
        for tool_def in self.enhanced_tools.values():
            if category and tool_def.category != category:
                continue
            if security_level and tool_def.security_level != security_level:
                continue
            
            tools.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "category": tool_def.category,
                "security_level": tool_def.security_level,
                "version": tool_def.version
            })
        
        return tools
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        total_validations = len(self.validation_cache)
        successful_validations = sum(
            1 for result in self.validation_cache.values() if result.is_valid
        )
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "cache_size": len(self.validation_cache)
        }
    
    def _build_conversation_with_history(self, user_request: str, conversation_history: list) -> list:
        """构建包含历史的对话"""
        conversation = [{"role": "user", "content": user_request}]
        
        # 添加历史对话
        for entry in conversation_history:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            conversation.append({"role": role, "content": content})
        
        return conversation
    
    def _is_critical_tool(self, tool_name: str) -> bool:
        """判断是否为关键工具（失败后会影响后续工具执行）"""
        critical_tools = {
            "generate_verilog_code",      # 代码生成是核心，失败后分析和测试都无意义
            "write_file",                 # 文件写入失败会影响后续读取
            "read_file",                  # 文件读取失败会影响基于文件内容的操作
            "run_simulation",             # 仿真失败会影响结果分析
            "generate_build_script"       # 构建脚本生成失败会影响执行
        }
        return tool_name in critical_tools
    
    def _should_skip_tool_due_to_dependencies(self, tool_call: ToolCall, failed_critical_tools: set) -> bool:
        """检查工具是否应该因为依赖关系而跳过执行"""
        tool_name = tool_call.tool_name
        
        # 定义工具依赖关系
        dependencies = {
            "generate_testbench": {"generate_verilog_code"},      # 测试台生成依赖代码生成
            "run_simulation": {"generate_verilog_code", "generate_testbench", "write_file"},  # 仿真依赖代码和测试台
            "execute_build_script": {"generate_build_script"}     # 脚本执行依赖脚本生成
        }
        
        tool_deps = dependencies.get(tool_name, set())
        # 检查是否有依赖的关键工具已失败
        return bool(tool_deps.intersection(failed_critical_tools))

    def _extract_simulation_result(self, tool_results: List[ToolResult]) -> Optional[str]:
        """从工具结果中提取仿真结果，判断任务是否完成"""
        logger.info(f"🔍 开始提取仿真结果，工具结果数量: {len(tool_results)}")
        
        for i, result in enumerate(tool_results):
            logger.info(f"🔍 检查工具结果 {i+1}: success={result.success}")
            
            if result.success and result.result:
                if isinstance(result.result, dict):
                    logger.info(f"🔍 工具结果 {i+1} 是字典类型")
                    
                    # 检查仿真是否成功完成
                    if result.result.get('success', False):
                        logger.info(f"🔍 工具结果 {i+1} 仿真成功")
                        
                        # 检查是否有仿真输出，表明测试已完成
                        simulation_output = result.result.get('simulation_output', '')
                        if simulation_output:
                            logger.info(f"🔍 找到仿真输出，长度: {len(simulation_output)}")
                            logger.info(f"🔍 仿真输出前100字符: {simulation_output[:100]}")
                            
                            # 检查多种可能的完成标志
                            completion_flags = [
                                'Simulation Finished',
                                'Testbench Finished', 
                                '$finish called',
                                '=== Testbench Finished ===',
                                '=== Simulation Finished ==='
                            ]
                            
                            for flag in completion_flags:
                                if flag in simulation_output:
                                    logger.info(f"🎯 检测到测试成功完成标志: {flag}")
                                    return f"🎯 **仿真结果分析**:\n\n✅ 仿真成功完成！\n\n输出信息:\n{simulation_output}"
                            
                            logger.info("🔍 未检测到完成标志")
                        
                        # 检查是否有成功的仿真结果
                        if result.result.get('return_code', 1) == 0:
                            logger.info("🎯 检测到仿真成功完成（返回码为0）")
                            return f"🎯 **仿真结果分析**:\n\n✅ 仿真成功完成！\n\n返回码: {result.result.get('return_code', 1)}"
        
        logger.info("🔍 未找到仿真结果")
        return None

    def _extract_simulation_and_error_info(self, tool_results: List[ToolResult]) -> Optional[str]:
        """从工具结果中提取仿真结果和错误信息，包括成功和失败的情况"""
        logger.info(f"🔍 开始提取仿真结果和错误信息，工具结果数量: {len(tool_results)}")
        
        simulation_info = []
        
        for i, result in enumerate(tool_results):
            logger.info(f"🔍 检查工具结果 {i+1}: success={result.success}")
            
            # 检查是否是仿真相关的工具（通过错误信息或结果内容判断）
            is_simulation_tool = False
            if result.error and ('编译错误' in result.error or '仿真' in result.error or 'simulation' in result.error.lower()):
                is_simulation_tool = True
            elif result.result and isinstance(result.result, dict):
                if 'simulation_output' in result.result or 'compilation_output' in result.result:
                    is_simulation_tool = True
            
            if is_simulation_tool:
                if result.success and result.result:
                    if isinstance(result.result, dict):
                        # 仿真成功的情况
                        if result.result.get('success', False):
                            simulation_output = result.result.get('simulation_output', '')
                            if simulation_output:
                                completion_flags = [
                                    'Simulation Finished',
                                    'Testbench Finished', 
                                    '$finish called',
                                    '=== Testbench Finished ===',
                                    '=== Simulation Finished ==='
                                ]
                                
                                for flag in completion_flags:
                                    if flag in simulation_output:
                                        logger.info(f"🎯 检测到测试成功完成标志: {flag}")
                                        simulation_info.append(f"🎯 **仿真成功**:\n\n✅ 仿真成功完成！\n\n输出信息:\n{simulation_output}")
                                        break
                                else:
                                    # 没有检测到完成标志，但仍然有输出
                                    simulation_info.append(f"🎯 **仿真执行**:\n\n仿真已执行，输出信息:\n{simulation_output}")
                        
                        # 检查返回码
                        if result.result.get('return_code', 1) == 0:
                            simulation_info.append(f"🎯 **仿真成功**:\n\n返回码: {result.result.get('return_code', 1)}")
                
                elif not result.success:
                    # 仿真失败的情况
                    error_message = result.error or "未知错误"
                    logger.info(f"🔍 检测到仿真失败: {error_message}")
                    
                    # 提取详细的错误信息
                    detailed_errors = []
                    if result.result and isinstance(result.result, dict):
                        compilation_errors = result.result.get('compilation_errors', '')
                        simulation_errors = result.result.get('simulation_errors', '')
                        error_msg = result.result.get('error_message', '')
                        
                        if compilation_errors:
                            detailed_errors.append(f"编译错误:\n{compilation_errors}")
                        if simulation_errors:
                            detailed_errors.append(f"仿真错误:\n{simulation_errors}")
                        if error_msg:
                            detailed_errors.append(f"错误消息:\n{error_msg}")
                    
                    if detailed_errors:
                        error_summary = "\n\n".join(detailed_errors)
                        simulation_info.append(f"❌ **仿真失败**:\n\n{error_summary}")
                    else:
                        simulation_info.append(f"❌ **仿真失败**:\n\n{error_message}")
        
        if simulation_info:
            return "\n\n" + "\n\n".join(simulation_info)
        
        logger.info("🔍 未找到仿真相关信息")
        return None

    def _check_simulation_success(self, tool_results: List[ToolResult]) -> bool:
        """检查仿真是否成功完成"""
        logger.info(f"🔍 检查仿真成功状态，工具结果数量: {len(tool_results)}")
        
        for result in tool_results:
            # 检查是否是仿真相关的工具
            is_simulation_tool = False
            if result.error and ('编译错误' in result.error or '仿真' in result.error or 'simulation' in result.error.lower()):
                is_simulation_tool = True
            elif result.result and isinstance(result.result, dict):
                if 'simulation_output' in result.result or 'compilation_output' in result.result:
                    is_simulation_tool = True
            
            if is_simulation_tool and result.success and result.result:
                if isinstance(result.result, dict):
                    # 检查仿真是否成功完成
                    if result.result.get('success', False):
                        simulation_output = result.result.get('simulation_output', '')
                        if simulation_output:
                            # 检查多种可能的完成标志
                            completion_flags = [
                                'Simulation Finished',
                                'Testbench Finished', 
                                '$finish called',
                                '=== Testbench Finished ===',
                                '=== Simulation Finished ===',
                                'Testbench Simulation Completed',
                                'All test cases executed'
                            ]
                            
                            for flag in completion_flags:
                                if flag in simulation_output:
                                    logger.info(f"🎯 检测到仿真成功完成标志: {flag}")
                                    return True
                        
                        # 检查返回码
                        if result.result.get('return_code', 1) == 0:
                            logger.info("🎯 检测到仿真成功完成（返回码为0）")
                            return True
        
        logger.info("🔍 仿真未成功完成")
        return False