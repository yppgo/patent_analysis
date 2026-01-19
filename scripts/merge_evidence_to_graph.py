#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将抽取的因果关系证据合并到知识图谱
- 匹配抽取结果到图谱的P01-P35路径
- 聚合多篇论文的证据
- 更新图谱的evidence字段
- 标记验证状态
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class EvidenceMerger:
    """证据合并器"""
    
    def __init__(self, graph_path: str, extraction_dir: str):
        """初始化"""
        self.graph_path = Path(graph_path)
        self.extraction_dir = Path(extraction_dir)
        
        # 加载图谱
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
        
        # 创建路径索引：(source, target) -> path_id
        self.path_index = {}
        for path in self.graph.get("causal_paths", []):
            source = path.get("source")
            target = path.get("target")
            if source and target:
                key = (source, target)
                self.path_index[key] = path
        
        print(f"✓ 加载图谱: {len(self.graph['variables'])} 个变量, {len(self.graph['causal_paths'])} 条路径")
    
    def load_extraction_results(self) -> List[Dict]:
        """加载所有抽取结果"""
        results = []
        
        # 读取聚合文件
        summary_file = self.extraction_dir / "extraction_summary_v2.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                results = summary.get("all_results", [])
        else:
            # 读取单个文件
            for json_file in self.extraction_dir.glob("*_v2.json"):
                if json_file.name == "extraction_summary_v2.json":
                    continue
                with open(json_file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
        
        print(f"✓ 加载抽取结果: {len(results)} 篇论文")
        return results
    
    def merge_evidence(self, extraction_results: List[Dict]) -> Dict[str, Any]:
        """合并证据到图谱"""
        
        # 统计每条路径的证据
        path_evidence = defaultdict(lambda: {
            "papers": [],
            "evidence_texts": [],
            "domains": set(),
            "effect_sizes": [],
            "mechanisms": []
        })
        
        # 遍历抽取结果
        for result in extraction_results:
            if not result.get("success"):
                continue
            
            paper_title = result.get("paper_title", "Unknown")
            paper_domain = result.get("paper_domain", "General")
            
            # 处理因果关系
            for rel in result.get("causal_relations", []):
                source = rel.get("source")
                target = rel.get("target")
                
                # 跳过unmapped变量
                if not source.startswith("V") or not target.startswith("V"):
                    continue
                
                # 查找对应的图谱路径
                key = (source, target)
                if key in self.path_index:
                    path_evidence[key]["papers"].append(paper_title)
                    path_evidence[key]["evidence_texts"].append(rel.get("evidence", ""))
                    path_evidence[key]["domains"].add(paper_domain)
                    path_evidence[key]["effect_sizes"].append(rel.get("effect_size", ""))
                    path_evidence[key]["mechanisms"].append(rel.get("mechanism", ""))
        
        # 更新图谱
        updated_count = 0
        new_paths = []
        
        for (source, target), evidence_data in path_evidence.items():
            if (source, target) in self.path_index:
                # 更新现有路径
                path = self.path_index[(source, target)]
                
                # 更新evidence字段
                evidence_count = len(evidence_data["papers"])
                path["evidence"]["evidence_count"] = evidence_count
                path["evidence"]["validated"] = evidence_count >= 3
                path["evidence"]["validated_domains"] = list(evidence_data["domains"])
                
                # 添加论文引用（简化版）
                path["evidence"]["extracted_papers"] = [
                    {
                        "title": paper[:80],
                        "evidence": evidence_data["evidence_texts"][i][:200]
                    }
                    for i, paper in enumerate(evidence_data["papers"][:5])  # 最多5篇
                ]
                
                updated_count += 1
            else:
                # 发现新路径（图谱中不存在）
                new_path = {
                    "path_id": f"P{len(self.graph['causal_paths']) + len(new_paths) + 1:02d}_NEW",
                    "source": source,
                    "target": target,
                    "effect_type": self._infer_effect_type(evidence_data["effect_sizes"]),
                    "effect_size": self._aggregate_effect_size(evidence_data["effect_sizes"]),
                    "mechanism": evidence_data["mechanisms"][0] if evidence_data["mechanisms"] else "",
                    "evidence": {
                        "validated": len(evidence_data["papers"]) >= 3,
                        "evidence_count": len(evidence_data["papers"]),
                        "key_papers": ["Extracted from literature"],
                        "validated_domains": list(evidence_data["domains"]),
                        "extracted_papers": [
                            {
                                "title": paper[:80],
                                "evidence": evidence_data["evidence_texts"][i][:200]
                            }
                            for i, paper in enumerate(evidence_data["papers"][:5])
                        ]
                    },
                    "hypothesis_template": f"H: {{query}}领域的{self._get_var_label(source)}对{self._get_var_label(target)}有影响"
                }
                new_paths.append(new_path)
        
        # 添加新路径到图谱
        if new_paths:
            self.graph["causal_paths"].extend(new_paths)
        
        # 更新统计信息
        self.graph["meta"]["last_updated"] = "2026-01-14"
        self.graph["meta"]["evidence_extraction_date"] = "2026-01-14"
        self.graph["path_statistics"]["updated_paths"] = updated_count
        self.graph["path_statistics"]["new_paths"] = len(new_paths)
        
        print(f"\n✓ 更新了 {updated_count} 条现有路径")
        print(f"✓ 发现了 {len(new_paths)} 条新路径")
        
        return self.graph
    
    def _infer_effect_type(self, effect_sizes: List[str]) -> str:
        """推断效应类型"""
        # 简化版：根据effect_size推断
        if not effect_sizes:
            return "positive"
        
        # 统计最常见的类型
        from collections import Counter
        counter = Counter(effect_sizes)
        return counter.most_common(1)[0][0] if counter else "positive"
    
    def _aggregate_effect_size(self, effect_sizes: List[str]) -> str:
        """聚合效应大小"""
        if not effect_sizes:
            return "medium"
        
        # 映射到数值
        size_map = {"small": 1, "medium": 2, "large": 3, "theoretical": 1.5}
        avg_size = sum(size_map.get(s, 2) for s in effect_sizes) / len(effect_sizes)
        
        if avg_size >= 2.5:
            return "large"
        elif avg_size >= 1.5:
            return "medium"
        else:
            return "small"
    
    def _get_var_label(self, var_id: str) -> str:
        """获取变量标签"""
        for var in self.graph.get("variables", []):
            if var["id"] == var_id:
                return var["label"]
        return var_id
    
    def save_updated_graph(self, output_path: str = None):
        """保存更新后的图谱"""
        if output_path is None:
            output_path = self.graph_path.parent / f"{self.graph_path.stem}_updated.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 更新后的图谱已保存到: {output_path}")
        return output_path


def main():
    """主函数"""
    print("=" * 60)
    print("证据合并器 - 将抽取结果填充到知识图谱")
    print("=" * 60)
    
    # 初始化
    merger = EvidenceMerger(
        graph_path="sandbox/static/data/complete_causal_ontology.json",
        extraction_dir="outputs/causal_extraction_v2"
    )
    
    # 加载抽取结果
    extraction_results = merger.load_extraction_results()
    
    # 合并证据
    print("\n开始合并证据...")
    updated_graph = merger.merge_evidence(extraction_results)
    
    # 保存
    merger.save_updated_graph()
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
