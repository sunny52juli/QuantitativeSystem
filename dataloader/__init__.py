#!/usr/bin/env python3
"""
dataloader 模块 - data2parquet 的别名

此模块是 data2parquet 的别名，为了向后兼容保留。
推荐使用 from data2parquet import ... 导入。
"""

# 重新导出 data2parquet 的所有内容
from data2parquet import *
from data2parquet import DataInterface, DataGenerator, DataFetcher, DataSaver, TradeCalendar

# 导出子模块
from data2parquet import data_interface
from data2parquet import trade_calendar

__all__ = [
    'DataGenerator',
    'DataFetcher', 
    'DataSaver',
    'DataInterface',
    'TradeCalendar',
    'data_interface',
    'trade_calendar',
]