#!/usr/bin/env python3
"""
筛选脚本回测入口

独立的筛选脚本回测模块，支持直接回测 asking_scripts 目录下已有的筛选脚本，
无需经过 AI Agent 生成流程。

使用方式：
    1. 命令行运行（回测所有脚本）：
        python -m stock_asking_system.backtest.run_script_backtest

    2. 命令行指定脚本：
        python -m stock_asking_system.backtest.run_script_backtest script1.py script2.py

    3. 在代码中调用：
        from stock_asking_system.backtest.run_script_backtest import backtest_asking_scripts
        result = backtest_asking_scripts("path/to/script.py")
        
    4. 使用回测引擎：
        from stock_asking_system.backtest.run_script_backtest import AskingScriptBacktester
        backtester = AskingScriptBacktester()
        result = backtester.backtest_all()
"""

import os
import sys
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from stock_asking_system.backtest.asking_script_loader import AskingScriptLoader
from stock_asking_system.tools.stock_screener import StockScreener
from datamodule.stock_data_loader import StockDataLoader
from config import StockQueryConfig


class AskingScriptBacktester:
    """
    筛选脚本回测引擎
    
    功能：
    1. 加载 asking_scripts 目录下的筛选脚本
    2. 加载市场数据
    3. 执行筛选逻辑
    4. 计算候选股票各持有期的未来收益率
    5. 生成回测报告
    
    示例：
        backtester = AskingScriptBacktester()
        
        # 回测所有脚本
        result = backtester.backtest_all()
        
        # 回测指定脚本
        result = backtester.backtest_script("path/to/script.py")
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        holding_periods: Optional[List[int]] = None,
        top_n: int = 20,
    ):
        """
        初始化回测引擎
        
        Args:
            data: 股票数据 DataFrame（双索引：trade_date, ts_code），
                  如果为 None 则自动加载
            holding_periods: 持有期列表（天数），默认使用 StockQueryConfig.HOLDING_PERIODS
            top_n: 每个脚本返回的股票数量上限
        """
        self.holding_periods = holding_periods or StockQueryConfig.HOLDING_PERIODS
        self.top_n = top_n
        
        # 加载数据
        if data is None:
            print("📥 加载市场数据...")
            self.data_loader = StockDataLoader()
            self.data = self.data_loader.load_market_data()
        else:
            self.data = data
            self.data_loader = None
        
        # 创建脚本加载器
        self.script_loader = AskingScriptLoader()
        
        # 创建筛选器（传入 holding_periods 实现日期前移）
        self.screener = StockScreener(self.data, holding_periods=self.holding_periods)
        
        # 缓存交易日列表
        self._all_dates = sorted(
            self.data.index.get_level_values('trade_date').unique()
        )
        self._screening_date = self.screener.latest_date
        
        print(f"✅ 回测引擎初始化完成")
        print(f"   📅 筛选日: {self._screening_date.strftime('%Y-%m-%d')}")
        print(f"   ⏱️ 持有期: {self.holding_periods}")
        print(f"   🔢 每脚本返回: {self.top_n} 只")
    
    def backtest_all(
        self,
        scripts_dir: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        回测目录下所有筛选脚本
        
        Args:
            scripts_dir: 筛选脚本目录，为 None 则使用默认的 asking_scripts 目录
            verbose: 是否输出详细日志
            
        Returns:
            回测结果字典
        """
        loader = AskingScriptLoader(scripts_dir=scripts_dir)
        script_names = loader.list_scripts()
        
        if not script_names:
            print("⚠️ 未找到任何筛选脚本文件")
            return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
        
        resolved_paths = [
            os.path.join(loader.scripts_dir, name) for name in script_names
        ]
        
        return self._run_backtest(resolved_paths, verbose=verbose)
    
    def backtest_script(
        self,
        script_path: str,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        回测单个筛选脚本
        
        Args:
            script_path: 脚本文件路径（绝对路径或相对于 asking_scripts 的路径）
            verbose: 是否输出详细日志
            
        Returns:
            回测结果字典
        """
        # 如果不是绝对路径，拼接 asking_scripts 目录
        if not os.path.isabs(script_path):
            script_path = os.path.join(self.script_loader.scripts_dir, script_path)
        
        return self._run_backtest([script_path], verbose=verbose)
    
    def backtest_scripts(
        self,
        script_paths: List[str],
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        回测多个筛选脚本
        
        Args:
            script_paths: 脚本文件路径列表
            verbose: 是否输出详细日志
            
        Returns:
            回测结果字典
        """
        # 处理相对路径
        resolved = []
        for p in script_paths:
            if os.path.isabs(p):
                resolved.append(p)
            else:
                resolved.append(os.path.join(self.script_loader.scripts_dir, p))
        
        return self._run_backtest(resolved, verbose=verbose)
    
    def _run_backtest(
        self,
        script_paths: List[str],
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        执行回测的核心逻辑
        
        Args:
            script_paths: 脚本文件路径列表
            verbose: 是否输出详细日志
            
        Returns:
            回测结果字典
        """
        # 验证文件存在性
        valid_paths = []
        for p in script_paths:
            if os.path.isfile(p):
                valid_paths.append(p)
            else:
                print(f"⚠️ 脚本文件不存在，已跳过: {p}")
        
        if not valid_paths:
            print("❌ 没有有效的脚本文件可供回测")
            return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
        
        config_info = {
            'holding_periods': self.holding_periods,
            'top_n': self.top_n,
            'script_count': len(valid_paths),
            'screening_date': self._screening_date.strftime('%Y%m%d'),
        }
        
        if verbose:
            print("\n" + "=" * 80)
            print("🔬 筛选脚本回测")
            print("=" * 80)
            print(f"📁 待回测脚本数量: {len(valid_paths)}")
            print(f"📅 筛选日: {self._screening_date.strftime('%Y-%m-%d')}")
            print(f"⏱️ 持有期: {self.holding_periods}")
            print(f"🔢 每脚本返回: {self.top_n} 只")
            print("=" * 80)
        
        # 逐个回测脚本
        summary_list = []
        details_dict = {}
        
        for idx, script_path in enumerate(valid_paths, 1):
            script_name = os.path.basename(script_path)
            
            if verbose:
                print(f"\n{'=' * 80}")
                print(f"📌 [{idx}/{len(valid_paths)}] 回测脚本: {script_name}")
                print(f"   路径: {script_path}")
                print(f"{'=' * 80}")
            
            try:
                result = self._backtest_single_script(
                    script_path=script_path,
                    verbose=verbose,
                )
                summary_list.append(result['summary'])
                if result['detail'] is not None:
                    details_dict[result['summary']['logic_name']] = result['detail']
                    
            except Exception as e:
                print(f"   ❌ 回测失败: {e}")
                if verbose:
                    traceback.print_exc()
                summary_list.append({
                    'script': script_name,
                    'logic_name': script_name.replace('.py', ''),
                    'status': '失败',
                    'error': str(e),
                })
        
        # 输出汇总报告
        if verbose:
            self._print_summary_report(summary_list)
        
        return {
            'summary': summary_list,
            'details': details_dict,
            'script_paths': valid_paths,
            'config': config_info,
        }
    
    def _backtest_single_script(
        self,
        script_path: str,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        回测单个脚本的内部逻辑
        
        Args:
            script_path: 脚本文件路径
            verbose: 是否输出详细日志
            
        Returns:
            包含 summary 和 detail 的字典
        """
        script_name = os.path.basename(script_path)
        
        # 1. 加载脚本，获取筛选逻辑
        screening_logic = self.script_loader.get_screening_logic(script_path)
        
        if screening_logic is None:
            print(f"   ⚠️ 脚本中未找到 SCREENING_LOGIC")
            return {
                'summary': {
                    'script': script_name,
                    'logic_name': script_name.replace('.py', ''),
                    'status': '失败',
                    'error': '脚本缺少 SCREENING_LOGIC',
                },
                'detail': None,
            }
        
        logic_name = screening_logic.get('name', script_name.replace('.py', ''))
        
        if verbose:
            print(f"   📊 筛选名称: {logic_name}")
            print(f"   📝 说明: {screening_logic.get('rationale', 'N/A')}")
            print(f"   📐 表达式: {screening_logic.get('expression', 'N/A')}")
        
        # 2. 执行筛选
        if verbose:
            print(f"\n   🔍 执行筛选...")
        
        candidates = self.script_loader.execute_screening(
            script_path, self.data, top_n=self.top_n,
            holding_periods=self.holding_periods
        )
        
        if verbose:
            print(f"   ✅ 筛选完成，找到 {len(candidates)} 只股票")
        
        if not candidates:
            return {
                'summary': {
                    'script': script_name,
                    'logic_name': logic_name,
                    'status': '成功',
                    'stock_count': 0,
                    'note': '无符合条件的股票',
                },
                'detail': {
                    'script_path': script_path,
                    'screening_logic': screening_logic,
                    'candidates': [],
                    'returns': {},
                },
            }
        
        # 3. 计算收益率
        if verbose:
            print(f"\n   💰 计算各持有期收益率...")
        
        returns_result = self._calculate_holding_returns(candidates)
        
        # 4. 显示简要收益率统计
        ret_summary = returns_result.get('summary', {})
        if verbose:
            for period in self.holding_periods:
                stats = ret_summary.get(period, {})
                if stats.get('count', 0) > 0:
                    print(f"      {period}日: 平均收益 {stats['mean']:.2%}, "
                          f"胜率 {stats['win_rate']:.1%}, "
                          f"有效 {stats['valid_stocks']}/{stats['total_stocks']}")
                else:
                    print(f"      {period}日: 数据不足")
        
        # 5. 构建摘要
        summary_entry = {
            'script': script_name,
            'logic_name': logic_name,
            'status': '成功',
            'stock_count': len(candidates),
            'screening_date': returns_result.get('screening_date', 'N/A'),
        }
        for period in self.holding_periods:
            stats = ret_summary.get(period, {})
            summary_entry[f'平均收益({period}d)'] = stats.get('mean')
            summary_entry[f'胜率({period}d)'] = stats.get('win_rate')
        
        return {
            'summary': summary_entry,
            'detail': {
                'script_path': script_path,
                'screening_logic': screening_logic,
                'candidates': candidates,
                'returns': returns_result,
            },
        }
    
    def _calculate_holding_returns(
        self,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        计算候选股票在各持有期的未来收益率
        
        基于筛选日之后 N 个交易日的收盘价变动来计算收益率。
        
        Args:
            candidates: 候选股票列表
            
        Returns:
            收益率结果字典
        """
        screening_date = self._screening_date
        screening_date_str = screening_date.strftime('%Y%m%d')
        
        # 找到筛选日在日期列表中的位置
        try:
            screen_idx = list(self._all_dates).index(screening_date)
        except ValueError:
            print(f"   ⚠️ 筛选日 {screening_date_str} 不在数据中")
            return {'screening_date': screening_date_str, 'per_stock': [], 'summary': {}}
        
        # 逐只股票计算各持有期收益率
        per_stock_results = []
        
        for candidate in candidates:
            ts_code = candidate['ts_code']
            stock_name = candidate.get('name', ts_code)
            confidence = candidate.get('confidence', 0)
            
            stock_entry = {
                'ts_code': ts_code,
                'name': stock_name,
                'confidence': confidence,
            }
            
            # 获取该股票的历史数据
            try:
                stock_data = self.data.xs(ts_code, level='ts_code')
            except KeyError:
                for period in self.holding_periods:
                    stock_entry[f'ret_{period}d'] = None
                    stock_entry[f'ret_{period}d_note'] = '无数据'
                per_stock_results.append(stock_entry)
                continue
            
            # 获取筛选日的收盘价
            if screening_date not in stock_data.index:
                for period in self.holding_periods:
                    stock_entry[f'ret_{period}d'] = None
                    stock_entry[f'ret_{period}d_note'] = '筛选日无数据'
                per_stock_results.append(stock_entry)
                continue
            
            screen_close = stock_data.loc[screening_date, 'close']
            
            # 计算各持有期收益率
            for period in self.holding_periods:
                target_idx = screen_idx + period
                
                if target_idx < len(self._all_dates):
                    target_date = self._all_dates[target_idx]
                    if target_date in stock_data.index:
                        target_close = stock_data.loc[target_date, 'close']
                        ret = (target_close - screen_close) / screen_close
                        stock_entry[f'ret_{period}d'] = float(ret)
                        stock_entry[f'ret_{period}d_note'] = 'ok'
                    else:
                        stock_entry[f'ret_{period}d'] = None
                        stock_entry[f'ret_{period}d_note'] = '目标日无数据'
                else:
                    stock_entry[f'ret_{period}d'] = None
                    stock_entry[f'ret_{period}d_note'] = '数据不足'
            
            per_stock_results.append(stock_entry)
        
        # 计算汇总统计
        summary = {}
        for period in self.holding_periods:
            key = f'ret_{period}d'
            valid_rets = [s[key] for s in per_stock_results if s.get(key) is not None]
            
            if valid_rets:
                summary[period] = {
                    'count': len(valid_rets),
                    'mean': float(np.mean(valid_rets)),
                    'median': float(np.median(valid_rets)),
                    'std': float(np.std(valid_rets)),
                    'min': float(np.min(valid_rets)),
                    'max': float(np.max(valid_rets)),
                    'win_rate': float(sum(1 for r in valid_rets if r > 0) / len(valid_rets)),
                    'total_stocks': len(per_stock_results),
                    'valid_stocks': len(valid_rets),
                }
            else:
                summary[period] = {
                    'count': 0,
                    'mean': None,
                    'note': '无有效收益率数据（可能是最新数据不足）',
                }
        
        return {
            'screening_date': screening_date_str,
            'per_stock': per_stock_results,
            'summary': summary,
        }
    
    def _print_summary_report(self, summary_list: List[Dict]):
        """打印回测汇总报告"""
        print(f"\n\n{'=' * 80}")
        print("📋 回测汇总报告")
        print(f"{'=' * 80}")
        
        success_count = sum(1 for s in summary_list if s['status'] == '成功')
        fail_count = sum(1 for s in summary_list if s['status'] == '失败')
        print(f"\n   📊 总计: {len(summary_list)} 个脚本 | "
              f"✅ 成功: {success_count} | ❌ 失败: {fail_count}")
        
        if success_count > 0:
            # 构建表头
            header = f"   {'筛选名称':<25} {'股票数':>6}"
            for period in self.holding_periods:
                header += f" {f'平均{period}日':>10} {f'胜率{period}日':>8}"
            print(f"\n{header}")
            print(f"   {'-' * (31 + 19 * len(self.holding_periods))}")
            
            for s in summary_list:
                if s['status'] == '成功':
                    line = f"   {s['logic_name']:<25} {s.get('stock_count', 0):>6}"
                    for period in self.holding_periods:
                        avg_ret = s.get(f'平均收益({period}d)')
                        win_rate = s.get(f'胜率({period}d)')
                        line += f" {avg_ret:>10.2%}" if avg_ret is not None else f" {'N/A':>10}"
                        line += f" {win_rate:>8.1%}" if win_rate is not None else f" {'N/A':>8}"
                    print(line)
        
        if fail_count > 0:
            print(f"\n   ❌ 失败的脚本:")
            for s in summary_list:
                if s['status'] == '失败':
                    print(f"      - {s.get('logic_name', 'N/A')}: {s.get('error', '未知错误')}")
        
        print(f"\n{'=' * 80}")


# ==================== 便捷函数 ====================

def backtest_asking_scripts(
    script_paths: Union[str, List[str], None] = None,
    scripts_dir: Optional[str] = None,
    holding_periods: Optional[List[int]] = None,
    top_n: int = 20,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    回测 asking_scripts 目录下已有的筛选脚本（无需 AI 生成，直接执行已有脚本）
    
    支持三种使用方式：
    1. 指定单个脚本路径：backtest_asking_scripts("path/to/script.py")
    2. 指定多个脚本路径：backtest_asking_scripts(["script1.py", "script2.py"])
    3. 扫描目录所有脚本：backtest_asking_scripts()  # 默认扫描 asking_scripts 目录
    
    Args:
        script_paths: 筛选脚本路径，可以是：
            - None: 扫描 scripts_dir 目录下的所有脚本
            - str: 单个脚本文件路径
            - List[str]: 多个脚本文件路径列表
        scripts_dir: 筛选脚本目录（仅当 script_paths=None 时生效），
                     默认为 stock_asking_system/asking_scripts
        holding_periods: 持有期列表（天数），默认使用 StockQueryConfig.HOLDING_PERIODS
        top_n: 每个脚本返回的股票数量上限
        verbose: 是否输出详细日志
        
    Returns:
        回测结果字典：
        {
            'summary': List[Dict],       # 各脚本筛选汇总
            'details': Dict[str, Dict],  # 各脚本详细结果（按脚本名索引）
            'script_paths': List[str],   # 实际回测的脚本路径列表
            'config': Dict,              # 回测配置信息
        }
    """
    # 创建回测引擎
    backtester = AskingScriptBacktester(
        holding_periods=holding_periods,
        top_n=top_n,
    )
    
    if script_paths is None:
        # 扫描目录所有脚本
        return backtester.backtest_all(scripts_dir=scripts_dir, verbose=verbose)
    elif isinstance(script_paths, str):
        # 单个脚本
        return backtester.backtest_script(script_paths, verbose=verbose)
    elif isinstance(script_paths, (list, tuple)):
        # 多个脚本
        return backtester.backtest_scripts(list(script_paths), verbose=verbose)
    else:
        raise TypeError(f"script_paths 参数类型不支持: {type(script_paths)}，"
                        f"请传入 str / List[str] / None")


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 80)
    print("🔬 筛选脚本回测工具")
    print("=" * 80)
    
    # 如果命令行传入了脚本路径参数
    if len(sys.argv) > 1:
        scripts = sys.argv[1:]
        print(f"\n📁 指定回测脚本: {scripts}")
        
        # 如果传入的是文件名（非绝对路径），自动拼接 asking_scripts 目录
        resolved = []
        base_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'asking_scripts'
        )
        base_dir = os.path.abspath(base_dir)
        for s in scripts:
            if os.path.isabs(s):
                resolved.append(s)
            else:
                resolved.append(os.path.join(base_dir, s))
        
        result = backtest_asking_scripts(script_paths=resolved)
    else:
        print("\n📁 扫描 asking_scripts 目录下所有脚本...")
        result = backtest_asking_scripts()
    
    # 输出最终统计
    summary = result.get('summary', [])
    success = sum(1 for s in summary if s['status'] == '成功')
    fail = sum(1 for s in summary if s['status'] == '失败')
    print(f"\n🏁 回测完成！成功: {success}, 失败: {fail}")
