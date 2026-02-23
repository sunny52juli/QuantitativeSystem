"""
数据保存器模块
负责将数据保存到本地文件系统
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging
import sys
from pathlib import Path as PathLib

# 添加项目根目录到路径
project_root = PathLib(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.data_path import DataConfig

logger = logging.getLogger(__name__)


class DataSaver:
    """
    数据保存器
    
    功能：
    - 保存市场数据
    - 保存股票数据
    - 保存指数数据
    - 保存成分股数据
    - 统一的文件格式和目录管理
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据保存器
        
        Args:
            data_dir: 数据保存根目录（如果为None，则从配置文件读取）
        """
        # 从配置文件读取路径，如果未指定则使用配置
        if data_dir is None:
            data_dir = DataConfig.DATA_CACHE_ROOT
        
        self.data_dir = Path(data_dir)
        self.daily_dir = Path(DataConfig.DAILY_DATA_DIR)
        self.indices_dir = Path(DataConfig.INDICES_DATA_DIR)
        self.stock_data_dir = self.data_dir / "stock_data"
        self.index_constituents_dir = self.data_dir / "index_constituents"
        
        # 创建目录
        self._create_directories()
        
        logger.info(f"✅ 数据保存器初始化完成")
        logger.info(f"📁 数据目录: {self.data_dir.absolute()}")
    
    def _create_directories(self):
        """创建所有必要的目录"""
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        self.stock_data_dir.mkdir(parents=True, exist_ok=True)
        self.index_constituents_dir.mkdir(parents=True, exist_ok=True)
    
    def save_market_data(self, df: pd.DataFrame, date: str) -> bool:
        """
        保存市场数据
        
        Args:
            df: 市场数据 DataFrame
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            是否保存成功
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ 数据为空，跳过保存")
            return False
        
        file_path = self.daily_dir / f"{date}.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"💾 市场数据已保存: {file_path} ({len(df)} 条记录)")
            return True
        except Exception as e:
            logger.error(f"❌ 保存市场数据失败: {e}")
            return False
    
    def save_stock_data(
        self,
        df: pd.DataFrame,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> bool:
        """
        保存股票数据
        
        Args:
            df: 股票数据 DataFrame
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            是否保存成功
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ {ts_code} 数据为空，跳过保存")
            return False
        
        file_path = self.stock_data_dir / f"{ts_code.replace('.', '_')}_{start_date}_{end_date}.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"💾 股票数据已保存: {file_path} ({len(df)} 条记录)")
            return True
        except Exception as e:
            logger.error(f"❌ 保存股票数据失败: {e}")
            return False
    
    def save_indices_data(self, df: pd.DataFrame, date: str) -> bool:
        """
        保存指数数据
        
        Args:
            df: 指数数据 DataFrame
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            是否保存成功
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ 指数数据为空，跳过保存")
            return False
        
        file_path = self.indices_dir / f"{date}.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"💾 指数数据已保存: {file_path} ({len(df)} 条记录)")
            return True
        except Exception as e:
            logger.error(f"❌ 保存指数数据失败: {e}")
            return False
    
    def save_stock_list(self, df: pd.DataFrame) -> bool:
        """
        保存股票列表
        
        Args:
            df: 股票列表 DataFrame
            
        Returns:
            是否保存成功
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ 股票列表为空，跳过保存")
            return False
        
        file_path = self.data_dir / "stock_list.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"💾 股票列表已保存: {file_path} ({len(df)} 只股票)")
            return True
        except Exception as e:
            logger.error(f"❌ 保存股票列表失败: {e}")
            return False
    
    def save_index_constituents(
        self,
        df: pd.DataFrame,
        index_code: str,
        trade_date: str
    ) -> bool:
        """
        保存指数成分股
        
        Args:
            df: 成分股数据 DataFrame
            index_code: 指数代码
            trade_date: 交易日期
            
        Returns:
            是否保存成功
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ {index_code} 成分股数据为空，跳过保存")
            return False
        
        file_path = self.index_constituents_dir / f"{index_code.replace('.', '_')}_{trade_date}.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"💾 成分股数据已保存: {file_path} ({len(df)} 只股票)")
            return True
        except Exception as e:
            logger.error(f"❌ 保存成分股数据失败: {e}")
            return False
    
    def get_stock_list_path(self) -> Path:
        """获取股票列表文件路径"""
        return self.data_dir / "stock_list.parquet"
    
    def stock_list_exists(self) -> bool:
        """检查股票列表文件是否存在"""
        return self.get_stock_list_path().exists()
    
    def market_data_exists(self, date: str) -> bool:
        """
        检查市场数据是否已存在
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            是否存在
        """
        file_path = self.daily_dir / f"{date}.parquet"
        return file_path.exists()
    
    def stock_data_exists(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> bool:
        """
        检查股票数据是否已存在
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            是否存在
        """
        file_path = self.stock_data_dir / f"{ts_code.replace('.', '_')}_{start_date}_{end_date}.parquet"
        return file_path.exists()
    
    def indices_data_exists(self, date: str) -> bool:
        """
        检查指数数据是否已存在
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            是否存在
        """
        file_path = self.indices_dir / f"{date}.parquet"
        return file_path.exists()
    
    def index_constituents_exists(
        self,
        index_code: str,
        trade_date: str
    ) -> bool:
        """
        检查指数成分股数据是否已存在
        
        Args:
            index_code: 指数代码
            trade_date: 交易日期
            
        Returns:
            是否存在
        """
        file_path = self.index_constituents_dir / f"{index_code.replace('.', '_')}_{trade_date}.parquet"
        return file_path.exists()
