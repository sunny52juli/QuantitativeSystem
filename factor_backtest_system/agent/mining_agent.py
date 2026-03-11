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
from factor_backtest_system.agent.ai_factor_agent import AIFactorMiner
from factor_backtest_system.generators.factor_script_generator import FactorScriptGenerator
from factor_backtest_system.backtest.factor_loader import FactorScriptExecutor, FactorScriptLoader
from factor_backtest_system.backtest.backtest_report import print_single_factor_detail
from datamodule.factor_data_loader import FactorDataLoader
from core.mcp.tools_selection import select_relevant_tools, load_mcp_tools
from factor_backtest_system.prompt.factor_prompts import get_message
from factor_backtest_system.agent.rule_based_optimizer import generate_rule_based_suggestions
from factor_backtest_system.agent.llm_optimizer import LLMFactorOptimizer, optimize_factor_with_llm
from config import FactorBacktestConfig
from config.data_fields import FIELD_MAPPING, FUNCTION_MAPPING

# 获取项目根目录和因子脚本目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
FACTOR_SCRIPTS_DIR = PROJECT_ROOT / "factor_backtest_system" / "factor_scripts"

# 类型别名（在 factor_optimization_agent.py 中也定义了相同的别名以避免循环导入）
FactorDict = Dict[str, Any]
BacktestResult = Dict[str, Any]


def _display_rule_based_suggestions(optimization_results: Dict[str, Any]) -> None:
    """显示规则基础的优化建议报告"""
    print(f"\n{'='*80}")
    print("📊 因子优化建议详情")
    print(f"{'='*80}")
    
    for factor_name, result in optimization_results.items():
        print(f"\n📌 因子：{factor_name}")
        print(result['report'])


def _fallback_to_rule_based_analysis(factor: FactorDict, backtest_result: BacktestResult) -> Dict[str, Any]:
    """降级到规则基础分析"""
    # 使用规则基础优化作为后备
    temp_factors = [factor]
    temp_results = [backtest_result]
    
    rule_based_results = generate_rule_based_suggestions(temp_factors, temp_results)
    
    factor_name = factor.get('name', 'unknown')
    if factor_name in rule_based_results:
        return {
            'analysis': rule_based_results[factor_name],
            'report': rule_based_results[factor_name]['report'],
            'fallback': True
        }
    else:
        return {
            'analysis': {},
            'report': '❌ 无法生成优化建议',
            'fallback': True
        }


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
        使用预计算的因子值执行回测（优化版 - 避免重复加载数据）
            
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
            
        # 计算未来收益率（适配双索引结构，并计算所有持有期的收益率）
        temp_data_reset = temp_data.reset_index()
            
        # 计算所有配置的持有期收益率
        holding_periods = FactorBacktestConfig.HOLDING_PERIODS
        print(f"   📊 计算未来收益率，持有期：{holding_periods}")
        for period in holding_periods:
            ret_col = f'ret_{period}d'
            if ret_col not in temp_data_reset.columns:
                # 计算 period 天后的收益率
                temp_data_reset[ret_col] = temp_data_reset.groupby('ts_code')['close'].pct_change(period).shift(-period)
            
        # 默认使用 1 日收益率作为 ret 列（向后兼容）
        if 'ret' not in temp_data_reset.columns:
            temp_data_reset['ret'] = temp_data_reset['ret_1d'] if 'ret_1d' in temp_data_reset.columns else \
                                  temp_data_reset.groupby('ts_code')['close'].pct_change().shift(-1)
            
        temp_data = temp_data_reset.set_index(['trade_date', 'ts_code'])
            
        # ✅ 不创建新的 FactorMiningFramework 实例，直接使用已有数据进行回测
        # 创建临时的回测框架（不加载数据，直接使用已处理的数据）
        class SimpleBacktester:
            """简单回测器 - 使用已有数据执行回测，避免重复加载"""
            def __init__(self, data: pd.DataFrame, holding_periods: List[int]):
                self.data = data
                self.holding_periods = holding_periods
                self.field_mapping = FIELD_MAPPING
                self.function_mapping = FUNCTION_MAPPING
                
            def backtest_factor(self, data_with_factor, factor_name, n_groups=5, holding_period=1):
                """执行回测"""
                framework = FactorMiningFramework.__new__(FactorMiningFramework)  # 创建空实例
                framework.data = self.data
                framework.holding_periods = self.holding_periods
                framework.field_mapping = self.field_mapping
                framework.function_mapping = self.function_mapping
                # ✅ 直接回测，不再重新计算收益率
                return framework.backtest_factor(data_with_factor, factor_name, n_groups, holding_period)
            
        backtester = SimpleBacktester(temp_data, holding_periods)
            
        # 对所有配置的持有期进行回测
        print(f"   📊 测试多个持有期：{holding_periods}")
                
        # 诊断：检查每个持有期的有效样本数
        temp_data_check = temp_data.reset_index()
        print(f"   📈 总样本数：{len(temp_data_check)}")
        
        # 检查因子值的缺失情况
        factor_missing = temp_data_check[factor_name].isna().sum()
        factor_valid = temp_data_check[factor_name].notna().sum()
        print(f"   📊 {factor_name}: 有效={factor_valid:,}, 缺失={factor_missing:,} ({factor_missing/len(temp_data_check)*100:.1f}%)")
        
        for period in holding_periods:
            ret_col = f'ret_{period}d'
            if ret_col in temp_data_check.columns:
                valid_count = temp_data_check[ret_col].notna().sum()
                nan_count = temp_data_check[ret_col].isna().sum()
                print(f"   📊 {ret_col}: 有效={valid_count:,}, 缺失={nan_count:,} ({nan_count/len(temp_data_check)*100:.1f}%)")
        
        # 诊断：检查按日期的分组统计
        date_counts = temp_data_check.groupby('trade_date').agg({
            factor_name: ['count', 'sum', 'mean', 'std'],
        }).reset_index()
        print(f"   📅 按日期统计 - 最早日期：{date_counts['trade_date'].min()}, 最晚日期：{date_counts['trade_date'].max()}")
        print(f"   📅 有数据的日期数：{date_counts[factor_name]['count'].gt(0).sum()} / {len(date_counts)}")
                
        all_results: Dict[str, BacktestResult] = {}
        for period in holding_periods:
            print(f"   ⏱️ 回测持有期：{period}天")
            period_results = backtester.backtest_factor(
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
            
        # 打印所有持有期的结果（使用公共的报告模块）
        print_single_factor_detail(
            factor_name=factor_name,
            all_period_results=all_results,
            holding_periods=holding_periods,
            verbose=True
        )
            
        return results
    
    def _display_backtest_result(self, backtest_result: BacktestResult) -> None:
        """显示回测结果（简化版，仅显示主要指标）"""
        # 详细报告已在 print_single_factor_detail 中显示，这里只显示简短提示
        pass

    def generate_optimization_suggestions(
        self, 
        factors: List[FactorDict], 
        backtest_results: List[BacktestResult],
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        生成因子优化建议（支持LLM智能分析）
        
        Args:
            factors: 因子列表
            backtest_results: 回测结果列表
            use_llm: 是否使用LLM进行深度分析
            
        Returns:
            优化建议报告
        """
        if use_llm and self.api_key:
            # 使用LLM驱动的智能优化
            return self._generate_llm_optimization_suggestions(factors, backtest_results)
        else:
            # 使用规则基础的优化（降级方案）
            optimization_results = generate_rule_based_suggestions(factors, backtest_results)
            _display_rule_based_suggestions(optimization_results)
            return optimization_results
    
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
            print("📌 使用脚本执行器回测因子")
            print("="*80)
            backtest_results = self.backtest_factors(factors, script_paths)
            
            # 4. 生成优化建议
            self.logger.info(get_message('INFO', 'optimization_suggestions'))
            optimization_suggestions = self.generate_optimization_suggestions(
                factors, backtest_results
            )
            # 优化建议已经在 generate_optimization_suggestions 中显示过了
            
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
    
    def _generate_llm_optimization_suggestions(self, factors: List[FactorDict], 
                                             backtest_results: List[BacktestResult]) -> Dict[str, Any]:
        """
        使用LLM生成智能优化建议
        
        Args:
            factors: 因子列表
            backtest_results: 回测结果列表
            
        Returns:
            LLM优化建议结果
        """
        print(f"\n{'='*80}")
        print("🤖 启动LLM智能因子优化分析")
        print(f"{'='*80}")
        
        llm_optimizer = LLMFactorOptimizer(api_key=self.api_key)
        llm_results = {}
        
        for i, (factor, backtest_result) in enumerate(zip(factors, backtest_results)):
            factor_name = factor.get('name', f'factor_{i}')
            print(f"\n📌 分析因子 [{i+1}/{len(factors)}]: {factor_name}")
            
            try:
                # 提取回测结果中的关键信息
                actual_backtest_data = backtest_result.get('backtest_result', backtest_result)
                
                # 调用LLM进行深度分析
                optimization_result = llm_optimizer.analyze_and_optimize_factor(
                    factor_definition=factor,
                    backtest_results=actual_backtest_data
                )
                
                # 格式化并显示报告
                report = llm_optimizer.format_optimization_report(optimization_result)
                print(report)
                
                llm_results[factor_name] = {
                    'analysis': optimization_result,
                    'report': report
                }
                
            except Exception as e:
                self.logger.error(f"LLM优化分析失败 [{factor_name}]: {e}")
                print(f"❌ LLM分析失败: {e}")
                # 降级到规则基础分析
                fallback_result = _fallback_to_rule_based_analysis(factor, backtest_result)
                llm_results[factor_name] = fallback_result
        
        print(f"\n{'='*80}")
        print("✅ LLM智能优化分析完成")
        print(f"{'='*80}")
        
        return llm_results
    

    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return load_mcp_tools()
    
    @staticmethod
    def select_tools_for_strategy(strategy: str) -> List[Dict[str, Any]]:
        """为策略选择相关工具"""
        all_tools = load_mcp_tools()
        return select_relevant_tools(strategy, all_tools)
