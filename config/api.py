"""
API配置模块 - 管理所有API相关的配置
"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class APIConfig:
    """API配置类 - 包含所有API相关的配置"""
    
    # API基础配置
    DEFAULT_API_URL = os.getenv('DEFAULT_API_URL')
    DEFAULT_API_KEY = os.getenv('DEFAULT_API_KEY')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL')
    
    # 模型参数配置
    MAX_ITERATIONS = 5
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
    @classmethod
    def get_api_config(cls) -> dict:
        """
        获取API配置字典
        
        Returns:
            dict: 包含所有API配置的字典
        """
        # 确保 api_url 是完整的 chat completions 端点
        base_url = cls.DEFAULT_API_URL or ""
        # 移除末尾的斜杠
        base_url = base_url.rstrip('/')
        # 如果不是以 /chat/completions 结尾，则添加
        if not base_url.endswith('/chat/completions'):
            api_url = f"{base_url}/chat/completions"
        else:
            api_url = base_url
        
        return {
            "api_key": cls.DEFAULT_API_KEY,
            "model": cls.DEFAULT_MODEL,
            "api_url": api_url,
            "base_url": cls.DEFAULT_API_URL,  # 保留原始的 base_url 供 OpenAI SDK 使用
            "max_iterations": cls.MAX_ITERATIONS,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE
        }
