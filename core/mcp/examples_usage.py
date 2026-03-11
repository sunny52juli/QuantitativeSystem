"""
MCP 工具模块 - 使用示例和最佳实践

本文件展示如何使用重构后的 MCP 工具模块的各项功能
"""

import pandas as pd
import numpy as np

# ==================== 1. 使用 DataAdapter 统一处理数据格式 ====================

from core.mcp import DataAdapter

def example_data_adapter():
    """示例：使用 DataAdapter 智能适配不同数据格式"""
    
    # 创建双索引数据（多股票时间序列）
    dates = pd.date_range('2024-01-01', periods=5)
    stocks = ['000001.SZ', '000002.SZ']
    index = pd.MultiIndex.from_product([dates, stocks], names=['trade_date', 'ts_code'])
    data = pd.DataFrame({
        'close': np.random.randn(10).cumsum() + 10,
        'vol': np.random.randint(1000, 5000, 10)
    }, index=index)
    
    # 获取分组键
    ts_code_key = DataAdapter.get_groupby_key(data, 'ts_code')
    
    # 应用分组操作（自动适配双索引）
    close_data = data['close']
    result = DataAdapter.apply_grouped_operation(
        data, 
        close_data, 
        lambda x: x.rolling(3).mean(),
        group_by_stock=True
    )
    
    print("双索引数据移动平均:")
    print(result)
    
    # 单索引数据也能自动适配
    single_stock_data = data.xs('000001.SZ', level='ts_code')
    result_single = DataAdapter.apply_grouped_operation(
        single_stock_data,
        single_stock_data['close'],
        lambda x: x.rolling(3).mean(),
        group_by_stock=False
    )
    
    print("\n单股票数据移动平均:")
    print(result_single)


# ==================== 2. 使用统一的异常处理 ====================

from core.mcp import (
    ToolExecutionError, 
    ExpressionEvalError, 
    handle_tool_errors,
    validate_expression
)

@handle_tool_errors
def safe_rolling_mean(data, window):
    """安全的移动平均计算（带错误处理装饰器）"""
    return data.rolling(window).mean()

@validate_expression
def safe_eval(expr, namespace):
    """安全的表达式评估（带验证装饰器）"""
    return eval(expr, {"__builtins__": {}}, namespace)

def example_error_handling():
    """示例：使用统一的异常处理"""
    
    try:
        # 模拟工具执行失败
        data = pd.Series([1, 2, 3])
        result = safe_rolling_mean(data, 10)  # 窗口过大
    except ToolExecutionError as e:
        print(f"工具执行失败：{e}")
        print(f"错误码：{e.code}")
        print(f"工具名称：{e.data.get('tool_name')}")
    
    try:
        # 模拟表达式评估失败
        result = safe_eval("invalid_expr", {})
    except ExpressionEvalError as e:
        print(f"\n表达式评估失败：{e}")
        print(f"表达式：{e.data.get('expression')}")


# ==================== 3. 使用配置管理工具 ====================

from core.mcp import MCPConfig

def example_config_management():
    """示例：使用配置管理工具"""
    
    # 获取某类别的所有工具
    math_tools = MCPConfig.get_tools_by_category('math')
    print(f"数学工具：{math_tools}")
    
    # 检查工具所属类别
    category = MCPConfig.get_tool_category('rsi')
    print(f"\nRSI 属于：{category} 类别")
    
    # 分析策略关键词
    strategy = "基于成交量和动量的突破策略"
    analysis = MCPConfig.analyze_strategy(strategy)
    print(f"\n策略：{strategy}")
    print(f"相关类别：{analysis['categories']}")
    print(f"匹配关键词：{analysis['keywords']}")
    
    # 获取相关工具列表
    relevant_tools = MCPConfig.get_relevant_tools_for_strategy(strategy)
    print(f"\n相关工具 ({len(relevant_tools)}个):")
    print(', '.join(relevant_tools[:10]))
    
    # 验证工具名称
    is_valid = MCPConfig.validate_tool_name('rsi')
    print(f"\n'rsi' 是有效工具：{is_valid}")
    
    # 工具建议
    suggestions = MCPConfig.get_tool_suggestions('roll')
    print(f"\n包含'roll'的工具：{suggestions}")


# ==================== 4. 使用 SkillValidator 验证因子 ====================

from core.mcp import SkillValidator, ValidationResult

def example_skill_validator():
    """示例：使用技能验证器验证因子定义"""
    
    # 假设的 SKILL.md 内容（实际使用时应该加载完整内容）
    skill_content = """
    # Factor Mining Skill
    
    ## 可用数据字段
    - 收盘价、开盘价、最高价、最低价
    - 成交量、成交额
    """
    
    # 可用的工具列表
    available_tools = [
        {'name': 'rolling_mean', 'description': '移动平均'},
        {'name': 'rsi', 'description': 'RSI 指标'},
        {'name': 'zscore_normalize', 'description': 'Z-score 标准化'},
    ]
    
    validator = SkillValidator(skill_content, available_tools)
    
    # 有效的因子定义
    valid_factor = {
        'name': '动量因子',
        'rationale': '基于 5 日收益率的动量策略',
        'tools': [
            {
                'tool': 'pct_change',
                'params': {'values': '收盘价', 'periods': 5},
                'var': 'momentum_5d'
            }
        ],
        'expression': 'momentum_5d'
    }
    
    result = validator.validate_factor_definition(valid_factor)
    print(f"有效因子验证结果:")
    print(f"  是否通过：{result.is_valid}")
    print(f"  错误数：{len(result.errors)}")
    print(f"  警告数：{len(result.warnings)}")
    print(f"  建议数：{len(result.suggestions)}")
    
    # 无效的因子定义（使用了不存在的工具）
    invalid_factor = {
        'name': '无效因子',
        'tools': [
            {
                'tool': 'invalid_tool_xyz',  # 不存在的工具
                'params': {},
                'var': 'temp'
            }
        ],
        'expression': 'temp'
    }
    
    result = validator.validate_factor_definition(invalid_factor)
    print(f"\n无效因子验证结果:")
    print(f"  是否通过：{result.is_valid}")
    if result.errors:
        print(f"  错误：{result.errors[0]}")


# ==================== 5. 完整的因子构建流程示例 ====================

from core.mcp import ExpressionParser, NamespaceBuilder, ExpressionEvaluator

def example_complete_factor_workflow():
    """示例：完整的因子构建流程"""
    
    # 创建示例数据
    dates = pd.date_range('2024-01-01', periods=60)
    stocks = ['000001.SZ']
    index = pd.MultiIndex.from_product([dates, stocks], names=['trade_date', 'ts_code'])
    data = pd.DataFrame({
        'close': np.random.randn(60).cumsum() + 100,
        'vol': np.random.randint(1000, 5000, 60),
        'high': np.random.randn(60).cumsum() + 102,
        'low': np.random.randn(60).cumsum() + 98
    }, index=index)
    
    # 步骤 1: 解析表达式
    raw_expr = "20 日平均 vol / vol"
    parsed_expr = ExpressionParser.parse_expression(raw_expr)
    print(f"原始表达式：{raw_expr}")
    print(f"解析后：{parsed_expr}")
    
    # 步骤 2: 推断变量
    var_name = 'vol_avg_20d'
    inferred = ExpressionParser.infer_variable(var_name, data)
    if inferred is not None:
        print(f"\n推断变量 {var_name}:")
        print(f"  均值：{inferred.mean():.2f}")
        print(f"  标准差：{inferred.std():.2f}")
    
    # 步骤 3: 构建命名空间
    namespace = NamespaceBuilder.build_namespace(data)
    print(f"\n命名空间包含 {len(namespace)} 个变量/函数")
    print(f"可用函数示例：{[k for k in namespace.keys() if callable(namespace[k])][:5]}")
    
    # 步骤 4: 评估表达式
    evaluator = ExpressionEvaluator(data)
    result = evaluator.evaluate("(close - rolling_mean(close, 20)) / rolling_std(close, 20)")
    print(f"\n表达式评估结果:")
    print(f"  长度：{len(result)}")
    print(f"  均值：{result.mean():.4f}")
    print(f"  标准差：{result.std():.4f}")


# ==================== 6. 最佳实践建议 ====================

def best_practices():
    """
    最佳实践总结
    
   1. 使用 DataAdapter 处理数据格式适配
       - 不要重复编写 _get_groupby_key 等函数
       - 让 DataAdapter 自动处理三种数据格式
    
    2. 使用统一的异常处理
       - 工具函数使用 @handle_tool_errors 装饰器
       - 表达式函数使用 @validate_expression 装饰器
       - 抛出特定的异常类型（ToolExecutionError 等）
    
    3. 使用 MCPConfig 管理配置
       - 不要硬编码工具分类
       - 使用 MCPConfig.get_tools_by_category()
       - 策略分析使用 analyze_strategy()
    
    4. 在 AI 生成因子后使用 SkillValidator 验证
       - 检查字段是否在允许列表中
       - 检查工具是否合法
       - 检查表达式复杂度
    
    5. 代码复用原则
       - 优先使用 utils.py 中的公共函数
       - 避免重复实现相同功能
       - 保持代码 DRY (Don't Repeat Yourself)
    """
    pass


if __name__ == "__main__":
    print("=" * 80)
    print("MCP 工具模块使用示例")
    print("=" * 80)
    
    print("\n## 1. DataAdapter 示例")
    print("-" * 80)
    example_data_adapter()
    
    print("\n\n## 2. 异常处理示例")
    print("-" * 80)
    example_error_handling()
    
    print("\n\n## 3. 配置管理示例")
    print("-" * 80)
    example_config_management()
    
    print("\n\n## 4. SkillValidator 示例")
    print("-" * 80)
    example_skill_validator()
    
    print("\n\n## 5. 完整因子构建流程示例")
    print("-" * 80)
    example_complete_factor_workflow()
    
    print("\n\n## 6. 最佳实践")
    print("-" * 80)
    print(best_practices.__doc__)
