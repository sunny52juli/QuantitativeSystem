"""
数据模块 - 量化系统数据层

模块结构：
- data_generator.py: 数据生成入口（主入口）
- data_fetcher.py: 数据源接口封装
- data_saver.py: 数据保存器
- data_interface.py: 数据读取接口
- trade_calendar.py: 交易日历工具
- stock_utils.py: 股票工具函数

使用示例：
    from data2parquet import DataGenerator
    
    generator = DataGenerator(token="your_token")
    generator.generate_market_data("20260212")
"""

from .data_generator import DataGenerator
from .data_fetcher import DataFetcher
from .data_saver import DataSaver
from .data_interface import DataInterface
from .trade_calendar import TradeCalendar
from .stock_utils import normalize_stock_code, parse_stock_code, get_market_from_code

__all__ = [
    'DataGenerator',
    'DataFetcher',
    'DataSaver',
    'DataInterface',
    'TradeCalendar',
    'normalize_stock_code',
    'parse_stock_code',
    'get_market_from_code',
]
