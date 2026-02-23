#!/usr/bin/env python3
"""
基础数据加载器 - 提取 StockDataLoader 和 FactorDataLoader 的共同代码

解决问题：
- StockDataLoader 和 FactorDataLoader 中存在重复的数据处理逻辑
- 双索引设置、数据筛选、行业信息补充等代码重复

设计原则：
- 提取共同方法到基类
- 保持子类的特定行为
- 不影响现有代码运行
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BaseDataLoader(ABC):
    """
    基础数据加载器抽象类
    
    职责：
    1. 定义数据加载的通用接口
    2. 提供共同的数据处理方法
    3. 管理数据缓存
    
    子类需要实现：
    - load_data(): 加载数据的具体实现
    """
    
    def __init__(self):
        """初始化基础数据加载器"""
        # 数据缓存
        self._data: Optional[pd.DataFrame] = None
        self._stock_pool: Optional[List[str]] = None
    
    @property
    def data(self) -> Optional[pd.DataFrame]:
        """获取已加载的数据"""
        return self._data
    
    @property
    def stock_pool(self) -> Optional[List[str]]:
        """获取股票池"""
        return self._stock_pool
    
    @abstractmethod
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        加载数据的抽象方法
        
        子类必须实现此方法
        
        Returns:
            加载的数据 DataFrame
        """
        pass
    
    def set_multi_index(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        设置双索引 (trade_date, ts_code)
        
        这是一个共同操作，StockDataLoader 和 FactorDataLoader 都使用相同的逻辑。
        
        Args:
            data: 市场数据 DataFrame（必须包含 trade_date 和 ts_code 列）
            
        Returns:
            设置双索引后的 DataFrame
        """
        if data is None or len(data) == 0:
            return data
        
        # 确保 trade_date 是 datetime 类型
        if 'trade_date' in data.columns:
            data['trade_date'] = pd.to_datetime(data['trade_date'])
        
        # 按日期和股票代码排序
        sort_columns = []
        if 'trade_date' in data.columns:
            sort_columns.append('trade_date')
        if 'ts_code' in data.columns:
            sort_columns.append('ts_code')
        
        if sort_columns:
            data = data.sort_values(sort_columns)
        
        # 设置双索引
        if 'trade_date' in data.columns and 'ts_code' in data.columns:
            data = data.set_index(['trade_date', 'ts_code'])
        
        return data
    
    def filter_by_stock_pool(
        self, 
        data: pd.DataFrame, 
        stock_pool: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        根据股票池筛选数据
        
        Args:
            data: 市场数据 DataFrame
            stock_pool: 股票代码列表，如果为 None 则使用实例的 stock_pool
            
        Returns:
            筛选后的 DataFrame
        """
        if data is None or len(data) == 0:
            return data
        
        pool = stock_pool or self._stock_pool
        
        if pool is None or len(pool) == 0:
            return data
        
        # 判断数据是否有双索引
        if isinstance(data.index, pd.MultiIndex):
            # 从索引中获取 ts_code
            ts_codes = data.index.get_level_values('ts_code')
            mask = ts_codes.isin(pool)
            return data[mask]
        elif 'ts_code' in data.columns:
            return data[data['ts_code'].isin(pool)]
        
        return data
    
    def merge_data_dicts(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        合并数据字典为单个 DataFrame
        
        Args:
            data_dict: 日期 -> DataFrame 的字典
            
        Returns:
            合并后的 DataFrame
        """
        if not data_dict:
            return pd.DataFrame()
        
        return pd.concat(data_dict.values(), ignore_index=True)

    @staticmethod
    def extract_industries(data: pd.DataFrame) -> List[str]:
        """
        从数据中提取行业列表
        
        Args:
            data: 市场数据 DataFrame
            
        Returns:
            行业名称列表（去重且排序）
        """
        if data is None or 'industry' not in data.columns:
            # 如果是 MultiIndex，需要重置索引
            if isinstance(data.index, pd.MultiIndex):
                reset_data = data.reset_index()
                if 'industry' not in reset_data.columns:
                    return []
                industries = reset_data['industry'].dropna().unique()
            else:
                return []
        else:
            # 重置索引以访问 industry 列
            if isinstance(data.index, pd.MultiIndex):
                industries = data.reset_index()['industry'].dropna().unique()
            else:
                industries = data['industry'].dropna().unique()
        
        # 转换为字符串列表并排序
        industry_list = sorted([str(ind) for ind in industries if str(ind).strip()])
        
        return industry_list
    
    def get_data_info(self) -> Dict[str, Any]:
        """
        获取数据信息摘要
        
        Returns:
            数据信息字典
        """
        if self._data is None:
            return {'status': 'not_loaded'}
        
        info = {
            'status': 'loaded',
            'record_count': len(self._data),
        }
        
        # 如果是双索引
        if isinstance(self._data.index, pd.MultiIndex):
            info['stock_count'] = self._data.index.get_level_values('ts_code').nunique()
            info['date_range'] = {
                'start': self._data.index.get_level_values('trade_date').min().strftime('%Y-%m-%d'),
                'end': self._data.index.get_level_values('trade_date').max().strftime('%Y-%m-%d'),
            }
        elif 'ts_code' in self._data.columns:
            info['stock_count'] = self._data['ts_code'].nunique()
        
        return info
    
    def clean_data(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        通用数据清洗
        
        Args:
            data: 待清洗的数据，如果为 None 则使用 self._data
            
        Returns:
            清洗后的数据
        """
        if data is None:
            data = self._data
        
        if data is None:
            raise ValueError("没有数据可清洗")
        
        # 1. 删除全为空的行
        data = data.dropna(how='all')
        
        # 2. 删除关键字段为空的行
        key_columns = ['open', 'high', 'low', 'close', 'vol']
        existing_key_columns = [col for col in key_columns if col in data.columns]
        if existing_key_columns:
            data = data.dropna(subset=existing_key_columns)
        
        # 3. 删除交易量为0的行（停牌）
        if 'vol' in data.columns:
            data = data[data['vol'] > 0]
        
        return data


class DataLoaderMixin:
    """
    数据加载器混入类
    
    提供可以混入到现有类的通用方法，用于不适合继承的情况。
    """
    
    @staticmethod
    def set_dataframe_index(data: pd.DataFrame) -> pd.DataFrame:
        """
        设置双索引的静态方法
        
        可以直接调用而不需要实例化类。
        
        Args:
            data: 市场数据 DataFrame
            
        Returns:
            设置索引后的 DataFrame
        """
        if data is None or len(data) == 0:
            return data
        
        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data = data.sort_values(['trade_date', 'ts_code'])
        data = data.set_index(['trade_date', 'ts_code'])
        return data
    
    @staticmethod
    def filter_stocks(data: pd.DataFrame, stock_pool: List[str]) -> pd.DataFrame:
        """
        根据股票池筛选数据的静态方法
        
        Args:
            data: 市场数据 DataFrame
            stock_pool: 股票代码列表
            
        Returns:
            筛选后的 DataFrame
        """
        if data is None or len(data) == 0 or not stock_pool:
            return data
        
        if isinstance(data.index, pd.MultiIndex):
            ts_codes = data.index.get_level_values('ts_code')
            mask = ts_codes.isin(stock_pool)
            return data[mask]
        elif 'ts_code' in data.columns:
            return data[data['ts_code'].isin(stock_pool)]
        
        return data
