"""
交易日历工具模块
提供交易日查询、判断等功能
"""

import pandas as pd
from typing import List, Optional
import logging
import time

logger = logging.getLogger(__name__)


class TradeCalendar:
    """
    交易日历工具类
    
    功能：
    - 查询交易日历
    - 判断是否为交易日
    - 获取交易日列表
    """
    
    def __init__(self, pro_api, max_retries: int = 3):
        """
        初始化交易日历工具
        
        Args:
            pro_api: Tushare Pro API 实例
            max_retries: 最大重试次数
        """
        self.pro = pro_api
        self.max_retries = max_retries
        self._cache = {}  # 缓存交易日历数据
    
    def get_trade_dates(
        self,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> List[str]:
        """
        获取交易日列表
        
        Args:
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            use_cache: 是否使用缓存
            
        Returns:
            交易日列表
        """
        cache_key = f"{start_date}_{end_date}"
        
        # 检查缓存
        if use_cache and cache_key in self._cache:
            logger.debug(f"📋 使用缓存的交易日历数据")
            return self._cache[cache_key]
        
        try:
            df = self.pro.trade_cal(
                exchange='SSE',
                start_date=start_date,
                end_date=end_date,
                is_open='1'  # 1=交易日 0=非交易日
            )
            
            if df is not None and not df.empty:
                trade_dates = sorted(df['cal_date'].tolist())  # 确保日期升序排列
                self._cache[cache_key] = trade_dates
                logger.info(f"✅ 获取交易日历成功，共 {len(trade_dates)} 个交易日")
                return trade_dates
            else:
                logger.warning(f"⚠️ 期间内无交易日数据")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取交易日历失败: {e}")
            return []
    
    def is_trade_day(self, date: str) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            是否为交易日
        """
        for retry in range(self.max_retries):
            try:
                df = self.pro.trade_cal(
                    exchange='SSE',
                    start_date=date,
                    end_date=date
                )
                
                if df is not None and not df.empty:
                    is_open = df.iloc[0]['is_open'] == 1
                    logger.debug(f"📅 {date} {'是' if is_open else '不是'}交易日")
                    return is_open
                else:
                    logger.warning(f"⚠️ 无法查询 {date} 的交易日历")
                    return False
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * 1
                    logger.warning(f"⚠️ 查询交易日历失败（第{retry+1}次），{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 查询交易日历失败（已重试{self.max_retries}次）: {e}")
                    return False
        
        return False
    
    def get_latest_trade_date(self, before_date: str) -> Optional[str]:
        """
        获取指定日期之前的最近交易日
        
        Args:
            before_date: 参考日期 'YYYYMMDD'
            
        Returns:
            最近的交易日，如果没有则返回 None
        """
        try:
            # 查询前30天的交易日历
            from datetime import datetime, timedelta
            start = (datetime.strptime(before_date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.pro.trade_cal(
                exchange='SSE',
                start_date=start,
                end_date=before_date,
                is_open='1'
            )
            
            if df is not None and not df.empty:
                latest = df['cal_date'].max()
                logger.info(f"✅ {before_date} 之前最近交易日: {latest}")
                return latest
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取最近交易日失败: {e}")
            return None
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("🗑️ 交易日历缓存已清除")
