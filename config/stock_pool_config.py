"""
股票池筛选配置模块 - 管理股票池筛选相关的公共配置
"""


class StockPoolConfig:
    """股票池筛选配置类 - 包含股票池筛选的公共规则"""
    
    # ==================== 股票池筛选规则 ====================
    MIN_LIST_DAYS = 180            # 最小上市天数（剔除新股）
    EXCLUDE_ST = True              # 是否剔除ST股票
    EXCLUDE_SUSPENDED = True       # 是否剔除停牌股票
    
    @classmethod
    def get_stock_pool_rules(cls) -> dict:
        """
        获取股票池筛选规则
        
        Returns:
            dict: 股票池筛选规则字典
        """
        return {
            "min_list_days": cls.MIN_LIST_DAYS,
            "exclude_st": cls.EXCLUDE_ST,
            "exclude_suspended": cls.EXCLUDE_SUSPENDED,
        }
