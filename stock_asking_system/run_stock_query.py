#!/usr/bin/env python3
"""
股票查询系统主入口
新工作流程：
1. Agent 生成筛选逻辑脚本，保存到 asking_scripts 目录
2. 基于 asking_scripts 中的脚本执行股票筛选
3. 对筛选结果计算持有期收益率（回测）
"""

import sys
import os
import io
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# 设置 Windows 终端 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
ASKING_SCRIPTS_DIR = PROJECT_ROOT / "stock_asking_system" / "asking_scripts"

# 导入核心功能
from stock_asking_system.pipeline import create_stock_query_pipeline

# 导入回测模块（仅用于 backtest_only 模式）
from stock_asking_system.backtest import backtest_asking_scripts, print_detailed_backtest_report

# 导入配置
from config import StockQueryConfig
from stock_asking_system.prompt import StockQueryPrompts


def _display_detailed_backtest_report(result: Dict, holding_periods: List[int]):
    """
    显示详细回测报告（按用户要求的格式）
    调用公共的 backtest_report 模块
    
    Args:
        result: run_complete_pipeline 返回的结果字典
        holding_periods: 持有期列表
    """
    candidates = result.get('candidates', [])
    returns_result = result.get('returns', {})
    query = result.get('query', 'N/A')
    screening_date = returns_result.get('screening_date', 'N/A')
    
    if not candidates or not returns_result:
        print(f"\n⚠️ 无有效回测数据")
        return
    
    # 调用公共的回测报告函数
    print_detailed_backtest_report(
        title=query,
        screening_date=screening_date,
        candidates=candidates,
        returns_result=returns_result,
        holding_periods=holding_periods,
    )


def main():
    """
  主函数 - 完整工作流

    流程：
    1. Agent 根据查询生成筛选逻辑脚本到 asking_scripts
    2. 运行完整流程（生成脚本 + 筛选 + 计算收益率）
    3. 显示详细回测报告
    """
    print("=" * 80)
    print("🤖 AI 股票查询系统")
    print("=" * 80)
    print("\n🔄 工作流程:")
    print("  1️⃣  Agent 生成筛选逻辑脚本 → asking_scripts/")
    print("  2️⃣  运行完整流程（生成 + 筛选 + 回测）")
    print("  3️⃣  显示详细回测报告")
    print("=" * 80)

    # 检查 API 密钥
    api_key = StockQueryConfig.get_api_config().get('api_key')

    if not api_key:
        print(f"\n{StockQueryPrompts.get_message('ERROR', 'no_api_key')}")
        print("设置方法:")
        print("  1. 复制 .env.example 为 .env")
        print("  2. 在 .env 中配置 DEEPSEEK_API_KEY")
        print("  3. 重新运行程序")
        return

    print("✅ API 密钥已配置")

    # 创建股票查询 Pipeline
    try:
        pipeline = create_stock_query_pipeline()
    except Exception as e:
        print(f"\n❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return

    # 从配置获取查询列表
    queries = StockQueryPrompts.get_demo_queries()
    top_n = StockQueryConfig.DEFAULT_TOP_N

    print(f"\n📋 将执行 {len(queries)} 个查询")
    print("=" * 80)

    # ==================== 步骤 1: Agent 生成筛选脚本并执行回测 ====================
    print(f"\n{'=' * 80}")
    print("📌 步骤 1: Agent 生成筛选逻辑脚本并执行回测")
    print("=" * 80)

    all_backtest_results = []

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"📌 查询 {i}/{len(queries)}: {query}")
        print(f"{'=' * 80}")

        try:
            # 运行完整流程：生成脚本 + 筛选 + 计算收益率
            result = pipeline.run_complete_pipeline(
                query=query,
                top_n=top_n,
            )

            if result and result.get('candidates'):
                # 收集回测结果用于后续汇总显示
                all_backtest_results.append(result)
                script_path = result.get('script_path')
                if script_path:
                    print(f"\n   ✅ 脚本已保存：{os.path.basename(script_path)}")
            else:
                print(f"\n   ⚠️ 查询未生成有效候选股票")

        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断程序")
            break
        except Exception as e:
            print(f"\n❌ 查询失败：{e}")
            import traceback
            traceback.print_exc()

    # ==================== 步骤 2: 显示详细回测报告 ====================
    if all_backtest_results:
        print(f"\n\n{'=' * 80}")
        print("📌 步骤 2: 详细回测报告")
        print("=" * 80)
        
        for result in all_backtest_results:
            _display_detailed_backtest_report(result, StockQueryConfig.HOLDING_PERIODS)

    print("\n" + "=" * 80)
    print("✅ 所有查询执行完成")
    print(f"📁 生成的脚本保存在：{ASKING_SCRIPTS_DIR}")
    print("=" * 80)


def backtest_only():
    """
    仅回测模式 - 回测 asking_scripts 中已有的脚本

    不调用 Agent，直接加载已有脚本执行筛选和回测
    """
    print("=" * 80)
    print("🔬 AI 股票查询系统 - 回测模式")
    print("=" * 80)
    print(f"📁 扫描脚本目录：{ASKING_SCRIPTS_DIR}")
    print("=" * 80)

    try:
        result = backtest_asking_scripts(verbose=True)

        summary = result.get('summary', [])
        success = sum(1 for s in summary if s['status'] == '成功')
        fail = sum(1 for s in summary if s['status'] == '失败')
        print(f"\n🏁 回测完成！成功：{success}, 失败：{fail}")

    except Exception as e:
        print(f"\n❌ 回测失败：{e}")
        import traceback
        traceback.print_exc()


def demo():
    """演示函数 - 运行预定义的查询示例"""
    print("=" * 80)
    print("🤖 AI 股票查询系统 - 演示模式")
    print("=" * 80)

    # 检查 API 密钥
    api_key = StockQueryConfig.get_api_config().get('api_key')

    if not api_key:
        print(f"\n{StockQueryPrompts.get_message('ERROR', 'no_api_key')}")
        return

    # 创建股票查询 Pipeline
    try:
        pipeline = create_stock_query_pipeline()
    except Exception as e:
        print(f"\n❌ 初始化失败：{e}")
        return

    # 从配置获取前 3 个查询示例
    demo_queries = StockQueryPrompts.get_demo_queries()[:3]

    # 依次执行查询（完整流程：生成脚本 + 筛选 + 回测）
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"📌 示例 {i}/{len(demo_queries)}")
        print(f"{'=' * 80}")

        try:
            results = pipeline.run_complete_pipeline(query, top_n=10)

            if i < len(demo_queries):
                input("\n按回车键继续下一个示例...")

        except Exception as e:
            print(f"\n❌ 查询失败：{e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80)


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'demo':
            # 演示模式
            try:
                demo()
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断程序")
                sys.exit(0)
        elif mode == 'backtest':
            # 仅回测模式
            try:
                backtest_only()
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断程序")
                sys.exit(0)
        else:
            print(f"未知模式：{mode}")
            print("用法:")
            print("  python run_stock_query.py          # 完整模式（生成 + 筛选 + 回测）")
            print("  python run_stock_query.py demo      # 演示模式")
            print("  python run_stock_query.py backtest   # 仅回测已有脚本")
            sys.exit(1)
    else:
        # 正常模式（完整流程）
        try:
            main()
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断程序")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 程序异常：{e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
