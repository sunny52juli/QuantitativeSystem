#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 驱动的因子优化器 - 基于深度理解和智能分析提供个性化优化建议

核心理念：
1. 利用 LLM 深度理解因子构建逻辑和回测表现
2. 基于上下文提供个性化的修改建议
3. 支持迭代优化思维
4. 生成可直接实施的代码修改方案
"""

import os
import json
import traceback
from typing import Dict, List, Any, Optional

from core.logger import get_logger
from config import FactorBacktestConfig


class LLMFactorOptimizer:
    """
    LLM 驱动的因子优化器
    
    核心能力：
    - 深度分析因子构建逻辑和回测表现
    - 理解因子失败的根本原因
    - 提供个性化的优化策略
    - 生成具体的代码修改建议
    - 支持多轮迭代优化
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 LLM 优化器
        
        Args:
            api_key: API 密钥，如果为 None 则从环境变量读取
        """
        self.logger = get_logger(__name__)
        
        # 获取 API 配置
        self.api_key = api_key or os.environ.get('DEFAULT_API_KEY')
        if not self.api_key:
            raise ValueError("未配置 API 密钥")
        
        self.api_config = FactorBacktestConfig.get_api_config()
        
        self.logger.info("✅ LLM 因子优化器初始化完成")
    
    def analyze_and_optimize_factor(
        self, 
        factor_definition: Dict[str, Any], 
        backtest_results: Dict[str, Any],
        iteration_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        分析因子并提供优化建议
        
        Args:
            factor_definition: 因子定义（包括表达式、工具链等）
            backtest_results: 回测结果（包括各项指标）
            iteration_history: 优化历史记录（支持多轮迭代）
            
        Returns:
            包含深度分析和优化建议的字典
        """
        try:
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt(
                factor_definition, backtest_results, iteration_history
            )
            
            # 调用 LLM 进行深度分析
            llm_response = self._call_llm(analysis_prompt)
            
            # 解析 LLM 响应
            optimization_plan = self._parse_llm_response(llm_response)
            
            return {
                'factor_name': factor_definition.get('name', 'unknown'),
                'analysis': optimization_plan.get('analysis', {}),
                'optimization_suggestions': optimization_plan.get('suggestions', []),
                'code_modifications': optimization_plan.get('code_changes', []),
                'iteration_plan': optimization_plan.get('iteration_plan', {}),  # 修改为 iteration_plan 以匹配 format_optimization_report
                'confidence_level': optimization_plan.get('confidence', 0.8)
            }
            
        except Exception as e:
            self.logger.error(f"LLM 优化分析失败：{e}")
            traceback.print_exc()
            raise
    
    def _build_analysis_prompt(
        self, 
        factor_definition: Dict[str, Any], 
        backtest_results: Dict[str, Any],
        iteration_history: Optional[List[Dict[str, Any]]]
    ) -> str:
        """构建深度分析提示词"""
        # 提取关键信息
        factor_name = factor_definition.get('name', '未知因子')
        expression = factor_definition.get('expression', '')
        tools = factor_definition.get('tools', [])
        rationale = factor_definition.get('rationale', '')
        
        # 回测指标
        metrics = backtest_results.get('metrics', {}).get('group_long_short', {})
        annual_return = metrics.get('年化收益率', 0)
        sharpe_ratio = metrics.get('夏普比率', 0)
        max_drawdown = metrics.get('最大回撤', 0)
        win_rate = metrics.get('胜率', 0)
        
        # 构建提示词
        prompt = f"""你是一位专业的量化因子研究员，请深度分析以下因子的表现并提供优化建议。

## 因子信息
**因子名称**: {factor_name}
**构建逻辑**: {rationale}
**数学表达式**: {expression}
**使用的工具链**: {json.dumps(tools, ensure_ascii=False, indent=2)}

## 回测表现
**年化收益率**: {annual_return:.2%}
**夏普比率**: {sharpe_ratio:.2f}
**最大回撤**: {max_drawdown:.2%}
**胜率**: {win_rate:.2%}

## 分析要求
请从以下几个维度进行深度分析：

1. **根本原因诊断**
   - 分析因子表现不佳的核心原因
   - 识别因子逻辑中的潜在问题
   - 评估工具链的有效性

2. **优化策略建议**
   - 提供 3-5 个具体的优化方向
   - 每个建议都要说明原理和预期效果
   - 考虑风险收益平衡

3. **代码修改方案**
   - 提供具体的代码修改建议
   - 包括表达式调整、参数优化、新增逻辑等
   - 给出修改前后的对比

4. **迭代优化路径**
   - 设计下一步的优化计划
   - 建议测试的参数组合
   - 预期的改进幅度

## 输出格式
请严格按照以下 JSON 格式输出：

{{
    "analysis": {{
        "performance_diagnosis": "详细的性能诊断",
        "root_cause": "根本原因分析",
        "strengths": ["优势 1", "优势 2"],
        "weaknesses": ["问题 1", "问题 2"]
    }},
    "suggestions": [
        {{
            "category": "收益率优化 | 风险控制 | 稳定性提升 | 信号质量",
            "priority": "high|medium|low",
            "description": "具体建议描述",
            "principle": "背后的原理",
            "expected_impact": "预期改进效果"
        }}
    ],
    "code_changes": [
        {{
            "type": "expression_modify|parameter_tuning|logic_addition",
            "before": "修改前的代码",
            "after": "修改后的代码",
            "reason": "修改原因",
            "impact": "预期影响"
        }}
    ],
    "iteration_plan": {{
        "next_steps": ["步骤 1", "步骤 2"],
        "parameter_tests": ["参数组合 1", "参数组合 2"],
        "expected_improvement": "预期改进幅度"
    }},
    "confidence": 0.85
}}

请基于因子的具体情况提供专业、深入的分析和建议。"""

        # 如果有优化历史，添加历史信息
        if iteration_history:
            prompt += f"\n\n## 优化历史\n这是第{len(iteration_history) + 1}轮优化，请考虑之前的优化尝试："
            for i, history in enumerate(iteration_history[-3:], 1):
                prompt += f"\n第{i}轮：{history.get('summary', '无记录')}"

        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.api_config["model"],
            "messages": [
                {"role": "system", "content": "你是一位专业的量化因子研究员，擅长因子分析和优化。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.api_config["temperature"],
            "max_tokens": self.api_config["max_tokens"]
        }

        response = requests.post(
            self.api_config["api_url"],
            headers=headers,
            json=payload,
            timeout=100
        )
        
        if response.status_code != 200:
            raise Exception(f"API 调用失败：{response.status_code}")
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        import re
        import json
        
        # 提取 JSON 内容
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON 解析失败：{e}")
        
        # 如果解析失败，抛出异常
        raise ValueError(f"无法解析 LLM 响应：{response[:200]}...")
    
    def format_optimization_report(self, optimization_result: Dict[str, Any]) -> str:
        """格式化优化报告"""
        report = []
        report.append("=" * 80)
        report.append(f"🤖 LLM 因子优化分析报告 - {optimization_result['factor_name']}")
        report.append("=" * 80)
        report.append("")
        
        # 分析部分
        analysis = optimization_result.get('analysis', {})
        report.append("🔍 深度分析")
        report.append("-" * 40)
        report.append(f"诊断结果：{analysis.get('performance_diagnosis', 'N/A')}")
        report.append(f"根本原因：{analysis.get('root_cause', 'N/A')}")
        if analysis.get('strengths'):
            report.append(f"优势：{', '.join(analysis['strengths'])}")
        if analysis.get('weaknesses'):
            report.append(f"问题：{', '.join(analysis['weaknesses'])}")
        report.append("")
        
        # 优化建议
        suggestions = optimization_result.get('optimization_suggestions', [])
        if suggestions:
            report.append("💡 优化建议")
            report.append("-" * 40)
            for i, suggestion in enumerate(suggestions, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                report.append(f"{i}. {priority_icon.get(suggestion['priority'], '⚪')} "
                             f"[{suggestion['category']}] {suggestion['description']}")
                report.append(f"   原理：{suggestion['principle']}")
                report.append(f"   预期效果：{suggestion['expected_impact']}")
                report.append("")
        
        # 代码修改
        code_changes = optimization_result.get('code_modifications', [])
        if code_changes:
            report.append("💻 代码修改建议")
            report.append("-" * 40)
            for i, change in enumerate(code_changes, 1):
                report.append(f"{i}. [{change['type']}] {change['reason']}")
                report.append("   修改前:")
                report.append(f"   ```python")
                report.append(f"   {change['before']}")
                report.append(f"   ```")
                report.append("   修改后:")
                report.append(f"   ```python")
                report.append(f"   {change['after']}")
                report.append(f"   ```")
                report.append(f"   预期影响：{change['impact']}")
                report.append("")
        
        # 迭代计划
        iteration_plan = optimization_result.get('iteration_plan', {})
        if iteration_plan:
            report.append("🔄 迭代优化计划")
            report.append("-" * 40)
            if iteration_plan.get('next_steps'):
                report.append("下一步行动:")
                for step in iteration_plan['next_steps']:
                    report.append(f"   • {step}")
            if iteration_plan.get('parameter_tests'):
                report.append("参数测试:")
                for test in iteration_plan['parameter_tests']:
                    report.append(f"   • {test}")
            report.append(f"预期改进：{iteration_plan.get('expected_improvement', '待评估')}")
            report.append("")
        
        report.append(f"🎯 置信度：{optimization_result.get('confidence_level', 0.8):.1%}")
        report.append("=" * 80)
        
        return "\n".join(report)


# 便捷函数
def optimize_factor_with_llm(
    factor_definition: Dict[str, Any], 
    backtest_results: Dict[str, Any],
    api_key: Optional[str] = None,
    iteration_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    使用 LLM 优化因子的便捷函数
    
    Args:
        factor_definition: 因子定义
        backtest_results: 回测结果
        api_key: API 密钥
        iteration_history: 优化历史
        
    Returns:
        优化分析结果
    """
    optimizer = LLMFactorOptimizer(api_key=api_key)
    return optimizer.analyze_and_optimize_factor(
        factor_definition, backtest_results, iteration_history
    )
