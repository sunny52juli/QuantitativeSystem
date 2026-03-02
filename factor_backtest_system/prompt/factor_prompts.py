#!/usr/bin/env python3
"""
因子回测系统 - 系统模板文件（一般不需要修改）

本文件包含系统级的模板结构和工具函数：
- 消息模板（成功/警告/错误/信息/提示）
- 类封装（保持向后兼容）
- 便捷访问函数

⚠️ 除非了解系统架构，否则不建议修改本文件。
    如需自定义业务内容，请修改 factor_config.py。
"""

from . import factor_config as _config
from core.base_messages import (
    BaseMessageMixin,
    COMMON_ERROR_MESSAGES,
    COMMON_WARNING_MESSAGES,
    COMMON_SUCCESS_MESSAGES,
    COMMON_INFO_MESSAGES,
    COMMON_HINT_MESSAGES,
)


# ==================== 类封装（向后兼容） ====================

class StrategyPrompts:
    """策略模板 Prompts（从 factor_config 加载）"""

    # 动态加载策略配置
    _strategies = _config.STRATEGY_CONFIGS

    @classmethod
    def get(cls, strategy_name: str) -> str:
        """获取策略 prompt"""
        return cls._strategies.get(strategy_name, "")

    @classmethod
    def list_strategies(cls) -> list:
        """列出所有可用策略名称"""
        return list(cls._strategies.keys())

    # 保持向后兼容：通过属性名直接访问
    def __class_getitem__(cls, key):
        return cls._strategies.get(key, "")


# 为向后兼容，将策略配置作为类属性动态注入
for _name, _prompt in _config.STRATEGY_CONFIGS.items():
    setattr(StrategyPrompts, _name, _prompt)


class AIFactorMinerPrompts:
    """AI因子挖掘器 Prompts（从 factor_config 加载）"""

    SYSTEM_PROMPT_TEMPLATE = _config.SYSTEM_ROLE
    USER_PROMPT_TEMPLATE = _config.USER_REQUEST_FORMAT
    FALLBACK_SKILL_CONTENT = _config.FALLBACK_SKILL_CONTENT


class FactorMiningAgentPrompts:
    """因子挖掘代理 Prompts（从 factor_config 加载）"""

    OPTIMIZATION_SUGGESTIONS = _config.OPTIMIZATION_SUGGESTIONS


# ==================== 消息模板（继承通用基类） ====================

class MessageTemplates(BaseMessageMixin):
    """
    消息模板 - 继承 BaseMessageMixin 获得通用消息和 get_message 方法

    通过 {**COMMON_xxx, ...} 合并通用消息，并添加本系统特有的消息。
    如果本系统需要覆盖通用消息，直接在字典中定义同名 key 即可。
    """

    # 成功消息：通用 + 本系统特有
    SUCCESS_MESSAGES = {
        **COMMON_SUCCESS_MESSAGES,
        'factor_generated': "✅ 成功生成 {count} 个因子",
        'factor_computed': "✅ 因子计算成功，数据点: {count}",
        'backtest_completed': "✅ 回测完成",
        'skill_loaded': "✅ 成功从SKILL.md加载技能文档",
    }

    # 警告消息：通用 + 本系统特有（覆盖通用的部分描述）
    WARNING_MESSAGES = {
        **COMMON_WARNING_MESSAGES,
        'no_api_key': "⚠️ 未找到DEFAULT_API_KEY，回退到规则生成",
        'ai_mode_disabled': "⚠️ AI Agent模式: 未启用（使用规则生成）",
        'nan_values': "⚠️ 变量 {var_name} 包含 {count} 个NaN值 ({percentage:.1f}%)",
        'partial_nan': "⚠️ 提示: 前{count}个值为NaN（可能是滚动窗口导致）",
        'all_nan': "❌ 警告: 所有值都是NaN！",
        'invalid_format': "⚠️ 返回格式不是列表，回退到规则生成",
        'no_valid_factors': "⚠️ 没有有效因子，回退到规则生成",
        'skill_not_found': "SKILL.md文件未找到，使用简化技能文档作为fallback",
    }

    # 错误消息：通用 + 本系统特有（覆盖通用的部分描述）
    ERROR_MESSAGES = {
        **COMMON_ERROR_MESSAGES,
        'factor_generation_failed': "❌ 因子生成失败",
        'backtest_failed': "❌ 因子回测失败: {error}",
        'computation_failed': "❌ 因子计算失败: {error}",
        'api_timeout': "❌ API调用超时，回退到规则生成",
    }

    # 信息消息：通用 + 本系统特有
    INFO_MESSAGES = {
        **COMMON_INFO_MESSAGES,
        'generating_data': "📊 生成示例数据...",
        'agent_started': "🤖 AI因子挖掘器 已启动（MCP工具集成）",
        'agent_initialized': "✅ 因子挖掘代理初始化完成",
        'generating_factors': "🤖 Agent正在生成因子...",
        'backtesting': "📈 开始回测 {count} 个因子...",
        'backtesting_factor': "🔍 回测因子 {current}/{total}: {name}",
        'optimization_suggestions': "💡 生成优化建议...",
        'complete_pipeline': "🚀 启动因子挖掘完整流程",
        'using_api': "🤖 使用AI Agent生成因子...",
        'parsed_factor': "✅ 解析因子: {name}",
        'ai_enabled': "✅ AI Agent模式: 已启用（使用DeepSeek API）",
        'available_tools': "💡 可用工具: {count}个",
        'supports_complex': "🔧 支持构建复杂时间序列因子",
        'skill_length': "📚 技能文档长度: {length} 字符",
    }

    # 提示消息：通用 + 本系统特有（覆盖通用的部分描述）
    HINT_MESSAGES = {
        **COMMON_HINT_MESSAGES,
        'set_api_key': "提示: 设置DEFAULT_API_KEY环境变量以启用AI生成",
        'nan_reasons': """可能原因:
      1. 滚动窗口大于数据长度
      2. 输入数据包含NaN
      3. 数学运算产生NaN（如除零）
      4. 数据没有正确分组""",
    }


# ==================== 便捷访问函数 ====================

def get_strategy_prompt(strategy_name: str) -> str:
    """
    获取策略 prompt

    Args:
        strategy_name: 策略名称（如 RECENT_STRONG_STOCKS）

    Returns:
        策略 prompt 文本
    """
    return StrategyPrompts.get(strategy_name)


def get_system_prompt(skill_content: str) -> str:
    """
    获取系统 prompt

    Args:
        skill_content: 技能文档内容

    Returns:
        系统 prompt 文本
    """
    return AIFactorMinerPrompts.SYSTEM_PROMPT_TEMPLATE.format(skill_content=skill_content)


def get_user_prompt(strategy: str, n_factors: int) -> str:
    """
    获取用户 prompt

    Args:
        strategy: 策略描述
        n_factors: 因子数量

    Returns:
        用户 prompt 文本
    """
    return AIFactorMinerPrompts.USER_PROMPT_TEMPLATE.format(
        strategy=strategy,
        n_factors=n_factors
    )


def get_message(category: str, key: str, **kwargs) -> str:
    """
    获取消息模板（委托给 MessageTemplates.get_message）

    Args:
        category: 消息类别（SUCCESS, WARNING, ERROR, INFO, HINT）
        key: 消息键
        **kwargs: 格式化参数

    Returns:
        格式化后的消息文本
    """
    return MessageTemplates.get_message(category, key, **kwargs)

