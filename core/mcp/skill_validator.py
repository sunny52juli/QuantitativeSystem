"""
技能验证器 - 将 SKILL.md 约束代码化

解决问题：
- SKILL.md 只是静态文档，LLM 可能忽略其中的约束
- 缺少对 AI 生成因子的自动验证机制
- 需要确保因子定义符合系统规范

使用方式：
    from core.mcp.skill_validator import SkillValidator
    
    validator = SkillValidator(SKILL_CONTENT, all_tools)
    result = validator.validate_factor_definition(generated_factor)
    
    if not result.is_valid:
        raise ValueError(f"因子不符合规范：{result.errors}")
"""

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """
    验证结果
    
    Attributes:
        is_valid: 是否通过验证
        errors: 错误列表
        warnings: 警告列表
        suggestions: 建议列表
    """
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str):
        """添加建议"""
        self.suggestions.append(suggestion)
    
    def merge(self, other: 'ValidationResult'):
        """合并另一个验证结果"""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.suggestions.extend(other.suggestions)


class SkillValidator:
    """
    技能验证器
    
    验证因子定义是否符合 SKILL.md 的约束：
    1. 字段约束：只能使用标准字段
    2. 工具约束：只能使用合法工具
    3. 表达式约束：语法正确性
    4. 逻辑约束：因子构建逻辑合理性
    """
    
    # ==================== 标准字段定义 ====================
    
    # 基础价格字段
    PRICE_FIELDS = {
        '开盘价', 'open', '最高价', 'high', '最低价', 'low', 
        '收盘价', 'close', '前收盘', 'pre_close', 
        '涨跌额', 'change', '涨跌幅', 'pct_chg'
    }
    
    # 成交量字段
    VOLUME_FIELDS = {
        '成交量', 'vol', '成交额', 'amount'
    }
    
    # 基础信息字段
    INFO_FIELDS = {
        'trade_date', 'date', 'ts_code', 'code', 'name', 
        'area', 'industry', 'market', 'list_date'
    }
    
    # 估值指标字段
    VALUATION_FIELDS = {
        'turnover_rate', 'turnover_rate_f', 'vol_ratio',
        'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm',
        'dv_ratio', 'dv_ttm',
        'total_share', 'float_share', 'free_share',
        'total_mv', 'circ_mv'
    }
    
    # 资金流向字段
    FLOW_FIELDS = {
        'buy_sm_vol', 'buy_sm_amount', 'sell_sm_vol', 'sell_sm_amount',
        'buy_md_vol', 'buy_md_amount', 'sell_md_vol', 'sell_md_amount',
        'buy_lg_vol', 'buy_lg_amount', 'sell_lg_vol', 'sell_lg_amount',
        'buy_elg_vol', 'buy_elg_amount', 'sell_elg_vol', 'sell_elg_amount',
        'net_mf_vol', 'net_mf_amount'
    }
    
    # 融资融券字段
    MARGIN_FIELDS = {
        'rzye', 'rqye', 'rzmre', 'rqyl', 'rzche', 'rqchl', 
        'rqmcl', 'rzrqye'
    }
    
    # 衍生字段
    DERIVED_FIELDS = {
        'vwap', 'ret', 'ret1', 'volatility', 'adj_factor'
    }
    
    # 所有允许的字段集合
    ALLOWED_FIELDS: Set[str] = (
        PRICE_FIELDS | VOLUME_FIELDS | INFO_FIELDS | 
        VALUATION_FIELDS | FLOW_FIELDS | MARGIN_FIELDS | DERIVED_FIELDS
    )
    
    # ==================== 初始化 ====================
    
    def __init__(self, skill_content: str, available_tools: List[Dict]):
        """
        初始化验证器
        
        Args:
            skill_content: SKILL.md 内容
            available_tools: 可用工具列表
        """
        self.skill_content = skill_content
        self.available_tools = {t['name']: t for t in available_tools}
        self.tool_names = set(self.available_tools.keys())
    
    # ==================== 主验证方法 ====================
    
    def validate_factor_definition(
        self, 
        factor_def: Dict[str, Any]
    ) -> ValidationResult:
        """
        验证因子定义
        
        Args:
            factor_def: 因子定义字典，包含 name, tools, expression, rationale
        
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        # 1. 检查必需字段
        required_fields = ['name', 'expression']
        for field in required_fields:
            if field not in factor_def:
                result.add_error(f"缺少必需字段：{field}")
        
        if not result.is_valid:
            return result
        
        # 2. 验证工具链
        tools = factor_def.get('tools', [])
        tools_result = self.validate_tools(tools)
        result.merge(tools_result)
        
        # 3. 验证表达式
        expression = factor_def.get('expression', '')
        expr_result = self.validate_expression(expression, tools)
        result.merge(expr_result)
        
        # 4. 验证命名合理性
        name = factor_def.get('name', '')
        name_result = self.validate_factor_name(name)
        result.merge(name_result)
        
        # 5. 验证逻辑说明（可选）
        rationale = factor_def.get('rationale', '')
        if rationale:
            rationale_result = self.validate_rationale(rationale)
            result.merge(rationale_result)
        
        return result
    
    # ==================== 工具验证 ====================
    
    def validate_tools(self, tools: List[Dict]) -> ValidationResult:
        """
        验证工具链
        
        Args:
            tools: 工具调用列表
        
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        if not tools:
            return result
        
        used_vars = set()
        
        for i, tool_call in enumerate(tools):
            # 检查工具是否存在
            tool_name = tool_call.get('tool')
            if not tool_name:
                result.add_error(f"工具 {i+1}: 缺少工具名称")
                continue
            
            if tool_name not in self.tool_names:
                result.add_error(
                    f"工具 {i+1}: 无效的工具名称 '{tool_name}'\n"
                    f"可用工具：{', '.join(sorted(self.tool_names)[:10])}..."
                )
                continue
            
            # 检查参数
            params = tool_call.get('params', {})
            if not isinstance(params, dict):
                result.add_error(f"工具 {i+1}: 参数必须是字典格式")
                continue
            
            # 检查变量名
            var_name = tool_call.get('var')
            if not var_name:
                result.add_warning(f"工具 {i+1}: 建议指定 var 名称")
            else:
                if var_name in used_vars:
                    result.add_error(f"工具 {i+1}: 变量名 '{var_name}' 重复")
                used_vars.add(var_name)
        
        return result
    
    # ==================== 表达式验证 ====================
    
    def validate_expression(
        self, 
        expression: str, 
        tools: List[Dict] = None
    ) -> ValidationResult:
        """
        验证表达式
        
        Args:
            expression: 表达式字符串
            tools: 工具调用列表（用于检查变量引用）
        
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        if not expression:
            result.add_error("表达式不能为空")
            return result
        
        # 1. 提取表达式中的所有标识符
        identifiers = self._extract_identifiers(expression)
        
        # 2. 获取可用的变量名（来自工具）
        available_vars = set()
        if tools:
            available_vars = {t.get('var', f'temp_{i}') 
                             for i, t in enumerate(tools, 1)}
        
        # 3. 检查每个标识符
        for ident in identifiers:
            # 跳过 Python 关键字和内置函数
            if self._is_python_keyword(ident):
                continue
            
            # 检查是否是字段名
            if ident in self.ALLOWED_FIELDS:
                continue
            
            # 检查是否是工具计算的变量
            if ident in available_vars:
                continue
            
            # 检查是否是数学函数
            if self._is_math_function(ident):
                continue
            
            # 无法识别，可能是无效标识符
            result.add_warning(
                f"表达式中包含未定义的标识符：'{ident}'\n"
                f"请确认这是有效的字段名或工具变量"
            )
        
        # 4. 检查除零风险
        if self._has_division_risk(expression):
            result.add_suggestion(
                "检测到除法运算，建议添加安全常数避免除零错误\n"
                "例如：x / (y + 0.0001)"
            )
        
        # 5. 检查表达式复杂度
        complexity = self._calculate_expression_complexity(expression)
        if complexity > 10:
            result.add_warning(
                f"表达式过于复杂（复杂度：{complexity}）\n"
                "建议简化表达式或拆分为多个工具步骤"
            )
        
        return result
    
    # ==================== 因子名称验证 ====================
    
    def validate_factor_name(self, name: str) -> ValidationResult:
        """
        验证因子名称
        
        Args:
            name: 因子名称
        
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        if not name:
            result.add_error("因子名称不能为空")
            return result
        
        if len(name) < 2:
            result.add_warning("因子名称过短，建议更具描述性")
        
        if len(name) > 50:
            result.add_warning("因子名称过长，建议简化")
        
        # 检查是否包含特殊字符
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$', name):
            result.add_warning(
                "因子名称包含特殊字符，建议使用中文、英文、数字、下划线或连字符"
            )
        
        return result
    
    # ==================== 逻辑说明验证 ====================
    
    def validate_rationale(self, rationale: str) -> ValidationResult:
        """
        验证因子构建逻辑说明
        
        Args:
            rationale: 逻辑说明文本
        
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        if len(rationale) < 10:
            result.add_warning("因子说明过短，建议提供更详细的构建逻辑")
        
        # 检查是否包含关键词
        keywords = ['因子', '计算', '构建', '逻辑', '原理', '基于']
        has_keyword = any(kw in rationale for kw in keywords)
        
        if not has_keyword:
            result.add_suggestion(
                "建议明确说明因子的构建逻辑和经济意义"
            )
        
        return result
    
    # ==================== 辅助方法 ====================
    
    def _extract_identifiers(self, expression: str) -> Set[str]:
        """
        从表达式中提取所有标识符
        
        Args:
            expression: 表达式字符串
        
        Returns:
            标识符集合
        """
        # 匹配标识符（变量名、字段名、函数名）
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, expression)
        return set(matches)
    
    def _is_python_keyword(self, ident: str) -> bool:
        """检查是否是 Python 关键字"""
        import keyword
        return keyword.iskeyword(ident) or ident in {
            'np', 'pd', 'True', 'False', 'None',
            'abs', 'log', 'sqrt', 'max', 'min', 'sign'
        }
    
    def _is_math_function(self, ident: str) -> bool:
        """检查是否是数学函数"""
        math_funcs = {
            'rolling_mean', 'rolling_std', 'rolling_max', 'rolling_min',
            'rsi', 'macd', 'kdj', 'atr', 'obv',
            'zscore', 'rank', 'correlation',
            'pct_change', 'lag', 'delta',
            'ts_rank', 'ts_argmax', 'ts_argmin',
            'decay_linear', 'bollinger_position',
            'volatility', 'max_drawdown',
            'max_of', 'min_of', 'clip'
        }
        return ident in math_funcs
    
    def _has_division_risk(self, expression: str) -> bool:
        """检查是否有除零风险"""
        # 简单的启发式检查：查找除法运算符
        division_pattern = r'/\s*([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(division_pattern, expression)
        
        for match in matches:
            # 如果除数不是明显的常数
            if not match.replace('_', '').isdigit():
                return True
        
        return False
    
    def _calculate_expression_complexity(self, expression: str) -> int:
        """
        计算表达式复杂度
        
        基于运算符数量、嵌套深度等
        """
        operators = ['+', '-', '*', '/', '(', ')', '**', '//']
        complexity = sum(expression.count(op) for op in operators)
        return complexity


# ==================== 便捷函数 ====================

def validate_factor(
    factor_def: Dict[str, Any], 
    skill_content: str, 
    available_tools: List[Dict]
) -> ValidationResult:
    """
    验证因子的便捷函数
    
    Args:
        factor_def: 因子定义
        skill_content: SKILL.md 内容
        available_tools: 可用工具列表
    
    Returns:
        验证结果
    """
    validator = SkillValidator(skill_content, available_tools)
    return validator.validate_factor_definition(factor_def)
