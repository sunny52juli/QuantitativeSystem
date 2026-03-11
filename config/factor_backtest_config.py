"""
因子回测系统配置
包含因子回测系统专属的配置参数

改进：
- 使用动态默认值代替硬编码日期
- 添加类型注解
- 提供配置验证
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .api import APIConfig
from .tool_config import ToolConfig
from .stock_pool_config import StockPoolConfig


class FactorBacktestConfig:
    """
    因子回测系统配置类
    
    配置项说明：
    - n_factors: 每次生成的因子数量
    - DEFAULT_INDEX_CODE: 默认股票池指数
    - HOLDING_PERIODS: 回测持有期列表
    
    日期配置：
    - 默认使用最近3个月作为回测区间
    - 可通过 set_date_range() 自定义日期
    """
    
    # ==================== 因子数量配置 ====================
    n_factors: int = 1
    
    # ==================== 股票池配置 ====================
    # 默认指数代码（用于获取成分股池）
    # 常用指数代码：
    #   - '000300.SH': 沪深300指数成分股
    #   - '000905.SH': 中证500指数成分股
    #   - '000016.SH': 上证50指数成分股
    #   - '399006.SZ': 创业板指数成分股
    #   - None: 全市场股票（不限定成分股范围）
    DEFAULT_INDEX_CODE: Optional[str] = None  # 默认None使用全市场
    
    # 股票池筛选规则（从 StockPoolConfig 导入）
    STOCK_POOL_EXCLUDE_ST: bool = True
    STOCK_POOL_MIN_LIST_DAYS: int = 180
    
    # ==================== 日期配置（动态计算） ====================
    # 私有变量存储自定义日期
    _custom_start_date: Optional[str] = None
    _custom_end_date: Optional[str] = None
    
    # 默认回测时间范围（天数）
    DEFAULT_LOOKBACK_DAYS: int = 90  # 默认回测最近90天
    
    @classmethod
    @property
    def BACKTEST_DEFAULT_START_DATE(cls) -> str:
        """
        获取回测开始日期
        
        优先使用自定义日期，否则动态计算为当前日期前90天
        """
        if cls._custom_start_date:
            return cls._custom_start_date
        return (datetime.now() - timedelta(days=cls.DEFAULT_LOOKBACK_DAYS)).strftime('%Y%m%d')
    
    @classmethod
    @property
    def BACKTEST_DEFAULT_END_DATE(cls) -> str:
        """
        获取回测结束日期
        
        优先使用自定义日期，否则使用当前日期减去最大持有期天数
        （确保有足够的未来数据计算未来收益率）
        """
        if cls._custom_end_date:
            return cls._custom_end_date
        
        # 当前日期减去最大持有期天数（确保有足够的未来数据）
        max_holding_period = max(cls.HOLDING_PERIODS)  # 如 20 天
        buffer_days = 5  # 额外预留 5 天缓冲
        end_date = datetime.now() - timedelta(days=max_holding_period + buffer_days)
        return end_date.strftime('%Y%m%d')
    
    @classmethod
    def set_date_range(cls, start_date: str, end_date: str) -> None:
        """
        设置自定义回测日期范围
        
        Args:
            start_date: 开始日期 (格式: YYYYMMDD)
            end_date: 结束日期 (格式: YYYYMMDD)
            
        Example:
            FactorBacktestConfig.set_date_range('20240101', '20240331')
        """
        # 验证日期格式
        try:
            datetime.strptime(start_date, '%Y%m%d')
            datetime.strptime(end_date, '%Y%m%d')
        except ValueError as e:
            raise ValueError(f"日期格式错误，请使用 YYYYMMDD 格式: {e}")
        
        cls._custom_start_date = start_date
        cls._custom_end_date = end_date
    
    @classmethod
    def reset_date_range(cls) -> None:
        """重置为动态默认日期"""
        cls._custom_start_date = None
        cls._custom_end_date = None
    
    # ==================== 持有期配置 ====================
    # 未来收益率持有期配置（天数）
    HOLDING_PERIODS: List[int] = [1, 5, 20]  # 支持多个持有期：1日、5日
    
    # ==================== 配置获取方法 ====================
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """获取API配置"""
        return APIConfig.get_api_config()
    
    @classmethod
    def get_factor_config(cls) -> Dict[str, Any]:
        """获取因子配置"""
        return {
            "n_factors": cls.n_factors,
            "default_index_code": cls.DEFAULT_INDEX_CODE,
            "default_start_date": cls.BACKTEST_DEFAULT_START_DATE,
            "default_end_date": cls.BACKTEST_DEFAULT_END_DATE,
        }
    
    @classmethod
    def get_backtest_config(cls) -> Dict[str, Any]:
        """获取回测配置"""
        return {
            "start_date": cls.BACKTEST_DEFAULT_START_DATE,
            "end_date": cls.BACKTEST_DEFAULT_END_DATE,
            "holding_periods": cls.HOLDING_PERIODS,
            "stock_pool_rules": StockPoolConfig.get_stock_pool_rules()
        }
    
    @classmethod
    def get_tool_categories(cls) -> Dict[str, List[str]]:
        """获取工具分类映射"""
        return ToolConfig.get_tool_categories()
    
    @classmethod
    def get_strategy_keywords(cls) -> Dict[str, List[str]]:
        """获取策略关键词映射"""
        return ToolConfig.get_strategy_keywords()
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        errors = []
        
        # 验证因子数量
        if cls.n_factors <= 0:
            errors.append("n_factors 必须大于 0")
        
        # 验证持有期
        if not cls.HOLDING_PERIODS:
            errors.append("HOLDING_PERIODS 不能为空")
        
        # 验证日期范围
        start = datetime.strptime(cls.BACKTEST_DEFAULT_START_DATE, '%Y%m%d')
        end = datetime.strptime(cls.BACKTEST_DEFAULT_END_DATE, '%Y%m%d')
        if start > end:
            errors.append("开始日期不能晚于结束日期")
        
        if errors:
            for error in errors:
                print(f"⚠️ 配置错误: {error}")
            return False
        
        return True