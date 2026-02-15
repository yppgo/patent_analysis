# -*- coding: utf-8 -*-
"""
轻量图预览模块
从 DataFrame 的列表型字段自动构建图，跑标准图算法，
输出结构特征文本供 LLM 解读。

设计原则：
- 图构建和标准算法是通用的（不依赖领域），可以固定
- 图结构的语义解读交给 LLM
- 大图自动降级，跳过 O(n^2) 算法
"""

import re
import logging
from collections import Counter
from itertools import combinations
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
import networkx as nx

try:
    import community as community_louvain
except ImportError:
    community_louvain = None

logger = logging.getLogger(__name__)

# ─── 元素类型检测正则 ─────────────────────────────────────

# 专利编号：字母开头 + 数字为主体（如 CN120822531A, US2024001234A1, EP3456789B1）
_RE_PATENT_ID = re.compile(r'^[A-Z]{2}\d{4,}[A-Z]?\d*$', re.IGNORECASE)

# 分类码：含斜杠的固定格式（如 G06F21/60, H04L9/32）
_RE_CLASSIFICATION = re.compile(r'^[A-H]\d{2}[A-Z]\d+/\d+', re.IGNORECASE)

# 短分类码前缀（如 G06F, H04L）
_RE_CLASSIFICATION_SHORT = re.compile(r'^[A-H]\d{2}[A-Z]', re.IGNORECASE)

# 大图阈值：超过此节点数跳过社区检测和介数中心性
LARGE_GRAPH_THRESHOLD = 10000


class GraphPreview:
    """
    从 DataFrame 的列表型字段自动构建图，跑标准图算法，
    输出结构特征文本供 LLM 解读。
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.graphs: Dict[str, nx.Graph] = {}          # name → Graph
        self.graph_meta: Dict[str, Dict] = {}           # name → metadata
        self.analyses: Dict[str, Dict[str, Any]] = {}   # name → analysis results

    @classmethod
    def from_file(cls, file_path: str, sheet_name=None) -> 'GraphPreview':
        from pathlib import Path
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0)
        elif suffix == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
        return cls(df)

    # ─── 自动图构建 ──────────────────────────────────────────

    def build_all(self) -> 'GraphPreview':
        """自动扫描 DataFrame，根据列特征构建图。"""
        for col in self.df.columns:
            col_data = self.df[col].dropna().astype(str)
            # 过滤掉 '-' 和空值
            col_data = col_data[col_data != '-']
            col_data = col_data[col_data.str.len() > 0]

            if len(col_data) == 0:
                continue

            if not self._is_delimiter_column(col_data):
                continue

            items_per_row = col_data.str.split(r'\s*[|;]\s*')

            # 判断元素类型
            elem_type = self._classify_elements(items_per_row)

            if elem_type == 'patent_id':
                self._build_citation_graph(col, items_per_row)
            elif elem_type == 'classification':
                self._build_cooccurrence_graph(col, items_per_row, elem_type='classification')
            elif elem_type == 'name':
                self._build_cooccurrence_graph(col, items_per_row, elem_type='name')
            # else: 跳过无法识别类型的列

        return self

    def _is_delimiter_column(self, col_data: pd.Series) -> bool:
        """检测是否为分隔符列。"""
        sample = col_data.head(100)
        # 检查是否含 | 或 ; 分隔符
        has_delim = sample.str.contains(r'[|;]', regex=True, na=False)
        delim_ratio = has_delim.sum() / len(sample)

        if delim_ratio > 0.2:
            # 计算平均元素数
            avg_items = sample.str.split(r'\s*[|;]\s*').apply(len).mean()
            return avg_items > 1.3
        return False

    def _classify_elements(self, items_per_row: pd.Series) -> str:
        """
        通过采样判断列表元素的类型。
        返回: 'patent_id' | 'classification' | 'name' | 'unknown'
        """
        # 采样前 200 行的所有元素
        all_items = []
        for items in items_per_row.head(200):
            if isinstance(items, list):
                all_items.extend([s.strip() for s in items if s.strip()])
        if not all_items:
            return 'unknown'

        sample_items = all_items[:500]
        n = len(sample_items)

        # 统计匹配比例
        patent_count = sum(1 for s in sample_items if _RE_PATENT_ID.match(s))
        class_count = sum(1 for s in sample_items
                         if _RE_CLASSIFICATION.match(s) or _RE_CLASSIFICATION_SHORT.match(s))

        if patent_count / n > 0.5:
            return 'patent_id'
        if class_count / n > 0.5:
            return 'classification'

        # 人名启发式：短文本、无斜杠、无长数字串
        avg_len = np.mean([len(s) for s in sample_items])
        has_slash = sum(1 for s in sample_items if '/' in s)
        if avg_len < 40 and has_slash / n < 0.1:
            return 'name'

        return 'unknown'

    def _build_cooccurrence_graph(
        self, col: str, items_per_row: pd.Series, elem_type: str = 'unknown'
    ):
        """构建无向共现/合作图。"""
        G = nx.Graph()
        edge_counter = Counter()

        for items in items_per_row:
            if not isinstance(items, list):
                continue
            cleaned = [s.strip() for s in items if s.strip()]
            if len(cleaned) < 2:
                # 单个元素只加节点不加边
                for item in cleaned:
                    G.add_node(item)
                continue
            # 限制每行最多取前 50 个元素，避免超长列表导致组合爆炸
            cleaned = cleaned[:50]
            for a, b in combinations(cleaned, 2):
                edge_counter[(a, b)] += 1

        for (a, b), w in edge_counter.items():
            G.add_edge(a, b, weight=w)

        if G.number_of_nodes() > 0:
            type_label = {
                'classification': '共现网络',
                'name': '合作网络',
            }.get(elem_type, '共现网络')
            name = f"{col} {type_label}"
            self.graphs[name] = G
            self.graph_meta[name] = {
                'source_column': col,
                'elem_type': elem_type,
                'graph_type': 'cooccurrence',
            }
            logger.info(f"构建 {name}: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")

    def _build_citation_graph(self, col: str, items_per_row: pd.Series):
        """
        构建引用网络。
        统计数据集内专利之间的互引关系（内部引用）和总引用统计。
        """
        # 收集数据集内的所有专利编号
        id_col_candidates = []
        for c in self.df.columns:
            if '公开' in c or '公告' in c or ('号' in c and '数量' not in c and 'IPC' not in c):
                id_col_candidates.append(c)

        internal_ids = set()
        if id_col_candidates:
            for c in id_col_candidates[:1]:  # 取第一个
                internal_ids = set(self.df[c].dropna().astype(str).str.strip())

        # 统计引用关系
        total_refs = 0
        internal_edges = Counter()  # (source_patent, cited_patent) → count
        cited_counter = Counter()   # 被引用次数统计

        # 获取专利ID列用于关联
        patent_id_col = id_col_candidates[0] if id_col_candidates else None

        for idx, items in items_per_row.items():
            if not isinstance(items, list):
                continue
            cleaned = [s.strip() for s in items if s.strip()]
            total_refs += len(cleaned)

            source_id = None
            if patent_id_col is not None:
                source_id = str(self.df.at[idx, patent_id_col]).strip() if idx in self.df.index else None

            for ref in cleaned:
                if ref in internal_ids:
                    cited_counter[ref] += 1
                    if source_id:
                        internal_edges[(source_id, ref)] += 1

        # 构建有向图（仅内部互引）
        G = nx.DiGraph()
        for (s, t), w in internal_edges.items():
            G.add_edge(s, t, weight=w)

        name = f"{col} 引用网络"
        self.graphs[name] = G
        self.graph_meta[name] = {
            'source_column': col,
            'elem_type': 'patent_id',
            'graph_type': 'citation',
            'total_refs': total_refs,
            'internal_edges': G.number_of_edges(),
            'external_refs': total_refs - sum(cited_counter.values()),
            'top_cited': cited_counter.most_common(10),
        }
        logger.info(f"构建 {name}: {G.number_of_nodes()} 节点, {G.number_of_edges()} 内部边, {total_refs} 总引用")

    # ─── 图分析 ──────────────────────────────────────────────

    def analyze_all(self) -> Dict[str, Any]:
        """对所有已构建的图跑标准算法。"""
        for name, G in self.graphs.items():
            meta = self.graph_meta.get(name, {})
            if meta.get('graph_type') == 'citation':
                self.analyses[name] = self._analyze_citation_graph(name, G, meta)
            else:
                self.analyses[name] = self._analyze_undirected_graph(name, G)
        return self.analyses

    def _analyze_undirected_graph(self, name: str, G: nx.Graph) -> Dict[str, Any]:
        """分析无向图（共现/合作网络）。"""
        stats: Dict[str, Any] = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(nx.density(G), 6),
        }

        # 连通分量
        if isinstance(G, nx.Graph) and not isinstance(G, nx.DiGraph):
            components = list(nx.connected_components(G))
            stats["connected_components"] = len(components)
            if components:
                largest = max(components, key=len)
                stats["largest_component_size"] = len(largest)

        # 度分布
        degrees = [d for _, d in G.degree()]
        if degrees:
            stats["degree_stats"] = {
                "mean": round(np.mean(degrees), 1),
                "median": int(np.median(degrees)),
                "max": max(degrees),
            }
            # Top 10 高度节点
            top_degree = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
            stats["top_degree_nodes"] = [
                {"node": str(n), "degree": d} for n, d in top_degree
            ]

        # 社区检测和介数中心性（仅小图）
        if G.number_of_nodes() <= LARGE_GRAPH_THRESHOLD and community_louvain is not None:
            try:
                communities = community_louvain.best_partition(G, random_state=42)
                community_sizes = Counter(communities.values())
                stats["communities"] = {
                    "count": len(community_sizes),
                    "sizes": dict(community_sizes.most_common(10)),
                    "representatives": self._get_community_representatives(G, communities, top_n=3),
                }
            except Exception as e:
                logger.warning(f"社区检测失败 ({name}): {e}")

            try:
                k = min(500, G.number_of_nodes())
                betweenness = nx.betweenness_centrality(G, k=k)
                top_bc = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
                stats["bridges"] = [
                    {"node": str(n), "centrality": round(c, 4)} for n, c in top_bc if c > 0
                ]
            except Exception as e:
                logger.warning(f"介数中心性计算失败 ({name}): {e}")

        elif G.number_of_nodes() > LARGE_GRAPH_THRESHOLD:
            stats["note"] = f"节点数 {G.number_of_nodes()} 超过 {LARGE_GRAPH_THRESHOLD}，跳过社区检测和介数中心性"

        return stats

    def _analyze_citation_graph(self, name: str, G: nx.DiGraph, meta: Dict) -> Dict[str, Any]:
        """分析引用网络（有向图）。"""
        stats: Dict[str, Any] = {
            "node_count": G.number_of_nodes(),
            "internal_edges": G.number_of_edges(),
            "total_refs": meta.get('total_refs', 0),
            "external_refs": meta.get('external_refs', 0),
        }

        # 高被引节点
        top_cited = meta.get('top_cited', [])
        if top_cited:
            stats["top_cited"] = [
                {"patent": str(p), "cited_count": c} for p, c in top_cited
            ]

        # 入度分布（被引用次数）
        if G.number_of_nodes() > 0:
            in_degrees = [d for _, d in G.in_degree()]
            if in_degrees:
                stats["in_degree_stats"] = {
                    "mean": round(np.mean(in_degrees), 2),
                    "max": max(in_degrees),
                    "gt0": sum(1 for d in in_degrees if d > 0),
                }

        return stats

    def _get_community_representatives(
        self, G: nx.Graph, communities: Dict, top_n: int = 3
    ) -> Dict[int, List[str]]:
        """获取每个社区中度最高的代表节点。"""
        comm_nodes: Dict[int, List] = {}
        for node, comm_id in communities.items():
            comm_nodes.setdefault(comm_id, []).append(node)

        representatives = {}
        # 只取最大的 10 个社区
        sorted_comms = sorted(comm_nodes.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for comm_id, nodes in sorted_comms:
            node_degrees = [(n, G.degree(n)) for n in nodes]
            node_degrees.sort(key=lambda x: x[1], reverse=True)
            representatives[comm_id] = [str(n) for n, _ in node_degrees[:top_n]]

        return representatives

    # ─── 输出 ────────────────────────────────────────────────

    def to_prompt_string(self) -> str:
        """
        生成结构特征文本，只输出数字和节点名，不做语义解读。
        """
        if not self.analyses:
            self.analyze_all()

        lines = ["**图结构分析结果**", ""]

        for i, (name, stats) in enumerate(self.analyses.items(), 1):
            meta = self.graph_meta.get(name, {})
            graph_type = meta.get('graph_type', 'unknown')

            # 跳过空图（无节点或无边的引用网络）
            if graph_type == 'citation' and stats.get('internal_edges', 0) == 0 and stats.get('node_count', 0) == 0:
                continue
            if graph_type != 'citation' and stats.get('node_count', 0) < 3:
                continue

            lines.append(f"--- 图{i}: {name} ---")

            if graph_type == 'citation':
                lines.append(
                    f"- 数据集内互引节点: {stats['node_count']} | "
                    f"内部引用边: {stats['internal_edges']} | "
                    f"总引用数: {stats['total_refs']} | "
                    f"外部引用: {stats['external_refs']}"
                )
                top_cited = stats.get('top_cited', [])
                if top_cited:
                    lines.append(f"- 数据集内高被引 Top {len(top_cited)}:")
                    for j, item in enumerate(top_cited[:5], 1):
                        lines.append(f"  {j}. {item['patent']} (被引 {item['cited_count']} 次)")
                in_deg = stats.get('in_degree_stats')
                if in_deg:
                    lines.append(
                        f"- 入度统计: 均值 {in_deg['mean']}, "
                        f"最大 {in_deg['max']}, "
                        f"被引>0的节点: {in_deg['gt0']}"
                    )
            else:
                # 无向图
                lines.append(
                    f"- 节点: {stats['node_count']} | "
                    f"边: {stats['edge_count']} | "
                    f"密度: {stats['density']}"
                )
                cc = stats.get('connected_components')
                if cc is not None:
                    lcs = stats.get('largest_component_size', '?')
                    lines.append(f"- 连通分量: {cc} 个（最大分量含 {lcs} 节点）")

                deg = stats.get('degree_stats')
                if deg:
                    lines.append(
                        f"- 度分布: 均值 {deg['mean']}, "
                        f"中位数 {deg['median']}, "
                        f"最大 {deg['max']}"
                    )

                comms = stats.get('communities')
                if comms:
                    lines.append(f"- 社区: 检测到 {comms['count']} 个社区")
                    reps = comms.get('representatives', {})
                    sizes = comms.get('sizes', {})
                    for comm_id, rep_nodes in list(reps.items())[:8]:
                        size = sizes.get(comm_id, '?')
                        rep_str = " / ".join(rep_nodes)
                        lines.append(f"  社区{comm_id} ({size}个节点): 代表 {rep_str}")

                bridges = stats.get('bridges', [])
                if bridges:
                    lines.append(f"- 桥梁节点 (介数中心性 Top {min(5, len(bridges))}):")
                    for j, b in enumerate(bridges[:5], 1):
                        lines.append(f"  {j}. {b['node']} ({b['centrality']})")

                top_deg = stats.get('top_degree_nodes', [])
                if top_deg and not comms:
                    # 没有社区信息时显示 Top 度节点
                    lines.append(f"- 高连接度节点 Top {min(5, len(top_deg))}:")
                    for j, item in enumerate(top_deg[:5], 1):
                        lines.append(f"  {j}. {item['node']} (度 {item['degree']})")

                note = stats.get('note')
                if note:
                    lines.append(f"- 注: {note}")

            lines.append("")

        return "\n".join(lines)
