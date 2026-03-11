"""
MCP 工具模块 - 公共工具函数和数据适配器

解决问题：
- expression_tools.py 和 tool_implementations.py 中存在重复代码
- _get_groupby_key 和 _apply_grouped_operation 在多处定义
- 统一数据格式适配逻辑

使用方式：
    from core.mcp.utils import DataAdapter
    
    # 获取分组键
    ts_code_key = DataAdapter.get_groupby_key(data, 'ts_code')
    
    # 应用分组操作
    result = DataAdapter.apply_grouped_operation(data, field_data, lambda x: x.rolling(20).mean())
"""

import pandas as pd
import numpy as np
from typing import Callable, Any


class DataAdapter:
    """
    数据适配器 - 智能处理不同的数据格式
    
    支持三种数据格式：
    1. 双索引 (trade_date, ts_code) - 多股票时间序列
   2. 单索引 ts_code - 单日期多股票（预筛选阶段）
    3. 单索引 trade_date - 单股票时间序列（批量筛选阶段）
    """
    
    @staticmethod
    def get_groupby_key(data: pd.DataFrame, key: str):
        """
        获取分组键，适配双索引结构
        
        Args:
            data: 数据 DataFrame（可能是双索引）
            key: 分组键名称（'ts_code' 或 'trade_date'）
        
        Returns:
            分组键（Series 或 Index level），如果是单股票/单日期数据且无法分组则返回 None
        """
        if isinstance(data.index, pd.MultiIndex):
            # 双索引情况，从索引中获取
            if key in data.index.names:
                return data.index.get_level_values(key)
            else:
                raise ValueError(f"索引中不存在 {key}")
        else:
            # 单索引情况
            # 1. 先检查索引名称是否匹配
            if data.index.name == key:
                return data.index
            # 2. 再检查列中是否存在
            elif key in data.columns:
                return data[key]
            else:
                # 3. 单股票/单日期数据，无法按该 key 分组
                # 返回 None，让调用方决定如何处理
                return None
    
    @staticmethod
    def apply_grouped_operation(
        data: pd.DataFrame, 
        field_data: pd.Series, 
        operation: Callable, 
        group_by_stock: bool = True
    ) -> pd.Series:
        """
        智能应用分组操作，自动适配不同的数据格式
        
        Args:
            data: 数据 DataFrame
            field_data: 要操作的 Series
            operation: 操作函数，接受 Series 或 GroupBy 对象
            group_by_stock: 是否按股票分组（默认 True）
        
        Returns:
            pd.Series: 操作结果
        """
        # 情况 1: 双索引数据（多股票时间序列）
        if isinstance(data.index, pd.MultiIndex):
            if group_by_stock:
                ts_code_key = DataAdapter.get_groupby_key(data, 'ts_code')
                result = operation(field_data.groupby(ts_code_key))
            else:
                raise ValueError("按股票分组的操作无法在单索引数据中执行")
            result.index = data.index
            return result
        
        # 情况 2: 单索引 ts_code（单日期多股票，预筛选阶段）
        elif data.index.name == 'ts_code':
            # 单日期数据，大多数时间序列操作无法执行，返回全 NaN
            result = pd.Series(np.nan, index=data.index)
            return result
        
        # 情况 3: 单索引 trade_date（单股票时间序列，批量筛选阶段）
        elif data.index.name == 'trade_date' or isinstance(data.index, pd.DatetimeIndex):
            # 单股票数据，直接操作（不需要分组）
            result = operation(field_data)
            result.index = data.index
            return result
        
        # 其他情况：尝试直接操作
        else:
            result = operation(field_data)
            result.index = data.index
            return result
    
    @staticmethod
    def ensure_series_with_index(
        data: pd.DataFrame, 
        series_or_column
    ) -> pd.Series:
        """
        确保返回的 Series 具有与 data 相同的索引
        
        Args:
            data: 原始数据 DataFrame
            series_or_column: Series 或列名
        
        Returns:
            pd.Series: 具有正确索引的 Series
        """
        if isinstance(series_or_column, str):
            # 如果是列名，从 data 中获取
            result = data[series_or_column]
        else:
            result = series_or_column
        
        # 确保索引对齐
        if not isinstance(result, pd.Series):
            result = pd.Series(result, index=data.index)
        elif not result.index.equals(data.index):
            result = result.copy()
            result.index = data.index
        
        return result


class ExpressionHelpers:
    """
    表达式辅助函数
    
    提供常用的表达式构建和验证功能
    """
    
    @staticmethod
    def is_expression(field_name: str) -> bool:
        """
        判断字段名是否是一个表达式（而非简单变量名）
        
        表达式特征：包含运算符或括号
        """
        expression_chars = ['+', '-', '*', '/', '(', ')', ' ']
        return any(char in field_name for char in expression_chars)
    
    @staticmethod
    def build_namespace(
        data: pd.DataFrame, 
        computed_vars: dict = None,
        extra_functions: dict = None
    ) -> dict:
        """
        构建基础命名空间
        
        Args:
            data: 原始数据 DataFrame
            computed_vars: 已计算的变量字典
            extra_functions: 额外的函数
        
        Returns:
            命名空间字典
        """
        if computed_vars is None:
            computed_vars = {}
        
        namespace = {}
        
        # 添加已计算的变量
        namespace.update(computed_vars)
        
        # 添加数据列
        for col in data.columns:
            namespace[col] = data[col]
        
        # 添加数学函数
        namespace['np'] = np
        namespace['abs'] = np.abs
        namespace['log'] = lambda x: np.log(np.abs(x) + 1e-10)
        namespace['sqrt'] = lambda x: np.sqrt(np.abs(x))
        namespace['sign'] = np.sign
        namespace['max'] = np.maximum
        namespace['min'] = np.minimum
        
        # 添加额外函数
        if extra_functions:
            namespace.update(extra_functions)
        
        return namespace
    
    @staticmethod
    def eval_expression(
        data: pd.DataFrame, 
        expr: str, 
        computed_vars: dict = None
    ) -> pd.Series:
        """
        计算表达式
        
        Args:
            data: 原始数据 DataFrame
            expr: 表达式字符串
            computed_vars: 已计算的变量字典
        
        Returns:
            pd.Series: 计算结果
        """
        namespace = ExpressionHelpers.build_namespace(data, computed_vars)
        
        try:
            result = eval(expr, {"__builtins__": {}}, namespace)
            
            # 确保返回 Series
            if not isinstance(result, pd.Series):
                result = pd.Series(result, index=data.index)
            elif not result.index.equals(data.index):
                result = result.copy()
                result.index = data.index
            
            return result
        except Exception as e:
            raise ValueError(f"表达式计算失败：{expr}, 错误：{e}")


# 便捷函数（向后兼容）
def get_groupby_key(data: pd.DataFrame, key: str):
    """便捷函数：获取分组键"""
    return DataAdapter.get_groupby_key(data, key)


def apply_grouped_operation(
    data: pd.DataFrame, 
    field_data: pd.Series, 
    operation: Callable, 
    group_by_stock: bool = True
) -> pd.Series:
    """便捷函数：应用分组操作"""
    return DataAdapter.apply_grouped_operation(data, field_data, operation, group_by_stock)


def ensure_series_with_index(data: pd.DataFrame, series_or_column) -> pd.Series:
    """便捷函数：确保 Series 索引对齐"""
    return DataAdapter.ensure_series_with_index(data, series_or_column)
