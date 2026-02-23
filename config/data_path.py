"""
数据配置模块 - 管理所有数据源相关的配置
包含数据缓存路径、数据质量配置等
"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class DataConfig:
    """数据配置类 - 包含所有数据源相关的配置"""
    
    # ==================== 数据源配置 ====================
    DATA_SOURCE_TOKEN = os.getenv('DATA_SOURCE_TOKEN')
    
    # ==================== 数据缓存路径配置 ====================
    # 数据缓存根目录
    DATA_CACHE_ROOT = r'D:\code\QuantitativeSystem\data2parquet\tushare_data'
    os.makedirs(DATA_CACHE_ROOT, exist_ok=True)
    # 子目录配置
    DAILY_DATA_DIR = os.path.join(DATA_CACHE_ROOT, 'daily')           # 日线数据目录
    INDICES_DATA_DIR = os.path.join(DATA_CACHE_ROOT, 'indices')        # 指数数据目录
    BY_DATE_DATA_DIR = os.path.join(DATA_CACHE_ROOT, 'by_date')       # 按日期分类数据目录
    FACTOR_DATA_DIR = os.path.join(DATA_CACHE_ROOT, 'factors')        # 因子数据目录
    BACKTEST_DATA_DIR = os.path.join(DATA_CACHE_ROOT, 'backtest')     # 回测数据目录
    
    # ==================== Tushare接口配置 ====================
    # 日线数据接口配置
    DAILY_DATA_FIELDS = [
        'ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close',
        'change', 'pct_chg', 'vol', 'amount', 'turnover_rate', 'turnover_rate_f',
        'vol_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm',
        'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'
    ]
    
    # ST股票列表接口配置
    ST_STOCK_FIELDS = [
        'ts_code', 'name', 'ann_date', 'st_ann_date', 'st_type', 'reason'
    ]
    
    # 股票基本信息接口配置
    STOCK_BASIC_FIELDS = [
        'ts_code', 'symbol', 'name', 'area', 'industry', 'market', 'list_date',
        'is_hs', 'curr_type', 'status'
    ]
    
    # ==================== 数据质量配置 ====================
    # 数据完整性检查
    MIN_DATA_COMPLETENESS_RATIO = 0.8    # 最小数据完整率
    MAX_MISSING_DAYS = 5                 # 最大连续缺失天数
    
    # 数据有效性检查
    MIN_PRICE = 0.01                     # 最小有效价格
    MAX_PRICE = 10000                    # 最大有效价格
    MIN_vol = 1000                    # 最小有效成交量
    
    @classmethod
    def get_data_config(cls) -> dict:
        """
        获取数据配置字典
        
        Returns:
            dict: 包含所有数据配置的字典
        """
        return {
            # 数据源配置
            "token": cls.DATA_SOURCE_TOKEN,
            
            # 缓存路径配置
            "data_cache_root": cls.DATA_CACHE_ROOT,
            "daily_data_dir": cls.DAILY_DATA_DIR,
            "indices_data_dir": cls.INDICES_DATA_DIR,
            "by_date_data_dir": cls.BY_DATE_DATA_DIR,
            "factor_data_dir": cls.FACTOR_DATA_DIR,
            "backtest_data_dir": cls.BACKTEST_DATA_DIR,
            
            # 数据质量配置
            "min_data_completeness_ratio": cls.MIN_DATA_COMPLETENESS_RATIO,
            "max_missing_days": cls.MAX_MISSING_DAYS,
            "min_price": cls.MIN_PRICE,
            "max_price": cls.MAX_PRICE,
            "min_vol": cls.MIN_vol,
        }
    
    @classmethod
    def get_cache_paths(cls) -> dict:
        """
        获取缓存路径配置
        
        Returns:
            dict: 缓存路径字典
        """
        return {
            "root": cls.DATA_CACHE_ROOT,
            "daily": cls.DAILY_DATA_DIR,
            "indices": cls.INDICES_DATA_DIR,
            "by_date": cls.BY_DATE_DATA_DIR,
            "factors": cls.FACTOR_DATA_DIR,
            "backtest": cls.BACKTEST_DATA_DIR,
        }
    
    @classmethod
    def get_tushare_config(cls) -> dict:
        """
        获取Tushare接口配置
        
        Returns:
            dict: Tushare配置字典
        """
        return {
            "daily_fields": cls.DAILY_DATA_FIELDS,
            "st_stock_fields": cls.ST_STOCK_FIELDS,
            "stock_basic_fields": cls.STOCK_BASIC_FIELDS,
        }
    
    @classmethod
    def get_data_quality_config(cls) -> dict:
        """
        获取数据质量配置
        
        Returns:
            dict: 数据质量配置字典
        """
        return {
            "min_completeness_ratio": cls.MIN_DATA_COMPLETENESS_RATIO,
            "max_missing_days": cls.MAX_MISSING_DAYS,
            "min_price": cls.MIN_PRICE,
            "max_price": cls.MAX_PRICE,
            "min_vol": cls.MIN_vol,
        }
