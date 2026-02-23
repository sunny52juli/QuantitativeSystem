# MCP - 工具选择与管理模块

## 模块简介

MCP (Model Context Protocol) 工具选择模块负责智能选择和管理系统中的各种工具。通过结合AI Agent和关键词匹配，自动识别用户策略描述中需要使用的工具。

## 文件结构

```
mcp/
├── tools_selection.py    # 工具选择核心逻辑
└── README.md             # 本文件
```

## 核心功能

### 1. 智能工具选择

结合两种匹配方式，确保工具选择的准确性和覆盖面：

- **Agent匹配**: 使用LLM理解策略语义，智能推荐相关工具
- **关键词匹配**: 基于关键词快速匹配工具
- **结果融合**: 取两种方式的并集，最大化覆盖面

### 2. 工具分类管理

支持按类别组织和查询工具：
- 数据获取类
- 筛选类
- 分析类
- 回测类
- 其他工具类

### 3. 工具信息查询

提供工具的详细信息查询功能，包括：
- 工具名称和描述
- 输入输出参数
- 使用示例
- 所属类别

## 核心类: ToolsSelector

### 类说明

```python
class ToolsSelector:
    """
    工具选择器类，提供智能工具选择和管理功能
    
    Attributes:
        tools: 工具列表
        llm_client: LLM客户端实例（用于Agent匹配）
    """
```

### 初始化

```python
from core.mcp.tools_selection import ToolsSelector

# 方式1: 使用默认配置
selector = ToolsSelector()

# 方式2: 自定义LLM客户端
from openai import OpenAI
custom_client = OpenAI(api_key="your_key")
selector = ToolsSelector(llm_client=custom_client)

# 方式3: 自定义工具列表
custom_tools = [...]  # 自定义工具列表
selector = ToolsSelector(tools=custom_tools)
```

### 主要方法

#### 1. select_relevant_tools()

选择与策略描述相关的工具（推荐使用）。

```python
def select_relevant_tools(
    self,
    strategy_description: str,
    use_agent: bool = True,
    use_keywords: bool = True,
    top_k: int = 10
) -> List[Dict]:
    """
    选择相关工具
    
    Args:
        strategy_description: 策略描述文本
        use_agent: 是否使用Agent匹配
        use_keywords: 是否使用关键词匹配
        top_k: 返回的最大工具数量
    
    Returns:
        选中的工具列表
    """
```

**使用示例**：

```python
selector = ToolsSelector()

# 完整匹配（Agent + 关键词）
tools = selector.select_relevant_tools(
    strategy_description="筛选放量突破的股票",
    use_agent=True,
    use_keywords=True
)

# 仅使用Agent匹配
tools = selector.select_relevant_tools(
    strategy_description="筛选放量突破的股票",
    use_agent=True,
    use_keywords=False
)

# 仅使用关键词匹配
tools = selector.select_relevant_tools(
    strategy_description="筛选放量突破的股票",
    use_agent=False,
    use_keywords=True
)
```

#### 2. get_tools_by_category()

按类别获取工具。

```python
def get_tools_by_category(self, category: str) -> List[Dict]:
    """
    按类别获取工具
    
    Args:
        category: 工具类别名称
    
    Returns:
        该类别下的所有工具
    """
```

**使用示例**：

```python
# 获取数据获取类工具
data_tools = selector.get_tools_by_category('数据获取')

# 获取筛选类工具
screen_tools = selector.get_tools_by_category('筛选')
```

#### 3. get_all_tools()

获取所有可用工具。

```python
all_tools = selector.get_all_tools()
print(f"共有 {len(all_tools)} 个工具")
```

#### 4. get_tool_info()

获取特定工具的详细信息。

```python
tool_info = selector.get_tool_info('stock_screener')
if tool_info:
    print(f"工具名称: {tool_info['name']}")
    print(f"工具描述: {tool_info['description']}")
```

## 工具选择流程

### 完整流程图

```
用户策略描述
      |
      v
+------------------+
| ToolsSelector    |
+------------------+
      |
      +---> Agent匹配 -----> Agent选中的工具
      |                            |
      +---> 关键词匹配 --> 关键词选中的工具
                                   |
                                   v
                            取并集 & 去重
                                   |
                                   v
                            返回最终工具列表
```

### Agent匹配流程

1. **构建Prompt**: 将策略描述和工具信息组织成Prompt
2. **调用LLM**: 使用配置的LLM模型进行语义理解
3. **解析结果**: 从LLM返回的JSON中提取工具名称
4. **验证工具**: 确保返回的工具名称在工具列表中存在

### 关键词匹配流程

1. **提取关键词**: 从策略描述中提取关键词
2. **模糊匹配**: 在工具名称、描述、类别中搜索关键词
3. **计算相关度**: 根据匹配次数计算相关度分数
4. **排序返回**: 按相关度排序返回匹配的工具

## 配置说明

### LLM配置

工具选择器使用 `config` 模块中的LLM配置：

```python
from config import StockQueryConfig

api_config = StockQueryConfig.get_api_config()
# api_config包含:
# - api_key: OpenAI API密钥
# - base_url: API基础URL
# - model: 使用的模型名称（默认gpt-4）
```

### 工具配置

工具列表通常从外部传入或从配置文件加载。工具格式示例：

```python
tool_example = {
    'name': 'stock_screener',
    'description': '根据条件筛选股票',
    'category': '筛选',
    'keywords': ['筛选', '过滤', '选股'],
    'input_schema': {...},
    'output_schema': {...}
}
```

## 使用场景

### 场景1: 策略生成时选择工具

```python
# 在策略生成流程中
strategy_desc = "找出最近5日放量且突破20日均线的股票"
selector = ToolsSelector()

# 选择相关工具
tools = selector.select_relevant_tools(strategy_desc)

# 使用选中的工具生成策略代码
for tool in tools:
    print(f"使用工具: {tool['name']}")
    # 生成调用该工具的代码...
```

### 场景2: 工具推荐

```python
# 向用户推荐可用的工具
user_query = "我想分析股票的技术指标"
selector = ToolsSelector()

tools = selector.select_relevant_tools(user_query, top_k=5)

print("推荐的工具:")
for i, tool in enumerate(tools, 1):
    print(f"{i}. {tool['name']}: {tool['description']}")
```

### 场景3: 工具浏览

```python
# 按类别浏览工具
selector = ToolsSelector()

categories = ['数据获取', '筛选', '分析', '回测']
for category in categories:
    tools = selector.get_tools_by_category(category)
    print(f"\n{category}类工具 ({len(tools)}个):")
    for tool in tools:
        print(f"  - {tool['name']}")
```

## 性能优化

### 1. 缓存机制

```python
# 缓存工具列表，避免重复加载
class ToolsSelector:
    _tools_cache = None
    
    def __init__(self, tools=None):
        if tools is None and self._tools_cache is not None:
            self.tools = self._tools_cache
        # ...
```

### 2. 并行匹配

```python
# Agent匹配和关键词匹配可以并行执行
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor() as executor:
    agent_future = executor.submit(self._select_by_agent, ...)
    keyword_future = executor.submit(self._select_by_keywords, ...)
    
    agent_tools = agent_future.result()
    keyword_tools = keyword_future.result()
```

## 错误处理

### Agent匹配失败

```python
try:
    tools = selector.select_relevant_tools(
        strategy_description="...",
        use_agent=True
    )
except Exception as e:
    print(f"Agent匹配失败: {e}")
    # 自动回退到关键词匹配
    tools = selector.select_relevant_tools(
        strategy_description="...",
        use_agent=False,
        use_keywords=True
    )
```

### LLM配置错误

```python
# 检查LLM配置
from config import StockQueryConfig

api_config = StockQueryConfig.get_api_config()
if not api_config.get('api_key'):
    print("警告: 未配置OpenAI API Key，Agent匹配将不可用")
    # 仅使用关键词匹配
```

## 调试技巧

### 1. 查看匹配详情

```python
# 启用详细输出
selector = ToolsSelector()
tools = selector.select_relevant_tools(
    strategy_description="...",
    use_agent=True,
    use_keywords=True
)

# 查看匹配报告
print("Agent匹配的工具:", [t['name'] for t in agent_tools])
print("关键词匹配的工具:", [t['name'] for t in keyword_tools])
print("最终选中的工具:", [t['name'] for t in tools])
```

### 2. 测试单个匹配方式

```python
# 仅测试Agent匹配
agent_tools = selector._select_by_agent("策略描述", top_k=10)

# 仅测试关键词匹配
keyword_tools = selector._select_by_keywords("策略描述", top_k=10)
```

## 扩展开发

### 添加新的匹配方式

```python
class ToolsSelector:
    def _select_by_embedding(self, strategy_description, top_k=10):
        """基于向量相似度的匹配"""
        # 1. 将策略描述转换为向量
        # 2. 计算与工具描述的相似度
        # 3. 返回最相似的top_k个工具
        pass
    
    def select_relevant_tools(self, strategy_description, ...):
        # 整合新的匹配方式
        embedding_tools = self._select_by_embedding(...)
        # ...
```

### 自定义工具格式

```python
# 定义自己的工具格式
custom_tools = [
    {
        'name': 'my_tool',
        'description': '我的自定义工具',
        'category': '自定义',
        # 其他字段...
    }
]

selector = ToolsSelector(tools=custom_tools)
```

## 注意事项

1. **API配额**: Agent匹配会调用LLM API，注意API配额限制
2. **响应时间**: Agent匹配比关键词匹配慢，可根据场景选择
3. **工具质量**: 工具描述的质量直接影响匹配准确度
4. **并发控制**: 大量并发请求时注意LLM API的速率限制

## 未来改进

- [ ] 支持向量相似度匹配
- [ ] 添加工具使用统计和推荐
- [ ] 支持工具依赖关系分析
- [ ] 优化Agent Prompt提高准确度
- [ ] 添加工具版本管理