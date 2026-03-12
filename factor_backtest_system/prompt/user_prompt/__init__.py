#!/usr/bin/env python3
"""
因子回测系统 - 用户配置模块

📖 使用说明：
本模块整合了所有用户可自定义的配置项，按功能拆分为多个子模块：

模块结构：
- strategy_configs.py   : 策略描述和优化建议（用户可以修改策略）
- system_role.py        : AI 系统角色设定（一般不需要修改）
- request_format.py     : 用户请求格式要求（一般不需要修改）
- fallback_skill.py     : Fallback 技能文档（一般不需要修改）

✅ 用户可以自由修改 strategy_configs.py 中的策略配置
⚠️ 其他配置文件请在了解作用后再进行修改
"""

from .strategy_configs import STRATEGY_CONFIGS, OPTIMIZATION_SUGGESTIONS
from .system_role import SYSTEM_ROLE
from .request_format import USER_REQUEST_FORMAT
from .fallback_skill import FALLBACK_SKILL_CONTENT

__all__ = [
    'STRATEGY_CONFIGS',
    'OPTIMIZATION_SUGGESTIONS',
    'SYSTEM_ROLE',
    'USER_REQUEST_FORMAT',
    'FALLBACK_SKILL_CONTENT',
]
