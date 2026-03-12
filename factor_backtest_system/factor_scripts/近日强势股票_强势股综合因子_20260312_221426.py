#!/usr/bin/env python3
"""
因子计算脚本: 强势股综合因子

因子说明:
综合短期动量、RSI强度及量价相关性。动量捕捉趋势，RSI衡量超买超卖，量价相关性确保上涨有成交量配合，三者等权合成强势股因子。

生成时间: 2026-03-12 22:14:26
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data2parquet.data_interface import DataInterface
from core.mcp.tool_implementations import execute_tool
from core.mcp.expression_tools import ExpressionParser, NamespaceBuilder


# ==================== 因子定义 ====================
# 此定义用于回测系统直接读取，确保与脚本逻辑一致
FACTOR_DEFINITION = {
    "name": "强势股综合因子",
    "tools": [
        {
            "tool": "pct_change",
            "params": {
                "values": "收盘价",
                "periods": 10
            },
            "var": "mom_10"
        },
        {
            "tool": "rsi",
            "params": {
                "values": "收盘价",
                "window": 14
            },
            "var": "rsi_14"
        },
        {
            "tool": "correlation",
            "params": {
                "x": "mom_10",
                "y": "vol",
                "window": 10
            },
            "var": "mom_vol_corr"
        }
    ],
    "expression": "(mom_10 + (rsi_14 - 50) / 50 + mom_vol_corr) / 3",
    "rationale": "综合短期动量、RSI强度及量价相关性。动量捕捉趋势，RSI衡量超买超卖，量价相关性确保上涨有成交量配合，三者等权合成强势股因子。"
}
# ==================== 因子定义结束 ====================


def get_factor_definition() -> dict:
    """获取因子定义（供回测系统使用）"""
    return FACTOR_DEFINITION


def calculate_with_data(data: pd.DataFrame) -> pd.Series:
    """
    使用提供的数据计算因子值（供回测系统使用）
    
    Args:
        data: 股票数据 DataFrame（双索引：trade_date, ts_code）
        
    Returns:
        因子值 Series
    """
    from factor_backtest_system.backtest.factor_loader import FactorScriptExecutor
    
    executor = FactorScriptExecutor(data=data)
    return executor.calculate_factor_from_definition(FACTOR_DEFINITION, data)


class 强势股综合因子Calculator:
    """
    强势股综合因子
    
    因子说明:
    综合短期动量、RSI强度及量价相关性。动量捕捉趋势，RSI衡量超买超卖，量价相关性确保上涨有成交量配合，三者等权合成强势股因子。
    """
    
    def __init__(self):
        """初始化因子计算器"""
        self.factor_name = "强势股综合因子"
        self.data_interface = DataInterface()
        self.computed_vars = {}
    
    def calculate(self, trade_date: str) -> pd.DataFrame:
        """
        计算指定日期的因子值
        
        Args:
            trade_date: 交易日期，格式 'YYYYMMDD'
            
        Returns:
            包含 ts_code 和因子值的 DataFrame
        """
        print(f"\n================================================================================")
        print(f"📊 计算因子: {self.factor_name}")
        print(f"📅 日期: {trade_date}")
        print(f"================================================================================")
        
        # 1. 加载数据
        print(f"\n📥 加载数据...")
        data = self._load_data(trade_date)
        
        if data is None or len(data) == 0:
            print(f"❌ 无法加载 {trade_date} 的数据")
            return pd.DataFrame()
        
        print(f"✅ 数据加载完成: {len(data)} 条记录")
        print(f"   股票数量: {data.index.get_level_values('ts_code').nunique()}")
        
        # 2. 执行工具调用
        print(f"\n🔧 执行工具调用...")
        self.computed_vars = {}

        # 工具 1: pct_change
        print(f"   [1/3] 执行工具: pct_change")
        mom_10 = execute_tool(
            tool_name='pct_change',
            data=data,
            params={"values": "收盘价", "periods": 10},
            computed_vars=self.computed_vars
        )
        self.computed_vars['mom_10'] = mom_10
        print(f"      ✅ mom_10 计算完成")

        # 工具 2: rsi
        print(f"   [2/3] 执行工具: rsi")
        rsi_14 = execute_tool(
            tool_name='rsi',
            data=data,
            params={"values": "收盘价", "window": 14},
            computed_vars=self.computed_vars
        )
        self.computed_vars['rsi_14'] = rsi_14
        print(f"      ✅ rsi_14 计算完成")

        # 工具 3: correlation
        print(f"   [3/3] 执行工具: correlation")
        mom_vol_corr = execute_tool(
            tool_name='correlation',
            data=data,
            params={"x": "mom_10", "y": "vol", "window": 10},
            computed_vars=self.computed_vars
        )
        self.computed_vars['mom_vol_corr'] = mom_vol_corr
        print(f"      ✅ mom_vol_corr 计算完成")

        
        # 3. 计算因子表达式
        print(f"\n📐 计算因子表达式...")
        print(f"   原始表达式: (mom_10 + (rsi_14 - 50) / 50 + mom_vol_corr) / 3")
        
        # 解析表达式
        parsed_expr = ExpressionParser.parse_expression("(mom_10 + (rsi_14 - 50) / 50 + mom_vol_corr) / 3")
        print(f"   解析后表达式: {parsed_expr}")
        
        # 构建命名空间
        namespace = NamespaceBuilder.build_namespace(data, self.computed_vars)
        
        # 计算表达式
        try:
            factor_values = eval(parsed_expr, {"__builtins__": {}}, namespace)
            
            # 转换为 Series 并确保索引对齐
            if not isinstance(factor_values, pd.Series):
                factor_values = pd.Series(factor_values, index=data.index)
            elif not factor_values.index.equals(data.index):
                factor_values.index = data.index
            
            print(f"   ✅ 表达式计算成功")
            
        except Exception as e:
            print(f"   ❌ 表达式计算失败: {e}")
            print(f"   可用变量: {list(namespace.keys())}")
            raise
        
        # 4. 返回结果
        result_df = factor_values.to_frame(self.factor_name)
    
        print(f"\n✅ 因子计算完成")
        print(f"   有效值数量: {result_df[self.factor_name].notna().sum()}")
        print(f"   因子均值: {result_df[self.factor_name].mean():.4f}")
        print(f"   因子标准差: {result_df[self.factor_name].std():.4f}")
        print(f"================================================================================")
        
        return result_df
    
    def _load_data(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        加载指定日期的市场数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            市场数据 DataFrame（双索引：trade_date, ts_code）
        """
        try:
            # 获取历史数据（需要足够的历史数据来计算技术指标）
            from config import FactorBacktestConfig
            
            # 计算开始日期（向前推120个交易日，确保有足够的历史数据）
            from data2parquet.trade_calendar import TradeCalendar
            import tushare as ts
            
            # 创建 Tushare Pro API 实例
            pro_api = ts.pro_api(os.getenv('DATA_SOURCE_TOKEN'))
            calendar = TradeCalendar(pro_api)
            
            # 获取交易日历
            trade_dates = calendar.get_trade_dates(
                start_date=FactorBacktestConfig.BACKTEST_DEFAULT_START_DATE,
                end_date=trade_date
            )
            
            if not trade_dates or trade_date not in trade_dates:
                print(f"⚠️ {trade_date} 不是交易日")
                return None
            
            # 取最近120个交易日作为历史数据
            recent_dates = trade_dates[-120:] if len(trade_dates) >= 120 else trade_dates
            start_date = recent_dates[0]
            
            # 批量获取数据
            market_data_dict = self.data_interface.batch_get_market_data(
                start_date=start_date,
                end_date=trade_date
            )
            
            if not market_data_dict:
                return None
            
            # 合并所有日期的数据
            data = pd.concat(market_data_dict.values(), ignore_index=True)
            
            # 设置双索引
            data['trade_date'] = pd.to_datetime(data['trade_date'])
            data = data.sort_values(['trade_date', 'ts_code'])
            data = data.set_index(['trade_date', 'ts_code'])
            
            return data
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='强势股综合因子 - 因子计算脚本')
    parser.add_argument('--trade_date', type=str, default='20260227', help='交易日期，格式 YYYYMMDD')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 创建因子计算器
    calculator = 强势股综合因子Calculator()
    
    # 计算因子
    result = calculator.calculate(args.trade_date)
    
    # 保存结果
    if not result.empty:
        if args.output:
            output_path = args.output
        else:
            output_path = f"{calculator.factor_name}_{args.trade_date}.csv"
        
        result.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n💾 结果已保存: {output_path}")
    else:
        print(f"\n⚠️ 无结果数据")


if __name__ == "__main__":
    main()
