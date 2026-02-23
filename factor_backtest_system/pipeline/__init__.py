"""
因子挖掘流程管道模块 - 调用入口

此模块负责协调和调用各模块：
- agent/ - LLM Agent 相关（因子生成）
- datamodule/ - 数据加载和清洗
- generators/ - 因子脚本生成器
- backtest/ - 因子回测引擎

导出：
- FactorMiningAgent: 因子挖掘代理（从 agent 模块）
- 便捷函数：create_factor_miner, get_available_tools 等
- StrategyTemplates: 预定义策略
"""

from .factor_mining_pipeline import (
    FactorMiningAgent,
    AIFactorMiner,
    ToolExecutor,
    FactorDataLoader,
    create_factor_miner,
    get_available_tools,
    select_tools_for_strategy,
    generate_recent_strong_stock_factors,
    generate_optimization_suggestions,
    StrategyTemplates,
)

__all__ = [
    # Agent 相关
    'FactorMiningAgent',
    'AIFactorMiner',
    'ToolExecutor',
    
    # Datamodule 相关
    'FactorScriptLoader',
    'FactorScriptExecutor',
    'FactorDataLoader',
    
    # 便捷函数
    'create_factor_miner',
    'get_available_tools',
    'select_tools_for_strategy',
    'generate_recent_strong_stock_factors',
    'generate_optimization_suggestions',
    
    # 预定义策略
    'StrategyTemplates',
]
