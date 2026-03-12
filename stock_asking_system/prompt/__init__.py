"""
股票问答系统提示词模块

📁 文件结构：
- user_config.py          : 用户配置文件（策略、查询示例等，用户可以修改）
- system_prompts.py       : 系统模板文件（消息模板、类封装，一般不需要修改）

📖 使用说明：
1. 如需修改策略、查询示例等，请编辑 user_config.py
2. system_prompts.py 提供统一的接口 StockQueryPrompts
3. 导入方式：from stock_asking_system.prompt import StockQueryPrompts
"""

from .system_prompts import StockQueryPrompts

__all__ = [
    'StockQueryPrompts',
]
