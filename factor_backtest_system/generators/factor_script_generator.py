#!/usr/bin/env python3
"""
因子脚本生成器
将AI生成的因子转换为可独立运行的日粒度脚本
"""

import os
from typing import Dict, List
from datetime import datetime
import json

from factor_backtest_system.tools import sanitize_filename, to_class_name


class FactorScriptGenerator:
    """
    因子脚本生成器
    
    功能：
    1. 将AI生成的因子转换为独立的Python脚本
    2. 生成的脚本可以按日期运行，计算每个股票的因子值
    3. 支持工具调用和表达式计算
    """
    
    def __init__(self, output_dir: str = "factor_scripts"):
        """
        初始化因子脚本生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ 因子脚本生成器初始化完成")
        print(f"📁 输出目录: {self.output_dir}")
    
    def generate_script(self, factor: Dict, strategy_name: str = "default") -> str:
        """
        生成因子计算脚本
        
        Args:
            factor: 因子定义字典
            strategy_name: 策略名称（用于文件命名）
            
        Returns:
            生成的脚本文件路径
        """
        factor_name = factor['name']
        factor_name_safe = sanitize_filename(factor_name)
        strategy_name_safe = sanitize_filename(strategy_name)
        
        # 生成文件名：策略名_因子名_时间戳.py
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy_name_safe}_{factor_name_safe}_{timestamp}.py"
        filepath = os.path.join(self.output_dir, filename)
        
        # 生成脚本内容
        script_content = self._generate_script_content(factor)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 生成因子脚本: {filename}")
        print(f"   因子名称: {factor_name}")
        print(f"   文件路径: {filepath}")
        
        return filepath
    
    def batch_generate_scripts(
        self, 
        factors: List[Dict], 
        strategy_name: str = "default"
    ) -> List[str]:
        """
        批量生成因子脚本
        
        Args:
            factors: 因子列表
            strategy_name: 策略名称
            
        Returns:
            生成的脚本文件路径列表
        """
        print(f"\n📝 批量生成因子脚本...")
        print(f"   策略: {strategy_name}")
        print(f"   因子数量: {len(factors)}")
        print("="*80)
        
        filepaths = []
        
        for i, factor in enumerate(factors, 1):
            print(f"\n[{i}/{len(factors)}] 生成脚本: {factor['name']}")
            filepath = self.generate_script(factor, strategy_name)
            filepaths.append(filepath)
        
        print("\n" + "="*80)
        print(f"✅ 批量生成完成，共生成 {len(filepaths)} 个脚本")
        print("="*80)
        
        return filepaths
    
    def _generate_script_content(self, factor: Dict) -> str:
        """
        生成脚本内容
        
        Args:
            factor: 因子定义字典
            
        Returns:
            脚本内容字符串
        """
        factor_name = factor['name']
        tools = factor.get('tools', [])
        expression = factor.get('expression', '')
        rationale = factor.get('rationale', '无说明')
        
        # 生成工具调用代码
        tools_code = self._generate_tools_code(tools)
        
        # 生成表达式计算代码
        expression_code = self._generate_expression_code(expression, tools)
        
        # 生成因子定义的 JSON 字符串（用于回测时直接读取）
        factor_def_json = json.dumps(factor, ensure_ascii=False, indent=4)
        
        # 生成完整脚本
        script = f'''#!/usr/bin/env python3
"""
因子计算脚本: {factor_name}

因子说明:
{rationale}

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data2parquet.data_interface import DataInterface
from core.mcp.tool_implementations import execute_tool
from core.mcp.expression_tools import ExpressionParser, NamespaceBuilder


# ==================== 因子定义 ====================
# 此定义用于回测系统直接读取，确保与脚本逻辑一致
FACTOR_DEFINITION = {factor_def_json}
# ==================== 因子定义结束 ====================


def get_factor_definition() -> dict:
    """获取因子定义（供回测系统使用）"""
    return FACTOR_DEFINITION


def calculate_with_data(data: pd.DataFrame) -> pd.Series:
    """
    使用提供的数据计算因子值（供回测系统使用）
    
    Args:
        data: 股票数据 DataFrame（双索引：trade_date, ts_code）
        
    Returns:
        因子值 Series
    """
    from factor_backtest_system.backtest.factor_loader import FactorScriptExecutor
    
    executor = FactorScriptExecutor(data=data)
    return executor.calculate_factor_from_definition(FACTOR_DEFINITION, data)


class {to_class_name(factor_name)}:
    """
    {factor_name}
    
    因子说明:
    {rationale}
    """
    
    def __init__(self):
        """初始化因子计算器"""
        self.factor_name = "{factor_name}"
        self.data_interface = DataInterface()
        self.computed_vars = {{}}
    
    def calculate(self, trade_date: str) -> pd.DataFrame:
        """
        计算指定日期的因子值
        
        Args:
            trade_date: 交易日期，格式 'YYYYMMDD'
            
        Returns:
            包含 ts_code 和因子值的 DataFrame
        """
        print(f"\\n{'='*80}")
        print(f"📊 计算因子: {{self.factor_name}}")
        print(f"📅 日期: {{trade_date}}")
        print(f"{'='*80}")
        
        # 1. 加载数据
        print(f"\\n📥 加载数据...")
        data = self._load_data(trade_date)
        
        if data is None or len(data) == 0:
            print(f"❌ 无法加载 {{trade_date}} 的数据")
            return pd.DataFrame()
        
        print(f"✅ 数据加载完成: {{len(data)}} 条记录")
        print(f"   股票数量: {{data.index.get_level_values('ts_code').nunique()}}")
        
        # 2. 执行工具调用
{tools_code}
        
        # 3. 计算因子表达式
{expression_code}
        
        # 4. 返回结果
        result_df = factor_values.to_frame(self.factor_name)
    
        print(f"\\n✅ 因子计算完成")
        print(f"   有效值数量: {{result_df[self.factor_name].notna().sum()}}")
        print(f"   因子均值: {{result_df[self.factor_name].mean():.4f}}")
        print(f"   因子标准差: {{result_df[self.factor_name].std():.4f}}")
        print(f"{'='*80}")
        
        return result_df
    
    def _load_data(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        加载指定日期的市场数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            市场数据 DataFrame（双索引：trade_date, ts_code）
        """
        try:
            # 获取历史数据（需要足够的历史数据来计算技术指标）
            from config import FactorBacktestConfig
            
            # 计算开始日期（向前推120个交易日，确保有足够的历史数据）
            from data2parquet.trade_calendar import TradeCalendar
            import tushare as ts
            
            # 创建 Tushare Pro API 实例
            pro_api = ts.pro_api(os.getenv('DATA_SOURCE_TOKEN'))
            calendar = TradeCalendar(pro_api)
            
            # 获取交易日历
            trade_dates = calendar.get_trade_dates(
                start_date=FactorBacktestConfig.BACKTEST_DEFAULT_START_DATE,
                end_date=trade_date
            )
            
            if not trade_dates or trade_date not in trade_dates:
                print(f"⚠️ {{trade_date}} 不是交易日")
                return None
            
            # 取最近120个交易日作为历史数据
            recent_dates = trade_dates[-120:] if len(trade_dates) >= 120 else trade_dates
            start_date = recent_dates[0]
            
            # 批量获取数据
            market_data_dict = self.data_interface.batch_get_market_data(
                start_date=start_date,
                end_date=trade_date
            )
            
            if not market_data_dict:
                return None
            
            # 合并所有日期的数据
            data = pd.concat(market_data_dict.values(), ignore_index=True)
            
            # 设置双索引
            data['trade_date'] = pd.to_datetime(data['trade_date'])
            data = data.sort_values(['trade_date', 'ts_code'])
            data = data.set_index(['trade_date', 'ts_code'])
            
            return data
            
        except Exception as e:
            print(f"❌ 加载数据失败: {{e}}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='{factor_name} - 因子计算脚本')
    parser.add_argument('--trade_date', type=str, default='20260227', help='交易日期，格式 YYYYMMDD')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 创建因子计算器
    calculator = {to_class_name(factor_name)}()
    
    # 计算因子
    result = calculator.calculate(args.trade_date)
    
    # 保存结果
    if not result.empty:
        if args.output:
            output_path = args.output
        else:
            output_path = f"{{calculator.factor_name}}_{{args.trade_date}}.csv"
        
        result.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\\n💾 结果已保存: {{output_path}}")
    else:
        print(f"\\n⚠️ 无结果数据")


if __name__ == "__main__":
    main()
'''
        
        return script
    
    def _generate_tools_code(self, tools: List[Dict]) -> str:
        """
        生成工具调用代码
        
        Args:
            tools: 工具列表
            
        Returns:
            工具调用代码字符串
        """
        if not tools:
            return "        # 无工具调用"
        
        code_lines = ["        print(f\"\\n🔧 执行工具调用...\")"]
        code_lines.append("        self.computed_vars = {}")
        code_lines.append("")
        
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('tool', 'unknown')
            params = tool.get('params', {})
            var_name = tool.get('var', f'temp_{i}')
            
            # 生成参数字符串
            params_str = json.dumps(params, ensure_ascii=False)
            
            code_lines.append(f"        # 工具 {i}: {tool_name}")
            code_lines.append(f"        print(f\"   [{i}/{len(tools)}] 执行工具: {tool_name}\")")
            code_lines.append(f"        {var_name} = execute_tool(")
            code_lines.append(f"            tool_name='{tool_name}',")
            code_lines.append(f"            data=data,")
            code_lines.append(f"            params={params_str},")
            code_lines.append(f"            computed_vars=self.computed_vars")
            code_lines.append(f"        )")
            code_lines.append(f"        self.computed_vars['{var_name}'] = {var_name}")
            code_lines.append(f"        print(f\"      ✅ {var_name} 计算完成\")")
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_expression_code(self, expression: str, tools: List[Dict]) -> str:
        """
        生成表达式计算代码
        
        Args:
            expression: 表达式字符串
            tools: 工具列表
            
        Returns:
            表达式计算代码字符串
        """
        if not expression:
            # 如果没有表达式，返回最后一个工具的结果
            if tools:
                last_var = tools[-1].get('var', 'temp_1')
                return f'''        print(f"\\n📐 使用工具结果作为因子值...")
        factor_values = self.computed_vars['{last_var}']
        
        # 确保是 Series 类型且索引对齐
        if not isinstance(factor_values, pd.Series):
            factor_values = pd.Series(factor_values, index=data.index)
        elif not factor_values.index.equals(data.index):
            factor_values.index = data.index'''
            else:
                return '''        print(f"\\n❌ 无表达式且无工具调用")
        raise ValueError("无法计算因子值")'''
        
        # 转义表达式中的引号和反斜杠
        expression_escaped = expression.replace('\\', '\\\\').replace('"', '\\"')
        
        code = f'''        print(f"\\n📐 计算因子表达式...")
        print(f"   原始表达式: {expression_escaped}")
        
        # 解析表达式
        parsed_expr = ExpressionParser.parse_expression("{expression_escaped}")
        print(f"   解析后表达式: {{parsed_expr}}")
        
        # 构建命名空间
        namespace = NamespaceBuilder.build_namespace(data, self.computed_vars)
        
        # 计算表达式
        try:
            factor_values = eval(parsed_expr, {{"__builtins__": {{}}}}, namespace)
            
            # 转换为 Series 并确保索引对齐
            if not isinstance(factor_values, pd.Series):
                factor_values = pd.Series(factor_values, index=data.index)
            elif not factor_values.index.equals(data.index):
                factor_values.index = data.index
            
            print(f"   ✅ 表达式计算成功")
            
        except Exception as e:
            print(f"   ❌ 表达式计算失败: {{e}}")
            print(f"   可用变量: {{list(namespace.keys())}}")
            raise'''
        
        return code
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        清理文件名，移除非法字符（向后兼容方法）
        """
        return sanitize_filename(name)
    
    @staticmethod
    def _to_class_name(name: str) -> str:
        """
        将因子名称转换为类名（向后兼容方法）
        """
        return to_class_name(name)


# 使用示例
if __name__ == "__main__":
    print("="*80)
    print("因子脚本生成器")
    print("="*80)
    print("\n使用方法:")
    print("1. 从 main/main.py 中调用本模块")
    print("2. 传入AI生成的因子定义")
    print("3. 自动生成可独立运行的因子计算脚本")
    print("="*80)
    print("\n示例代码:")
    print("""
from factor_backtest_system.generators.factor_script_generator import FactorScriptGenerator
    
    # 创建生成器
    generator = FactorScriptGenerator(output_dir='factor_scripts')
    
    # 生成单个因子脚本
    factor = {
        'name': '动量因子',
        'tools': [...],
        'expression': 'zscore_normalize(mom20)',
        'rationale': '捕捉20日动量效应'
    }
    filepath = generator.generate_script(factor, strategy_name='动量策略')
    
    # 批量生成
    filepaths = generator.batch_generate_scripts(factors, strategy_name='动量策略')
    """)
    print("="*80)
