"""
MCP 工具模块 - 包含因子工具、表达式工具、工具选择功能和验证器
"""

from .factor_tools_mcp import FactorToolsMCP
from .tools_selection import select_relevant_tools, categorize_tools, load_mcp_tools
from .expression_tools import (
    ExpressionParser,
    NamespaceBuilder,
    ExpressionEvaluator,
    parse_expression,
    infer_variable,
    build_namespace,
    evaluate_expression
)
from .utils import (
    DataAdapter,
    ExpressionHelpers,
    get_groupby_key,
    apply_grouped_operation,
    ensure_series_with_index
)
from .exceptions import (
    MCPError,
    ToolExecutionError,
    ToolNotFoundError,
    ExpressionEvalError,
    ExpressionSyntaxError,
    InvalidFieldError,
    DataFormatError,
    SkillValidationError,
    ErrorResponseBuilder,
    handle_tool_errors,
    validate_expression
)
from .mcp_config import (
    MCPConfig,
    get_tools_by_category,
    get_tool_category,
    analyze_strategy_keywords,
    get_relevant_tools_for_strategy
)
from .skill_validator import (
    SkillValidator,
    ValidationResult,
    validate_factor
)

# 简化别名
FactorTools = FactorToolsMCP

__all__ = [
    # 核心类
    'FactorToolsMCP',
    'ExpressionParser',
    'NamespaceBuilder',
    'ExpressionEvaluator',
    
    # 工具函数
    'select_relevant_tools',
    'categorize_tools',
    'load_mcp_tools',
    'parse_expression',
    'infer_variable',
    'build_namespace',
    'evaluate_expression',
    
    # 数据适配器
    'DataAdapter',
    'ExpressionHelpers',
    'get_groupby_key',
    'apply_grouped_operation',
    'ensure_series_with_index',
    
    # 异常处理
    'MCPError',
    'ToolExecutionError',
    'ToolNotFoundError',
    'ExpressionEvalError',
    'ExpressionSyntaxError',
    'InvalidFieldError',
    'DataFormatError',
    'SkillValidationError',
    'ErrorResponseBuilder',
    'handle_tool_errors',
    'validate_expression',
    
    # 配置管理
    'MCPConfig',
    'get_tools_by_category',
    'get_tool_category',
    'analyze_strategy_keywords',
    'get_relevant_tools_for_strategy',
    
    # 验证器
    'SkillValidator',
    'ValidationResult',
    'validate_factor',
    
    # 别名
    'FactorTools'
]
