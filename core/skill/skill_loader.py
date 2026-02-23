"""
技能文档加载模块 - 动态加载技能文档内容
"""

import os
from typing import Optional


def load_skill_content() -> str:
    """
    从SKILL.md文件加载技能文档内容
    
    Returns:
        技能文档内容字符串
    """
    try:
        # 使用绝对路径引用SKILL.md文件（从core/skill目录）
        import os
        current_dir = os.path.dirname(__file__)
        skill_path = os.path.join(current_dir, 'SKILL.md')
        
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("[INFO] SKILL.md loaded from core/skill/")
        return content
    except FileNotFoundError:
        raise FileNotFoundError("SKILL.md文件未找到，请检查路径: core/skill/SKILL.md")


def load_custom_skill(skill_path: str) -> Optional[str]:
    """
    加载自定义技能文档
    
    Args:
        skill_path: 技能文档文件路径
        
    Returns:
        技能文档内容，如果文件不存在返回None
    """
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[INFO] Custom skill loaded from: {skill_path}")
        return content
    except FileNotFoundError:
        print(f"[WARNING] Custom skill not found: {skill_path}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to load custom skill: {str(e)}")
        return None


def get_skill_summary(skill_content: str) -> dict:
    """
    获取技能文档摘要信息
    
    Args:
        skill_content: 技能文档内容
        
    Returns:
        包含摘要信息的字典
    """
    lines = skill_content.split('\n')
    summary = {
        "total_lines": len(lines),
        "total_chars": len(skill_content),
        "sections": [],
        "has_api_reference": "## API参考" in skill_content
    }
    
    # 提取章节标题
    for line in lines:
        if line.startswith('## '):
            section_title = line.replace('## ', '').strip()
            summary["sections"].append(section_title)
    
    return summary


def validate_skill_content(skill_content: str) -> bool:
    """
    验证技能文档内容是否有效
    
    Args:
        skill_content: 技能文档内容
        
    Returns:
        是否有效
    """
    if not skill_content:
        return False
    
    # 检查是否包含必要的关键词
    required_keywords = ["因子", "工具", "表达式"]
    content_lower = skill_content.lower()
    
    for keyword in required_keywords:
        if keyword not in content_lower:
            print(f"[WARNING] Skill content missing keyword: {keyword}")
            return False
    
    return True


class SkillLoader:
    """
    技能文档加载器类 - 封装技能文档加载功能
    """
    
    def __init__(self, skill_path: str = None):
        """
        初始化技能加载器
        
        Args:
            skill_path: 自定义技能文档路径，如果为None则使用默认路径
        """
        self.skill_path = skill_path
        self.content = None
        self._load_content()
    
    def _load_content(self):
        """加载技能文档内容"""
        if self.skill_path:
            self.content = load_custom_skill(self.skill_path)
        else:
            self.content = load_skill_content()
    
    def get_content(self) -> str:
        """获取技能文档内容"""
        return self.content or ""
    
    def get_summary(self) -> dict:
        """获取技能文档摘要"""
        return get_skill_summary(self.content) if self.content else {}
    
    def is_valid(self) -> bool:
        """验证技能文档是否有效"""
        return validate_skill_content(self.content) if self.content else False
    
    def reload(self):
        """重新加载技能文档"""
        self._load_content()


# 全局技能文档内容（模块加载时自动加载）
SKILL_CONTENT = load_skill_content()