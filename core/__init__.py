"""
Core模块 - 量化因子挖掘系统核心组件

包含：
- mcp: MCP工具系统
- skill: 技能文档加载器
- path_manager: 统一路径管理
- exceptions: 自定义异常类
- logger: 统一日志系统
- prompt_manager: Prompt模板管理
- base_messages: 通用消息模板基类
"""

# 导出子模块
from . import mcp
from . import skill

# 导出路径管理器
from .path_manager import (
    PathManager,
    get_path_manager,
    ensure_project_path,
    get_project_root,
)

# 导出异常类
from .exceptions import (
    QuantSystemError,
    DataError,
    DataLoadError,
    DataValidationError,
    StockPoolError,
    FactorError,
    FactorCalculationError,
    FactorBacktestError,
    FactorScriptError,
    ConfigError,
    APIConfigError,
    MissingAPIKeyError,
    ScreeningError,
    ScreeningLogicError,
    ToolExecutionError,
    LLMError,
    LLMResponseError,
    LLMParseError,
)

# 导出日志系统
from .logger import (
    get_logger,
    configure_logging,
    LoggerMixin,
    log_info,
    log_warning,
    log_error,
    log_debug,
)

# 导出Prompt管理器
from .prompt_manager import (
    PromptManager,
    get_prompt_manager,
    render_prompt,
)

# 导出通用消息基类
from .base_messages import (
    BaseMessageMixin,
    COMMON_ERROR_MESSAGES,
    COMMON_WARNING_MESSAGES,
    COMMON_SUCCESS_MESSAGES,
    COMMON_INFO_MESSAGES,
    COMMON_HINT_MESSAGES,
)

__all__ = [
    # 子模块
    'mcp', 
    'skill',
    # 路径管理
    'PathManager',
    'get_path_manager',
    'ensure_project_path',
    'get_project_root',
    # 异常类
    'QuantSystemError',
    'DataError',
    'DataLoadError',
    'DataValidationError',
    'StockPoolError',
    'FactorError',
    'FactorCalculationError',
    'FactorBacktestError',
    'FactorScriptError',
    'ConfigError',
    'APIConfigError',
    'MissingAPIKeyError',
    'ScreeningError',
    'ScreeningLogicError',
    'ToolExecutionError',
    'LLMError',
    'LLMResponseError',
    'LLMParseError',
    # 日志系统
    'get_logger',
    'configure_logging',
    'LoggerMixin',
    'log_info',
    'log_warning',
    'log_error',
    'log_debug',
    # Prompt管理器
    'PromptManager',
    'get_prompt_manager',
    'render_prompt',
    # 通用消息基类
    'BaseMessageMixin',
    'COMMON_ERROR_MESSAGES',
    'COMMON_WARNING_MESSAGES',
    'COMMON_SUCCESS_MESSAGES',
    'COMMON_INFO_MESSAGES',
    'COMMON_HINT_MESSAGES',
]
