# QuantitativeSystem - AI驱动的量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于AI大模型的智能量化交易系统，包含**因子回测系统**和**股票查询系统**两大核心模块。系统利用LLM（大语言模型）自动生成量化因子和股票筛选逻辑，并提供完整的回测和评估功能。

---

## 📋 目录

- [系统概述](#系统概述)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [详细使用指南](#详细使用指南)
  - [因子回测系统](#因子回测系统)
  - [股票查询系统](#股票查询系统)
- [配置说明](#配置说明)
- [模块详解](#模块详解)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

---

## 🎯 系统概述

**QuantitativeSystem** 是一个创新的量化交易系统，将人工智能与量化投资深度结合：

### 系统一：因子回测系统 (Factor Backtest System)

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

### 因子回测系统核心功能

1. **AI因子生成**
   - 基于策略描述自动生成量化因子
   - 支持多种预定义策略模板
   - 智能选择相关的技术指标和工具

2. **因子脚本化**
   - 将因子定义转换为可执行Python脚本
   - 脚本可独立运行，便于调试和复用
   - 自动保存到 `factor_scripts/` 目录

3. **多维度回测**
   - 支持多个持有期同时回测（1日、5日、20日等）
   - 计算年化收益率、夏普比率、最大回撤等指标
   - 分组回测，评估因子区分度

4. **智能优化建议**
   - 分析因子表现并生成优化建议
   - 识别因子的优势和不足
   - 提供改进方向

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
├── factor_backtest_system/    # 因子回测系统
│   ├── agent/                  # AI Agent（因子生成）
│   ├── backtest/               # 回测引擎
│   ├── generators/             # 脚本生成器
│   ├── pipeline/               # 流程管道
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
│   ├── mcp/                    # MCP工具管理
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
│   ├── api.py                  # API配置
│   ├── data_fields.py          # 数据字段定义
│   ├── data_path.py            # 数据路径配置
│   ├── factor_backtest_config.py  # 因子回测配置
│   ├── stock_query_config.py   # 股票查询配置
│   └── tool_config.py          # 工具配置
│
├── .env.example                # 环境变量示例
└── README.md                   # 本文件
```

### 工作流程

#### 因子回测系统工作流程

```
用户输入策略描述
        ↓
   AI Agent分析
        ↓
   生成因子定义
        ↓
   生成因子脚本 → factor_scripts/
        ↓
   加载历史数据
        ↓
   执行因子计算
        ↓
   多持有期回测
        ↓
   生成优化建议
        ↓
   输出完整报告
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

#### 运行因子回测系统

```bash
python factor_backtest_system/run_factor_mining.py
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

# 演示模式（运行3个示例查询）
python stock_asking_system/run_stock_query.py demo

# 仅回测模式（回测已有脚本）
python stock_asking_system/run_stock_query.py backtest
```

---

## 📖 详细使用指南

### 因子回测系统

#### 基本使用

```python
from factor_backtest_system import create_factor_miner

# 创建因子挖掘器
miner = create_factor_miner()

# 定义策略
strategy = """
生成近日强势股票的因子，重点关注：
1. 最近5日涨幅较大
2. 成交量放大
3. 突破关键技术位
"""

# 运行完整流程
result = miner.run_complete_pipeline(
    strategy=strategy,
    n_factors=3,
    strategy_name="近日强势股票"
)

# 查看结果
print(f"生成因子数量: {len(result['factors'])}")
print(f"生成脚本数量: {len(result['script_paths'])}")
```

#### 预定义策略模板

系统内置多个策略模板，在 `factor_backtest_system/prompt/factor_prompts.py` 中定义：

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

result = miner.run_complete_pipeline(
    strategy=custom_strategy,
    n_factors=5,
    strategy_name="低估值高成长"
)
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
print(f"脚本路径: {result['script_path']}")
```

#### 仅筛选（不计算收益率）

```python
# 快速筛选，不生成脚本，不计算收益率
candidates = pipeline.query(
    query="市盈率低于20且换手率大于5%的股票",
    top_n=30
)

for stock in candidates:
    print(f"{stock['name']} ({stock['ts_code']}): {stock['confidence']:.2%}")
```

#### 回测已有脚本

```python
from stock_asking_system.pipeline import backtest_asking_scripts

# 回测所有已生成的脚本
result = backtest_asking_scripts(
    holding_periods=[1, 5],
    top_n=20,
    verbose=True
)

# 查看汇总
for summary in result['summary']:
    print(f"{summary['logic_name']}: {summary['stock_count']}只股票")
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
"通信设备行业中市值最大的10只股票"

# 技术指标
"最近5日放量且突破20日均线的股票"

# 估值指标
"市盈率低于15且市净率低于2的股票"

# 组合条件
"电子行业中，市盈率低于30，换手率大于3%，最近涨幅超过5%的股票"

# 排名筛选
"按照成交额排名前20的股票"
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

### Core模块 (core/)

**核心功能模块**，提供通用的工具和服务。

#### MCP工具管理 (core/mcp/)

- **tools_selection.py**: 智能工具选择器
  - 基于Agent的语义匹配
  - 基于关键词的快速匹配
  - 工具分类管理

- **tool_implementations.py**: MCP工具实现
  - 技术指标计算工具
  - 数据筛选工具
  - 统计分析工具

- **expression_tools.py**: 表达式工具
  - 因子表达式解析
  - 表达式执行引擎

#### 异常处理 (core/exceptions.py)

定义了系统的自定义异常类：
- `MissingAPIKeyError`: API密钥缺失
- `DataLoadError`: 数据加载失败
- `FactorCalculationError`: 因子计算错误
- `FactorBacktestError`: 回测执行错误
- `ScreeningLogicError`: 筛选逻辑错误

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

```python
from datamodule import FactorDataLoader

loader = FactorDataLoader()
data = loader.load_backtest_data()  # 加载回测数据
```

#### 股票数据加载器 (stock_data_loader.py)

```python
from datamodule import StockDataLoader

loader = StockDataLoader()
data = loader.load_market_data()  # 加载市场数据
industries = loader.get_available_industries()  # 获取行业列表
```

### Data2Parquet模块 (data2parquet/)

**数据获取与转换模块**，负责从数据源获取数据并转换为Parquet格式。

- **data_fetcher.py**: 从Tushare等数据源获取数据
- **data_generator.py**: 生成衍生数据（技术指标等）
- **data_saver.py**: 保存数据为Parquet格式
- **trade_calendar.py**: 交易日历管理

---

## 👨‍💻 开发指南

### 添加新的策略模板

在 `factor_backtest_system/prompt/factor_prompts.py` 中添加：

```python
class StrategyPrompts:
    # 新策略模板
    MY_STRATEGY = """
    生成XXX的因子，重点关注：
    1. 条件1
    2. 条件2
    3. 条件3
    """
```

### 添加新的MCP工具

在 `core/mcp/tool_implementations.py` 中实现：

```python
def my_new_tool(data: pd.DataFrame, param1: float, param2: str) -> pd.Series:
    """
    新工具的实现
    
    Args:
        data: 输入数据
        param1: 参数1
        param2: 参数2
    
    Returns:
        计算结果
    """
    # 实现逻辑
    result = ...
    return result
```

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

---

## 📝 更新日志

### v1.0.0 (2024-01-01)

**初始版本发布**

- ✅ 因子回测系统完整实现
- ✅ 股票查询系统完整实现
- ✅ MCP工具管理系统
- ✅ 数据加载和管理模块
- ✅ 配置管理系统
- ✅ 日志和异常处理系统

**核心功能**:
- AI驱动的因子生成
- 多持有期回测
- 自然语言股票查询
- 筛选逻辑自动生成
- 收益率回测评估

---

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
- 发送邮件至: [your-email@example.com]

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
