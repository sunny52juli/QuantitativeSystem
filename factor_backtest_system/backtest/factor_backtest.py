"""
自动化因子挖掘框架
支持文字输入因子表达式，自动计算并回测因子表现
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any, Union
from typing_extensions import TypedDict
import warnings
import sys
from pathlib import Path


# ==================== 类型定义 ====================

class MetricsResult(TypedDict, total=False):
    """单组绩效指标的类型定义"""
    年化收益率: float
    年化波动率: float
    夏普比率: float
    最大回撤: float
    胜率: float
    平均收益: float
    信息比率: float
    样本数量: int


class BacktestMetrics(TypedDict, total=False):
    """回测指标集合的类型定义"""
    group_0: MetricsResult
    group_1: MetricsResult
    group_2: MetricsResult
    group_3: MetricsResult
    group_4: MetricsResult
    group_long_short: MetricsResult


class BacktestResult(TypedDict, total=False):
    """回测结果的完整类型定义"""
    factor_name: str
    expression: str
    n_groups: int
    holding_period: int
    return_col: str
    group_returns: pd.DataFrame
    metrics: BacktestMetrics

warnings.filterwarnings('ignore')

# 使用统一的路径管理（优先尝试，失败则回退到旧方式以保持兼容）
try:
    from core.path_manager import ensure_project_path
    ensure_project_path()
except ImportError:
    # 回退：手动添加项目根目录到路径
    _project_root = Path(__file__).parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from data2parquet.data_interface import DataInterface
from config import FactorBacktestConfig as FactorConfig
from config.data_fields import FIELD_MAPPING, FUNCTION_MAPPING


class FactorMiningFramework:
    """
    自动化因子挖掘框架
    
    功能:
    1. 解析文字因子表达式
    2. 自动计算因子值
    3. 回测因子表现
    4. 生成评估报告
    
    改进:
    - 支持指定日期范围获取全量历史数据
    - 按股票分组在时间序列维度计算指标
    - 支持配置不同的未来收益率持有期
    """
    
    def __init__(self, 
                 start_date: str = None,
                 end_date: str = None,
                 holding_periods: List[int] = None,
                 index_code: str = None,
                 data_interface: DataInterface = None):
        """
        初始化框架
        
        Parameters:
        -----------
        start_date : str
            回测开始日期 'YYYYMMDD'，如果为None则使用配置文件默认值
        end_date : str
            回测结束日期 'YYYYMMDD'，如果为None则使用配置文件默认值
        holding_periods : List[int]
            未来收益率持有期列表（天数），如 [1, 5, 10, 20]
            如果为None则使用 [1, 5, 10, 20]
        index_code : str
            指数代码，用于限定股票池，如 '000300.SH'（沪深300）
            如果为None则使用全市场股票
        data_interface : DataInterface
            数据接口实例，如果为None则自动创建
        """
        # 使用配置文件的默认值
        self.start_date = start_date if start_date is not None else FactorConfig.BACKTEST_DEFAULT_START_DATE
        self.end_date = end_date if end_date is not None else FactorConfig.BACKTEST_DEFAULT_END_DATE
        self.holding_periods = holding_periods if holding_periods is not None else FactorConfig.HOLDING_PERIODS
        self.index_code = index_code if index_code is not None else FactorConfig.DEFAULT_INDEX_CODE
        
        # 初始化数据接口
        self.data_interface = data_interface or DataInterface()
        
        # 加载数据
        print(f"📊 加载数据: {self.start_date} ~ {self.end_date}")
        self.data = self._load_data()
        
        # 预处理数据
        self._preprocess_data()
        
        print(f"✅ 数据加载完成: {len(self.data)} 条记录")
        # 对于MultiIndex，需要从索引level获取股票和日期数量
        if isinstance(self.data.index, pd.MultiIndex):
            print(f"📈 股票数量: {self.data.index.get_level_values('ts_code').nunique()}")
            print(f"📅 交易日数量: {self.data.index.get_level_values('trade_date').nunique()}")
        else:
            print(f"📈 股票数量: {self.data['ts_code'].nunique()}")
            print(f"📅 交易日数量: {self.data['trade_date'].nunique()}")
        
        # 从配置文件导入字段映射和函数映射（避免重复定义）
        self.field_mapping = FIELD_MAPPING
        self.function_mapping = FUNCTION_MAPPING
    
    def _load_data(self) -> pd.DataFrame:
        """
        加载指定日期范围的全量数据
        
        Returns:
        --------
        pd.DataFrame : 合并后的全量数据
        """
        # 批量获取市场数据
        data_dict = self.data_interface.batch_get_market_data(
            self.start_date,
            self.end_date
        )
        
        if not data_dict:
            raise ValueError(
                f"❌ 未找到日期范围 {self.start_date}~{self.end_date} 的数据\n"
                f"请先运行数据下载模块获取数据"
            )
        
        # 合并所有日期的数据
        all_data = []
        for date_str, df in sorted(data_dict.items()):
            df = df.copy()
            # 确保有trade_date列
            if 'trade_date' not in df.columns:
                df['trade_date'] = date_str
            all_data.append(df)
        
        merged_data = pd.concat(all_data, ignore_index=True)
        
        # 如果指定了指数代码，筛选股票池
        if self.index_code:
            stock_pool = self.data_interface.get_stock_pool(
                index_code=self.index_code,
                trade_date=self.end_date,
                exclude_st=FactorConfig.STOCK_POOL_EXCLUDE_ST,
                min_list_days=FactorConfig.STOCK_POOL_MIN_LIST_DAYS
            )
            merged_data = merged_data[merged_data['ts_code'].isin(stock_pool)]
            print(f"📊 使用 {self.index_code} 成分股，共 {len(stock_pool)} 只")
        
        # 设置双索引 (trade_date, ts_code)
        merged_data['trade_date'] = pd.to_datetime(merged_data['trade_date'])
        merged_data = merged_data.sort_values(['trade_date', 'ts_code'])
        merged_data = merged_data.set_index(['trade_date', 'ts_code'])
        print(f"📊 数据索引结构: MultiIndex(trade_date, ts_code)")
        
        return merged_data
        
    def _preprocess_data(self):
        """
        预处理数据 - 按股票分组在时间序列维度计算指标
        注意：数据已经是双索引 (trade_date, ts_code)
        """
        print("🔧 预处理数据...")
        
        # 数据已经是双索引，需要重置索引进行分组操作
        data_reset = self.data.reset_index()
        
        # 计算VWAP（成交均价）
        if 'vwap' not in data_reset.columns and 'amount' in data_reset.columns and 'vol' in data_reset.columns:
            data_reset['vwap'] = data_reset['amount'] / (data_reset['vol'] + 1e-8)
        
        # 计算当日涨跌幅（按股票分组）
        if 'pct_change' not in data_reset.columns:
            data_reset['pct_change'] = data_reset.groupby('ts_code')['close'].pct_change()
        
        # 计算不同持有期的未来收益率（按股票分组）
        print(f"📊 计算未来收益率，持有期：{self.holding_periods}")
                
        # 诊断信息：检查数据范围
        data_reset_copy = data_reset.copy()
        date_range = data_reset_copy['trade_date'].unique()
        if len(date_range) > 0:
            min_date = pd.to_datetime(date_range.min())
            max_date = pd.to_datetime(date_range.max())
            print(f"   📅 数据范围：{min_date.strftime('%Y%m%d')} ~ {max_date.strftime('%Y%m%d')}")
            print(f"   📅 总交易日数：{len(date_range)}")
            
            # 理论上有数据的日期范围
            print(f"\n   📊 理论有效样本分析：")
            for period in self.holding_periods:
                # 对于持有期 N，最后 N 个交易日的数据会是 NaN
                last_n_dates = sorted(date_range)[-period:] if len(date_range) >= period else []
                valid_dates = len(date_range) - len(last_n_dates)
                print(f"   📅 {period}日持有期：最后{period}天无数据 → 有效交易日={valid_dates}/{len(date_range)} ({valid_dates/len(date_range)*100:.1f}%)")
                print(f"      无效日期范围：{pd.to_datetime(last_n_dates[0]).strftime('%Y%m%d') if last_n_dates else 'N/A'} ~ {pd.to_datetime(last_n_dates[-1]).strftime('%Y%m%d') if last_n_dates else 'N/A'}")
                
        for period in self.holding_periods:
            ret_col = f'ret_{period}d'
            if ret_col not in data_reset.columns:
                # 计算 period 天后的收益率
                data_reset[ret_col] = data_reset.groupby('ts_code')['close'].pct_change(period).shift(-period)
                        
                # 诊断：统计每个持有期的有效样本数
                valid_count = data_reset[ret_col].notna().sum()
                nan_count = data_reset[ret_col].isna().sum()
                total = len(data_reset)
                print(f"   📊 {ret_col}: 有效={valid_count:,}, 缺失={nan_count:,} ({nan_count/total*100:.1f}%)")
        
        # 默认使用1日收益率作为ret列（向后兼容）
        if 'ret' not in data_reset.columns:
            data_reset['ret'] = data_reset['ret_1d'] if 'ret_1d' in data_reset.columns else \
                              data_reset.groupby('ts_code')['close'].pct_change().shift(-1)
        
        # 计算波动率（20日滚动标准差，按股票分组）
        if 'volatility' not in data_reset.columns:
            data_reset['volatility'] = data_reset.groupby('ts_code')['pct_change'].transform(
                lambda x: x.rolling(20, min_periods=5).std()
            )
        
        # 恢复双索引
        self.data = data_reset.set_index(['trade_date', 'ts_code'])
        
        # 计算换手率（如果有流通股本数据）
        if 'turnover_rate' not in self.data.columns and 'vol' in self.data.columns:
            # 这里简化处理，实际需要流通股本数据
            pass
        
        print("✅ 数据预处理完成")
    
    def parse_factor(self, factor_expr: str) -> str:
        """
        解析因子表达式，将中文转换为Python代码
        
        Parameters:
        -----------
        factor_expr : str
            因子表达式，如 "(最高价-最低价)/收盘价"
            
        Returns:
        --------
        str : Python可执行的表达式
        """
        expr = factor_expr
        
        # 收集使用的字段
        used_fields = []
        
        # 替换字段名
        for chinese, english in self.field_mapping.items():
            if chinese in expr:
                expr = expr.replace(chinese, f"self.data['{english}']")
                used_fields.append(english)
        
        # 检查字段是否存在于数据中
        missing_fields = [field for field in used_fields if field not in self.data.columns]
        if missing_fields:
            print(f"⚠️ 警告：以下字段在数据中不存在: {missing_fields}")
            print(f"💡 提示：这些字段可能需要重新下载数据才能获取")
            print(f"   请运行数据下载模块获取完整的市场数据（包含财务指标）")
            print(f"   可用字段: {sorted(self.data.columns.tolist())[:20]}...")
            raise ValueError(f"Unknown field: {', '.join(missing_fields)}")
        
        # 处理常用函数
        # 例如: 移动平均(收盘价, 5) -> rolling_mean(close, 5)
        for chinese, english in self.function_mapping.items():
            if chinese in expr:
                expr = expr.replace(chinese, english)
        
        return expr
    
    def calculate_factor(self, factor_expr: str, factor_name: str = 'factor') -> pd.DataFrame:
        """
        计算因子值
        
        Parameters:
        -----------
        factor_expr : str
            因子表达式
        factor_name : str
            因子名称
            
        Returns:
        --------
        pd.DataFrame : 包含因子值的数据框
        """
        try:
            # 解析表达式
            parsed_expr = self.parse_factor(factor_expr)
            
            # 计算因子
            print(f"计算因子: {factor_name}")
            print(f"原始表达式: {factor_expr}")
            print(f"解析表达式: {parsed_expr}")
            
            # 执行计算
            factor_values = eval(parsed_expr)
            
            # 添加到数据框
            result = self.data.copy()
            result[factor_name] = factor_values
            
            # 处理无穷值和缺失值
            result[factor_name] = result[factor_name].replace([np.inf, -np.inf], np.nan)
            
            return result
            
        except Exception as e:
            print(f"计算因子时出错: {str(e)}")
            raise
    
    def backtest_factor(
        self, 
        data_with_factor: pd.DataFrame, 
        factor_name: str = 'factor',
        n_groups: int = 5,
        holding_period: int = 1,
        return_col: Optional[str] = None
    ) -> BacktestResult:
        """
        回测因子表现
        
        Parameters:
        -----------
        data_with_factor : pd.DataFrame
            包含因子值的数据框
        factor_name : str
            因子列名
        n_groups : int
            分组数量
        holding_period : int
            持有期(天数)
        return_col : str
            收益率列名，如果为None则自动根据holding_period选择
            
        Returns:
        --------
        Dict : 回测结果
        """
        df = data_with_factor.copy()
        
        # 如果是双索引，需要重置索引以便分组操作
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
        
        # 确定使用哪个收益率列
        if return_col is None:
            return_col = f'ret_{holding_period}d'
            if return_col not in df.columns:
                print(f"⚠️ 未找到 {return_col} 列，使用默认的 ret 列")
                return_col = 'ret'
        
        print(f"📊 回测配置：分组数={n_groups}, 持有期={holding_period}天，收益率列={return_col}")
                
        # 诊断：检查删除缺失值前后的样本数
        total_before = len(df)
        missing_factor = df[factor_name].isna().sum()
        missing_return = df[return_col].isna().sum()
        print(f"   📊 回测前总样本：{total_before:,}")
        print(f"   📊 因子值缺失：{missing_factor:,} ({missing_factor/total_before*100:.1f}%)")
        print(f"   📊 收益率缺失：{missing_return:,} ({missing_return/total_before*100:.1f}%)")
        
        # 分别统计只缺失因子、只缺失收益、两者都缺失的数量
        only_missing_factor = ((df[factor_name].isna()) & (df[return_col].notna())).sum()
        only_missing_return = ((df[factor_name].notna()) & (df[return_col].isna())).sum()
        both_missing = (df[factor_name].isna() & df[return_col].isna()).sum()
        print(f"   📊 仅因子值缺失：{only_missing_factor:,}")
        print(f"   📊 仅收益率缺失：{only_missing_return:,}")
        print(f"   📊 两者都缺失：{both_missing:,}")
        
        # 删除缺失值
        df = df.dropna(subset=[factor_name, return_col])
        total_after = len(df)
        print(f"   📊 回测有效样本：{total_after:,} (删除 {total_before-total_after:,}, {(total_before-total_after)/total_before*100:.1f}%)")
        
        # 如果有效样本太少，打印警告
        if total_after < total_before * 0.5:
            print(f"   ⚠️ 警告：超过 50% 的样本被删除！")
            print(f"   💡 建议：检查因子计算逻辑或数据质量")
        
        # 按日期分组，对因子进行排名分组
        df['factor_group'] = df.groupby('trade_date')[factor_name].transform(
            lambda x: pd.qcut(x, n_groups, labels=False, duplicates='drop')
        )
        
        # 计算各组的平均收益
        group_returns = df.groupby(['trade_date', 'factor_group'])[return_col].mean().reset_index()
        
        # 计算多空组合收益(最高组 - 最低组)
        long_short = group_returns.pivot(index='trade_date', columns='factor_group', values=return_col)
        long_short['long_short'] = long_short[n_groups-1] - long_short[0]
        
        # 计算绩效指标
        results = {
            'factor_name': factor_name,
            'expression': factor_name,
            'n_groups': n_groups,
            'holding_period': holding_period,
            'return_col': return_col,
            'group_returns': long_short,
            'metrics': self._calculate_metrics(long_short, holding_period)
        }
        
        return results
    
    def _calculate_metrics(
        self, 
        returns_df: pd.DataFrame, 
        holding_period: int = 1
    ) -> Dict[str, MetricsResult]:
        """
        计算绩效指标
        
        Parameters:
        -----------
        returns_df : pd.DataFrame
            收益率数据框
        holding_period : int
            持有期（天数），用于年化计算
        """
        metrics = {}
        
        for col in returns_df.columns:
            rets = returns_df[col].dropna()
            
            if len(rets) == 0:
                continue
                
            # 根据持有期调整年化因子
            annual_factor = 252 / holding_period
            
            metrics[f'group_{col}'] = {
                '年化收益率': rets.mean() * annual_factor,
                '年化波动率': rets.std() * np.sqrt(annual_factor),
                '夏普比率': (rets.mean() / rets.std() * np.sqrt(annual_factor)) if rets.std() > 0 else 0,
                '最大回撤': self._calculate_max_drawdown(rets),
                '胜率': (rets > 0).sum() / len(rets),
                '平均收益': rets.mean(),
                '信息比率': rets.mean() / rets.std() if rets.std() > 0 else 0,
                '样本数量': len(rets)
            }
        
        return metrics
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        return drawdown.min()
    
    def run_backtest(
        self, 
        factor_expr: str, 
        factor_name: Optional[str] = None, 
        **kwargs: Any
    ) -> BacktestResult:
        """
        一键运行因子回测
        
        Parameters:
        -----------
        factor_expr : str
            因子表达式
        factor_name : str
            因子名称
        **kwargs : 其他参数传递给backtest_factor
            
        Returns:
        --------
        Dict : 回测结果
        """
        if factor_name is None:
            factor_name = 'factor_' + str(hash(factor_expr))[:8]
        
        # 计算因子
        data_with_factor = self.calculate_factor(factor_expr, factor_name)
        
        # 回测
        results = self.backtest_factor(data_with_factor, factor_name, **kwargs)
        results['expression'] = factor_expr
        
        return results
    
    def print_results(self, results: BacktestResult) -> None:
        """打印回测结果"""
        print("\n" + "="*80)
        print(f"因子回测报告: {results['factor_name']}")
        print(f"因子表达式: {results['expression']}")
        print("="*80)
        
        print(f"\n回测配置:")
        print(f"  分组数量: {results['n_groups']}")
        print(f"  持有期: {results.get('holding_period', 1)} 天")
        print(f"  收益率列: {results.get('return_col', 'ret')}")
        
        metrics = results['metrics']
        
        # 打印各组表现
        print("\n各组表现:")
        print("-" * 80)
        
        # 获取所有组的名称
        group_names = sorted([k for k in metrics.keys() if k != 'group_long_short'])
        
        # 打印表头
        print(f"{'指标':<15}", end='')
        for group in group_names:
            print(f"{group:>12}", end='')
        if 'group_long_short' in metrics:
            print(f"{'多空组合':>12}", end='')
        print()
        print("-" * 80)
        
        # 打印各项指标
        metric_keys = ['年化收益率', '年化波动率', '夏普比率', '最大回撤', '胜率', '信息比率']
        
        for metric in metric_keys:
            print(f"{metric:<15}", end='')
            for group in group_names:
                value = metrics[group][metric]
                # 确保值是数字类型
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0.0
                
                if metric in ['年化收益率', '年化波动率', '最大回撤', '胜率']:
                    print(f"{value:>11.2%}", end='')
                else:
                    print(f"{value:>12.3f}", end='')
            
            if 'group_long_short' in metrics:
                value = metrics['group_long_short'][metric]
                # 确保值是数字类型
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0.0
                
                if metric in ['年化收益率', '年化波动率', '最大回撤', '胜率']:
                    print(f"{value:>11.2%}", end='')
                else:
                    print(f"{value:>12.3f}", end='')
            print()
        
        print("="*80)
        
        # 多空组合表现
        if 'group_long_short' in metrics:
            ls_metrics = metrics['group_long_short']
            print("\n多空组合表现(最高组-最低组):")
            
            # 确保所有值都是数字类型
            ann_ret = ls_metrics['年化收益率']
            if isinstance(ann_ret, str):
                try:
                    ann_ret = float(ann_ret)
                except (ValueError, TypeError):
                    ann_ret = 0.0
            
            sharpe = ls_metrics['夏普比率']
            if isinstance(sharpe, str):
                try:
                    sharpe = float(sharpe)
                except (ValueError, TypeError):
                    sharpe = 0.0
            
            ir = ls_metrics['信息比率']
            if isinstance(ir, str):
                try:
                    ir = float(ir)
                except (ValueError, TypeError):
                    ir = 0.0
            
            win_rate = ls_metrics['胜率']
            if isinstance(win_rate, str):
                try:
                    win_rate = float(win_rate)
                except (ValueError, TypeError):
                    win_rate = 0.0
            
            print(f"  年化收益率: {ann_ret:.2%}")
            print(f"  夏普比率: {sharpe:.3f}")
            print(f"  信息比率: {ir:.3f}")
            print(f"  胜率: {win_rate:.2%}")


# 示例用法
if __name__ == "__main__":
    print("因子回测框架")
    print("="*80)
    print("使用方法:")
    print("1. 从 main/main.py 中调用本框架")
    print("2. 指定回测日期范围和持有期")
    print("3. 使用 run_backtest() 方法进行因子回测")
    print("="*80)
    print("\n示例代码:")
    print("""
    from factor_backtest_system.backtest.factor_backtest import FactorMiningFramework
    
    # 方法1: 使用默认配置（从config/factor.py读取）
    framework = FactorMiningFramework()
    
    # 方法2: 自定义配置
    framework = FactorMiningFramework(
        start_date='20250801',      # 回测开始日期
        end_date='20251231',        # 回测结束日期
        holding_periods=[1, 5, 10, 20],  # 未来收益率持有期
        index_code='000300.SH'      # 限定股票池（None=全市场）
    )
    
    # 回测因子
    results = framework.run_backtest(
        factor_expr="(最高价-最低价)/收盘价",
        factor_name="日内振幅",
        n_groups=5,
        holding_period=5  # 使用5日收益率
    )
    
    # 打印结果
    framework.print_results(results)
    
    # 测试不同持有期
    for period in [1, 5, 10, 20]:
        print(f"\\n{'='*80}")
        print(f"持有期: {period}天")
        results = framework.run_backtest(
            factor_expr="(最高价-最低价)/收盘价",
            factor_name=f"日内振幅_{period}d",
            n_groups=5,
            holding_period=period
        )
        framework.print_results(results)
    """)
    print("\n详细使用示例请参考: main/main.py")
