#!/usr/bin/env python3
"""
因子脚本回测入口

独立的因子脚本回测模块，支持直接回测 factor_scripts 目录下已有的因子脚本，
无需经过 AI Agent 生成流程。

使用方式：
    1. 命令行运行（回测所有脚本）：
        python -m factor_backtest_system.backtest.run_scrip_backtest

    2. 命令行指定脚本：
        python -m factor_backtest_system.backtest.run_scrip_backtest script1.py script2.py

    3. 在代码中调用：
        from factor_backtest_system.backtest.run_scrip_backtest import backtest_factor_scripts
        result = backtest_factor_scripts("path/to/script.py")
"""

import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from factor_backtest_system.backtest.factor_loader import FactorScriptLoader, FactorScriptExecutor
from config import FactorBacktestConfig
from factor_backtest_system.backtest.factor_backtest import FactorMiningFramework
from factor_backtest_system.backtest.backtest_report import print_factor_backtest_summary


def backtest_factor_scripts(
    script_paths: Any = None,
    scripts_dir: Optional[str] = None,
    holding_periods: Optional[List[int]] = None,
    n_groups: int = 5,
    index_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    回测指定的因子脚本文件（无需 AI 生成，直接回测已有脚本）
    
    支持三种使用方式：
    1. 指定单个脚本路径：backtest_factor_scripts("path/to/script.py")
    2. 指定多个脚本路径：backtest_factor_scripts(["script1.py", "script2.py"])
    3. 扫描目录所有脚本：backtest_factor_scripts()  # 默认扫描 factor_scripts 目录
    
    Args:
        script_paths: 因子脚本路径，可以是：
            - None: 扫描 scripts_dir 目录下的所有脚本
            - str: 单个脚本文件路径
            - List[str]: 多个脚本文件路径列表
        scripts_dir: 因子脚本目录（仅当 script_paths=None 时生效），
                     默认为 factor_backtest_system/factor_scripts
        holding_periods: 持有期列表（天数），如 [1, 5, 10, 20]，默认使用配置值
        n_groups: 分组数量，默认 5 组
        index_code: 股票池指数代码（如 '000300.SH'），默认使用配置值
        start_date: 回测开始日期 'YYYYMMDD'，默认使用配置值
        end_date: 回测结束日期 'YYYYMMDD'，默认使用配置值
        verbose: 是否输出详细日志
        
    Returns:
        回测结果字典，格式如下：
        {
            'summary': List[Dict],       # 各因子回测摘要
            'details': Dict[str, Dict],  # 各因子详细回测结果（按因子名索引）
            'script_paths': List[str],   # 实际回测的脚本路径列表
            'config': Dict,              # 回测配置信息
        }
    """
    # ==================== 1. 解析脚本路径 ====================
    if script_paths is None:
        # 扫描目录下所有脚本
        loader = FactorScriptLoader(scripts_dir=scripts_dir)
        script_names = loader.list_scripts()
        if not script_names:
            print("⚠️ 未找到任何因子脚本文件")
            return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
        resolved_paths = [
            os.path.join(loader.scripts_dir, name) for name in script_names
        ]
    elif isinstance(script_paths, str):
        resolved_paths = [script_paths]
    elif isinstance(script_paths, (list, tuple)):
        resolved_paths = list(script_paths)
    else:
        raise TypeError(f"script_paths 参数类型不支持: {type(script_paths)}，"
                        f"请传入 str / List[str] / None")
    
    # 验证文件存在性
    valid_paths = []
    for p in resolved_paths:
        if os.path.isfile(p):
            valid_paths.append(p)
        else:
            print(f"⚠️ 脚本文件不存在，已跳过: {p}")
    
    if not valid_paths:
        print("❌ 没有有效的脚本文件可供回测")
        return {'summary': [], 'details': {}, 'script_paths': [], 'config': {}}
    
    # ==================== 2. 准备回测配置 ====================
    _holding_periods = holding_periods or FactorBacktestConfig.HOLDING_PERIODS
    _index_code = index_code if index_code is not None else FactorBacktestConfig.DEFAULT_INDEX_CODE
    _start_date = start_date or FactorBacktestConfig.BACKTEST_DEFAULT_START_DATE
    _end_date = end_date or FactorBacktestConfig.BACKTEST_DEFAULT_END_DATE
    
    config_info = {
        'start_date': _start_date,
        'end_date': _end_date,
        'holding_periods': _holding_periods,
        'n_groups': n_groups,
        'index_code': _index_code,
        'script_count': len(valid_paths),
    }
    
    if verbose:
        print("\n" + "=" * 80)
        print("🔬 因子脚本回测")
        print("=" * 80)
        print(f"📁 待回测脚本数量: {len(valid_paths)}")
        print(f"📅 回测区间: {_start_date} ~ {_end_date}")
        print(f"⏱️ 持有期: {_holding_periods}")
        print(f"📊 分组数量: {n_groups}")
        if _index_code:
            print(f"📈 股票池: {_index_code}")
        print("=" * 80)
    
    # ==================== 3. 创建回测框架（内部会加载并预处理数据） ====================
    if verbose:
        print("\n📥 创建回测框架（加载并预处理数据）...")
    
    framework = FactorMiningFramework(
        start_date=_start_date,
        end_date=_end_date,
        holding_periods=_holding_periods,
        index_code=_index_code,
    )
    
    # 直接使用框架预处理好的数据（已包含 ret、ret_1d、ret_5d 等收益率列）
    data = framework.data
    
    if verbose:
        print(f"✅ 数据准备完成: {len(data)} 条记录（含收益率列）")
    
    # ==================== 4. 创建脚本加载器和执行器 ====================
    script_loader = FactorScriptLoader()
    executor = FactorScriptExecutor(data=data)
    
    # ==================== 5. 逐个回测脚本 ====================
    summary_list = []
    details_dict = {}
    
    for idx, script_path in enumerate(valid_paths, 1):
        script_name = os.path.basename(script_path)
        
        if verbose:
            print(f"\n{'=' * 80}")
            print(f"📌 [{idx}/{len(valid_paths)}] 回测脚本: {script_name}")
            print(f"   路径: {script_path}")
            print(f"{'=' * 80}")
        
        try:
            # 5.1 加载脚本，获取因子定义
            module = script_loader.load_script(script_path)
            
            factor_def = None
            if hasattr(module, 'FACTOR_DEFINITION'):
                factor_def = module.FACTOR_DEFINITION
            elif hasattr(module, 'get_factor_definition'):
                factor_def = module.get_factor_definition()
            
            if factor_def is None:
                if verbose:
                    print(f"   ⚠️ 脚本中未找到 FACTOR_DEFINITION，尝试使用 calculate_with_data")
            
            factor_name = (factor_def.get('name', script_name) if factor_def 
                          else script_name.replace('.py', ''))
            
            if verbose:
                print(f"   📊 因子名称: {factor_name}")
                if factor_def:
                    print(f"   📝 因子说明: {factor_def.get('rationale', 'N/A')}")
                    print(f"   📐 表达式: {factor_def.get('expression', 'N/A')}")
            
            # 5.2 计算因子值
            if verbose:
                print(f"\n   🔧 计算因子值...")
            
            if hasattr(module, 'calculate_with_data'):
                factor_values = module.calculate_with_data(data)
            elif factor_def:
                factor_values = executor.calculate_factor_from_definition(factor_def, data)
            else:
                print(f"   ❌ 无法计算因子值：脚本中缺少 FACTOR_DEFINITION 和 calculate_with_data")
                summary_list.append({
                    'script': script_name,
                    'factor_name': factor_name,
                    'status': '失败',
                    'error': '脚本缺少因子定义或计算函数',
                })
                continue
            
            valid_count = factor_values.notna().sum()
            if verbose:
                print(f"   ✅ 因子计算完成，有效值数量: {valid_count}")
            
            if valid_count == 0:
                print(f"   ❌ 因子值全部为 NaN，跳过回测")
                summary_list.append({
                    'script': script_name,
                    'factor_name': factor_name,
                    'status': '失败',
                    'error': '因子值全部为NaN',
                })
                continue
            
            # 5.3 将因子值合入数据，执行多持有期回测
            temp_data = data.copy()
            temp_data[factor_name] = factor_values
            
            all_period_results = {}
            for period in _holding_periods:
                if verbose:
                    print(f"\n   ⏱️ 回测持有期: {period} 天")
                
                period_result = framework.backtest_factor(
                    temp_data,
                    factor_name=factor_name,
                    n_groups=n_groups,
                    holding_period=period,
                )
                all_period_results[f'{period}d'] = period_result
                
                if verbose:
                    framework.print_results(period_result)
            
            # 5.4 提取摘要指标（取第一个持有期的多空组合指标作为主要参考）
            main_period = _holding_periods[0]
            main_result = all_period_results[f'{main_period}d']
            ls_metrics = main_result.get('metrics', {}).get('group_long_short', {})
            
            summary_entry = {
                'script': script_name,
                'factor_name': factor_name,
                'status': '成功',
                'expression': factor_def.get('expression', 'N/A') if factor_def else 'N/A',
                'rationale': factor_def.get('rationale', 'N/A') if factor_def else 'N/A',
                f'年化收益率({main_period}d)': ls_metrics.get('年化收益率', None),
                f'夏普比率({main_period}d)': ls_metrics.get('夏普比率', None),
                f'最大回撤({main_period}d)': ls_metrics.get('最大回撤', None),
                f'胜率({main_period}d)': ls_metrics.get('胜率', None),
            }
            summary_list.append(summary_entry)
            
            # 保存详细结果
            details_dict[factor_name] = {
                'script_path': script_path,
                'factor_definition': factor_def,
                'all_holding_periods': all_period_results,
                'factor_values_stats': {
                    'count': int(valid_count),
                    'mean': float(factor_values.mean()) if valid_count > 0 else None,
                    'std': float(factor_values.std()) if valid_count > 0 else None,
                },
            }
            
        except Exception as e:
            print(f"   ❌ 回测失败: {e}")
            if verbose:
                traceback.print_exc()
            summary_list.append({
                'script': script_name,
                'factor_name': script_name.replace('.py', ''),
                'status': '失败',
                'error': str(e),
            })
    
    # ==================== 6. 输出汇总报告 ====================
    if verbose:
        print_factor_backtest_summary(summary_list, _holding_periods)
    
    return {
        'summary': summary_list,
        'details': details_dict,
        'script_paths': valid_paths,
        'config': config_info,
    }


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("🔬 因子脚本回测工具")
    print("=" * 80)
    
    # 如果命令行传入了脚本路径参数
    if len(sys.argv) > 1:
        scripts = sys.argv[1:]
        print(f"\n📁 指定回测脚本: {scripts}")
        
        # 如果传入的是文件名（非绝对路径），自动拼接 factor_scripts 目录
        resolved = []
        base_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'factor_scripts'
        )
        base_dir = os.path.abspath(base_dir)
        for s in scripts:
            if os.path.isabs(s):
                resolved.append(s)
            else:
                resolved.append(os.path.join(base_dir, s))
        
        result = backtest_factor_scripts(script_paths=resolved)
    else:
        print("\n📁 扫描 factor_scripts 目录下所有脚本...")
        result = backtest_factor_scripts()
    
    # 输出最终统计
    summary = result.get('summary', [])
    success = sum(1 for s in summary if s['status'] == '成功')
    fail = sum(1 for s in summary if s['status'] == '失败')
    print(f"\n🏁 回测完成！成功: {success}, 失败: {fail}")
