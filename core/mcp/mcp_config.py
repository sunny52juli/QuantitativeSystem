"""
MCP 工具模块 - 统一配置管理

解决问题：
- tools_selection.py 从 config 导入 tool_categories 和 strategy_keywords
- 配置分散在多个地方，造成依赖混乱
- 统一管理 MCP 工具相关的配置

使用方式：
    from core.mcp.mcp_config import MCPConfig
    
    # 获取工具分类
    tools = MCPConfig.get_tools_by_category('math')
    
    # 检查策略关键词
    categories = MCPConfig.analyze_strategy('动量策略')
"""

from typing import Dict, List, Set


class MCPConfig:
    """
    MCP 配置管理中心
    
    统一管理：
    1. 工具分类定义
   2. 策略关键词映射
    3. MCP 服务器配置
    """
    
    # ==================== 工具分类配置 ====================
    
    TOOL_CATEGORIES: Dict[str, List[str]] = {
        "math": [
            "abs_value", "log_transform", "rank_normalize", 
            "zscore_normalize", "sqrt_transform", "power_transform", "sign"
        ],
        "time_series": [
            "rolling_mean", "rolling_std", "rolling_max", "rolling_min", 
            "rolling_sum", "lag", "delta", "pct_change", "ewm"
        ],
        "technical": [
            "rsi", "bollinger_position", "ema", "macd", "kdj", 
            "atr", "obv", "cci", "williams_r", "adx"
        ],
        "statistical": [
            "correlation", "quantile", "skewness", "kurtosis", "covariance"
        ],
        "combination": [
            "max_of", "min_of", "clip", "where", "weighted_avg"
        ],
        "feature_engineering": [
            "ts_rank", "ts_argmax", "ts_argmin", "decay_linear", 
            "highday", "lowday"
        ],
        "risk_metrics": [
            "volatility", "sharpe_ratio", "max_drawdown", "beta"
        ],
        "data_management": [
            "load_data", "save_factor", "list_factors"
        ]
    }
    
    # ==================== 策略关键词映射 ====================
    
    STRATEGY_KEYWORDS: Dict[str, List[str]] = {
        # 动量相关
        '动量': ['technical', 'time_series', 'math'],
        '趋势': ['technical', 'time_series'],
        '突破': ['technical', 'feature_engineering'],
        '反转': ['technical', 'time_series', 'math'],
        
        # 波动率相关
        '波动': ['risk_metrics', 'time_series', 'statistical'],
        '风险': ['risk_metrics'],
        '稳定': ['risk_metrics', 'math'],
        
        # 成交量相关
        '成交量': ['technical', 'time_series'],
        '放量': ['technical', 'time_series'],
        '缩量': ['technical', 'time_series'],
        '量价': ['technical', 'statistical'],
        
        # 估值相关
        '估值': ['math', 'statistical'],
        '价值': ['math', 'time_series'],
        '市盈率': ['math'],
        '市净率': ['math'],
        
        # 技术指标相关
        '均线': ['technical', 'time_series'],
        'MACD': ['technical'],
        'KDJ': ['technical'],
        'RSI': ['technical'],
        '布林': ['technical'],
        
        # 统计特征相关
        '偏度': ['statistical'],
        '峰度': ['statistical'],
        '相关': ['statistical'],
        '分布': ['statistical', 'math'],
        
        # 资金流向相关
        '资金': ['technical', 'time_series'],
        '主力': ['technical'],
        '流入': ['technical'],
        '流出': ['technical'],
        
        # 时间周期相关
        '短期': ['time_series'],
        '中期': ['time_series'],
        '长期': ['time_series'],
        '日内': ['time_series', 'math'],
    }
    
    # ==================== MCP 服务器配置 ====================
    
    MCP_SERVER_CONFIG = {
        'protocol_version': '2024-11-05',
        'server_name': 'factor-tools-mcp',
        'server_version': '1.0.0',
        'capabilities': {'tools': {}}
    }
    
    # ==================== 类方法 ====================
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[str]:
        """
        获取指定类别的工具列表
        
        Args:
            category: 类别名称
        
        Returns:
            工具名称列表
        """
        return cls.TOOL_CATEGORIES.get(category, [])
    
    @classmethod
    def get_all_tools(cls) -> List[str]:
        """
        获取所有工具名称
        
        Returns:
            所有工具名称的扁平列表
        """
        all_tools = []
        for tools in cls.TOOL_CATEGORIES.values():
            all_tools.extend(tools)
        return all_tools
    
    @classmethod
    def get_tool_category(cls, tool_name: str) -> str:
        """
        获取工具所属类别
        
        Args:
            tool_name: 工具名称
        
        Returns:
            类别名称，未找到返回 None
        """
        for category, tools in cls.TOOL_CATEGORIES.items():
            if tool_name in tools:
                return category
        return None
    
    @classmethod
    def analyze_strategy(cls, strategy: str) -> Dict[str, List[str]]:
        """
        分析策略中的关键词，返回相关类别
        
        Args:
            strategy: 策略描述文本
        
        Returns:
            包含相关类别和匹配关键词的字典
        """
        strategy_lower = strategy.lower()
        relevant_categories: Set[str] = set()
        matched_keywords: List[str] = []
        
        for keyword, categories in cls.STRATEGY_KEYWORDS.items():
            if keyword.lower() in strategy_lower or keyword in strategy:
                relevant_categories.update(categories)
                matched_keywords.append(keyword)
        
        return {
            'categories': list(relevant_categories),
            'keywords': matched_keywords
        }
    
    @classmethod
    def get_relevant_tools_for_strategy(cls, strategy: str) -> List[str]:
        """
        根据策略获取相关工具列表
        
        Args:
            strategy: 策略描述文本
        
        Returns:
            相关工具名称列表
        """
        analysis = cls.analyze_strategy(strategy)
        relevant_tools = []
        
        for category in analysis['categories']:
            relevant_tools.extend(cls.get_tools_by_category(category))
        
        return list(set(relevant_tools))
    
    @classmethod
    def categorize_tools(cls, tools: List[str]) -> Dict[str, List[str]]:
        """
        对工具列表按类别分组
        
        Args:
            tools: 工具名称列表
        
        Returns:
            按类别分组的工具字典
        """
        categorized = {cat: [] for cat in cls.TOOL_CATEGORIES}
        
        for tool in tools:
            category = cls.get_tool_category(tool)
            if category:
                categorized[category].append(tool)
            else:
                categorized.setdefault('其他', []).append(tool)
        
        # 移除空类别
        return {cat: t for cat, t in categorized.items() if t}
    
    @classmethod
    def validate_tool_name(cls, tool_name: str) -> bool:
        """
        验证工具名称是否有效
        
        Args:
            tool_name: 工具名称
        
        Returns:
            是否有效
        """
        return tool_name in cls.get_all_tools()
    
    @classmethod
    def get_tool_suggestions(cls, partial_name: str) -> List[str]:
        """
        根据部分名称获取工具建议
        
        Args:
            partial_name: 工具名称的部分
        
        Returns:
            匹配的工具名称列表
        """
        all_tools = cls.get_all_tools()
        return [
            tool for tool in all_tools 
            if partial_name.lower() in tool.lower()
        ]


# ==================== 便捷函数（向后兼容） ====================

def get_tools_by_category(category: str) -> List[str]:
    """便捷函数：获取指定类别的工具"""
    return MCPConfig.get_tools_by_category(category)


def get_tool_category(tool_name: str) -> str:
    """便捷函数：获取工具所属类别"""
    return MCPConfig.get_tool_category(tool_name)


def analyze_strategy_keywords(strategy: str) -> Dict[str, List[str]]:
    """便捷函数：分析策略关键词"""
    return MCPConfig.analyze_strategy(strategy)


def get_relevant_tools_for_strategy(strategy: str) -> List[str]:
    """便捷函数：获取策略相关工具"""
    return MCPConfig.get_relevant_tools_for_strategy(strategy)
