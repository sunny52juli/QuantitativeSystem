#!/usr/bin/env python3
"""
因子脚本加载器
动态加载和执行 factor_scripts 目录中的因子计算脚本

加载模式：
    仅支持使用脚本中内嵌的 calculate_with_data(data) 函数执行因子计算
"""

import os
import sys
import importlib.util
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path


class FactorScriptLoader:
    """
    因子脚本加载器
    
    功能：
    1. 扫描 factor_scripts 目录中的因子脚本
    2. 动态加载因子脚本模块
    3. 使用脚本内置的 calculate_with_data 函数执行因子计算
    """
    
    def __init__(self, scripts_dir: str = None):
        """
        初始化因子脚本加载器
        
        Args:
            scripts_dir: 因子脚本目录，如果为 None 则使用 factor_scripts 目录
        """
        if scripts_dir is None:
            # 默认指向 factor_scripts 目录（本文件位于 backtest/ 目录下）
            scripts_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'factor_backtest_system', 'factor_scripts'
            )
            # 如果上面的路径不存在，尝试兄弟目录
            if not os.path.isdir(scripts_dir):
                scripts_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..', 'factor_scripts'
                )
                scripts_dir = os.path.abspath(scripts_dir)
        
        self.scripts_dir = scripts_dir
        self.loaded_modules = {}  # 缓存已加载的模块
        
        print(f"✅ 因子脚本加载器初始化完成")
        print(f"📁 脚本目录: {self.scripts_dir}")
    
    def list_scripts(self) -> List[str]:
        """
        列出所有因子脚本
        
        Returns:
            脚本文件名列表
        """
        # 排除非因子脚本文件（工具文件已移至 backtest 目录）
        exclude_files = {'factor_loader.py', 'run_scrip_backtest.py'}
        scripts = []
        for filename in os.listdir(self.scripts_dir):
            if (filename.endswith('.py') 
                and not filename.startswith('_') 
                and filename not in exclude_files):
                scripts.append(filename)
        return scripts
    
    def load_script(self, script_path: str) -> object:
        """
        加载单个因子脚本模块
        
        Args:
            script_path: 脚本文件路径（相对路径或绝对路径）
            
        Returns:
            加载的模块对象
        """
        # 处理路径
        if not os.path.isabs(script_path):
            script_path = os.path.join(self.scripts_dir, script_path)
        
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")
        
        # 检查缓存
        if script_path in self.loaded_modules:
            return self.loaded_modules[script_path]
        
        # 动态加载模块
        module_name = os.path.basename(script_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        
        # 添加项目根目录到路径
        project_root = Path(script_path).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        spec.loader.exec_module(module)
        
        # 缓存模块
        self.loaded_modules[script_path] = module
        
        return module
    
    def calculate_factor(self, script_path: str, data: pd.DataFrame) -> pd.Series:
        """
        使用脚本计算因子值
        
        使用脚本中内嵌的 calculate_with_data 函数执行计算
        
        Args:
            script_path: 脚本文件路径
            data: 股票数据 DataFrame（双索引：trade_date, ts_code）
            
        Returns:
            因子值 Series
        """
        # 加载脚本模块
        module = self.load_script(script_path)
        
        print(f"📊 使用脚本计算因子")
        print(f"   脚本路径: {script_path}")
        
        # 使用脚本中的 calculate_with_data 函数
        if hasattr(module, 'calculate_with_data'):
            print(f"   使用脚本内置的 calculate_with_data 函数")
            return module.calculate_with_data(data)
        
        raise ValueError(
            f"脚本中缺少 calculate_with_data 函数: {script_path}\n"
            f"请确保脚本中定义了 calculate_with_data(data: pd.DataFrame) -> pd.Series 函数"
        )
    
    def clear_cache(self):
        """清除已加载模块的缓存"""
        self.loaded_modules.clear()
        print("🗑️ 已清除脚本缓存")


class FactorScriptExecutor:
    """
    因子脚本执行器
    
    功能：
    1. 根据因子定义执行计算
    2. 支持从脚本加载因子定义
    3. 执行回测
    """
    
    def __init__(self, data: pd.DataFrame = None):
        """
        初始化因子脚本执行器
        
        Args:
            data: 股票数据 DataFrame（双索引：trade_date, ts_code）
        """
        self.data = data
        self.computed_vars = {}
    
    def calculate_factor_from_definition(self, factor: Dict, data: pd.DataFrame = None) -> pd.Series:
        """
        根据因子定义计算因子值
        
        Args:
            factor: 因子定义字典，包含 name, tools, expression, rationale 等
            data: 股票数据，如果为 None 则使用初始化时的数据
            
        Returns:
            因子值 Series
        """
        from core.mcp.tool_implementations import execute_tool
        from core.mcp.expression_tools import ExpressionParser, NamespaceBuilder
        
        if data is not None:
            self.data = data
        
        if self.data is None:
            raise ValueError("必须提供股票数据")
        
        factor_name = factor.get('name', 'unknown')
        tools = factor.get('tools', [])
        expression = factor.get('expression', '')
        
        print(f"📊 计算因子: {factor_name}")
        print(f"   工具数量: {len(tools)}")
        print(f"   表达式: {expression}")
        
        # 重置计算变量
        self.computed_vars = {}
        
        # 执行工具调用
        if tools:
            print(f"🔧 执行工具调用...")
            for i, tool_spec in enumerate(tools, 1):
                tool_name = tool_spec.get('tool', 'unknown')
                params = tool_spec.get('params', {})
                var_name = tool_spec.get('var', f'temp_{i}')
                
                print(f"   [{i}/{len(tools)}] {tool_name} -> {var_name}")
                
                result = execute_tool(
                    tool_name=tool_name,
                    data=self.data,
                    params=params,
                    computed_vars=self.computed_vars
                )
                self.computed_vars[var_name] = result
        
        # 计算表达式
        if expression:
            print(f"📐 计算表达式...")
            parsed_expr = ExpressionParser.parse_expression(expression)
            print(f"   解析后: {parsed_expr}")
            
            namespace = NamespaceBuilder.build_namespace(self.data, self.computed_vars)
            
            try:
                factor_values = eval(parsed_expr, {"__builtins__": {}}, namespace)
                
                # 转换为 Series 并确保索引对齐
                if not isinstance(factor_values, pd.Series):
                    factor_values = pd.Series(factor_values, index=self.data.index)
                elif not factor_values.index.equals(self.data.index):
                    factor_values.index = self.data.index
                
                print(f"✅ 表达式计算成功")
                
            except Exception as e:
                print(f"❌ 表达式计算失败: {e}")
                print(f"   可用变量: {list(namespace.keys())}")
                raise
        else:
            # 如果没有表达式，返回最后一个工具的结果
            if self.computed_vars:
                last_var = list(self.computed_vars.values())[-1]
                if not isinstance(last_var, pd.Series):
                    factor_values = pd.Series(last_var, index=self.data.index)
                else:
                    factor_values = last_var
            else:
                raise ValueError("没有表达式且没有工具调用，无法计算因子")
        
        return factor_values


# 使用示例
if __name__ == "__main__":
    print("="*80)
    print("因子脚本加载器")
    print("="*80)
    print("\n使用方法:")
    print("""
    from factor_backtest_system.backtest.factor_loader import FactorScriptLoader, FactorScriptExecutor
    
    # 方法1: 列出所有因子脚本并通过 calculate_with_data 计算
    loader = FactorScriptLoader()
    scripts = loader.list_scripts()
    print(f"找到 {len(scripts)} 个因子脚本")
    
    # 加载并计算因子（脚本必须定义 calculate_with_data 函数）
    factor_values = loader.calculate_factor(scripts[0], data)
    
    # 方法2: 使用因子定义计算因子
    executor = FactorScriptExecutor(data=your_data)
    factor_definition = {
        'name': '动量因子',
        'tools': [
            {'tool': 'pct_change', 'params': {'values': '收盘价', 'periods': 10}, 'var': 'mom10'}
        ],
        'expression': 'zscore_normalize(mom10)'
    }
    factor_values = executor.calculate_factor_from_definition(factor_definition)
    """)
    print("="*80)
