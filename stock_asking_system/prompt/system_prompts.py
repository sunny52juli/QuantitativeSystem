#!/usr/bin/env python3
"""
股票问答系统 - 系统提示词模板

📖 使用说明：
本文件包含系统级的模板结构和工具函数，一般不需要修改。
如需自定义业务内容（策略、查询示例等），请修改 user_config.py。

模块结构：
- StockQueryPrompts: 主类，提供所有 Prompt 相关的方法
- get_system_prompt(): 获取系统角色设定
- get_user_query_prompt(): 获取用户查询模板
- get_demo_queries(): 获取演示查询列表
- get_screening_system_prompt(): 获取筛选系统 Prompt
"""

import logging
from typing import List

from .user_config import (
    QUERY_EXAMPLES,
    SYSTEM_ROLE,
    USER_QUERY_FORMAT,
    SCREENING_SYSTEM_PROMPT,
)
from core.base_messages import (
    BaseMessageMixin,
    COMMON_ERROR_MESSAGES,
    COMMON_WARNING_MESSAGES,
    COMMON_SUCCESS_MESSAGES,
    COMMON_INFO_MESSAGES,
    COMMON_HINT_MESSAGES,
)

logger = logging.getLogger(__name__)


# ==================== 类封装（主接口） ====================

class StockQueryPrompts(BaseMessageMixin):
    """
    股票查询 Prompts（从 user_config 加载）

    继承 BaseMessageMixin 获得通用消息和 get_message 方法。
    通过 {**COMMON_xxx, ...} 合并通用消息，并添加本系统特有的消息。
    """

    # 动态加载查询示例（浅拷贝，防止外部修改影响本类）
    _query_examples = dict(QUERY_EXAMPLES)

    # 系统模板（从 user_config 模块加载）
    SYSTEM_PROMPT_TEMPLATE = SYSTEM_ROLE
    USER_QUERY_TEMPLATE = USER_QUERY_FORMAT
    SCREENING_SYSTEM_PROMPT_TEMPLATE = SCREENING_SYSTEM_PROMPT

    # ==================== 消息模板（继承通用 + 本系统特有） ====================

    # 错误消息：通用 + 本系统特有
    ERROR_MESSAGES = {
        **COMMON_ERROR_MESSAGES,
        'no_api_key': "❌ 未检测到 API 密钥，请设置环境变量 DEFAULT_API_KEY",
        'query_failed': "❌ 查询失败：{error}",
        'no_results': "📭 未找到符合条件的股票",
        'invalid_response': "⚠️ AI 返回格式无效，请重试",
        'api_error': "❌ API 调用失败：{error}",
        'data_error': "❌ 数据加载失败：{error}",
        'filter_failed': "❌ 股票筛选失败：{error}",
    }

    # 警告消息：通用 + 本系统特有
    # 注意：与通用消息相同的键不再重复定义，仅添加本系统特有消息
    WARNING_MESSAGES = {
        **COMMON_WARNING_MESSAGES,
        'partial_results': "⚠️ 仅找到部分结果：{count} 只股票",
        'low_confidence': "⚠️ 所有结果置信度较低（<0.5），建议调整查询条件",
        'data_incomplete': "⚠️ 数据不完整，部分股票可能被排除",
        'nan_values_detail': "⚠️ 指标 {indicator} 包含 {count} 个无效值",
        'tool_unavailable': "⚠️ MCP 工具 {tool_name} 不可用，使用备用方案",
    }

    # 成功消息：通用 + 本系统特有
    SUCCESS_MESSAGES = {
        **COMMON_SUCCESS_MESSAGES,
        'query_started': "🔍 正在分析查询：{query}",
        'data_loaded': "✅ 数据加载完成，股票池：{count} 只",
        'analysis_complete': "✅ 分析完成，找到 {count} 只符合条件的股票",
        'agent_ready': "✅ 股票查询代理已就绪",
        'agent_initialized': "✅ 股票查询代理初始化完成",
        'indicator_calculated': "✅ 技术指标计算完成",
        'stocks_filtered': "✅ 股票筛选完成：{count} 只",
        'stocks_ranked': "✅ 股票排序完成",
    }

    # 信息消息：通用 + 本系统特有
    INFO_MESSAGES = {
        **COMMON_INFO_MESSAGES,
        'generating_data': "📊 正在加载市场数据...",
        'analyzing': "🤖 AI 正在分析...",
        'calculating': "📊 计算技术指标...",
        'filtering': "🔎 筛选股票...",
        'ranking': "📈 按置信度排序...",
        'using_tools': "🔧 使用 MCP 工具：{tool_name}",
        'processing_stock': "🔍 处理股票 {current}/{total}: {stock_code}",
        'query_received': "📥 收到查询：{query}",
    }

    # 提示消息：通用 + 本系统特有
    HINT_MESSAGES = {
        **COMMON_HINT_MESSAGES,
        'set_api_key': "💡 提示：设置 DEFAULT_API_KEY 环境变量以启用 AI 分析",
        'adjust_query': "💡 提示：尝试调整查询条件以获得更好的结果",
        'check_data': "💡 提示：检查数据时间范围和股票池设置",
        'use_demo': "💡 提示：可以尝试预定义的演示查询",
    }

    # ==================== 业务方法 ====================

    @classmethod
    def get_system_prompt(cls) -> str:
        """获取系统提示词（注入 SKILL.md 内容）"""
        return cls.SYSTEM_PROMPT_TEMPLATE.format(skill_content=SKILL_CONTENT)

    @classmethod
    def get_user_query_prompt(cls, query: str, stock_count: int,
                             lookback_days: int, top_n: int) -> str:
        """
        获取用户查询提示词

        Args:
            query: 用户查询（不能为空）
            stock_count: 股票池数量（正整数）
            lookback_days: 回溯天数（正整数）
            top_n: 返回数量（正整数）

        Returns:
            格式化的用户查询提示词

        Raises:
            ValueError: 当参数不合法时抛出
        """
        if not query or not query.strip():
            raise ValueError("查询内容 query 不能为空")
        if not isinstance(stock_count, int) or stock_count <= 0:
            raise ValueError(f"stock_count 必须为正整数，当前值：{stock_count}")
        if not isinstance(lookback_days, int) or lookback_days <= 0:
            raise ValueError(f"lookback_days 必须为正整数，当前值：{lookback_days}")
        if not isinstance(top_n, int) or top_n <= 0:
            raise ValueError(f"top_n 必须为正整数，当前值：{top_n}")

        return cls.USER_QUERY_TEMPLATE.format(
            query=query,
            stock_count=stock_count,
            lookback_days=lookback_days,
            top_n=top_n
        )

    @classmethod
    def get_demo_queries(cls) -> List[str]:
        """
        获取演示查询列表（从 user_config.QUERY_EXAMPLES 加载）

        Returns:
            查询字符串列表，顺序与 user_config.QUERY_EXAMPLES 定义顺序一致
        """
        return list(cls._query_examples.values())

    @classmethod
    def get_screening_system_prompt_template(cls) -> str:
        """
        获取筛选逻辑系统 Prompt 模板
        
        Returns:
            筛选系统 Prompt 模板字符串（包含占位符 ${tools_desc}, ${industries_desc} 等）
        """
        return cls.SCREENING_SYSTEM_PROMPT_TEMPLATE


# 为向后兼容，将查询示例作为类属性动态注入（带冲突检测）
_RESERVED_ATTRS = {attr for attr in dir(StockQueryPrompts) if not attr.startswith('__')}
for _name, _query in QUERY_EXAMPLES.items():
    if _name in _RESERVED_ATTRS:
        logger.warning(
            f"查询示例键名 '{_name}' 与 StockQueryPrompts 已有属性冲突，已跳过注入。"
            f"请在 user_config/query_examples.py 中修改该键名。"
        )
        continue
    setattr(StockQueryPrompts, _name, _query)
del _RESERVED_ATTRS

