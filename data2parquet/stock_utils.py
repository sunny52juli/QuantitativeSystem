"""
股票工具函数模块
提供股票代码标准化等通用工具函数
"""

import logging

logger = logging.getLogger(__name__)


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码
    
    Args:
        code: 股票代码（可以是6位数字或带后缀的完整代码）
        
    Returns:
        标准化后的股票代码（如 '600000.SH'）
        
    Examples:
        >>> normalize_stock_code('600000')
        '600000.SH'
        >>> normalize_stock_code('000001')
        '000001.SZ'
        >>> normalize_stock_code('600000.SH')
        '600000.SH'
    """
    if '.' in code:
        return code
    
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith('0') or code.startswith('3'):
        return f"{code}.SZ"
    elif code.startswith('8') or code.startswith('4'):
        return f"{code}.BJ"
    else:
        return f"{code}.SH"


def parse_stock_code(ts_code: str) -> tuple:
    """
    解析股票代码
    
    Args:
        ts_code: 完整股票代码（如 '600000.SH'）
        
    Returns:
        (股票代码, 交易所) 如 ('600000', 'SH')
    """
    if '.' in ts_code:
        code, exchange = ts_code.split('.')
        return code, exchange
    return ts_code, ''


def get_market_from_code(code: str) -> str:
    """
    根据股票代码判断所属市场
    
    Args:
        code: 股票代码
        
    Returns:
        市场名称：'主板'/'创业板'/'科创板'/'北交所'
    """
    if code.startswith('6'):
        return '主板'
    elif code.startswith('00'):
        return '主板'
    elif code.startswith('3'):
        return '创业板'
    elif code.startswith('688'):
        return '科创板'
    elif code.startswith('8') or code.startswith('4'):
        return '北交所'
    else:
        return '未知'
