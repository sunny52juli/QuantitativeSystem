#!/usr/bin/env python3
"""
股票查询系统 (Stock Asking System)

基于自然语言的智能股票筛选系统

模块结构：
├── pipeline/               # 工作流入口（展示完整流程）
│   └── stock_query_pipeline.py
├── agent/                  # LLM Agent（智能处理）
│   ├── screening_logic_agent.py  # 筛选逻辑生成
│   └── stock_query_agent.py      # 兼容层
├── generators/             # 脚本生成器
│   └── asking_script_generator.py  # 筛选逻辑脚本生成
├── asking_scripts/         # 筛选脚本目录（仅存放 Agent 生成的脚本）
├── backtest/               # 独立回测模块
│   ├── asking_script_loader.py   # 脚本加载器
│   └── run_script_backtest.py    # 筛选脚本回测引擎
├── tools/                  # 工具模块（执行层）
│   └── stock_screener.py         # 股票筛选器
├── datamodule/             # 数据模块（数据加载与管理）
│   └── stock_data_loader.py      # 股票数据加载器
├── prompt/                 # 配置模块
│   ├── asking_prompts.py
│   └── stock_query_config.py
└── run_stock_query.py      # 运行入口

使用示例：
    # 方式1：简单查询（仅筛选）
    from stock_asking_system.pipeline import StockQueryPipeline
    pipeline = StockQueryPipeline()
    results = pipeline.query("通信设备行业放量上涨的股票")
    
    # 方式2：完整流程（生成脚本 + 筛选 + 计算收益率）
    result = pipeline.run_complete_pipeline("通信设备行业放量上涨的股票")
    
    # 方式3：独立回测已有筛选脚本
    from stock_asking_system.backtest import backtest_asking_scripts
    result = backtest_asking_scripts()
    
    # 方式4：使用回测引擎
    from stock_asking_system.backtest import AskingScriptBacktester
    backtester = AskingScriptBacktester()
    result = backtester.backtest_all()
"""

__all__ = [
    # Pipeline（工作流入口）
    'StockQueryPipeline',
    'create_stock_query_pipeline',
    'query_stocks',
    'query_stocks_with_returns',
    'backtest_asking_scripts',
    
    # Agent（LLM 相关）
    'ScreeningLogicAgent',
    'StockQueryAgent',
    'create_stock_query_agent',
    
    # Generators（脚本生成）
    'AskingScriptGenerator',
    
    # 脚本加载器
    'AskingScriptLoader',
    
    # Backtest（独立回测）
    'AskingScriptBacktester',
    
    # Tools（执行层）
    'StockScreener',
    
    # DataModule（数据模块）
    'StockDataLoader',
    'load_market_data',
    'get_available_industries',
]


def __getattr__(name):
    """延迟导入，只在真正使用时才导入相关模块"""
    # Pipeline
    if name in ('StockQueryPipeline', 'create_stock_query_pipeline', 'query_stocks',
                'query_stocks_with_returns', 'backtest_asking_scripts'):
        from stock_asking_system.pipeline.stock_query_pipeline import (
            StockQueryPipeline, create_stock_query_pipeline, query_stocks,
            query_stocks_with_returns, backtest_asking_scripts,
        )
        return locals()[name]
    
    # Agent
    elif name == 'ScreeningLogicAgent':
        from stock_asking_system.agent.screening_logic_agent import ScreeningLogicAgent
        return ScreeningLogicAgent
    
    elif name in ('StockQueryAgent', 'create_stock_query_agent'):
        from stock_asking_system.agent.stock_query_agent import (
            StockQueryAgent, create_stock_query_agent
        )
        return locals()[name]
    
    # Generators
    elif name == 'AskingScriptGenerator':
        from stock_asking_system.generators.asking_script_generator import AskingScriptGenerator
        return AskingScriptGenerator
    
    # 脚本加载器
    elif name == 'AskingScriptLoader':
        from stock_asking_system.backtest.asking_script_loader import AskingScriptLoader
        return AskingScriptLoader
    
    # Backtest
    elif name == 'AskingScriptBacktester':
        from stock_asking_system.backtest.run_script_backtest import AskingScriptBacktester
        return AskingScriptBacktester
    
    # Tools
    elif name == 'StockScreener':
        from stock_asking_system.tools.stock_screener import StockScreener
        return StockScreener
    
    # DataModule
    elif name == 'StockDataLoader':
        from datamodule.stock_data_loader import StockDataLoader
        return StockDataLoader
    
    elif name in ('load_market_data', 'get_available_industries'):
        from datamodule.stock_data_loader import (
            load_market_data, get_available_industries
        )
        return locals()[name]
    
    raise AttributeError(f"module 'stock_asking_system' has no attribute '{name}'")
