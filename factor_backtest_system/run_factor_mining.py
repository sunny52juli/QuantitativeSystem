#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子挖掘系统主入口
提供灵活的因子生成和回测功能

新工作流程:
1. 根据 prompt 生成因子代码，放入 factor_scripts
2. 回测时，使用生成的因子代码生成因子

模块结构：
- agent/ - LLM Agent 相关（因子生成、挖掘代理）
- datamodule/ - 数据加载和清洗（脚本加载器、数据加载器）
- backtest/ - 因子回测引擎
- generators/ - 因子脚本生成器
- pipeline/ - 因子挖掘流程管道（调用入口）
"""

import sys
import os
import io

# 设置 Windows 终端 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
FACTOR_SCRIPTS_DIR = PROJECT_ROOT / "factor_backtest_system" / "factor_scripts"

# ==================== 导入核心功能 ====================

# 从 pipeline 模块导入（pipeline 负责调用 agent 和 datamodule）
from factor_backtest_system.pipeline.factor_mining_pipeline import (
    create_factor_miner,
    get_available_tools,
    select_tools_for_strategy,
    generate_recent_strong_stock_factors,
    generate_optimization_suggestions,
    StrategyTemplates
)

# 导入配置
import inspect
from config import FactorBacktestConfig

# 重新导出，保持向后兼容
__all__ = [
    'create_factor_miner',
    'get_available_tools',
    'select_tools_for_strategy',
    'generate_recent_strong_stock_factors',
    'generate_optimization_suggestions'
]


# ==================== 辅助函数 ====================


def run_factor_mining(strategy: str, strategy_name: str, n_factors: int, api_key: str, data=None):
    """
    运行因子挖掘流程（新工作流）
    
    新工作流程：
    1. 根据 prompt 生成因子定义（agent 模块）
    2. 生成因子脚本文件到 factor_scripts 目录（generators 模块）
    3. 使用脚本执行器进行回测（datamodule 模块）
    
    Args:
        strategy: 策略描述
        strategy_name: 策略名称
        n_factors: 因子数量
        api_key: API密钥
        data: 预加载的数据DataFrame，如果为None则由Agent自动加载
    """
    print("\n" + "="*80)
    print(f"🚀 启动因子挖掘系统（模块化架构）")
    print("="*80)
    print(f"📊 策略: {strategy_name}")
    print(f"🎯 目标因子数量: {n_factors}")
    print("="*80)
    print("\n🔄 模块化工作流程:")
    print("   1️⃣ agent/ - 调用 LLM 生成因子定义")
    print("   2️⃣ generators/ - 生成因子脚本文件")
    print("   3️⃣ datamodule/ - 加载数据并执行回测")
    print("="*80)
    
    # 创建因子挖掘器（传入预加载的数据，避免重复加载）
    miner = create_factor_miner(data=data, api_key=api_key)
    
    # 运行完整流程（新工作流）
    result = miner.run_complete_pipeline(
        strategy=strategy, 
        n_factors=n_factors,
        strategy_name=strategy_name
    )
    
    if result:
        print("\n" + "="*80)
        print("🎉 因子挖掘完成！")
        print("="*80)
        print(f"✅ 生成因子数量: {len(result['factors'])}")
        print(f"✅ 生成脚本数量: {len(result.get('script_paths', []))}")
        print(f"✅ 回测完成因子: {len([r for r in result['backtest_results'] if 'backtest_result' in r])}")
        print(f"✅ 优化建议数量: {len(result['optimization_suggestions'])}")
        
        # 显示生成的脚本文件
        if result.get('script_paths'):
            print(f"\n📁 生成的因子脚本:")
            for i, path in enumerate(result['script_paths'], 1):
                print(f"   {i}. {os.path.basename(path)}")
        
        print("="*80)
        print(f"\n💡 提示: 生成的因子脚本可以独立运行:")
        print(f"   python {FACTOR_SCRIPTS_DIR}/<脚本名>.py <日期>")
        print("="*80)
        
        return result
    else:
        print("\n❌ 因子生成失败")
        return None


# ==================== 主程序入口 ====================

def main():
    """主函数"""
    print("="*80)
    print("🤖 AI因子挖掘系统（模块化架构）")
    print("="*80)
    print("\n📦 模块结构:")
    print("   agent/      - LLM Agent 相关（因子生成）")
    print("   datamodule/ - 数据加载和清洗")
    print("   backtest/   - 因子回测引擎")
    print("   generators/ - 因子脚本生成器")
    print("   pipeline/   - 流程管道（调用入口）")
    print("="*80)
    
    # 检查API密钥
    api_key = FactorBacktestConfig.get_api_config().get('api_key')
    n_factors = FactorBacktestConfig.get_factor_config().get('n_factors', 3)

    if not api_key:
        print("\n⚠️ 未检测到API密钥")
        print("设置方法:")
        print("  1. 复制 .env.example 为 .env")
        print("  2. 在 .env 中配置 DEEPSEEK_API_KEY")
        print("  3. 重新运行程序")
        print("\n💡 详细配置说明请查看: docs/CONFIG.md")
        return
    
    print("✅ API密钥已配置")
    
    # 自动从 StrategyPrompts 类中读取所有策略
    strategies = []
    for name, value in inspect.getmembers(StrategyTemplates):
        # 只获取大写字母开头的类属性（策略配置）
        if name.isupper() and isinstance(value, str) and not name.startswith('_'):
            display_name = value.split('\n')[0].replace('生成', '').replace('的因子，重点关注：', '').replace('因子，重点关注：', '').strip()
            strategies.append((name, display_name, value))
    
    # 按策略名称排序
    strategies.sort(key=lambda x: x[0])
    
    print(f"\n📋 共配置 {len(strategies)} 个策略")
    print(f"🎯 每个策略生成 {n_factors} 个因子")
    print("="*80)
    
    # ==================== 预加载数据（只加载一次） ====================
    print(f"\n📥 预加载回测数据（所有策略共享，仅加载一次）...")
    from datamodule import FactorDataLoader
    data_loader = FactorDataLoader()
    shared_data = data_loader.load_backtest_data()
    print(f"✅ 数据预加载完成: {len(shared_data)} 条记录")
    print("=" * 80)
    
    # 存储所有结果
    all_results = {}
    
    # 依次运行每个策略
    for idx, (strategy_key, strategy_name, strategy_prompt) in enumerate(strategies, 1):
        print(f"\n{'='*80}")
        print(f"📌 [{idx}/{len(strategies)}] 开始运行策略: {strategy_name}")
        print(f"{'='*80}")
        
        # 运行因子挖掘（传入共享数据，避免重复加载）
        result = run_factor_mining(strategy_prompt, strategy_name, n_factors, api_key, data=shared_data)
        
        # 保存结果
        all_results[strategy_key] = {
            'name': strategy_name,
            'result': result
        }
        
        if result:
            print(f"\n✅ 策略 [{strategy_name}] 完成")
        else:
            print(f"\n❌ 策略 [{strategy_name}] 失败")
    
    # 打印总结
    print("\n" + "="*80)
    print("📊 所有策略执行完成 - 总结")
    print("="*80)
    
    total_scripts = 0
    for idx, (strategy_key, info) in enumerate(all_results.items(), 1):
        result = info['result']
        name = info['name']
        
        if result:
            factor_count = len(result['factors'])
            script_count = len(result.get('script_paths', []))
            backtest_count = len([r for r in result['backtest_results'] if 'backtest_result' in r])
            total_scripts += script_count
            print(f"{idx}. ✅ {name}: 生成{factor_count}个因子, {script_count}个脚本, 回测{backtest_count}个")
        else:
            print(f"{idx}. ❌ {name}: 执行失败")
    
    print("="*80)
    print(f"\n📁 所有因子脚本已保存到: {FACTOR_SCRIPTS_DIR}")
    print(f"📄 共生成 {total_scripts} 个因子脚本")
    print("="*80)
    
    return all_results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

