"""
股票问答系统提示词模块

文件结构：
- asking_config.py   : 用户配置文件（查询示例、角色设定等，可自定义修改）
- asking_prompts.py  : 系统模板文件（消息模板、便捷函数，一般不需要修改）
- screening_system.txt : 筛选逻辑系统 Prompt 模板
"""

from .asking_prompts import StockQueryPrompts

__all__ = [
    'StockQueryPrompts',
]
