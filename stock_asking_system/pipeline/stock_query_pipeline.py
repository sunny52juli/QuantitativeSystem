#!/usr/bin/env python3
"""
股票查询 Pipeline - 股票筛选系统主入口

提供股票筛选的完整流程：
1. 数据加载
2. 工具选择
3. 筛选逻辑生成（Agent）
4. 生成筛选脚本到 asking_scripts 目录
5. 执行筛选
6. 计算筛选结果的持有期收益率
7. 结果展示
"""

import os
import traceback
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from core.mcp.tools_selection import select_relevant_tools, load_mcp_tools
from stock_asking_system.agent.screening_logic_agent import ScreeningLogicAgent
from stock_asking_system.tools.stock_screener import StockScreener
from stock_asking_system.generators.asking_script_generator import AskingScriptGenerator
from stock_asking_system.backtest.asking_script_loader import AskingScriptLoader
from datamodule.stock_data_loader import StockDataLoader
from config import StockQueryConfig


class StockQueryPipeline:
    """
    股票查询 Pipeline
    
    职责：
    1. 管理数据加载和初始化
    2. 协调筛选逻辑生成和执行
    3. 格式化输出结果
    
    示例：
        pipeline = StockQueryPipeline()
        results = pipeline.query("通信设备行业中放量上涨的股票")
    """
    
    def __init__(self):
        """
        初始化股票查询 Pipeline
        """

        # 1. 加载数据（使用 datamodule）

        self.data_loader = StockDataLoader()
        self.data = self.data_loader.load_market_data()

        # 2. 加载可用工具
        self.available_tools = load_mcp_tools()
        
        # 3. 获取数据中的实际行业列表
        self.available_industries = self._get_available_industries()
        
        # 4. 创建筛选逻辑 Agent（LLM 相关，配置从 prompt 读取）
        self.logic_agent = ScreeningLogicAgent()
        self.logic_agent.set_available_industries(self.available_industries)
        
        # 5. 创建股票筛选器（使用 tools 模块）
        # 注意：不传 holding_periods，使用最新日期；
        # run_complete_pipeline 中会根据 holding_periods 重新创建
        self.screener = StockScreener(self.data)
        
        # 6. 创建脚本生成器
        self.script_generator = AskingScriptGenerator()
        
        # 7. 创建脚本加载器
        self.script_loader = AskingScriptLoader()
        
        # 打印初始化信息
        self._print_init_info()
    
    def _print_init_info(self):
        """打印初始化信息"""
        print("✅ 股票查询 Pipeline 初始化完成")
        print(f"   可用工具: {len(self.available_tools)} 个")
        print(f"   可用行业: {len(self.available_industries)} 个")
        print(f"   数据范围: {self.data.index.get_level_values('trade_date').min()} ~ {self.data.index.get_level_values('trade_date').max()}")
        print(f"   股票数量: {self.data.index.get_level_values('ts_code').nunique()} 只")
    
    def _get_available_industries(self) -> List[str]:
        """
        获取数据中的实际行业列表
        
        Returns:
            行业名称列表（去重且排序）
        """
        # 优先使用 data_loader 的方法
        if self.data_loader is not None:
            return self.data_loader.get_available_industries()
        
        # 从数据中直接提取（兼容传入 data 的情况）
        if self.data is None or 'industry' not in self.data.columns:
            return []
        
        # 重置索引以访问 industry 列
        if isinstance(self.data.index, pd.MultiIndex):
            industries = self.data.reset_index()['industry'].dropna().unique()
        else:
            industries = self.data['industry'].dropna().unique()
        
        # 转换为字符串列表并排序
        industry_list = sorted([str(ind) for ind in industries if str(ind).strip()])
        
        return industry_list
    
    def query(self, query: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        执行股票查询（原有逻辑，不生成脚本，不计算收益率）
        
        工作流程：
        1. 选择相关工具
        2. 生成筛选逻辑
        3. 执行筛选
        4. 返回结果
        
        Args:
            query: 用户的自然语言查询
            top_n: 返回的股票数量上限
            
        Returns:
            符合条件的股票列表
        """
        print("\n" + "="*80)
        print(f"🔍 股票查询: {query}")
        print("="*80)
        
        try:
            # 1. 选择相关工具
            print("\n🔧 选择分析工具...")
            relevant_tools = select_relevant_tools(query, self.available_tools)
            print(f"   选中工具: {len(relevant_tools)} 个")
            
            # 2. 生成筛选逻辑（调用 LLM Agent）
            print("\n🤖 生成筛选逻辑...")
            screening_logic = self.logic_agent.generate(query, relevant_tools)
            
            if not screening_logic:
                print("❌ 无法生成筛选逻辑")
                return []
            
            self._display_screening_logic(screening_logic)
            
            # 3. 执行筛选
            print("\n📊 执行股票筛选...")
            candidates = self.screener.execute_screening(
                screening_logic=screening_logic,
                top_n=top_n,
                query=query
            )
            
            # 4. 显示结果
            print("\n🎯 筛选结果...")
            print("="*80)
            print(f"✅ 找到 {len(candidates)} 只符合条件的股票")
            print("="*80)
            
            self._display_results(candidates)
            
            return candidates
            
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            traceback.print_exc()
            return []
    
    def run_complete_pipeline(
        self, 
        query: str, 
        top_n: int = 20,
        holding_periods: Optional[List[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        运行完整流程：Agent 生成筛选逻辑 → 保存脚本 → 执行筛选 → 计算收益率
        
        工作流程：
        1. 选择相关工具
        2. Agent 生成筛选逻辑
        3. 将筛选逻辑保存为脚本文件到 asking_scripts 目录
        4. 执行筛选获取候选股票
        5. 计算候选股票在各持有期的收益率
        6. 输出完整报告
        
        Args:
            query: 用户的自然语言查询
            top_n: 返回的股票数量上限
            holding_periods: 持有期列表（天数），默认使用 StockQueryConfig.HOLDING_PERIODS
            
        Returns:
            完整流程结果字典，失败时返回 None
        """
        _holding_periods = holding_periods or StockQueryConfig.HOLDING_PERIODS
        
        print("\n" + "=" * 80)
        print("🔄 股票查询完整流程")
        print("=" * 80)
        print(f"📝 查询: {query}")
        print(f"🔢 返回数量: {top_n}")
        print(f"⏱️ 持有期: {_holding_periods} 天")
        print("=" * 80)
        print("\n工作流程:")
        print("   1️⃣  Agent 生成筛选逻辑")
        print("   2️⃣  保存筛选脚本到 asking_scripts 目录")
        print("   3️⃣  执行筛选获取候选股票")
        print("   4️⃣  计算候选股票各持有期收益率")
        print("=" * 80)
        
        try:
            # ==================== 步骤1: 生成筛选逻辑 ====================
            print(f"\n{'=' * 80}")
            print("📌 步骤 1: Agent 生成筛选逻辑")
            print("=" * 80)
            
            print("\n🔧 选择分析工具...")
            relevant_tools = select_relevant_tools(query, self.available_tools)
            print(f"   选中工具: {len(relevant_tools)} 个")
            
            print("\n🤖 生成筛选逻辑...")
            screening_logic = self.logic_agent.generate(query, relevant_tools)
            
            if not screening_logic:
                print("❌ 无法生成筛选逻辑")
                return None
            
            self._display_screening_logic(screening_logic)
            
            # ==================== 步骤2: 保存脚本 ====================
            print(f"\n{'=' * 80}")
            print("📌 步骤 2: 保存筛选脚本")
            print("=" * 80)
            
            script_path = self.script_generator.generate_script(
                screening_logic=screening_logic,
                query=query
            )
            
            # ==================== 步骤3: 执行筛选 ====================
            print(f"\n{'=' * 80}")
            print("📌 步骤 3: 执行筛选")
            print("=" * 80)
            
            # 创建带日期前移的筛选器（确保有足够的后续交易日计算收益率）
            screener_for_backtest = StockScreener(
                self.data, holding_periods=_holding_periods
            )
            
            candidates = screener_for_backtest.execute_screening(
                screening_logic=screening_logic,
                top_n=top_n,
                query=query
            )
            
            print(f"\n✅ 找到 {len(candidates)} 只符合条件的股票")
            self._display_results(candidates)
            
            # 更新筛选日（用于后续收益率计算）
            screening_date_for_returns = screener_for_backtest.latest_date
            
            if not candidates:
                print("⚠️ 无候选股票，跳过收益率计算")
                return {
                    'query': query,
                    'screening_logic': screening_logic,
                    'script_path': script_path,
                    'candidates': candidates,
                    'returns': {},
                }
            
            # ==================== 步骤4: 计算收益率 ====================
            print(f"\n{'=' * 80}")
            print("📌 步骤 4: 计算候选股票各持有期收益率")
            print("=" * 80)
            
            returns_result = self._calculate_holding_returns(
                candidates=candidates,
                holding_periods=_holding_periods,
                screening_date=screening_date_for_returns,
            )
            
            # ==================== 输出完整报告 ====================
            self._display_complete_report(
                query=query,
                screening_logic=screening_logic,
                candidates=candidates,
                returns_result=returns_result,
                holding_periods=_holding_periods,
                script_path=script_path,
            )
            
            return {
                'query': query,
                'screening_logic': screening_logic,
                'script_path': script_path,
                'candidates': candidates,
                'returns': returns_result,
            }
        
        except Exception as e:
            print(f"❌ 完整流程执行失败: {e}")
            traceback.print_exc()
            return None
    
    def _calculate_holding_returns(
        self,
        candidates: List[Dict[str, Any]],
        holding_periods: List[int],
        screening_date: Optional[pd.Timestamp] = None,
    ) -> Dict[str, Any]:
        """
        计算候选股票在各持有期的未来收益率
        
        基于筛选日之后 N 个交易日的收盘价变动来计算收益率。
        当 screening_date 指定时，使用该日期作为筛选日（通常已经前移以确保有足够后续数据）。
        如果未来数据不足，则标注为“数据不足”。
        
        Args:
            candidates: 候选股票列表（每项含 ts_code, name, confidence 等）
            holding_periods: 持有期列表（天数）
            screening_date: 筛选日（前移后的日期），为 None 时使用数据中的最新日期
            
        Returns:
            收益率结果字典：
            {
                'screening_date': str,                # 筛选日
                'per_stock': List[Dict],               # 每只股票各持有期的收益率
                'summary': Dict[int, Dict],            # 各持有期的汇总统计
            }
        """
        # 获取筛选日（优先使用传入的 screening_date，否则使用数据最新日期）
        if screening_date is None:
            screening_date = self.data.index.get_level_values('trade_date').max()
        screening_date_str = screening_date.strftime('%Y%m%d')
        
        print(f"\n   📅 筛选日: {screening_date.strftime('%Y-%m-%d')}")
        print(f"   ⏱️ 持有期: {holding_periods} 天")
        print(f"   📊 候选股票: {len(candidates)} 只")
        
        # 获取全部交易日列表（升序排列）
        all_dates = sorted(self.data.index.get_level_values('trade_date').unique())
        
        # 找到筛选日在日期列表中的位置
        try:
            screen_idx = list(all_dates).index(screening_date)
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
                for period in holding_periods:
                    stock_entry[f'ret_{period}d'] = None
                    stock_entry[f'ret_{period}d_note'] = '无数据'
                per_stock_results.append(stock_entry)
                continue
            
            # 获取筛选日的收盘价
            if screening_date not in stock_data.index:
                for period in holding_periods:
                    stock_entry[f'ret_{period}d'] = None
                    stock_entry[f'ret_{period}d_note'] = '筛选日无数据'
                per_stock_results.append(stock_entry)
                continue
            
            screen_close = stock_data.loc[screening_date, 'close']
            
            # 计算各持有期收益率
            for period in holding_periods:
                target_idx = screen_idx + period
                
                if target_idx < len(all_dates):
                    target_date = all_dates[target_idx]
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
        for period in holding_periods:
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
    
    def _display_complete_report(
        self,
        query: str,
        screening_logic: Dict,
        candidates: List[Dict],
        returns_result: Dict,
        holding_periods: List[int],
        script_path: str,
    ):
        """显示完整报告（含收益率）"""
        print(f"\n\n{'=' * 80}")
        print("📋 完整筛选报告")
        print(f"{'=' * 80}")
        print(f"\n   📝 查询: {query}")
        print(f"   📊 筛选条件: {screening_logic.get('name', 'N/A')}")
        print(f"   📁 脚本路径: {script_path}")
        print(f"   📅 筛选日: {returns_result.get('screening_date', 'N/A')}")
        print(f"   🎯 筛选结果: {len(candidates)} 只股票")
        
        # 汇总统计
        summary = returns_result.get('summary', {})
        if summary:
            print(f"\n   {'持有期':>8} {'平均收益':>10} {'中位数':>10} {'标准差':>10} {'最小值':>10} {'最大值':>10} {'胜率':>8} {'有效/总数':>10}")
            print(f"   {'-' * 78}")
            for period in holding_periods:
                stats = summary.get(period, {})
                if stats.get('count', 0) > 0:
                    print(f"   {period:>5}天  "
                          f"{stats['mean']:>10.2%} "
                          f"{stats['median']:>10.2%} "
                          f"{stats['std']:>10.2%} "
                          f"{stats['min']:>10.2%} "
                          f"{stats['max']:>10.2%} "
                          f"{stats['win_rate']:>8.1%} "
                          f"{stats['valid_stocks']}/{stats['total_stocks']:>5}")
                else:
                    print(f"   {period:>5}天  {'数据不足':>10}")
        
        # 逐只股票收益率
        per_stock = returns_result.get('per_stock', [])
        if per_stock:
            # 构建表头
            header = f"   {'排名':<5} {'代码':<12} {'名称':<16} {'置信度':>8}"
            for period in holding_periods:
                header += f" {f'{period}日收益':>10}"
            print(f"\n{header}")
            print(f"   {'-' * (47 + 11 * len(holding_periods))}")
            
            for i, stock in enumerate(per_stock, 1):
                line = f"   {i:<5} {stock['ts_code']:<12} {stock['name']:<16} {stock['confidence']:>8.2%}"
                for period in holding_periods:
                    ret = stock.get(f'ret_{period}d')
                    if ret is not None:
                        line += f" {ret:>10.2%}"
                    else:
                        note = stock.get(f'ret_{period}d_note', '无数据')
                        line += f" {note:>10}"
                print(line)
        
        print(f"\n{'=' * 80}")

    @staticmethod
    def _display_screening_logic(screening_logic: Dict):
        """显示筛选逻辑详情"""
        print(f"   筛选条件：{screening_logic.get('name', 'N/A')}")
        print(f"   工具步骤：{len(screening_logic.get('tools', []))} 步")
        
        print("\n📋 筛选逻辑详情:")
        print(f"   表达式：{screening_logic.get('expression', 'N/A')}")
        print(f"   置信度公式：{screening_logic.get('confidence_formula', 'N/A')}")
        
        if screening_logic.get('tools'):
            print("   工具调用:")
            for i, tool in enumerate(screening_logic['tools'], 1):
                print(f"      {i}. {tool.get('var')} = {tool.get('tool')}({tool.get('params', {})})")
   
    def generate_script_only(
       self,
       query: str,
       top_n: int = 20,
    ) -> Optional[Dict[str, Any]]:

        """
        仅生成筛选脚本，不执行筛选和回测

        工作流程：
        1. 选择相关工具
        2. Agent 生成筛选逻辑
        3. 将筛选逻辑保存为脚本文件到 asking_scripts 目录

        Args:
           query: 用户的自然语言查询
           top_n: 返回的股票数量上限（用于脚本中的默认值）

        Returns:
           结果字典：{'script_path': str, 'screening_logic': dict}, 失败时返回 None
        """

        print("\n" + "=" * 80)
        print("📝 生成筛选脚本")
        print("=" * 80)
        print(f"🔍 查询：{query}")
        print(f"🔢 默认返回数量：{top_n}")
        print("=" * 80)

        try:
           # 1. 选择相关工具
          print("\n🔧 选择分析工具...")
          relevant_tools = select_relevant_tools(query, self.available_tools)
          print(f"   选中工具：{len(relevant_tools)} 个")

           # 2. 生成筛选逻辑（调用 LLM Agent）
          print("\n🤖 生成筛选逻辑...")
          screening_logic = self.logic_agent.generate(query, relevant_tools)

          if not screening_logic:
            print("❌ 无法生成筛选逻辑")
            return None

          self._display_screening_logic(screening_logic)

           # 3. 保存脚本
          print("\n💾 保存筛选脚本...")
          script_path = self.script_generator.generate_script(
               screening_logic=screening_logic,
               query=query
           )

          print(f"\n✅ 脚本已保存：{os.path.basename(script_path)}")

          return {
               'script_path': script_path,
               'screening_logic': screening_logic,
           }

        except Exception as e:
          print(f"❌ 生成脚本失败：{e}")
          traceback.print_exc()
          return None

    @staticmethod
    def _display_results(results: List[Dict[str, Any]]):
        """显示查询结果"""
        if not results:
            print("\n❌ 未找到符合条件的股票")
            return
        
        print(f"\n{'排名':<6}{'股票代码':<12}{'股票名称':<20}{'置信度':<10}{'筛选理由'}")
        print("-" * 100)
        
        for i, stock in enumerate(results, 1):
            print(f"{i:<6}{stock['ts_code']:<12}{stock['name']:<20}{stock['confidence']:.2%}    {stock['reason']}")
    
    # ==================== 静态方法 ====================
    
    @staticmethod
    def get_available_tools() -> List[Dict]:
        """获取可用工具列表"""
        return load_mcp_tools()
    
    @staticmethod
    def select_tools_for_query(query: str) -> List[Dict]:
        """为查询选择相关工具"""
        all_tools = load_mcp_tools()
        return select_relevant_tools(query, all_tools)


# ==================== 便捷函数 ====================

def create_stock_query_pipeline() -> StockQueryPipeline:
    """创建股票查询 Pipeline 实例的便捷函数"""
    return StockQueryPipeline()


def query_stocks(query: str, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    快速查询股票（一次性调用，仅筛选，不保存脚本/不计算收益率）
    
    Args:
        query: 用户的自然语言查询
        top_n: 返回的股票数量上限
        
    Returns:
        符合条件的股票列表
    """
    pipeline = StockQueryPipeline()
    return pipeline.query(query, top_n=top_n)


def query_stocks_with_returns(
    query: str, 
    top_n: int = 20,
    holding_periods: Optional[List[int]] = None,
) -> Optional[Dict[str, Any]]:
    """
    完整流程：Agent 生成筛选逻辑 → 保存脚本 → 筛选 → 计算收益率
    
    Args:
        query: 用户的自然语言查询
        top_n: 返回的股票数量上限
        holding_periods: 持有期列表（天数），默认使用 StockQueryConfig.HOLDING_PERIODS
        
    Returns:
        完整流程结果字典，失败时返回 None
    """
    pipeline = StockQueryPipeline()
    return pipeline.run_complete_pipeline(
        query=query,
        top_n=top_n,
        holding_periods=holding_periods,
    )


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
    _holding_periods = holding_periods or StockQueryConfig.HOLDING_PERIODS
    
    # ==================== 1. 解析脚本路径 ====================
    loader = AskingScriptLoader(scripts_dir=scripts_dir)
    
    if script_paths is None:
        script_names = loader.list_scripts()
        if not script_names:
            print("⚠️ 未找到任何筛选脚本文件")
            return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
        resolved_paths = [
            os.path.join(loader.scripts_dir, name) for name in script_names
        ]
    elif isinstance(script_paths, str):
        resolved_paths = [script_paths]
    elif isinstance(script_paths, (list, tuple)):
        resolved_paths = list(script_paths)
    else:
        raise TypeError(f"script_paths 参数类型不支持: {type(script_paths)}")
    
    # 验证文件存在性
    valid_paths = []
    for p in resolved_paths:
        if os.path.isfile(p):
            valid_paths.append(p)
        else:
            print(f"⚠️ 脚本文件不存在，已跳过: {p}")
    
    if not valid_paths:
        print("❌ 没有有效的脚本文件可供回测")
        return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
    
    config_info = {
        'holding_periods': _holding_periods,
        'top_n': top_n,
        'script_count': len(valid_paths),
    }
    
    if verbose:
        print("\n" + "=" * 80)
        print("🔬 筛选脚本回测")
        print("=" * 80)
        print(f"📁 待回测脚本数量: {len(valid_paths)}")
        print(f"⏱️ 持有期: {_holding_periods}")
        print(f"🔢 每脚本返回: {top_n} 只")
        print("=" * 80)
    
    # ==================== 2. 加载数据 ====================
    if verbose:
        print("\n📥 加载市场数据...")
    
    data_loader = StockDataLoader()
    data = data_loader.load_market_data()
    
    if verbose:
        print(f"✅ 数据加载完成: {len(data)} 条记录")
    
    # 创建 pipeline 实例（复用收益率计算逻辑）
    temp_pipeline = StockQueryPipeline(data=data)
    
    # ==================== 3. 逐个回测脚本 ====================
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
            # 3.1 加载脚本，获取筛选逻辑
            screening_logic = loader.get_screening_logic(script_path)
            
            if screening_logic is None:
                print(f"   ⚠️ 脚本中未找到 SCREENING_LOGIC")
                summary_list.append({
                    'script': script_name,
                    'logic_name': script_name.replace('.py', ''),
                    'status': '失败',
                    'error': '脚本缺少 SCREENING_LOGIC',
                })
                continue
            
            logic_name = screening_logic.get('name', script_name.replace('.py', ''))
            
            if verbose:
                print(f"   📊 筛选名称: {logic_name}")
                print(f"   📝 说明: {screening_logic.get('rationale', 'N/A')}")
                print(f"   📐 表达式: {screening_logic.get('expression', 'N/A')}")
            
            # 3.2 执行筛选
            if verbose:
                print(f"\n   🔍 执行筛选...")
            
            candidates = loader.execute_screening(
                script_path, data, top_n=top_n,
                holding_periods=_holding_periods
            )
            
            if verbose:
                print(f"   ✅ 筛选完成，找到 {len(candidates)} 只股票")
            
            if not candidates:
                summary_list.append({
                    'script': script_name,
                    'logic_name': logic_name,
                    'status': '成功',
                    'stock_count': 0,
                    'note': '无符合条件的股票',
                })
                details_dict[logic_name] = {
                    'script_path': script_path,
                    'screening_logic': screening_logic,
                    'candidates': [],
                    'returns': {},
                }
                continue
            
            # 3.3 计算收益率
            if verbose:
                print(f"\n   💰 计算各持有期收益率...")
            
            # 计算前移后的筛选日（与 StockScreener 保持一致）
            all_dates_sorted = sorted(data.index.get_level_values('trade_date').unique())
            max_period = max(_holding_periods)
            offset_idx = len(all_dates_sorted) - 1 - max_period
            if offset_idx >= 0:
                screening_date_for_ret = all_dates_sorted[offset_idx]
            else:
                screening_date_for_ret = all_dates_sorted[-1]
            
            returns_result = temp_pipeline._calculate_holding_returns(
                candidates=candidates,
                holding_periods=_holding_periods,
                screening_date=screening_date_for_ret,
            )
            
            # 3.4 提取摘要
            ret_summary = returns_result.get('summary', {})
            summary_entry = {
                'script': script_name,
                'logic_name': logic_name,
                'status': '成功',
                'stock_count': len(candidates),
                'screening_date': returns_result.get('screening_date', 'N/A'),
            }
            for period in _holding_periods:
                stats = ret_summary.get(period, {})
                summary_entry[f'平均收益({period}d)'] = stats.get('mean')
                summary_entry[f'胜率({period}d)'] = stats.get('win_rate')
            
            summary_list.append(summary_entry)
            
            details_dict[logic_name] = {
                'script_path': script_path,
                'screening_logic': screening_logic,
                'candidates': candidates,
                'returns': returns_result,
            }
            
            # 显示简要收益率统计
            if verbose:
                for period in _holding_periods:
                    stats = ret_summary.get(period, {})
                    if stats.get('count', 0) > 0:
                        print(f"      {period}日: 平均收益 {stats['mean']:.2%}, "
                              f"胜率 {stats['win_rate']:.1%}, "
                              f"有效 {stats['valid_stocks']}/{stats['total_stocks']}")
                    else:
                        print(f"      {period}日: 数据不足")
            
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
    
    # ==================== 4. 输出汇总报告 ====================
    if verbose:
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
            for period in _holding_periods:
                header += f" {f'平均{period}日':>10} {f'胜率{period}日':>8}"
            print(f"\n{header}")
            print(f"   {'-' * (31 + 19 * len(_holding_periods))}")
            
            for s in summary_list:
                if s['status'] == '成功':
                    line = f"   {s['logic_name']:<25} {s.get('stock_count', 0):>6}"
                    for period in _holding_periods:
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
    
    return {
        'summary': summary_list,
        'details': details_dict,
        'script_paths': valid_paths,
        'config': config_info,
    }
