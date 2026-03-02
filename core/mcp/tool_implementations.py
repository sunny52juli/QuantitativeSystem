"""
工具实现的单一数据源
所有工具的实际计算逻辑都在这里

这个模块被以下两个地方调用：
1. factor_generator.py 的 ToolExecutor（本地执行）
2. factor_tools_mcp.py 的 FactorToolsMCP（MCP服务器）

维护规则：
- 修改工具时只需修改这一个文件
- 所有工具函数必须返回 pd.Series
- 所有工具函数必须确保索引对齐
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from config.data_fields import FIELD_MAPPING


def _ensure_series_with_index(data: pd.DataFrame, series_or_column) -> pd.Series:
    """
    确保返回的Series具有与data相同的索引
    
    Args:
        data: 原始数据DataFrame（可能是双索引）
        series_or_column: Series或列名
    
    Returns:
        pd.Series: 具有正确索引的Series
    """
    if isinstance(series_or_column, str):
        # 如果是列名，从data中获取
        result = data[series_or_column]
    else:
        result = series_or_column
    
    # 确保索引对齐
    if not isinstance(result, pd.Series):
        result = pd.Series(result, index=data.index)
    elif not result.index.equals(data.index):
        result.index = data.index
    
    return result


def _get_groupby_key(data: pd.DataFrame, key: str):
    """
    获取分组键，适配双索引结构
    
    Args:
        data: 数据DataFrame（可能是双索引）
        key: 分组键名称（'ts_code' 或 'trade_date'）
    
    Returns:
        分组键（Series或Index level）
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
            raise ValueError(f"索引和列中都不存在 {key}")


def _apply_grouped_operation(data: pd.DataFrame, field_data: pd.Series, operation, group_by_stock: bool = True):
    """
    智能应用分组操作，自动适配不同的数据格式
    
    支持三种数据格式：
    1. 双索引 (trade_date, ts_code) - 多股票时间序列 → 按 ts_code 分组
    2. 单索引 ts_code - 单日期多股票（预筛选阶段） → 返回 NaN 或直接操作
    3. 单索引 trade_date - 单股票时间序列（批量筛选阶段） → 直接操作，不分组
    
    Args:
        data: 数据DataFrame
        field_data: 要操作的Series
        operation: 操作函数，接受 Series 或 GroupBy 对象
        group_by_stock: 是否按股票分组（默认True）
    
    Returns:
        pd.Series: 操作结果
    """
    # 情况1: 双索引数据（多股票时间序列）
    if isinstance(data.index, pd.MultiIndex):
        if group_by_stock:
            ts_code_key = _get_groupby_key(data, 'ts_code')
            result = operation(field_data.groupby(ts_code_key))
        else:
            raise ValueError("按股票分组的操作无法在单索引数据中执行")
        result.index = data.index
        return result
    
    # 情况2: 单索引 ts_code（单日期多股票，预筛选阶段）
    elif data.index.name == 'ts_code':
        # 单日期数据，大多数时间序列操作无法执行，返回全NaN
        result = pd.Series(np.nan, index=data.index)
        return result
    
    # 情况3: 单索引 trade_date（单股票时间序列，批量筛选阶段）
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


def _is_expression(field_name: str) -> bool:
    """
    判断字段名是否是一个表达式（而非简单变量名）
    
    表达式特征：包含运算符或括号
    """
    expression_chars = ['+', '-', '*', '/', '(', ')', ' ']
    return any(char in field_name for char in expression_chars)


def _eval_expression(data: pd.DataFrame, expr: str, computed_vars: Dict) -> pd.Series:
    """
    计算表达式
    
    Args:
        data: 原始数据DataFrame
        expr: 表达式字符串
        computed_vars: 已计算的变量字典
    
    Returns:
        pd.Series: 计算结果
    """
    # 构建命名空间
    namespace = {}
    
    # 添加已计算的变量
    namespace.update(computed_vars)
    
    # 添加数据列（英文）
    for col in data.columns:
        namespace[col] = data[col]
    
    # 添加中文字段映射
    for cn_name, en_name in FIELD_MAPPING.items():
        if en_name in data.columns:
            namespace[cn_name] = data[en_name]
    
    # 添加数学函数
    namespace['np'] = np
    namespace['abs'] = np.abs
    namespace['log'] = lambda x: np.log(np.abs(x) + 1e-10)
    namespace['sqrt'] = lambda x: np.sqrt(np.abs(x))
    namespace['sign'] = np.sign
    namespace['max'] = np.maximum
    namespace['min'] = np.minimum
    
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
        raise ValueError(f"表达式计算失败: {expr}, 错误: {e}")


def _get_field(data: pd.DataFrame, field_name: str, computed_vars: Dict = None) -> pd.Series:
    """
    获取字段数据（可能是基础字段、已计算变量或表达式）
    
    Args:
        data: 原始数据DataFrame
        field_name: 字段名（中文/英文）或表达式
        computed_vars: 已计算的变量字典
    
    Returns:
        pd.Series: 字段数据
    """
    if computed_vars is None:
        computed_vars = {}
    
    # 如果是已计算的变量，直接返回
    if field_name in computed_vars:
        result = computed_vars[field_name]
    # 如果是中文字段名，从配置映射中查找
    elif field_name in FIELD_MAPPING:
        english_name = FIELD_MAPPING[field_name]
        if english_name not in data.columns:
            raise ValueError(f"字段 {field_name} (映射为 {english_name}) 在数据中不存在")
        result = data[english_name]
    # 如果是英文字段名，直接使用
    elif field_name in data.columns:
        result = data[field_name]
    # 检查是否是表达式，如果是则尝试计算
    elif _is_expression(field_name):
        try:
            result = _eval_expression(data, field_name, computed_vars)
        except Exception as e:
            raise ValueError(f"无法解析字段或表达式: {field_name}, 错误: {e}")
    else:
        # 提供更详细的错误信息
        available_vars = list(computed_vars.keys()) if computed_vars else []
        available_fields = list(FIELD_MAPPING.keys())[:10]  # 只显示部分
        available_columns = list(data.columns)[:10]  # 只显示部分
        
        error_msg = f"Unknown field: {field_name}\n"
        error_msg += f"  已计算的变量: {available_vars}\n"
        error_msg += f"  可用的中文字段: {available_fields}...\n"
        error_msg += f"  数据列: {available_columns}..."
        raise ValueError(error_msg)
    
    # 验证返回的数据
    if not isinstance(result, pd.Series):
        raise TypeError(f"_get_field 必须返回 Series，但得到了 {type(result)}")
    
    if len(result) != len(data):
        raise ValueError(f"字段 {field_name} 长度不匹配: {len(result)} vs {len(data)}")
    
    # 确保索引对齐
    if not result.index.equals(data.index):
        result = result.copy()
        result.index = data.index
    
    return result


# ============================================================================
# 基础变换工具
# ============================================================================

def pct_change(data: pd.DataFrame, values: str, periods: int = 1, computed_vars: Dict = None) -> pd.Series:
    """
    百分比变化
    
    支持三种数据格式：
    1. 双索引 (trade_date, ts_code) - 多股票时间序列
    2. 单索引 ts_code - 单日期多股票（预筛选阶段）
    3. 单索引 trade_date - 单股票时间序列（批量筛选阶段）
    """
    field_data = _get_field(data, values, computed_vars)
    
    # 情况1: 双索引数据（多股票时间序列）
    if isinstance(data.index, pd.MultiIndex):
        ts_code_key = _get_groupby_key(data, 'ts_code')
        result = field_data.groupby(ts_code_key).pct_change(periods)
        result.index = data.index
        return result
    
    # 情况2: 单索引 ts_code（单日期多股票，预筛选阶段）
    elif data.index.name == 'ts_code':
        # 单日期数据，无法计算pct_change，返回全NaN
        result = pd.Series(np.nan, index=data.index)
        return result
    
    # 情况3: 单索引 trade_date（单股票时间序列，批量筛选阶段）
    elif data.index.name == 'trade_date' or isinstance(data.index, pd.DatetimeIndex):
        # 单股票数据，直接计算pct_change（不需要分组）
        result = field_data.pct_change(periods)
        result.index = data.index
        return result
    
    # 其他情况：尝试直接计算
    else:
        result = field_data.pct_change(periods)
        result.index = data.index
        return result


def lag(data: pd.DataFrame, values: str, periods: int = 1, computed_vars: Dict = None) -> pd.Series:
    """滞后"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.groupby(level=0).shift(periods) if hasattr(x, 'groupby') else x.shift(periods)
    )


def delta(data: pd.DataFrame, values: str, periods: int = 1, computed_vars: Dict = None) -> pd.Series:
    """差分"""
    field_data = _get_field(data, values, computed_vars)
    def calc_delta(x):
        if hasattr(x, 'groupby'):
            lagged = x.groupby(level=0).shift(periods)
        else:
            lagged = x.shift(periods)
        return x - lagged
    return _apply_grouped_operation(data, field_data, calc_delta)


# ============================================================================
# 移动窗口工具
# ============================================================================

def rolling_mean(data: pd.DataFrame, values: str, window: int = 5, computed_vars: Dict = None) -> pd.Series:
    """移动平均"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).mean()) if hasattr(x, 'transform') else x.rolling(window).mean()
    )


def rolling_std(data: pd.DataFrame, values: str, window: int = 5, computed_vars: Dict = None) -> pd.Series:
    """移动标准差"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).std()) if hasattr(x, 'transform') else x.rolling(window).std()
    )


def rolling_max(data: pd.DataFrame, values: str, window: int = 5, computed_vars: Dict = None) -> pd.Series:
    """移动最大值"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).max()) if hasattr(x, 'transform') else x.rolling(window).max()
    )


def rolling_min(data: pd.DataFrame, values: str, window: int = 5, computed_vars: Dict = None) -> pd.Series:
    """移动最小值"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).min()) if hasattr(x, 'transform') else x.rolling(window).min()
    )


# ============================================================================
# 标准化工具
# ============================================================================

def rank(data: pd.DataFrame, values: str, computed_vars: Dict = None) -> pd.Series:
    """排名（按日期分组）"""
    field_data = _get_field(data, values, computed_vars)
    trade_date_key = _get_groupby_key(data, 'trade_date')
    result = field_data.groupby(trade_date_key).rank(pct=True)
    result.index = data.index
    return result


def zscore(data: pd.DataFrame, values: str, computed_vars: Dict = None) -> pd.Series:
    """标准化（按日期分组）"""
    field_data = _get_field(data, values, computed_vars)
    trade_date_key = _get_groupby_key(data, 'trade_date')
    result = field_data.groupby(trade_date_key).transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))
    result.index = data.index
    return result


# ============================================================================
# 数学变换工具
# ============================================================================

def abs_value(data: pd.DataFrame, values: str, computed_vars: Dict = None) -> pd.Series:
    """绝对值"""
    field_data = _get_field(data, values, computed_vars)
    result = field_data.abs()
    result.index = data.index
    return result


def log_transform(data: pd.DataFrame, values: str, computed_vars: Dict = None) -> pd.Series:
    """对数变换"""
    field_data = _get_field(data, values, computed_vars)
    result = pd.Series(np.log1p(field_data))
    result.index = data.index
    return result


def sqrt_transform(data: pd.DataFrame, values: str, computed_vars: Dict = None) -> pd.Series:
    """平方根变换，保留符号"""
    field_data = _get_field(data, values, computed_vars)
    result = pd.Series(np.sqrt(np.abs(field_data)) * np.sign(field_data))
    result.index = data.index
    return result


def power_transform(data: pd.DataFrame, values: str, power: float = 2, computed_vars: Dict = None) -> pd.Series:
    """幂次变换"""
    field_data = _get_field(data, values, computed_vars)
    result = pd.Series(field_data ** power)
    result.index = data.index
    return result


# ============================================================================
# 技术指标工具
# ============================================================================

def rsi(data: pd.DataFrame, values: str, window: int = 14, computed_vars: Dict = None) -> pd.Series:
    """相对强弱指标"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_rsi(x):
        if hasattr(x, 'transform'):
            # GroupBy对象
            return x.transform(lambda y: _calc_rsi_series(y, window))
        else:
            # Series对象
            return _calc_rsi_series(x, window)
    
    return _apply_grouped_operation(data, field_data, calc_rsi)

def _calc_rsi_series(x, window):
    """计算单个序列的RSI"""
    delta = x.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / (loss + 1e-8)
    return 100 - (100 / (1 + rs))


def ema(data: pd.DataFrame, values: str, span: int = 12, computed_vars: Dict = None) -> pd.Series:
    """指数移动平均"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.ewm(span=span).mean()) if hasattr(x, 'transform') else x.ewm(span=span).mean()
    )


def ewm(data: pd.DataFrame, values: str, span: int = 12, computed_vars: Dict = None) -> pd.Series:
    """指数加权移动平均（与ema相同）"""
    return ema(data, values, span, computed_vars)


def macd(data: pd.DataFrame, values: str, fast: int = 12, slow: int = 26, signal: int = 9, computed_vars: Dict = None) -> pd.Series:
    """
    MACD指标 - 返回MACD柱状图
    
    Args:
        data: 数据DataFrame
        values: 价格列名
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9
        computed_vars: 已计算的变量字典
        
    Returns:
        MACD柱状图 = (DIF - DEA) * 2
    """
    field_data = _get_field(data, values, computed_vars)
    
    def calc_macd_series(x):
        # 计算快慢均线
        ema_fast = x.ewm(span=fast, adjust=False).mean()
        ema_slow = x.ewm(span=slow, adjust=False).mean()
        # DIF线（差离值）
        dif = ema_fast - ema_slow
        # DEA线（信号线）
        dea = dif.ewm(span=signal, adjust=False).mean()
        # MACD柱状图
        macd = (dif - dea) * 2
        return macd
    
    def calc_macd(x):
        if hasattr(x, 'transform'):
            return x.transform(calc_macd_series)
        else:
            return calc_macd_series(x)
    
    return _apply_grouped_operation(data, field_data, calc_macd)


def bollinger_position(data: pd.DataFrame, values: str, window: int = 20, num_std: float = 2, computed_vars: Dict = None) -> pd.Series:
    """布林带位置"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_bb_pos_series(x):
        ma = x.rolling(window).mean()
        std = x.rolling(window).std()
        upper = ma + num_std * std
        lower = ma - num_std * std
        return (x - lower) / (upper - lower + 1e-8)
    
    def calc_bb_pos(x):
        if hasattr(x, 'transform'):
            return x.transform(calc_bb_pos_series)
        else:
            return calc_bb_pos_series(x)
    
    return _apply_grouped_operation(data, field_data, calc_bb_pos)


def kdj(data: pd.DataFrame, high: str = '最高价', low: str = '最低价', close: str = '收盘价', 
        window: int = 9, computed_vars: Dict = None) -> pd.Series:
    """KDJ指标（返回J值）"""
    high_data = _get_field(data, high, computed_vars)
    low_data = _get_field(data, low, computed_vars)
    close_data = _get_field(data, close, computed_vars)
    
    def calc_kdj(df):
        llv = df['low'].rolling(window).min()
        hhv = df['high'].rolling(window).max()
        rsv = (df['close'] - llv) / (hhv - llv + 1e-8) * 100
        k = rsv.ewm(alpha=1/3).mean()
        d = k.ewm(alpha=1/3).mean()
        j = 3 * k - 2 * d
        return j
    
    ts_code_key = _get_groupby_key(data, 'ts_code')
    # 使用简单索引避免冲突
    temp_df = pd.DataFrame({
        'high': high_data.values,
        'low': low_data.values,
        'close': close_data.values,
        'group_key': ts_code_key.values
    })
    result = temp_df.groupby('group_key').apply(calc_kdj).reset_index(level=0, drop=True)
    result.index = data.index
    return result


def atr(data: pd.DataFrame, high: str = '最高价', low: str = '最低价', close: str = '收盘价',
        window: int = 14, computed_vars: Dict = None) -> pd.Series:
    """平均真实波幅"""
    high_data = _get_field(data, high, computed_vars)
    low_data = _get_field(data, low, computed_vars)
    close_data = _get_field(data, close, computed_vars)
    
    def calc_atr(df):
        prev_close = df['close'].shift(1)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - prev_close).abs()
        tr3 = (df['low'] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window).mean()
    
    ts_code_key = _get_groupby_key(data, 'ts_code')
    # 使用简单索引避免冲突
    temp_df = pd.DataFrame({
        'high': high_data.values,
        'low': low_data.values,
        'close': close_data.values,
        'group_key': ts_code_key.values
    })
    result = temp_df.groupby('group_key').apply(calc_atr).reset_index(level=0, drop=True)
    result.index = data.index
    return result


def obv(data: pd.DataFrame, close: str = '收盘价', vol: str = '成交量', computed_vars: Dict = None) -> pd.Series:
    """能量潮指标"""
    close_data = _get_field(data, close, computed_vars)
    vol_data = _get_field(data, vol, computed_vars)
    
    def calc_obv(df):
        price_change = df['close'].diff()
        obv = (df['vol'] * np.sign(price_change)).cumsum()
        return obv
    
    ts_code_key = _get_groupby_key(data, 'ts_code')
    # 使用简单索引避免冲突
    temp_df = pd.DataFrame({
        'close': close_data.values,
        'vol': vol_data.values,
        'group_key': ts_code_key.values
    })
    result = temp_df.groupby('group_key').apply(calc_obv).reset_index(level=0, drop=True)
    result.index = data.index
    return result


# ============================================================================
# 统计工具
# ============================================================================

def correlation(data: pd.DataFrame, x: str, y: str, window: int = 20, computed_vars: Dict = None) -> pd.Series:
    """滚动相关系数"""
    x_data = _get_field(data, x, computed_vars)
    y_data = _get_field(data, y, computed_vars)
    
    def calc_corr(df):
        return df['x'].rolling(window).corr(df['y'])
    
    ts_code_key = _get_groupby_key(data, 'ts_code')
    # 使用简单索引避免冲突
    temp_df = pd.DataFrame({
        'x': x_data.values,
        'y': y_data.values,
        'group_key': ts_code_key.values
    })
    result = temp_df.groupby('group_key').apply(calc_corr).reset_index(level=0, drop=True)
    result.index = data.index
    return result


def skewness(data: pd.DataFrame, values: str, window: int = 20, computed_vars: Dict = None) -> pd.Series:
    """偏度"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).skew()) if hasattr(x, 'transform') else x.rolling(window).skew()
    )


def kurtosis(data: pd.DataFrame, values: str, window: int = 20, computed_vars: Dict = None) -> pd.Series:
    """峰度"""
    field_data = _get_field(data, values, computed_vars)
    return _apply_grouped_operation(
        data, field_data,
        lambda x: x.transform(lambda y: y.rolling(window).kurt()) if hasattr(x, 'transform') else x.rolling(window).kurt()
    )


# ============================================================================
# 时间序列工具
# ============================================================================


def _use_numba() -> bool:
    """检查是否可以使用 numba 加速"""
    try:
        import numba
        return True
    except ImportError:
        return False


def ts_rank(data: pd.DataFrame, values: str, window: int = 10, computed_vars: Dict = None) -> pd.Series:
    """时间序列排名（优化版）"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_ts_rank_optimized(x):
        """优化的时间序列排名计算"""
        # 使用 numpy 数组避免 Series 开销
        values_array = x.values if hasattr(x, 'values') else np.asarray(x)
        n = len(values_array)
        
        if n < window:
            return pd.Series(np.nan, index=x.index if hasattr(x, 'index') else range(n))
        
        # 预分配结果数组
        result = np.full(n, np.nan)
        
        # 向量化计算
        for i in range(window - 1, n):
            # 获取当前窗口的数据
            window_data = values_array[i - window + 1:i + 1]
            
            # 计算当前值在窗口中的排名百分位
            current_value = window_data[-1]
            rank_pct = (np.sum(window_data < current_value) + 0.5 * np.sum(window_data == current_value)) / window
            
            result[i] = rank_pct
        
        return pd.Series(result, index=x.index if hasattr(x, 'index') else range(n))
    
    def calc_ts_rank_wrapper(x):
        """包装器以支持不同的输入类型"""
        if hasattr(x, 'transform'):
            # GroupBy 对象，使用 transform
            return x.transform(calc_ts_rank_optimized, engine='numba' if _use_numba() else None)
        else:
            # 普通 Series，直接计算
            return calc_ts_rank_optimized(x)
    
    return _apply_grouped_operation(data, field_data, calc_ts_rank_wrapper)


def ts_argmax(data: pd.DataFrame, values: str, window: int = 10, computed_vars: Dict = None) -> pd.Series:
    """时间序列最大值位置（优化版）"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_ts_argmax_optimized(x):
        """优化的 argmax 计算"""
        values_array = x.values if hasattr(x, 'values') else np.asarray(x)
        n = len(values_array)
        result = np.full(n, np.nan)
        
        for i in range(window - 1, n):
            window_data = values_array[i - window + 1:i + 1]
            result[i] = window - 1 - np.argmax(window_data)
        
        return pd.Series(result, index=x.index if hasattr(x, 'index') else range(n))
    
    def calc_ts_argmax_wrapper(x):
        if hasattr(x, 'transform'):
            return x.transform(calc_ts_argmax_optimized)
        else:
            return calc_ts_argmax_optimized(x)
    
    return _apply_grouped_operation(data, field_data, calc_ts_argmax_wrapper)


def ts_argmin(data: pd.DataFrame, values: str, window: int = 10, computed_vars: Dict = None) -> pd.Series:
    """时间序列最小值位置（优化版）"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_ts_argmin_optimized(x):
        """优化的 argmin 计算"""
        values_array = x.values if hasattr(x, 'values') else np.asarray(x)
        n = len(values_array)
        result = np.full(n, np.nan)
        
        for i in range(window - 1, n):
            window_data = values_array[i - window + 1:i + 1]
            result[i] = window - 1 - np.argmin(window_data)
        
        return pd.Series(result, index=x.index if hasattr(x, 'index') else range(n))
    
    def calc_ts_argmin_wrapper(x):
        if hasattr(x, 'transform'):
            return x.transform(calc_ts_argmin_optimized)
        else:
            return calc_ts_argmin_optimized(x)
    
    return _apply_grouped_operation(data, field_data, calc_ts_argmin_wrapper)


def decay_linear(data: pd.DataFrame, values: str, window: int = 10, computed_vars: Dict = None) -> pd.Series:
    """线性衰减加权平均（优化版）"""
    field_data = _get_field(data, values, computed_vars)
    
    # 预计算权重
    weights = np.arange(1, window + 1, dtype=np.float64)
    
    def calc_decay_linear_optimized(x):
        """优化的线性衰减加权计算"""
        values_array = x.values if hasattr(x, 'values') else np.asarray(x)
        n = len(values_array)
        result = np.full(n, np.nan)
        
        for i in range(window - 1, n):
            window_data = values_array[i - window + 1:i + 1]
            current_weights = weights[:len(window_data)]
            result[i] = np.average(window_data, weights=current_weights)
        
        return pd.Series(result, index=x.index if hasattr(x, 'index') else range(n))
    
    def calc_decay_linear_wrapper(x):
        if hasattr(x, 'transform'):
            return x.transform(calc_decay_linear_optimized)
        else:
            return calc_decay_linear_optimized(x)
    
    return _apply_grouped_operation(data, field_data, calc_decay_linear_wrapper)


def volatility(data: pd.DataFrame, values: str, window: int = 20, computed_vars: Dict = None) -> pd.Series:
    """波动率（年化标准差）"""
    field_data = _get_field(data, values, computed_vars)
    ts_code_key = _get_groupby_key(data, 'ts_code')
    result = field_data.groupby(ts_code_key).transform(lambda x: x.rolling(window).std() * np.sqrt(252))
    result.index = data.index
    return result


def max_drawdown(data: pd.DataFrame, values: str, window: int = 60, computed_vars: Dict = None) -> pd.Series:
    """最大回撤"""
    field_data = _get_field(data, values, computed_vars)
    
    def calc_max_drawdown(x):
        roll_max = x.rolling(window, min_periods=1).max()
        drawdown = (x - roll_max) / (roll_max + 1e-8)
        return drawdown
    
    ts_code_key = _get_groupby_key(data, 'ts_code')
    result = field_data.groupby(ts_code_key).transform(calc_max_drawdown)
    result.index = data.index
    return result


# ============================================================================
# 比较工具
# ============================================================================

def max_of(data: pd.DataFrame, x: str, y: str, computed_vars: Dict = None) -> pd.Series:
    """取两个值的最大值"""
    x_data = _get_field(data, x, computed_vars)
    y_data = _get_field(data, y, computed_vars)
    result = pd.Series(np.maximum(x_data, y_data))
    result.index = data.index
    return result


def min_of(data: pd.DataFrame, x: str, y: str, computed_vars: Dict = None) -> pd.Series:
    """取两个值的最小值"""
    x_data = _get_field(data, x, computed_vars)
    y_data = _get_field(data, y, computed_vars)
    result = pd.Series(np.minimum(x_data, y_data))
    result.index = data.index
    return result


def clip(data: pd.DataFrame, values: str, lower: float = None, upper: float = None, computed_vars: Dict = None) -> pd.Series:
    """截断值"""
    field_data = _get_field(data, values, computed_vars)
    result = field_data.clip(lower=lower, upper=upper)
    result.index = data.index
    return result


def filter_by_industry(data: pd.DataFrame, industry: str, computed_vars: Dict = None) -> pd.Series:
    """
    按行业筛选股票（返回布尔Series）
    
    Args:
        data: 数据DataFrame（必须包含 industry 字段）
        industry: 行业名称（支持模糊匹配）
        computed_vars: 已计算的变量字典
    
    Returns:
        pd.Series: 布尔Series，True表示属于该行业
    
    Examples:
        >>> # 筛选通信设备行业
        >>> result = filter_by_industry(data, industry="通信设备")
        >>> # 筛选包含"通信"的行业
        >>> result = filter_by_industry(data, industry="通信")
    """
    # 获取行业字段
    if 'industry' not in data.columns:
        raise ValueError("数据中不包含 industry 字段，无法按行业筛选")
    
    industry_data = data['industry']
    
    # 模糊匹配：检查行业名称中是否包含指定的关键词
    result = industry_data.str.contains(industry, na=False, case=False)
    
    # 确保索引对齐
    result.index = data.index
    
    return result


def filter_by_market(data: pd.DataFrame, market: str, computed_vars: Dict = None) -> pd.Series:
    """
    按市场筛选股票（返回布尔Series）
    
    Args:
        data: 数据DataFrame（必须包含 market 字段）
        market: 市场名称（主板/创业板/科创板等）
        computed_vars: 已计算的变量字典
    
    Returns:
        pd.Series: 布尔Series，True表示属于该市场
    
    Examples:
        >>> # 筛选主板股票
        >>> result = filter_by_market(data, market="主板")
        >>> # 筛选科创板股票
        >>> result = filter_by_market(data, market="科创板")
    """
    # 获取市场字段
    if 'market' not in data.columns:
        raise ValueError("数据中不包含 market 字段，无法按市场筛选")
    
    market_data = data['market']
    
    # 模糊匹配：检查市场名称中是否包含指定的关键词
    result = market_data.str.contains(market, na=False, case=False)
    
    # 确保索引对齐
    result.index = data.index
    
    return result


# ============================================================================
# 工具映射表（用于动态调用）
# ============================================================================

TOOL_FUNCTIONS = {
    'pct_change': pct_change,
    'lag': lag,
    'delta': delta,
    'rolling_mean': rolling_mean,
    'rolling_std': rolling_std,
    'rolling_max': rolling_max,
    'rolling_min': rolling_min,
    'rank_normalize': rank,  # 修复：函数名是rank
    'zscore_normalize': zscore,  # 修复：函数名是zscore
    'abs_value': abs_value,
    'log_transform': log_transform,
    'sqrt_transform': sqrt_transform,
    'power_transform': power_transform,
    'rsi': rsi,
    'ema': ema,
    'ewm': ewm,
    'macd': macd,
    'bollinger_position': bollinger_position,
    'kdj': kdj,
    'atr': atr,
    'obv': obv,
    'correlation': correlation,
    'skewness': skewness,
    'kurtosis': kurtosis,
    'ts_rank': ts_rank,
    'ts_argmax': ts_argmax,
    'ts_argmin': ts_argmin,
    'decay_linear': decay_linear,
    'volatility': volatility,
    'max_drawdown': max_drawdown,
    'max_of': max_of,
    'min_of': min_of,
    'clip': clip,
    'filter_by_industry': filter_by_industry,
    'filter_by_market': filter_by_market,
}


def execute_tool(tool_name: str, data: pd.DataFrame, params: Dict[str, Any], computed_vars: Dict = None) -> pd.Series:
    """
    统一的工具执行入口
    
    Args:
        tool_name: 工具名称
        data: 原始数据DataFrame
        params: 工具参数
        computed_vars: 已计算的变量字典
    
    Returns:
        pd.Series: 计算结果
    """
    if tool_name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_func = TOOL_FUNCTIONS[tool_name]
    
    # 调用工具函数
    result = tool_func(data, **params, computed_vars=computed_vars)
    
    return result
