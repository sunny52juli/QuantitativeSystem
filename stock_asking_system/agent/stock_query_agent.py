#!/usr/bin/env python3
"""
股票查询Agent - 基于自然语言的智能股票筛选系统

这是一个兼容层，保持向后兼容性。
实际功能已迁移到 StockQueryPipeline。

示例：
    用户："所有均线发散的股票"
    系统：理解为多头排列 -> 生成MA计算逻辑 -> 筛选股票 -> 输出结果+置信度
"""

import pandas as pd
from typing import Dict, List, Optional, Any

# 注意：StockQueryPipeline 使用延迟导入，避免循环导入问题


class StockQueryAgent:
    """
    股票查询代理类 - 兼容层
    
    实际功能已迁移到 StockQueryPipeline。
    此类保留以保持向后兼容性。
    
    示例：
        query_agent = StockQueryAgent()
        results = query_agent.query_stocks("所有均线发散的股票")
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, api_key: Optional[str] = None):
        """
        初始化股票查询代理
        
        Args:
            data: 股票数据 DataFrame，如果为None则从本地获取数据
            api_key: API密钥，如果为None则从环境变量读取
        """
        # 延迟导入，避免循环导入问题
        from stock_asking_system.pipeline.stock_query_pipeline import StockQueryPipeline
        
        # 创建内部 Pipeline 实例
        self._pipeline = StockQueryPipeline(data=data, api_key=api_key)
        
        # 暴露属性以保持兼容性
        self.data = self._pipeline.data
        self.available_tools = self._pipeline.available_tools
        self.available_industries = self._pipeline.available_industries
        self.screener = self._pipeline.screener
    
    def query_stocks(self, query: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        根据自然语言查询筛选股票
        
        Args:
            query: 用户的自然语言查询
            top_n: 返回的股票数量上限
            
        Returns:
            符合条件的股票列表
        """
        return self._pipeline.query(query, top_n=top_n)


# ==================== 便捷函数 ====================

def create_stock_query_agent(data: Optional[pd.DataFrame] = None, api_key: Optional[str] = None) -> StockQueryAgent:
    """创建股票查询代理实例的便捷函数"""
    return StockQueryAgent(data=data, api_key=api_key)