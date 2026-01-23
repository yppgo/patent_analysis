"""
图谱模块
包含因果图谱和方法图谱的查询器
"""

from .causal_graph_query import CausalGraphQuery
from .method_graph_query import MethodGraphQuery

__all__ = ['CausalGraphQuery', 'MethodGraphQuery']
