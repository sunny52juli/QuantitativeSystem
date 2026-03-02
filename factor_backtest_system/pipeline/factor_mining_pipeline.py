#!/usr/bin/env python3
"""
因子挖掘流程管道 - 负责协调整个因子挖掘流程

此模块是调用入口，负责：
1. 创建和管理 FactorMiningAgent
2. 协调数据加载、因子生成、回测等流程
3. 提供便捷函数和预定义策略
"""

from typing import Dict, List, Optional, Any
import pandas as pd

# 从 agent 模块导入
from factor_backtest_system.agent.mining_agent import FactorMiningAgent
from factor_backtest_system.agent.ai_factor_agent import AIFactorMiner

# 从 datamodule 模块导入数据加载器
from datamodule import FactorDataLoader

# 从配置模块导入
from factor_backtest_system.prompt.factor_prompts import StrategyPrompts, get_message


# ==================== 便捷函数 ====================

def create_factor_miner(data=None, api_key=None):
    """
    创建因子挖掘代理实例
    
    Args:
        data: 股票数据 DataFrame，如果为 None 则自动加载
        api_key: API 密钥
        
    Returns:
        FactorMiningAgent 实例
    """
    return FactorMiningAgent(data=data, api_key=api_key)


def get_available_tools():
    """获取可用工具列表"""
    return FactorMiningAgent.get_available_tools()


def select_tools_for_strategy(strategy: str):
    """为策略选择相关工具"""
    return FactorMiningAgent.select_tools_for_strategy(strategy)


# ==================== 预定义策略 ====================

StrategyTemplates = StrategyPrompts


# ==================== 专用入口函数 ====================

def generate_recent_strong_stock_factors(
    n_factors: int = 3, 
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    生成近日强势股票因子
    
    Args:
        n_factors: 因子数量
        api_key: API 密钥
        
    Returns:
        生成的因子列表和回测结果
    """
    try:
        agent = FactorMiningAgent(api_key=api_key)
        
        result = agent.run_complete_pipeline(
            strategy=StrategyTemplates.RECENT_STRONG_STOCKS,
            n_factors=n_factors,
            strategy_name="近日强势股票"
        )
        
        return result
        
    except ValueError as e:
        print(get_message('ERROR', 'no_api_key_error'))
        print(get_message('HINT', 'export_api_key'))
        return None
    except Exception as e:
        print(get_message('ERROR', 'system_failed', error=str(e)))
        import traceback
        traceback.print_exc()
        return None


def generate_optimization_suggestions(
    factors: List[Dict], 
    backtest_results: List[Dict]
) -> List[Dict]:
    """
    生成因子优化建议
    
    Args:
        factors: 因子列表
        backtest_results: 回测结果列表
        
    Returns:
        优化建议列表
    """
    try:
        agent = FactorMiningAgent()
        return agent.generate_optimization_suggestions(factors, backtest_results)
    except:
        return []


# ==================== 导出列表 ====================

__all__ = [
    # Agent 相关
    'FactorMiningAgent',
    'AIFactorMiner',
    'ToolExecutor',
    
    # Datamodule 相关
    'FactorDataLoader',
    
    # 便捷函数
    'create_factor_miner',
    'get_available_tools',
    'select_tools_for_strategy',
    'generate_recent_strong_stock_factors',
    'generate_optimization_suggestions',
    
    # 预定义策略
    'StrategyTemplates',
]