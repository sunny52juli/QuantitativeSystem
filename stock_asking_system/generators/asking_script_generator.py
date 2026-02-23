#!/usr/bin/env python3
"""
筛选逻辑脚本生成器
将 Agent 生成的筛选逻辑转换为可独立运行的 Python 脚本，保存到 asking_scripts 目录
"""

import os
import json
from typing import Dict, List
from datetime import datetime


def _sanitize_filename(name: str) -> str:
    """清理文件名，移除非法字符"""
    illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ',
                     '（', '）', '(', ')', '，', '。', '！', '？']
    for char in illegal_chars:
        name = name.replace(char, '_')
    while '__' in name:
        name = name.replace('__', '_')
    return name.strip('_')


class AskingScriptGenerator:
    """
    筛选逻辑脚本生成器
    
    功能：
    1. 将 Agent 生成的筛选逻辑 JSON 转换为独立的 Python 脚本
    2. 生成的脚本包含 SCREENING_LOGIC 定义和 screen_with_data 函数
    3. 脚本可被 AskingScriptLoader 加载并执行
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化脚本生成器
        
        Args:
            output_dir: 输出目录，默认为 stock_asking_system/asking_scripts
        """
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'asking_scripts'
            )
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ 筛选脚本生成器初始化完成")
        print(f"📁 输出目录: {self.output_dir}")
    
    def generate_script(self, screening_logic: Dict, query: str = "") -> str:
        """
        生成筛选逻辑脚本
        
        Args:
            screening_logic: 筛选逻辑字典，格式：
                {
                    "name": "筛选条件名称",
                    "tools": [...],
                    "expression": "筛选表达式",
                    "confidence_formula": "置信度公式",
                    "rationale": "筛选理由"
                }
            query: 原始用户查询文本
            
        Returns:
            生成的脚本文件路径
        """
        logic_name = screening_logic.get('name', '未命名筛选')
        logic_name_safe = _sanitize_filename(logic_name)
        
        # 生成文件名：筛选名_时间戳.py
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{logic_name_safe}_{timestamp}.py"
        filepath = os.path.join(self.output_dir, filename)
        
        # 生成脚本内容
        script_content = self._generate_script_content(screening_logic, query)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 生成筛选脚本: {filename}")
        print(f"   筛选名称: {logic_name}")
        print(f"   文件路径: {filepath}")
        
        return filepath
    
    def batch_generate_scripts(
        self, 
        screening_logics: List[Dict],
        queries: List[str] = None
    ) -> List[str]:
        """
        批量生成筛选脚本
        
        Args:
            screening_logics: 筛选逻辑列表
            queries: 对应的原始查询列表
            
        Returns:
            生成的脚本文件路径列表
        """
        if queries is None:
            queries = [""] * len(screening_logics)
        
        print(f"\n📝 批量生成筛选脚本...")
        print(f"   筛选逻辑数量: {len(screening_logics)}")
        print("=" * 80)
        
        filepaths = []
        for i, (logic, query) in enumerate(zip(screening_logics, queries), 1):
            print(f"\n[{i}/{len(screening_logics)}] 生成脚本: {logic.get('name', 'N/A')}")
            filepath = self.generate_script(logic, query)
            filepaths.append(filepath)
        
        print("\n" + "=" * 80)
        print(f"✅ 批量生成完成，共生成 {len(filepaths)} 个脚本")
        print("=" * 80)
        
        return filepaths
    
    def _generate_script_content(self, screening_logic: Dict, query: str) -> str:
        """
        生成脚本内容
        
        Args:
            screening_logic: 筛选逻辑字典
            query: 原始用户查询
            
        Returns:
            脚本内容字符串
        """
        logic_name = screening_logic.get('name', '未命名筛选')
        rationale = screening_logic.get('rationale', '无说明')
        tools = screening_logic.get('tools', [])
        expression = screening_logic.get('expression', '')
        confidence_formula = screening_logic.get('confidence_formula', '1.0')
        
        # 生成筛选逻辑 JSON 字符串
        logic_json = json.dumps(screening_logic, ensure_ascii=False, indent=4)
        
        # 生成工具调用描述（用于注释）
        tools_desc = ""
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('tool', 'unknown')
            params = tool.get('params', {})
            var_name = tool.get('var', f'temp_{i}')
            tools_desc += f"    {i}. {var_name} = {tool_name}({params})\n"
        
        script = f'''#!/usr/bin/env python3
"""
筛选逻辑脚本: {logic_name}

原始查询: {query if query else "N/A"}

筛选说明:
    {rationale}

工具步骤:
{tools_desc if tools_desc else "    无工具调用"}
筛选表达式: {expression}
置信度公式: {confidence_formula}

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==================== 筛选逻辑定义 ====================
# 此定义用于 AskingScriptLoader 直接读取，确保与脚本逻辑一致
SCREENING_LOGIC = {logic_json}
# ==================== 筛选逻辑定义结束 ====================

# 原始查询
ORIGINAL_QUERY = """{query}"""


def get_screening_logic() -> dict:
    """获取筛选逻辑定义（供加载器使用）"""
    return SCREENING_LOGIC


def screen_with_data(data: pd.DataFrame, top_n: int = 20, holding_periods: list = None) -> List[Dict[str, Any]]:
    """
    使用提供的数据执行筛选（供加载器使用）
    
    Args:
        data: 股票数据 DataFrame（双索引：trade_date, ts_code）
        top_n: 返回的股票数量上限
        holding_periods: 持有期列表（天数），传入后会将分析日期前移
        
    Returns:
        筛选结果列表，每项包含 ts_code, name, confidence, reason
    """
    from stock_asking_system.tools.stock_screener import StockScreener
    
    screener = StockScreener(data, holding_periods=holding_periods)
    return screener.execute_screening(
        screening_logic=SCREENING_LOGIC,
        top_n=top_n,
        query=ORIGINAL_QUERY
    )


def main():
    """主函数 - 独立运行时使用"""
    import argparse
    
    parser = argparse.ArgumentParser(description='{logic_name} - 筛选脚本')
    parser.add_argument('--top_n', type=int, default=20, help='返回股票数量（默认20）')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 加载数据
    from datamodule.stock_data_loader import StockDataLoader
    
    print("📊 加载市场数据...")
    loader = StockDataLoader()
    data = loader.load_market_data()
    print(f"✅ 数据加载完成: {{len(data)}} 条记录")
    
    # 执行筛选
    print(f"\\n🔍 执行筛选: {logic_name}")
    results = screen_with_data(data, top_n=args.top_n)
    
    # 显示结果
    print(f"\\n✅ 找到 {{len(results)}} 只符合条件的股票")
    print(f"{{\'排名\':<6}}{{\'股票代码\':<12}}{{\'股票名称\':<20}}{{\'置信度\':<10}}{{\'筛选理由\'}}")
    print("-" * 100)
    
    for i, stock in enumerate(results, 1):
        print(f"{{i:<6}}{{stock[\'ts_code\']:<12}}{{stock[\'name\']:<20}}{{stock[\'confidence\']:.2%}}    {{stock[\'reason\']}}")
    
    # 保存结果
    if args.output and results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"\\n💾 结果已保存: {{args.output}}")


if __name__ == "__main__":
    main()
'''
        
        return script
