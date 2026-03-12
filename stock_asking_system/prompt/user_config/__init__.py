#!/usr/bin/env python3
"""
股票问答系统 - 用户配置模块

📖 使用说明：
本模块整合了所有用户可自定义的配置项，按功能拆分为多个子模块：

模块结构：
- query_examples.py    : 预定义查询示例（用户可以修改策略）
- system_role.py       : AI 系统角色设定（一般不需要修改）
- query_format.py      : 用户查询格式要求（一般不需要修改）
- screening_prompt.py  : 筛选逻辑系统 Prompt 模板（一般不需要修改）

✅ 用户可以自由修改 query_examples.py 中的策略配置
⚠️ 其他配置文件请在了解作用后再进行修改
"""

from .query_examples import QUERY_EXAMPLES
from .system_role import SYSTEM_ROLE, SKILL_CONTENT
from .query_format import USER_QUERY_FORMAT
from .screening_prompt import SCREENING_SYSTEM_PROMPT

__all__ = [
    'QUERY_EXAMPLES',
    'SYSTEM_ROLE',
    'USER_QUERY_FORMAT',
    'SCREENING_SYSTEM_PROMPT',
    'SKILL_CONTENT',
]
