#!/usr/bin/env python3
"""
Pipeline 模块 - 工作流入口

展示如何使用 Agent 和 Tools 完成股票查询的完整工作流：
1. 数据加载
2. 工具选择
3. LLM Agent 生成筛选逻辑
4. 生成筛选脚本到 asking_scripts 目录
5. 工具执行筛选
6. 计算持有期收益率
7. 结果展示

包含:
- StockQueryPipeline: 股票查询完整工作流
"""

from .stock_query_pipeline import (
    StockQueryPipeline,
    create_stock_query_pipeline,
    query_stocks,
    query_stocks_with_returns,
    backtest_asking_scripts,
)

__all__ = [
    'StockQueryPipeline',
    'create_stock_query_pipeline',
    'query_stocks',
    'query_stocks_with_returns',
    'backtest_asking_scripts',
]

def __getattr__(name):
    """延迟导入，只在真正使用时才导入相关模块"""
    if name in __all__:
        from stock_asking_system.pipeline.stock_query_pipeline import (
            StockQueryPipeline, create_stock_query_pipeline, query_stocks,
            query_stocks_with_returns, backtest_asking_scripts,
        )
        return locals()[name]
    raise AttributeError(f"module 'stock_asking_system.pipeline' has no attribute '{name}'")