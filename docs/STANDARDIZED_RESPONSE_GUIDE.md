# 智能体标准化响应格式指南

## 🎯 概述

本文档介绍中心化智能体框架中的标准化响应格式系统，该系统确保智能体之间的通信规范化、结构化和可解析。

## 🏗️ 系统架构

### 核心组件

```
标准化响应系统
├── response_format.py      # 响应格式定义和构建器
├── response_parser.py      # 响应解析器和验证器
├── base_agent.py          # 智能体响应方法集成
└── centralized_coordinator.py  # 协调者响应处理
```

### 设计理念

1. **统一格式**: 所有智能体使用相同的响应结构
2. **多格式支持**: 支持JSON、XML、Markdown三种输出格式
3. **自动解析**: 协调者能自动识别和解析不同格式
4. **向后兼容**: 支持传统响应格式的处理
5. **结构化信息**: 包含任务状态、文件路径、质量指标等完整信息

## 📝 响应格式结构

### 标准响应字段

```python
StandardizedResponse:
    # 基本信息
    agent_name: str          # 智能体类名
    agent_id: str           # 智能体实例ID
    task_id: str            # 任务ID
    timestamp: str          # 时间戳
    response_type: ResponseType  # 响应类型
    
    # 状态信息  
    status: TaskStatus      # 任务状态
    completion_percentage: float  # 完成百分比
    message: str            # 主要消息
    
    # 文件信息
    generated_files: List[FileReference]  # 生成的文件
    modified_files: List[FileReference]   # 修改的文件
    reference_files: List[FileReference]  # 参考文件
    
    # 问题和质量
    issues: List[IssueReport]       # 问题报告
    quality_metrics: QualityMetrics  # 质量指标
    
    # 额外信息
    resource_requests: List[ResourceRequest]  # 资源请求
    next_steps: List[str]           # 下一步建议
    metadata: Dict[str, Any]        # 元数据
```

### 响应类型枚举

```python
class ResponseType(Enum):
    TASK_COMPLETION = "task_completion"      # 任务完成
    PROGRESS_UPDATE = "progress_update"      # 进度更新
    ERROR_REPORT = "error_report"           # 错误报告
    RESOURCE_REQUEST = "resource_request"    # 资源请求
    QUALITY_REPORT = "quality_report"       # 质量报告
```

### 任务状态枚举

```python
class TaskStatus(Enum):
    SUCCESS = "success"               # 成功完成
    PARTIAL_SUCCESS = "partial_success"  # 部分成功
    FAILED = "failed"                # 失败
    IN_PROGRESS = "in_progress"      # 进行中
    REQUIRES_RETRY = "requires_retry" # 需要重试
```

## 🔧 使用方法

### 1. 在智能体中创建响应

#### 方法一：使用便捷方法

```python
class MyAgent(BaseAgent):
    async def execute_task(self, task_message):
        try:
            # 执行任务逻辑
            result = self.process_task(task_message)
            
            # 创建成功响应
            return self.create_success_response_formatted(
                task_id=task_message.task_id,
                message="任务成功完成，生成了ALU模块",
                generated_files=["/output/alu.v", "/output/alu_tb.v"],
                format_type=ResponseFormat.JSON
            )
            
        except Exception as e:
            # 创建错误响应
            return self.create_error_response_formatted(
                task_id=task_message.task_id,
                error_message=f"任务执行失败: {str(e)}",
                error_details="请检查输入参数和系统状态"
            )
```

#### 方法二：使用ResponseBuilder

```python
async def execute_complex_task(self, task_message):
    builder = self.create_response_builder(task_message.task_id)
    
    # 添加生成的文件
    builder.add_generated_file(
        "/output/processor.v", "verilog", "32位处理器核心模块"
    )
    
    # 添加问题报告
    builder.add_issue(
        "warning", "medium", "时钟域交叉可能存在亚稳态风险",
        location="processor.v:145", 
        solution="添加同步器电路"
    )
    
    # 添加质量指标
    quality = QualityMetrics(
        overall_score=0.85,
        syntax_score=0.95,
        functionality_score=0.80,
        test_coverage=0.75,
        documentation_quality=0.90
    )
    
    # 添加下一步建议
    builder.add_next_step("运行功能仿真验证")
    builder.add_next_step("执行时序分析")
    
    # 构建响应
    response = builder.build(
        response_type=ResponseType.TASK_COMPLETION,
        status=TaskStatus.SUCCESS,
        message="处理器模块设计完成，包含完整的ALU和控制单元",
        completion_percentage=100.0,
        quality_metrics=quality
    )
    
    return response.format_response(ResponseFormat.JSON)
```

### 2. 响应格式示例

#### JSON格式

```json
{
  "agent_name": "VerilogDesignAgent",
  "agent_id": "verilog_designer_01",
  "response_type": "task_completion",
  "task_id": "design_alu_001",
  "timestamp": "2024-01-01T10:30:00",
  "status": "success",
  "completion_percentage": 100.0,
  "message": "成功设计了32位ALU模块，包含8种运算功能",
  "generated_files": [
    {
      "path": "/output/alu_32bit.v",
      "file_type": "verilog",
      "description": "32位算术逻辑单元主模块"
    },
    {
      "path": "/output/alu_32bit_tb.v", 
      "file_type": "testbench",
      "description": "ALU模块测试平台"
    }
  ],
  "issues": [
    {
      "issue_type": "warning",
      "severity": "low",
      "description": "建议添加溢出检测逻辑",
      "location": "alu_32bit.v:67"
    }
  ],
  "quality_metrics": {
    "overall_score": 0.88,
    "syntax_score": 0.95,
    "functionality_score": 0.85,
    "test_coverage": 0.80,
    "documentation_quality": 0.90
  },
  "next_steps": [
    "运行功能仿真测试",
    "进行时序分析验证"
  ],
  "metadata": {
    "bit_width": 32,
    "operations": ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA"]
  }
}
```

#### Markdown格式

```markdown
# Agent Response: VerilogDesignAgent

## 📋 Basic Information
- **Agent**: VerilogDesignAgent (`verilog_designer_01`)
- **Task ID**: `design_alu_001`
- **Response Type**: task_completion
- **Status**: success
- **Progress**: 100.0%
- **Timestamp**: 2024-01-01T10:30:00

## 💬 Message
成功设计了32位ALU模块，包含8种运算功能

## 📁 Files
### Generated Files
- **/output/alu_32bit.v** (verilog): 32位算术逻辑单元主模块
- **/output/alu_32bit_tb.v** (testbench): ALU模块测试平台

## ⚠️ Issues
### 🟢 Warning - Low
**Description**: 建议添加溢出检测逻辑
**Location**: `alu_32bit.v:67`

## 📊 Quality Metrics
- **Overall Score**: 0.88
- **Syntax Score**: 0.95
- **Functionality Score**: 0.85
- **Test Coverage**: 0.80
- **Documentation Quality**: 0.90

## 🚀 Next Steps
1. 运行功能仿真测试
2. 进行时序分析验证

## 🔍 Metadata
- **bit_width**: 32
- **operations**: ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA']
```

### 3. 协调者处理

协调者会自动解析和处理标准化响应：

```python
# 协调者内部处理
async def process_agent_task(self, agent_id, task_message):
    # 1. 智能体执行任务
    raw_response = await agent.process_task_with_file_references(task_message)
    
    # 2. 自动解析响应
    parsed_response = await self._process_agent_response(
        agent_id=agent_id,
        raw_response=raw_response, 
        task_id=task_message.task_id
    )
    
    # 3. 提取关键信息用于决策
    if parsed_response["success"]:
        print(f"✅ {agent_id} 任务完成")
        files = parsed_response.get("file_references", [])
        print(f"📁 生成文件: {len(files)} 个")
        
        # 检查质量指标
        quality = parsed_response.get("quality_metrics")
        if quality and quality["overall_score"] < 0.7:
            print("⚠️ 质量分数较低，可能需要重新处理")
```

## 🔍 响应解析和验证

### 自动格式检测

系统能自动检测响应格式：

```python
parser = ResponseParser()

# 自动检测并解析
standardized_response = parser.parse_response(response_content)

# 或指定格式解析
json_response = parser.parse_response(content, ResponseFormat.JSON)
xml_response = parser.parse_response(content, ResponseFormat.XML)
md_response = parser.parse_response(content, ResponseFormat.MARKDOWN)
```

### 响应验证

```python
# 验证响应完整性
validation_errors = parser.validate_response(standardized_response)

if validation_errors:
    print("响应验证失败:")
    for error in validation_errors:
        print(f"  - {error}")
else:
    print("响应验证通过")
```

### 提取关键信息

```python
# 提取决策关键信息
key_info = parser.extract_key_information(standardized_response)

print(f"任务状态: {key_info['status']}")
print(f"完成度: {key_info['completion_percentage']}%")
print(f"是否有严重错误: {key_info['has_errors']}")
print(f"生成文件数: {key_info['generated_files_count']}")
```

## ⚙️ 配置和设置

### 设置首选格式

```python
# 在协调者中设置首选响应格式
coordinator.set_preferred_response_format(ResponseFormat.JSON)

# 获取格式说明
instructions = coordinator.get_response_format_instructions()
```

### 环境变量配置

```bash
# 在.env文件中配置
CAF_PREFERRED_RESPONSE_FORMAT=json  # json, xml, markdown
CAF_ENABLE_RESPONSE_VALIDATION=true
CAF_RESPONSE_TIMEOUT=30
```

## 🧪 测试和调试

### 运行测试

```bash
# 运行标准化响应格式测试
python test_standardized_response.py
```

### 调试技巧

```python
# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 检查响应解析过程
parser = ResponseParser()
try:
    response = parser.parse_response(content)
    print("✅ 解析成功")
except ResponseParseError as e:
    print(f"❌ 解析失败: {str(e)}")
    
# 验证响应格式
errors = parser.validate_response(response)
if errors:
    print("格式问题:")
    for error in errors:
        print(f"  - {error}")
```

## 📊 最佳实践

### 1. 智能体响应设计

```python
# ✅ 好的做法
async def execute_task(self, task_message):
    builder = self.create_response_builder(task_message.task_id)
    
    try:
        # 执行主要任务
        result = await self.main_task_logic(task_message)
        
        # 添加生成的文件
        for file_path in result.generated_files:
            builder.add_generated_file(
                file_path, 
                self._detect_file_type(file_path),
                f"Generated by {self.agent_id}"
            )
        
        # 添加质量指标
        quality = self.calculate_quality_metrics(result)
        
        # 构建成功响应
        response = builder.build(
            response_type=ResponseType.TASK_COMPLETION,
            status=TaskStatus.SUCCESS,
            message="任务成功完成",
            completion_percentage=100.0,
            quality_metrics=quality
        )
        
        return response.format_response(ResponseFormat.JSON)
        
    except Exception as e:
        # 构建错误响应
        builder.add_issue("error", "high", str(e))
        response = builder.build(
            response_type=ResponseType.ERROR_REPORT,
            status=TaskStatus.FAILED,
            message=f"任务执行失败: {str(e)}",
            completion_percentage=0.0
        )
        
        return response.format_response(ResponseFormat.JSON)
```

### 2. 响应消息编写

```python
# ✅ 清晰、具体的消息
message = "成功生成32位RISC-V处理器核心，包含5级流水线和分支预测器"

# ❌ 模糊、不具体的消息  
message = "任务完成"
```

### 3. 文件引用管理

```python
# ✅ 详细的文件描述
builder.add_generated_file(
    "/output/riscv_core.v", 
    "verilog",
    "32位RISC-V处理器核心，支持RV32I指令集"
)

# ❌ 模糊的文件描述
builder.add_generated_file("/output/core.v", "verilog", "处理器")
```

### 4. 问题报告

```python
# ✅ 完整的问题报告
builder.add_issue(
    issue_type="warning",
    severity="medium", 
    description="分支预测器的预测准确率较低 (65%)",
    location="branch_predictor.v:89-95",
    solution="考虑使用2位饱和计数器或全局历史预测器"
)

# ❌ 不完整的问题报告
builder.add_issue("warning", "medium", "性能问题")
```

## 🔧 扩展和自定义

### 添加新的响应类型

```python
class ResponseType(Enum):
    TASK_COMPLETION = "task_completion"
    PROGRESS_UPDATE = "progress_update"
    ERROR_REPORT = "error_report"
    RESOURCE_REQUEST = "resource_request"
    QUALITY_REPORT = "quality_report"
    # 添加新类型
    OPTIMIZATION_REPORT = "optimization_report"
    VERIFICATION_RESULT = "verification_result"
```

### 自定义质量指标

```python
@dataclass
class CustomQualityMetrics:
    overall_score: float
    syntax_score: float
    functionality_score: float
    test_coverage: float
    documentation_quality: float
    # 自定义指标
    timing_closure: float
    area_efficiency: float
    power_consumption: float
```

### 扩展文件类型

```python
def _detect_file_type(self, file_path: str) -> str:
    if file_path.endswith('.v'):
        return 'verilog'
    elif file_path.endswith('.sv'):
        return 'systemverilog'
    elif file_path.endswith('.vhd'):
        return 'vhdl'
    elif file_path.endswith('.py'):
        return 'python'
    elif file_path.endswith('.cpp'):
        return 'cpp'
    # 添加更多文件类型...
```

## 🚨 常见问题

### 1. 响应解析失败

**问题**: `ResponseParseError: JSON解析失败`

**解决方案**:
- 检查JSON格式是否正确
- 确保所有必需字段都存在
- 验证数据类型是否匹配

```python
# 调试JSON格式
import json
try:
    data = json.loads(response_content)
    print("JSON格式正确")
except json.JSONDecodeError as e:
    print(f"JSON格式错误: {str(e)}")
```

### 2. 响应验证失败

**问题**: `completion_percentage 超出有效范围 (0-100)`

**解决方案**:
```python
# 确保百分比在有效范围内
completion_percentage = max(0.0, min(100.0, calculated_percentage))
```

### 3. 文件路径问题

**问题**: 生成的文件路径不存在

**解决方案**:
```python
# 在添加文件引用前检查文件是否存在
if os.path.exists(file_path):
    builder.add_generated_file(file_path, file_type, description)
else:
    builder.add_issue("error", "high", f"生成的文件不存在: {file_path}")
```

## 📈 性能优化

### 1. 响应缓存

```python
class ResponseCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    
    def get_cached_response(self, key):
        return self.cache.get(key)
    
    def cache_response(self, key, response):
        if len(self.cache) >= self.max_size:
            # 移除最旧的条目
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = response
```

### 2. 异步处理

```python
async def process_multiple_responses(self, responses):
    """并行处理多个响应"""
    tasks = []
    for response in responses:
        task = asyncio.create_task(
            self.response_parser.parse_response(response)
        )
        tasks.append(task)
    
    return await asyncio.gather(*tasks)
```

## 🎉 总结

标准化响应格式系统为中心化智能体框架提供了：

✅ **统一通信**: 所有智能体使用相同的响应结构  
✅ **多格式支持**: JSON、XML、Markdown三种输出格式  
✅ **自动解析**: 协调者智能识别和处理响应  
✅ **完整信息**: 包含状态、文件、质量、问题等完整信息  
✅ **向后兼容**: 支持传统响应格式的处理  
✅ **易于扩展**: 支持自定义响应类型和质量指标  

通过使用标准化响应格式，智能体之间的协作变得更加高效、可靠和易于管理！