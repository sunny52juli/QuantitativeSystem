"""
统一数据接口 - 只读本地数据版本
所有接口只从本地路径读取数据，没有数据则报错
数据获取由独立的数据下载模块负责
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Union
import logging
import sys

# 使用统一的路径管理（优先尝试，失败则回退到旧方式以保持兼容）
try:
    from core.path_manager import ensure_project_path
    ensure_project_path()
except ImportError:
    # 回退：手动添加项目根目录到路径
    _project_root = Path(__file__).parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from config.data_path import DataConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataInterface:
    """
    统一数据接口 - 只读本地数据
    
    特性：
    - 只读本地：所有接口只从本地缓存读取
    - 无网络请求：不进行任何在线数据拉取
    - 快速响应：直接读取本地文件，速度快
    - 明确错误：数据不存在时抛出明确的异常
    
    注意：
    - 数据获取由独立的数据下载模块负责（data_downloader.py）
    - 建议配合定时任务使用（daily_cron.py）
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据接口
        
        Args:
            data_dir: 数据保存目录（如果为None，则从配置文件读取）
        """
        # 从配置文件读取路径，如果未指定则使用配置
        if data_dir is None:
            data_dir = DataConfig.DATA_CACHE_ROOT
        
        self.data_dir = Path(data_dir)
        self.daily_dir = Path(DataConfig.DAILY_DATA_DIR)
        self.indices_dir = Path(DataConfig.INDICES_DATA_DIR)
        self.stock_data_dir = self.data_dir / "stock_data"
        self.index_constituents_dir = self.data_dir / "index_constituents"
        
        # 确保目录存在
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        self.stock_data_dir.mkdir(parents=True, exist_ok=True)
        self.index_constituents_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ 数据接口初始化完成（只读模式）")
        logger.info(f"📁 数据目录: {self.data_dir.absolute()}")
    
    def get_market_data(self, date: str) -> pd.DataFrame:
        """
        获取全市场数据（只读本地）
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            全市场数据DataFrame
            
        Raises:
            FileNotFoundError: 本地数据不存在
        """
        file_path = self.daily_dir / f"{date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ 本地不存在 {date} 的市场数据\n"
                f"文件路径: {file_path}\n"
                f"请先运行数据下载模块获取数据"
            )
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"✅ 读取 {date} 市场数据，共 {len(df)} 只股票")
            return df
        except Exception as e:
            raise IOError(f"❌ 读取市场数据失败: {e}")
    
    def get_stock_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取单只股票的历史数据（只读本地）
        
        Args:
            stock_code: 股票代码，如 '000001.SZ' 或 '600000.SH'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            
        Returns:
            股票历史数据DataFrame
            
        Raises:
            FileNotFoundError: 本地数据不存在
        """
        # 标准化股票代码
        ts_code = self._normalize_stock_code(stock_code)
        
        # 构建文件路径
        file_path = self.stock_data_dir / f"{ts_code.replace('.', '_')}_{start_date}_{end_date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ 本地不存在 {ts_code} 的历史数据 ({start_date}~{end_date})\n"
                f"文件路径: {file_path}\n"
                f"请先运行数据下载模块获取数据"
            )
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"✅ 读取 {ts_code} 数据，共 {len(df)} 条")
            return df
        except Exception as e:
            raise IOError(f"❌ 读取股票数据失败: {e}")
    
    def get_indices_data(self, date: str) -> pd.DataFrame:
        """
        获取指数数据（只读本地）
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            指数数据DataFrame
            
        Raises:
            FileNotFoundError: 本地数据不存在
        """
        file_path = self.indices_dir / f"indices_{date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ 本地不存在 {date} 的指数数据\n"
                f"文件路径: {file_path}\n"
                f"请先运行数据下载模块获取数据"
            )
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"✅ 读取 {date} 指数数据")
            return df
        except Exception as e:
            raise IOError(f"❌ 读取指数数据失败: {e}")
    
    def get_stock_list(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        从市场数据中提取股票列表
        
        Args:
            date: 日期字符串 'YYYYMMDD'，如果为None则使用最新交易日

        Returns:
            股票列表DataFrame（包含ts_code, name, area, industry, market, list_date等字段）

        Raises:
            FileNotFoundError: 本地数据不存在
        """
        # 如果未指定日期，使用最新交易日
        if date is None:
            date = self.get_latest_trading_date()
            if date is None:
                raise FileNotFoundError(
                    f"❌ 本地没有任何市场数据\n"
                    f"请先运行数据下载模块获取数据"
                )
        
        # 从市场数据中提取股票基本信息
        market_df = self.get_market_data(date)
        
        # 提取股票列表相关字段
        stock_list_columns = ['ts_code', 'name', 'area', 'industry', 'market', 'list_date']
        available_columns = [col for col in stock_list_columns if col in market_df.columns]
        
        if 'ts_code' not in available_columns:
            raise ValueError("❌ 市场数据中缺少ts_code字段")
        
        stock_list = market_df[available_columns].drop_duplicates(subset=['ts_code']).copy()
        logger.info(f"✅ 从 {date} 市场数据中提取股票列表，共 {len(stock_list)} 只股票")
        return stock_list
    
    def get_index_constituents(
        self,
        index_code: str,
        trade_date: str
    ) -> pd.DataFrame:
        """
        获取指数成分股列表（只读本地）
        
        Args:
            index_code: 指数代码，如 '000300.SH'（沪深300）
            trade_date: 交易日期 'YYYYMMDD'
            
        Returns:
            成分股列表DataFrame
            
        Raises:
            FileNotFoundError: 本地数据不存在
        """
        file_path = self.index_constituents_dir / f"{index_code.replace('.', '_')}_{trade_date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ 本地不存在 {index_code} 的成分股数据 ({trade_date})\n"
                f"文件路径: {file_path}\n"
                f"请先运行数据下载模块获取数据"
            )
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"✅ 读取 {index_code} 成分股列表，共 {len(df)} 只股票")
            return df
        except Exception as e:
            raise IOError(f"❌ 读取成分股数据失败: {e}")
    
    def get_stock_pool(
        self,
        index_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        exclude_st: bool = True,
        min_list_days: int = 180
    ) -> List[str]:
        """
        获取股票池（成分股列表）
        
        Args:
            index_code: 指数代码，如 '000300.SH'。如果为None，返回全市场股票
            trade_date: 交易日期 'YYYYMMDD'，如果为None则使用最新交易日
            exclude_st: 是否剔除ST股票
            min_list_days: 最小上市天数（剔除新股）
            
        Returns:
            股票代码列表
            
        Raises:
            FileNotFoundError: 本地数据不存在
        """
        # 如果未指定日期，使用最新交易日
        if trade_date is None:
            trade_date = self.get_latest_trading_date()
            if trade_date is None:
                raise FileNotFoundError(
                    f"❌ 本地没有任何市场数据\n"
                    f"请先运行数据下载模块获取数据"
                )
        
        if index_code:
            # 获取指数成分股
            df = self.get_index_constituents(index_code, trade_date)
            stock_list = df['ts_code'].tolist()
            logger.info(f"📊 获取 {index_code} 成分股 {len(stock_list)} 只")
            # 获取股票基本信息用于筛选
            stock_basic = self.get_stock_list(trade_date) if (exclude_st or min_list_days > 0) else None
        else:
            # 获取全市场股票
            stock_basic = self.get_stock_list(trade_date)
            stock_list = stock_basic['ts_code'].tolist()
            logger.info(f"📊 获取全市场股票 {len(stock_list)} 只")
        
        # 筛选条件
        if exclude_st or min_list_days > 0:
            
            # 计算上市天数（如果有list_date字段）
            if 'list_date' in stock_basic.columns:
                today = datetime.now()
                stock_basic['list_date'] = pd.to_datetime(stock_basic['list_date'])
                stock_basic['list_days'] = (today - stock_basic['list_date']).dt.days
                
                # 筛选
                valid_stocks = stock_basic[
                    (stock_basic['ts_code'].isin(stock_list)) &
                    (stock_basic['list_days'] >= min_list_days)
                ]
            else:
                # 如果没有list_date字段，只筛选股票代码
                valid_stocks = stock_basic[stock_basic['ts_code'].isin(stock_list)]
                logger.warning(f"⚠️ 市场数据中缺少list_date字段，跳过上市天数筛选")
            
            # 剔除ST股票（名称中包含ST）
            if exclude_st and 'name' in valid_stocks.columns:
                valid_stocks = valid_stocks[~valid_stocks['name'].str.contains('ST', na=False)]
            elif exclude_st:
                logger.warning(f"⚠️ 市场数据中缺少name字段，跳过ST股票筛选")
            
            filtered_list = valid_stocks['ts_code'].tolist()
            logger.info(f"📊 筛选后股票池: {len(filtered_list)} 只（原 {len(stock_list)} 只）")
            return filtered_list
        
        return stock_list
    
    def batch_get_market_data(
        self,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        批量获取多日市场数据
        
        Args:
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            
        Returns:
            字典 {日期: DataFrame}
        """
        result = {}
        
        # 获取所有可用日期
        available_dates = self.get_available_dates('market')
        
        # 筛选日期范围内的数据
        for date_str in available_dates:
            if start_date <= date_str <= end_date:
                try:
                    df = self.get_market_data(date_str)
                    result[date_str] = df
                except FileNotFoundError:
                    logger.warning(f"⚠️ 跳过缺失日期: {date_str}")
                    continue
        
        logger.info(f"✅ 批量获取完成，成功获取 {len(result)} 天的数据")
        return result
    
    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码为标准格式
        
        Args:
            code: 股票代码，如 '000001' 或 '000001.SZ'
            
        Returns:
            标准格式代码，如 '000001.SZ'
        """
        # 如果已经是标准格式，直接返回
        if '.' in code:
            return code
        
        # 根据代码判断市场
        if code.startswith('6'):
            return f"{code}.SH"  # 上海
        elif code.startswith('0') or code.startswith('3'):
            return f"{code}.SZ"  # 深圳
        elif code.startswith('8') or code.startswith('4'):
            return f"{code}.BJ"  # 北京
        else:
            return f"{code}.SH"  # 默认上海
    
    # ==================== 便捷方法 ====================
    
    def get_latest_trading_date(self) -> Optional[str]:
        """获取本地最新的交易日期"""
        if not self.daily_dir.exists():
            return None
        
        files = sorted(self.daily_dir.glob('*.parquet'))
        if files:
            latest_file = files[-1]
            date_str = latest_file.stem
            return date_str
        return None
    
    def check_data_exists(self, date: str, data_type: str = 'market') -> bool:
        """
        检查指定日期的数据是否存在
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            data_type: 数据类型 'market'/'indices'
            
        Returns:
            是否存在
        """
        if data_type == 'market':
            file_path = self.daily_dir / f"{date}.parquet"
        elif data_type == 'indices':
            file_path = self.indices_dir / f"indices_{date}.parquet"
        else:
            return False
        
        return file_path.exists()
    
    def get_available_dates(self, data_type: str = 'market') -> List[str]:
        """
        获取所有可用的日期列表
        
        Args:
            data_type: 数据类型 'market'/'indices'
            
        Returns:
            日期列表
        """
        if data_type == 'market':
            pattern = '*.parquet'
            search_dir = self.daily_dir
        elif data_type == 'indices':
            pattern = 'indices_*.parquet'
            search_dir = self.indices_dir
        else:
            return []
        
        files = sorted(search_dir.glob(pattern))
        
        if data_type == 'market':
            # 市场数据文件直接以日期命名
            dates = [f.stem for f in files]
        else:
            # 指数数据文件以 indices_ 前缀命名
            dates = [f.stem.replace('indices_', '') for f in files]
        
        return dates
    
    def get_data_summary(self) -> dict:
        """
        获取本地数据摘要
        
        Returns:
            数据摘要字典
        """
        summary = {
            'data_dir': str(self.data_dir.absolute()),
            'market_data': {
                'available_dates': len(self.get_available_dates('market')),
                'date_range': self._get_date_range('market')
            },
            'indices_data': {
                'available_dates': len(self.get_available_dates('indices')),
                'date_range': self._get_date_range('indices')
            },
            'latest_trading_date': self.get_latest_trading_date()
        }
        
        return summary
    
    def _get_date_range(self, data_type: str) -> dict:
        """获取数据日期范围"""
        dates = self.get_available_dates(data_type)
        if dates:
            return {
                'start': dates[0],
                'end': dates[-1],
                'count': len(dates)
            }
        return {'start': None, 'end': None, 'count': 0}


if __name__ == "__main__":
    # 使用示例
    data_interface = DataInterface()
    
    # 获取数据摘要
    summary = data_interface.get_data_summary()
    print("本地数据摘要:", summary)