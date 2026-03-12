#!/usr/bin/env python3
"""
因子回测系统 - 用户请求格式配置

📖 使用说明：
本文件包含发送给 AI 的用户请求格式模板和返回要求。
{n_factors} 和 {strategy} 是占位符，运行时会被替换。
"""


# ==================== 用户请求格式要求 ====================

USER_REQUEST_FORMAT = """请根据以下策略生成{n_factors}个量化因子：

策略描述：{strategy}

要求：
1. 返回严格的 JSON 格式
2. 每个因子包含：name（因子名称）、tools（工具步骤列表）、expression（最终表达式）、rationale（设计理由）
3. tools 是一个列表，每个元素包含：tool（工具名）、params（参数字典）、var（变量名）
4. 简单因子可以不使用工具，直接用 expression
5. 复杂因子可以组合多个工具，但不超过 3 步

⚠️ 重要规则：
- expression 和 params 中引用变量时，必须使用 tools 中定义的 var 名称，不能使用工具名
- 例如：如果 tool 是 pct_change，var 是 mom5，那么后续引用必须用 mom5，不能用 pct_change
- 如果需要计算量价相关性，必须先分别计算价格变化和成交量变化，存为不同的 var
- params 中的字段名必须是基础数据字段（如"收盘价"、"成交量"）或已定义的 var 名称

返回格式示例：
[
  {{
    "name": "量价动量因子",
    "tools": [
      {{"tool": "pct_change", "params": {{"values": "收盘价", "periods": 5}}, "var": "price_mom"}},
      {{"tool": "pct_change", "params": {{"values": "成交量", "periods": 5}}, "var": "vol_mom"}},
      {{"tool": "correlation", "params": {{"x": "price_mom", "y": "vol_mom", "window": 10}}, "var": "pv_corr"}}
    ],
    "expression": "pv_corr",
    "rationale": "价格动量与成交量动量的相关性，捕捉量价配合特征"
  }}
]

请直接返回 JSON 数组，不要有其他文字。"""
