#!/usr/bin/env python3
"""
因子数据加载器 - 负责加载和准备回测数据

职责：
1. 从本地加载股票数据
2. 获取和筛选股票池
3. 准备回测所需的数据格式
4. 数据清洗和预处理

重构说明：
- 继承自 BaseDataLoader，复用共同的数据处理方法
- 保持原有接口不变，确保向后兼容
"""

import pandas as pd
from typing import Dict, List, Optional
from dataloader.data_interface import DataInterface
from config import FactorBacktestConfig
from datamodule.base_loader import BaseDataLoader
from core.exceptions import DataLoadError, StockPoolError


class FactorDataLoader(BaseDataLoader):
    """
    因子数据加载器
    
    功能：
    1. 从本地加载股票数据
    2. 获取和筛选股票池
    3. 准备回测所需的数据格式
    
    继承自 BaseDataLoader，复用以下方法：
    - set_multi_index(): 设置双索引
    - filter_by_stock_pool(): 股票池筛选
    - merge_data_dicts(): 合并数据字典
    - clean_data(): 数据清洗
    - get_data_info(): 获取数据信息
    """
    
    def __init__(self):
        """初始化数据加载器"""
        super().__init__()  # 调用基类初始化
        self.data_interface = DataInterface()
    
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        实现基类的抽象方法
        
        这是 BaseDataLoader 要求实现的方法。
        实际调用 load_backtest_data 方法。
        """
        return self.load_backtest_data(**kwargs)
    
    def get_stock_pool(
        self, 
        index_code: Optional[str] = None,
        exclude_st: bool = True,
        min_list_days: int = 180
    ) -> List[str]:
        """
        获取股票池
        
        Args:
            index_code: 指数代码，如果为 None 则获取全市场股票
            exclude_st: 是否排除 ST 股票
            min_list_days: 最小上市天数
            
        Returns:
            股票代码列表
        """
        if index_code is None:
            index_code = FactorBacktestConfig.DEFAULT_INDEX_CODE
        
        if index_code:
            print(f"📊 使用指数 {index_code} 的成分股作为股票池")
        else:
            print(f"📊 使用全市场股票作为股票池")
        
        # 获取股票池列表（自动应用筛选规则：剔除ST、新股等）
        self._stock_pool = self.data_interface.get_stock_pool(
            index_code=index_code,
            exclude_st=exclude_st,
            min_list_days=min_list_days
        )
        
        if self._stock_pool is None or len(self._stock_pool) == 0:
            raise StockPoolError("无法获取股票池数据，请检查本地数据是否存在")
        
        print(f"📊 股票池共 {len(self._stock_pool)} 只股票")
        return self._stock_pool
    
    def load_market_data(
        self, 
        start_date: str = None,
        end_date: str = None,
        stock_pool: List[str] = None
    ) -> pd.DataFrame:
        """
        加载市场数据
        
        Args:
            start_date: 开始日期，默认使用配置中的回测开始日期
            end_date: 结束日期，默认使用配置中的回测结束日期
            stock_pool: 股票池，如果为 None 则使用全部股票
            
        Returns:
            市场数据 DataFrame（双索引：trade_date, ts_code）
        """
        if start_date is None:
            start_date = FactorBacktestConfig.BACKTEST_DEFAULT_START_DATE
        if end_date is None:
            end_date = FactorBacktestConfig.BACKTEST_DEFAULT_END_DATE
        
        print(f"📊 加载回测数据: {start_date} ~ {end_date}")
        
        # 获取市场数据
        market_data_dict = self.data_interface.batch_get_market_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if not market_data_dict:
            raise DataLoadError(
                f"无法获取回测时间范围内的数据 ({start_date}~{end_date})",
                details={"start_date": start_date, "end_date": end_date}
            )
        
        # 使用基类方法合并数据
        self._data = self.merge_data_dicts(market_data_dict)
        
        if self._data is None or len(self._data) == 0:
            raise DataLoadError("无法获取股票数据，请检查本地数据是否存在")
        
        # 使用基类方法筛选股票池
        pool = stock_pool or self._stock_pool
        if pool is not None:
            self._data = self._data[self._data['ts_code'].isin(pool)]
        
        # 使用基类方法设置双索引
        self._data = self.set_multi_index(self._data)
        
        print(f"✅ 已加载本地数据: {len(self._data)} 条记录")
        print(f"   时间范围: {self._data.index.get_level_values('trade_date').min()} ~ {self._data.index.get_level_values('trade_date').max()}")
        print(f"   股票数量: {self._data.index.get_level_values('ts_code').nunique()} 只")
        print(f"   索引结构: MultiIndex(trade_date, ts_code)")
        
        return self._data
    
    def load_backtest_data(
        self,
        index_code: Optional[str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        加载回测数据（一站式方法）
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            准备好的回测数据 DataFrame
        """
        # 1. 获取股票池
        stock_pool = self.get_stock_pool(index_code=index_code)
        
        # 2. 加载市场数据
        data = self.load_market_data(
            start_date=start_date,
            end_date=end_date,
            stock_pool=stock_pool
        )
        
        return data
    
    def get_single_date_data(self, trade_date: str) -> pd.DataFrame:
        """
        获取单个交易日的数据
        
        Args:
            trade_date: 交易日期（格式：YYYYMMDD）
            
        Returns:
            单日数据 DataFrame
        """
        data = self.data_interface.get_market_data(trade_date)
        
        if data is None or len(data) == 0:
            raise DataLoadError(
                f"无法获取 {trade_date} 的数据",
                details={"trade_date": trade_date}
            )
        
        return data
    
    def clean_data(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        数据清洗
        
        覆盖基类方法，增加日志输出。
        
        Args:
            data: 待清洗的数据，如果为 None 则使用 self.data
            
        Returns:
            清洗后的数据
        """
        # 调用基类的清洗方法
        cleaned_data = super().clean_data(data)
        print(f"✅ 数据清洗完成: {len(cleaned_data)} 条记录")
        return cleaned_data
