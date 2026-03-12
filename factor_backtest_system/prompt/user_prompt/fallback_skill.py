#!/usr/bin/env python3
"""
因子回测系统 - Fallback 技能文档配置

📖 使用说明：
本文件包含当 SKILL.md 文件不存在时使用的简化版技能文档。
一般不需要修改此文件，除非需要调整 fallback 行为。
"""


# ==================== Fallback 技能文档 ====================

FALLBACK_SKILL_CONTENT = """# Factor Mining Skill - 简化版

## 可用基础字段
开盘价，最高价，最低价，收盘价，成交量，成交额

## 可用工具
1. pct_change - 计算百分比变化
2. rolling_mean - 滚动平均
3. rolling_std - 滚动标准差
4. rank_normalize - 排名标准化
5. zscore_normalize - Z-score 标准化

## 示例
```json
{
  "name": "短期动量",
  "tools": [
    {"tool": "pct_change", "params": {"values": "收盘价", "periods": 5}, "var": "mom5"}
  ],
  "expression": "mom5",
  "rationale": "5 日价格动量"
}
```
"""
