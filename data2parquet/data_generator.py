"""
数据生成入口模块
提供统一的数据下载和生成接口
"""

import logging
import sys
from pathlib import Path as PathLib
from datetime import datetime, timedelta
from typing import Optional, List
import argparse

# 添加项目根目录到路径
project_root = PathLib(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data2parquet.data_fetcher import DataFetcher
from data2parquet.data_saver import DataSaver
from data2parquet.trade_calendar import TradeCalendar
from config.data_path import DataConfig
import tushare as ts

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataGenerator:
    """
    数据生成器 - 统一的数据下载和生成入口
    
    功能：
    - 下载市场数据（全市场日线数据）
    - 下载指数数据
    - 下载股票列表
    - 下载指数成分股
    - 批量下载多日数据
    - 自动补全缺失数据
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化数据生成器
        
        Args:
            token: Tushare API token（如果为None，则从配置文件读取）
        """
        # 获取token
        if token is None:
            token = DataConfig.DATA_SOURCE_TOKEN
            if not token:
                raise ValueError("❌ 未配置 Tushare API Token，请在.env文件中设置 DATA_SOURCE_TOKEN")
        
        # 初始化组件
        self.fetcher = DataFetcher(token=token)
        self.saver = DataSaver()
        
        # 初始化交易日历
        pro_api = ts.pro_api()
        self.calendar = TradeCalendar(pro_api)
        
        logger.info("✅ 数据生成器初始化完成")
    
    def generate_market_data(self, date: str, force: bool = False) -> bool:
        """
        生成市场数据（单日）
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            force: 是否强制重新下载（覆盖已有数据）
            
        Returns:
            是否成功
        """
        # 检查数据是否已存在
        if not force and self.saver.market_data_exists(date):
            logger.info(f"✅ {date} 市场数据已存在，跳过下载")
            return True
        
        logger.info(f"📥 开始下载 {date} 市场数据...")
        
        # 拉取数据
        df = self.fetcher.fetch_market_data(date)
        
        if df is None or df.empty:
            logger.warning(f"⚠️ {date} 无市场数据（可能非交易日）")
            return False
        
        # 保存数据
        success = self.saver.save_market_data(df, date)
        
        if success:
            logger.info(f"✅ {date} 市场数据生成完成")
        else:
            logger.error(f"❌ {date} 市场数据保存失败")
        
        return success
    
    def generate_indices_data(self, date: str, force: bool = False) -> bool:
        """
        生成指数数据（单日）
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            force: 是否强制重新下载
            
        Returns:
            是否成功
        """
        # 检查数据是否已存在
        if not force and self.saver.indices_data_exists(date):
            logger.info(f"✅ {date} 指数数据已存在，跳过下载")
            return True
        
        logger.info(f"📥 开始下载 {date} 指数数据...")
        
        # 拉取数据
        df = self.fetcher.fetch_indices_data(date)
        
        if df is None or df.empty:
            logger.warning(f"⚠️ {date} 无指数数据")
            return False
        
        # 保存数据
        success = self.saver.save_indices_data(df, date)
        
        if success:
            logger.info(f"✅ {date} 指数数据生成完成")
        else:
            logger.error(f"❌ {date} 指数数据保存失败")
        
        return success
    
    def generate_stock_list(self, force: bool = False) -> bool:
        """
        生成股票列表
        
        Args:
            force: 是否强制重新下载
            
        Returns:
            是否成功
        """
        # 检查数据是否已存在
        if not force and self.saver.stock_list_exists():
            logger.info(f"✅ 股票列表已存在，跳过下载")
            return True
        
        logger.info(f"📥 开始下载股票列表...")
        
        # 拉取数据
        df = self.fetcher.fetch_stock_list()
        
        if df is None or df.empty:
            logger.error(f"❌ 股票列表下载失败")
            return False
        
        # 保存数据
        success = self.saver.save_stock_list(df)
        
        if success:
            logger.info(f"✅ 股票列表生成完成，共 {len(df)} 只股票")
        else:
            logger.error(f"❌ 股票列表保存失败")
        
        return success
    
    def generate_index_constituents(
        self,
        index_code: str,
        trade_date: str,
        force: bool = False
    ) -> bool:
        """
        生成指数成分股数据
        
        Args:
            index_code: 指数代码，如 '000300.SH'
            trade_date: 交易日期 'YYYYMMDD'
            force: 是否强制重新下载
            
        Returns:
            是否成功
        """
        # 检查数据是否已存在
        if not force and self.saver.index_constituents_exists(index_code, trade_date):
            logger.info(f"✅ {index_code} 成分股数据已存在，跳过下载")
            return True
        
        logger.info(f"📥 开始下载 {index_code} 成分股数据...")
        
        # 拉取数据
        df = self.fetcher.fetch_index_constituents(index_code, trade_date)
        
        if df is None or df.empty:
            logger.warning(f"⚠️ {index_code} 无成分股数据")
            return False
        
        # 保存数据
        success = self.saver.save_index_constituents(df, index_code, trade_date)
        
        if success:
            logger.info(f"✅ {index_code} 成分股数据生成完成，共 {len(df)} 只股票")
        else:
            logger.error(f"❌ {index_code} 成分股数据保存失败")
        
        return success
    
    def batch_generate_market_data(
        self,
        start_date: str,
        end_date: str,
        force: bool = False
    ) -> dict:
        """
        批量生成市场数据
        
        Args:
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            force: 是否强制重新下载
            
        Returns:
            结果统计字典 {'success': int, 'failed': int, 'skipped': int}
        """
        logger.info(f"📊 开始批量生成市场数据: {start_date} ~ {end_date}")
        
        # 获取交易日列表
        trade_dates = self.calendar.get_trade_dates(start_date, end_date)
        
        if not trade_dates:
            logger.error(f"❌ 未找到交易日")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        logger.info(f"📅 共 {len(trade_dates)} 个交易日")
        
        # 批量下载
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, date in enumerate(trade_dates, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"进度: [{i}/{len(trade_dates)}] 处理日期: {date}")
            logger.info(f"{'='*60}")
            
            # 检查是否已存在
            if not force and self.saver.market_data_exists(date):
                logger.info(f"✅ {date} 数据已存在，跳过")
                stats['skipped'] += 1
                continue
            
            # 下载数据
            success = self.generate_market_data(date, force=force)
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        # 输出统计
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量生成完成")
        logger.info(f"✅ 成功: {stats['success']} 天")
        logger.info(f"❌ 失败: {stats['failed']} 天")
        logger.info(f"⏭️ 跳过: {stats['skipped']} 天")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def batch_generate_indices_data(
        self,
        start_date: str,
        end_date: str,
        force: bool = False
    ) -> dict:
        """
        批量生成指数数据
        
        Args:
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            force: 是否强制重新下载
            
        Returns:
            结果统计字典
        """
        logger.info(f"📊 开始批量生成指数数据: {start_date} ~ {end_date}")
        
        # 获取交易日列表
        trade_dates = self.calendar.get_trade_dates(start_date, end_date)
        
        if not trade_dates:
            logger.error(f"❌ 未找到交易日")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        logger.info(f"📅 共 {len(trade_dates)} 个交易日")
        
        # 批量下载
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, date in enumerate(trade_dates, 1):
            logger.info(f"\n进度: [{i}/{len(trade_dates)}] 处理日期: {date}")
            
            # 检查是否已存在
            if not force and self.saver.indices_data_exists(date):
                logger.info(f"✅ {date} 指数数据已存在，跳过")
                stats['skipped'] += 1
                continue
            
            # 下载数据
            success = self.generate_indices_data(date, force=force)
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        # 输出统计
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量生成完成")
        logger.info(f"✅ 成功: {stats['success']} 天")
        logger.info(f"❌ 失败: {stats['failed']} 天")
        logger.info(f"⏭️ 跳过: {stats['skipped']} 天")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def generate_recent_data(
        self,
        days: int = 30,
        include_indices: bool = True,
        force: bool = False
    ) -> dict:
        """
        生成最近N天的数据
        
        Args:
            days: 天数
            include_indices: 是否包含指数数据
            force: 是否强制重新下载
            
        Returns:
            结果统计字典
        """
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')  # 多取一些天数以确保有足够的交易日
        
        logger.info(f"📊 生成最近 {days} 天的数据")
        
        # 生成市场数据
        market_stats = self.batch_generate_market_data(start_date, end_date, force=force)
        
        # 生成指数数据
        indices_stats = {'success': 0, 'failed': 0, 'skipped': 0}
        if include_indices:
            indices_stats = self.batch_generate_indices_data(start_date, end_date, force=force)
        
        return {
            'market': market_stats,
            'indices': indices_stats
        }
    
    def generate_all_basic_data(self, date: str, force: bool = False) -> dict:
        """
        生成指定日期的所有基础数据
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            force: 是否强制重新下载
            
        Returns:
            结果字典
        """
        logger.info(f"📊 生成 {date} 的所有基础数据")
        
        results = {}
        
        # 1. 生成股票列表
        logger.info(f"\n{'='*60}")
        logger.info(f"1/3 生成股票列表")
        logger.info(f"{'='*60}")
        results['stock_list'] = self.generate_stock_list(force=force)
        
        # 2. 生成市场数据
        logger.info(f"\n{'='*60}")
        logger.info(f"2/3 生成市场数据")
        logger.info(f"{'='*60}")
        results['market_data'] = self.generate_market_data(date, force=force)
        
        # 3. 生成指数数据
        logger.info(f"\n{'='*60}")
        logger.info(f"3/3 生成指数数据")
        logger.info(f"{'='*60}")
        results['indices_data'] = self.generate_indices_data(date, force=force)
        
        # 输出总结
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {date} 基础数据生成完成")
        logger.info(f"股票列表: {'✅' if results['stock_list'] else '❌'}")
        logger.info(f"市场数据: {'✅' if results['market_data'] else '❌'}")
        logger.info(f"指数数据: {'✅' if results['indices_data'] else '❌'}")
        logger.info(f"{'='*60}\n")
        
        return results


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='数据生成工具 - 下载和生成量化系统所需的数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 直接运行（默认生成最近30天的数据）
  python data_generator.py
  
  # 生成今天的所有基础数据
  python data_generator.py --mode all
  
  # 生成今天的市场数据
  python data_generator.py --mode market
  
  # 生成今天的指数数据
  python data_generator.py --mode indices
  
  # 生成指定日期的所有基础数据
  python data_generator.py --mode all --date 20260212
  
  # 生成最近60天的数据
  python data_generator.py --mode recent --days 60
  
  # 批量生成指定日期范围的市场数据
  python data_generator.py --mode batch --start 20260101 --end 20260131
  
  # 强制重新下载（覆盖已有数据）
  python data_generator.py --mode market --force
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='recent',
        choices=['all', 'market', 'indices', 'stock_list', 'batch', 'recent'],
        help='生成模式: all=所有基础数据(默认今天), market=市场数据(默认今天), indices=指数数据(默认今天), stock_list=股票列表, batch=批量生成, recent=最近N天（默认）'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='日期 (格式: YYYYMMDD)，默认为今天'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        help='开始日期 (格式: YYYYMMDD)，用于batch模式'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        help='结束日期 (格式: YYYYMMDD)，用于batch模式'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='天数，用于recent模式，默认30天'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载（覆盖已有数据）'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        help='Tushare API Token（可选，默认从配置文件读取）'
    )
    
    args = parser.parse_args()
    
    # 默认日期为今天
    if args.date is None and args.mode in ['all', 'market', 'indices']:
        args.date = datetime.now().strftime('%Y%m%d')
    
    try:
        # 初始化数据生成器
        logger.info("🚀 启动数据生成器...")
        generator = DataGenerator(token=args.token)
        
        # 根据模式执行不同的操作
        if args.mode == 'all':
            # 生成所有基础数据（默认今天）
            logger.info(f"📅 生成日期: {args.date}")
            generator.generate_all_basic_data(args.date, force=args.force)
        
        elif args.mode == 'market':
            # 生成市场数据（默认今天）
            logger.info(f"📅 生成日期: {args.date}")
            generator.generate_market_data(args.date, force=args.force)
        
        elif args.mode == 'indices':
            # 生成指数数据（默认今天）
            logger.info(f"📅 生成日期: {args.date}")
            generator.generate_indices_data(args.date, force=args.force)
        
        elif args.mode == 'stock_list':
            # 生成股票列表
            generator.generate_stock_list(force=args.force)
        
        elif args.mode == 'batch':
            # 批量生成
            if not args.start or not args.end:
                logger.error("❌ batch模式需要指定--start和--end参数")
                return
            generator.batch_generate_market_data(args.start, args.end, force=args.force)
        
        elif args.mode == 'recent':
            # 生成最近N天
            generator.generate_recent_data(days=args.days, force=args.force)
        
        logger.info("✅ 数据生成完成")
        
    except Exception as e:
        logger.error(f"❌ 数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
