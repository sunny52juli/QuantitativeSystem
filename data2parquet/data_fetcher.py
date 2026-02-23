"""
数据源接口封装模块
负责从 Tushare 数据源拉取数据
"""

import pandas as pd
from typing import Optional
import logging
import tushare as ts
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    数据源接口封装类
    
    功能：
    - 从 Tushare 拉取市场数据
    - 从 Tushare 拉取股票数据
    - 从 Tushare 拉取指数数据
    - 从 Tushare 拉取成分股数据
    - 统一的重试机制和错误处理
    """
    
    def __init__(
        self,
        token: str,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        初始化数据拉取器
        
        Args:
            token: Tushare API token
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        ts.set_token(token)
        self.pro = ts.pro_api()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(f"✅ 数据拉取器初始化完成")
        logger.info(f"⚙️ 配置: 最大重试{self.max_retries}次, 重试延迟{self.retry_delay}秒")
    
    def fetch_market_data(
        self,
        date: str
    ) -> Optional[pd.DataFrame]:
        """
        拉取全市场数据（增强版）
        
        拼接信息包括：
        - 日线行情：开高低收、成交量、成交额、涨跌幅等
        - 基本信息：股票名称、行业、市场
        - 每日指标：市盈率、市净率、市销率、总市值、流通市值、换手率等
        - 复权因子：前复权因子、后复权因子
        - 资金流向：主力资金、超大单、大单、中单、小单净流入
        - 融资融券：融资余额、融券余额、融资买入额、融券卖出量
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            市场数据 DataFrame，失败返回 None
        """
        for retry in range(self.max_retries):
            try:
                # 1. 使用daily接口获取全市场日线数据
                df = self.pro.daily(trade_date=date)
                
                if df is None or df.empty:
                    logger.warning(f"⚠️ {date} 返回数据为空（可能非交易日）")
                    return None
                
                logger.info(f"📊 获取日线数据: {len(df)} 只股票")
                
                # 2. 通过 API 获取并补充股票基本信息
                try:
                    stock_basic_df = self.pro.stock_basic(
                        exchange='',
                        list_status='L',
                        fields='ts_code,name,area,industry,market,list_date'
                    )
                    if stock_basic_df is not None and not stock_basic_df.empty:
                        df = df.merge(
                            stock_basic_df[['ts_code', 'name', 'area', 'industry', 'market', 'list_date']],
                            on='ts_code',
                            how='left'
                        )
                        logger.info(f"   ✅ 拼接基本信息（股票名称、行业、市场、上市日期）")
                    time.sleep(0.3)  # API限流
                except Exception as e:
                    logger.warning(f"   ⚠️ 获取股票基本信息失败: {e}")
                
                # 3. 获取每日指标（市盈率、市净率、总市值等）
                try:
                    daily_basic = self.pro.daily_basic(
                        trade_date=date,
                        fields='ts_code,trade_date,turnover_rate,turnover_rate_f,vol_ratio,'
                               'pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,'
                               'free_share,total_mv,circ_mv'
                    )
                    if daily_basic is not None and not daily_basic.empty:
                        df = df.merge(daily_basic, on='ts_code', how='left', suffixes=('', '_basic'))
                        logger.info(f"   ✅ 拼接每日指标（市盈率、市值等）")
                    time.sleep(0.3)  # API限流
                except Exception as e:
                    logger.warning(f"   ⚠️ 获取每日指标失败: {e}")
                
                # 4. 获取复权因子
                try:
                    adj_factor = self.pro.adj_factor(
                        trade_date=date,
                        fields='ts_code,trade_date,adj_factor'
                    )
                    if adj_factor is not None and not adj_factor.empty:
                        df = df.merge(adj_factor, on='ts_code', how='left', suffixes=('', '_adj'))
                        logger.info(f"   ✅ 拼接复权因子")
                    time.sleep(0.3)  # API限流
                except Exception as e:
                    logger.warning(f"   ⚠️ 获取复权因子失败: {e}")
                
                # 5. 获取资金流向（个股资金流向）
                try:
                    moneyflow = self.pro.moneyflow(
                        trade_date=date,
                        fields='ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,'
                               'buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,'
                               'buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,'
                               'buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,'
                               'net_mf_vol,net_mf_amount'
                    )
                    if moneyflow is not None and not moneyflow.empty:
                        df = df.merge(moneyflow, on='ts_code', how='left', suffixes=('', '_mf'))
                        logger.info(f"   ✅ 拼接资金流向（主力/大单/中单/小单）")
                    time.sleep(0.3)  # API限流
                except Exception as e:
                    logger.warning(f"   ⚠️ 获取资金流向失败: {e}")
                
                # 6. 获取融资融券数据
                try:
                    margin = self.pro.margin_detail(
                        trade_date=date,
                        fields='ts_code,trade_date,rzye,rqye,rzmre,rqyl,rzche,rqchl,rqmcl,rzrqye'
                    )
                    if margin is not None and not margin.empty:
                        df = df.merge(margin, on='ts_code', how='left', suffixes=('', '_margin'))
                        logger.info(f"   ✅ 拼接融资融券数据")
                    time.sleep(0.3)  # API限流
                except Exception as e:
                    logger.warning(f"   ⚠️ 获取融资融券数据失败: {e}")
                
                # 7. 清理重复的 trade_date 列
                trade_date_cols = [col for col in df.columns if col.startswith('trade_date')]
                if len(trade_date_cols) > 1:
                    for col in trade_date_cols[1:]:
                        df.drop(columns=[col], inplace=True)
                
                logger.info(f"✅ 拉取 {date} 市场数据成功，共 {len(df)} 只股票，{len(df.columns)} 个字段")
                return df
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * self.retry_delay
                    logger.warning(f"⚠️ 拉取市场数据失败（第{retry+1}次）: {e}")
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 拉取市场数据失败（已重试{self.max_retries}次）: {e}")
                    return None
        
        return None
    
    def fetch_stock_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        adjust: str = "hfq"
    ) -> Optional[pd.DataFrame]:
        """
        拉取单只股票数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            adjust: 复权类型 'qfq'/'hfq'/''
            
        Returns:
            股票数据 DataFrame，失败返回 None
        """
        # 转换复权类型
        adj_map = {
            'qfq': 'qfq',  # 前复权
            'hfq': 'hfq',  # 后复权
            '': None       # 不复权
        }
        adj_type = adj_map.get(adjust, None)
        
        for retry in range(self.max_retries):
            try:
                # 使用pro_bar接口获取复权数据
                df = ts.pro_bar(
                    ts_code=ts_code,
                    adj=adj_type,
                    start_date=start_date,
                    end_date=end_date
                )

                if df is not None and not df.empty:
                    # 重命名列以保持一致性
                    df.rename(columns={'trade_date': 'date'}, inplace=True)
                    df = df.sort_values('date').reset_index(drop=True)
                    logger.info(f"✅ 拉取 {ts_code} 数据成功，共 {len(df)} 条")
                    return df
                else:
                    logger.warning(f"⚠️ {ts_code} 返回数据为空")
                    return None
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * self.retry_delay
                    logger.warning(f"⚠️ 拉取 {ts_code} 失败（第{retry+1}次）: {e}")
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 拉取 {ts_code} 失败（已重试{self.max_retries}次）: {e}")
                    return None
        
        return None
    
    def fetch_indices_data(self, date: str) -> Optional[pd.DataFrame]:
        """
        拉取指数数据
        
        Args:
            date: 日期字符串 'YYYYMMDD'
            
        Returns:
            指数数据 DataFrame，失败返回 None
        """
        # 主要指数代码
        indices = {
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指',
            '000300.SH': '沪深300',
            '000016.SH': '上证50',
            '399005.SZ': '中小板指',
            '000688.SH': '科创50',
        }
        
        all_data = []
        
        for ts_code, name in indices.items():
            for retry in range(self.max_retries):
                try:
                    # 使用index_daily接口获取指数日线数据
                    df = self.pro.index_daily(
                        ts_code=ts_code,
                        start_date=date,
                        end_date=date
                    )
                    
                    if df is not None and not df.empty:
                        df['指数代码'] = ts_code
                        df['指数名称'] = name
                        df.rename(columns={'trade_date': 'date'}, inplace=True)
                        all_data.append(df)
                        logger.info(f"   ✅ 获取指数 {name} 成功")
                        break
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    if retry < self.max_retries - 1:
                        logger.warning(f"   ⚠️ 获取指数 {name} 失败（第{retry+1}次）: {e}")
                        time.sleep(1)
                    else:
                        logger.warning(f"   ❌ 获取指数 {name} 失败（已重试{self.max_retries}次）: {e}")
                    continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            logger.info(f"✅ 拉取 {date} 指数数据成功，共 {len(result)} 个指数")
            return result
        else:
            logger.error(f"❌ 拉取 {date} 指数数据失败")
            return None
    
    def fetch_stock_list(self) -> Optional[pd.DataFrame]:
        """
        拉取A股股票列表
        
        Returns:
            股票列表 DataFrame，失败返回 None
        """
        for retry in range(self.max_retries):
            try:
                # 获取A股股票列表
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',  # L=上市 D=退市 P=暂停上市
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                
                if df is not None and not df.empty:
                    logger.info(f"✅ 拉取股票列表成功，共 {len(df)} 只股票")
                    return df
                else:
                    logger.warning(f"⚠️ 股票列表返回数据为空")
                    return None
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * self.retry_delay
                    logger.warning(f"⚠️ 拉取股票列表失败（第{retry+1}次）: {e}")
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 拉取股票列表失败（已重试{self.max_retries}次）: {e}")
                    return None
        
        return None
    
    def fetch_index_constituents(
        self,
        index_code: str,
        trade_date: str
    ) -> Optional[pd.DataFrame]:
        """
        拉取指数成分股
        
        Args:
            index_code: 指数代码
            trade_date: 交易日期 'YYYYMMDD'
            
        Returns:
            成分股数据 DataFrame，失败返回 None
        """
        for retry in range(self.max_retries):
            try:
                # 使用 index_weight 接口获取指数成分股及权重
                df = self.pro.index_weight(
                    index_code=index_code,
                    trade_date=trade_date
                )
                
                if df is not None and not df.empty:
                    logger.info(f"✅ 拉取 {index_code} 成分股成功，共 {len(df)} 只")
                    return df
                else:
                    # 如果当天没有数据，尝试获取最近有数据的日期
                    logger.warning(f"⚠️ {trade_date} 无成分股数据，尝试获取最近数据")
                    df = self.pro.index_weight(
                        index_code=index_code,
                        start_date=(datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d'),
                        end_date=trade_date
                    )
                    
                    if df is not None and not df.empty:
                        # 取最新日期的数据
                        latest_date = df['trade_date'].max()
                        df = df[df['trade_date'] == latest_date]
                        logger.info(f"✅ 拉取 {index_code} 成分股成功（{latest_date}），共 {len(df)} 只")
                        return df
                    
                    return None
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * self.retry_delay
                    logger.warning(f"⚠️ 拉取成分股失败（第{retry+1}次）: {e}")
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 拉取成分股失败（已重试{self.max_retries}次）: {e}")
                    return None
        
        return None
    
    def get_pro_api(self):
        """获取 Tushare Pro API 实例（供其他模块使用）"""
        return self.pro
