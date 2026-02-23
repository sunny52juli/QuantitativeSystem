import json
from typing import Dict, List, Optional
from config import tool_categories, strategy_keywords
from config import StockQueryConfig
api_config = StockQueryConfig.get_api_config()


class ToolsSelector:
    """
    工具选择器类 - 封装智能工具选择和分类功能
    支持两种选择模式：
    1. LLM Agent 语义匹配（主要）
    2. 关键词匹配（辅助兜底）
    两者结果取并集，确保工具覆盖面最大化。
    """

    def __init__(self, strategy: str = None, llm_client=None):
        """
        初始化工具选择器

        Args:
            strategy: 策略描述文本，用于智能工具选择
            llm_client: LLM客户端实例（OpenAI兼容），
                        若不传则使用config中的配置自动创建。
        """
        self.strategy = strategy
        self.llm_client = llm_client
        self.all_tools: List[Dict] = []
        self._load_tools()

    # ==================== 公开接口 ====================

    def select_relevant_tools(self) -> List[Dict]:
        """根据策略智能选择相关工具（Agent + 关键词取并集）

        Returns:
            筛选后的相关工具列表

        Raises:
            ValueError: 未设置策略或未匹配到任何工具
        """
        if not self.strategy:
            raise ValueError("❌ 未提供策略描述，无法智能选择工具")

        # 1. Agent智能匹配
        agent_selected = self._select_by_agent()

        # 2. 关键词匹配（辅助补充）
        keyword_selected = self._select_by_keywords()

        # 3. 取并集
        all_selected_names = set(agent_selected) | set(keyword_selected)

        # 4. 两种方式都没有匹配到任何工具时抛出错误
        if not all_selected_names:
            raise ValueError(
                f"❌ 未能匹配到任何相关工具。\n"
                f"   Agent匹配: {len(agent_selected)} 个\n"
                f"   关键词匹配: {len(keyword_selected)} 个\n"
                f"   策略: '{self.strategy}'"
            )

        # 5. 根据名称筛选出完整工具定义
        relevant_tools = [
            tool for tool in self.all_tools
            if tool["function"]["name"] in all_selected_names
        ]

        # 输出匹配报告
        self._print_match_report(agent_selected, keyword_selected, relevant_tools)

        return relevant_tools

    def get_tools_by_category(self, category: str) -> List[Dict]:
        """根据类别获取工具列表"""
        tools_in_category = tool_categories.get(category, [])
        return [
            tool for tool in self.all_tools
            if tool["function"]["name"] in tools_in_category
        ]

    def analyze_strategy(self) -> Dict[str, List[str]]:
        """分析策略中的关键词，返回相关类别和匹配到的关键词"""
        if not self.strategy:
            return {"categories": [], "keywords": []}

        strategy_lower = self.strategy.lower()
        relevant_categories = set()
        matched_keywords = []

        for keyword, categories in strategy_keywords.items():
            if keyword.lower() in strategy_lower:
                relevant_categories.update(categories)
                matched_keywords.append(keyword)

        return {
            "categories": list(relevant_categories),
            "keywords": matched_keywords,
        }

    def get_all_tools(self) -> List[Dict]:
        """获取所有可用工具"""
        return self.all_tools

    def reload_tools(self):
        """重新加载工具列表"""
        self._load_tools()

    def set_strategy(self, strategy: str):
        """设置策略描述"""
        self.strategy = strategy

    def set_llm_client(self, llm_client):
        """设置LLM客户端"""
        self.llm_client = llm_client

    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """获取指定工具的详细信息，未找到返回None"""
        for tool in self.all_tools:
            if tool["function"]["name"] == tool_name:
                return tool
        return None

    def get_tool_category(self, tool_name: str) -> Optional[str]:
        """获取工具所属类别，未找到返回None"""
        for category, tools_in_cat in tool_categories.items():
            if tool_name in tools_in_cat:
                return category
        return None

    def categorize_tools(self, tools: List[Dict] = None) -> Dict[str, List[Dict]]:
        """对工具列表按类别分组

        Args:
            tools: 要分类的工具列表，默认使用全部工具

        Returns:
            按类别分组的工具字典
        """
        if tools is None:
            tools = self.all_tools

        categorized: Dict[str, List[Dict]] = {
            cat: [] for cat in tool_categories
        }

        for tool in tools:
            tool_name = tool["function"]["name"]
            cat = self.get_tool_category(tool_name)
            if cat:
                categorized[cat].append(tool)
            else:
                categorized.setdefault("其他", []).append(tool)

        # 移除空类别
        return {cat: t for cat, t in categorized.items() if t}

    # ==================== 内部方法 ====================

    def _load_tools(self):
        """从 factor_tools_mcp 加载所有可用MCP工具定义"""
        try:
            from .factor_tools_mcp import TOOL_DEFINITIONS

            tools_list = []
            for tool_name, tool_spec in TOOL_DEFINITIONS.items():
                tools_list.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_spec["description"],
                        "parameters": tool_spec["inputSchema"],
                    },
                })

            self.all_tools = tools_list
            print(f"✅ 成功加载 {len(self.all_tools)} 个MCP工具")

        except ImportError as e:
            print(f"❌ 无法导入MCP工具: {e}")
            raise

    def _get_llm_client(self):
        """获取可用的LLM客户端和模型名称

        优先使用外部传入的 llm_client，否则用 config 配置自动创建。

        Returns:
            (client, model) 元组；创建失败时返回 (None, None)
        """
        model = api_config.get('model', 'gpt-4')

        if self.llm_client is not None:
            return self.llm_client, model

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_config.get('api_key'),
                base_url=api_config.get('base_url'),
            )
            return client, model
        except (ImportError, Exception) as e:
            print(f"   ⚠️ 无法创建默认LLM客户端: {e}")
            return None, None

    def _select_by_agent(self) -> List[str]:
        """使用LLM Agent智能匹配策略所需的工具

        Returns:
            Agent选出的工具名称列表，失败时返回空列表
        """
        client, model = self._get_llm_client()
        if client is None:
            print("   ⚠️ 无可用LLM客户端，跳过Agent工具匹配")
            return []

        # 构建提示词
        tool_summary = self._build_tool_summary()
        prompt = self._build_selection_prompt(tool_summary)

        try:
            print("   🤖 正在使用Agent智能匹配工具...")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是量化交易工具选择专家，请严格按JSON数组格式返回工具名称列表。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            result_text = response.choices[0].message.content.strip()
            selected_names = self._parse_agent_response(result_text)

            # 校验：只保留实际存在的工具名称
            valid_names = {t["function"]["name"] for t in self.all_tools}
            selected_names = [n for n in selected_names if n in valid_names]

            print(f"   🤖 Agent匹配到 {len(selected_names)} 个工具")
            return selected_names

        except json.JSONDecodeError as e:
            print(f"   ⚠️ Agent返回结果解析失败: {e}，将回退到关键词匹配")
            return []
        except Exception as e:
            print(f"   ⚠️ Agent工具匹配异常: {e}，将回退到关键词匹配")
            return []

    def _select_by_keywords(self) -> List[str]:
        """基于关键词匹配选择工具（辅助方式）

        Returns:
            关键词匹配到的工具名称列表
        """
        analysis = self.analyze_strategy()
        relevant_categories = set(analysis["categories"])

        if not relevant_categories:
            return []

        matched_names = []
        for tool in self.all_tools:
            tool_name = tool["function"]["name"]
            for category, tools_in_cat in tool_categories.items():
                if category in relevant_categories and tool_name in tools_in_cat:
                    matched_names.append(tool_name)
                    break

        print(
            f"   🔑 关键词匹配到 {len(matched_names)} 个工具，"
            f"相关类别: {', '.join(relevant_categories)}"
        )
        return matched_names

    def _build_tool_summary(self) -> str:
        """构建工具摘要文本，供LLM理解所有可用工具"""
        lines = []
        for i, tool in enumerate(self.all_tools, 1):
            name = tool["function"]["name"]
            desc = tool["function"].get("description", "无描述")
            category = self.get_tool_category(name) or "未分类"
            lines.append(f"{i}. [{category}] {name}: {desc}")
        return "\n".join(lines)

    def _build_selection_prompt(self, tool_summary: str) -> str:
        """构建用于LLM工具选择的提示词"""
        return (
            "你是一个量化交易工具选择专家。"
            "请根据用户的策略描述，从下方工具列表中选出所有可能用到的工具。\n\n"
            f"## 策略描述\n{self.strategy}\n\n"
            f"## 可用工具列表\n{tool_summary}\n\n"
            "## 选择要求\n"
            "1. 仔细理解策略的意图和所需的数据/计算/操作\n"
            "2. 选择所有「可能」用到的工具，宁可多选也不要遗漏\n"
            "3. 考虑策略实现的完整流程：数据获取 → 因子计算 → 信号生成 → 回测/执行\n"
            "4. 如果策略涉及某个领域（如技术分析、基本面分析），该领域的常用工具都应选入\n\n"
            "## 输出格式\n"
            '请严格以JSON数组格式返回选中的工具名称列表，不要包含任何其他文字：\n'
            '["tool_name_1", "tool_name_2", ...]'
        )

    @staticmethod
    def _parse_agent_response(result_text: str) -> List[str]:
        """解析Agent返回的JSON结果（兼容markdown代码块包裹）"""
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )
        return json.loads(result_text)

    @staticmethod
    def _print_match_report(
        agent_selected: List[str],
        keyword_selected: List[str],
        relevant_tools: List[Dict],
    ):
        """输出两种匹配方式的对比报告"""
        only_agent = set(agent_selected) - set(keyword_selected)
        only_keyword = set(keyword_selected) - set(agent_selected)
        both = set(agent_selected) & set(keyword_selected)

        total = len(relevant_tools)
        print(f"   🔍 工具选择结果: 共选中 {total} 个工具")
        if both:
            print(f"   ✅ 两种方式共同选中: {len(both)} 个")
        if only_agent:
            print(f"   🤖 仅Agent选中: {len(only_agent)} 个 -> {', '.join(only_agent)}")
        if only_keyword:
            print(f"   🔑 仅关键词选中: {len(only_keyword)} 个 -> {', '.join(only_keyword)}")


# ==================== 模块级便捷函数（向后兼容） ====================

def select_relevant_tools(
    strategy: str,
    all_tools: List[Dict],
    llm_client=None,
) -> List[Dict]:
    """根据策略描述智能选择相关工具（便捷函数，内部委托给 ToolsSelector）"""
    selector = ToolsSelector(strategy=strategy, llm_client=llm_client)
    selector.all_tools = all_tools  # 直接使用传入的工具列表，避免重复加载
    return selector.select_relevant_tools()


def load_mcp_tools() -> List[Dict]:
    """加载所有MCP工具定义（便捷函数）"""
    selector = ToolsSelector()
    return selector.get_all_tools()


def get_tool_category(tool_name: str) -> Optional[str]:
    """获取工具所属类别（便捷函数）"""
    for category, tools_in_cat in tool_categories.items():
        if tool_name in tools_in_cat:
            return category
    return None


def get_tools_by_category(category: str, all_tools: List[Dict]) -> List[Dict]:
    """根据类别获取工具列表（便捷函数）"""
    tools_in_category = tool_categories.get(category, [])
    return [
        tool for tool in all_tools
        if tool["function"]["name"] in tools_in_category
    ]


def analyze_strategy_keywords(strategy: str) -> Dict[str, List[str]]:
    """分析策略中的关键词（便捷函数）"""
    selector = ToolsSelector(strategy=strategy)
    return selector.analyze_strategy()


def categorize_tools(tools: List[Dict]) -> Dict[str, List[Dict]]:
    """对工具列表进行分类（便捷函数）"""
    selector = ToolsSelector()
    return selector.categorize_tools(tools)