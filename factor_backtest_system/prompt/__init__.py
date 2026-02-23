"""
因子回测系统提示词模块

文件结构：
- factor_config.py   : 用户配置文件（策略描述、角色设定等，可自定义修改）
- factor_prompts.py  : 系统模板文件（消息模板、便捷函数，一般不需要修改）
"""

from .factor_prompts import StrategyPrompts, AIFactorMinerPrompts
from .factor_prompts import (
    get_system_prompt,
    get_user_prompt,
    get_message,
    get_optimization_suggestion
)

# 兼容性别名
FactorBacktestPrompts = AIFactorMinerPrompts

__all__ = [
    'StrategyPrompts',
    'AIFactorMinerPrompts',
    'FactorBacktestPrompts',
    'get_system_prompt',
    'get_user_prompt',
    'get_message',
    'get_optimization_suggestion',
]
