#!/usr/bin/env python3
"""
数据模块 (Datamodule) - 数据加载和清洗相关功能

本模块合并了 factor_backtest_system 和 stock_asking_system 的数据加载功能。

包含：
- BaseDataLoader: 基础数据加载器（抽象类，提供共同方法）
- DataLoaderMixin: 数据加载器混入类（静态工具方法）
- FactorDataLoader: 因子数据加载器，负责加载和准备回测数据
- StockDataLoader: 股票数据加载器，负责加载市场数据和行业信息

注意：因子脚本加载器(FactorScriptLoader/FactorScriptExecutor)已移至
      factor_backtest_system.backtest.factor_loader

使用示例：
    # 因子回测系统使用
    from datamodule import FactorDataLoader
    loader = FactorDataLoader()
    data = loader.load_backtest_data()
    
    # 股票查询系统使用
    from datamodule import StockDataLoader
    loader = StockDataLoader()
    data = loader.load_market_data()
    
    # 使用基础加载器的工具方法
    from datamodule import DataLoaderMixin
    data = DataLoaderMixin.set_dataframe_index(data)
"""

import sys
from pathlib import Path

# 使用统一的路径管理（优先尝试，失败则回退到旧方式以保持兼容）
try:
    from core.path_manager import ensure_project_path
    ensure_project_path()
except ImportError:
    # 回退：手动添加项目根目录到路径
    _project_root = Path(__file__).resolve().parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

# 基础加载器（新增）
from datamodule.base_loader import BaseDataLoader, DataLoaderMixin

# 因子数据加载器
from datamodule.factor_data_loader import FactorDataLoader

# 股票数据相关
from datamodule.stock_data_loader import (
    StockDataLoader,
    create_stock_data_loader,
    load_market_data,
    get_available_industries,
)

__all__ = [
    # 基础加载器
    'BaseDataLoader',
    'DataLoaderMixin',
    # 因子数据加载器
    'FactorDataLoader',
    # 股票数据相关
    'StockDataLoader',
    'create_stock_data_loader',
    'load_market_data',
    'get_available_industries',
]
