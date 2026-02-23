"""
配置模块 - 包含系统配置、技能加载和提示词模板
"""

from config.api import APIConfig
from config.data_path import DataConfig
from config.tool_config import ToolConfig, tool_categories, strategy_keywords
from config.stock_pool_config import StockPoolConfig
from config.stock_query_config import StockQueryConfig
from config.factor_backtest_config import FactorBacktestConfig
from core.skill.skill_loader import SkillLoader

# 简化别名
SkillManager = SkillLoader

__all__ = [
    # 公共配置
    'APIConfig',
    'DataConfig',
    'ToolConfig',
    'StockPoolConfig',
    'tool_categories',
    'strategy_keywords',
    
    # 系统专属配置
    'StockQueryConfig',
    'FactorBacktestConfig',
    
    # 其他
    'SkillLoader',
    'SkillManager',
]