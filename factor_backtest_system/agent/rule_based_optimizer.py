#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子优化器模块 - 提供基于规则的因子性能分析和优化建议

职责：
1. 分析因子回测的各项具体指标
2. 根据量化标准提供针对性的修改建议
3. 生成可直接实施的技术改进方案
"""

from typing import Dict, List, Any


class RuleBasedFactorOptimizer:
    """
    基于规则的因子优化器（作为 LLM 优化的降级方案）
    
    核心功能：
    - 基于预定义阈值评估因子表现
    - 提供标准化的优化建议
    - 用于 LLM 不可用时的备用方案
    """
    
    def __init__(self):
        """初始化优化器"""
        # 定义各项指标的评估标准
        self.thresholds = {
            'annual_return': {
                'excellent': 0.30,
                'good': 0.15,
                'acceptable': 0.05,
                'poor': 0.00
            },
            'sharpe_ratio': {
                'excellent': 2.0,
                'good': 1.5,
                'acceptable': 1.0,
                'poor': 0.5
            },
            'max_drawdown': {
                'excellent': -0.10,
                'good': -0.15,
                'acceptable': -0.20,
                'poor': -0.25
            },
            'win_rate': {
                'excellent': 0.60,
                'good': 0.55,
                'acceptable': 0.50,
                'poor': 0.45
            }
        }
    
    def analyze_performance(self, factor: Dict[str, Any], 
                           backtest_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析因子表现
        
        Args:
            factor: 因子定义
            backtest_result: 回测结果
            
        Returns:
            性能分析报告
        """
        metrics = backtest_result.get('metrics', {})
        long_short_metrics = metrics.get('group_long_short', {})
        
        if not long_short_metrics:
            return {
                'factor_name': factor.get('name', 'unknown'),
                'status': 'failed',
                'error': '无有效回测指标数据'
            }
        
        # 提取关键指标
        annual_return = long_short_metrics.get('年化收益率', 0)
        sharpe_ratio = long_short_metrics.get('夏普比率', 0)
        max_drawdown = long_short_metrics.get('最大回撤', 0)
        win_rate = long_short_metrics.get('胜率', 0)
        
        # 评估指标等级
        return_grade = self._grade_metric(annual_return, 'annual_return')
        sharpe_grade = self._grade_metric(sharpe_ratio, 'sharpe_ratio')
        drawdown_grade = self._grade_metric(max_drawdown, 'max_drawdown')
        win_rate_grade = self._grade_metric(win_rate, 'win_rate')
        
        # 计算综合评分
        composite_score = self._calculate_composite_score(
            return_grade, sharpe_grade, drawdown_grade, win_rate_grade
        )
        
        return {
            'factor_name': factor.get('name', 'unknown'),
            'status': 'success',
            'metrics': {
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate
            },
            'grades': {
                'return_grade': return_grade,
                'sharpe_grade': sharpe_grade,
                'drawdown_grade': drawdown_grade,
                'win_rate_grade': win_rate_grade
            },
            'composite_score': composite_score,
            'performance_level': self._get_performance_level(composite_score)
        }
    
    def generate_suggestions(self, analysis: Dict[str, Any], 
                            factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成优化建议
        
        Args:
            analysis: 性能分析结果
            factor: 因子定义
            
        Returns:
            优化建议列表
        """
        if analysis['status'] == 'failed':
            return [{
                'type': 'critical_fix',
                'priority': 'high',
                'issue': '因子计算失败',
                'description': analysis['error'],
                'specific_actions': [
                    '检查因子表达式语法',
                    '验证输入数据完整性',
                    '确认工具调用参数正确性'
                ],
                'code_examples': []
            }]
        
        suggestions = []
        grades = analysis['grades']
        metrics = analysis['metrics']
        
        # 根据不同维度生成建议
        if grades['return_grade'] in ['poor', 'acceptable']:
            suggestions.extend(self._suggest_return_improvements(metrics, factor))
        
        if grades['drawdown_grade'] in ['poor', 'acceptable']:
            suggestions.extend(self._suggest_risk_control(metrics, factor))
        
        if grades['sharpe_grade'] in ['poor', 'acceptable']:
            suggestions.extend(self._suggest_stability_improvements(metrics, factor))
        
        if grades['win_rate_grade'] in ['poor', 'acceptable']:
            suggestions.extend(self._suggest_win_rate_improvements(metrics, factor))
        
        if analysis['composite_score'] < 70:
            suggestions.extend(self._suggest_comprehensive_optimization(factor))
        
        return suggestions
    
    def _grade_metric(self, value: float, metric_type: str) -> str:
        """根据阈值对指标进行分级"""
        thresholds = self.thresholds[metric_type]
        
        if metric_type == 'max_drawdown':
            if value >= thresholds['excellent']:
                return 'excellent'
            elif value >= thresholds['good']:
                return 'good'
            elif value >= thresholds['acceptable']:
                return 'acceptable'
            else:
                return 'poor'
        else:
            if value >= thresholds['excellent']:
                return 'excellent'
            elif value >= thresholds['good']:
                return 'good'
            elif value >= thresholds['acceptable']:
                return 'acceptable'
            else:
                return 'poor'
    
    def _calculate_composite_score(self, return_grade: str, sharpe_grade: str,
                                 drawdown_grade: str, win_rate_grade: str) -> float:
        """计算综合评分 (0-100 分)"""
        grade_scores = {
            'excellent': 100,
            'good': 80,
            'acceptable': 60,
            'poor': 40
        }
        
        scores = [
            grade_scores[return_grade] * 0.35,
            grade_scores[sharpe_grade] * 0.25,
            grade_scores[drawdown_grade] * 0.25,
            grade_scores[win_rate_grade] * 0.15
        ]
        
        return sum(scores)
    
    def _get_performance_level(self, score: float) -> str:
        """根据综合评分确定表现等级"""
        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 55:
            return 'acceptable'
        else:
            return 'poor'
    
    def _suggest_return_improvements(self, metrics: Dict, 
                                    factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """收益率提升建议"""
        suggestions = []
        current_return = metrics['annual_return']
        
        if current_return < 0:
            suggestions.append({
                'type': 'return_optimization',
                'priority': 'critical',
                'issue': f'因子收益率为负 ({current_return:.2%})',
                'description': '因子信号方向可能完全错误',
                'specific_actions': [
                    f'反转因子符号：{factor.get("expression", "")} * -1',
                    '检查因子构建逻辑中的方向性假设',
                    '验证数据质量，排除异常值影响'
                ],
                'code_examples': [
                    f'# 反转因子方向\nnew_expression = "({factor.get("expression", "factor")}) * -1"'
                ]
            })
        elif current_return < 0.05:
            suggestions.append({
                'type': 'return_optimization',
                'priority': 'high',
                'issue': f'收益率偏低 ({current_return:.2%})',
                'description': '因子区分度不足，需要增强信号强度',
                'specific_actions': [
                    '增加动量窗口长度以捕捉更强趋势',
                    '引入成交量确认提高信号质量',
                    '添加波动率标准化提高稳定性'
                ],
                'code_examples': [
                    '# 增加动量窗口\nmomentum_20 = close.pct_change(20)',
                    '# 添加成交量确认\nvolume_ratio = volume / volume.rolling(20).mean()',
                    '# 波动率标准化\nvol_adjusted = momentum / atr(14)'
                ]
            })
        
        return suggestions
    
    def _suggest_risk_control(self, metrics: Dict, 
                             factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """风险控制建议"""
        suggestions = []
        drawdown = abs(metrics['max_drawdown'])
        
        if drawdown > 0.25:
            suggestions.append({
                'type': 'risk_management',
                'priority': 'critical',
                'issue': f'最大回撤过大 ({drawdown:.2%})',
                'description': '因子波动性过高，需要加强风控机制',
                'specific_actions': [
                    '添加止损机制限制单笔损失',
                    '引入波动率过滤器筛除高风险时段',
                    '设置仓位规模动态调整规则'
                ],
                'code_examples': [
                    '# 添加波动率过滤\nvolatility = close.rolling(20).std()',
                    'vol_filter = volatility < volatility.quantile(0.8)',
                    '# 动态仓位调整\nposition_size = 1.0 / (1.0 + volatility / volatility.mean())'
                ]
            })
        
        return suggestions
    
    def _suggest_stability_improvements(self, metrics: Dict, 
                                       factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """稳定性提升建议"""
        suggestions = []
        sharpe = metrics['sharpe_ratio']
        
        if sharpe < 1.0:
            suggestions.append({
                'type': 'stability_optimization',
                'priority': 'medium',
                'issue': f'夏普比率偏低 ({sharpe:.2f})',
                'description': '收益风险比不佳，需要改善风险调整后收益',
                'specific_actions': [
                    '平滑因子值减少噪声',
                    '添加行业中性化处理',
                    '引入时间衰减权重降低历史数据影响'
                ],
                'code_examples': [
                    '# 因子值平滑\nsmoothed_factor = factor.ewm(span=5).mean()',
                    '# 行业中性化\ngrouped_mean = factor.groupby(industry).transform("mean")',
                    'neutralized_factor = factor - grouped_mean',
                    '# 时间衰减权重\ndecay_weights = np.exp(-np.arange(len(factor)) * 0.1)'
                ]
            })
        
        return suggestions
    
    def _suggest_win_rate_improvements(self, metrics: Dict, 
                                      factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """胜率提升建议"""
        suggestions = []
        win_rate = metrics['win_rate']
        
        if win_rate < 0.5:
            suggestions.append({
                'type': 'signal_quality',
                'priority': 'high',
                'issue': f'胜率过低 ({win_rate:.2%})',
                'description': '因子预测准确性不足',
                'specific_actions': [
                    '提高入选门槛筛选高质量信号',
                    '结合多个互补因子形成复合信号',
                    '添加基本面指标验证技术信号'
                ],
                'code_examples': [
                    '# 提高信号门槛\nsignal_threshold = factor.quantile(0.9)',
                    '# 复合信号\ncomposite_signal = (momentum_signal > 0) & (volume_signal > 1.5)',
                    '# 基本面验证\npe_ratio = pe_data / pe_industry_avg',
                    'confirmed_signal = technical_signal & (pe_ratio < 1.2)'
                ]
            })
        
        return suggestions
    
    def _suggest_comprehensive_optimization(self, factor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """综合性优化建议"""
        return [{
            'type': 'comprehensive_refactoring',
            'priority': 'medium',
            'issue': '因子整体表现不佳',
            'description': '建议重新设计因子逻辑架构',
            'specific_actions': [
                '重构为多因子复合模型',
                '引入机器学习方法优化参数',
                '添加宏观经济状态过滤器'
            ],
            'code_examples': [
                '# 多因子复合模型\nfactor_score = 0.4 * momentum_score + 0.3 * volume_score + 0.3 * quality_score',
                '# 参数优化\ndef optimize_parameters(data, param_ranges):\n    best_params = grid_search(data, param_ranges)\n    return best_params',
                '# 宏观状态过滤\nbull_market = ma_20 > ma_60 and volume_ratio > 1.2',
                'bear_market = ma_20 < ma_60 or volatility > vol_threshold',
                'factor_value = bull_factor if bull_market else bear_factor'
            ]
        }]


def generate_rule_based_suggestions(factors: List[Dict[str, Any]], 
                                   backtest_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    为因子列表生成基于规则的优化建议
    
    Args:
        factors: 因子列表
        backtest_results: 回测结果列表
        
    Returns:
        包含详细分析和建议的字典
    """
    optimizer = RuleBasedFactorOptimizer()
    results = {}
    
    for factor, result in zip(factors, backtest_results):
        # 分析因子表现
        analysis = optimizer.analyze_performance(factor, result)
        
        # 生成优化建议
        suggestions = optimizer.generate_suggestions(analysis, factor)
        
        # 格式化报告
        report = _format_suggestions_report(suggestions, analysis)
        
        results[factor.get('name', 'unknown')] = {
            'analysis': analysis,
            'suggestions': suggestions,
            'report': report
        }
    
    return results


def _format_suggestions_report(suggestions: List[Dict[str, Any]], 
                              analysis: Dict[str, Any]) -> str:
    """
    格式化建议报告
    
    Args:
        suggestions: 优化建议列表
        analysis: 性能分析结果
        
    Returns:
        格式化的建议报告字符串
    """
    if not suggestions:
        return "✅ 因子表现优秀，无需优化建议"
    
    report = []
    report.append("=" * 80)
    report.append(f"📈 因子优化建议报告 - {analysis.get('factor_name', 'Unknown')}")
    report.append("=" * 80)
    report.append("")
    
    # 按优先级分组
    priority_order = ['critical', 'high', 'medium', 'low']
    grouped_suggestions = {p: [] for p in priority_order}
    
    for suggestion in suggestions:
        priority = suggestion['priority']
        if priority in grouped_suggestions:
            grouped_suggestions[priority].append(suggestion)
    
    # 输出各优先级建议
    for priority in priority_order:
        suggestions_of_priority = grouped_suggestions[priority]
        if not suggestions_of_priority:
            continue
        
        priority_labels = {
            'critical': '🔴 紧急修复',
            'high': '🟡 重要优化',
            'medium': '🔵 建议改进',
            'low': '🟢 可选增强'
        }
        
        report.append(f"{priority_labels[priority]} ({len(suggestions_of_priority)}项)")
        report.append("-" * 40)
        
        for i, suggestion in enumerate(suggestions_of_priority, 1):
            report.append(f"{i}. {suggestion['issue']}")
            report.append(f"   描述：{suggestion['description']}")
            report.append("   具体行动:")
            for action in suggestion['specific_actions']:
                report.append(f"   • {action}")
            
            if suggestion['code_examples']:
                report.append("   代码示例:")
                for example in suggestion['code_examples']:
                    report.append(f"   ```python")
                    report.append(f"   {example}")
                    report.append(f"   ```")
            report.append("")
    
    report.append("=" * 80)
    return "\n".join(report)
