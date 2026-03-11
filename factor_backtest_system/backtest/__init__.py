"""
回测分析模块
提供因子回测和性能评估功能，包含：
- FactorMiningFramework: 因子回测引擎
- FactorScriptLoader: 因子脚本加载器
- FactorScriptExecutor: 因子脚本执行器
- backtest_factor_scripts: 独立回测入口函数
- backtest_report: 回测报告格式化输出
"""

from .factor_backtest import FactorMiningFramework
from .factor_loader import FactorScriptLoader, FactorScriptExecutor
from .run_scrip_backtest import backtest_factor_scripts
from .backtest_report import print_factor_backtest_summary, print_single_factor_detail

__all__ = [
    'FactorMiningFramework',
    'FactorScriptLoader',
    'FactorScriptExecutor',
    'backtest_factor_scripts',
    'print_factor_backtest_summary',
    'print_single_factor_detail',
]
