# LLM协调智能体框架使用指南

## 🧠 概述

LLM协调智能体框架是一个基于大语言模型的智能协调系统，将复杂的规则判断逻辑写入system prompt，实现智能的任务分配和流程协调。

### 核心特点

1. **智能决策**: 基于LLM的智能任务分析和分配
2. **上下文保持**: 长期维护对话上下文，支持多轮交互
3. **动态协调**: 根据任务特征和智能体能力动态调整策略
4. **质量保证**: 内置结果质量评估和改进机制

## 🏗️ 架构设计

### 组件结构

```
LLMCoordinatorAgent (协调智能体)
├── 任务分析器 (Task Analyzer)
├── 智能体管理器 (Agent Manager)
├── 结果评估器 (Result Evaluator)
└── 上下文管理器 (Context Manager)

工作智能体 (Worker Agents)
├── EnhancedRealVerilogAgent (设计智能体)
├── EnhancedRealCodeReviewAgent (审查智能体)
└── 其他专业智能体...
```

### 工作流程

1. **任务接收**: 协调智能体接收用户请求
2. **任务分析**: LLM分析任务类型、复杂度和需求
3. **智能体选择**: 根据任务特征选择最合适的智能体
4. **任务分配**: 将任务分配给选定的智能体
5. **结果评估**: 分析智能体执行结果的质量
6. **决策下一步**: 决定继续、完成或调整策略
7. **上下文更新**: 维护对话历史和任务状态

## 🚀 快速开始

### 基本使用

```python
import asyncio
from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def basic_example():
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建并注册工作智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(code_reviewer_agent)
    
    # 执行协调任务
    result = await coordinator.coordinate_task(
        user_request="设计一个8位加法器模块",
        conversation_id="my_conversation_123",
        max_iterations=10
    )
    
    print(f"任务完成: {result['success']}")
    print(f"协调结果: {result['coordination_result'][:200]}...")

# 运行示例
asyncio.run(basic_example())
```

### 多轮对话示例

```python
async def multi_turn_example():
    config = FrameworkConfig.from_env()
    coordinator = LLMCoordinatorAgent(config)
    
    # 注册智能体...
    
    conversation_id = "multi_turn_example"
    
    # 第一轮：设计任务
    result1 = await coordinator.coordinate_task(
        user_request="设计一个4位计数器",
        conversation_id=conversation_id,
        max_iterations=8
    )
    
    # 第二轮：基于第一轮结果改进
    result2 = await coordinator.coordinate_task(
        user_request="基于之前的设计，添加参数化支持",
        conversation_id=conversation_id,
        max_iterations=8
    )
    
    # 第三轮：质量检查
    result3 = await coordinator.coordinate_task(
        user_request="对设计进行全面的质量检查",
        conversation_id=conversation_id,
        max_iterations=8
    )
    
    return [result1, result2, result3]
```

## 🛠️ 协调工具

### 1. assign_task_to_agent

分配任务给指定的智能体。

**参数**:
- `agent_id`: 目标智能体ID
- `task_description`: 任务描述
- `task_context`: 任务上下文信息
- `expected_output`: 期望的输出格式

**示例**:
```python
# 在system prompt中调用
{
    "tool_name": "assign_task_to_agent",
    "parameters": {
        "agent_id": "enhanced_real_verilog_agent",
        "task_description": "设计一个8位ALU模块",
        "expected_output": "完整的Verilog代码和测试台"
    }
}
```

### 2. analyze_agent_result

分析智能体执行结果并决定下一步。

**参数**:
- `agent_id`: 执行任务的智能体ID
- `result`: 智能体执行结果
- `task_context`: 当前任务上下文

**返回**:
- `analysis`: 结果质量分析
- `next_action`: 下一步行动建议
- `recommendations`: 改进建议

### 3. check_task_completion

检查任务是否完成。

**参数**:
- `task_id`: 任务ID
- `all_results`: 所有智能体的执行结果
- `original_requirements`: 原始需求

**返回**:
- `is_completed`: 是否完成
- `completion_score`: 完成度评分
- `missing_requirements`: 缺失的需求
- `quality_assessment`: 质量评估

### 4. query_agent_status

查询智能体状态和能力。

**参数**:
- `agent_id`: 智能体ID

**返回**:
- `status`: 智能体状态
- `capabilities`: 能力列表
- `specialty`: 专业领域
- `success_count`: 成功次数
- `failure_count`: 失败次数

## 🎯 决策逻辑

### 任务类型识别

协调智能体会自动识别以下任务类型：

- **设计任务**: 需要生成Verilog代码、电路设计
- **验证任务**: 需要测试台生成、仿真验证
- **分析任务**: 需要代码审查、质量分析
- **调试任务**: 需要错误分析、问题修复

### 智能体能力匹配

- **enhanced_real_verilog_agent**: 擅长Verilog代码设计和生成，支持Schema验证
- **enhanced_real_code_review_agent**: 擅长代码审查、测试台生成、仿真验证，支持Schema验证

### 执行流程决策

1. **单阶段任务**: 直接分配给最合适的智能体
2. **多阶段任务**: 按阶段顺序分配，每阶段完成后评估结果
3. **迭代任务**: 根据结果质量决定是否需要继续迭代
4. **协作任务**: 多个智能体协作完成复杂任务

## 📊 结果分析

### 质量评估标准

1. **功能完整性**: 是否满足所有功能需求
2. **代码质量**: 代码是否规范、可读、可维护
3. **测试覆盖**: 是否有充分的测试验证
4. **错误处理**: 是否处理了边界情况和异常

### 迭代决策逻辑

- **继续迭代**: 结果不完整、质量不达标、有明确改进空间
- **完成任务**: 结果完整、质量达标、满足所有需求
- **切换策略**: 当前方法无效，需要换其他智能体或方法

## 🔧 高级配置

### 自定义协调策略

```python
class CustomLLMCoordinatorAgent(LLMCoordinatorAgent):
    def _build_enhanced_system_prompt(self) -> str:
        # 自定义system prompt
        custom_prompt = """
        你是一个专业的硬件设计协调专家...
        
        # 添加自定义决策逻辑
        ## 自定义策略
        - 优先考虑性能优化
        - 重点关注功耗控制
        - 强调可测试性设计
        """
        
        return custom_prompt + "\n\n" + self._build_tools_description()
    
    def _analyze_result_quality(self, result: Dict[str, Any], 
                              task_context: Dict[str, Any]) -> Dict[str, Any]:
        # 自定义质量分析逻辑
        analysis = super()._analyze_result_quality(result, task_context)
        
        # 添加自定义评估标准
        if "power" in str(result).lower():
            analysis["quality_score"] += 10
            analysis["strengths"].append("包含功耗考虑")
        
        return analysis
```

### 智能体扩展

```python
class CustomVerilogAgent(EnhancedRealVerilogAgent):
    def get_specialty_description(self) -> str:
        return "高级Verilog设计专家，专注于高性能和低功耗设计"
    
    def get_capabilities(self) -> Set[AgentCapability]:
        capabilities = super().get_capabilities()
        capabilities.add(AgentCapability.POWER_OPTIMIZATION)
        return capabilities

# 注册自定义智能体
custom_agent = CustomVerilogAgent(config)
await coordinator.register_agent(custom_agent)
```

## 📈 性能优化

### 1. 智能体缓存

```python
# 启用智能体结果缓存
coordinator.enable_agent_cache = True
coordinator.cache_ttl = 3600  # 1小时缓存
```

### 2. 并行执行

```python
# 支持并行任务执行
async def parallel_execution():
    tasks = [
        coordinator.coordinate_task("任务1", conversation_id="conv1"),
        coordinator.coordinate_task("任务2", conversation_id="conv2"),
        coordinator.coordinate_task("任务3", conversation_id="conv3")
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 结果复用

```python
# 复用之前的执行结果
previous_results = coordinator.get_agent_results("previous_task_id")
if previous_results:
    # 基于之前的结果继续
    result = await coordinator.coordinate_task(
        "基于之前结果改进",
        conversation_id="conv_id",
        previous_results=previous_results
    )
```

## 🐛 故障排除

### 常见问题

1. **智能体选择不准确**
   - 检查智能体的能力描述是否准确
   - 优化system prompt中的决策逻辑
   - 增加智能体的历史表现权重

2. **上下文丢失**
   - 确保conversation_id一致
   - 检查preserve_context参数
   - 验证对话历史管理

3. **结果质量不达标**
   - 调整质量评估标准
   - 增加迭代次数
   - 优化智能体的任务描述

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看协调决策过程
coordinator.enable_decision_logging = True

# 分析智能体选择原因
for agent_id, agent_info in coordinator.get_registered_agents().items():
    print(f"智能体 {agent_id}: {agent_info.specialty}")
    print(f"  能力: {[cap.value for cap in agent_info.capabilities]}")
    print(f"  成功率: {agent_info.success_count}/{agent_info.success_count + agent_info.failure_count}")
```

## 📚 最佳实践

### 1. 任务描述优化

- **明确需求**: 详细描述功能要求和约束条件
- **分阶段**: 将复杂任务分解为多个阶段
- **质量要求**: 明确说明质量标准和验收条件

### 2. 智能体管理

- **能力匹配**: 确保智能体能力与任务需求匹配
- **负载均衡**: 避免单个智能体过载
- **性能监控**: 定期评估智能体的成功率

### 3. 上下文管理

- **一致性**: 使用一致的conversation_id
- **完整性**: 确保上下文信息完整传递
- **清理**: 及时清理过期的上下文数据

### 4. 结果评估

- **多维度**: 从功能、质量、性能等多个维度评估
- **迭代改进**: 基于评估结果进行迭代改进
- **用户反馈**: 收集用户反馈优化评估标准

## 🔮 未来扩展

### 计划中的功能

1. **自适应学习**: 根据历史表现自动调整决策策略
2. **智能体发现**: 自动发现和集成新的智能体
3. **分布式协调**: 支持跨节点的分布式协调
4. **可视化监控**: 提供协调过程的可视化监控界面

### 贡献指南

欢迎贡献代码和改进建议！请参考以下步骤：

1. Fork项目仓库
2. 创建功能分支
3. 实现改进功能
4. 添加测试用例
5. 提交Pull Request

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交Issue到项目仓库
- 发送邮件到项目维护者
- 参与项目讨论区

---

*LLM协调智能体框架 - 让AI协作更智能* 