#!/usr/bin/env python3
"""
筛选逻辑脚本: 放量突破股票

原始查询: 找出最近放量突破的股票：
    1. 成交量较前期放大（至少1.5倍）
    2. 涨幅>3%
    3. 技术形态良好
    

筛选说明:
    成交量较20日均量放大1.5倍以上，当日涨幅超过3%，且5日均线在20日均线之上，技术形态良好。

工具步骤:
    1. vol_ma20 = rolling_mean({'values': 'vol', 'window': 20})
    2. pct_1d = pct_change({'values': 'close', 'periods': 1})
    3. ma5 = rolling_mean({'values': 'close', 'window': 5})
    4. ma20 = rolling_mean({'values': 'close', 'window': 20})

筛选表达式: (vol > vol_ma20 * 1.5) & (pct_1d > 0.03) & (ma5 > ma20)
置信度公式: (pct_1d + (vol / vol_ma20 - 1) + (ma5 - ma20) / ma20) / 3

生成时间: 2026-03-03 00:04:14
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==================== 筛选逻辑定义 ====================
# 此定义用于 AskingScriptLoader 直接读取，确保与脚本逻辑一致
SCREENING_LOGIC = {
    "name": "放量突破股票",
    "tools": [
        {
            "tool": "rolling_mean",
            "params": {
                "values": "vol",
                "window": 20
            },
            "var": "vol_ma20"
        },
        {
            "tool": "pct_change",
            "params": {
                "values": "close",
                "periods": 1
            },
            "var": "pct_1d"
        },
        {
            "tool": "rolling_mean",
            "params": {
                "values": "close",
                "window": 5
            },
            "var": "ma5"
        },
        {
            "tool": "rolling_mean",
            "params": {
                "values": "close",
                "window": 20
            },
            "var": "ma20"
        }
    ],
    "expression": "(vol > vol_ma20 * 1.5) & (pct_1d > 0.03) & (ma5 > ma20)",
    "confidence_formula": "(pct_1d + (vol / vol_ma20 - 1) + (ma5 - ma20) / ma20) / 3",
    "rationale": "成交量较20日均量放大1.5倍以上，当日涨幅超过3%，且5日均线在20日均线之上，技术形态良好。"
}
# ==================== 筛选逻辑定义结束 ====================

# 原始查询
ORIGINAL_QUERY = """找出最近放量突破的股票：
    1. 成交量较前期放大（至少1.5倍）
    2. 涨幅>3%
    3. 技术形态良好
    """


def get_screening_logic() -> dict:
    """获取筛选逻辑定义（供加载器使用）"""
    return SCREENING_LOGIC


def screen_with_data(data: pd.DataFrame, top_n: int = 20, holding_periods: list = None) -> List[Dict[str, Any]]:
    """
    使用提供的数据执行筛选（供加载器使用）
    
    Args:
        data: 股票数据 DataFrame（双索引：trade_date, ts_code）
        top_n: 返回的股票数量上限
        holding_periods: 持有期列表（天数），传入后会将分析日期前移
        
    Returns:
        筛选结果列表，每项包含 ts_code, name, confidence, reason
    """
    from stock_asking_system.tools.stock_screener import StockScreener
    
    screener = StockScreener(data, holding_periods=holding_periods)
    return screener.execute_screening(
        screening_logic=SCREENING_LOGIC,
        top_n=top_n,
        query=ORIGINAL_QUERY
    )


def main():
    """主函数 - 独立运行时使用"""
    import argparse
    
    parser = argparse.ArgumentParser(description='放量突破股票 - 筛选脚本')
    parser.add_argument('--top_n', type=int, default=20, help='返回股票数量（默认20）')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 加载数据
    from datamodule.stock_data_loader import StockDataLoader
    
    print("📊 加载市场数据...")
    loader = StockDataLoader()
    data = loader.load_market_data()
    print(f"✅ 数据加载完成: {len(data)} 条记录")
    
    # 执行筛选
    print(f"\n🔍 执行筛选: 放量突破股票")
    results = screen_with_data(data, top_n=args.top_n)
    
    # 显示结果
    print(f"\n✅ 找到 {len(results)} 只符合条件的股票")
    print(f"{'排名':<6}{'股票代码':<12}{'股票名称':<20}{'置信度':<10}{'筛选理由'}")
    print("-" * 100)
    
    for i, stock in enumerate(results, 1):
        print(f"{i:<6}{stock['ts_code']:<12}{stock['name']:<20}{stock['confidence']:.2%}    {stock['reason']}")
    
    # 保存结果
    if args.output and results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"\n💾 结果已保存: {args.output}")


if __name__ == "__main__":
    main()
