#!/usr/bin/env python3
"""因子回测报告格式化输出模块"""

from typing import Dict, List, Any


def print_factor_backtest_summary(
    summary_list: List[Dict[str, Any]],
    holding_periods: List[int],
):
    """打印因子回测汇总报告"""
    print(f"\n\n{'=' * 80}")
    print("📋 因子回测汇总报告")
    print(f"{'=' * 80}")
    
    success_count = sum(1 for s in summary_list if s['status'] == '成功')
    fail_count= sum(1 for s in summary_list if s['status'] == '失败')
    print(f"\n  📊 总计：{len(summary_list)} 个因子 | "
          f"✅ 成功：{success_count} | ❌ 失败：{fail_count}")
    
    if success_count > 0:
        main_period = holding_periods[0]
        header = (f"   {'因子名称':<25} "
                 f"{'年化收益率':>12} "
                 f"{'夏普比率':>10} "
                f"{'最大回撤':>10} "
                f"{'胜率':>10}")
        print(f"\n{header}")
        print(f"   {'-' * 67}")
        
    for s in summary_list:
            if s['status'] == '成功':
                ann_ret = s.get(f'年化收益率 ({main_period}d)', 0) or 0
                sharpe = s.get(f'夏普比率 ({main_period}d)', 0) or 0
                max_dd = s.get(f'最大回撤 ({main_period}d)', 0) or 0
                win_rate = s.get(f'胜率 ({main_period}d)', 0) or 0
                print(f"   {s['factor_name']:<25} "
                    f"{ann_ret:>11.2%} "
                      f"{sharpe:>10.3f} "
                     f"{max_dd:>10.2%} "
                     f"{win_rate:>10.2%}")
    
    if fail_count > 0:
        print(f"\n  ❌ 失败的因子:")
        for s in summary_list:
            if s['status'] == '失败':
                print(f"      - {s['factor_name']}: {s.get('error', '未知错误')}")
    
    print(f"\n{'=' * 80}")


def print_single_factor_detail(
    factor_name: str,
    all_period_results: Dict[str, Any],
    holding_periods: List[int],
    verbose: bool = True,
):
        """打印单个因子详细回测报告"""
        if not verbose:
            return

        print(f"\n{'=' * 80}")
        print(f"📊 因子详情：{factor_name}")
        print(f"{'=' * 80}")

        for period in holding_periods:
            period_key = f'{period}d'
            if period_key not in all_period_results:
                continue

            result = all_period_results[period_key]
            metrics = result.get('metrics', {}).get('group_long_short', {})

            if not metrics:
                print(f"\n⚠️ 持有期 {period}天：无有效数据")
                continue

            print(f"\n⏱️ 持有期：{period} 天")

        if metrics.get('年化收益率'):
            print(f"   年化收益率：{metrics.get('年化收益率', 'N/A'):.2%}")
        else:
            print(f"   年化收益率：N/A")
        if metrics.get('夏普比率'):
            print(f"   夏普比率：{metrics.get('夏普比率', 'N/A'):.3f}")
        else:
            print(f"   夏普比率：N/A")
        if metrics.get('最大回撤'):
            print(f"   最大回撤：{metrics.get('最大回撤', 'N/A'):.2%}")
        else:
            print(f"   最大回撤：N/A")
        if metrics.get('胜率'):
            print(f"   胜率：{metrics.get('胜率', 'N/A'):.2%}")
        else:
            print(f"   胜率：N/A")
        
        group_stats = result.get('group_stats', [])
        if group_stats and verbose:
            print(f"\n  分组收益（第 1 组为最低分组，第{len(group_stats)}组为最高分组）:")
            print(f"   {'组别':<8} {'股票数':>8} {'平均收益':>12} {'累计收益':>12}")
            print(f"   {'-' * 42}")
            for i, stats in enumerate(group_stats, 1):
                stock_count = int(stats.get('count', 0))
                mean_ret = stats.get('mean_return', 0)
                cum_ret = stats.get('cumulative_return', 0)
                print(f"   {i:<8} {stock_count:>8} {mean_ret:>11.2%} {cum_ret:>11.2%}")
    
        print(f"\n{'=' * 80}")
