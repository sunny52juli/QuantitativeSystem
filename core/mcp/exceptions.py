"""
MCP 工具模块 - 统一异常处理

解决问题：
- factor_tools_mcp.py 使用 JSON-RPC 错误响应
- tool_implementations.py 抛出 Python 异常
- expression_tools.py 混合使用 print 和异常

提供统一的异常体系和错误码定义
"""

from typing import Any, Dict, Optional


# ==================== 错误码定义 ====================

class ErrorCodes:
    """错误码常量定义"""
    
    # 通用错误 (-32000 ~ -32099)
    INTERNAL_ERROR = -32000
    PARSE_ERROR = -32001
    INVALID_REQUEST = -32002
    METHOD_NOT_FOUND = -32003
    INVALID_PARAMS = -32004
    
    # 工具执行错误 (-32100 ~ -32199)
    TOOL_NOT_FOUND = -32100
    TOOL_EXECUTION_FAILED = -32101
    TOOL_INVALID_PARAMS = -32102
    TOOL_DEPENDENCY_MISSING = -32103
    
    # 表达式错误 (-32200 ~ -32299)
    EXPRESSION_SYNTAX_ERROR = -32200
    EXPRESSION_EVAL_FAILED = -32201
    EXPRESSION_INVALID_FIELD = -32202
    EXPRESSION_VARIABLE_NOT_FOUND = -32203
    
    # 数据错误 (-32300 ~ -32399)
    DATA_NOT_FOUND = -32300
    DATA_FORMAT_ERROR = -32301
    DATA_INDEX_MISMATCH = -32302
    DATA_MISSING_COLUMN = -32303
    
    # 技能验证错误 (-32400 ~ -32499)
    SKILL_VALIDATION_FAILED = -32400
    SKILL_INVALID_FIELD = -32401
    SKILL_INVALID_TOOL = -32402
    SKILL_CONSTRAINT_VIOLATED = -32403


# ==================== 异常类定义 ====================

class MCPError(Exception):
    """
    MCP 基础异常类
    
    Attributes:
        code: 错误码
        message: 错误消息
        data: 附加数据
    """
    
    def __init__(
        self, 
        message: str, 
        code: int = ErrorCodes.INTERNAL_ERROR,
        data: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data
        }
    
    def __str__(self) -> str:
        return f"[Error {self.code}] {self.message}"


class ToolExecutionError(MCPError):
    """工具执行异常"""
    
    def __init__(self, message: str, tool_name: str = None, **kwargs):
        data = {'tool_name': tool_name, **kwargs}
        super().__init__(message, ErrorCodes.TOOL_EXECUTION_FAILED, data)


class ToolNotFoundError(MCPError):
    """工具未找到异常"""
    
    def __init__(self, tool_name: str):
        super().__init__(
            f"工具不存在：{tool_name}",
            ErrorCodes.TOOL_NOT_FOUND,
            {'tool_name': tool_name}
        )


class ExpressionEvalError(MCPError):
    """表达式评估异常"""
    
    def __init__(self, message: str, expression: str = None, **kwargs):
        data = {'expression': expression, **kwargs}
        super().__init__(message, ErrorCodes.EXPRESSION_EVAL_FAILED, data)


class ExpressionSyntaxError(MCPError):
    """表达式语法错误"""
    
    def __init__(self, message: str, expression: str = None):
        data = {'expression': expression}
        super().__init__(message, ErrorCodes.EXPRESSION_SYNTAX_ERROR, data)


class InvalidFieldError(MCPError):
    """无效字段错误"""
    
    def __init__(self, field_name: str, available_fields: list = None):
        message = f"无效字段：{field_name}"
        if available_fields:
            message += f"\n可用字段：{available_fields[:10]}"
        super().__init__(message, ErrorCodes.EXPRESSION_INVALID_FIELD, 
                        {'field_name': field_name})


class DataFormatError(MCPError):
    """数据格式错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCodes.DATA_FORMAT_ERROR, kwargs)


class SkillValidationError(MCPError):
    """技能验证失败"""
    
    def __init__(self, message: str, errors: list = None):
        data = {'errors': errors or []}
        super().__init__(message, ErrorCodes.SKILL_VALIDATION_FAILED, data)


# ==================== 错误响应构建器 ====================

class ErrorResponseBuilder:
    """
    错误响应构建器
    
    用于构建标准的 JSON-RPC 错误响应
    """
    
    @staticmethod
    def build_error(
        error: Exception,
        request_id: Any = None
    ) -> Dict[str, Any]:
        """
        构建错误响应
        
        Args:
            error: 异常对象
            request_id: 请求 ID
        
        Returns:
            JSON-RPC 错误响应字典
        """
        if isinstance(error, MCPError):
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': error.code,
                    'message': error.message,
                    'data': error.data
                }
            }
        else:
            # 普通异常
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': ErrorCodes.INTERNAL_ERROR,
                    'message': str(error),
                    'data': {'exception_type': type(error).__name__}
                }
            }
    
    @staticmethod
    def build_success_response(
        result: Any,
        request_id: Any = None
    ) -> Dict[str, Any]:
        """
        构建成功响应
        
        Args:
            result: 结果数据
            request_id: 请求 ID
        
        Returns:
            JSON-RPC 成功响应字典
        """
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        }


# ==================== 装饰器工具 ====================

import functools
import logging

logger = logging.getLogger(__name__)


def handle_tool_errors(func):
    """
    工具执行错误处理装饰器
    
    用法:
        @handle_tool_errors
        def my_tool(data, params):
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPError:
            # 已经是 MCP 异常，直接抛出
            raise
        except KeyError as e:
            raise ToolExecutionError(
                f"缺少必需参数：{e}",
                tool_name=func.__name__
            )
        except TypeError as e:
            raise ToolExecutionError(
                f"参数类型错误：{e}",
                tool_name=func.__name__
            )
        except ValueError as e:
            raise ToolExecutionError(
                str(e),
                tool_name=func.__name__
            )
        except Exception as e:
            logger.error(f"工具 {func.__name__} 执行失败：{e}", exc_info=True)
            raise ToolExecutionError(
                f"工具执行失败：{e}",
                tool_name=func.__name__,
                original_error=str(e)
            )
    return wrapper


def validate_expression(func):
    """
    表达式验证装饰器
    
    用法:
        @validate_expression
        def evaluate(expr, data):
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取表达式参数
        expr = kwargs.get('expr') or (args[1] if len(args) > 1 else None)
        
        if not expr:
            raise ExpressionSyntaxError("表达式不能为空")
        
        if not isinstance(expr, str):
            raise ExpressionSyntaxError("表达式必须是字符串", expression=str(expr))
        
        try:
            return func(*args, **kwargs)
        except ExpressionEvalError:
            raise
        except Exception as e:
            raise ExpressionEvalError(
                f"表达式计算失败：{e}",
                expression=expr
            )
    return wrapper
