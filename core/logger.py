#!/usr/bin/env python3
"""
统一日志系统 - 提供一致的日志配置和管理

解决问题：
- 项目中混用 print() 和 logging
- 日志格式不统一
- 难以统一管理日志级别

使用方法：
    from core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("这是一条信息日志")
    logger.error("这是一条错误日志")
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# 日志格式
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
SIMPLE_FORMAT = '%(levelname)s - %(message)s'
DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# 日志级别映射
LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# 全局日志配置
_configured = False
_log_level = logging.INFO
_log_file: Optional[Path] = None


def configure_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_style: str = 'default'
) -> None:
    """
    配置全局日志系统
    
    Args:
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: 日志文件路径（可选）
        format_style: 格式风格 ('default', 'simple', 'detailed')
    """
    global _configured, _log_level, _log_file
    
    _log_level = LEVEL_MAP.get(level.upper(), logging.INFO)
    _log_file = Path(log_file) if log_file else None
    
    # 选择格式
    if format_style == 'simple':
        log_format = SIMPLE_FORMAT
    elif format_style == 'detailed':
        log_format = DETAILED_FORMAT
    else:
        log_format = DEFAULT_FORMAT
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(_log_level)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if _log_file:
        _log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_log_file, encoding='utf-8')
        file_handler.setLevel(_log_level)
        file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        root_logger.addHandler(file_handler)
    
    _configured = True


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    这是获取日志器的推荐方式。如果全局日志未配置，将自动进行默认配置。
    
    Args:
        name: 日志器名称（通常使用 __name__）
        
    Returns:
        配置好的日志器
        
    Example:
        from core.logger import get_logger
        
        logger = get_logger(__name__)
        logger.info("开始处理数据")
        logger.error("处理失败", exc_info=True)
    """
    global _configured
    
    if not _configured:
        configure_logging()
    
    logger = logging.getLogger(name)
    
    # 确保日志器有正确的级别
    if logger.level == logging.NOTSET:
        logger.setLevel(_log_level)
    
    return logger


class LoggerMixin:
    """
    日志混入类
    
    可以混入到任何类中，提供 self.logger 属性。
    
    Example:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.logger.info("正在执行操作")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """获取类专属的日志器"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


# 便捷函数：提供 print 风格的日志接口
def log_info(message: str, *args, **kwargs) -> None:
    """记录信息日志（替代 print）"""
    get_logger('QuantSystem').info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """记录警告日志"""
    get_logger('QuantSystem').warning(message, *args, **kwargs)


def log_error(message: str, *args, exc_info: bool = False, **kwargs) -> None:
    """记录错误日志"""
    get_logger('QuantSystem').error(message, *args, exc_info=exc_info, **kwargs)


def log_debug(message: str, *args, **kwargs) -> None:
    """记录调试日志"""
    get_logger('QuantSystem').debug(message, *args, **kwargs)


# 特殊日志函数：保持与现有 print 输出风格兼容
def print_info(message: str) -> None:
    """
    打印信息（同时输出到控制台和日志）
    
    这个函数用于保持与现有代码的兼容性，
    在保留 print 风格输出的同时也记录到日志。
    """
    print(message)
    get_logger('QuantSystem').info(message.replace('📊', '').replace('✅', '').replace('❌', '').strip())


def print_error(message: str, exc_info: bool = True) -> None:
    """
    打印错误（同时输出到控制台和日志）
    """
    print(message)
    get_logger('QuantSystem').error(message.replace('❌', '').strip(), exc_info=exc_info)
