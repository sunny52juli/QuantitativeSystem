"""
工具执行器

将工具调用转换为实际代码，管理中间计算变量
"""

from typing import Dict
import pandas as pd

from core.mcp.tool_implementations import execute_tool as execute_tool_impl


class ToolExecutor:
    """
    工具执行器，将工具调用转换为实际代码
    
    职责：
    - 协调工具调用
    - 管理中间变量
    - 调用 core/mcp/tool_implementations.py 中的共享工具实现
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化工具执行器
        
        Args:
            data: 股票数据 DataFrame
        """
        self.data = data
        self.computed_vars = {}  # 存储中间计算结果
    
    def execute_tool(self, tool_spec: Dict) -> str:
        """
        执行工具调用（通过共享工具实现）
        
        Args:
            tool_spec: 工具规格字典，包含 tool, params, var 字段
            
        Returns:
            变量名（用于后续引用）
        """
        tool = tool_spec.get('tool')
        params = tool_spec.get('params', {})
        var_name = tool_spec.get('var', f"temp_{len(self.computed_vars)}")
        
        # 调用共享工具实现（单一数据源）
        try:
            result = execute_tool_impl(
                tool_name=tool,
                data=self.data,
                params=params,
                computed_vars=self.computed_vars
            )
        except ValueError as e:
            raise ValueError(f"工具执行失败 [{tool}]: {str(e)}")
        
        # 存储结果
        self.computed_vars[var_name] = result
        return var_name
    
    def reset(self):
        """重置工具执行器，清空中间变量"""
        self.computed_vars = {}
    
    def get_computed_vars(self) -> Dict:
        """获取所有已计算的变量"""
        return self.computed_vars.copy()
