"""
数据辅助工具

提供数据加载和列名提取功能
"""

import pandas as pd
from typing import List, Optional


def get_columns_from_file(
    file_path: str, 
    sheet_name: str = 'sheet1',
    nrows: int = 0
) -> List[str]:
    """
    从 Excel 文件读取列名
    
    Args:
        file_path: Excel 文件路径
        sheet_name: Sheet 名称
        nrows: 读取行数（0 表示只读取列名，不读取数据）
        
    Returns:
        列名列表
        
    Example:
        >>> columns = get_columns_from_file('data/patents.xlsx')
        >>> print(columns)
        ['序号', '名称', '摘要', '授权日']
    """
    try:
        # 只读取列名，不读取数据（nrows=0）
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=nrows)
        return list(df.columns)
    except Exception as e:
        raise ValueError(f"无法从文件读取列名: {e}")


def get_available_columns(
    file_path: Optional[str] = None,
    manual_columns: Optional[List[str]] = None,
    sheet_name: str = 'sheet1'
) -> Optional[List[str]]:
    """
    获取可用列名（智能选择）
    
    优先级：
    1. 如果提供了 file_path，从文件读取
    2. 如果提供了 manual_columns，使用手动指定的列名
    3. 否则返回 None
    
    Args:
        file_path: Excel 文件路径（可选）
        manual_columns: 手动指定的列名（可选）
        sheet_name: Sheet 名称
        
    Returns:
        列名列表，如果都未提供则返回 None
        
    Example:
        # 方式 1: 从文件读取
        >>> columns = get_available_columns(file_path='data/patents.xlsx')
        
        # 方式 2: 手动指定
        >>> columns = get_available_columns(manual_columns=['序号', '名称', '摘要'])
        
        # 方式 3: 不提供（Strategist 会使用默认假设）
        >>> columns = get_available_columns()
        >>> print(columns)  # None
    """
    # 优先从文件读取
    if file_path:
        try:
            return get_columns_from_file(file_path, sheet_name=sheet_name)
        except Exception as e:
            print(f"⚠️ 从文件读取列名失败: {e}")
            # 降级到手动指定
            if manual_columns:
                print(f"   使用手动指定的列名")
                return manual_columns
            return None
    
    # 使用手动指定
    if manual_columns:
        return manual_columns
    
    # 都未提供
    return None


# 常用数据集的列名预设
PRESET_COLUMNS = {
    'patents_standard': [
        '序号', '公开(公告)号', '公开(公告)日', '授权日', '申请日',
        '名称', '摘要', '申请(专利权)人', 'IPC分类号', '发明人'
    ],
    'patents_minimal': [
        '序号', '名称', '摘要', '申请(专利权)人', '授权日'
    ],
    'patents_with_topics': [
        '序号', '名称', '摘要', '申请(专利权)人', '授权日',
        'IPC分类号', 'topic_0', 'topic_1', 'topic_2'
    ]
}


def get_preset_columns(preset_name: str) -> List[str]:
    """
    获取预设的列名
    
    Args:
        preset_name: 预设名称（'patents_standard', 'patents_minimal', 'patents_with_topics'）
        
    Returns:
        列名列表
        
    Example:
        >>> columns = get_preset_columns('patents_minimal')
        >>> print(columns)
        ['序号', '名称', '摘要', '申请(专利权)人', '授权日']
    """
    if preset_name not in PRESET_COLUMNS:
        raise ValueError(f"未知的预设名称: {preset_name}。可用预设: {list(PRESET_COLUMNS.keys())}")
    
    return PRESET_COLUMNS[preset_name]
