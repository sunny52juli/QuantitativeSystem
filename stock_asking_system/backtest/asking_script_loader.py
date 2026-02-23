#!/usr/bin/env python3
"""
筛选脚本加载器
动态加载和执行 asking_scripts 目录中的筛选逻辑脚本
"""

import os
import sys
import importlib.util
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path


class AskingScriptLoader:
    """
    筛选脚本加载器
    
    功能：
    1. 扫描 asking_scripts 目录中的筛选脚本
    2. 动态加载筛选脚本模块
    3. 从脚本中获取筛选逻辑定义 (SCREENING_LOGIC)
    4. 执行筛选并计算收益率
    """
    
    def __init__(self, scripts_dir: str = None):
        """
        初始化筛选脚本加载器
        
        Args:
            scripts_dir: 筛选脚本目录，如果为 None 则使用默认目录
        """
        if scripts_dir is None:
            # 默认指向 asking_scripts 目录（Agent 生成的脚本存放处）
            scripts_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'asking_scripts'
            )
        
        self.scripts_dir = scripts_dir
        self.loaded_modules = {}  # 缓存已加载的模块
        
        print(f"✅ 筛选脚本加载器初始化完成")
        print(f"📁 脚本目录: {self.scripts_dir}")
    
    def list_scripts(self) -> List[str]:
        """
        列出所有筛选脚本
        
        Returns:
            脚本文件名列表
        """
        scripts = []
        if os.path.exists(self.scripts_dir):
            for filename in os.listdir(self.scripts_dir):
                if (filename.endswith('.py') 
                    and not filename.startswith('_') 
                    and filename != 'asking_script_loader.py'):
                    scripts.append(filename)
        return sorted(scripts)
    
    def load_script(self, script_path: str) -> object:
        """
        加载单个筛选脚本模块
        
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
    
    def get_screening_logic(self, script_path: str) -> Optional[Dict]:
        """
        从脚本中获取筛选逻辑定义
        
        Args:
            script_path: 脚本文件路径
            
        Returns:
            筛选逻辑字典，包含 name, tools, expression, confidence_formula, rationale
        """
        module = self.load_script(script_path)
        
        # 优先使用 SCREENING_LOGIC 变量
        if hasattr(module, 'SCREENING_LOGIC'):
            return module.SCREENING_LOGIC
        
        # 尝试使用 get_screening_logic 函数
        if hasattr(module, 'get_screening_logic'):
            return module.get_screening_logic()
        
        return None
    
    def execute_screening(
        self,
        script_path: str,
        data: pd.DataFrame,
        top_n: int = 20,
        holding_periods: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        使用脚本执行筛选
        
        优先使用脚本中的 screen_with_data 函数，
        否则使用 SCREENING_LOGIC + StockScreener 执行
        
        Args:
            script_path: 脚本文件路径
            data: 股票数据 DataFrame（双索引：trade_date, ts_code）
            top_n: 返回的股票数量上限
            holding_periods: 持有期列表（天数），传入后会将分析日期前移
            
        Returns:
            筛选结果列表
        """
        module = self.load_script(script_path)
        
        print(f"📊 使用脚本执行筛选")
        print(f"   脚本路径: {script_path}")
        
        # 方法1: 优先使用脚本中的 screen_with_data 函数
        if hasattr(module, 'screen_with_data'):
            print(f"   使用脚本内置的 screen_with_data 函数")
            return module.screen_with_data(data, top_n=top_n, holding_periods=holding_periods)
        
        raise ValueError(f"脚本中缺少 SCREENING_LOGIC 或 screen_with_data: {script_path}")
    
    def clear_cache(self):
        """清除已加载模块的缓存"""
        self.loaded_modules.clear()
        print("🗑️ 已清除脚本缓存")
