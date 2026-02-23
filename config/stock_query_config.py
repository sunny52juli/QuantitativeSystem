"""
股票问答系统配置
包含股票查询系统专属的配置参数
"""

from typing import List

from .api import APIConfig
from .stock_pool_config import StockPoolConfig


class StockQueryConfig:
    """股票问答系统配置类"""
    
    # ==================== 查询配置 ====================
    # 默认返回股票数量
    DEFAULT_TOP_N = 20
    
    # 置信度阈值
    MIN_CONFIDENCE = 0.3  # 最小置信度，低于此值的结果会被过滤
    
    # 数据获取配置
    DEFAULT_LOOKBACK_DAYS = 60  # 默认获取最近60个交易日的数据
    
    # ==================== 收益率持有期配置 ====================
    # 筛选出的股票计算未来N日收益率，用于评估筛选效果
    HOLDING_PERIODS: List[int] = [1, 5]  # 1日、5日
    
    # ==================== 显示配置 ====================
    # 结果显示列
    DISPLAY_COLUMNS = [
        'stock_code',      # 股票代码
        'stock_name',      # 股票名称
        'confidence',      # 置信度
        'reason',          # 推荐理由
        'latest_price',    # 最新价格
        'change_pct'       # 涨跌幅
    ]
    
    # 数值格式化配置
    PRICE_DECIMAL = 2      # 价格保留小数位数
    PERCENT_DECIMAL = 2    # 百分比保留小数位数
    CONFIDENCE_DECIMAL = 2 # 置信度保留小数位数
    
    @classmethod
    def get_api_config(cls) -> dict:
        """获取API配置"""
        return APIConfig.get_api_config()
    
    @classmethod
    def get_query_config(cls) -> dict:
        """获取查询配置"""
        return {
            "default_top_n": cls.DEFAULT_TOP_N,
            "min_confidence": cls.MIN_CONFIDENCE,
            "default_lookback_days": cls.DEFAULT_LOOKBACK_DAYS,
            "stock_pool_rules": StockPoolConfig.get_stock_pool_rules()
        }
    
    @classmethod
    def get_display_config(cls) -> dict:
        """获取显示配置"""
        return {
            "display_columns": cls.DISPLAY_COLUMNS,
            "price_decimal": cls.PRICE_DECIMAL,
            "percent_decimal": cls.PERCENT_DECIMAL,
            "confidence_decimal": cls.CONFIDENCE_DECIMAL,
        }
