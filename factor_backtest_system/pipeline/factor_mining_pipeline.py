#!/usr/bin/env python3
"""
因子挖掘流程管道 - 负责协调和调用各模块

此模块是调用入口，负责：
1. 调用 agent 模块进行因子挖掘
2. 调用 datamodule 模块加载数据
3. 提供便捷函数和预定义策略
"""

from typing import Dict, List, Optional, Any

# 从 agent 模块导入 LLM Agent 相关功能
from factor_backtest_system.agent import FactorMiningAgent, AIFactorMiner

# 从 tools 模块导入工具相关功能
from factor_backtest_system.tools import ToolExecutor

# 从 datamodule 模块导入数据加载相关功能
from datamodule import FactorDataLoader

# 从配置模块导入
from factor_backtest_system.prompt.factor_prompts import StrategyPrompts, get_message
from core.mcp.tools_selection import select_relevant_tools, load_mcp_tools


# ==================== 便捷函数 ====================

def create_factor_miner(data=None, api_key=None):
    """
    创建因子挖掘代理实例的便捷函数
    
    Args:
        data: 股票数据 DataFrame，如果为None则自动加载
        api_key: API密钥，如果为None则从环境变量读取
        
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

# 策略模板类（从配置文件导入）
StrategyTemplates = StrategyPrompts


# ==================== 专用入口函数 ====================

def generate_recent_strong_stock_factors(
    n_factors: int = 3, 
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    生成近日强势股票因子的专用入口函数
    
    Args:
        n_factors: 要生成的因子数量
        api_key: API密钥
        
    Returns:
        生成的因子列表和回测结果
    """
    try:
        # 创建代理
        agent = FactorMiningAgent(api_key=api_key)
        
        # 运行完整流程
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