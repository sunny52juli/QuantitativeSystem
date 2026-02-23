#!/usr/bin/env python3
"""
股票筛选工具 - 高性能的股票筛选执行引擎

所属模块: tools（工具层）
职责: 执行筛选逻辑，不涉及 LLM 交互

核心优化：
1. 预筛选机制：先按行业、市场等条件缩小股票池
2. 批量计算：对筛选后的股票池批量计算指标
3. 向量化处理：利用 pandas 向量化避免逐股循环

示例：
    from stock_asking_system.tools import StockScreener
    screener = StockScreener(data)
    results = screener.execute_screening(screening_logic, top_n=20)
"""

import time as _time
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime

from core.mcp.tool_implementations import execute_tool as execute_tool_impl
from core.mcp.expression_tools import NamespaceBuilder

# 预筛选工具名称常量
_PRE_FILTER_TOOLS = frozenset(['filter_by_industry', 'filter_by_market'])


class StockScreener:
    """
    股票筛选执行器 - 负责高效执行筛选逻辑
    
    核心功能：
    1. 预筛选：识别并优先执行行业、市场等过滤条件
    2. 批量计算：对筛选后的股票池批量计算技术指标
    3. 结果排序：按置信度排序并返回Top N
    
    优化策略：
    - 先执行低成本的过滤（行业、市场、市值等）
    - 再执行高成本的技术指标计算
    - 减少不必要的计算量
    
    日期前移策略：
    - 当指定 holding_periods 时，自动将分析日期前移 max(holding_periods) 个交易日
    - 确保筛选日之后有足够的数据来计算持有期收益率
    """
    
    def __init__(self, data: pd.DataFrame, holding_periods: Optional[List[int]] = None):
        """
        初始化筛选器
        
        Args:
            data: 股票数据 DataFrame（双索引：trade_date, ts_code）
            holding_periods: 持有期列表（天数），如 [1, 5]。
                当指定时，分析日期会自动前移 max(holding_periods) 个交易日，
                确保筛选日之后有足够数据来计算收益率。
                为 None 时使用数据中的最新日期。
        """
        self.data = data
        self.namespace_builder = NamespaceBuilder()
        
        # 获取所有交易日（升序排列）
        all_dates = sorted(data.index.get_level_values('trade_date').unique())
        self._all_dates = all_dates
        
        # 数据中的最新日期
        data_latest_date = all_dates[-1]
        
        # 根据 holding_periods 计算分析日期（前移）
        if holding_periods and max(holding_periods) > 0:
            max_period = max(holding_periods)
            offset_idx = len(all_dates) - 1 - max_period
            if offset_idx >= 0:
                self.latest_date = all_dates[offset_idx]
                print(f"   📊 筛选器初始化完成")
                print(f"      数据最新日期: {data_latest_date.strftime('%Y-%m-%d')}")
                print(f"      持有期: {holding_periods} 天 → 前移 {max_period} 个交易日")
                print(f"      分析日期(筛选日): {self.latest_date.strftime('%Y-%m-%d')}")
            else:
                self.latest_date = data_latest_date
                print(f"   📊 筛选器初始化完成")
                print(f"      ⚠️ 数据交易日数量({len(all_dates)})不足以前移{max_period}天，使用最新日期")
                print(f"      分析日期: {self.latest_date.strftime('%Y-%m-%d')}")
        else:
            self.latest_date = data_latest_date
            print(f"   📊 筛选器初始化完成")
            print(f"      分析日期: {self.latest_date.strftime('%Y-%m-%d')}")
        
        # 获取所有股票代码
        self.all_stock_codes = data.index.get_level_values('ts_code').unique().tolist()
        print(f"      股票总数: {len(self.all_stock_codes)}")
    
    def execute_screening(
        self, 
        screening_logic: Dict,
        top_n: int = 20,
        query: str = ''
    ) -> List[Dict[str, Any]]:
        """
        执行筛选逻辑（带预筛选优化）
        
        Args:
            screening_logic: 筛选逻辑字典
            top_n: 返回的股票数量上限
            query: 原始用户查询（用于智能提取行业等预筛选条件）
            
        Returns:
            候选股票列表
        """
        # 1. 预筛选：识别并执行简单的过滤条件
        print(f"\n   🔍 步骤1: 预筛选股票池...")
        filtered_stock_codes = self._pre_filter_stocks(screening_logic, query=query)
        print(f"      预筛选后: {len(filtered_stock_codes)} 只股票")
        
        if not filtered_stock_codes:
            print(f"      ⚠️ 预筛选后无股票，请检查筛选条件")
            return []
        
        # 2. 批量计算技术指标并筛选
        print(f"\n   📊 步骤2: 计算技术指标并筛选...")
        candidates = self._batch_screen_stocks(
            stock_codes=filtered_stock_codes,
            screening_logic=screening_logic
        )
        print(f"      成功筛选: {len(candidates)} 只")
        
        # 3. 排序并返回Top N
        results = sorted(candidates, key=lambda x: x['confidence'], reverse=True)[:top_n]
        return results
    
    def _pre_filter_stocks(self, screening_logic: Dict, query: str = '') -> List[str]:
        """
        预筛选：识别并执行简单的过滤条件（行业、市场等）
        
        策略：
        1. 从 tools 列表中识别 filter_by_industry、filter_by_market 等工具
        2. 从用户查询和 screening_logic 中智能提取行业/市场关键词
        3. 合并执行预筛选，缩小股票池
        """
        tools = screening_logic.get('tools', [])
        
        # 收集所有预筛选工具步骤，使用 (tool_name, param_value) 元组去重
        seen: Set[Tuple[str, str]] = set()
        pre_filter_tools: List[Dict] = []
        
        def _add_tool(tool_step: Dict):
            """去重添加预筛选工具"""
            tool_name = tool_step.get('tool', '')
            params = tool_step.get('params', {})
            # 提取去重键值
            if tool_name == 'filter_by_industry':
                key = ('industry', params.get('industry', ''))
            elif tool_name == 'filter_by_market':
                key = ('market', params.get('market', ''))
            else:
                return
            if key[1] and key not in seen:
                seen.add(key)
                pre_filter_tools.append(tool_step)
        
        # 从 AI 生成的 tools 列表中收集
        for tool_step in tools:
            if tool_step.get('tool', '') in _PRE_FILTER_TOOLS:
                _add_tool(tool_step)
        
        # 智能补充：从用户查询和 screening_logic 中自动检测
        for tool_step in self._auto_detect_pre_filters(screening_logic, query):
            _add_tool(tool_step)
        
        # 如果没有预筛选工具，返回全部股票
        if not pre_filter_tools:
            print(f"      未检测到预筛选条件，使用全部股票池")
            return self.all_stock_codes
        
        # 执行预筛选
        print(f"      检测到 {len(pre_filter_tools)} 个预筛选条件:")
        for tool_step in pre_filter_tools:
            print(f"         - {tool_step.get('tool')}({tool_step.get('params', {})})")
        
        # 获取最新日期的数据（用于预筛选）
        latest_data = self.data.xs(self.latest_date, level='trade_date')
        
        # 按工具类型分组执行（同类工具 OR，不同类型 AND）
        tool_results: Dict[str, List[pd.Series]] = {}
        
        for tool_step in pre_filter_tools:
            tool_name = tool_step.get('tool')
            params = tool_step.get('params', {})
            try:
                result = execute_tool_impl(
                    tool_name=tool_name,
                    data=latest_data,
                    params=params,
                    computed_vars={}
                )
                tool_results.setdefault(tool_name, []).append(result)
                print(f"         ↳ {tool_name}({params}): 匹配 {result.sum()} 只股票")
            except Exception as e:
                print(f"      ⚠️ 预筛选工具 {tool_name} 执行失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 合并过滤条件：同类 OR，不同类型 AND
        filter_mask = pd.Series(True, index=latest_data.index)
        for tool_name, results in tool_results.items():
            # 同类工具之间 OR
            tool_mask = pd.concat(results, axis=1).any(axis=1)
            filter_mask &= tool_mask
            print(f"         ↳ {tool_name} 合计匹配: {tool_mask.sum()} 只股票")
        
        return latest_data[filter_mask].index.tolist()
    
    def _auto_detect_pre_filters(self, screening_logic: Dict, query: str = '') -> List[Dict]:
        """
        智能检测预筛选条件：从用户查询和screening_logic中自动提取行业/市场信息
        """
        detected_tools = []
        
        # 获取数据中的实际行业列表
        available_industries = self._get_available_industries_from_data()
        
        # 合并所有待检测的文本
        text_sources = [
            query,
            screening_logic.get('name', ''),
            screening_logic.get('rationale', ''),
            screening_logic.get('expression', ''),
        ]
        combined_text = ' '.join(str(t) for t in text_sources if t)
        if not combined_text.strip():
            return detected_tools
        
        # 从文本中匹配行业名称（贪心匹配：较长名称优先，避免子串冲突）
        if available_industries:
            sorted_industries = sorted(available_industries, key=len, reverse=True)
            matched_industries: List[str] = []
            remaining_text = combined_text
            
            for industry in sorted_industries:
                if industry in remaining_text:
                    matched_industries.append(industry)
                    # 贪心替换，避免子串重复匹配
                    remaining_text = remaining_text.replace(industry, '')
            
            for industry in matched_industries:
                detected_tools.append({
                    'tool': 'filter_by_industry',
                    'params': {'industry': industry},
                    'var': f'is_{industry}',
                })
        
        # 检测市场信息
        market_keywords = {'主板': '主板', '创业板': '创业板', '科创板': '科创板', '北交所': '北交所'}
        for keyword, market_name in market_keywords.items():
            if keyword in combined_text:
                detected_tools.append({
                    'tool': 'filter_by_market',
                    'params': {'market': market_name},
                    'var': f'is_{market_name}',
                })
        
        if detected_tools:
            print(f"      🔍 智能检测到预筛选条件:")
            for tool_step in detected_tools:
                print(f"         - {tool_step['tool']}({tool_step['params']})")
        
        return detected_tools
    
    def _get_available_industries_from_data(self) -> List[str]:
        """从数据中提取所有可用的行业名称"""
        try:
            latest_data = self.data.xs(self.latest_date, level='trade_date')
            if 'industry' in latest_data.columns:
                industries = latest_data['industry'].dropna().unique().tolist()
                return [str(ind) for ind in industries if str(ind).strip()]
        except Exception:
            pass
        
        try:
            if isinstance(self.data.index, pd.MultiIndex):
                industries = self.data.reset_index()['industry'].dropna().unique().tolist()
            else:
                industries = self.data['industry'].dropna().unique().tolist()
            return [str(ind) for ind in industries if str(ind).strip()]
        except Exception:
            return []
    
    # ==================== 批量筛选主方法 ====================
    
    def _batch_screen_stocks(
        self,
        stock_codes: List[str],
        screening_logic: Dict
    ) -> List[Dict[str, Any]]:
        """
        向量化批量筛选股票（对预筛选后的股票池执行完整的筛选逻辑）
        
        流程：过滤有效股票 → 执行工具 → 表达式评估 → 构建结果
        """
        t_start = _time.time()
        
        # 提取筛选逻辑
        tools = screening_logic.get('tools', [])
        expression = screening_logic.get('expression', '')
        confidence_formula = screening_logic.get('confidence_formula', '1.0')
        rationale = screening_logic.get('rationale', '')
        
        # 分离主工具和预筛选变量
        main_tools = [t for t in tools if t.get('tool') not in _PRE_FILTER_TOOLS]
        pre_filter_vars = {
            t.get('var'): True for t in tools
            if t.get('tool') in _PRE_FILTER_TOOLS and t.get('var')
        }
        
        # 提取表达式中引用的变量名
        expression_vars = NamespaceBuilder.extract_variables(expression) if expression else set()
        
        # 打印筛选逻辑摘要
        self._print_logic_summary(expression, confidence_formula, main_tools)
        
        print(f"\n      ⚡ 向量化批量筛选模式 ({len(stock_codes)} 只股票)")
        
        # 阶段1: 过滤有效股票
        valid_stocks, valid_data, stats = self._filter_valid_stocks(stock_codes)
        if not valid_stocks:
            self._print_screening_stats(
                len(stock_codes), stats['data_insufficient'], stats['no_latest'],
                0, 0, 0, 0, 0, 0
            )
            return []
        
        # 阶段2: 批量执行工具
        namespace, tool_error_count = self._execute_main_tools(
            valid_data, main_tools, pre_filter_vars
        )
        
        # 阶段3: 提取最新日期截面
        latest_namespace = self._extract_latest_cross_section(namespace, valid_data)
        
        # 阶段4: 向量化表达式评估
        matched_stocks, eval_stats = self._vectorized_expression_eval(
            expression, expression_vars, latest_namespace, valid_stocks
        )
        
        # 阶段5: 构建候选结果
        candidates = self._build_candidates(
            matched_stocks, confidence_formula, latest_namespace,
            expression_vars, valid_data, valid_stocks, rationale
        )
        
        # 打印统计信息
        t_elapsed = _time.time() - t_start
        self._print_screening_stats(
            len(stock_codes), stats['data_insufficient'], stats['no_latest'],
            tool_error_count, eval_stats['false_count'], eval_stats['nan_count'],
            eval_stats['eval_error_count'], 0, len(candidates),
            elapsed=t_elapsed
        )
        
        return candidates
    
    def _filter_valid_stocks(
        self, stock_codes: List[str]
    ) -> Tuple[List[str], pd.DataFrame, Dict[str, int]]:
        """
        过滤有效股票：数据充足且在分析日有数据
        
        Returns:
            (有效股票代码列表, 有效数据子集, 统计信息字典)
        """
        # 提取子集
        all_ts_codes = self.data.index.get_level_values('ts_code')
        subset_data = self.data[all_ts_codes.isin(stock_codes)]
        
        if len(subset_data) == 0:
            print(f"      ⚠️ 子集数据为空")
            return [], subset_data, {'data_insufficient': 0, 'no_latest': 0}
        
        # 统计每只股票的数据天数，过滤不足20天的
        stock_day_counts = subset_data.groupby(level='ts_code').size()
        sufficient_stocks = stock_day_counts[stock_day_counts >= 20].index
        data_insufficient_count = len(stock_day_counts) - len(sufficient_stocks)
        
        # 检查哪些股票在 latest_date 有数据
        try:
            latest_date_data = subset_data.xs(self.latest_date, level='trade_date')
            stocks_with_latest = set(latest_date_data.index)
        except KeyError:
            print(f"      ⚠️ 数据中不存在分析日期 {self.latest_date}")
            return [], subset_data, {'data_insufficient': data_insufficient_count, 'no_latest': 0}
        
        # 有效股票 = 数据充足 ∩ 有最新数据
        valid_stocks = [s for s in sufficient_stocks if s in stocks_with_latest]
        no_latest_count = len(sufficient_stocks) - len(valid_stocks)
        
        print(f"      数据过滤: {len(stock_codes)} → {len(valid_stocks)} 只有效股票")
        if data_insufficient_count > 0:
            print(f"         数据不足(<20天): {data_insufficient_count} 只")
        if no_latest_count > 0:
            print(f"         无最新数据: {no_latest_count} 只")
        
        if not valid_stocks:
            print(f"      ⚠️ 无有效股票")
            return [], subset_data, {'data_insufficient': data_insufficient_count, 'no_latest': no_latest_count}
        
        # 缩小数据范围
        valid_ts_codes = subset_data.index.get_level_values('ts_code')
        valid_data = subset_data[valid_ts_codes.isin(valid_stocks)]
        
        return valid_stocks, valid_data, {'data_insufficient': data_insufficient_count, 'no_latest': no_latest_count}
    
    def _execute_main_tools(
        self,
        valid_data: pd.DataFrame,
        main_tools: List[Dict],
        pre_filter_vars: Dict[str, bool]
    ) -> Tuple[Dict, int]:
        """
        批量执行主要工具步骤
        
        Returns:
            (命名空间字典, 工具执行失败数)
        """
        namespace = self.namespace_builder.build_namespace(valid_data)
        namespace.update(pre_filter_vars)
        
        tool_error_count = 0
        for tool_step in main_tools:
            tool_name = tool_step.get('tool')
            params = tool_step.get('params', {})
            var_name = tool_step.get('var')
            
            if not tool_name or not var_name:
                continue
            
            try:
                result = execute_tool_impl(
                    tool_name=tool_name,
                    data=valid_data,
                    params=params,
                    computed_vars=namespace
                )
                namespace[var_name] = result
                print(f"      ✅ 工具 {tool_name} → {var_name} 执行完成")
            except Exception as e:
                tool_error_count += 1
                print(f"      ⚠️ 工具 {tool_name} 批量执行失败: {e}")
                if tool_error_count <= 2:
                    import traceback
                    traceback.print_exc()
                namespace[var_name] = pd.Series(np.nan, index=valid_data.index)
        
        return namespace, tool_error_count
    
    def _vectorized_expression_eval(
        self,
        expression: str,
        expression_vars: Set[str],
        latest_namespace: Dict,
        valid_stocks: List[str]
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        向量化评估筛选表达式
        
        Returns:
            (匹配的股票代码列表, 评估统计信息)
        """
        stats = {'false_count': 0, 'nan_count': 0, 'eval_error_count': 0}
        stock_index = latest_namespace.get('_stock_index', pd.Index(valid_stocks))
        
        try:
            # 向量化检测关键变量中的 NaN
            var_series = [
                latest_namespace[v] for v in expression_vars
                if v in latest_namespace and isinstance(latest_namespace[v], pd.Series)
            ]
            if var_series:
                nan_mask = pd.concat(var_series, axis=1).isna().any(axis=1).reindex(stock_index, fill_value=False)
            else:
                nan_mask = pd.Series(False, index=stock_index)
            
            stats['nan_count'] = int(nan_mask.sum())
            
            # 向量化评估筛选条件
            match_result = eval(expression, {"__builtins__": {}}, latest_namespace)
            
            if isinstance(match_result, pd.Series):
                match_result = match_result.where(~nan_mask, False).fillna(False).astype(bool)
                stats['false_count'] = max(0, int((~match_result).sum()) - stats['nan_count'])
                matched_stocks = match_result[match_result].index.tolist()
            elif isinstance(match_result, (bool, np.bool_)):
                matched_stocks = valid_stocks if match_result else []
                stats['false_count'] = 0 if match_result else len(valid_stocks)
            else:
                matched_stocks = valid_stocks if match_result else []
            
            # 调试输出：前3只 False 的股票
            if stats['false_count'] > 0 and isinstance(match_result, pd.Series):
                self._debug_print_samples(
                    match_result[match_result].index[:3],
                    expression_vars, latest_namespace, "表达式为True"
                )
            # 调试输出：前3只 NaN 的股票
            if stats['nan_count'] > 0:
                self._debug_print_samples(
                    nan_mask[nan_mask].index[:3],
                    expression_vars, latest_namespace, "变量含NaN",
                    show_nan_only=True
                )
            
        except Exception as e:
            stats['eval_error_count'] = 1
            print(f"      ⚠️ 向量化表达式评估失败: {e}")
            import traceback
            traceback.print_exc()
            matched_stocks = []
        
        return matched_stocks, stats
    
    def _build_candidates(
        self,
        matched_stocks: List[str],
        confidence_formula: str,
        latest_namespace: Dict,
        expression_vars: Set[str],
        valid_data: pd.DataFrame,
        valid_stocks: List[str],
        rationale: str
    ) -> List[Dict[str, Any]]:
        """
        向量化计算置信度并构建候选结果列表
        """
        if not matched_stocks:
            return []
        
        # 向量化计算置信度
        try:
            conf_raw = eval(confidence_formula, {"__builtins__": {}}, latest_namespace)
            if isinstance(conf_raw, pd.Series):
                confidence_series = 1.0 / (1.0 + np.exp(-conf_raw))
            elif isinstance(conf_raw, (int, float)):
                confidence_series = pd.Series(
                    1.0 / (1.0 + np.exp(-conf_raw)),
                    index=pd.Index(valid_stocks)
                )
            else:
                confidence_series = pd.Series(0.5, index=pd.Index(valid_stocks))
        except Exception as e:
            print(f"      ⚠️ 置信度批量计算失败: {e}，使用默认值 0.5")
            confidence_series = pd.Series(0.5, index=pd.Index(valid_stocks))
        
        # 获取股票名称映射
        name_map = self._get_stock_names_batch(valid_data, matched_stocks)
        
        # 向量化提取关键指标：构建指标 DataFrame
        metrics_dict: Dict[str, pd.Series] = {}
        for var in expression_vars:
            val = latest_namespace.get(var)
            if isinstance(val, pd.Series):
                metrics_dict[var] = val
            elif isinstance(val, (int, float, np.number)):
                metrics_dict[var] = pd.Series(float(val), index=pd.Index(matched_stocks))
        
        if metrics_dict:
            metrics_df = pd.DataFrame(metrics_dict).reindex(matched_stocks)
        else:
            metrics_df = pd.DataFrame(index=matched_stocks)
        
        # 构建结果列表
        candidates = []
        for ts_code in matched_stocks:
            # 获取置信度
            try:
                conf = float(confidence_series.loc[ts_code]) if ts_code in confidence_series.index else 0.5
            except (KeyError, TypeError):
                conf = 0.5
            if pd.isna(conf):
                conf = 0.5
            
            # 提取指标（向量化预构建的 DataFrame 中直接取行）
            if ts_code in metrics_df.index:
                row = metrics_df.loc[ts_code]
                metrics = {k: float(v) for k, v in row.items() if pd.notna(v) and isinstance(v, (int, float, np.number))}
            else:
                metrics = {}
            
            candidates.append({
                'ts_code': ts_code,
                'name': name_map.get(ts_code, ts_code),
                'confidence': conf,
                'reason': rationale,
                'metrics': metrics
            })
        
        return candidates
    
    # ==================== 辅助方法 ====================
    
    def _extract_latest_cross_section(self, namespace: Dict, valid_data: pd.DataFrame) -> Dict:
        """
        从双索引命名空间中提取 latest_date 的截面数据
        
        将以 (trade_date, ts_code) 为索引的 Series 转换为以 ts_code 为索引的 Series，
        使后续的 eval() 能够对所有股票同时进行向量化运算。
        """
        latest_namespace = {}
        
        try:
            latest_slice = valid_data.xs(self.latest_date, level='trade_date')
            stock_index = latest_slice.index
        except KeyError:
            return latest_namespace
        
        latest_namespace['_stock_index'] = stock_index
        
        for key, value in namespace.items():
            if isinstance(value, pd.Series):
                if isinstance(value.index, pd.MultiIndex):
                    try:
                        cross_section = value.xs(self.latest_date, level='trade_date')
                        latest_namespace[key] = cross_section.reindex(stock_index)
                    except KeyError:
                        latest_namespace[key] = pd.Series(np.nan, index=stock_index)
                elif value.index.equals(valid_data.index):
                    try:
                        mask = valid_data.index.get_level_values('trade_date') == self.latest_date
                        sliced = value[mask]
                        sliced.index = stock_index
                        latest_namespace[key] = sliced
                    except Exception:
                        latest_namespace[key] = pd.Series(np.nan, index=stock_index)
                else:
                    latest_namespace[key] = value.reindex(stock_index) if hasattr(value, 'reindex') else value
            elif callable(value):
                latest_namespace[key] = value
            else:
                latest_namespace[key] = value
        
        return latest_namespace
    
    @staticmethod
    def _get_stock_names_batch(data: pd.DataFrame, stock_codes: List[str]) -> Dict[str, str]:
        """
        批量获取股票名称映射
        """
        if 'name' not in data.columns:
            return {code: code for code in stock_codes}
        
        try:
            names = data.groupby(level='ts_code')['name'].first()
            return {
                code: str(names.loc[code]) if code in names.index else code
                for code in stock_codes
            }
        except Exception:
            return {code: code for code in stock_codes}
    
    @staticmethod
    def _debug_print_samples(
        sample_codes,
        expression_vars: Set[str],
        latest_namespace: Dict,
        label: str,
        show_nan_only: bool = False
    ):
        """统一调试输出：打印样本股票的变量值"""
        for ts_code in sample_codes:
            print(f"\n      🔍 调试[{ts_code}] {label}:")
            for var_name in expression_vars:
                val = latest_namespace.get(var_name)
                if isinstance(val, pd.Series) and ts_code in val.index:
                    v = val.loc[ts_code]
                    if show_nan_only:
                        try:
                            if pd.isna(v):
                                print(f"         {var_name} = NaN")
                        except (TypeError, ValueError):
                            pass
                    elif isinstance(v, (int, float, np.number, bool, np.bool_)):
                        print(f"         {var_name} = {v}")
    
    @staticmethod
    def _print_logic_summary(expression: str, confidence_formula: str, main_tools: List[Dict]):
        """打印筛选逻辑摘要"""
        print(f"\n      📋 筛选逻辑:")
        print(f"         表达式: {expression}")
        print(f"         置信度: {confidence_formula}")
        if main_tools:
            print(f"         工具步骤:")
            for t in main_tools:
                print(f"            {t.get('var')} = {t.get('tool')}({t.get('params', {})})")
    
    @staticmethod
    def _print_screening_stats(
        total: int, data_insufficient: int, no_latest: int,
        tool_error: int, expr_false: int, expr_nan: int,
        expr_eval_error: int, other_error: int, success: int,
        elapsed: float = 0.0
    ):
        """打印筛选统计信息"""
        print(f"\n      📊 筛选统计:")
        print(f"         候选股票数: {total}")
        if data_insufficient > 0:
            print(f"         数据不足(<20天): {data_insufficient} 只")
        if no_latest > 0:
            print(f"         无最新数据: {no_latest} 只")
        if tool_error > 0:
            print(f"         工具执行失败: {tool_error} 个")
        print(f"         表达式为False: {expr_false} 只")
        if expr_nan > 0:
            print(f"         表达式为NaN: {expr_nan} 只")
        if expr_eval_error > 0:
            print(f"         表达式评估错误: {expr_eval_error} 只")
        if other_error > 0:
            print(f"         其他错误: {other_error} 只")
        print(f"         ✅ 成功匹配: {success} 只")
        if elapsed > 0:
            print(f"         ⏱️ 耗时: {elapsed:.2f}s")


# ==================== 便捷函数 ====================

def create_stock_screener(
    data: pd.DataFrame,
    holding_periods: Optional[List[int]] = None
) -> StockScreener:
    """创建股票筛选器实例的便捷函数"""
    return StockScreener(data, holding_periods=holding_periods)