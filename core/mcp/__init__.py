"""
MCP工具模块 - 包含因子工具、表达式工具和工具选择功能
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

# 简化别名
FactorTools = FactorToolsMCP

__all__ = [
    'FactorToolsMCP',
    'select_relevant_tools',
    'categorize_tools',
    'load_mcp_tools',
    'FactorTools',
    'ExpressionParser',
    'NamespaceBuilder',
    'ExpressionEvaluator',
    'parse_expression',
    'infer_variable',
    'build_namespace',
    'evaluate_expression'
]
