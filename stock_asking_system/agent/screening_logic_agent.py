#!/usr/bin/env python3
"""
筛选逻辑 Agent - 基于 LLM 将自然语言转换为筛选逻辑

职责：
1. 使用 LLM 理解用户查询意图
2. 生成 JSON 格式的筛选逻辑
3. 验证筛选逻辑的格式正确性

改进：
- 使用 Prompt 模板管理器管理系统提示词
- 使用自定义异常类进行更精确的错误处理
- 使用统一的日志系统
- 添加完整的类型注解
"""

import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from config import StockQueryConfig

# 导入核心组件
from core.exceptions import (
    MissingAPIKeyError,
    LLMResponseError,
    LLMParseError,
    ScreeningLogicError,
)
from core.logger import get_logger, LoggerMixin
from core.prompt_manager import PromptManager

# 导入LLM客户端
try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请安装openai库: pip install openai")


# 类型别名
ScreeningLogic = Dict[str, Any]
ToolSpec = Dict[str, Any]


class ScreeningLogicAgent(LoggerMixin):
    """
    筛选逻辑 Agent
    
    使用 LLM 将自然语言查询转换为可执行的筛选逻辑 JSON
    
    改进：
    - LLM 配置从 StockQueryConfig 读取，不接受外部参数传递
    - Prompt 模板管理器从 user_config 加载模板
    - 集成日志系统
    - 使用自定义异常类
    """
    
    def __init__(self, prompt_manager: Optional[PromptManager] = None):
        """
        初始化筛选逻辑 Agent
        
        Args:
            prompt_manager: Prompt模板管理器（可选，用于依赖注入）
        
        Raises:
            MissingAPIKeyError: 当API密钥未配置时
        """
        # 从配置读取 API 设置
        api_config = StockQueryConfig.get_api_config()
        
        api_key = api_config.get('api_key')
        if not api_key:
            raise MissingAPIKeyError()
        
        # 初始化LLM客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_config.get('base_url')
        )
        self.model = api_config.get('model', 'deepseek-chat')
        
        # 可用行业列表（需要从外部设置）
        self.available_industries: List[str] = []
        
        # Prompt 模板管理器（使用本系统的 prompt 目录）
        if prompt_manager is None:
            prompt_dir = str(Path(__file__).parent.parent / "prompt")
            self._prompt_manager = PromptManager(template_dir=prompt_dir)
        else:
            self._prompt_manager = prompt_manager
        
        self.logger.info("筛选逻辑Agent初始化完成")
    
    def set_available_industries(self, industries: List[str]) -> None:
        """
        设置可用的行业列表
        
        Args:
            industries: 行业名称列表
        """
        self.available_industries = industries
        self.logger.debug(f"设置可用行业列表: {len(industries)} 个行业")
    
    def generate(
        self, 
        query: str, 
        relevant_tools: List[ToolSpec]
    ) -> Optional[ScreeningLogic]:
        """
        根据用户查询生成筛选逻辑
        
        生成的筛选逻辑格式：
        {
            "name": "筛选条件名称",
            "tools": [
                {"tool": "工具名", "params": {...}, "var": "变量名"},
                ...
            ],
            "expression": "筛选表达式",
            "confidence_formula": "置信度计算公式",
            "rationale": "筛选理由"
        }
        
        Args:
            query: 用户的自然语言查询
            relevant_tools: 相关的MCP工具列表
            
        Returns:
            筛选逻辑字典，如果生成失败返回None
            
        Raises:
            LLMResponseError: 当LLM返回无效响应时
            LLMParseError: 当无法解析LLM返回内容时
        """
        self.logger.info(f"生成筛选逻辑: {query[:50]}...")
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(relevant_tools)
        user_prompt = f"用户查询：{query}\n\n请生成筛选逻辑的JSON："
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            self.logger.debug(f"LLM响应: {content[:200]}...")
            
            # 提取JSON（可能被代码块包裹）
            json_str = self._extract_json(content)
            
            # 解析JSON
            screening_logic = json.loads(json_str)
            
            # 验证必要字段
            if not self._validate_screening_logic(screening_logic):
                return None
            
            self.logger.info(f"筛选逻辑生成成功: {screening_logic.get('name', 'unknown')}")
            return screening_logic
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            print(f"   ⚠️ JSON解析失败: {e}")
            print(f"   原始内容: {content[:200]}...")
            return None
        except Exception as e:
            self.logger.error(f"生成筛选逻辑失败: {e}", exc_info=True)
            print(f"   ⚠️ 生成筛选逻辑失败: {e}")
            return None
    
    def _extract_json(self, content: str) -> str:
        """
        从LLM响应中提取JSON字符串
        
        Args:
            content: LLM响应内容
            
        Returns:
            JSON字符串
        """
        # 尝试提取代码块中的JSON
        json_match = re.search(r'``json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # 尝试提取普通代码块
        code_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        # 直接返回原内容
        return content
    
    def _build_system_prompt(self, relevant_tools: List[ToolSpec]) -> str:
        """
        构建系统提示词（从 user_config.SCREENING_SYSTEM_PROMPT 加载）
        
        Args:
            relevant_tools: 相关工具列表
            
        Returns:
            系统提示词字符串
        """
        # 准备工具描述（安全访问字段）
        tools_desc = "\n".join([
            f"- {tool.get('name', tool.get('tool', 'unknown'))}: {tool.get('description', tool.get('desc', '无描述'))}"
            for tool in relevant_tools
        ])
        
        # 构建可用行业列表（最多显示 100 个，避免 prompt 过长）
        industries_sample = (
            self.available_industries[:100] 
            if len(self.available_industries) > 100 
            else self.available_industries
        )
        industries_desc = ", ".join(industries_sample)
        
        # 准备模板变量
        template_vars = {
            'tools_desc': tools_desc,
            'industry_count': str(len(self.available_industries)),
            'industries_desc': industries_desc,
        }
        
        # 直接使用 user_config 中的模板（不再尝试从文件加载）
        from stock_asking_system.prompt.user_config import SCREENING_SYSTEM_PROMPT
        from string import Template
        template = Template(SCREENING_SYSTEM_PROMPT)
        return template.safe_substitute(**template_vars)

    def _validate_screening_logic(self, screening_logic: ScreeningLogic) -> bool:
        """
        验证筛选逻辑的格式
        
        Args:
            screening_logic: 筛选逻辑字典
            
        Returns:
            是否有效
        """
        required_fields = ['name', 'tools', 'expression']
        for field in required_fields:
            if field not in screening_logic:
                self.logger.warning(f"筛选逻辑缺少必要字段: {field}")
                print(f"   ⚠️ 缺少必要字段: {field}")
                return False
        
        # 验证 tools 格式
        tools = screening_logic.get('tools', [])
        if not isinstance(tools, list):
            self.logger.warning("筛选逻辑 tools 字段格式错误")
            print("   ⚠️ tools 字段必须是数组")
            return False
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                self.logger.warning(f"筛选逻辑 tools[{i}] 格式错误")
                print(f"   ⚠️ tools[{i}] 必须是对象")
                return False
            if 'tool' not in tool:
                self.logger.warning(f"筛选逻辑 tools[{i}] 缺少 tool 字段")
                print(f"   ⚠️ tools[{i}] 缺少 tool 字段")
                return False
            if 'var' not in tool:
                self.logger.warning(f"筛选逻辑 tools[{i}] 缺少 var 字段")
                print(f"   ⚠️ tools[{i}] 缺少 var 字段")
                return False
        
        return True
