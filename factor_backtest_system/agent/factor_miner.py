#!/usr/bin/env python3
"""
AI因子挖掘器 - 负责调用LLM生成因子定义

职责：
1. 调用 LLM API 生成因子定义
2. 解析 LLM 返回的因子 JSON
3. 执行因子计算工具
4. 计算因子值
"""

import os
from typing import Dict, List
import pandas as pd
import numpy as np
from core.mcp.expression_tools import ExpressionParser, NamespaceBuilder
from factor_backtest_system.prompt.factor_prompts import (
    AIFactorMinerPrompts,
    get_system_prompt,
    get_user_prompt,
    get_message
)
from factor_backtest_system.tools import load_skill_content, SKILL_CONTENT, ToolExecutor
from config.data_fields import FIELD_MAPPING


class AIFactorMiner:
    """
    AI因子挖掘器 - 负责调用LLM生成因子定义
    
    职责：
    1. 管理 LLM API 调用
    2. 解析生成的因子定义
    3. 执行因子计算
    """
    
    def __init__(self, data: pd.DataFrame, api_key: str = None, skill_content: str = None):
        """
        初始化AI因子挖掘器
        
        Parameters:
        -----------
        data : pd.DataFrame
            股票数据（必须提供，来自 DataInterface）
        api_key : str, optional
            API密钥（如果不提供，从环境变量读取）
        skill_content : str, optional
            技能文档内容（如果不提供，从SKILL.md读取）
        """
        if data is None:
            raise ValueError("必须提供股票数据！请使用 DataInterface 获取实际数据。")
        
        self.framework = None  # 延迟初始化，在需要时创建
        self.data = data
        
        # 工具执行器
        self.tool_executor = ToolExecutor(data)
        
        # API配置 - 优先使用传入的api_key，否则从环境变量读取
        if api_key is None:
            api_key = os.getenv('DEFAULT_API_KEY')
        
        self.api_key = api_key
        self.has_api = api_key is not None
        
        # 动态加载技能内容，优先使用传入的skill_content，否则从文件加载
        self.skill_content = skill_content or SKILL_CONTENT
        
        # 系统提示（从配置文件获取）
        self.system_prompt = get_system_prompt(self.skill_content)
        
        print(get_message('INFO', 'agent_started'))
        print(get_message('INFO', 'available_tools', count=31))
        print(get_message('INFO', 'supports_complex'))
        print(get_message('INFO', 'skill_length', length=len(self.skill_content)))
        
        # 显示API状态
        if self.has_api:
            print(get_message('INFO', 'ai_enabled'))
        else:
            print(get_message('WARNING', 'ai_mode_disabled'))
            print(f"   {get_message('HINT', 'set_api_key')}")
    
    def generate_factors(self, strategy: str, n_factors: int = 3) -> List[Dict]:
        """生成因子（支持工具调用）"""
        print(f"\n🔍 生成因子: {strategy}")
        
        if self.has_api:
            factors = self._generate_with_api(strategy, n_factors)
        else:
            raise ValueError("⚠️ 未找到DEFAULT_API_KEY")
        
        return factors

    def _generate_with_api(self, strategy: str, n: int) -> List[Dict]:
        """使用API生成因子 - 真实的agent逐步解析"""
        import requests
        import json
        from config import FactorBacktestConfig
        
        # 获取API配置
        api_config = FactorBacktestConfig.get_api_config()
        api_key = api_config.get('api_key')
        
        if not api_key:
            print("⚠️ 未找到API密钥，回退到规则生成")
            raise ValueError("未找到API密钥")

        print(f"🤖 使用AI Agent生成因子...")
        print(f"   策略: {strategy}")
        print(f"   目标数量: {n}")
        
        # 构建提示词（从配置文件获取）
        user_prompt = get_user_prompt(strategy, n)
        
        # 调用API
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
            
            print(f"   {get_message('INFO', 'calling_api', url=api_config['api_url'])}")
            response = requests.post(
                api_config["api_url"],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(get_message('ERROR', 'api_failed', status_code=response.status_code))
                print(f"   响应: {response.text}")
                raise ValueError(f"API调用失败，状态码: {response.status_code}")
            
            # 解析响应
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(get_message('SUCCESS', 'api_success'))
            print(f"   📝 原始响应长度: {len(content)} 字符")
            
            # 提取JSON（可能被markdown代码块包裹）
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content.strip()
            
            # 解析JSON
            try:
                factors = json.loads(json_str)
                
                if not isinstance(factors, list):
                    print(get_message('WARNING', 'invalid_format'))
                    raise ValueError("API返回的因子格式无效，期望列表类型")
                
                # 验证因子格式
                valid_factors = []
                for factor in factors[:n]:
                    if isinstance(factor, dict) and 'name' in factor:
                        # 确保必要字段存在
                        if 'tools' not in factor:
                            factor['tools'] = []
                        if 'expression' not in factor:
                            factor['expression'] = factor.get('var', 'unknown')
                        if 'rationale' not in factor:
                            factor['rationale'] = '无说明'
                        
                        valid_factors.append(factor)
                        print(f"   {get_message('INFO', 'parsed_factor', name=factor['name'])}")
                
                if valid_factors:
                    print(f"   🎉 {get_message('SUCCESS', 'factor_generated', count=len(valid_factors))}")
                    return valid_factors
                else:
                    print(get_message('WARNING', 'no_valid_factors'))
                    raise ValueError("API返回的因子中没有有效的因子")
                    
            except json.JSONDecodeError as e:
                print(get_message('ERROR', 'json_parse_failed', error=str(e)))
                print(f"   原始内容: {content[:200]}...")
                raise ValueError(f"JSON解析失败: {str(e)}")
                
        except requests.exceptions.Timeout:
            print(get_message('ERROR', 'api_timeout'))
            raise ValueError("API调用超时")
        except requests.exceptions.RequestException as e:
            print(get_message('ERROR', 'api_exception', error=str(e)))
            raise ValueError(f"API请求异常: {str(e)}")
        except Exception as e:
            print(get_message('ERROR', 'unknown_error', error=str(e)))
            import traceback
            traceback.print_exc()
            raise
    
    def compute_factor(self, factor_spec: Dict) -> pd.Series:
        """
        计算因子值（支持工具）
        
        Returns:
            因子值序列（索引与self.data一致）
        """
        # 重置工具执行器
        self.tool_executor = ToolExecutor(self.data)
        
        # 执行工具步骤
        if factor_spec.get('tools'):
            for tool_spec in factor_spec['tools']:
                var_name = self.tool_executor.execute_tool(tool_spec)
                print(f"   执行工具: {tool_spec['tool']} -> {var_name}")
        
        # 计算最终表达式
        expression = factor_spec.get('expression', '')
        
        if not expression:
            # 如果没有表达式，返回最后一个计算的变量
            if self.tool_executor.computed_vars:
                last_var = list(self.tool_executor.computed_vars.values())[-1]
                # 确保索引对齐
                if not isinstance(last_var, pd.Series):
                    last_var = pd.Series(last_var, index=self.data.index)
                elif last_var.index.tolist() != self.data.index.tolist():
                    last_var.index = self.data.index
                return last_var
            else:
                raise ValueError("No expression and no computed variables")
        
        # 解析表达式（替换变量和字段）
        parsed_expr = self._parse_expression(expression)
        print(f"   📝 解析后的表达式: {parsed_expr}")
        
        # 智能推断并计算缺失的变量
        namespace = self._build_namespace(parsed_expr)
        
        try:
            # 评估表达式
            result = eval(parsed_expr, {"__builtins__": {}}, namespace)
            
            # 转换为Series并确保索引对齐
            if not isinstance(result, pd.Series):
                result = pd.Series(result, index=self.data.index)
            elif result.index.tolist() != self.data.index.tolist():
                result.index = self.data.index
            
            return result
            
        except Exception as e:
            print(f"❌ 因子计算失败: {e}")
            print(f"   表达式: {parsed_expr}")
            print(f"   可用变量: {list(namespace.keys())}")
            raise
    
    def _parse_expression(self, expr: str) -> str:
        """
        解析表达式，替换中文字段名和中文变量名
        （委托给ExpressionParser处理）
        """
        return ExpressionParser.parse_expression(expr)
    
    def _build_namespace(self, parsed_expr: str) -> Dict:
        """
        构建表达式的命名空间，智能推断并计算缺失的变量
        （委托给NamespaceBuilder处理）
        """
        # 构建基础命名空间
        namespace = NamespaceBuilder.build_namespace(self.data, self.tool_executor.computed_vars)
        
        # 提取变量并智能推断缺失的变量
        variables = NamespaceBuilder.extract_variables(parsed_expr)
        known_vars = set(namespace.keys())
        missing_vars = variables - known_vars
        
        # 智能推断并计算缺失的变量
        for var in missing_vars:
            computed_value = self._infer_variable(var)
            if computed_value is not None:
                namespace[var] = computed_value
                print(f"   🔍 智能推断变量: {var}")
        
        return namespace
    
    def _infer_variable(self, var_name: str):
        """
        根据变量名智能推断并计算变量值
        （委托给ExpressionParser处理）
        """
        result = ExpressionParser.infer_variable(var_name, self.data)
        if result is None:
            print(f"   ⚠️ 无法推断变量: {var_name}")
        return result
    
    def backtest_factor(self, factor_spec: Dict) -> Dict:
        """回测因子"""
        name = factor_spec['name']
        print(f"\n📊 回测因子: {name}")
        
        try:
            # 计算因子
            factor_values = self.compute_factor(factor_spec)
            
            # 验证因子值
            print(f"   📊 因子值统计:")
            print(f"      - 长度: {len(factor_values)}")
            print(f"      - 索引范围: {factor_values.index.min()} ~ {factor_values.index.max()}")
            print(f"      - 非空值: {factor_values.notna().sum()}")
            print(f"      - 均值: {factor_values.mean():.4f}")
            print(f"      - 标准差: {factor_values.std():.4f}")
            
            # 验证索引对齐
            if not factor_values.index.equals(self.data.index):
                print(f"   ⚠️ 警告: 因子值索引与数据索引不一致")
                factor_values.index = self.data.index
                print(f"      - 已强制对齐索引")
            
            # 添加到数据
            temp_data = self.data.copy()
            temp_data[name] = factor_values
            
            # 计算未来收益率（适配双索引结构）
            temp_data_reset = temp_data.reset_index()
            temp_data_reset['ret'] = temp_data_reset.groupby('ts_code')['close'].pct_change().shift(-1)
            temp_data = temp_data_reset.set_index(['trade_date', 'ts_code'])
            
            # 手动执行回测逻辑
            from factor_backtest_system.backtest.factor_backtest import FactorMiningFramework
            
            # 创建临时框架
            if self.framework is None:
                self.framework = FactorMiningFramework()
            
            # 对所有配置的持有期进行回测
            from config import FactorBacktestConfig
            holding_periods = FactorBacktestConfig.HOLDING_PERIODS
            
            print(f"   📊 测试多个持有期: {holding_periods}")
            
            all_results = {}
            for period in holding_periods:
                print(f"   ⏱️ 回测持有期: {period}天")
                period_results = self.framework.backtest_factor(
                    temp_data,
                    factor_name=name,
                    n_groups=5,
                    holding_period=period
                )
                all_results[f'{period}d'] = period_results
            
            # 使用第一个持有期的结果作为主结果
            main_period = holding_periods[0]
            results = all_results[f'{main_period}d']
            
            results['factor_name'] = name
            results['expression'] = factor_spec.get('expression', 'computed')
            results['all_holding_periods'] = all_results
            
            # 打印所有持有期的完整结果
            for i, period in enumerate(holding_periods):
                period_result = all_results[f'{period}d']
                
                if i == 0:
                    print(f"\n{'='*80}")
                    print(f"📊 主要持有期回测结果: {period}天")
                    print(f"{'='*80}")
                else:
                    print(f"\n{'='*80}")
                    print(f"📊 持有期回测结果: {period}天")
                    print(f"{'='*80}")
                
                self.framework.print_results(period_result)
            
            return results
            
        except Exception as e:
            print(f"❌ 回测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def batch_test(self, factors: List[Dict]) -> pd.DataFrame:
        """批量测试"""
        print(f"\n🚀 批量测试 {len(factors)} 个因子...")
        
        results_list = []
        
        for i, factor in enumerate(factors, 1):
            print(f"\n[{i}/{len(factors)}] {factor['name']}")
            
            try:
                results = self.backtest_factor(factor)
                
                if results:
                    ls = results['metrics'].get('group_long_short', {})
                    results_list.append({
                        '因子': factor['name'],
                        '工具数': len(factor.get('tools', [])),
                        '年化收益': ls.get('年化收益率', 0),
                        '夏普比率': ls.get('夏普比率', 0),
                        '信息比率': ls.get('信息比率', 0)
                    })
            except Exception as e:
                print(f"  失败: {e}")
        
        if results_list:
            df = pd.DataFrame(results_list)
            df = df.sort_values('夏普比率', ascending=False)
            
            print("\n" + "="*80)
            print("测试结果")
            print("="*80)
            print(df.to_string(index=False))
            print("="*80)
            
            return df
        else:
            return pd.DataFrame()
