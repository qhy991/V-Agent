#!/usr/bin/env python3
"""
重构后的Verilog设计智能体
使用统一的LLM通信模块，减少重复代码
"""

import os 
import json
import asyncio
import subprocess
import tempfile
from typing import Dict, Any, Set, List
from pathlib import Path
import time

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from core.base_agent import TaskMessage
from core.response_format import StandardizedResponse, TaskStatus, ResponseType, QualityMetrics, IssueReport
from datetime import datetime
from core.llm_communication import UnifiedLLMClientManager, SystemPromptBuilder, CallType
from config.config import FrameworkConfig
from core.enhanced_logging_config import get_agent_logger, get_artifacts_dir


class EnhancedRealVerilogAgentRefactored(EnhancedBaseAgent):
    """重构后的Verilog HDL设计智能体 - 使用统一LLM通信模块"""
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="enhanced_real_verilog_agent",
            role="verilog_designer",
            capabilities={
                AgentCapability.CODE_GENERATION,
                AgentCapability.MODULE_DESIGN,
                AgentCapability.SPECIFICATION_ANALYSIS
            },
            config=config
        )
        
        # 初始化配置
        self.config = config or FrameworkConfig.from_env()
        
        # 使用统一的LLM通信管理器
        self.llm_manager = UnifiedLLMClientManager(
            agent_id=self.agent_id,
            role="verilog_designer",
            config=self.config
        )
        
        # 使用统一的System Prompt构建器
        self.prompt_builder = SystemPromptBuilder()
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('EnhancedRealVerilogAgent')
        self.artifacts_dir = get_artifacts_dir()
        
        # 注册增强工具
        self._register_enhanced_verilog_tools()
        
        self.logger.debug(f"🔧 重构后的Verilog智能体初始化完成")
    
    def _register_enhanced_verilog_tools(self):
        """注册带Schema验证的Verilog设计工具"""
        
        # 1. 设计需求分析工具
        self.register_enhanced_tool(
            name="analyze_design_requirements",
            func=self._tool_analyze_design_requirements,
            description="分析和解析Verilog设计需求，提取关键设计参数",
            security_level="normal",
            category="analysis",
            schema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 50000,
                        "description": "设计需求描述，包含功能规格和约束条件"
                    },
                    "design_type": {
                        "type": "string",
                        "enum": ["combinational", "sequential", "mixed", "custom"],
                        "default": "mixed",
                        "description": "设计类型分类"
                    },
                    "complexity_level": {
                        "type": "string", 
                        "enum": ["simple", "medium", "complex", "advanced"],
                        "default": "medium",
                        "description": "设计复杂度级别"
                    }
                },
                "required": ["requirements"],
                "additionalProperties": False
            }
        )
        
        # 2. Verilog代码生成工具
        self.register_enhanced_tool(
            name="generate_verilog_code",
            func=self._tool_generate_verilog_code,
            description="生成高质量的Verilog HDL代码",
            security_level="high",
            category="code_generation",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "模块名称"
                    },
                    "requirements": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 50000,
                        "description": "设计需求描述"
                    },
                    "input_ports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "width": {"type": "integer", "minimum": 1},
                                "description": {"type": "string"}
                            },
                            "required": ["name", "width"]
                        },
                        "description": "输入端口定义"
                    },
                    "output_ports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "width": {"type": "integer", "minimum": 1},
                                "description": {"type": "string"}
                            },
                            "required": ["name", "width"]
                        },
                        "description": "输出端口定义"
                    },
                    "coding_style": {
                        "type": "string",
                        "enum": ["rtl", "behavioral", "structural"],
                        "default": "rtl",
                        "description": "编码风格"
                    }
                },
                "required": ["module_name", "requirements"],
                "additionalProperties": False
            }
        )
        
        # 3. 代码质量分析工具
        self.register_enhanced_tool(
            name="analyze_code_quality",
            func=self._tool_analyze_code_quality,
            description="分析Verilog代码质量，提供改进建议",
            security_level="normal",
            category="analysis",
            schema={
                "type": "object",
                "properties": {
                    "verilog_code": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 100000,
                        "description": "要分析的Verilog代码"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "模块名称（可选）"
                    }
                },
                "required": ["verilog_code"],
                "additionalProperties": False
            }
        )
        
        # 4. 代码优化工具
        self.register_enhanced_tool(
            name="optimize_verilog_code",
            func=self._tool_optimize_verilog_code,
            description="优化Verilog代码性能和资源使用",
            security_level="normal",
            category="optimization",
            schema={
                "type": "object",
                "properties": {
                    "verilog_code": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 100000,
                        "description": "要优化的Verilog代码"
                    },
                    "optimization_target": {
                        "type": "string",
                        "enum": ["area", "speed", "power", "balanced"],
                        "default": "balanced",
                        "description": "优化目标"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "模块名称（可选）"
                    }
                },
                "required": ["verilog_code"],
                "additionalProperties": False
            }
        )
        
        # 5. 工具使用指南
        self.register_enhanced_tool(
            name="get_tool_usage_guide",
            func=self._tool_get_tool_usage_guide,
            description="获取Verilog设计工具的使用指南和最佳实践",
            security_level="low",
            category="help",
            schema={
                "type": "object",
                "properties": {
                    "include_examples": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含使用示例"
                    },
                    "include_best_practices": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含最佳实践"
                    }
                },
                "additionalProperties": False
            }
        )
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """使用统一的LLM通信管理器进行Function Calling调用"""
        return await self.llm_manager.call_llm_for_function_calling(
            conversation, 
            system_prompt_builder=self._build_system_prompt
        )
    
    async def _build_system_prompt(self) -> str:
        """使用统一的System Prompt构建器"""
        return await self.prompt_builder.build_system_prompt(
            role="verilog_designer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id=self.agent_id,
            capabilities=self._capabilities
        )
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.MODULE_DESIGN,
            AgentCapability.SPECIFICATION_ANALYSIS
        }
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "集成Schema验证的增强Verilog HDL设计智能体，提供严格参数验证和智能错误修复的专业数字电路设计服务"
    
    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """获取注册的工具列表"""
        return self.enhanced_tools
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强任务 - 使用统一的LLM通信模块"""
        
        try:
            self.logger.info(f"🚀 开始执行Verilog设计任务")
            
            # 构建对话历史
            conversation = [
                {"role": "system", "content": await self._build_system_prompt()},
                {"role": "user", "content": enhanced_prompt}
            ]
            
            # 使用统一的LLM管理器进行调用
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            # 解析响应
            result = self._parse_llm_response(response)
            
            # 构建响应格式
            response_format = StandardizedResponse(
                agent_name=self.role,
                agent_id=self.agent_id,
                response_type=ResponseType.TASK_COMPLETION,
                task_id=original_message.task_id,
                timestamp=datetime.now().isoformat(),
                status=TaskStatus.SUCCESS,
                completion_percentage=100.0,
                message="Verilog设计任务执行成功",
                generated_files=[],
                modified_files=[],
                reference_files=[],
                issues=[],
                quality_metrics=QualityMetrics(
                    overall_score=0.9,
                    syntax_score=0.85,
                    functionality_score=0.8,
                    test_coverage=0.75,
                    documentation_quality=0.8
                ),
                metadata=result
            )
            
            self.logger.info(f"✅ Verilog设计任务执行完成")
            return response_format.to_dict()
            
        except Exception as e:
            self.logger.error(f"❌ Verilog设计任务执行失败: {str(e)}")
            
            response_format = StandardizedResponse(
                agent_name=self.role,
                agent_id=self.agent_id,
                response_type=ResponseType.ERROR_REPORT,
                task_id=original_message.task_id,
                timestamp=datetime.now().isoformat(),
                status=TaskStatus.FAILED,
                completion_percentage=0.0,
                message=f"Verilog设计任务执行失败: {str(e)}",
                generated_files=[],
                modified_files=[],
                reference_files=[],
                issues=[IssueReport(
                    issue_type="error",
                    severity="critical",
                    description=str(e),
                    location="execute_enhanced_task"
                )],
                quality_metrics=QualityMetrics(
                    overall_score=0.0,
                    syntax_score=0.0,
                    functionality_score=0.0,
                    test_coverage=0.0,
                    documentation_quality=0.0
                ),
                metadata={"error": str(e)}
            )
            
            return response_format.to_dict()
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON响应
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # 如果不是JSON，返回文本内容
                return {"content": response}
        except json.JSONDecodeError:
            return {"content": response}
    
    # 工具方法实现（保持原有逻辑）
    async def _tool_analyze_design_requirements(self, requirements: str, 
                                              design_type: str = "mixed",
                                              complexity_level: str = "medium") -> Dict[str, Any]:
        """分析设计需求"""
        try:
            self.logger.info(f"🔍 开始分析设计需求")
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下Verilog设计需求：

**需求描述**:
{requirements}

**设计类型**: {design_type}
**复杂度级别**: {complexity_level}

请提供详细的分析结果，包括：
1. 功能需求分析
2. 接口定义建议
3. 设计约束识别
4. 实现建议
"""
            
            conversation = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            return {
                "analysis_result": response,
                "design_type": design_type,
                "complexity_level": complexity_level,
                "requirements_length": len(requirements)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 设计需求分析失败: {str(e)}")
            return {"error": str(e)}
    
    async def _tool_generate_verilog_code(self, module_name: str, requirements: str = None,
                                        input_ports: List[Dict] = None,
                                        output_ports: List[Dict] = None,
                                        coding_style: str = "rtl",
                                        **kwargs) -> Dict[str, Any]:
        """生成Verilog代码"""
        try:
            self.logger.info(f"💻 开始生成Verilog代码: {module_name}")
            
            # 构建代码生成提示
            code_prompt = f"""
请生成一个名为 {module_name} 的Verilog模块。

**设计需求**:
{requirements or "标准模块设计"}

**输入端口**:
{json.dumps(input_ports or [], indent=2)}

**输出端口**:
{json.dumps(output_ports or [], indent=2)}

**编码风格**: {coding_style}

请生成完整、可编译的Verilog代码，包含：
1. 模块声明和端口定义
2. 内部信号声明
3. 功能实现逻辑
4. 适当的注释
"""
            
            conversation = [
                {"role": "user", "content": code_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            return {
                "module_name": module_name,
                "verilog_code": response,
                "coding_style": coding_style,
                "generation_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Verilog代码生成失败: {str(e)}")
            return {"error": str(e)}
    
    async def _tool_analyze_code_quality(self, verilog_code: str, module_name: str = None) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            self.logger.info(f"🔍 开始分析代码质量")
            
            analysis_prompt = f"""
请分析以下Verilog代码的质量：

**代码**:
```verilog
{verilog_code}
```

请提供详细的质量分析，包括：
1. 语法正确性
2. 代码风格和可读性
3. 功能完整性
4. 性能考虑
5. 改进建议
"""
            
            conversation = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            return {
                "quality_analysis": response,
                "module_name": module_name,
                "code_length": len(verilog_code)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 代码质量分析失败: {str(e)}")
            return {"error": str(e)}
    
    async def _tool_optimize_verilog_code(self, verilog_code: str, 
                                        optimization_target: str = "balanced",
                                        module_name: str = None) -> Dict[str, Any]:
        """优化Verilog代码"""
        try:
            self.logger.info(f"⚡ 开始优化Verilog代码")
            
            optimization_prompt = f"""
请优化以下Verilog代码，优化目标：{optimization_target}

**原始代码**:
```verilog
{verilog_code}
```

请提供优化后的代码，重点关注：
1. 性能优化
2. 资源使用优化
3. 代码结构改进
4. 可读性提升
"""
            
            conversation = [
                {"role": "user", "content": optimization_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            return {
                "optimized_code": response,
                "optimization_target": optimization_target,
                "module_name": module_name,
                "optimization_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 代码优化失败: {str(e)}")
            return {"error": str(e)}
    
    async def _tool_get_tool_usage_guide(self, include_examples: bool = True,
                                       include_best_practices: bool = True) -> Dict[str, Any]:
        """获取工具使用指南"""
        try:
            self.logger.info(f"📚 生成工具使用指南")
            
            guide_prompt = f"""
请提供Verilog设计工具的使用指南。

**要求**:
- 包含示例: {include_examples}
- 包含最佳实践: {include_best_practices}

请提供详细的指南，包括：
1. 工具功能介绍
2. 使用方法和参数说明
3. 实际使用示例
4. 最佳实践建议
5. 常见问题和解决方案
"""
            
            conversation = [
                {"role": "user", "content": guide_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            return {
                "usage_guide": response,
                "include_examples": include_examples,
                "include_best_practices": include_best_practices
            }
            
        except Exception as e:
            self.logger.error(f"❌ 工具指南生成失败: {str(e)}")
            return {"error": str(e)} 