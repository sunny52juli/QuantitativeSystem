# Config - 配置管理模块

## 目录说明

本目录存放系统的所有配置文件，包括API密钥、数据库连接、系统参数等。

## 配置文件结构

```
config/
├── __init__.py           # 配置模块初始化，导出配置变量
├── config.py             # 主配置文件（如果存在）
└── README.md             # 本文件
```

## 主要配置项

### 1. API配置

#### Tushare配置
```python
TUSHARE_TOKEN = "your_tushare_token"  # Tushare API Token
```

#### OpenAI配置
```python
OPENAI_API_KEY = "your_openai_api_key"      # OpenAI API密钥
OPENAI_BASE_URL = "https://api.openai.com"  # API基础URL
OPENAI_MODEL = "gpt-4"                       # 使用的模型名称
```

### 2. 数据库配置（如果使用）
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'password',
    'database': 'stock_db'
}
```

### 3. 系统参数
```python
# 数据缓存配置
CACHE_DIR = "./cache"           # 缓存目录
CACHE_EXPIRE_DAYS = 7           # 缓存过期天数

# 日志配置
LOG_LEVEL = "INFO"              # 日志级别
LOG_FILE = "./logs/system.log"  # 日志文件路径
```

## 配置使用方法

### 1. 导入配置

```python
# 方式1：导入所有配置
from config import *

# 方式2：导入特定配置
from config import TUSHARE_TOKEN, OPENAI_API_KEY

# 方式3：导入配置模块
import config
token = config.TUSHARE_TOKEN
```

### 2. 使用StockQueryConfig类（推荐）

```python
from config import StockQueryConfig

# 获取API配置
api_config = StockQueryConfig.get_api_config()
api_key = api_config.get('api_key')
base_url = api_config.get('base_url')
model = api_config.get('model', 'gpt-4')  # 带默认值
```

## 配置文件安全

### 1. 敏感信息保护

**重要**: 配置文件包含敏感信息（API密钥等），请注意：

- ✅ 将配置文件添加到 `.gitignore`
- ✅ 使用环境变量存储敏感信息
- ✅ 提供配置模板文件（如 `config.example.py`）
- ❌ 不要将真实配置提交到版本控制系统

### 2. 环境变量方式（推荐）

```python
import os

# 从环境变量读取配置
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
```

设置环境变量：
```bash
# Linux/Mac
export TUSHARE_TOKEN="your_token"
export OPENAI_API_KEY="your_key"

# Windows
set TUSHARE_TOKEN=your_token
set OPENAI_API_KEY=your_key
```

## 配置初始化流程

1. **首次使用**：复制配置模板并填写真实值
2. **导入检查**：系统启动时检查必需配置是否存在
3. **默认值**：为非必需配置提供合理默认值
4. **验证**：验证配置格式和有效性

## 配置更新

修改配置后需要重启应用才能生效。部分配置支持热更新（如日志级别）。

## 常见问题

### Q1: 如何获取Tushare Token？
A: 访问 [Tushare官网](https://tushare.pro/) 注册并获取Token。

### Q2: OpenAI API Key在哪里获取？
A: 访问 [OpenAI官网](https://platform.openai.com/) 注册并创建API Key。

### Q3: 配置文件找不到怎么办？
A: 检查是否在正确的目录下，或者创建配置文件并填写必需的配置项。

## 配置示例

```python
# config/__init__.py 示例

import os

# Tushare配置
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')

# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

# 系统配置
CACHE_DIR = './cache'
LOG_LEVEL = 'INFO'

class StockQueryConfig:
    @staticmethod
    def get_api_config():
        return {
            'api_key': OPENAI_API_KEY,
            'base_url': OPENAI_BASE_URL,
            'model': OPENAI_MODEL
        }
```