# System Prompt 传递问题修复报告

## 问题概述

在LLM协调智能体的运行过程中，发现两个关键问题：

1. **System Prompt 没有正确传递**：LLM没有接收到强制性的系统提示词
2. **工具调用格式错误**：LLM返回了描述性文本而不是JSON格式的工具调用

## 问题分析

### 1. System Prompt 传递问题

**根本原因**：
- 在 `LLMCoordinatorAgent._call_llm_for_function_calling` 方法中，使用了优化的LLM调用机制
- 优化机制通过 `is_first_call` 判断是否传递system prompt
- 判断逻辑 `len(conversation) <= 1` 存在问题，导致后续调用不传递system prompt

**问题代码**：
```python
# 原始有问题的代码
is_first_call = len(conversation) <= 1  # 这个判断有问题

response = await self.llm_client.send_prompt_optimized(
    conversation_id=self.current_conversation_id,
    user_message=user_message.strip(),
    system_prompt=self._build_enhanced_system_prompt() if is_first_call else None,  # 问题在这里
    temperature=0.3,
    max_tokens=4000,
    force_refresh_system=is_first_call
)
```

**问题表现**：
- 从日志可以看到，LLM返回了完整的策略描述和JSON格式，而不是工具调用
- 这说明system prompt中的"禁止直接回答"、"必须调用工具"等规则没有被正确传递

### 2. 工具调用格式问题

**根本原因**：
- 由于system prompt没有正确传递，LLM没有接收到强制性的规则
- LLM按照默认行为生成了描述性文本，而不是JSON工具调用格式

**问题表现**：
- LLM生成了完整的markdown格式的策略描述
- 包含了表格、分析、建议等被system prompt明确禁止的内容
- 没有按照system prompt要求的JSON工具调用格式返回

## 修复方案

### 1. 修复 System Prompt 传递

**修复内容**：
- 移除有问题的 `is_first_call` 判断逻辑
- 始终传递system prompt，确保规则被正确应用
- 强制刷新system prompt缓存

**修复代码**：
```python
# 修复后的代码
async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
    """实现LLM调用 - 修复system prompt传递问题"""
    # 生成对话ID（如果还没有）
    if not hasattr(self, 'current_conversation_id') or not self.current_conversation_id:
        self.current_conversation_id = f"coordinator_agent_{int(time.time())}"
    
    # 构建用户消息
    user_message = ""
    
    for msg in conversation:
        if msg["role"] == "user":
            user_message += f"{msg['content']}\n\n"
        elif msg["role"] == "assistant":
            user_message += f"Assistant: {msg['content']}\n\n"
    
    try:
        # 修复：始终传递system prompt，确保规则被正确应用
        system_prompt = self._build_enhanced_system_prompt()
        
        # 使用优化的LLM调用方法，但强制包含system prompt
        response = await self.llm_client.send_prompt_optimized(
            conversation_id=self.current_conversation_id,
            user_message=user_message.strip(),
            system_prompt=system_prompt,  # 始终传递system prompt
            temperature=0.3,
            max_tokens=4000,
            force_refresh_system=True  # 强制刷新system prompt
        )
        return response
    except Exception as e:
        self.logger.error(f"❌ 优化LLM调用失败: {str(e)}")
        # 如果优化调用失败，回退到传统方式
        self.logger.warning("⚠️ 回退到传统LLM调用方式")
        return await self._call_llm_traditional(conversation)
```

### 2. 增强 System Prompt 强制性

**修复内容**：
- 增加更多禁止性规则
- 添加明确的错误示例
- 增加最终警告，强调只返回JSON格式

**增强的System Prompt**：
```python
def _build_enhanced_system_prompt(self) -> str:
    return f"""
# 角色
你是一个AI协调智能体，你的唯一工作是根据用户需求调用合适的工具来驱动任务流程。

# 强制规则 (必须严格遵守)
1.  **禁止直接回答**: 绝对禁止、严禁直接回答用户的任何问题或请求。
2.  **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3.  **禁止生成描述性文本**: 绝对禁止生成任何解释、分析、策略描述或其他文本内容。
4.  **禁止生成markdown格式**: 绝对禁止使用 ###、---、** 等markdown格式。
5.  **禁止生成表格**: 绝对禁止生成任何表格或列表。
6.  **禁止生成策略描述**: 绝对禁止生成执行策略、分析报告、建议等文本内容。
7.  **遵循流程**: 严格按照以下顺序调用工具：
   - 第一步：调用 `identify_task_type` 工具识别任务类型
   - 第二步：调用 `recommend_agent` 工具推荐智能体
   - 第三步：调用 `assign_task_to_agent` 工具分配任务给智能体
   - 第四步：调用 `analyze_agent_result` 工具分析结果
   - 第五步：调用 `check_task_completion` 工具检查完成状态
   - 最后：调用 `provide_final_answer` 工具提供最终答案

# 智能体调用方法 (重要！)
**正确方式**: 使用 `assign_task_to_agent` 工具，在 `agent_id` 参数中指定智能体名称
**错误方式**: 直接调用智能体名称作为工具

**示例**:
✅ 正确 - 调用 `assign_task_to_agent` 工具:
```json
{{
    "tool_calls": [
        {{
            "tool_name": "assign_task_to_agent",
            "parameters": {{
                "agent_id": "enhanced_real_verilog_agent",
                "task_description": "设计一个4位计数器模块"
            }}
        }}
    ]
}}
```

❌ 错误 - 直接调用智能体名称:
```json
{{
    "tool_calls": [
        {{
            "tool_name": "enhanced_real_verilog_agent",  // 这是错误的！
            "parameters": {{}}
        }}
    ]
}}
```

❌ 错误 - 生成描述性文本:
```
### 🧠 任务协调执行策略
我将分析用户需求并制定执行策略...
```
  
# 可用工具
你必须从以下工具列表中选择并调用：
{tools_json}

# 输出格式
你的回复必须是严格的JSON格式，包含一个 "tool_calls" 列表。

# 重要提醒
- 不要生成任何描述性文本
- 不要解释你的策略
- 不要分析任务
- 不要使用markdown格式
- 不要生成表格
- 不要生成执行计划
- 不要生成分析报告
- 只生成工具调用JSON
- 立即开始调用第一个工具：`identify_task_type`

# 最终警告
如果你生成任何非JSON格式的文本，系统将拒绝你的响应。你必须且只能返回JSON格式的工具调用。

立即开始分析用户请求并调用第一个工具：`identify_task_type`。
"""
```

### 3. 修复优化LLM客户端的缓存逻辑

**修复内容**：
- 修复 `force_refresh_system` 参数的处理逻辑
- 确保当 `force_refresh_system=True` 时，强制包含system prompt

**修复代码**：
```python
# 判断是否包含system prompt - 修复：当force_refresh_system=True时，强制包含
include_system = force_refresh_system or self._should_include_system_prompt(context, system_prompt)
```

## 修复效果

### 预期改进

1. **System Prompt 正确传递**：
   - 每次LLM调用都会包含完整的system prompt
   - 强制规则被正确应用

2. **工具调用格式正确**：
   - LLM返回JSON格式的工具调用
   - 不再生成描述性文本、markdown格式或表格

3. **流程执行正确**：
   - 按照预定的工具调用顺序执行
   - 正确调用智能体分配工具

### 验证方法

创建了测试脚本 `test_system_prompt_fix.py` 来验证修复效果：

```python
# 检查是否返回了工具调用格式
coordination_result = result.get('coordination_result', '')
if 'tool_calls' in coordination_result or 'identify_task_type' in coordination_result:
    print("✅ System prompt修复成功 - 返回了工具调用格式")
else:
    print("❌ System prompt修复失败 - 仍然返回了描述性文本")
```

## 总结

通过以上修复，解决了两个关键问题：

1. **System Prompt 传递问题**：通过始终传递system prompt和强制刷新缓存解决
2. **工具调用格式问题**：通过增强system prompt的强制性和明确性解决

这些修复确保了LLM协调智能体能够：
- 正确接收和应用系统规则
- 返回正确的JSON工具调用格式
- 按照预定的流程执行任务

修复后的系统应该能够正常工作，不再出现描述性文本输出的问题。 