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

# 从 agent 模块导入 LLM Agent 相关
from .agent import AIFactorMiner, FactorMiningAgent

# 从 tools 模块导入工具相关
from .tools import ToolExecutor, sanitize_filename, to_class_name

# 从 backtest 模块导入脚本加载相关
from .backtest.factor_loader import FactorScriptLoader, FactorScriptExecutor

# 从 datamodule 模块导入数据加载相关
from datamodule import FactorDataLoader

# 从 backtest 模块导入回测框架
from .backtest.factor_backtest import FactorMiningFramework

# 从 generators 模块导入脚本生成器
from .generators.factor_script_generator import FactorScriptGenerator

# 从 pipeline 模块导入便捷函数
from .pipeline.factor_mining_pipeline import (
    StrategyTemplates,
    create_factor_miner,
    get_available_tools,
    select_tools_for_strategy,
    generate_recent_strong_stock_factors,
    generate_optimization_suggestions,
)

# 从 backtest 模块导入回测入口
from .backtest.run_scrip_backtest import backtest_factor_scripts

__all__ = [
    # 回测引擎
    'FactorMiningFramework',
    
    # Agent 模块 - LLM 相关
    'AIFactorMiner',
    'ToolExecutor',
    'FactorMiningAgent',
    
    # Datamodule 模块 - 数据加载相关
    'FactorScriptLoader',
    'FactorScriptExecutor',
    'FactorDataLoader',
    
    # 脚本生成器
    'FactorScriptGenerator',
    
    # 便捷函数
    'StrategyTemplates',
    'create_factor_miner',
    'get_available_tools',
    'select_tools_for_strategy',
    'generate_recent_strong_stock_factors',
    'generate_optimization_suggestions',
    'backtest_factor_scripts',
]
