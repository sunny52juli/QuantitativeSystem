#!/usr/bin/env python3
"""
AI 因子挖掘 Agent - 负责调用 LLM 生成因子定义

职责：
1. 调用 LLM API 生成因子定义
2. 解析 LLM 返回的因子 JSON
3. 执行因子计算工具
4. 计算因子值
"""

import os
import requests
import json
from typing import Dict, List
import pandas as pd

from core.logger import get_logger
from core.mcp.expression_tools import ExpressionParser, NamespaceBuilder
from core.mcp.tool_implementations import execute_tool
from factor_backtest_system.prompt.system_prompts import (
    get_system_prompt,
    get_user_prompt,
    get_message
)
from factor_backtest_system.tools import SKILL_CONTENT


class AIFactorMiner:
    """
    AI 因子挖掘 Agent
    
    核心职责：
    1. 管理 LLM API 调用
    2. 解析生成的因子定义
    3. 执行因子计算
    """
    
    def __init__(self, data: pd.DataFrame, api_key: str = None, skill_content: str = None):
        """
        初始化 AI 因子挖掘 Agent
        
        Args:
            data: 股票数据 DataFrame
            api_key: API 密钥
            skill_content: 技能文档内容
        """
        self.logger = get_logger(__name__)
        
        if data is None:
            raise ValueError("必须提供股票数据！")
        
        self.data = data
        self.tool_executor = None  # 延迟初始化
        
        # API 配置
        self.api_key = api_key or os.getenv('DEFAULT_API_KEY')
        self.has_api = self.api_key is not None
        
        # 技能内容
        self.skill_content = skill_content or SKILL_CONTENT
        self.system_prompt = get_system_prompt(self.skill_content)
        
        self.logger.info("✅ AI 因子挖掘 Agent 初始化完成")
        self.logger.info(f"📚 可用工具数量：31")
        self.logger.info(f"🔧 支持复杂工具调用链")
        self.logger.info(f"📖 技能文档长度：{len(self.skill_content)} 字符")
        
        if self.has_api:
            self.logger.info("🤖 LLM API 已启用")
        else:
            self.logger.warning("⚠️ 未检测到 API 密钥，将无法生成因子")
    
    def generate_factors(self, strategy: str, n_factors: int = 3) -> List[Dict]:
        """
        生成因子
        
        Args:
            strategy: 策略描述
            n_factors: 因子数量
            
        Returns:
            因子列表
        """
        self.logger.info(f"\n🔍 开始生成因子：{strategy}")
        
        if not self.has_api:
            raise ValueError("⚠️ 未找到 DEFAULT_API_KEY，无法生成因子")
        
        return self._generate_with_api(strategy, n_factors)
    
    def _generate_with_api(self, strategy: str, n: int) -> List[Dict]:
        """使用 API 生成因子"""
        from config import FactorBacktestConfig
        
        api_config = FactorBacktestConfig.get_api_config()
        api_key = api_config.get('api_key')
        
        if not api_key:
            raise ValueError("未找到 API 密钥")
        
        print(f"\n🤖 使用 AI Agent 生成因子...")
        print(f"   策略：{strategy}")
        print(f"   目标数量：{n}")
        
        user_prompt = get_user_prompt(strategy, n)
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": api_config["model"],
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": api_config["temperature"],
                "max_tokens": api_config["max_tokens"]
            }
            
            print(f"   📡 调用 API: {api_config['api_url']}")
            response = requests.post(
                api_config["api_url"],
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise ValueError(f"API 调用失败，状态码：{response.status_code}")
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"   ✅ API 调用成功")
            print(f"   📝 原始响应长度：{len(content)} 字符")
            
            # 提取 JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            json_str = json_match.group(1) if json_match else content.strip()
            
            # 解析 JSON
            factors = json.loads(json_str)
            
            if not isinstance(factors, list):
                raise ValueError("API 返回的因子格式无效")
            
            # 验证因子格式
            valid_factors = []
            for factor in factors[:n]:
                if isinstance(factor, dict) and 'name' in factor:
                    factor.setdefault('tools', [])
                    factor.setdefault('expression', factor.get('var', 'unknown'))
                    factor.setdefault('rationale', '无说明')
                    
                    valid_factors.append(factor)
                    print(f"   ✓ 解析因子：{factor['name']}")
            
            if valid_factors:
                print(f"   🎉 成功生成 {len(valid_factors)} 个因子")
                return valid_factors
            else:
                raise ValueError("API 返回的因子中没有有效的因子")
                
        except requests.exceptions.Timeout:
            raise ValueError("API 调用超时")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API 请求异常：{str(e)}")
        except Exception as e:
            self.logger.error(f"因子生成失败：{e}")
            raise
    
    def compute_factor(self, factor_spec: Dict) -> pd.Series:
        """
        计算因子值
        
        Args:
            factor_spec: 因子定义字典
            
        Returns:
            因子值 Series
        """
        # 重置工具执行器
        self.tool_executor = execute_tool
        
        factor_name = factor_spec.get('name', 'unknown')
        tools = factor_spec.get('tools', [])
        expression = factor_spec.get('expression', '')
        
        print(f"\n📊 计算因子：{factor_name}")
        
        # 执行工具步骤
        computed_vars = {}
        if tools:
            for i, tool_spec in enumerate(tools, 1):
                tool_name = tool_spec.get('tool', 'unknown')
                var_name = tool_spec.get('var', f'temp_{i}')
                params = tool_spec.get('params', {})
                
                try:
                    result = self.tool_executor(
                        tool_name=tool_name,
                        data=self.data,
                        params=params,
                        computed_vars=computed_vars
                    )
                    computed_vars[var_name] = result
                    print(f"   ✓ 执行工具 {i}: {tool_name} -> {var_name}")
                except Exception as e:
                    print(f"   ❌ 工具执行失败：{e}")
                    raise
        
        # 计算最终表达式
        if not expression:
            if computed_vars:
                last_var = list(computed_vars.values())[-1]
                if not isinstance(last_var, pd.Series):
                    last_var = pd.Series(last_var, index=self.data.index)
                return last_var
            else:
                raise ValueError("No expression and no computed variables")
        
        # 解析并计算表达式
        parsed_expr = ExpressionParser.parse_expression(expression)
        print(f"   📝 解析后的表达式：{parsed_expr}")
        
        namespace = NamespaceBuilder.build_namespace(self.data, computed_vars)
        
        # 智能推断缺失的变量
        variables = NamespaceBuilder.extract_variables(parsed_expr)
        known_vars = set(namespace.keys())
        missing_vars = variables - known_vars
        
        for var in missing_vars:
            computed_value = ExpressionParser.infer_variable(var, self.data)
            if computed_value is not None:
                namespace[var] = computed_value
                print(f"   🔍 智能推断变量：{var}")
        
        try:
            result = eval(parsed_expr, {"__builtins__": {}}, namespace)
            
            if not isinstance(result, pd.Series):
                result = pd.Series(result, index=self.data.index)
            elif not result.index.equals(self.data.index):
                result.index = self.data.index
            
            return result
            
        except Exception as e:
            print(f"   ❌ 表达式计算失败：{e}")
            print(f"   可用变量：{list(namespace.keys())}")
            raise
    
    def backtest_factor(self, factor_spec: Dict) -> Dict:
        """
        回测因子
        
        Args:
            factor_spec: 因子定义字典
            
        Returns:
            回测结果字典
        """
        from factor_backtest_system.backtest.factor_backtest import FactorMiningFramework
        from config import FactorBacktestConfig
        
        factor_name = factor_spec['name']
        print(f"\n📊 回测因子：{factor_name}")
        
        try:
            # 计算因子值
            factor_values = self.compute_factor(factor_spec)
            
            print(f"   📊 因子值统计:")
            print(f"      - 长度：{len(factor_values)}")
            print(f"      - 非空值：{factor_values.notna().sum()}")
            print(f"      - 均值：{factor_values.mean():.4f}")
            print(f"      - 标准差：{factor_values.std():.4f}")
            
            # 添加到数据
            temp_data = self.data.copy()
            temp_data[factor_name] = factor_values
            
            # 计算未来收益率
            temp_data_reset = temp_data.reset_index()
            temp_data_reset['ret'] = temp_data_reset.groupby('ts_code')['close'].pct_change().shift(-1)
            temp_data = temp_data_reset.set_index(['trade_date', 'ts_code'])
            
            # 创建回测框架
            framework = FactorMiningFramework()
            
            # 对所有持有期进行回测
            holding_periods = FactorBacktestConfig.HOLDING_PERIODS
            print(f"   📊 测试多个持有期：{holding_periods}")
            
            all_results = {}
            for period in holding_periods:
                print(f"   ⏱️ 回测持有期：{period}天")
                period_results = framework.backtest_factor(
                    temp_data,
                    factor_name=factor_name,
                    n_groups=5,
                    holding_period=period
                )
                all_results[f'{period}d'] = period_results
            
            # 使用第一个持有期的结果作为主结果
            main_period = holding_periods[0]
            results = all_results[f'{main_period}d']
            
            results['factor_name'] = factor_name
            results['expression'] = factor_spec.get('expression', 'computed')
            results['all_holding_periods'] = all_results
            
            # 打印所有持有期的结果
            for i, period in enumerate(holding_periods):
                period_result = all_results[f'{period}d']
                
                if i == 0:
                    print(f"\n{'='*80}")
                    print(f"📊 主要持有期回测结果：{period}天")
                    print(f"{'='*80}")
                else:
                    print(f"\n{'='*80}")
                    print(f"📊 持有期回测结果：{period}天")
                    print(f"{'='*80}")
                
                framework.print_results(period_result)
            
            return results
            
        except Exception as e:
            print(f"❌ 回测失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return None
