# 数据库工具系统设计指南

## 🎯 概述

本文档详细介绍了中心化智能体框架中的数据库工具系统，包括设计理念、架构实现、使用方法和扩展指南。

## 🏗️ 系统架构

### 核心组件

```
数据库工具系统
├── database_tools.py          # 数据库工具核心实现
│   ├── DatabaseConnector      # 数据库连接器抽象基类
│   ├── SQLiteConnector       # SQLite连接器实现
│   ├── DatabaseToolManager   # 数据库工具管理器
│   └── 工具函数               # 供智能体调用的工具函数
├── tool_registry.py          # 增强的工具注册表
├── agent_prompts.py          # 智能体System Prompt
└── sample_database.py        # 示例数据库创建
```

### 设计原则

1. **抽象化设计**: 通过DatabaseConnector抽象基类支持多种数据库类型
2. **安全优先**: 预定义查询模板防止SQL注入攻击
3. **工具导向**: 智能体通过工具调用访问数据库，而非直接连接
4. **文件路径传递**: 查询结果保存到文件，通过路径在智能体间传递
5. **权限控制**: 基于智能体能力的分层权限管理

## 🔧 核心功能

### 1. 数据库连接管理

```python
# 支持多种数据库连接器
class DatabaseConnector(ABC):
    async def connect(self)
    async def disconnect(self) 
    async def execute_query(self, query: str, params: tuple = None) -> QueryResult
    async def get_schema_info(self) -> Dict[str, Any]

# SQLite实现
class SQLiteConnector(DatabaseConnector):
    # 完整的SQLite支持实现
```

### 2. 安全查询系统

```python
# 预定义的安全查询模板
safe_query_templates = {
    "search_modules": "SELECT * FROM verilog_modules WHERE name LIKE ? OR description LIKE ?",
    "get_module_by_id": "SELECT * FROM verilog_modules WHERE id = ?",
    "search_by_functionality": "SELECT * FROM verilog_modules WHERE functionality LIKE ?",
    # ... 更多模板
}
```

### 3. 智能体工具集成

```python
# 智能体可调用的数据库工具
async def database_search_modules(module_name: str, description: str, limit: int) -> Dict[str, Any]
async def database_get_module(module_id: int) -> Dict[str, Any]
async def database_search_by_functionality(functionality: str, tags: str, limit: int) -> Dict[str, Any]
async def database_get_similar_modules(bit_width: int, functionality: str, limit: int) -> Dict[str, Any]
async def database_get_test_cases(module_id: int, module_name: str) -> Dict[str, Any]
async def database_search_design_patterns(pattern_type: str, description: str, limit: int) -> Dict[str, Any]
```

## 🛠️ 使用方法

### 1. 数据库初始化

```python
from tools.sample_database import setup_database_for_framework

# 创建并配置示例数据库
await setup_database_for_framework("path/to/database.db")
```

### 2. 智能体工具调用

```python
# 在智能体中搜索模块
result = await self.search_database_modules(
    module_name="alu",
    description="arithmetic",
    limit=5
)

# 检查调用结果
if result.get("success"):
    modules = result.get("result", {}).get("data", [])
    for module in modules:
        print(f"找到模块: {module['name']}")
```

### 3. 结果文件保存

```python
# 将查询结果保存到文件
save_result = await self.save_database_result_to_file(
    query_result=search_result['result'],
    file_path="output/search_results.json",
    format_type="json"  # 支持 json, csv, txt
)
```

## 📋 System Prompt集成

### 智能体能力增强

每个智能体都会获得包含数据库工具使用指南的system prompt：

```
## 🗄️ 数据库工具使用指南

### 模块搜索工具
1. **database_search_modules(module_name, description, limit)**:
   - 搜索Verilog模块
   - 示例: `await self.search_database_modules(module_name="alu", description="arithmetic")`

2. **database_search_by_functionality(functionality, tags, limit)**:
   - 按功能搜索模块
   - 示例: `await self.search_by_functionality(functionality="counter", tags="sequential")`

### 数据库查询策略
- 优先使用现有模块：设计前先搜索相似功能的模块
- 检索测试用例：为新设计提供测试参考
- 查找设计模式：遵循最佳实践和标准模式
- 保存查询结果：将重要的搜索结果保存到文件供后续使用
```

### 工作流程优化

智能体现在会在执行任务前自动：

1. **搜索现有模块**: 避免重复开发
2. **检索相关模式**: 遵循最佳实践
3. **获取测试案例**: 参考现有测试方法
4. **保存查询结果**: 供后续智能体使用

## 📊 数据库架构

### 核心数据表

```sql
-- Verilog模块表
CREATE TABLE verilog_modules (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    functionality TEXT,
    bit_width INTEGER,
    tags TEXT,
    code TEXT,
    quality_score REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- 测试用例表
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY,
    module_id INTEGER,
    module_name TEXT,
    test_type TEXT,
    test_vectors TEXT,
    expected_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES verilog_modules (id)
);

-- 设计模式表  
CREATE TABLE design_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    code_template TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 示例数据

系统包含以下示例数据：

- **5个Verilog模块**: ALU、计数器、FIFO、加法器、乘法器
- **4个测试用例**: 涵盖功能测试和边界测试
- **3个设计模式**: Moore FSM、流水线、跨时钟域

## 🔒 安全特性

### 1. SQL注入防护

```python
# 禁止的危险关键词
dangerous_keywords = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
    'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE'
]

# 只允许SELECT查询
if keyword in query_upper:
    return QueryResult(success=False, error=f"禁止执行包含 {keyword} 的查询")
```

### 2. 权限分级管理

```python
# 智能体权限配置
DATABASE_READ = "database_read"      # 只读权限
DATABASE_WRITE = "database_write"    # 写入权限（仅协调者）

# 基于能力的权限分配
if AgentCapability.CODE_GENERATION in capabilities:
    permissions.add(ToolPermission.DATABASE_READ)
if AgentCapability.TASK_COORDINATION in capabilities:
    permissions.add(ToolPermission.DATABASE_WRITE)
```

### 3. 预定义查询模板

所有数据库查询都通过预定义的安全模板执行，避免动态SQL构建。

## 🚀 扩展指南

### 1. 添加新的数据库连接器

```python
class PostgreSQLConnector(DatabaseConnector):
    async def connect(self):
        # PostgreSQL连接实现
        pass
    
    async def execute_query(self, query: str, params: tuple = None) -> QueryResult:
        # PostgreSQL查询实现
        pass
```

### 2. 创建新的查询模板

```python
# 在DatabaseToolManager中添加新模板
self.safe_query_templates["search_by_author"] = """
    SELECT * FROM verilog_modules 
    WHERE author = ? 
    ORDER BY created_at DESC LIMIT ?
"""

# 创建对应的工具函数
async def database_search_by_author(author: str, limit: int = 10) -> Dict[str, Any]:
    result = await db_tool_manager.execute_safe_query(
        "search_by_author", (author, limit)
    )
    return {
        "tool": "database_search_by_author",
        "success": result.success,
        "result": result.to_dict()
    }
```

### 3. 扩展智能体工具能力

```python
# 在BaseAgent中添加新的便捷方法
async def search_by_author(self, author: str, limit: int = 10) -> Dict[str, Any]:
    return await self.call_tool(
        "database_search_by_author",
        author=author,
        limit=limit
    )
```

## 📈 性能优化

### 1. 连接池管理

```python
# 连接复用和自动断开
@asynccontextmanager
async def _get_session(self) -> aiohttp.ClientSession:
    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session
```

### 2. 查询结果缓存

```python
# 在智能体中实现查询缓存
class BaseAgent:
    def __init__(self):
        self.query_cache: Dict[str, Dict] = {}
    
    async def cached_database_search(self, cache_key: str, query_func, **kwargs):
        if cache_key not in self.query_cache:
            self.query_cache[cache_key] = await query_func(**kwargs)
        return self.query_cache[cache_key]
```

### 3. 批量查询优化

```python
# 支持批量查询减少数据库访问次数
async def batch_search_modules(self, search_terms: List[str]) -> List[Dict[str, Any]]:
    results = []
    for term in search_terms:
        result = await self.search_database_modules(module_name=term)
        results.append(result)
    return results
```

## 🧪 测试和验证

### 1. 单元测试

```python
async def test_database_search():
    agent = VerilogDesignAgent()
    result = await agent.search_database_modules(
        module_name="alu",
        description="arithmetic"
    )
    assert result["success"] == True
    assert len(result["result"]["data"]) > 0
```

### 2. 集成测试

```python
async def test_full_workflow():
    # 创建数据库
    await setup_database_for_framework("test.db")
    
    # 创建智能体
    coordinator = CentralizedCoordinator(config)
    design_agent = VerilogDesignAgent()
    coordinator.register_agent(design_agent)
    
    # 执行任务
    result = await coordinator.coordinate_task_execution(
        "设计一个ALU模块，参考现有设计"
    )
    
    assert result["success"] == True
```

### 3. 性能测试

```python
async def test_database_performance():
    start_time = time.time()
    
    # 执行多次查询
    for i in range(100):
        await agent.search_database_modules(f"test_{i}")
    
    duration = time.time() - start_time
    print(f"100次查询耗时: {duration:.2f}秒")
```

## 📝 最佳实践

### 1. 智能体使用建议

- **优先搜索**: 在开始新设计前先搜索现有模块
- **结果保存**: 将重要查询结果保存到文件
- **权限最小化**: 只申请必要的数据库权限
- **错误处理**: 妥善处理数据库连接失败等异常情况

### 2. 数据库设计建议

- **规范化设计**: 避免数据冗余，保持数据一致性
- **索引优化**: 为常用查询字段创建索引
- **版本控制**: 对数据库架构变更进行版本管理
- **备份策略**: 定期备份重要数据

### 3. 查询优化建议

- **使用LIMIT**: 限制查询结果数量避免过载
- **参数化查询**: 使用预定义模板防止SQL注入
- **结果缓存**: 缓存频繁访问的查询结果
- **批量操作**: 减少数据库往返次数

## 🔧 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查数据库路径是否正确
   - 确认数据库文件权限
   - 验证连接配置参数

2. **查询结果为空**
   - 检查数据库是否包含数据
   - 验证查询参数是否正确
   - 确认查询模板语法

3. **工具调用失败**
   - 检查智能体权限配置
   - 验证工具注册是否正确
   - 确认参数类型匹配

### 调试技巧

```python
# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 检查数据库状态
schema = await agent.get_database_schema()
print(f"数据库表: {list(schema.get('tables', {}).keys())}")

# 验证工具注册
tools = agent.tool_registry.get_available_tools()
print(f"可用工具: {list(tools.keys())}")
```

## 🎉 总结

数据库工具系统为中心化智能体框架提供了强大的数据检索和重用能力，主要特点包括：

✅ **完整的架构**: 从连接器到工具函数的完整实现  
✅ **安全设计**: 多层安全防护机制  
✅ **灵活扩展**: 支持多种数据库和查询类型  
✅ **智能集成**: 与智能体工作流程深度集成  
✅ **文件导向**: 基于文件路径的信息传递机制  

通过这个系统，智能体现在可以：
- 🔍 搜索和重用现有的Verilog模块
- 🧪 获取相关的测试用例和设计模式
- 💾 将查询结果保存并在智能体间共享
- 🤖 通过System Prompt获得详细的使用指导

这大大提升了智能体的工作效率和输出质量！