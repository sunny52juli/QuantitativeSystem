"""
工具配置模块 - 管理工具分类和策略关键词映射
"""

# ==================== 工具分类映射 ====================

# 工具分类映射 - 用于智能选择
TOOL_CATEGORIES = {
    # 数学运算工具
    "math": ["abs_value", "log_transform", "rank_normalize", "zscore_normalize"],
    
    # 时间序列工具
    "time_series": ["rolling_mean", "rolling_std", "lag", "delta", "pct_change"],
    
    # 技术指标工具
    "technical": ["rsi", "bollinger_position", "ema", "macd"],
    
    # 统计工具
    "statistical": ["correlation", "quantile"],
    
    # 组合工具
    "combination": ["max_of", "min_of", "clip"],
    
    # 筛选工具（行业、市场等）
    "filter": ["filter_by_industry", "filter_by_market"],
    
    # 数据管理工具
    "data_management": ["load_data", "save_factor", "list_factors"]
}

# 策略关键词到工具类别的映射
STRATEGY_KEYWORDS = {
    # 动量相关策略
    "动量": ["time_series", "math"],
    "收益率": ["time_series"],
    "涨幅": ["time_series"],
    "上涨": ["time_series", "math"],
    "下跌": ["time_series", "math"],
    "趋势": ["time_series", "technical"],
    "突破": ["time_series", "technical"],
    
    # 成交量相关策略
    "放量": ["time_series", "math"],
    "缩量": ["time_series", "math"],
    "成交量": ["time_series", "math"],
    "量价": ["time_series", "math"],
    
    # 波动率相关策略
    "波动": ["time_series", "statistical"],
    "标准差": ["time_series"],
    "振幅": ["time_series"],
    "风险": ["time_series", "statistical"],
    "波动率": ["time_series", "statistical"],
    
    # 技术指标相关策略
    "RSI": ["technical"],
    "MACD": ["technical"],
    "布林带": ["technical"],
    "均线": ["time_series", "technical"],
    "技术指标": ["technical"],
    "金叉": ["time_series", "technical"],
    "死叉": ["time_series", "technical"],
    
    # 价值相关策略
    "估值": ["math"],
    "排名": ["math"],
    "标准化": ["math"],
    "归一化": ["math"],
    "价值": ["math"],
    
    # 相关性策略
    "相关": ["statistical"],
    "协整": ["statistical"],
    "回归": ["statistical"],
    "相关性": ["statistical"],
    
    # 筛选相关策略（行业、市场等）
    "行业": ["filter"],
    "板块": ["filter"],
    "市场": ["filter"],
    "主板": ["filter"],
    "创业板": ["filter"],
    "科创板": ["filter"],
    "通信": ["filter"],
    "医药": ["filter"],
    "金融": ["filter"],
    "科技": ["filter"],
    "消费": ["filter"],
    "制造": ["filter"]
}


class ToolConfig:
    """工具配置类 - 包含工具分类和策略关键词映射"""
    
    # 工具分类映射
    tool_categories = TOOL_CATEGORIES
    strategy_keywords = STRATEGY_KEYWORDS
    
    @classmethod
    def get_tool_categories(cls) -> dict:
        """
        获取工具分类映射
        
        Returns:
            dict: 工具分类映射字典
        """
        return cls.tool_categories
    
    @classmethod
    def get_strategy_keywords(cls) -> dict:
        """
        获取策略关键词映射
        
        Returns:
            dict: 策略关键词映射字典
        """
        return cls.strategy_keywords


# 为了向后兼容，导出这些变量
tool_categories = TOOL_CATEGORIES
strategy_keywords = STRATEGY_KEYWORDS
