#!/usr/bin/env python3
"""
因子计算脚本: 强势股综合因子

因子说明:
综合短期动量、价格突破（接近20日高点）、RSI强势（>50）、成交量增长以及较低的波动率，构建强势股识别因子。正因子值越高表示股票越强势。

生成时间: 2026-03-02 23:54:07
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Optional

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
            "var": "mom10"
        },
        {
            "tool": "rolling_max",
            "params": {
                "values": "收盘价",
                "window": 20
            },
            "var": "high20"
        },
        {
            "tool": "rsi",
            "params": {
                "values": "收盘价",
                "window": 14
            },
            "var": "rsi14"
        },
        {
            "tool": "pct_change",
            "params": {
                "values": "vol",
                "periods": 5
            },
            "var": "vol_mom5"
        },
        {
            "tool": "rolling_std",
            "params": {
                "values": "收盘价",
                "window": 20
            },
            "var": "volatility20"
        }
    ],
    "expression": "(mom10 * 0.3) + ((收盘价 - high20) / (high20 + 0.0001) * 0.25) + ((rsi14 - 50) / 50 * 0.2) + (vol_mom5 * 0.15) - (volatility20 * 0.1)",
    "rationale": "综合短期动量、价格突破（接近20日高点）、RSI强势（>50）、成交量增长以及较低的波动率，构建强势股识别因子。正因子值越高表示股票越强势。"
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
    综合短期动量、价格突破（接近20日高点）、RSI强势（>50）、成交量增长以及较低的波动率，构建强势股识别因子。正因子值越高表示股票越强势。
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
        print(f"   [1/5] 执行工具: pct_change")
        mom10 = execute_tool(
            tool_name='pct_change',
            data=data,
            params={"values": "收盘价", "periods": 10},
            computed_vars=self.computed_vars
        )
        self.computed_vars['mom10'] = mom10
        print(f"      ✅ mom10 计算完成")

        # 工具 2: rolling_max
        print(f"   [2/5] 执行工具: rolling_max")
        high20 = execute_tool(
            tool_name='rolling_max',
            data=data,
            params={"values": "收盘价", "window": 20},
            computed_vars=self.computed_vars
        )
        self.computed_vars['high20'] = high20
        print(f"      ✅ high20 计算完成")

        # 工具 3: rsi
        print(f"   [3/5] 执行工具: rsi")
        rsi14 = execute_tool(
            tool_name='rsi',
            data=data,
            params={"values": "收盘价", "window": 14},
            computed_vars=self.computed_vars
        )
        self.computed_vars['rsi14'] = rsi14
        print(f"      ✅ rsi14 计算完成")

        # 工具 4: pct_change
        print(f"   [4/5] 执行工具: pct_change")
        vol_mom5 = execute_tool(
            tool_name='pct_change',
            data=data,
            params={"values": "vol", "periods": 5},
            computed_vars=self.computed_vars
        )
        self.computed_vars['vol_mom5'] = vol_mom5
        print(f"      ✅ vol_mom5 计算完成")

        # 工具 5: rolling_std
        print(f"   [5/5] 执行工具: rolling_std")
        volatility20 = execute_tool(
            tool_name='rolling_std',
            data=data,
            params={"values": "收盘价", "window": 20},
            computed_vars=self.computed_vars
        )
        self.computed_vars['volatility20'] = volatility20
        print(f"      ✅ volatility20 计算完成")

        
        # 3. 计算因子表达式
        print(f"\n📐 计算因子表达式...")
        print(f"   原始表达式: (mom10 * 0.3) + ((收盘价 - high20) / (high20 + 0.0001) * 0.25) + ((rsi14 - 50) / 50 * 0.2) + (vol_mom5 * 0.15) - (volatility20 * 0.1)")
        
        # 解析表达式
        parsed_expr = ExpressionParser.parse_expression("(mom10 * 0.3) + ((收盘价 - high20) / (high20 + 0.0001) * 0.25) + ((rsi14 - 50) / 50 * 0.2) + (vol_mom5 * 0.15) - (volatility20 * 0.1)")
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
        result_df = pd.DataFrame({
            'ts_code': factor_values.index.get_level_values('ts_code'),
            'trade_date': trade_date,
            self.factor_name: factor_values.values
        })
        
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
            from dataloader.trade_calendar import TradeCalendar
            import tushare as ts
            
            # 创建 Tushare Pro API 实例
            pro_api = ts.pro_api()
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
    parser.add_argument('trade_date', type=str, default='20260227', help='交易日期，格式 YYYYMMDD')
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
