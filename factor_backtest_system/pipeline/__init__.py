"""
因子挖掘流程管道模块 - 调用入口

此模块负责协调整个因子挖掘流程：
- 创建和管理 FactorMiningAgent
- 协调数据加载、因子生成、回测等流程
- 提供便捷函数和预定义策略
"""

from .factor_mining_pipeline import (
    FactorMiningAgent,
    AIFactorMiner,
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
    
    # Datamodule 相关
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
