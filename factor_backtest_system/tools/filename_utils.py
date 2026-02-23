"""
文件名工具函数

提供文件名清理和类名转换等工具函数
"""


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        name: 原始名称
        
    Returns:
        清理后的名称
    """
    # 移除非法字符
    illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ', '（', '）', '(', ')']
    for char in illegal_chars:
        name = name.replace(char, '_')
    
    # 移除连续的下划线
    while '__' in name:
        name = name.replace('__', '_')
    
    # 移除首尾的下划线
    name = name.strip('_')
    
    return name


def to_class_name(name: str) -> str:
    """
    将因子名称转换为类名
    
    Args:
        name: 因子名称
        
    Returns:
        类名（驼峰命名）
    """
    # 清理名称
    clean_name = sanitize_filename(name)
    
    # 转换为驼峰命名
    parts = clean_name.split('_')
    class_name = ''.join(word.capitalize() for word in parts if word)
    
    # 确保以字母开头
    if class_name and not class_name[0].isalpha():
        class_name = 'Factor' + class_name
    
    return class_name + 'Calculator'
