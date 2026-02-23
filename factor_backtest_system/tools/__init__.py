"""
因子回测系统 - 工具模块

提供共享的辅助函数和工具类
注意: skill_loader 从 core.skill 导入，避免重复代码
"""

# 从 core.skill 模块导入 skill 相关功能（统一使用 core 模块）
from core.skill import load_skill_content, SKILL_CONTENT

# factor_backtest_system 特有的工具
from factor_backtest_system.tools.tool_executor import ToolExecutor
from factor_backtest_system.tools.filename_utils import sanitize_filename, to_class_name

__all__ = [
    'load_skill_content',
    'SKILL_CONTENT',
    'ToolExecutor',
    'sanitize_filename',
    'to_class_name',
]
