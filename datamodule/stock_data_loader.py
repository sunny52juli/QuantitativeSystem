#!/usr/bin/env python3
"""
股票数据加载器 - 负责数据加载与预处理

所属模块: datamodule（数据模块）
职责: 从本地/远程加载股票数据，进行预处理和格式化

核心功能：
1. 加载市场数据（日线数据）
2. 管理股票池
3. 提取行业信息
4. 数据预处理（设置索引、补充字段等）

重构说明：
- 继承自 BaseDataLoader，复用共同的数据处理方法
- 保持原有接口不变，确保向后兼容

示例：
    from project.datamodule import StockDataLoader
    
    loader = StockDataLoader()
    data = loader.load_market_data()
    industries = loader.get_available_industries()
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from datamodule.base_loader import BaseDataLoader
from core.exceptions import DataLoadError, StockPoolError


class StockDataLoader(BaseDataLoader):
    """
    股票数据加载器
    
    职责：
    1. 从本地数据源加载市场数据
    2. 管理股票池（排除ST、新股等）
    3. 提取和补充行业信息
    4. 数据格式化（设置双索引等）
    
    继承自 BaseDataLoader，复用以下方法：
    - set_multi_index(): 设置双索引
    - filter_by_stock_pool(): 股票池筛选
    - merge_data_dicts(): 合并数据字典
    - extract_industries(): 提取行业列表
    - clean_data(): 数据清洗
    - get_data_info(): 获取数据信息
    
    示例：
        loader = StockDataLoader()
        data = loader.load_market_data()
        
        # 或者使用自定义参数
        loader = StockDataLoader(
            exclude_st=True,
            min_list_days=180,
            recent_days=60
        )
        data = loader.load_market_data()
    """
    
    def __init__(
        self,
        exclude_st: bool = True,
        min_list_days: int = 180,
        recent_days: int = 60,
        index_code: Optional[str] = None
    ):
        """
        初始化数据加载器
        
        Args:
            exclude_st: 是否排除ST股票
            min_list_days: 最小上市天数
            recent_days: 加载最近多少个交易日的数据
            index_code: 指数代码（用于限定股票池），None表示全市场
        """
        super().__init__()  # 调用基类初始化
        
        self.exclude_st = exclude_st
        self.min_list_days = min_list_days
        self.recent_days = recent_days
        self.index_code = index_code
        
        # 行业缓存
        self._available_industries: Optional[List[str]] = None
    
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        实现基类的抽象方法
        
        这是 BaseDataLoader 要求实现的方法。
        实际调用 load_market_data 方法。
        """
        return self.load_market_data(**kwargs)
    
    def load_market_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        加载市场数据
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            股票数据 DataFrame（双索引：trade_date, ts_code）
        """
        if self._data is not None and not force_reload:
            print("📊 使用缓存的市场数据")
            return self._data
        
        print("📊 正在加载市场数据...")
        
        # 导入数据接口
        from dataloader.data_interface import DataInterface
        data_interface = DataInterface()
        
        # 1. 获取股票池
        self._stock_pool = self._load_stock_pool(data_interface)
        
        if self._stock_pool is None or len(self._stock_pool) == 0:
            raise StockPoolError("无法获取股票池数据，请检查本地数据是否存在")
        
        print(f"📊 股票池共 {len(self._stock_pool)} 只股票")
        
        # 2. 获取日期范围
        start_date, end_date = self._get_date_range()
        print(f"📊 加载最近数据: {start_date} ~ {end_date}")
        
        # 3. 加载市场数据
        market_data_dict = data_interface.batch_get_market_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if not market_data_dict:
            raise DataLoadError(
                f"无法获取市场数据 ({start_date}~{end_date})",
                details={"start_date": start_date, "end_date": end_date}
            )
        
        # 4. 使用基类方法合并所有日期的数据
        self._data = self.merge_data_dicts(market_data_dict)
        
        if self._data is None or len(self._data) == 0:
            raise DataLoadError("加载的市场数据为空")
        
        # 5. 筛选股票池内的数据
        self._data = self._data[self._data['ts_code'].isin(self._stock_pool)]
        
        # 6. 补充行业信息
        self._data = self._supplement_industry_info(self._data, data_interface)
        
        # 7. 使用基类方法设置双索引
        self._data = self.set_multi_index(self._data)
        
        # 8. 使用基类方法缓存行业列表
        self._available_industries = self.extract_industries(self._data)
        
        print(f"✅ 已加载本地数据: {len(self._data)} 条记录")
        
        return self._data
    
    def _load_stock_pool(self, data_interface) -> List[str]:
        """
        加载股票池
        
        Args:
            data_interface: 数据接口实例
            
        Returns:
            股票代码列表
        """
        if self.index_code:
            print(f"📊 使用指数 {self.index_code} 作为股票池")
        else:
            print(f"📊 使用全市场股票作为股票池")
        
        stock_pool = data_interface.get_stock_pool(
            index_code=self.index_code,
            exclude_st=self.exclude_st,
            min_list_days=self.min_list_days
        )
        
        return stock_pool
    
    def _get_date_range(self) -> tuple:
        """
        获取日期范围
        
        Returns:
            (start_date, end_date) 元组
        """
        from dataloader.trade_calendar import TradeCalendar
        import tushare as ts
        
        # 创建 Tushare Pro API 实例
        pro_api = ts.pro_api()
        calendar = TradeCalendar(pro_api)
        
        # 计算日期范围（向前推更多天以确保有足够的交易日）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=self.recent_days * 2)).strftime('%Y%m%d')
        
        # 获取交易日列表
        recent_dates = calendar.get_trade_dates(start_date, end_date)
        
        if not recent_dates:
            raise ValueError("无法获取交易日历")
        
        # 确保日期列表是升序排列的
        recent_dates = sorted(recent_dates)
        
        # 取最近 N 个交易日
        recent_dates = recent_dates[-self.recent_days:] if len(recent_dates) > self.recent_days else recent_dates
        
        return recent_dates[0], recent_dates[-1]
    
    def _supplement_industry_info(
        self, 
        data: pd.DataFrame, 
        data_interface
    ) -> pd.DataFrame:
        """
        补充行业信息
        
        Args:
            data: 市场数据 DataFrame
            data_interface: 数据接口实例
            
        Returns:
            补充行业信息后的 DataFrame
        """
        if 'industry' in data.columns:
            unique_industries = data['industry'].nunique()
            print(f"📊 数据已包含行业信息: {unique_industries} 个行业")
            return data
        
        print(f"⚠️ 数据中缺少 industry 字段，尝试合并股票基础信息...")
        stock_list = data_interface.get_stock_list()
        
        if stock_list is not None and 'industry' in stock_list.columns:
            stock_info = stock_list[['ts_code', 'industry', 'market']].drop_duplicates('ts_code')
            data = data.merge(stock_info, on='ts_code', how='left')
            unique_industries = data['industry'].nunique()
            print(f"📊 已补充行业信息: {unique_industries} 个行业")
        else:
            print(f"⚠️ 无法获取股票行业信息，filter_by_industry 工具可能无法使用")
        
        return data
    
    def get_available_industries(self) -> List[str]:
        """
        获取数据中的实际行业列表
        
        Returns:
            行业名称列表（去重且排序）
        """
        if self._available_industries is not None:
            return self._available_industries
        
        if self._data is None:
            # 如果数据未加载，先加载数据
            self.load_market_data()
        
        return self._available_industries or []
    
    def get_latest_date(self) -> Optional[datetime]:
        """获取最新交易日"""
        if self._data is None:
            return None
        return self._data.index.get_level_values('trade_date').max()
    
    def get_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        if self._data is None:
            return []
        return self._data.index.get_level_values('ts_code').unique().tolist()


# ==================== 便捷函数 ====================

def create_stock_data_loader(
    exclude_st: bool = True,
    min_list_days: int = 180,
    recent_days: int = 60,
    index_code: Optional[str] = None
) -> StockDataLoader:
    """
    创建股票数据加载器实例的便捷函数
    
    Args:
        exclude_st: 是否排除ST股票
        min_list_days: 最小上市天数
        recent_days: 加载最近多少个交易日的数据
        index_code: 指数代码
        
    Returns:
        StockDataLoader 实例
    """
    return StockDataLoader(
        exclude_st=exclude_st,
        min_list_days=min_list_days,
        recent_days=recent_days,
        index_code=index_code
    )


def load_market_data(
    exclude_st: bool = True,
    min_list_days: int = 180,
    recent_days: int = 60,
    index_code: Optional[str] = None
) -> pd.DataFrame:
    """
    快速加载市场数据（一次性调用）
    
    Args:
        exclude_st: 是否排除ST股票
        min_list_days: 最小上市天数
        recent_days: 加载最近多少个交易日的数据
        index_code: 指数代码
        
    Returns:
        股票数据 DataFrame
    """
    loader = create_stock_data_loader(
        exclude_st=exclude_st,
        min_list_days=min_list_days,
        recent_days=recent_days,
        index_code=index_code
    )
    return loader.load_market_data()


def get_available_industries(data: Optional[pd.DataFrame] = None) -> List[str]:
    """
    获取可用行业列表
    
    Args:
        data: 股票数据 DataFrame，如果为 None 则自动加载
        
    Returns:
        行业名称列表
    """
    if data is None:
        loader = StockDataLoader()
        loader.load_market_data()
        return loader.get_available_industries()
    
    # 从数据中提取行业
    if 'industry' not in data.columns:
        return []
    
    if isinstance(data.index, pd.MultiIndex):
        industries = data.reset_index()['industry'].dropna().unique()
    else:
        industries = data['industry'].dropna().unique()
    
    return sorted([str(ind) for ind in industries if str(ind).strip()])