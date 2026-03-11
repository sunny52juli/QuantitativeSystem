#!/usr/bin/env python3
"""
回测报告格式化输出模块

提供统一的回测报告格式化输出功能，用于显示详细的回测结果信息。
"""

from typing import Dict, List, Any


def print_detailed_backtest_report(
    title: str,
    screening_date: str,
    candidates: List[Dict[str, Any]],
    returns_result: Dict[str, Any],
    holding_periods: List[int],
):
    """
    打印详细回测报告（按用户要求的格式）
    
    Args:
        title: 报告标题（查询语句或筛选逻辑名称）
        screening_date: 筛选日字符串（YYYYMMDD）
        candidates: 候选股票列表
        returns_result: 收益率计算结果字典
        holding_periods: 持有期列表（天数）
    
    输出格式示例：
    ================================================================================
    📊 回测详情：放量突破股票
    ================================================================================
    
     筛选日：20260303
        筛选结果：20 只股票
    
            持有期       平均收益        中位数        标准差        最小值        最大值       胜率      有效/总数
       ----------------------------------------------------------------------------------------------
          1 天     -10.53%     -11.51%       5.90%     -21.23%       4.60%      5.0%       20/20
         5 天     -15.72%     -14.98%       8.29%     -31.55%       4.91%      5.0%       20/20
    
       排名    代码           名称                    置信度      1 日收益      5 日收益
       ----------------------------------------------------------------------------------------
     1     920260.BJ      中寰股份                     94.11%       -16.04%       -21.75%
      2     920717.BJ      瑞星股份                     85.26%       -15.47%       -20.62%
      3     920351.BJ      华光源海                     82.73%       -21.23%       -29.90%
    
    ================================================================================
    """
    per_stock = returns_result.get('per_stock', [])
    summary = returns_result.get('summary', {})
    
    print(f"\n{'=' * 80}")
    print(f"📊 回测详情：{title}")
    print(f"{'=' * 80}")
    
    # 1. 筛选日和筛选结果
    print(f"\n 筛选日：{screening_date}")
    print(f"    筛选结果：{len(candidates)} 只股票")
    
    # 2. 持有期收益统计表格
    if summary:
        print(f"\n        持有期       平均收益        中位数        标准差        最小值        最大值       胜率      有效/总数")
        print(f"   {'-' * 94}")
        
        for period in holding_periods:
            stats = summary.get(period, {})
            if stats.get('count', 0) > 0:
                mean_ret = f"{stats['mean']:.2%}".rjust(10)
                median_ret = f"{stats['median']:.2%}".rjust(10)
                std_ret = f"{stats['std']:.2%}".rjust(10)
                min_ret = f"{stats['min']:.2%}".rjust(10)
                max_ret = f"{stats['max']:.2%}".rjust(10)
                win_rate = f"{stats['win_rate']:.1%}".rjust(8)
                valid_total = f"{stats['valid_stocks']:>2}/{stats['total_stocks']:<2}".rjust(10)
                
                print(f"       {period}天  {mean_ret}  {median_ret}  {std_ret}  {min_ret}  {max_ret}  {win_rate}  {valid_total}")
            else:
                print(f"       {period}天  {'数据不足':>10}")
    
    # 3. 个股排名表格
    if per_stock:
        # 构建表头
        header = f"   排名    代码           名称                    置信度"
        for period in holding_periods:
            header += f"       {period}日收益"
        print(f"\n{header}")
        print(f"   {'-' * (11 +15 +22 +12 +14 * len(holding_periods))}")
        
        for i, stock in enumerate(per_stock, 1):
            line = f"   {i:<5} {stock['ts_code']:<14} {stock['name']:<22} {stock['confidence']:>8.2%}"
            for period in holding_periods:
                ret = stock.get(f'ret_{period}d')
                if ret is not None:
                    line += f" {ret:>13.2%}"
                else:
                    note = stock.get(f'ret_{period}d_note', '无数据')
                    line += f" {note:>13}"
            print(line)
    
    print(f"\n{'=' * 80}")


def print_backtest_summary(
    summary_list: List[Dict[str, Any]],
    holding_periods: List[int],
):
    """
    打印回测汇总报告（多个脚本的汇总统计）
    
    Args:
        summary_list: 各脚本的筛选汇总列表
        holding_periods: 持有期列表（天数）
    
    输出格式示例：
    ================================================================================
    📋 回测汇总报告
    ================================================================================
    
       📊 总计：3 个脚本 | ✅ 成功：3 | ❌ 失败：0
    
       筛选名称                   股票数     平均 1 日   胜率 1 日     平均 5 日   胜率 5 日
       --------------------------------------------------------------
       放量突破股票                   20      -10.53%     5.0%      -15.72%    5.0%
       ...
    ================================================================================
    """
    print(f"\n\n{'=' * 80}")
    print("📋 回测汇总报告")
    print(f"{'=' * 80}")
    
    success_count = sum(1 for s in summary_list if s['status'] == '成功')
    fail_count = sum(1 for s in summary_list if s['status'] == '失败')
    print(f"\n   📊 总计：{len(summary_list)} 个脚本 | "
          f"✅ 成功：{success_count} | ❌ 失败：{fail_count}")
    
    if success_count > 0:
        # 构建表头
        header= f"   {'筛选名称':<25} {'股票数':>6}"
        for period in holding_periods:
            header += f" {f'平均{period}日':>10} {f'胜率{period}日':>8}"
        print(f"\n{header}")
        print(f"   {'-' * (31 + 19 * len(holding_periods))}")
        
        for s in summary_list:
            if s['status'] == '成功':
                line = f"   {s['logic_name']:<25} {s.get('stock_count', 0):>6}"
                for period in holding_periods:
                    avg_ret = s.get(f'平均收益 ({period}d)')
                    win_rate = s.get(f'胜率 ({period}d)')
                    line += f" {avg_ret:>10.2%}" if avg_ret is not None else f" {'N/A':>10}"
                    line += f" {win_rate:>8.1%}" if win_rate is not None else f" {'N/A':>8}"
                print(line)
    
    if fail_count > 0:
        print(f"\n   ❌ 失败的脚本:")
        for s in summary_list:
            if s['status'] == '失败':
                print(f"      - {s.get('logic_name', 'N/A')}: {s.get('error', '未知错误')}")
    
    print(f"\n{'=' * 80}")
