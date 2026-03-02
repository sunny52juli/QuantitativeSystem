"""
因子回测系统 - 基于Agent的因子挖掘和回测

核心模块：
- agent/ - LLM Agent 相关（因子生成、挖掘代理）
- datamodule/ - 数据加载和清洗（脚本加载器、数据加载器）
- backtest/ - 因子回测引擎
- generators/ - 因子脚本生成器
- pipeline/ - 因子挖掘流程管道（调用入口）
- prompt/ - 配置文件
- factor_scripts/ - 生成的因子脚本

工作流程：
1. 根据 prompt 生成因子定义
2. 将因子定义生成为脚本文件，保存到 factor_scripts 目录
3. 使用 FactorScriptExecutor 执行因子计算和回测
"""

# 从核心模块导入主要功能
from .agent import FactorMiningAgent
from .tools import ToolExecutor, sanitize_filename, to_class_name
from .backtest.factor_loader import FactorScriptLoader, FactorScriptExecutor
from .backtest.factor_backtest import FactorMiningFramework
from .generators.factor_script_generator import FactorScriptGenerator
from .pipeline.factor_mining_pipeline import (
    StrategyTemplates,
    create_factor_miner,
    get_available_tools,
    select_tools_for_strategy,
    generate_recent_strong_stock_factors,
    generate_optimization_suggestions,
)

# 从外部模块导入数据加载器
from datamodule import FactorDataLoader

__all__ = [
    # 核心功能
    'FactorMiningFramework',
    'FactorMiningAgent',
    'ToolExecutor',
    
    # 数据处理
    'FactorScriptLoader',
    'FactorScriptExecutor',
    'FactorDataLoader',
    
    # 脚本生成
    'FactorScriptGenerator',
    
    # 便捷函数
    'StrategyTemplates',
    'create_factor_miner',
    'get_available_tools',
    'select_tools_for_strategy',
    'generate_recent_strong_stock_factors',
    'generate_optimization_suggestions',
]
