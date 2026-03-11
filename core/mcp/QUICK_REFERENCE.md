# MCP 工具模块重构 - 快速参考指南

## 📦 新增模块总览

| 模块 | 用途 | 核心功能 |
|------|------|----------|
| `utils.py` | 公共工具函数 | DataAdapter, ExpressionHelpers |
| `exceptions.py` | 异常处理 | 统一异常体系，装饰器 |
| `mcp_config.py` | 配置管理 | MCPConfig 类，工具分类 |
| `skill_validator.py` | 技能验证 | SkillValidator 验证器 |

---

## 🔧 常用 API 速查

### 1. DataAdapter - 数据适配

```python
from core.mcp import DataAdapter

# 获取分组键（自动适配双索引/单索引）
ts_code_key = DataAdapter.get_groupby_key(data, 'ts_code')

# 应用分组操作（智能处理三种数据格式）
result = DataAdapter.apply_grouped_operation(
    data, 
    field_data, 
    lambda x: x.rolling(20).mean(),
    group_by_stock=True
)

# 确保 Series 索引对齐
series = DataAdapter.ensure_series_with_index(data, column_or_series)
```

### 2. 异常处理 - 装饰器

```python
from core.mcp import handle_tool_errors, validate_expression

# 工具函数自动错误处理
@handle_tool_errors
def my_tool(data, params):
    return data[params['field']].rolling(params['window']).mean()

# 表达式验证
@validate_expression
def evaluate(expr, namespace):
    return eval(expr, {"__builtins__": {}}, namespace)
```

### 3. 异常类型 - 捕获特定错误

```python
from core.mcp import (
    ToolExecutionError,      # 工具执行失败
    ExpressionEvalError,     # 表达式评估失败
    InvalidFieldError,       # 无效字段
    DataFormatError,         # 数据格式错误
    SkillValidationError     # 技能验证失败
)

try:
    result = my_tool(data, params)
except ToolExecutionError as e:
    print(f"工具 {e.data['tool_name']} 失败")
    print(f"错误码：{e.code}")
    print(f"消息：{e.message}")
```

### 4. 配置管理 - 工具查询

```python
from core.mcp import MCPConfig

# 获取某类别的所有工具
math_tools = MCPConfig.get_tools_by_category('math')

# 检查工具所属类别
category = MCPConfig.get_tool_category('rsi')  # 返回 'technical'

# 分析策略关键词
strategy = "基于成交量和动量的突破策略"
analysis = MCPConfig.analyze_strategy(strategy)
# 返回：{'categories': [...], 'keywords': [...]}

# 获取相关工具
relevant_tools = MCPConfig.get_relevant_tools_for_strategy(strategy)

# 验证工具名称
is_valid = MCPConfig.validate_tool_name('rsi')  # True

# 获取工具建议
suggestions = MCPConfig.get_tool_suggestions('roll')  
# 返回包含 'roll' 的工具列表
```

### 5. 技能验证器 - 因子验证

```python
from core.mcp import SkillValidator

# 创建验证器
validator = SkillValidator(SKILL_CONTENT, available_tools)

# 验证因子定义
factor_def = {
    'name': '动量因子',
    'rationale': '基于 5 日收益率',
    'tools': [
        {'tool': 'pct_change', 'params': {'values': 'close', 'periods': 5}, 'var': 'mom'}
    ],
    'expression': 'mom'
}

result = validator.validate_factor_definition(factor_def)

# 检查结果
if not result.is_valid:
    for error in result.errors:
        print(f"错误：{error}")
    
# 访问验证结果属性
print(f"错误数：{len(result.errors)}")
print(f"警告数：{len(result.warnings)}")
print(f"建议数：{len(result.suggestions)}")
```

---

## 🎯 典型使用场景

### 场景 1: 编写新工具函数

```python
from core.mcp import handle_tool_errors, ToolExecutionError

@handle_tool_errors
def custom_indicator(data, params):
    """自定义指标"""
    field = params.get('field', 'close')
    window = params.get('window', 20)
    
    # 使用 DataAdapter 确保索引对齐
    field_data = DataAdapter.ensure_series_with_index(data, data[field])
    
    # 应用分组操作（自动适配数据格式）
    result = DataAdapter.apply_grouped_operation(
        data, 
        field_data, 
        lambda x: x.rolling(window).mean()
    )
    
    return result

# 调用时自动错误处理
try:
    result = custom_indicator(data, {'field': 'close', 'window': 20})
except ToolExecutionError as e:
    print(f"工具执行失败：{e}")
```

### 场景 2: AI 生成因子后验证

```python
from core.mcp import SkillValidator

# 在 AI 生成因子后
generated_factor = ai_generate_factor(strategy)

# 创建验证器
validator = SkillValidator(SKILL_CONTENT, all_available_tools)

# 验证
result = validator.validate_factor_definition(generated_factor)

if result.is_valid:
    print("✅ 因子通过验证")
    # 继续后续流程
else:
    print("❌ 因子未通过验证")
    for error in result.errors:
        print(f"  - {error}")
    
    # 可选：显示警告和建议
    for warning in result.warnings:
        print(f"  ⚠️ {warning}")
    
    for suggestion in result.suggestions:
        print(f"  💡 {suggestion}")
```

### 场景 3: 策略分析工具推荐

```python
from core.mcp import MCPConfig

# 用户输入策略描述
user_strategy = "我想做一个放量突破均线的动量策略"

# 分析策略
analysis = MCPConfig.analyze_strategy(user_strategy)

print(f"识别到的关键词：{analysis['keywords']}")
print(f"相关工具类别：{analysis['categories']}")

# 获取相关工具
tools = MCPConfig.get_relevant_tools_for_strategy(user_strategy)

print(f"\n推荐工具 ({len(tools)}个):")
for tool in sorted(tools):
    category = MCPConfig.get_tool_category(tool)
    print(f"  [{category}] {tool}")
```

### 场景 4: 表达式安全检查

```python
from core.mcp import ExpressionHelpers

# 检查是否是表达式
is_expr = ExpressionHelpers.is_expression("close + vol")  # True
is_expr = ExpressionHelpers.is_expression("close")  # False

# 构建命名空间
namespace = ExpressionHelpers.build_namespace(
    data, 
    computed_vars={'var1': series1},
    extra_functions={'custom_func': my_func}
)

# 安全计算表达式
result = ExpressionHelpers.eval_expression(data, "var1 / close", {'var1': series1})
```

---

## ⚡ 便捷函数速查

### 从 utils.py 导入

```python
from core.mcp import (
    get_groupby_key,              # 获取分组键
    apply_grouped_operation,      # 应用分组操作
    ensure_series_with_index      # 确保 Series 索引对齐
)
```

### 从 mcp_config.py 导入

```python
from core.mcp import (
    get_tools_by_category,           # 获取类别工具
    get_tool_category,               # 获取工具类别
    analyze_strategy_keywords,       # 分析策略关键词
    get_relevant_tools_for_strategy  # 获取策略相关工具
)
```

### 从 skill_validator.py 导入

```python
from core.mcp import (
    validate_factor  # 便捷验证因子
)

# 使用
result = validate_factor(factor_def, SKILL_CONTENT, available_tools)
```

---

## 🛡️ 错误码参考

| 错误码范围 | 类型 | 示例 |
|-----------|------|------|
| -32000 ~ -32099 | 通用错误 | INTERNAL_ERROR, PARSE_ERROR |
| -32100 ~ -32199 | 工具执行错误 | TOOL_NOT_FOUND, TOOL_EXECUTION_FAILED |
| -32200 ~ -32299 | 表达式错误 | EXPRESSION_SYNTAX_ERROR, EXPRESSION_EVAL_FAILED |
| -32300 ~ -32399 | 数据错误 | DATA_NOT_FOUND, DATA_FORMAT_ERROR |
| -32400 ~ -32499 | 技能验证错误 | SKILL_VALIDATION_FAILED, SKILL_INVALID_FIELD |

完整列表见 `exceptions.ErrorCodes` 类。

---

## 📝 迁移指南

### 旧代码 → 新代码

**之前:**
```python
# 重复实现 _get_groupby_key
def _get_groupby_key(data, key):
    if isinstance(data.index, pd.MultiIndex):
        ...

# 手动错误处理
try:
    result = complex_operation(data)
except Exception as e:
    print(f"失败：{e}")
    raise
```

**现在:**
```python
from core.mcp import DataAdapter, handle_tool_errors

@handle_tool_errors
def my_operation(data, params):
    ts_code_key = DataAdapter.get_groupby_key(data, 'ts_code')
    ...
```

---

## 💡 最佳实践 Tips

1. **始终使用 DataAdapter**
   - 不要自己实现 `_get_groupby_key`
   - 让 DataAdapter 自动处理数据格式

2. **使用装饰器处理错误**
   - `@handle_tool_errors` 用于工具函数
   - `@validate_expression` 用于表达式函数

3. **优先使用配置管理**
   - 不要硬编码工具分类
   - 使用 `MCPConfig` 查询配置

4. **AI 生成后必须验证**
   - 使用 `SkillValidator` 验证因子
   - 检查字段、工具、表达式

5. **查看示例代码**
   - 参考 `examples_usage.py` 中的完整示例
   - 运行示例了解最佳实践

---

## 🔍 调试技巧

### 查看详细错误信息

```python
from core.mcp import ErrorResponseBuilder

try:
    result = my_function()
except Exception as e:
    error_response = ErrorResponseBuilder.build_error(e, request_id=123)
    print(error_response)
    # 输出完整的 JSON-RPC 错误响应
```

### 验证配置正确性

```python
from core.mcp import MCPConfig

# 列出所有工具类别
for category in MCPConfig.TOOL_CATEGORIES.keys():
    tools = MCPConfig.get_tools_by_category(category)
    print(f"{category}: {len(tools)} 个工具")
```

---

## 📚 进一步阅读

- `REFACTOR_SUMMARY.txt` - 详细的重构总结
- `examples_usage.py` - 完整使用示例
- `SKILL.md` - 技能文档（约束规范）

---

**版本**: v1.0 (重构版)  
**更新日期**: 2026-03-10  
**维护者**: QuantitativeSystem Team
