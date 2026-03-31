# QuantitativeSystem - AI驱动的量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于AI大模型的智能量化交易系统，包含**因子挖掘系统**和**股票查询系统**两大核心模块。系统利用LLM（大语言模型）自动生成量化因子和股票筛选逻辑，并提供完整的回测和评估功能。

---

## 📋 目录

- [系统概述](#系统概述)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [详细使用指南](#详细使用指南)
  - [因子挖掘系统](#因子挖掘系统)
  - [股票查询系统](#股票查询系统)
- [配置说明](#配置说明)
- [模块详解](#模块详解)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

---

## 🎯 系统概述

**QuantitativeSystem** 是一个创新的量化交易系统，将人工智能与量化投资深度结合：

### 系统一：因子挖掘系统 (Factor Backtest System)

**主函数**: `factor_backtest_system/run_factor_mining.py`

利用AI自动挖掘和生成量化因子，并进行历史回测验证。系统能够：
- 🤖 根据策略描述自动生成量化因子
- 📊 生成可执行的因子计算脚本
- 📈 对因子进行多持有期回测
- 💡 提供因子优化建议

### 系统二：股票查询系统 (Stock Asking System)

**主函数**: `stock_asking_system/run_stock_query.py`

将自然语言查询转换为股票筛选逻辑，智能筛选符合条件的股票。系统能够：
- 🔍 理解自然语言查询意图
- 🎯 生成精确的筛选逻辑脚本
- 📊 执行股票筛选并计算收益率
- 📈 评估筛选策略的有效性

---

## ✨ 核心功能

### 因子挖掘系统核心功能

1. **AI 因子生成**（AIFactorMiner）
   - 基于策略描述自动生成量化因子
   - 调用 LLM API 进行深度分析
   - 智能选择相关的技术指标和工具
   - 支持工具调用链执行

2. **流程协调**（FactorMiningAgent）
   - 管理数据加载和组件生命周期
   - 协调整个因子挖掘流程
   - 生成因子脚本文件
   - 组织优化建议输出

3. **因子脚本化**（FactorScriptGenerator）
   - 将因子定义转换为可执行 Python 脚本
   - 脚本可独立运行，便于调试和复用
   - 自动保存到 `factor_scripts/` 目录

4. **多维度回测**（FactorMiningFramework）
   - 支持多个持有期同时回测（1 日、5 日、20 日等）
   - 计算年化收益率、夏普比率、最大回撤等指标
   - 分组回测，评估因子区分度

5. **智能优化建议**
   - **LLM 模式**（LLMFactorOptimizer）：基于大模型的深度优化分析
   - **规则模式**（RuleBasedFactorOptimizer）：基于规则的降级方案
   - 分析因子表现并生成优化建议
   - 识别因子的优势和不足

### 股票查询系统核心功能

1. **自然语言理解**
   - 将用户查询转换为结构化筛选逻辑
   - 智能识别行业、指标、条件等要素
   - 支持复杂的组合查询

2. **筛选逻辑生成**
   - 生成JSON格式的筛选逻辑
   - 自动生成可执行的筛选脚本
   - 保存到 `asking_scripts/` 目录

3. **股票筛选执行**
   - 基于生成的逻辑筛选股票
   - 计算置信度评分
   - 提供筛选理由说明

4. **收益率回测**
   - 计算筛选股票的未来收益率
   - 支持多个持有期（1日、5日等）
   - 统计平均收益、胜率等指标

---

## 🏗️ 系统架构

### 整体架构

```
QuantitativeSystem/
├── factor_backtest_system/    # 因子挖掘系统
│   ├── agent/                  # AI Agent 模块
│   │   ├── ai_factor_agent.py  # LLM Agent（调用 API 生成因子）
│   │   ├── mining_agent.py     # 流程协调代理
│   │   ├── llm_optimizer.py    # LLM 优化器
│   │   └── rule_based_optimizer.py  # 规则优化器（降级方案）
│   ├── backtest/               # 回测引擎
│   ├── generators/             # 脚本生成器
│   ├── pipeline/               # 流程管道（调用入口）
│   ├── prompt/                 # 提示词配置
│   ├── tools/                  # 工具函数
│   ├── factor_scripts/         # 生成的因子脚本
│   └── run_factor_mining.py    # 主入口
│
├── stock_asking_system/        # 股票查询系统
│   ├── agent/                  # AI Agent（筛选逻辑生成）
│   ├── backtest/               # 回测模块
│   ├── generators/             # 脚本生成器
│   ├── pipeline/               # 流程管道
│   ├── prompt/                 # 提示词配置
│   ├── tools/                  # 筛选工具
│   ├── asking_scripts/         # 生成的筛选脚本
│   └── run_stock_query.py      # 主入口
│
├── core/                       # 核心功能模块
│   ├── mcp/                    # MCP 工具管理 🆕 重构升级版
│   │   ├── utils.py            # 公共工具函数 (DataAdapter, ExpressionHelpers)
│   │   ├── exceptions.py       # 统一异常处理 (装饰器、错误码)
│   │   ├── mcp_config.py       # 配置管理 (MCPConfig, 工具分类)
│   │   ├── skill_validator.py  # 技能验证器 (因子定义验证)
│   │   ├── tools_selection.py  # 智能工具选择
│   │   ├── tool_implementations.py  # MCP 工具实现
│   │   ├── expression_tools.py # 表达式工具
│   │   └── QUICK_REFERENCE.md  # 快速参考指南
│   ├── skill/                  # 技能系统
│   ├── base_messages.py        # 消息基类
│   ├── exceptions.py           # 异常定义
│   ├── logger.py               # 日志系统
│   ├── path_manager.py         # 路径管理
│   └── prompt_manager.py       # 提示词管理
│
├── datamodule/                 # 数据加载模块
│   ├── base_loader.py          # 基础加载器
│   ├── factor_data_loader.py   # 因子数据加载
│   └── stock_data_loader.py    # 股票数据加载
│
├── data2parquet/               # 数据获取与转换
│   ├── data_fetcher.py         # 数据获取
│   ├── data_generator.py       # 数据生成
│   ├── data_interface.py       # 数据接口
│   └── data_saver.py           # 数据保存
│
├── config/                     # 配置管理
│   ├── api.py                  # API 配置
│   ├── data_fields.py          # 数据字段定义
│   ├── data_path.py            # 数据路径配置
│   ├── factor_backtest_config.py  # 因子挖掘配置
│   ├── stock_query_config.py   # 股票查询配置
│   └── tool_config.py          # 工具配置
│
├── .env.example                # 环境变量示例
└── README.md                   # 本文件
```

### 工作流程

#### 因子挖掘系统工作流程

```
用户输入策略描述
        ↓
   FactorMiningAgent（流程协调与数据管理）
        ↓
   AIFactorMiner（LLM Agent 调用 API）
        ↓
   生成因子定义（包含工具链和表达式）
        ↓
   FactorScriptGenerator（生成脚本） → factor_scripts/
        ↓
   加载历史数据（支持预加载优化）
        ↓
   FactorScriptExecutor（执行计算）
        ↓
   计算多持有期收益率（预计算优化）
        ↓
   多持有期回测（1 日、5 日、20 日等）
        ↓
   LLMFactorOptimizer（可选：深度优化分析）
        ↓
   输出结构化报告（汇总 + 详情）
```

#### 股票查询系统工作流程

```
用户输入自然语言查询
        ↓
   AI Agent理解意图
        ↓
   生成筛选逻辑JSON
        ↓
   生成筛选脚本 → asking_scripts/
        ↓
   加载市场数据
        ↓
   执行股票筛选
        ↓
   计算置信度评分
        ↓
   计算未来收益率
        ↓
   输出筛选报告
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖库：pandas, numpy, openai, tushare, python-dotenv 等

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd QuantitativeSystem
```

2. **安装依赖**

```bash
pip install pandas numpy openai tushare python-dotenv
```

3. **配置环境变量**

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# DeepSeek API配置（或其他兼容OpenAI的API）
DEFAULT_API_KEY=your-api-key-here
DEFAULT_MODEL=deepseek-chat
DEFAULT_API_URL=https://api.deepseek.com/v1/chat/completions

# Tushare配置（可选，用于数据获取）
TUSHARE_TOKEN=your-tushare-token

# 模型参数
MAX_ITERATIONS=5
MAX_TOKENS=4096
TEMPERATURE=0.7
```

4. **准备数据**

确保在 `data2parquet/tushare_data/` 目录下有历史数据文件，或运行数据获取脚本：

```bash
python data2parquet/data_fetcher.py
```

### 快速运行

#### 运行因子挖掘系统

```bash
# 因子挖掘完整模式
python factor_backtest_system/run_factor_mining.py
# 仅回测模式（回测已有脚本）
python factor_backtest_system/backtest/run_scrip_backtest.py
```

系统会自动：
- 读取预定义的策略模板
- 为每个策略生成因子
- 执行回测并输出结果
- 保存因子脚本到 `factor_scripts/` 目录

#### 运行股票查询系统

```bash
# 完整模式（生成 + 筛选 + 回测）
python stock_asking_system/run_stock_query.py

# 仅回测模式（回测已有脚本）
python stock_asking_system/backtest/run_scrip_backtest.py
```

---



#### 预定义策略模板

系统内置多个策略模板，在 `factor_backtest_system/prompt/user_prompt/strategy_configs.py` 中定义：

- **近日强势股票**: 关注短期涨幅和成交量
- **价值投资**: 关注估值指标和基本面
- **成长股**: 关注业绩增长和市场热度
- **技术突破**: 关注技术形态和突破信号

#### 自定义策略

```python
# 自定义策略描述
custom_strategy = """
生成低估值高成长的因子，重点关注：
1. PE < 20，PB < 3
2. 营收增长率 > 20%
3. ROE > 15%
4. 近期股价稳定
"""
```

#### 回测配置

在 `config/factor_backtest_config.py` 中配置：

```python
class FactorBacktestConfig:
    # 每次生成的因子数量
    n_factors = 3
    
    # 持有期配置（天数）
    HOLDING_PERIODS = [1, 5, 20]
    
    # 回测时间范围
    DEFAULT_LOOKBACK_DAYS = 90  # 最近90天
    
    # 股票池配置
    DEFAULT_INDEX_CODE = None  # None表示全市场
    STOCK_POOL_EXCLUDE_ST = True  # 排除ST股票
    STOCK_POOL_MIN_LIST_DAYS = 180  # 最少上市天数
```

#### 独立运行因子脚本

生成的因子脚本可以独立运行：

```bash
# 运行特定日期的因子计算
python factor_scripts/近日强势股票_factor_1_20240101.py 20240315

# 不指定日期则使用最新数据
python factor_scripts/近日强势股票_factor_1_20240101.py
```

#### 运行实例

以下是生成"近日强势股票"因子的完整输出示例：

**策略配置**：
```
策略：生成近日强势股票的因子，重点关注：
1. 短期动量（5-10 日收益率）
2. 价格突破（相对高点位置）
3. 成交量配合（量价齐升）
4. 技术指标强势（RSI、MACD 等）
5. 波动率特征（强势股的波动特性）

目标数量：1
```

**生成的因子**：
```
1. 强势股综合因子
   工具步骤：3 步
      - pct_change({'values': '收盘价', 'periods': 10})
      - rsi({'values': '收盘价', 'window': 14})
      - correlation({'x': 'mom_10', 'y': 'vol', 'window': 10})
   表达式：(mom_10 + (rsi_14 - 50) / 50 + mom_vol_corr) / 3
   逻辑：综合短期动量、RSI 强度及量价相关性。动量捕捉趋势，RSI 衡量超买超卖，
        量价相关性确保上涨有成交量配合，三者等权合成强势股因子。
```

**回测结果**：
```
因子详情：强势股综合因子
================================================================================

持有期：1 天
   - 信号明确度：高
   - 数据完整性：98.5%
   - 计算成功率：100%

持有期：5 天
   - 年化收益率：12.45%
   - 夏普比率：2.683
   - 最大回撤：-4.32%
   - 胜率：62.00%

持有期：20 天
   - 年化收益率：8.32%
   - 夏普比率：1.259
   - 最大回撤：-6.88%
   - 胜率：56.00%
```

**迭代优化计划**：
```
下一步行动:
   • 第一步：修正量价相关性逻辑并回测，验证基础改进效果
   • 第二步：测试不同参数组合（动量 5/10/20 天，RSI 6/12/24 天），寻找最优周期
   • 第三步：实现动态加权方案（基于滚动 20 日 ICIR 计算权重），对比静态加权
   • 第四步：加入行业市值中性化，测试纯 Alpha 表现
   • 第五步：考虑增加反转保护（如 RSI>70 时降低动量权重）

参数测试:
   • 测试 1：mom=[5,10,15], rsi=[6,12,18], corr_window=[5,10,15] 全组合
   • 测试 2：权重组合：进攻型 (0.5,0.3,0.2)、平衡型 (0.4,0.3,0.3)、保守型 (0.3,0.4,0.3)
   • 测试 3：动态加权：基于过去 20 日 ICIR 计算权重，衰减半衰期 5-20 日

预期改进：修正核心错误后，预期年化收益率可提升至 11-13%，夏普比率维持 2.5+；
          完成全部优化后，目标年化收益率 14-16%，夏普比率 3.0+，最大回撤控制在 -1.5% 以内
```

---

### 股票查询系统

#### 基本使用

```python
from stock_asking_system import create_stock_query_pipeline

# 创建查询管道
pipeline = create_stock_query_pipeline()

# 执行查询（完整流程：生成脚本 + 筛选 + 回测）
result = pipeline.run_complete_pipeline(
    query="找出通信设备行业中放量上涨的股票",
    top_n=20,
    holding_periods=[1, 5]
)

# 查看结果
print(f"筛选到 {len(result['candidates'])} 只股票")
print(f"脚本路径：{result['script_path']}")
```

#### 查询配置

在 `config/stock_query_config.py` 中配置：

```python
class StockQueryConfig:
    # 默认返回股票数量
    DEFAULT_TOP_N = 20
    
    # 置信度阈值
    MIN_CONFIDENCE = 0.3
    
    # 持有期配置（天数）
    HOLDING_PERIODS = [1, 5]
    
    # 数据获取配置
    DEFAULT_LOOKBACK_DAYS = 60  # 最近60个交易日
```

#### 查询示例

系统支持多种自然语言查询：

```python
# 行业筛选
"通信设备行业中市值最大的 10 只股票"

# 技术指标
"最近 5 日放量且突破 20 日均线的股票"

# 估值指标
"市盈率低于 15 且市净率低于 2 的股票"

# 组合条件
"电子行业中，市盈率低于 30，换手率大于 3%，均线多头排列，最近涨幅超过 5% 的股票"

# 排名筛选
"按照成交额排名前 20 的股票"
```

#### 运行实例

以下是"找出最近放量突破的股票"查询的完整输出示例：

**查询配置**：
```
查询：找出最近放量突破的股票：
    1. 成交量较前期放大（至少 1.5 倍）
    2. 涨幅>3%
    3. 技术形态良好
    
返回数量：20
持有期：[1, 5] 天
```

**筛选逻辑详情**：
```
表达式：(vol > vol_ma20 * 1.5) & (pct_1d > 0.03) & (ma5 > ma20)
置信度公式：(vol / vol_ma20) * (pct_1d) * ((ma5 - ma20) / ma20)
工具调用:
   1. vol_ma20 = rolling_mean({'values': 'vol', 'window': 20})
   2. pct_1d = pct_change({'values': 'close', 'periods': 1})
   3. ma5 = rolling_mean({'values': 'close', 'window': 5})
   4. ma20 = rolling_mean({'values': 'close', 'window': 20})
```

**回测详情**：
```
筛选日：20260304
筛选结果：20 只股票

    持有期       平均收益        中位数        标准差        最小值        最大值       胜率      有效/总数
   ----------------------------------------------------------------------------------------------
       1 天      -0.58%      -2.67%       8.07%     -10.03%      20.02%     40.0%       20/20
       5 天       0.16%      -1.92%      16.76%     -21.09%      52.39%     40.0%       20/20

   排名    代码           名称                    置信度       1 日收益       5 日收益
   ----------------------------------------------------------------------------------------
   1     603318.SH      水发燃气                     53.34%       -10.03%       -12.56%
   2     001896.SZ      豫能控股                     52.75%         1.26%        16.34%
   3     300164.SZ      通源石油                     51.93%        -8.75%       -19.26%
   4     301373.SZ      凌玮科技                     51.91%        17.38%        52.39%
   5     688297.SH      中无人机                     51.77%        -3.42%       -13.62%
   6     000890.SZ      法尔胜                      51.76%         3.16%         3.27%
   7     300617.SZ      安靠智电                     51.60%         0.45%         5.31%
   8     300880.SZ      迦南智能                     51.53%         5.12%        11.93%
   9     300303.SZ      聚飞光电                     51.47%        20.02%         4.50%
   10    600108.SH      亚盛集团                     51.41%        -5.10%        24.20%
   11    688551.SH      科威尔                      51.37%        -6.33%        -5.51%
   12    301302.SZ      华如科技                     51.33%        -9.95%       -14.37%
   13    002378.SZ      章源钨业                     51.28%        -7.07%        -2.42%
   14    603530.SH      神马电力                     51.11%         6.35%         2.83%
   15    301120.SZ      新特电气                     51.00%        -3.09%        -0.18%
   16    002272.SZ      川润股份                     50.98%        -0.28%        -1.80%
   17    002207.SZ      准油股份                     50.92%        -6.85%       -21.09%
   18    000010.SZ      美丽生态                     50.92%        -2.26%        -2.04%
   19    600714.SH      金瑞矿业                     50.84%         4.30%        -5.17%
   20    600871.SH      石化油服                     50.82%        -6.56%       -19.44%
```

---

## ⚙️ 配置说明

### API配置 (config/api.py)

```python
class APIConfig:
    # DeepSeek API配置
    DEFAULT_API_KEY = os.getenv('DEFAULT_API_KEY')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-chat')
    DEFAULT_API_URL = os.getenv('DEFAULT_API_URL')
    
    # 模型参数
    MAX_ITERATIONS = int(os.getenv('MAX_ITERATIONS', 5))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 4096))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
```

### 数据路径配置 (config/data_path.py)

```python
class DataPathConfig:
    # 数据根目录
    DATA_ROOT = Path(__file__).parent.parent / "data2parquet" / "tushare_data"
    
    # 股票数据路径
    STOCK_DATA_PATH = DATA_ROOT / "stock_data"
    
    # 指数数据路径
    INDEX_DATA_PATH = DATA_ROOT / "indices"
    
    # 行业数据路径
    INDUSTRY_DATA_PATH = DATA_ROOT / "industry"
```

### 工具配置 (config/tool_config.py)

定义了MCP工具的分类和关键词映射，用于智能工具选择。

---

## 🔧 模块详解

### Factor Backtest System 模块 (factor_backtest_system/)

**因子挖掘系统**，基于AI大模型的智能因子挖掘和回测平台。

#### Agent 模块 (agent/)

AI Agent 模块采用职责分离设计，包含以下组件：

1. **AIFactorMiner** (`ai_factor_agent.py`)
   - LLM Agent，负责调用 API 生成因子定义
   - 执行工具调用链
   - 计算因子值
   - 执行回测
   


2. **FactorMiningAgent** (`mining_agent.py`)
   - 流程协调代理，负责协调整个因子挖掘流程
   - 管理数据加载和组件生命周期
   - 生成因子脚本文件
   - 组织优化建议输出


3. **LLMFactorOptimizer** (`llm_optimizer.py`)
   - LLM 驱动的因子优化器
   - 提供深度优化分析
   - 生成代码修改建议
   - 支持置信度评分
   


4. **RuleBasedFactorOptimizer** (`rule_based_optimizer.py`)
   - 基于规则的因子优化器（降级方案）
   - 当 LLM 不可用时的后备方案
   - 基于预设规则生成优化建议

#### Pipeline 模块 (pipeline/)

流程管道模块，系统的调用入口：

- **factor_mining_pipeline.py**: 提供便捷函数和预定义策略
  - `create_factor_miner()`: 创建因子挖掘器实例（支持数据预加载）
  - `get_available_tools()`: 获取 MCP 可用工具列表
  - `select_tools_for_strategy()`: 为策略选择相关工具
  - `generate_recent_strong_stock_factors()`: 生成近日强势股票因子
  - `StrategyTemplates`: 预定义策略模板类
  - **特性**：支持数据共享，避免重复加载；完整的流程编排和结果汇总

#### Backtest 模块 (backtest/)

回测引擎模块：

- **factor_backtest.py**: 因子挖掘框架
  - `FactorMiningFramework`: 回测执行类
  - 多持有期同时回测
  - 分组收益计算
  - **优化**：支持预计算的收益率数据，避免重复计算

- **factor_loader.py**: 因子脚本加载和执行
  - `FactorScriptLoader`: 加载并执行因子脚本
  - `FactorScriptExecutor`: 从因子定义执行计算

- **backtest_report.py** 🆕: 结构化回测报告
  - `print_factor_backtest_summary()`: 汇总报告（多因子对比）
  - `print_single_factor_detail()`: 单个因子详细报告
  - 支持多持有期展示
  - 分组收益统计和个股排名

#### Generators 模块 (generators/)

脚本生成器模块：

- **factor_script_generator.py**: 将因子定义转换为可执行脚本
  - 自动生成 Python 代码
  - 保存到 `factor_scripts/` 目录

---

#### Core 模块 (core/) 

**核心功能模块**，提供通用的工具和服务。

##### MCP 工具管理 (core/mcp/) - 🎉 重构升级版

经过全面重构的 MCP 工具模块，采用模块化设计，提供强大的工具管理和验证功能：

- **utils.py** 🆕 - 公共工具函数和数据适配器
  - `DataAdapter` 类：智能适配双索引/单索引数据格式
    - `get_groupby_key()`: 获取分组键（自动适配索引结构）
    - `apply_grouped_operation()`: 应用分组操作（支持三种数据格式）
    - `ensure_series_with_index()`: 确保 Series 索引对齐
  - `ExpressionHelpers` 类：表达式辅助函数
    - `is_expression()`: 判断是否为表达式
    - `build_namespace()`: 构建计算命名空间
  - **解决问题**：统一数据格式处理逻辑，消除重复代码
  
- **exceptions.py** 🆕 - 统一异常处理体系
  - 完整的异常类层次结构（基类 `MCPError`）
  - 特定异常类型：
    - `ToolExecutionError`: 工具执行失败
    - `ExpressionEvalError`: 表达式评估失败
    - `InvalidFieldError`: 无效字段错误
    - `DataFormatError`: 数据格式错误
  - 错误码常量定义 (`ErrorCodes` 类)
  - 装饰器工具：
    - `@handle_tool_errors`: 自动捕获并转换异常
    - `@validate_expression`: 验证表达式合法性
  - **优势**：精确的错误定位和友好的错误提示
  
- **mcp_config.py** 🆕 - 配置统一管理
  - `MCPConfig` 类集中管理所有配置
  - `TOOL_CATEGORIES`: 工具分类定义（技术指标、数据筛选、统计分析等）
  - `STRATEGY_KEYWORDS`: 策略关键词映射
  - 便捷的配置查询方法：
    - `get_tools_by_category()`: 按类别查询工具
    - `analyze_strategy()`: 分析策略并推荐工具
    - `get_relevant_tools_for_strategy()`: 获取相关工具列表
  - **优势**：避免配置分散，统一管理规则
  
- **skill_validator.py** 🆕 - 技能验证器
  - `SkillValidator` 类验证因子定义
  - 四大验证维度：
    1. **字段验证**：只能使用标准字段（价格、成交量、估值等）
    2. **工具验证**：只能使用合法工具
    3. **表达式验证**：语法正确性和复杂度检查
    4. **逻辑验证**：因子构建逻辑合理性
  - `ValidationResult`: 结构化验证结果
    - `errors`: 错误列表（阻止执行）
    - `warnings`: 警告列表（建议修改）
    - `suggestions`: 优化建议
  - **优势**：将 SKILL.md 文档约束代码化，自动验证 AI 生成的因子
  
- **tools_selection.py**: 智能工具选择器
  - 基于 Agent 的语义匹配
  - 基于关键词的快速匹配
  - 工具分类管理

- **tool_implementations.py**: MCP 工具实现
  - 技术指标计算工具（已优化为 numpy 实现）
    - `calc_ma_optimized()`: 移动平均
    - `calc_macd_optimized()`: MACD
    - `calc_rsi_optimized()`: RSI
    - `calc_boll_optimized()`: 布林带
    - `calc_atr_optimized()`: ATR
  - 数据筛选工具
  - 统计分析工具
  - **性能优化**：技术指标计算速度提升 5-10 倍

- **expression_tools.py**: 表达式工具
  - 因子表达式解析
  - 表达式执行引擎
  - 变量智能推断
  - **增强**：集成 DataAdapter 和 ExpressionHelpers


**快速参考**：详见 [`core/mcp/QUICK_REFERENCE.md`](core/mcp/QUICK_REFERENCE.md)

##### 技能系统 (core/skill/)

- **SKILL.md**: 因子构建知识库
  - 完整的数据字段说明
  - 工具 API 参考
  - 因子构建指南和最佳实践
  
- **skill_loader.py**: 技能文档加载器
  - 动态加载技能文档
  - 支持自定义技能
  - 内容验证和摘要提取

##### 异常处理 (core/exceptions.py)

定义了系统的自定义异常类：
- `MissingAPIKeyError`: API 密钥缺失
- `DataLoadError`: 数据加载失败
- `FactorCalculationError`: 因子计算错误
- `FactorBacktestError`: 回测执行错误
- `ScreeningLogicError`: 筛选逻辑错误
- `MCPError`: MCP 工具基础异常 🆕
- `ToolExecutionError`: 工具执行失败 🆕
- `ExpressionEvalError`: 表达式评估失败 🆕
- `InvalidFieldError`: 无效字段错误 🆕
- `SkillValidationError`: 技能验证失败 🆕

#### 日志系统 (core/logger.py)

统一的日志管理：
```python
from core.logger import get_logger

logger = get_logger(__name__)
logger.info("系统启动")
logger.error("发生错误", exc_info=True)
```

### Datamodule模块 (datamodule/)

**数据加载模块**，负责数据的加载、清洗和预处理。

#### 基础加载器 (base_loader.py)

提供数据加载的基础功能和工具方法。

#### 因子数据加载器 (factor_data_loader.py)


#### 股票数据加载器 (stock_data_loader.py)


### Data2Parquet模块 (data2parquet/)

**数据获取与转换模块**，负责从数据源获取数据并转换为Parquet格式。


## 👨‍💻 开发指南

### 添加新的策略模板

在 `factor_backtest_system/prompt/user_prompt/strategy_configs.py` 中添加：

```python
STRATEGY_CONFIGS = {
    # 新策略模板
    "MY_STRATEGY": """
    生成 XXX 的因子，重点关注：
    1. 条件 1
    2. 条件 2
    3. 条件 3
    """,
}
```

### 添加新的 MCP 工具

在 `core/mcp/tool_implementations.py` 中实现（使用 DataAdapter 和异常装饰器）：

```python
from core.mcp import handle_tool_errors, DataAdapter
import numpy as np

@handle_tool_errors  # 自动错误处理
def my_new_tool(data: pd.DataFrame, params: dict) -> pd.Series:
    """
    新工具的实现
    
    Args:
        data: 输入数据 DataFrame（可能是双索引或单索引）
        params: 参数字典
    
    Returns:
        计算结果 Series
    """
    field = params.get('field', 'close')
    window = params.get('window', 20)
    
    # 使用 DataAdapter 确保索引对齐并适配不同数据格式
    field_data = DataAdapter.ensure_series_with_index(data, data[field])
    
    # 应用分组操作（自动适配：双索引/单索引 ts_code/单索引 trade_date）
    result = DataAdapter.apply_grouped_operation(
        data, 
        field_data, 
        lambda x: x.rolling(window).mean()
    )
    
    return result
```

**性能优化建议**：
- 避免使用 `rolling.apply(lambda x: ...)`
- 使用 numpy 数组操作替代 pandas apply
- 预分配结果数组，避免动态增长
- 参考 `tool_implementations.py` 中的 `calc_*_optimized` 函数实现

在 `config/tool_config.py` 中注册：

```python
class ToolConfig:
    TOOL_CATEGORIES = {
        "我的工具类": ["my_new_tool"]
    }
    
    STRATEGY_KEYWORDS = {
        "my_new_tool": ["关键词1", "关键词2"]
    }
```

### 扩展数据源

在 `data2parquet/` 中添加新的数据接口：

```python
class MyDataInterface:
    def fetch_data(self, start_date, end_date):
        """获取数据"""
        pass
    
    def save_data(self, data, path):
        """保存数据"""
        pass
```

### 验证因子定义（新增）

使用 SkillValidator 验证 AI 生成的因子定义：

```python
from core.mcp import SkillValidator

# 初始化验证器
validator = SkillValidator(SKILL_CONTENT, all_available_tools)

# 验证因子定义
factor_def = {
    'name': '强势股因子',
    'tools': [...],
    'expression': 'score > 0.7',
    'rationale': '...'  # 可选
}

result = validator.validate_factor_definition(factor_def)

if not result.is_valid:
    print("❌ 因子不符合规范：")
    for error in result.errors:
        print(f"   - {error}")
else:
    print("✅ 因子通过验证")
```

### 自定义回测指标

在 `factor_backtest_system/backtest/factor_backtest.py` 中扩展：

```python
def calculate_custom_metric(returns: pd.Series) -> float:
    """计算自定义指标"""
    # 实现逻辑
    return metric_value
```

---

## ❓ 常见问题

### Q1: API密钥配置失败

**问题**: 运行时提示"未检测到API密钥"

**解决方案**:
1. 确保已复制 `.env.example` 为 `.env`
2. 在 `.env` 中正确配置 `DEFAULT_API_KEY`
3. 检查环境变量是否正确加载

### Q2: 数据加载失败

**问题**: 提示"数据文件不存在"或"数据加载失败"

**解决方案**:
1. 检查 `data2parquet/tushare_data/` 目录是否有数据文件
2. 运行数据获取脚本：`python data2parquet/data_fetcher.py`
3. 确保Tushare Token配置正确（如果使用Tushare）

### Q3: 因子计算错误

**问题**: 因子计算时出现异常

**解决方案**:
1. 检查生成的因子脚本语法是否正确
2. 查看日志文件了解详细错误信息
3. 确保数据中包含因子所需的字段
4. 尝试减少因子复杂度

### Q4: 回测结果异常

**问题**: 回测结果显示异常高的收益或异常低的收益

**解决方案**:
1. 检查数据质量，确保没有异常值
2. 验证因子计算逻辑是否正确
3. 检查回测参数配置（持有期、分组数等）
4. 查看详细的回测日志

### Q5: 股票筛选结果为空

**问题**: 查询后没有找到符合条件的股票

**解决方案**:
1. 放宽筛选条件
2. 检查行业名称是否正确（必须使用数据中实际存在的行业名）
3. 确认数据日期范围是否覆盖查询期间
4. 查看生成的筛选逻辑是否合理

### Q6: 内存不足

**问题**: 处理大量数据时内存溢出

**解决方案**:
1. 减少回测的时间范围
2. 限制股票池大小
3. 分批处理数据
4. 增加系统内存

### Q7: MCP 工具使用问题

**问题**: 如何使用新的 MCP 工具模块？

**解决方案**:
1. 查看 [`core/mcp/QUICK_REFERENCE.md`](core/mcp/QUICK_REFERENCE.md) 快速参考指南
2. 参考 [`core/mcp/examples_usage.py`](core/mcp/examples_usage.py) 中的示例代码
3. 使用 `MCPConfig.get_tools_by_category()` 查询可用工具
4. 使用 `SkillValidator` 验证生成的因子定义
5. 使用 `@handle_tool_errors` 装饰器自动处理错误
6. 使用 `DataAdapter` 确保工具函数兼容不同数据格式

### Q8: 如何优化自定义工具的性能？

**问题**: 自定义工具计算速度慢

**解决方案**:
1. **避免使用 pandas apply**: 不使用 `rolling.apply(lambda x: ...)`
2. **使用 numpy 数组操作**: 参考 `tool_implementations.py` 中的优化实现
3. **预分配结果数组**: 避免动态增长导致的性能损耗
4. **简化计算逻辑**: 如用 sum 比较替代完整排序
5. **封装优化函数**: 使用 `calc_*_optimized` 命名规范
6. **考虑 JIT 编译**: 可使用 numba 进行加速
7. **使用 DataAdapter**: 确保正确处理不同数据格式

### Q9: 如何处理不同的数据格式（双索引/单索引）？

**问题**: 工具函数在不同数据格式下报错

**解决方案**:
1. **使用 DataAdapter**: 自动适配三种数据格式
   - 双索引 `(trade_date, ts_code)`: 多股票时间序列
   - 单索引 `ts_code`: 单日期多股票（预筛选阶段）
   - 单索引 `trade_date`: 单股票时间序列（批量筛选阶段）
2. **示例代码**:
```python
from core.mcp import DataAdapter

# 获取字段数据并确保索引对齐
field_data = DataAdapter.ensure_series_with_index(data, data['close'])

# 应用分组操作（自动适配数据格式）
result = DataAdapter.apply_grouped_operation(
    data, 
    field_data, 
    lambda x: x.rolling(20).mean()
)
```

### Q10: 因子验证失败怎么办？

**问题**: AI 生成的因子定义无法通过验证

**解决方案**:
1. **查看错误信息**: SkillValidator 会返回详细的错误列表
2. **检查字段合法性**: 只能使用 ALLOWED_FIELDS 中定义的字段
3. **检查工具合法性**: 只能使用系统中已注册的工具
4. **验证表达式语法**: 确保表达式可以正确执行
5. **参考 SKILL.md**: 查看因子构建的完整约束说明
6. **逐步调试**: 使用 validation_result.errors 定位具体问题

---

## 📝 更新日志


## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至: [houdd@mail.ustc.edu.cn]

---

## 🙏 致谢

感谢以下开源项目和服务：

- [OpenAI](https://openai.com/) - 提供强大的LLM能力
- [DeepSeek](https://www.deepseek.com/) - 提供高性价比的API服务
- [Tushare](https://tushare.pro/) - 提供金融数据接口
- [Pandas](https://pandas.pydata.org/) - 数据处理框架
- [NumPy](https://numpy.org/) - 数值计算库

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**
