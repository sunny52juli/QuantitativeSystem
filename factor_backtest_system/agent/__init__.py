#!/usr/bin/env python3
"""
Agent 模块 - LLM Agent 相关功能

包含：
- AIFactorMiner: AI 因子挖掘 Agent（调用 LLM 生成因子）
- FactorMiningAgent: 因子挖掘流程代理（协调整个流程）
- RuleBasedFactorOptimizer: 基于规则的因子优化器（降级方案）
- LLMFactorOptimizer: LLM 驱动的因子优化器
"""

from factor_backtest_system.agent.ai_factor_agent import AIFactorMiner
from factor_backtest_system.agent.mining_agent import FactorMiningAgent
from factor_backtest_system.agent.rule_based_optimizer import RuleBasedFactorOptimizer, generate_rule_based_suggestions
from factor_backtest_system.agent.llm_optimizer import LLMFactorOptimizer, optimize_factor_with_llm

__all__ = [
    'AIFactorMiner',
    'FactorMiningAgent',
    'RuleBasedFactorOptimizer',
    'LLMFactorOptimizer',
    'generate_rule_based_suggestions',
    'optimize_factor_with_llm'
]
