# Core - 核心功能模块

## 目录说明

本目录包含系统的核心功能模块，提供通用的工具和服务，供其他业务模块调用。

## 目录结构

```
core/
├── mcp/                  # MCP工具管理模块
│   ├── tools_selection.py    # 工具选择逻辑
│   └── README.md             # MCP模块说明
└── README.md             # 本文件
```

## 主要模块

### 1. MCP模块 (mcp/)

MCP (Model Context Protocol) 工具管理模块，负责智能选择和管理系统中的各种工具。

**核心功能**：
- 基于Agent的智能工具选择
- 基于关键词的工具匹配
- 工具分类管理
- 工具信息查询

**详细文档**: 参见 [mcp/README.md](./mcp/README.md)

## 设计原则

### 1. 模块化设计
- 每个模块职责单一，功能明确
- 模块间低耦合，高内聚
- 便于测试和维护

### 2. 可扩展性
- 支持插件式扩展
- 提供统一的接口规范
- 易于添加新功能

### 3. 通用性
- 核心功能与业务逻辑分离
- 可被多个业务模块复用
- 提供灵活的配置选项

## 使用示例

### 使用MCP工具选择

```python
from core.mcp.tools_selection import ToolsSelector

# 创建工具选择器实例
selector = ToolsSelector()

# 根据策略描述选择相关工具
strategy_desc = "筛选放量突破的股票"
selected_tools = selector.select_relevant_tools(
    strategy_description=strategy_desc,
    use_agent=True  # 使用Agent智能匹配
)

print(f"选中的工具: {[tool['name'] for tool in selected_tools]}")
```

### 按类别获取工具

```python
from core.mcp.tools_selection import ToolsSelector

selector = ToolsSelector()

# 获取所有数据获取类工具
data_tools = selector.get_tools_by_category('数据获取')

# 获取所有筛选类工具
screen_tools = selector.get_tools_by_category('筛选')
```

## 核心类说明

### ToolsSelector

工具选择器类，提供智能工具选择功能。

**主要方法**：
- `select_relevant_tools()`: 选择相关工具（Agent + 关键词）
- `get_tools_by_category()`: 按类别获取工具
- `get_all_tools()`: 获取所有可用工具
- `get_tool_info()`: 获取特定工具信息

**初始化参数**：
- `llm_client`: 可选的LLM客户端实例
- `tools`: 可选的工具列表（默认从配置加载）

## 扩展开发

### 添加新的核心模块

1. 在 `core/` 下创建新目录
2. 实现模块功能
3. 创建模块的 README.md
4. 在本文件中添加模块说明

### 模块开发规范

```python
# 模块结构示例
core/
└── new_module/
    ├── __init__.py       # 模块初始化
    ├── core_class.py     # 核心类实现
    ├── utils.py          # 工具函数
    ├── README.md         # 模块文档
    └── tests/            # 单元测试
        └── test_core_class.py
```

## 依赖关系

```
core/
  ├── 依赖: config (配置模块)
  └── 被依赖: stock_asking_system (业务模块)
```

## 测试

```bash
# 运行核心模块测试
python -m pytest core/tests/

# 运行特定模块测试
python -m pytest core/mcp/tests/
```

## 注意事项

1. **配置依赖**: 核心模块依赖 `config` 模块，确保配置正确
2. **版本兼容**: 修改核心模块时注意向后兼容性
3. **文档更新**: 添加新功能时同步更新文档
4. **单元测试**: 核心功能必须有完善的单元测试

## 未来规划

- [ ] 添加缓存管理模块
- [ ] 添加日志管理模块
- [ ] 添加数据库连接池模块
- [ ] 添加任务调度模块
- [ ] 完善单元测试覆盖率