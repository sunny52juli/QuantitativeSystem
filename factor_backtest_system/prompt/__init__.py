"""
因子回测系统提示词模块

文件结构：
- user_prompt/            : 用户配置模块（用户可以修改策略）
  - strategy_configs.py   : 策略描述和优化建议
  - system_role.py        : AI 系统角色设定
  - request_format.py     : 用户请求格式要求
  - fallback_skill.py     : Fallback 技能文档
- system_prompts.py     : 系统模板文件（一般不需要修改）
"""

from .system_prompts import StrategyPrompts, AIFactorMinerPrompts, FactorMiningAgentPrompts, MessageTemplates
from .system_prompts import (
    get_strategy_prompt,
    get_system_prompt,
    get_user_prompt,
    get_message,
)

# 兼容性别名
FactorBacktestPrompts = AIFactorMinerPrompts

__all__ = [
    'StrategyPrompts',
    'AIFactorMinerPrompts',
    'FactorMiningAgentPrompts',
    'FactorBacktestPrompts',
    'MessageTemplates',
    'get_strategy_prompt',
    'get_system_prompt',
    'get_user_prompt',
    'get_message',
]
