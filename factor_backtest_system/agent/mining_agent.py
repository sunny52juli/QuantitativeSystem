#!/usr/bin/env python3
"""
因子挖掘代理 - 协调整个因子挖掘流程

职责：
1. 管理因子挖掘器的生命周期
2. 提供因子生成和回测的完整流程
3. 生成优化建议
4. 格式化输出结果

工作流程：
1. 根据 prompt 生成因子定义
2. 将因子定义生成为可执行脚本，保存到 factor_scripts 目录
3. 使用 FactorScriptExecutor 执行因子计算和回测

改进：
- 使用依赖注入模式，便于测试和替换组件
- 使用自定义异常类进行更精确的错误处理
- 使用统一的日志系统
- 添加完整的类型注解
"""

import os
import traceback
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# 导入核心组件
from core.exceptions import (
    QuantSystemError,
    MissingAPIKeyError,
    FactorCalculationError,
    FactorBacktestError,
    DataLoadError,
)
from core.logger import get_logger, LoggerMixin

# 导入业务组件
from factor_backtest_system.agent.factor_miner import AIFactorMiner
from factor_backtest_system.generators.factor_script_generator import FactorScriptGenerator
from factor_backtest_system.backtest.factor_loader import FactorScriptExecutor, FactorScriptLoader
from datamodule.factor_data_loader import FactorDataLoader
from core.mcp.tools_selection import select_relevant_tools, load_mcp_tools
from factor_backtest_system.prompt.factor_prompts import get_message, get_optimization_suggestion
from config import FactorBacktestConfig

# 获取项目根目录和因子脚本目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
FACTOR_SCRIPTS_DIR = PROJECT_ROOT / "factor_backtest_system" / "factor_scripts"

# 类型别名
FactorDict = Dict[str, Any]
BacktestResult = Dict[str, Any]


class FactorMiningAgent(LoggerMixin):
    """
    因子挖掘代理类
    
    职责：
    1. 管理因子挖掘器的生命周期
    2. 提供因子生成和回测的完整流程
    3. 生成优化建议
    4. 格式化输出结果
    
    改进：
    - 支持依赖注入，便于测试
    - 使用自定义异常类
    - 集成日志系统
    """
    
    def __init__(
        self, 
        data: Optional[pd.DataFrame] = None, 
        api_key: Optional[str] = None,
        # 依赖注入参数
        data_loader: Optional[FactorDataLoader] = None,
        miner: Optional[AIFactorMiner] = None,
        script_executor: Optional[FactorScriptExecutor] = None,
        script_generator: Optional[FactorScriptGenerator] = None,
    ):
        """
        初始化因子挖掘代理
        
        Args:
            data: 股票数据 DataFrame，如果为None则从本地获取数据
            api_key: API密钥，如果为None则从环境变量读取
            data_loader: 数据加载器（可选，用于依赖注入）
            miner: 因子挖掘器（可选，用于依赖注入）
            script_executor: 脚本执行器（可选，用于依赖注入）
            script_generator: 脚本生成器（可选，用于依赖注入）
        
        Raises:
            MissingAPIKeyError: 当API密钥未配置时
            DataLoadError: 当数据加载失败时
        """
        # 获取API密钥
        self.api_key = api_key or os.environ.get('DEFAULT_API_KEY')
        
        if not self.api_key:
            raise MissingAPIKeyError()
        
        # 准备数据（使用依赖注入或创建新实例）
        if data is None:
            self.logger.info(get_message('INFO', 'generating_data'))
            try:
                self._data_loader = data_loader or FactorDataLoader()
                self.data = self._data_loader.load_backtest_data()
            except Exception as e:
                raise DataLoadError(f"数据加载失败: {e}")
        else:
            self._data_loader = data_loader
            self.data = data
        
        # 创建或使用注入的因子挖掘器
        self.miner = miner or AIFactorMiner(data=self.data, api_key=self.api_key)
        
        # 创建或使用注入的因子脚本执行器
        self.script_executor = script_executor or FactorScriptExecutor(data=self.data)
        
        # 创建或使用注入的因子脚本生成器
        self.script_generator = script_generator or FactorScriptGenerator(
            output_dir=str(FACTOR_SCRIPTS_DIR)
        )
        
        self.logger.info(get_message('INFO', 'agent_initialized'))
    
    def generate_factors(self, strategy: str, n_factors: int = 3) -> List[FactorDict]:
        """
        生成因子
        
        Args:
            strategy: 策略描述
            n_factors: 要生成的因子数量
            
        Returns:
            生成的因子列表
            
        Raises:
            FactorCalculationError: 当因子生成失败时
        """
        self.logger.info(get_message('INFO', 'generating_factors'))
        print(f"📊 策略: {strategy}")
        print(f"🎯 目标数量: {n_factors}")
        
        try:
            factors = self.miner.generate_factors(strategy, n_factors=n_factors)
        except Exception as e:
            self.logger.error(f"因子生成失败: {e}")
            raise FactorCalculationError(f"因子生成失败: {e}")
        
        if not factors:
            self.logger.warning(get_message('ERROR', 'factor_generation_failed'))
            return []
        
        self.logger.info(get_message('SUCCESS', 'factor_generated', count=len(factors)))
        self._display_factors(factors)
        
        return factors
    
    def generate_factor_scripts(
        self, 
        factors: List[FactorDict], 
        strategy_name: str = "default"
    ) -> List[str]:
        """
        生成因子脚本文件
        
        Args:
            factors: 因子列表
            strategy_name: 策略名称
            
        Returns:
            生成的脚本文件路径列表
        """
        print(f"\n{'='*80}")
        print(f"📝 生成因子计算脚本...")
        print(f"{'='*80}")
        
        script_paths = self.script_generator.batch_generate_scripts(
            factors=factors,
            strategy_name=strategy_name
        )
        
        self.logger.info(f"因子脚本生成完成: {len(script_paths)} 个文件")
        print(f"\n✅ 因子脚本生成完成")
        print(f"📁 脚本目录: {FACTOR_SCRIPTS_DIR}")
        print(f"📄 生成脚本数量: {len(script_paths)}")
        
        return script_paths
    
    def backtest_factors(
        self, 
        factors: List[FactorDict], 
        script_paths: Optional[List[str]] = None
    ) -> List[BacktestResult]:
        """
        批量回测因子（优先使用生成的脚本文件）
        
        Args:
            factors: 因子列表
            script_paths: 对应的脚本文件路径列表
            
        Returns:
            回测结果列表
        """
        self.logger.info(get_message('INFO', 'backtesting', count=len(factors)))
        
        # 判断使用哪种方式计算因子
        use_scripts = bool(script_paths and len(script_paths) == len(factors))
        
        if use_scripts:
            print(f"🔄 使用生成的脚本文件执行因子计算...")
        else:
            print(f"🔄 使用因子定义直接执行计算...")
        
        backtest_results: List[BacktestResult] = []
        
        # 创建脚本加载器（用于执行脚本）
        script_loader = FactorScriptLoader()
        
        for i, factor in enumerate(factors, 1):
            factor_name = factor.get('name', f'factor_{i}')
            self.logger.info(get_message(
                'INFO', 'backtesting_factor', 
                current=i, total=len(factors), name=factor_name
            ))
            
            try:
                # 计算因子值
                factor_values = self._calculate_factor_values(
                    factor=factor,
                    script_path=script_paths[i - 1] if use_scripts else None,
                    script_loader=script_loader
                )
                
                self.logger.info(get_message(
                    'SUCCESS', 'factor_computed', count=len(factor_values)
                ))
                
                # 执行回测
                backtest_result = self._run_backtest_with_factor_values(
                    factor_name=factor_name,
                    factor_values=factor_values,
                    factor_spec=factor
                )
                
                # 检查回测结果是否有效
                if backtest_result is None:
                    self.logger.error(f"因子 {factor_name} 回测返回None")
                    backtest_results.append({
                        'factor_name': factor_name,
                        'error': '回测失败，返回None'
                    })
                else:
                    backtest_results.append({
                        'factor_name': factor_name,
                        'backtest_result': backtest_result
                    })
                    self._display_backtest_result(backtest_result)
                
            except FactorCalculationError as e:
                self.logger.error(f"因子 {factor_name} 计算失败: {e}")
                backtest_results.append({
                    'factor_name': factor_name,
                    'error': str(e)
                })
            except FactorBacktestError as e:
                self.logger.error(f"因子 {factor_name} 回测失败: {e}")
                backtest_results.append({
                    'factor_name': factor_name,
                    'error': str(e)
                })
            except Exception as e:
                self.logger.error(f"因子 {factor_name} 处理异常: {e}", exc_info=True)
                print(f"   {get_message('ERROR', 'backtest_failed', error=str(e))}")
                traceback.print_exc()
                backtest_results.append({
                    'factor_name': factor_name,
                    'error': str(e)
                })
        
        return backtest_results
    
    def _calculate_factor_values(
        self,
        factor: FactorDict,
        script_path: Optional[str],
        script_loader: FactorScriptLoader
    ) -> pd.Series:
        """
        计算因子值
        
        Args:
            factor: 因子定义
            script_path: 脚本文件路径（可选）
            script_loader: 脚本加载器
            
        Returns:
            因子值 Series
            
        Raises:
            FactorCalculationError: 当计算失败时
        """
        try:
            if script_path:
                print(f"   📊 执行脚本文件: {script_path}")
                return script_loader.calculate_factor(script_path, self.data)
            else:
                print(f"   📊 使用因子定义计算因子值...")
                return self.script_executor.calculate_factor_from_definition(
                    factor=factor,
                    data=self.data
                )
        except Exception as e:
            raise FactorCalculationError(f"因子计算失败: {e}")
    
    def _run_backtest_with_factor_values(
        self, 
        factor_name: str, 
        factor_values: pd.Series, 
        factor_spec: FactorDict
    ) -> BacktestResult:
        """
        使用预计算的因子值执行回测
        
        Args:
            factor_name: 因子名称
            factor_values: 因子值 Series
            factor_spec: 因子定义
            
        Returns:
            回测结果字典
        """
        from factor_backtest_system.backtest.factor_backtest import FactorMiningFramework
        
        # 添加因子值到数据
        temp_data = self.data.copy()
        temp_data[factor_name] = factor_values
        
        # 计算未来收益率（适配双索引结构）
        temp_data_reset = temp_data.reset_index()
        temp_data_reset['ret'] = temp_data_reset.groupby('ts_code')['close'].pct_change().shift(-1)
        temp_data = temp_data_reset.set_index(['trade_date', 'ts_code'])
        
        # 创建回测框架
        framework = FactorMiningFramework()
        
        # 对所有配置的持有期进行回测
        holding_periods = FactorBacktestConfig.HOLDING_PERIODS
        print(f"   📊 测试多个持有期: {holding_periods}")
        
        all_results: Dict[str, BacktestResult] = {}
        for period in holding_periods:
            print(f"   ⏱️ 回测持有期: {period}天")
            period_results = framework.backtest_factor(
                temp_data,
                factor_name=factor_name,
                n_groups=5,
                holding_period=period
            )
            all_results[f'{period}d'] = period_results
        
        # 使用第一个持有期的结果作为主结果
        main_period = holding_periods[0]
        results = all_results[f'{main_period}d']
        
        results['factor_name'] = factor_name
        results['expression'] = factor_spec.get('expression', 'computed')
        results['all_holding_periods'] = all_results
        
        # 打印所有持有期的结果
        for i, period in enumerate(holding_periods):
            period_result = all_results[f'{period}d']
            
            if i == 0:
                print(f"\n{'='*80}")
                print(f"📊 主要持有期回测结果: {period}天")
                print(f"{'='*80}")
            else:
                print(f"\n{'='*80}")
                print(f"📊 持有期回测结果: {period}天")
                print(f"{'='*80}")
            
            framework.print_results(period_result)
        
        return results
    
    def generate_optimization_suggestions(
        self, 
        factors: List[FactorDict], 
        backtest_results: List[BacktestResult]
    ) -> List[Dict[str, Any]]:
        """
        生成因子优化建议
        
        Args:
            factors: 因子列表
            backtest_results: 回测结果列表
            
        Returns:
            优化建议列表
        """
        suggestions: List[Dict[str, Any]] = []
        
        for factor, result in zip(factors, backtest_results):
            factor_name = factor.get('name', 'unknown')
            
            if 'error' in result:
                suggestions.append({
                    'factor': factor_name,
                    'suggestions': [get_optimization_suggestion('computation_error')]
                })
                continue
            
            backtest = result.get('backtest_result', {})
            factor_suggestions = self._analyze_factor_performance(factor, backtest)
            
            suggestions.append({
                'factor': factor_name,
                'suggestions': factor_suggestions
            })
        
        return suggestions
    
    def run_complete_pipeline(
        self, 
        strategy: str, 
        n_factors: int = 3,
        strategy_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        运行完整的因子挖掘流程（新工作流）
        
        新工作流程：
        1. 根据 prompt 生成因子定义
        2. 将因子定义生成为脚本文件，保存到 factor_scripts 目录
        3. 使用 FactorScriptExecutor 执行因子计算和回测
        
        Args:
            strategy: 策略描述
            n_factors: 因子数量
            strategy_name: 策略名称（可选）
            
        Returns:
            完整的流程结果，失败时返回 None
        """
        self.logger.info(get_message('INFO', 'complete_pipeline'))
        print("="*80)
        print("🔄 新工作流程:")
        print("   1️⃣ 根据 prompt 生成因子定义")
        print("   2️⃣ 生成因子脚本文件到 factor_scripts 目录")
        print("   3️⃣ 使用脚本执行器进行回测")
        print("="*80)
        
        try:
            # 1. 生成因子定义
            print(f"\n{'='*80}")
            print("📌 步骤 1: 生成因子定义")
            print("="*80)
            factors = self.generate_factors(strategy, n_factors)
            
            if not factors:
                self.logger.warning("未生成任何因子")
                return None
            
            # 2. 生成因子脚本文件
            print(f"\n{'='*80}")
            print("📌 步骤 2: 生成因子脚本文件")
            print("="*80)
            if strategy_name is None:
                # 从策略描述中提取简短名称
                strategy_name = (
                    strategy.split('\n')[0]
                    .replace('生成', '')
                    .replace('的因子', '')
                    .replace('，重点关注：', '')
                    .strip()[:20]
                )
            
            script_paths = self.generate_factor_scripts(factors, strategy_name)
            
            # 3. 使用脚本执行器回测因子
            print(f"\n{'='*80}")
            print("📌 步骤 3: 使用脚本执行器回测因子")
            print("="*80)
            backtest_results = self.backtest_factors(factors, script_paths)
            
            # 4. 生成优化建议
            self.logger.info(get_message('INFO', 'optimization_suggestions'))
            optimization_suggestions = self.generate_optimization_suggestions(
                factors, backtest_results
            )
            self._display_optimization_suggestions(optimization_suggestions)
            
            return {
                'factors': factors,
                'script_paths': script_paths,
                'backtest_results': backtest_results,
                'optimization_suggestions': optimization_suggestions
            }
            
        except QuantSystemError as e:
            self.logger.error(f"流程执行失败: {e}", exc_info=True)
            print(get_message('ERROR', 'system_failed', error=str(e)))
            return None
        except Exception as e:
            self.logger.error(f"未知错误: {e}", exc_info=True)
            print(get_message('ERROR', 'system_failed', error=str(e)))
            traceback.print_exc()
            return None
    
    # ==================== 私有方法：显示和分析 ====================
    
    def _display_factors(self, factors: List[FactorDict]) -> None:
        """显示生成的因子"""
        for i, factor in enumerate(factors, 1):
            print(f"\n{i}. {factor.get('name', 'unknown')}")
            
            if factor.get('tools'):
                print(f"   工具步骤: {len(factor['tools'])}步")
                for tool in factor['tools']:
                    tool_name = tool.get('tool', 'unknown')
                    tool_params = tool.get('params', {})
                    print(f"      - {tool_name}({tool_params})")
            
            print(f"   表达式: {factor.get('expression', 'N/A')}")
            print(f"   逻辑: {factor.get('rationale', 'N/A')}")
    
    def _display_backtest_result(self, backtest_result: BacktestResult) -> None:
        """显示回测结果"""
        print(f"   📊 回测结果:")
        
        if not backtest_result:
            print("      - 回测结果为空")
            return
        
        metrics_data = backtest_result.get('metrics', {})
        long_short_metrics = metrics_data.get('group_long_short', {})
        
        if not long_short_metrics:
            print("      - 未找到多空组合指标")
            return
        
        metrics_mapping = [
            ('年化收益率', '年化收益率', '.2%'),
            ('夏普比率', '夏普比率', '.2f'),
            ('最大回撤', '最大回撤', '.2%'),
            ('胜率', '胜率', '.2%')
        ]
        
        for key, label, fmt in metrics_mapping:
            value = long_short_metrics.get(key, 'N/A')
            if isinstance(value, (int, float)):
                print(f"      - {label}: {value:{fmt}}")
            else:
                print(f"      - {label}: {value}")
    
    def _display_optimization_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """显示优化建议"""
        for item in suggestions:
            print(f"\n📌 {item['factor']}:")
            for suggestion in item['suggestions']:
                print(f"   • {suggestion}")
    
    def _analyze_factor_performance(
        self, 
        factor: FactorDict, 
        backtest: BacktestResult
    ) -> List[str]:
        """分析因子表现并生成建议"""
        suggestions: List[str] = []
        
        metrics_data = backtest.get('metrics', {})
        long_short_metrics = metrics_data.get('group_long_short', {})
        
        if not long_short_metrics:
            suggestions.append(get_optimization_suggestion('computation_error'))
            return suggestions
        
        # 收益率相关建议
        annual_return = long_short_metrics.get('年化收益率', 0)
        if annual_return < 0:
            suggestions.append(get_optimization_suggestion('poor_return'))
        elif annual_return < 0.1:
            suggestions.append(get_optimization_suggestion('low_return'))
        else:
            suggestions.append(get_optimization_suggestion('good_return'))
        
        # 风险相关建议
        sharpe_ratio = long_short_metrics.get('夏普比率', 0)
        if sharpe_ratio < 1:
            suggestions.append(get_optimization_suggestion('low_sharpe'))
        
        max_drawdown = long_short_metrics.get('最大回撤', 0)
        if abs(max_drawdown) > 0.2:
            suggestions.append(get_optimization_suggestion('high_drawdown'))
        
        # 工具复杂度建议
        if factor.get('tools') and len(factor['tools']) > 3:
            suggestions.append(get_optimization_suggestion('complex_tools'))
        
        return suggestions
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return load_mcp_tools()
    
    @staticmethod
    def select_tools_for_strategy(strategy: str) -> List[Dict[str, Any]]:
        """为策略选择相关工具"""
        all_tools = load_mcp_tools()
        return select_relevant_tools(strategy, all_tools)
