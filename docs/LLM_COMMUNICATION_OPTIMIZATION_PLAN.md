# 🚀 LLM通信抽象层优化完整方案

## 🎯 核心问题分析

### ⚠️ 当前关键问题

1. **LLM调用重复严重** - 三个智能体每个都重复实现~400行LLM调用逻辑
2. **System Prompt构建重复** - 每个智能体~800行重复的Prompt构建方法
3. **缺少统一错误处理** - 错误处理、重试机制分散在各个智能体中
4. **性能监控缺失** - 无法统计调用性能、Token使用、缓存效果

### 💡 优化目标

- **减少重复代码**: 消除1200+行LLM相关重复代码
- **提升性能**: 通过缓存、优化降低30%以上的LLM调用成本
- **增强稳定性**: 统一错误处理和重试机制，提高系统可靠性
- **改善监控**: 完整的性能监控和调用统计分析

## 🏗️ LLM通信抽象层完整设计

### 📋 架构概览

```
core/llm_communication/
├── __init__.py                    # 模块导入和初始化
├── managers/
│   ├── __init__.py
│   ├── client_manager.py          # LLM客户端管理器
│   ├── conversation_optimizer.py  # 对话优化器
│   └── performance_monitor.py     # 性能监控器
├── templates/
│   ├── __init__.py
│   ├── prompt_template_engine.py  # Prompt模板引擎
│   ├── role_templates/            # 角色特定模板
│   │   ├── verilog_designer.py
│   │   ├── code_reviewer.py
│   │   └── coordinator.py
│   └── dynamic_prompt_builder.py  # 动态Prompt构建器
├── error_handling/
│   ├── __init__.py
│   ├── retry_strategy.py          # 重试策略
│   ├── error_classifier.py       # 错误分类器
│   └── fallback_handler.py       # 回退处理器
├── caching/
│   ├── __init__.py
│   ├── prompt_cache.py            # Prompt缓存
│   ├── response_cache.py          # 响应缓存
│   └── context_cache.py           # 上下文缓存
└── utils/
    ├── __init__.py
    ├── token_counter.py           # Token计算器
    ├── content_optimizer.py       # 内容优化器
    └── metrics_collector.py       # 指标收集器
```

## 💻 核心组件实现

### 1. 统一LLM客户端管理器

```python
# /core/llm_communication/managers/client_manager.py
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from ..templates.prompt_template_engine import PromptTemplateEngine
from ..error_handling.retry_strategy import RetryStrategy
from ..caching.context_cache import ContextCache
from ..utils.metrics_collector import MetricsCollector
from ...unified_logging_system import get_global_logging_system


class CallType(Enum):
    """LLM调用类型"""
    FUNCTION_CALLING = "function_calling"
    SYSTEM_PROMPT = "system_prompt"
    CONVERSATION = "conversation"
    ANALYSIS = "analysis"


@dataclass
class LLMCallContext:
    """LLM调用上下文"""
    agent_id: str
    role: str
    call_type: CallType
    conversation_id: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.3
    enable_cache: bool = True
    priority: str = "normal"  # low, normal, high, critical
    metadata: Dict[str, Any] = None


class UnifiedLLMClientManager:
    """统一的LLM客户端管理器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.template_engine = PromptTemplateEngine()
        self.retry_strategy = RetryStrategy(config)
        self.context_cache = ContextCache(config)
        self.metrics_collector = MetricsCollector()
        
        # 性能统计
        self.call_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens': 0,
            'average_response_time': 0.0
        }
        
        # 活跃会话管理
        self.active_sessions: Dict[str, Dict] = {}
        
        # 集成增强日志系统
        self.logging_system = get_global_logging_system()
    
    async def call_llm_for_function_calling(self, 
                                          context: LLMCallContext,
                                          conversation: List[Dict[str, str]],
                                          system_prompt: Optional[str] = None) -> str:
        """统一的Function Calling LLM调用"""
        call_start_time = time.time()
        
        try:
            # 1. 准备调用上下文
            session_key = f"{context.agent_id}_{context.conversation_id or 'default'}"
            
            # 2. 构建或获取System Prompt
            if not system_prompt:
                system_prompt = await self.template_engine.build_system_prompt(
                    role=context.role,
                    call_type=context.call_type,
                    agent_id=context.agent_id,
                    metadata=context.metadata
                )
            
            # 3. 检查缓存
            if context.enable_cache:
                cached_response = await self.context_cache.get_cached_response(
                    system_prompt, conversation, context
                )
                if cached_response:
                    self.call_stats['cache_hits'] += 1
                    self._log_llm_call(context, call_start_time, True, cached=True)
                    return cached_response
            
            self.call_stats['cache_misses'] += 1
            
            # 4. 执行LLM调用（带重试机制）
            response = await self.retry_strategy.execute_with_retry(
                self._execute_llm_call,
                context=context,
                system_prompt=system_prompt,
                conversation=conversation
            )
            
            # 5. 缓存响应
            if context.enable_cache and response:
                await self.context_cache.cache_response(
                    system_prompt, conversation, response, context
                )
            
            # 6. 记录成功调用
            self.call_stats['successful_calls'] += 1
            self.call_stats['total_calls'] += 1
            self._log_llm_call(context, call_start_time, True)
            
            return response
            
        except Exception as e:
            # 记录失败调用
            self.call_stats['failed_calls'] += 1
            self.call_stats['total_calls'] += 1
            self._log_llm_call(context, call_start_time, False, error=str(e))
            
            # 使用回退处理器
            return await self._handle_llm_failure(context, conversation, e)
    
    async def _execute_llm_call(self, context: LLMCallContext, 
                               system_prompt: str, 
                               conversation: List[Dict[str, str]]) -> str:
        """执行实际的LLM调用"""
        from llm_integration.enhanced_llm_client import EnhancedLLMClient
        
        # 创建或获取LLM客户端
        client = EnhancedLLMClient(self.config.llm)
        
        # 构建完整的对话内容
        full_prompt = self._build_conversation_prompt(conversation)
        
        # 根据调用类型选择合适的调用方法
        if context.call_type == CallType.FUNCTION_CALLING:
            # 对于Function Calling，使用优化的方法
            if hasattr(client, 'send_prompt_optimized'):
                response = await client.send_prompt_optimized(
                    conversation_id=context.conversation_id,
                    user_message=full_prompt,
                    system_prompt=system_prompt,
                    temperature=context.temperature,
                    max_tokens=context.max_tokens,
                    force_refresh_system=False
                )
            else:
                response = await client.send_prompt(
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    temperature=context.temperature,
                    max_tokens=context.max_tokens
                )
        else:
            # 标准调用
            response = await client.send_prompt(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=context.temperature,
                max_tokens=context.max_tokens
            )
        
        return response
    
    def _build_conversation_prompt(self, conversation: List[Dict[str, str]]) -> str:
        """构建对话Prompt"""
        prompt_parts = []
        for msg in conversation:
            if msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Assistant: {msg['content']}")
        
        return "\n\n".join(prompt_parts)
    
    async def _handle_llm_failure(self, context: LLMCallContext, 
                                 conversation: List[Dict[str, str]], 
                                 error: Exception) -> str:
        """处理LLM调用失败"""
        from .fallback_handler import FallbackHandler
        
        fallback_handler = FallbackHandler(self.config)
        return await fallback_handler.handle_failure(context, conversation, error)
    
    def _log_llm_call(self, context: LLMCallContext, start_time: float, 
                     success: bool, cached: bool = False, error: str = None):
        """记录LLM调用信息"""
        duration = time.time() - start_time
        
        # 更新性能统计
        self.call_stats['average_response_time'] = (
            (self.call_stats['average_response_time'] * (self.call_stats['total_calls'] - 1) + duration) 
            / max(self.call_stats['total_calls'], 1)
        )
        
        # 记录到增强日志系统
        if self.logging_system:
            try:
                self.logging_system.log_llm_call(
                    agent_id=context.agent_id,
                    model_name="claude-3.5-sonnet",
                    conversation_id=context.conversation_id,
                    call_type=context.call_type.value,
                    duration=duration,
                    success=success,
                    cached=cached,
                    error_info={"error": error} if error else None,
                    metadata={
                        "temperature": context.temperature,
                        "max_tokens": context.max_tokens,
                        "priority": context.priority
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log LLM call: {e}")
        
        # 本地日志
        status = "SUCCESS" if success else "FAILED"
        cache_status = "(CACHED)" if cached else ""
        self.logger.info(
            f"🤖 LLM Call {status} {cache_status} - "
            f"Agent: {context.agent_id}, "
            f"Type: {context.call_type.value}, "
            f"Duration: {duration:.3f}s"
        )
        
        if error:
            self.logger.error(f"❌ LLM Call Error: {error}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.call_stats,
            'cache_hit_rate': (
                self.call_stats['cache_hits'] / 
                max(self.call_stats['cache_hits'] + self.call_stats['cache_misses'], 1)
            ),
            'success_rate': (
                self.call_stats['successful_calls'] / 
                max(self.call_stats['total_calls'], 1)
            ),
            'active_sessions': len(self.active_sessions)
        }
    
    def reset_metrics(self):
        """重置性能指标"""
        self.call_stats = {key: 0 if isinstance(value, (int, float)) else value 
                          for key, value in self.call_stats.items()}
```

### 2. System Prompt模板引擎

```python
# /core/llm_communication/templates/prompt_template_engine.py
import json
import os
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from ..managers.client_manager import CallType
from ...enums import AgentCapability


@dataclass
class PromptTemplate:
    """Prompt模板定义"""
    name: str
    role: str
    base_template: str
    capability_sections: Dict[str, str]
    tool_sections: Dict[str, str]
    dynamic_sections: Dict[str, str]
    metadata: Dict[str, Any] = None


class PromptTemplateEngine:
    """Prompt模板引擎"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_cache: Dict[str, str] = {}
        self.load_templates()
    
    def load_templates(self):
        """加载所有模板"""
        # 加载角色特定模板
        self._load_role_templates()
        
        # 加载通用模板组件
        self._load_common_components()
    
    def _load_role_templates(self):
        """加载角色特定模板"""
        
        # Verilog设计师模板
        self.templates['verilog_designer'] = PromptTemplate(
            name="verilog_designer",
            role="verilog_designer", 
            base_template=self._get_verilog_base_template(),
            capability_sections={
                "code_generation": self._get_verilog_code_generation_section(),
                "module_design": self._get_verilog_module_design_section(),
                "specification_analysis": self._get_verilog_analysis_section()
            },
            tool_sections={
                "analyze_design_requirements": self._get_tool_section("analyze_design_requirements"),
                "generate_verilog_code": self._get_tool_section("generate_verilog_code"),
                "analyze_code_quality": self._get_tool_section("analyze_code_quality"),
                "optimize_verilog_code": self._get_tool_section("optimize_verilog_code"),
                "write_file": self._get_tool_section("write_file"),
                "read_file": self._get_tool_section("read_file")
            },
            dynamic_sections={
                "error_guidance": "根据历史错误提供针对性指导",
                "success_patterns": "基于成功案例的最佳实践",
                "context_awareness": "任务特定的上下文信息"
            }
        )
        
        # 代码审查师模板
        self.templates['code_reviewer'] = PromptTemplate(
            name="code_reviewer",
            role="code_reviewer",
            base_template=self._get_reviewer_base_template(),
            capability_sections={
                "code_review": self._get_reviewer_code_review_section(),
                "test_generation": self._get_reviewer_test_generation_section(),
                "verification": self._get_reviewer_verification_section()
            },
            tool_sections={
                "generate_testbench": self._get_tool_section("generate_testbench"),
                "run_simulation": self._get_tool_section("run_simulation"),
                "analyze_test_failures": self._get_tool_section("analyze_test_failures"),
                "write_file": self._get_tool_section("write_file"),
                "read_file": self._get_tool_section("read_file")
            },
            dynamic_sections={
                "error_recovery": "仿真错误诊断和恢复策略",
                "test_optimization": "测试覆盖率和优化建议",
                "quality_metrics": "代码质量评估标准"
            }
        )
        
        # 协调器模板
        self.templates['coordinator'] = PromptTemplate(
            name="coordinator",
            role="coordinator",
            base_template=self._get_coordinator_base_template(),
            capability_sections={
                "task_coordination": self._get_coordinator_task_section(),
                "workflow_management": self._get_coordinator_workflow_section(),
                "agent_selection": self._get_coordinator_selection_section()
            },
            tool_sections={
                "assign_task_to_agent": self._get_tool_section("assign_task_to_agent"),
                "analyze_agent_result": self._get_tool_section("analyze_agent_result")
            },
            dynamic_sections={
                "agent_performance": "基于历史表现的智能体选择",
                "task_optimization": "任务分解和执行优化",
                "quality_control": "结果质量控制和验证"
            }
        )
    
    async def build_system_prompt(self, role: str, call_type: CallType,
                                agent_id: str, capabilities: Set[AgentCapability] = None,
                                metadata: Dict[str, Any] = None) -> str:
        """构建System Prompt"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(role, call_type, agent_id, capabilities, metadata)
        
        # 检查缓存
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        # 获取模板
        template = self.templates.get(role)
        if not template:
            raise ValueError(f"No template found for role: {role}")
        
        # 构建Prompt
        prompt_parts = []
        
        # 1. 基础模板
        prompt_parts.append(template.base_template)
        
        # 2. 能力相关部分
        if capabilities:
            for capability in capabilities:
                capability_name = capability.value
                if capability_name in template.capability_sections:
                    prompt_parts.append(template.capability_sections[capability_name])
        
        # 3. 工具相关部分
        prompt_parts.append(self._build_tools_section(template))
        
        # 4. 动态部分
        if metadata:
            dynamic_content = self._build_dynamic_content(template, metadata)
            if dynamic_content:
                prompt_parts.append(dynamic_content)
        
        # 5. 调用类型特定部分
        if call_type == CallType.FUNCTION_CALLING:
            prompt_parts.append(self._get_function_calling_section())
        
        # 组合所有部分
        full_prompt = "\n\n".join(filter(None, prompt_parts))
        
        # 缓存结果
        self.template_cache[cache_key] = full_prompt
        
        return full_prompt
    
    def _generate_cache_key(self, role: str, call_type: CallType, agent_id: str,
                          capabilities: Set[AgentCapability] = None,
                          metadata: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        import hashlib
        
        key_components = [
            role,
            call_type.value,
            agent_id
        ]
        
        if capabilities:
            key_components.append(",".join(sorted(cap.value for cap in capabilities)))
        
        if metadata:
            # 只包含稳定的metadata部分，排除动态内容
            stable_metadata = {k: v for k, v in metadata.items() 
                             if k in ['task_type', 'complexity_level', 'priority']}
            if stable_metadata:
                key_components.append(json.dumps(stable_metadata, sort_keys=True))
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _get_verilog_base_template(self) -> str:
        """获取Verilog设计师基础模板"""
        return """你是一位资深的Verilog硬件设计专家，具备以下专业能力：

🔍 **核心专长**:
- Verilog/SystemVerilog模块设计和代码生成
- 组合逻辑和时序逻辑设计
- 参数化设计和可重用模块开发
- 代码质量分析和最佳实践应用
- 可综合性和时序收敛设计
- 设计验证和测试策略

📋 **设计标准**:
1. IEEE 1800标准合规性
2. 代码可读性和维护性
3. 综合性和时序收敛
4. 参数化和可重用性
5. 最佳实践和设计模式
6. 安全性和可靠性

🎯 **任务执行原则**:
- 根据需求智能判断设计类型（组合/时序/混合）
- 自动检测和适配参数化位宽需求
- 生成高质量、可综合的Verilog代码
- 提供详细的代码注释和文档
- 支持多种编码风格和设计模式
- 确保代码符合行业标准"""
    
    def _get_reviewer_base_template(self) -> str:
        """获取代码审查师基础模板"""
        return """你是一位专业的Verilog代码审查和验证专家，具备以下核心能力：

🔍 **审查专长**:
- Verilog代码质量分析和评估
- 测试台(testbench)生成和优化
- 仿真验证和调试
- 错误诊断和修复建议
- 覆盖率分析和测试优化
- 代码规范和最佳实践检查

🧪 **验证能力**:
- 功能验证和时序分析
- 边界条件和异常情况测试
- 仿真环境搭建和优化
- 自动化测试流程设计
- 调试工具和方法应用
- 验证报告生成和分析

⚡ **专业工具**:
- iverilog编译和仿真
- 测试向量生成和分析
- 波形分析和调试
- 覆盖率统计和报告
- 性能基准测试
- 错误分类和修复策略"""
    
    def _get_coordinator_base_template(self) -> str:
        """获取协调器基础模板"""
        return """你是一位智能的多智能体协调专家，负责任务分配、工作流管理和质量控制：

🧠 **协调能力**:
- 智能任务分析和分解
- 基于能力的智能体选择
- 工作流优化和管理
- 质量控制和结果验证
- 错误恢复和重试策略
- 性能监控和优化

📊 **决策原则**:
- 基于任务类型选择最适合的智能体
- 考虑历史表现和当前负载
- 确保任务执行的高质量完成
- 提供详细的执行分析和建议
- 支持并行处理和依赖管理
- 实现智能错误恢复和重试"""
    
    def _build_tools_section(self, template: PromptTemplate) -> str:
        """构建工具部分"""
        tools_section = "\n🛠️ **可用工具**:\n"
        tools_section += "你必须使用JSON格式调用工具，格式如下：\n"
        tools_section += """```json
{
    "tool_calls": [
        {
            "tool_name": "工具名称",
            "parameters": {
                "参数名": "参数值"
            }
        }
    ]
}
```\n"""
        
        tools_section += "### 可用工具列表:\n"
        for tool_name, tool_desc in template.tool_sections.items():
            tools_section += f"- **{tool_name}**: {tool_desc}\n"
        
        return tools_section
    
    def _get_function_calling_section(self) -> str:
        """获取Function Calling特定部分"""
        return """
🚨 **强制规则 - 必须使用工具调用**:
1. **禁止直接生成代码**: 绝对禁止在回复中直接生成Verilog代码
2. **必须调用工具**: 所有设计任务都必须通过工具调用完成
3. **必须写入文件**: 生成的代码必须使用 `write_file` 工具保存到文件
4. **JSON格式输出**: 当需要调用工具时回复必须是JSON格式的工具调用

**正确的工作流程**:
1. 分析需求 → 调用相应的分析工具
2. 生成/审查代码 → 调用生成/审查工具
3. **保存文件** → 调用 `write_file` 保存结果到指定目录
4. 质量检查 → 调用质量分析工具 (可选)
5. **路径回传** → 在任务总结中列出所有生成文件的完整路径

立即开始工具调用，严格按照工具列表执行，不要直接生成任何代码！"""
    
    # ... 其他辅助方法实现 ...
    
    def clear_cache(self):
        """清除模板缓存"""
        self.template_cache.clear()
    
    def get_template_stats(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        return {
            'total_templates': len(self.templates),
            'cached_prompts': len(self.template_cache),
            'template_roles': list(self.templates.keys())
        }
```

### 3. 统一错误处理和重试机制

```python
# /core/llm_communication/error_handling/retry_strategy.py
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from .error_classifier import ErrorType, ErrorClassifier
from .fallback_handler import FallbackHandler


class RetryType(Enum):
    """重试类型"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    retry_type: RetryType = RetryType.EXPONENTIAL_BACKOFF
    retryable_errors: List[ErrorType] = None
    timeout: float = 300.0  # 5分钟总超时


class RetryStrategy:
    """重试策略管理器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.error_classifier = ErrorClassifier()
        self.fallback_handler = FallbackHandler(config)
        
        # 默认重试配置
        self.default_retry_config = RetryConfig()
        
        # 按错误类型的特定重试配置
        self.error_specific_configs = {
            ErrorType.RATE_LIMIT: RetryConfig(
                max_attempts=5,
                base_delay=2.0,
                max_delay=120.0,
                backoff_multiplier=2.5
            ),
            ErrorType.NETWORK_TIMEOUT: RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0,
                backoff_multiplier=2.0
            ),
            ErrorType.SERVER_ERROR: RetryConfig(
                max_attempts=4,
                base_delay=5.0,
                max_delay=60.0,
                backoff_multiplier=1.5
            ),
            ErrorType.AUTHENTICATION_ERROR: RetryConfig(
                max_attempts=1  # 不重试认证错误
            )
        }
        
        # 重试统计
        self.retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'retry_by_error_type': {}
        }
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数并支持重试"""
        start_time = time.time()
        last_exception = None
        
        # 确定重试配置
        retry_config = kwargs.pop('retry_config', self.default_retry_config)
        
        for attempt in range(retry_config.max_attempts):
            try:
                # 检查总超时
                if time.time() - start_time > retry_config.timeout:
                    raise TimeoutError(f"Total execution timeout after {retry_config.timeout}s")
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 成功执行
                if attempt > 0:
                    self.retry_stats['successful_retries'] += 1
                    self.logger.info(
                        f"✅ Retry successful after {attempt} attempts - "
                        f"Function: {func.__name__}"
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 分类错误
                error_type = self.error_classifier.classify_error(e)
                
                # 记录重试统计
                self.retry_stats['total_retries'] += 1
                error_type_name = error_type.value
                self.retry_stats['retry_by_error_type'][error_type_name] = (
                    self.retry_stats['retry_by_error_type'].get(error_type_name, 0) + 1
                )
                
                # 检查是否应该重试
                if not self._should_retry(error_type, attempt, retry_config):
                    self.logger.error(
                        f"❌ Max retries exceeded or non-retryable error - "
                        f"Function: {func.__name__}, "
                        f"Error: {error_type_name}, "
                        f"Attempts: {attempt + 1}"
                    )
                    self.retry_stats['failed_retries'] += 1
                    break
                
                # 计算延迟时间
                delay = self._calculate_delay(attempt, retry_config, error_type)
                
                self.logger.warning(
                    f"⚠️ Retry attempt {attempt + 1}/{retry_config.max_attempts} - "
                    f"Function: {func.__name__}, "
                    f"Error: {error_type_name}, "
                    f"Delay: {delay:.1f}s"
                )
                
                # 等待重试
                if delay > 0:
                    await asyncio.sleep(delay)
        
        # 所有重试都失败了，使用回退处理
        self.logger.error(f"🚨 All retry attempts failed for {func.__name__}")
        return await self.fallback_handler.handle_retry_failure(
            func, last_exception, *args, **kwargs
        )
    
    def _should_retry(self, error_type: ErrorType, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        # 检查是否超过最大重试次数
        if attempt + 1 >= config.max_attempts:
            return False
        
        # 检查错误类型是否可重试
        if config.retryable_errors is not None:
            return error_type in config.retryable_errors
        
        # 默认不重试的错误类型
        non_retryable_errors = {
            ErrorType.AUTHENTICATION_ERROR,
            ErrorType.PERMISSION_ERROR,
            ErrorType.INVALID_REQUEST,
            ErrorType.CONFIGURATION_ERROR
        }
        
        return error_type not in non_retryable_errors
    
    def _calculate_delay(self, attempt: int, config: RetryConfig, error_type: ErrorType) -> float:
        """计算重试延迟时间"""
        # 获取特定错误类型的配置
        specific_config = self.error_specific_configs.get(error_type, config)
        
        if specific_config.retry_type == RetryType.IMMEDIATE:
            return 0
        
        elif specific_config.retry_type == RetryType.LINEAR_BACKOFF:
            delay = specific_config.base_delay * (attempt + 1)
        
        elif specific_config.retry_type == RetryType.EXPONENTIAL_BACKOFF:
            delay = specific_config.base_delay * (specific_config.backoff_multiplier ** attempt)
        
        else:  # CUSTOM或其他
            delay = specific_config.base_delay
        
        # 应用最大延迟限制
        delay = min(delay, specific_config.max_delay)
        
        # 添加随机抖动（避免雷群效应）
        import random
        jitter = delay * 0.1 * random.random()
        
        return delay + jitter
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        total_attempts = self.retry_stats['total_retries']
        if total_attempts > 0:
            success_rate = self.retry_stats['successful_retries'] / total_attempts
        else:
            success_rate = 0.0
        
        return {
            **self.retry_stats,
            'retry_success_rate': success_rate,
            'most_common_retry_errors': sorted(
                self.retry_stats['retry_by_error_type'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def reset_stats(self):
        """重置重试统计"""
        self.retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'retry_by_error_type': {}
        }
```

### 4. 性能监控和缓存优化

```python
# /core/llm_communication/utils/metrics_collector.py
import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    timestamp: float
    agent_id: str
    call_type: str
    duration: float
    success: bool
    cached: bool = False
    tokens: int = 0
    error_type: Optional[str] = None


@dataclass
class AggregatedMetrics:
    """聚合性能指标"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_duration: float = 0.0
    total_tokens: int = 0
    average_duration: float = 0.0
    success_rate: float = 0.0
    cache_hit_rate: float = 0.0
    error_distribution: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.metrics_history: deque = deque()
        self.real_time_metrics: Dict[str, Any] = defaultdict(int)
        self._lock = threading.Lock()
        
        # 按时间窗口聚合的指标
        self.hourly_metrics: Dict[str, AggregatedMetrics] = {}
        self.daily_metrics: AggregatedMetrics = AggregatedMetrics()
        
        # 启动后台清理任务
        self._start_cleanup_task()
    
    def record_llm_call(self, agent_id: str, call_type: str, duration: float,
                       success: bool, cached: bool = False, tokens: int = 0,
                       error_type: Optional[str] = None):
        """记录LLM调用指标"""
        with self._lock:
            metric = PerformanceMetric(
                timestamp=time.time(),
                agent_id=agent_id,
                call_type=call_type,
                duration=duration,
                success=success,
                cached=cached,
                tokens=tokens,
                error_type=error_type
            )
            
            # 添加到历史记录
            self.metrics_history.append(metric)
            
            # 更新实时指标
            self._update_real_time_metrics(metric)
            
            # 更新聚合指标
            self._update_aggregated_metrics(metric)
    
    def _update_real_time_metrics(self, metric: PerformanceMetric):
        """更新实时指标"""
        self.real_time_metrics['total_calls'] += 1
        self.real_time_metrics['total_duration'] += metric.duration
        self.real_time_metrics['total_tokens'] += metric.tokens
        
        if metric.success:
            self.real_time_metrics['successful_calls'] += 1
        else:
            self.real_time_metrics['failed_calls'] += 1
            if metric.error_type:
                error_key = f'error_{metric.error_type}'
                self.real_time_metrics[error_key] += 1
        
        if metric.cached:
            self.real_time_metrics['cache_hits'] += 1
        else:
            self.real_time_metrics['cache_misses'] += 1
        
        # 按智能体统计
        agent_key = f'agent_{metric.agent_id}'
        self.real_time_metrics[agent_key] += 1
        
        # 按调用类型统计
        call_type_key = f'call_type_{metric.call_type}'
        self.real_time_metrics[call_type_key] += 1
    
    def _update_aggregated_metrics(self, metric: PerformanceMetric):
        """更新聚合指标"""
        # 获取小时键
        hour_key = datetime.fromtimestamp(metric.timestamp).strftime('%Y-%m-%d_%H')
        
        if hour_key not in self.hourly_metrics:
            self.hourly_metrics[hour_key] = AggregatedMetrics()
        
        # 更新小时指标
        hourly = self.hourly_metrics[hour_key]
        hourly.total_calls += 1
        hourly.total_duration += metric.duration
        hourly.total_tokens += metric.tokens
        
        if metric.success:
            hourly.successful_calls += 1
        else:
            hourly.failed_calls += 1
            if metric.error_type:
                hourly.error_distribution[metric.error_type] = (
                    hourly.error_distribution.get(metric.error_type, 0) + 1
                )
        
        if metric.cached:
            hourly.cache_hits += 1
        else:
            hourly.cache_misses += 1
        
        # 计算平均值和比率
        hourly.average_duration = hourly.total_duration / hourly.total_calls
        hourly.success_rate = hourly.successful_calls / hourly.total_calls
        total_cache_attempts = hourly.cache_hits + hourly.cache_misses
        if total_cache_attempts > 0:
            hourly.cache_hit_rate = hourly.cache_hits / total_cache_attempts
        
        # 更新日指标
        self._update_daily_metrics(metric)
    
    def _update_daily_metrics(self, metric: PerformanceMetric):
        """更新日指标"""
        self.daily_metrics.total_calls += 1
        self.daily_metrics.total_duration += metric.duration
        self.daily_metrics.total_tokens += metric.tokens
        
        if metric.success:
            self.daily_metrics.successful_calls += 1
        else:
            self.daily_metrics.failed_calls += 1
            if metric.error_type:
                self.daily_metrics.error_distribution[metric.error_type] = (
                    self.daily_metrics.error_distribution.get(metric.error_type, 0) + 1
                )
        
        if metric.cached:
            self.daily_metrics.cache_hits += 1
        else:
            self.daily_metrics.cache_misses += 1
        
        # 重新计算平均值和比率
        if self.daily_metrics.total_calls > 0:
            self.daily_metrics.average_duration = (
                self.daily_metrics.total_duration / self.daily_metrics.total_calls
            )
            self.daily_metrics.success_rate = (
                self.daily_metrics.successful_calls / self.daily_metrics.total_calls
            )
            
            total_cache_attempts = self.daily_metrics.cache_hits + self.daily_metrics.cache_misses
            if total_cache_attempts > 0:
                self.daily_metrics.cache_hit_rate = (
                    self.daily_metrics.cache_hits / total_cache_attempts
                )
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """获取实时指标"""
        with self._lock:
            # 计算衍生指标
            total_calls = self.real_time_metrics.get('total_calls', 0)
            if total_calls > 0:
                success_rate = self.real_time_metrics.get('successful_calls', 0) / total_calls
                average_duration = self.real_time_metrics.get('total_duration', 0) / total_calls
                
                cache_total = (
                    self.real_time_metrics.get('cache_hits', 0) + 
                    self.real_time_metrics.get('cache_misses', 0)
                )
                cache_hit_rate = (
                    self.real_time_metrics.get('cache_hits', 0) / cache_total 
                    if cache_total > 0 else 0
                )
            else:
                success_rate = 0
                average_duration = 0
                cache_hit_rate = 0
            
            return {
                **dict(self.real_time_metrics),
                'success_rate': success_rate,
                'average_duration': average_duration,
                'cache_hit_rate': cache_hit_rate,
                'metrics_history_size': len(self.metrics_history)
            }
    
    def get_hourly_metrics(self, hours_back: int = 24) -> Dict[str, AggregatedMetrics]:
        """获取按小时聚合的指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cutoff_key = cutoff_time.strftime('%Y-%m-%d_%H')
        
        return {
            hour_key: metrics 
            for hour_key, metrics in self.hourly_metrics.items()
            if hour_key >= cutoff_key
        }
    
    def get_daily_metrics(self) -> AggregatedMetrics:
        """获取日指标"""
        return self.daily_metrics
    
    def get_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取按智能体的性能统计"""
        agent_stats = defaultdict(lambda: {
            'total_calls': 0,
            'successful_calls': 0,
            'total_duration': 0.0,
            'total_tokens': 0,
            'call_types': defaultdict(int)
        })
        
        with self._lock:
            for metric in self.metrics_history:
                stats = agent_stats[metric.agent_id]
                stats['total_calls'] += 1
                stats['total_duration'] += metric.duration
                stats['total_tokens'] += metric.tokens
                stats['call_types'][metric.call_type] += 1
                
                if metric.success:
                    stats['successful_calls'] += 1
        
        # 计算衍生指标
        for agent_id, stats in agent_stats.items():
            if stats['total_calls'] > 0:
                stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
                stats['average_duration'] = stats['total_duration'] / stats['total_calls']
                stats['average_tokens'] = stats['total_tokens'] / stats['total_calls']
        
        return dict(agent_stats)
    
    def _start_cleanup_task(self):
        """启动后台清理任务"""
        def cleanup_old_metrics():
            cutoff_time = time.time() - (self.max_history_hours * 3600)
            
            with self._lock:
                # 清理旧的指标记录
                while (self.metrics_history and 
                       self.metrics_history[0].timestamp < cutoff_time):
                    self.metrics_history.popleft()
                
                # 清理旧的小时指标
                cutoff_hour = datetime.fromtimestamp(cutoff_time).strftime('%Y-%m-%d_%H')
                old_hours = [
                    hour_key for hour_key in self.hourly_metrics.keys()
                    if hour_key < cutoff_hour
                ]
                for hour_key in old_hours:
                    del self.hourly_metrics[hour_key]
        
        # 启动定时清理（每小时执行一次）
        import threading
        
        def periodic_cleanup():
            while True:
                time.sleep(3600)  # 1小时
                try:
                    cleanup_old_metrics()
                except Exception as e:
                    # 记录错误但不中断清理任务
                    pass
        
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
    
    def export_metrics(self, format_type: str = "json") -> Any:
        """导出指标数据"""
        if format_type == "json":
            return {
                'real_time': self.get_real_time_metrics(),
                'hourly': {k: v.__dict__ for k, v in self.get_hourly_metrics().items()},
                'daily': self.daily_metrics.__dict__,
                'agent_performance': self.get_agent_performance(),
                'export_timestamp': time.time()
            }
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def reset_metrics(self):
        """重置所有指标"""
        with self._lock:
            self.metrics_history.clear()
            self.real_time_metrics.clear()
            self.hourly_metrics.clear()
            self.daily_metrics = AggregatedMetrics()
```

## 🚀 实施路线图

### **第1周: LLM通信核心架构**
1. 创建 `UnifiedLLMClientManager` 核心类
2. 实现基础的LLM调用统一接口
3. 集成现有的 `EnhancedLLMClient`
4. 基础单元测试

### **第2周: System Prompt模板系统**
1. 实现 `PromptTemplateEngine` 
2. 创建三个角色的基础模板
3. 实现模板缓存和动态构建
4. 模板系统测试

### **第3周: 错误处理和重试机制**
1. 实现 `RetryStrategy` 和错误分类
2. 创建 `FallbackHandler` 回退处理
3. 集成到LLM客户端管理器
4. 错误处理测试

### **第4周: 性能监控和缓存**
1. 实现 `MetricsCollector` 性能收集
2. 创建缓存系统和优化
3. 集成增强日志系统
4. 性能监控测试

### **第5周: 智能体集成**
1. 修改三个智能体使用新的LLM通信层
2. 保持API兼容性
3. 全面集成测试
4. 性能基准测试

### **第6周: 优化和文档**
1. 性能优化和bug修复
2. 完整文档编写
3. 使用指南和最佳实践
4. 代码清理和发布准备

## 📊 预期收益

### **代码减少量**:
- **LLM调用逻辑**: ~1200行重复代码 → 400行统一实现 = 节省800行
- **System Prompt构建**: ~2400行重复代码 → 600行模板系统 = 节省1800行  
- **错误处理**: ~600行分散代码 → 200行统一处理 = 节省400行
- **总计减少**: ~3000行代码

### **性能提升**:
- **缓存命中率**: 预计40-60%的Prompt调用可以缓存
- **响应时间**: 缓存命中的调用响应时间减少90%以上
- **Token节省**: 通过优化和缓存节省20-30%的Token使用
- **错误恢复**: 统一重试机制提高95%以上的调用成功率

### **维护性改善**:
- **单一代码源**: LLM相关逻辑统一管理
- **配置集中**: 所有LLM配置在一处管理
- **监控完善**: 完整的调用统计和性能分析
- **扩展简化**: 新智能体开发时间减少70%

这个优化方案将彻底解决LLM通信层的重复代码问题，提供企业级的性能监控和错误处理能力，为V-Agent框架奠定坚实的技术基础。