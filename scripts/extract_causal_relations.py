#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因果关系抽取器 - 从专利分析论文中提取因果假设
用于构建和完善因果知识图谱

功能：
1. 从50篇论文的分析结果中提取因果关系
2. 统计变量出现频次
3. 统计因果路径的验证情况
4. 生成完善后的因果图谱
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()


class CausalRelationExtractor:
    """从论文分析结果中抽取因果关系"""
    
    def __init__(self, llm_client=None):
        """
        初始化抽取器
        
        Args:
            llm_client: LLM客户端（用于深度分析）
        """
        self.llm = llm_client
        
        # 变量映射表：将论文中的具体指标映射到抽象变量
        self.variable_mapping = {
            # 输入变量
            "专利数量": "tech_intensity",
            "patent count": "tech_intensity",
            "申请人规模": "firm_size",
            "企业规模": "firm_size",
            "研发投入": "rd_investment",
            "R&D": "rd_investment",
            "国际合作": "international_collab",
            "international collaboration": "international_collab",
            "产学研": "university_collab",
            "university": "university_collab",
            
            # 中介变量
            "IPC熵": "tech_diversity",
            "技术多样性": "tech_diversity",
            "技术跨界": "tech_diversity",
            "diversity": "tech_diversity",
            "NPL": "science_linkage",
            "科学引用": "science_linkage",
            "science linkage": "science_linkage",
            "TCT": "tech_cycle_time",
            "技术周期": "tech_cycle_time",
            "cycle time": "tech_cycle_time",
            
            # 结果变量
            "引用": "tech_impact",
            "citation": "tech_impact",
            "被引": "tech_impact",
            "影响力": "tech_impact",
            "impact": "tech_impact",
            "专利价值": "commercial_value",
            "patent value": "commercial_value",
            "维持年限": "commercial_value",
        }
        
        # 变量定义
        self.variable_definitions = {
            "tech_intensity": {"label": "技术投入强度", "category": "input"},
            "firm_size": {"label": "企业规模", "category": "input"},
            "rd_investment": {"label": "研发投资", "category": "input"},
            "international_collab": {"label": "国际合作", "category": "input"},
            "university_collab": {"label": "产学研合作", "category": "input"},
            "tech_diversity": {"label": "技术跨界度", "category": "mediator"},
            "science_linkage": {"label": "科学关联度", "category": "mediator"},
            "tech_cycle_time": {"label": "技术迭代速度", "category": "mediator"},
            "tech_impact": {"label": "技术影响力", "category": "outcome"},
            "commercial_value": {"label": "商业价值", "category": "outcome"},
        }
        
        # 统计数据
        self.variable_counts = defaultdict(int)
        self.path_counts = defaultdict(lambda: {"count": 0, "papers": [], "domains": set()})
        self.domain_counts = defaultdict(int)
    
    def extract_from_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        从文件夹中的所有论文分析结果中抽取因果关系
        
        Args:
            folder_path: 包含分析结果JSON的文件夹
            
        Returns:
            抽取结果统计
        """
        folder = Path(folder_path)
        json_files = list(folder.glob("*_analysis_result.json"))
        
        print(f"找到 {len(json_files)} 个分析结果文件")
        print("=" * 60)
        
        for idx, json_file in enumerate(json_files, 1):
            try:
                print(f"[{idx}/{len(json_files)}] 处理: {json_file.name[:50]}...")
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._extract_from_paper(data)
                
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
        
        return self._generate_statistics()
    
    def _extract_from_paper(self, paper_data: Dict) -> None:
        """从单篇论文中抽取信息"""
        
        paper_title = paper_data.get("paper_meta", {}).get("title", "Unknown")
        
        # 提取研究领域
        domain = self._extract_domain(paper_data)
        if domain:
            self.domain_counts[domain] += 1
        
        # 提取分析步骤中的变量
        for step in paper_data.get("analysis_logic_chains", []):
            self._extract_variables_from_step(step, paper_title, domain)
    
    def _extract_domain(self, paper_data: Dict) -> str:
        """从论文数据中提取研究领域"""
        
        # 尝试从数据集配置中提取
        dataset_config = paper_data.get("dataset_config", {})
        dataset_name = dataset_config.get("name", "")
        query_condition = dataset_config.get("query_condition", "")
        
        # 简单的领域识别规则
        text = f"{dataset_name} {query_condition}".lower()
        
        if any(kw in text for kw in ["clean", "green", "energy", "solar", "wind"]):
            return "Clean Energy"
        elif any(kw in text for kw in ["bio", "pharma", "medical", "health"]):
            return "Biotech"
        elif any(kw in text for kw in ["ict", "telecom", "5g", "iot", "ai", "machine learning"]):
            return "ICT"
        elif any(kw in text for kw in ["material", "nano"]):
            return "Materials"
        elif any(kw in text for kw in ["automotive", "vehicle", "car"]):
            return "Automotive"
        else:
            return "General"
    
    def _extract_variables_from_step(self, step: Dict, paper_title: str, domain: str) -> None:
        """从分析步骤中提取变量"""
        
        method_name = step.get("method_name", "")
        objective = step.get("objective", "")
        inputs = step.get("inputs", [])
        metrics = step.get("evaluation_metrics", [])
        
        # 合并所有文本用于变量识别
        all_text = f"{method_name} {objective} {' '.join(inputs)}"
        
        # 识别变量
        found_variables = []
        for keyword, var_id in self.variable_mapping.items():
            if keyword.lower() in all_text.lower():
                found_variables.append(var_id)
                self.variable_counts[var_id] += 1
        
        # 如果找到多个变量，尝试推断因果关系
        if len(found_variables) >= 2:
            # 简单规则：假设第一个是自变量，最后一个是因变量
            # 这是一个简化的启发式规则
            for i, var1 in enumerate(found_variables[:-1]):
                for var2 in found_variables[i+1:]:
                    # 检查变量类别，确保方向合理
                    cat1 = self.variable_definitions.get(var1, {}).get("category", "")
                    cat2 = self.variable_definitions.get(var2, {}).get("category", "")
                    
                    # 只记录合理的因果方向
                    if self._is_valid_causal_direction(cat1, cat2):
                        path_key = f"{var1} -> {var2}"
                        self.path_counts[path_key]["count"] += 1
                        self.path_counts[path_key]["papers"].append(paper_title)
                        if domain:
                            self.path_counts[path_key]["domains"].add(domain)
    
    def _is_valid_causal_direction(self, cat1: str, cat2: str) -> bool:
        """检查因果方向是否合理"""
        
        # 定义合理的因果方向
        valid_directions = {
            ("input", "mediator"),
            ("input", "outcome"),
            ("mediator", "outcome"),
            ("mediator", "mediator"),
        }
        
        return (cat1, cat2) in valid_directions
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """生成统计结果"""
        
        return {
            "variable_counts": dict(self.variable_counts),
            "path_counts": {
                k: {
                    "count": v["count"],
                    "papers": v["papers"][:5],  # 只保留前5篇
                    "domains": list(v["domains"])
                }
                for k, v in sorted(
                    self.path_counts.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )
            },
            "domain_counts": dict(self.domain_counts),
            "total_papers": sum(self.domain_counts.values())
        }
    
    def generate_ontology(self, output_path: str = None) -> Dict[str, Any]:
        """
        基于抽取结果生成因果本体论
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            生成的本体论
        """
        
        # 构建变量列表
        variables = []
        for var_id, count in sorted(self.variable_counts.items(), key=lambda x: x[1], reverse=True):
            var_def = self.variable_definitions.get(var_id, {})
            variables.append({
                "id": var_id,
                "label": var_def.get("label", var_id),
                "category": var_def.get("category", "unknown"),
                "evidence_count": count,
                "source": "extracted_from_papers"
            })
        
        # 构建因果路径列表
        causal_paths = []
        for path_key, path_data in self.path_counts.items():
            source, target = path_key.split(" -> ")
            causal_paths.append({
                "path_id": f"P_{len(causal_paths)+1:02d}",
                "source": source,
                "target": target,
                "evidence": {
                    "validated": path_data["count"] >= 3,  # 3篇以上视为已验证
                    "evidence_count": path_data["count"],
                    "sample_papers": path_data["papers"][:3],
                    "validated_domains": list(path_data["domains"])  # set转list
                },
                "source": "extracted_from_papers"
            })
        
        ontology = {
            "meta": {
                "name": "Extracted Causal Ontology",
                "version": "1.0",
                "description": "从50篇专利分析论文中自动抽取的因果关系",
                "extraction_method": "rule_based + keyword_matching",
                "total_papers_analyzed": sum(self.domain_counts.values())
            },
            "variables": variables,
            "causal_paths": causal_paths,
            "statistics": {
                "total_variables": len(variables),
                "total_paths": len(causal_paths),
                "validated_paths": sum(1 for p in causal_paths if p["evidence"]["validated"]),
                "domain_coverage": dict(self.domain_counts)
            }
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(ontology, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 本体论已保存到: {output_path}")
        
        return ontology


def extract_with_llm(paper_data: Dict, llm_client) -> Dict[str, Any]:
    """
    使用LLM深度抽取因果关系（更准确但更慢）
    
    Args:
        paper_data: 论文分析结果
        llm_client: LLM客户端
        
    Returns:
        抽取的因果关系
    """
    
    prompt = f"""
# 任务
从以下专利分析论文的分析结果中，提取研究假设和因果关系。

# 论文信息
标题: {paper_data.get('paper_meta', {}).get('title', 'Unknown')}

# 分析步骤
{json.dumps(paper_data.get('analysis_logic_chains', []), ensure_ascii=False, indent=2)}

# 要求
1. 识别论文中隐含的研究假设（如果有）
2. 识别自变量和因变量
3. 判断因果效应的方向（正向/负向）
4. 识别研究的技术领域

# 输出格式（严格JSON）
{{
  "domain": "技术领域（如 ICT, Biotech, Clean Energy）",
  "hypotheses": [
    {{
      "independent_var": "自变量名称",
      "dependent_var": "因变量名称",
      "effect_direction": "positive/negative/unknown",
      "confidence": 0.8,
      "evidence": "从论文中提取的证据"
    }}
  ]
}}

只输出JSON，不要其他内容。
"""
    
    try:
        response = llm_client.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # 清理响应
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"LLM抽取失败: {e}")
        return None


def main():
    """主函数"""
    
    print("=" * 60)
    print("因果关系抽取器 - 从专利分析论文中提取因果假设")
    print("=" * 60)
    
    # 创建抽取器
    extractor = CausalRelationExtractor()
    
    # 从batch_50_results文件夹抽取
    folder_path = "batch_50_results"
    
    if not Path(folder_path).exists():
        print(f"错误: 文件夹不存在 - {folder_path}")
        return
    
    # 执行抽取
    stats = extractor.extract_from_folder(folder_path)
    
    # 打印统计结果
    print("\n" + "=" * 60)
    print("抽取结果统计")
    print("=" * 60)
    
    print(f"\n📊 分析论文数: {stats['total_papers']}")
    
    print(f"\n📋 变量出现频次:")
    for var_id, count in sorted(stats['variable_counts'].items(), key=lambda x: x[1], reverse=True):
        var_def = extractor.variable_definitions.get(var_id, {})
        print(f"  - {var_def.get('label', var_id)}: {count}次")
    
    print(f"\n🔗 因果路径统计 (Top 10):")
    for i, (path, data) in enumerate(list(stats['path_counts'].items())[:10], 1):
        validated = "✓" if data['count'] >= 3 else "?"
        print(f"  {i}. [{validated}] {path}: {data['count']}篇论文")
        print(f"      领域: {', '.join(data['domains']) if data['domains'] else '未知'}")
    
    print(f"\n🌍 领域分布:")
    for domain, count in sorted(stats['domain_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {domain}: {count}篇")
    
    # 生成本体论
    output_path = "sandbox/static/data/extracted_causal_ontology.json"
    ontology = extractor.generate_ontology(output_path)
    
    print(f"\n✅ 抽取完成!")
    print(f"  - 变量数: {ontology['statistics']['total_variables']}")
    print(f"  - 路径数: {ontology['statistics']['total_paths']}")
    print(f"  - 已验证路径: {ontology['statistics']['validated_paths']}")


if __name__ == "__main__":
    main()
