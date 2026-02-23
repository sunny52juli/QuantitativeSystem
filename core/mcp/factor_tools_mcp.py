"""
因子工具MCP服务器 - 重构优化版
提供丰富的数学、统计、技术分析工具，支持构建复杂因子

重构优化：
1. 工具定义与实现分离
2. 按功能模块化组织
3. 统一错误处理机制
4. 增强类型注解和文档
"""

import json
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod


# ==================== 工具定义常量 ====================

TOOL_CATEGORIES = {
    "math": ["abs_value", "log_transform", "rank_normalize", "zscore_normalize", "sqrt_transform", "power_transform", "sign"],
    "time_series": ["rolling_mean", "rolling_std", "rolling_max", "rolling_min", "rolling_sum", "lag", "delta", "pct_change", "ewm"],
    "technical": ["rsi", "bollinger_position", "ema", "macd", "kdj", "atr", "obv", "cci", "williams_r", "adx"],
    "statistical": ["correlation", "quantile", "skewness", "kurtosis", "covariance"],
    "combination": ["max_of", "min_of", "clip", "where", "weighted_avg"],
    "feature_engineering": ["ts_rank", "ts_argmax", "ts_argmin", "decay_linear", "highday", "lowday"],
    "risk_metrics": ["volatility", "sharpe_ratio", "max_drawdown", "beta"],
    "data_management": ["load_data", "save_factor", "list_factors"]
}

TOOL_DEFINITIONS = {
    # 数学运算工具
    "abs_value": {
        "description": "计算绝对值",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式或因子名称"}
            },
            "required": ["values"]
        }
    },
    
    "log_transform": {
        "description": "对数变换，log(1 + x)",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式"}
            },
            "required": ["values"]
        }
    },
    
    "sqrt_transform": {
        "description": "平方根变换，保留符号",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式"}
            },
            "required": ["values"]
        }
    },
    
    "power_transform": {
        "description": "幂次变换，x^n",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式"},
                "power": {"type": "number", "description": "幂次", "default": 2}
            },
            "required": ["values"]
        }
    },
    
    "rank_normalize": {
        "description": "横截面排名归一化到[0,1]",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式"}
            },
            "required": ["values"]
        }
    },
    
    "zscore_normalize": {
        "description": "Z-score标准化",
        "category": "math",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入表达式"}
            },
            "required": ["values"]
        }
    },
    
    # 时间序列工具
    "rolling_mean": {
        "description": "移动平均",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段（如'收盘价'）"},
                "window": {"type": "integer", "description": "窗口大小（天数）", "default": 5}
            },
            "required": ["values", "window"]
        }
    },
    
    "pct_change": {
        "description": "百分比变化",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段（如'收盘价'）"},
                "periods": {"type": "integer", "description": "时间间隔（天数）", "default": 1}
            },
            "required": ["values", "periods"]
        }
    },
    
    "rolling_std": {
        "description": "移动标准差",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values", "window"]
        }
    },
    
    "rolling_max": {
        "description": "移动最大值",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values", "window"]
        }
    },
    
    "rolling_min": {
        "description": "移动最小值",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values", "window"]
        }
    },
    
    "ewm": {
        "description": "指数加权移动平均",
        "category": "time_series",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "span": {"type": "integer", "description": "时间跨度", "default": 12}
            },
            "required": ["values", "span"]
        }
    },
    
    # 技术指标工具
    "rsi": {
        "description": "相对强弱指标RSI",
        "category": "technical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "价格字段（通常是'收盘价'）"},
                "window": {"type": "integer", "description": "计算窗口", "default": 14}
            },
            "required": ["values", "window"]
        }
    },
    
    "macd": {
        "description": "MACD指标",
        "category": "technical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "价格字段"},
                "fast": {"type": "integer", "description": "快线周期", "default": 12},
                "slow": {"type": "integer", "description": "慢线周期", "default": 26},
                "signal": {"type": "integer", "description": "信号线周期", "default": 9}
            },
            "required": ["values"]
        }
    },
    
    "kdj": {
        "description": "KDJ随机指标",
        "category": "technical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "high": {"type": "string", "description": "最高价字段", "default": "最高价"},
                "low": {"type": "string", "description": "最低价字段", "default": "最低价"},
                "close": {"type": "string", "description": "收盘价字段", "default": "收盘价"},
                "window": {"type": "integer", "description": "计算窗口", "default": 9}
            },
            "required": []
        }
    },
    
    "atr": {
        "description": "平均真实波幅ATR",
        "category": "technical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "high": {"type": "string", "description": "最高价字段", "default": "最高价"},
                "low": {"type": "string", "description": "最低价字段", "default": "最低价"},
                "close": {"type": "string", "description": "收盘价字段", "default": "收盘价"},
                "window": {"type": "integer", "description": "计算窗口", "default": 14}
            },
            "required": []
        }
    },
    
    "obv": {
        "description": "能量潮OBV",
        "category": "technical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "close": {"type": "string", "description": "收盘价字段", "default": "收盘价"},
                "vol": {"type": "string", "description": "成交量字段", "default": "成交量"}
            },
            "required": []
        }
    },
    
    # 统计工具
    "correlation": {
        "description": "滚动相关系数",
        "category": "statistical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "string", "description": "第一个字段"},
                "y": {"type": "string", "description": "第二个字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["x", "y"]
        }
    },
    
    "skewness": {
        "description": "偏度（分布偏斜程度）",
        "category": "statistical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values"]
        }
    },
    
    "kurtosis": {
        "description": "峰度（分布尖峭程度）",
        "category": "statistical",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values"]
        }
    },
    
    # 特征工程工具
    "ts_rank": {
        "description": "时间序列排名（过去N天的排名）",
        "category": "feature_engineering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 10}
            },
            "required": ["values", "window"]
        }
    },
    
    "ts_argmax": {
        "description": "时间序列最大值位置（过去N天最大值距今天数）",
        "category": "feature_engineering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 10}
            },
            "required": ["values", "window"]
        }
    },
    
    "ts_argmin": {
        "description": "时间序列最小值位置（过去N天最小值距今天数）",
        "category": "feature_engineering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 10}
            },
            "required": ["values", "window"]
        }
    },
    
    "decay_linear": {
        "description": "线性衰减加权平均",
        "category": "feature_engineering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "输入字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 10}
            },
            "required": ["values", "window"]
        }
    },
    
    # 风险指标工具
    "volatility": {
        "description": "波动率（年化标准差）",
        "category": "risk_metrics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "收益率字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 20}
            },
            "required": ["values"]
        }
    },
    
    "max_drawdown": {
        "description": "最大回撤",
        "category": "risk_metrics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {"type": "string", "description": "价格字段"},
                "window": {"type": "integer", "description": "窗口大小", "default": 60}
            },
            "required": ["values"]
        }
    },
    
    # 数据管理工具
    "load_data": {
        "description": "加载股票数据",
        "category": "data_management",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "数据源：'sample'或文件路径", "default": "sample"},
                "n_stocks": {"type": "integer", "description": "股票数量（示例数据）", "default": 50},
                "n_days": {"type": "integer", "description": "交易天数（示例数据）", "default": 252}
            }
        }
    }
}


# ==================== 工具执行器基类 ====================

class ToolExecutor(ABC):
    """工具执行器基类"""
    
    @abstractmethod
    def execute(self, args: Dict) -> Dict:
        """执行工具并返回结果"""
        pass
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """返回工具名称"""
        pass


# ==================== 具体工具执行器 ====================

class MathToolExecutor(ToolExecutor):
    """数学工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行数学工具"""
        expr = args.get("values")
        
        if self.tool_name == "abs_value":
            return {
                "tool": "abs_value",
                "result_expression": f"abs({expr})",
                "description": f"对 {expr} 取绝对值"
            }
        elif self.tool_name == "log_transform":
            return {
                "tool": "log_transform",
                "result_expression": f"log(1 + {expr})",
                "description": f"对 {expr} 进行对数变换",
                "note": "使用log(1+x)避免负值问题"
            }
        elif self.tool_name == "sqrt_transform":
            return {
                "tool": "sqrt_transform",
                "result_expression": f"sqrt(abs({expr})) * sign({expr})",
                "description": f"对 {expr} 进行平方根变换，保留符号"
            }
        elif self.tool_name == "power_transform":
            power = args.get("power", 2)
            return {
                "tool": "power_transform",
                "result_expression": f"({expr}) ** {power}",
                "description": f"对 {expr} 进行{power}次幂变换"
            }
        elif self.tool_name == "rank_normalize":
            return {
                "tool": "rank_normalize",
                "result_expression": f"rank({expr})",
                "description": f"对 {expr} 进行横截面排名归一化"
            }
        elif self.tool_name == "zscore_normalize":
            return {
                "tool": "zscore_normalize",
                "result_expression": f"zscore({expr})",
                "description": f"对 {expr} 进行Z-score标准化"
            }
        
        return {"error": f"未知数学工具: {self.tool_name}"}


class TimeSeriesToolExecutor(ToolExecutor):
    """时间序列工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行时间序列工具"""
        field = args.get("values")
        
        if self.tool_name == "rolling_mean":
            window = args.get("window", 5)
            return {
                "tool": "rolling_mean",
                "result_expression": f"ma_{window}({field})",
                "description": f"{field}的{window}日移动平均",
                "formula": f"mean of last {window} days"
            }
        elif self.tool_name == "pct_change":
            periods = args.get("periods", 1)
            return {
                "tool": "pct_change",
                "result_expression": f"pct_{periods}({field})",
                "description": f"{field}相对{periods}天前的涨跌幅",
                "formula": f"({field}(t) - {field}(t-{periods})) / {field}(t-{periods})"
            }
        elif self.tool_name == "rolling_std":
            window = args.get("window", 20)
            return {
                "tool": "rolling_std",
                "result_expression": f"std_{window}({field})",
                "description": f"{field}的{window}日移动标准差",
                "formula": f"std of last {window} days"
            }
        elif self.tool_name == "rolling_max":
            window = args.get("window", 20)
            return {
                "tool": "rolling_max",
                "result_expression": f"max_{window}({field})",
                "description": f"{field}的{window}日最大值"
            }
        elif self.tool_name == "rolling_min":
            window = args.get("window", 20)
            return {
                "tool": "rolling_min",
                "result_expression": f"min_{window}({field})",
                "description": f"{field}的{window}日最小值"
            }
        elif self.tool_name == "ewm":
            span = args.get("span", 12)
            return {
                "tool": "ewm",
                "result_expression": f"ema_{span}({field})",
                "description": f"{field}的{span}日指数加权移动平均",
                "note": "对近期数据赋予更高权重"
            }
        
        return {"error": f"未知时间序列工具: {self.tool_name}"}


class TechnicalToolExecutor(ToolExecutor):
    """技术指标工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行技术指标工具"""
        field = args.get("values", "收盘价")
        
        if self.tool_name == "rsi":
            window = args.get("window", 14)
            return {
                "tool": "rsi",
                "result_expression": f"rsi_{window}({field})",
                "description": f"基于{field}的{window}日RSI指标",
                "range": "[0, 100]",
                "interpretation": "RSI > 70: 超买, RSI < 30: 超卖"
            }
        elif self.tool_name == "macd":
            fast = args.get("fast", 12)
            slow = args.get("slow", 26)
            signal = args.get("signal", 9)
            return {
                "tool": "macd",
                "result_expression": f"macd_{fast}_{slow}_{signal}({field})",
                "description": f"MACD指标，快线{fast}日，慢线{slow}日，信号线{signal}日",
                "interpretation": "DIF上穿DEA为金叉买入信号"
            }
        elif self.tool_name == "kdj":
            window = args.get("window", 9)
            high = args.get("high", "最高价")
            low = args.get("low", "最低价")
            close = args.get("close", "收盘价")
            return {
                "tool": "kdj",
                "result_expression": f"kdj_{window}",
                "description": f"KDJ随机指标，周期{window}日",
                "interpretation": "K值>80超买，K值<20超卖"
            }
        elif self.tool_name == "atr":
            window = args.get("window", 14)
            return {
                "tool": "atr",
                "result_expression": f"atr_{window}",
                "description": f"平均真实波幅ATR，周期{window}日",
                "interpretation": "衡量市场波动性，ATR越大波动越大"
            }
        elif self.tool_name == "obv":
            return {
                "tool": "obv",
                "result_expression": "obv",
                "description": "能量潮OBV指标",
                "interpretation": "价涨量增OBV上升为强势，价涨量缩OBV下降为弱势"
            }
        
        return {"error": f"未知技术指标工具: {self.tool_name}"}


class StatisticalToolExecutor(ToolExecutor):
    """统计工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行统计工具"""
        if self.tool_name == "correlation":
            x = args.get("x")
            y = args.get("y")
            window = args.get("window", 20)
            return {
                "tool": "correlation",
                "result_expression": f"corr_{window}({x}, {y})",
                "description": f"{x}与{y}的{window}日滚动相关系数",
                "range": "[-1, 1]"
            }
        elif self.tool_name == "skewness":
            values = args.get("values")
            window = args.get("window", 20)
            return {
                "tool": "skewness",
                "result_expression": f"skew_{window}({values})",
                "description": f"{values}的{window}日偏度",
                "interpretation": "正偏：右偏分布，负偏：左偏分布"
            }
        elif self.tool_name == "kurtosis":
            values = args.get("values")
            window = args.get("window", 20)
            return {
                "tool": "kurtosis",
                "result_expression": f"kurt_{window}({values})",
                "description": f"{values}的{window}日峰度",
                "interpretation": "峰度>3：尖峰分布，峰度<3：平坦分布"
            }
        
        return {"error": f"未知统计工具: {self.tool_name}"}


class FeatureEngineeringToolExecutor(ToolExecutor):
    """特征工程工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行特征工程工具"""
        values = args.get("values")
        window = args.get("window", 10)
        
        if self.tool_name == "ts_rank":
            return {
                "tool": "ts_rank",
                "result_expression": f"ts_rank_{window}({values})",
                "description": f"{values}在过去{window}天的排名",
                "interpretation": "值越大表示当前值在历史中排名越靠前"
            }
        elif self.tool_name == "ts_argmax":
            return {
                "tool": "ts_argmax",
                "result_expression": f"ts_argmax_{window}({values})",
                "description": f"{values}在过去{window}天最大值距今天数",
                "interpretation": "值越小表示最大值越接近当前"
            }
        elif self.tool_name == "ts_argmin":
            return {
                "tool": "ts_argmin",
                "result_expression": f"ts_argmin_{window}({values})",
                "description": f"{values}在过去{window}天最小值距今天数",
                "interpretation": "值越小表示最小值越接近当前"
            }
        elif self.tool_name == "decay_linear":
            return {
                "tool": "decay_linear",
                "result_expression": f"decay_linear_{window}({values})",
                "description": f"{values}的{window}日线性衰减加权平均",
                "interpretation": "近期数据权重更高"
            }
        
        return {"error": f"未知特征工程工具: {self.tool_name}"}


class RiskMetricsToolExecutor(ToolExecutor):
    """风险指标工具执行器"""
    
    def __init__(self, tool_name: str):
        self._tool_name = tool_name
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    def execute(self, args: Dict) -> Dict:
        """执行风险指标工具"""
        values = args.get("values")
        
        if self.tool_name == "volatility":
            window = args.get("window", 20)
            return {
                "tool": "volatility",
                "result_expression": f"vol_{window}({values})",
                "description": f"{values}的{window}日年化波动率",
                "formula": "std * sqrt(252)"
            }
        elif self.tool_name == "max_drawdown":
            window = args.get("window", 60)
            return {
                "tool": "max_drawdown",
                "result_expression": f"mdd_{window}({values})",
                "description": f"{values}的{window}日最大回撤",
                "interpretation": "值越小风险越大"
            }
        
        return {"error": f"未知风险指标工具: {self.tool_name}"}


# ==================== 工具工厂 ====================

class ToolFactory:
    """工具工厂类，负责创建工具执行器"""
    
    @staticmethod
    def create_executor(tool_name: str) -> Optional[ToolExecutor]:
        """根据工具名称创建对应的执行器"""
        tool_def = TOOL_DEFINITIONS.get(tool_name)
        if not tool_def:
            return None
        
        category = tool_def.get("category")
        
        if category == "math":
            return MathToolExecutor(tool_name)
        elif category == "time_series":
            return TimeSeriesToolExecutor(tool_name)
        elif category == "technical":
            return TechnicalToolExecutor(tool_name)
        elif category == "statistical":
            return StatisticalToolExecutor(tool_name)
        elif category == "feature_engineering":
            return FeatureEngineeringToolExecutor(tool_name)
        elif category == "risk_metrics":
            return RiskMetricsToolExecutor(tool_name)
        
        return None


# ==================== MCP服务器主类 ====================

class FactorToolsMCP:
    """因子工具MCP服务器 - 重构优化版"""
    
    def __init__(self):
        """初始化工具服务器"""
        self.data_cache = {}
        self.computed_factors = {}
        self.tool_factory = ToolFactory()
        
        print("✅ FactorToolsMCP初始化完成")
    
    def handle_initialize(self, params: Dict) -> Dict:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "factor-tools-mcp",
                "version": "1.0.0"
            }
        }
    
    def handle_tools_list(self, params: Dict) -> Dict:
        """返回工具列表"""
        tools_list = []
        for name, spec in TOOL_DEFINITIONS.items():
            tools_list.append({
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"]
            })
        return {"tools": tools_list}
    
    def handle_tools_call(self, params: Dict) -> Dict:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # 使用工具工厂创建执行器
            executor = self.tool_factory.create_executor(tool_name)
            if not executor:
                return self._create_error_response(f"未知工具: {tool_name}")
            
            # 执行工具
            result = executor.execute(arguments)
            return self._create_success_response(result)
            
        except Exception as e:
            return self._create_error_response(str(e))
    
    def _create_success_response(self, result: Dict) -> Dict:
        """创建成功响应"""
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }]
        }
    
    def _create_error_response(self, error_msg: str) -> Dict:
        """创建错误响应"""
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({"error": error_msg}, ensure_ascii=False)
            }],
            "isError": True
        }
    
    def run(self):
        """运行MCP服务器"""
        print("🚀 Factor Tools MCP Server started", file=sys.stderr)
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")
                
                if method == "initialize":
                    response = self.handle_initialize(params)
                elif method == "tools/list":
                    response = self.handle_tools_list(params)
                elif method == "tools/call":
                    response = self.handle_tools_call(params)
                else:
                    response = {"error": f"未知方法: {method}"}
                
                output = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": response
                }
                
                print(json.dumps(output), flush=True)
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = FactorToolsMCP()
    server.run()