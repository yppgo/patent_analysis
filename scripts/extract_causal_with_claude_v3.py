#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Claude API 直接读取 PDF 文献并抽取因果关系 - V3 并行版
- 支持并行处理（5线程）
- 自动构建因果图谱
- 聚合多篇论文的证据
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import anthropic
from dotenv import load_dotenv

load_dotenv()

# 线程安全的计数器
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value


class ClaudePDFExtractorV3:
    """使用 Claude 从 PDF 中抽取因果关系 - V3 并行版"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """初始化"""
        self.api_key = api_key or os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("JUHENEXT_BASE_URL") or "https://api.anthropic.com"
        
        if not self.api_key:
            raise ValueError("请提供 API Key")
        
        self.model = model or os.getenv("CLAUDE_MODEL") or "claude-sonnet-4-20250514"
        
        print(f"使用 API: {self.base_url}")
        print(f"使用模型: {self.model}")
        
        # 加载标准变量本体
        self.variable_ontology = self._load_ontology()
        
        # 线程安全的结果收集
        self.results_lock = threading.Lock()
        self.all_results = []
        self.counter = ThreadSafeCounter()
    
    def _get_client(self):
        """为每个线程创建独立的客户端"""
        return anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _load_ontology(self) -> Dict[str, Any]:
        """加载变量本体"""
        graph_path = "sandbox/static/data/causal_ontology_extracted.json"
        
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph = json.load(f)
            
            ontology = {}
            for var in graph.get("variables", []):
                var_id = var["id"]
                ontology[var_id] = {
                    "label": var["label"],
                    "category": var["category"],
                    "definition": var.get("definition", "")
                }
            
            print(f"✓ 加载了 {len(ontology)} 个变量")
            return ontology
            
        except Exception as e:
            print(f"警告: 加载本体失败 {e}")
            return {}
    
    def _build_extraction_prompt(self) -> str:
        """构建抽取提示词"""
        
        # 按类别组织变量
        var_by_category = defaultdict(list)
        for var_id, var_info in self.variable_ontology.items():
            category = var_info["category"]
            var_by_category[category].append(f"    - {var_id}: {var_info['label']}")
        
        variables_str = f"""
  【输入变量 Input】
{chr(10).join(var_by_category.get('input', []))}

  【中介变量 Mediator】
{chr(10).join(var_by_category.get('mediator', []))}

  【结果变量 Outcome】
{chr(10).join(var_by_category.get('outcome', []))}

  【调节变量 Moderator】
{chr(10).join(var_by_category.get('moderator', []))}
"""
        
        return f"""# 角色
你是专利计量学和因果推断专家，擅长从学术论文中识别因果关系。

# 任务
从这篇论文中抽取因果关系，特别关注：
1. **直接因果关系**：A → B
2. **中介效应**：A → M → B（M是中介变量）
3. **调节效应**：Z 调节 A → B 的强度
4. **非线性关系**：倒U型、阈值效应等

# 标准变量本体（必须使用这些ID）
{variables_str}

# 变量映射指南（重要！）
- "技术差距/技术水平/技术能力" → V16_tech_impact 或 V18_tech_independence
- "追赶能力/后发优势/catch-up" → V26_catching_up
- "先发优势/先动者优势/first-mover" → V06_prior_experience
- "技术成熟度/生命周期/maturity" → V22_tech_maturity
- "知识溢出/知识转移/spillover" → V29_knowledge_spillover
- "隐性知识/tacit knowledge" → V27_tacit_knowledge
- "技术融合/convergence" → V28_tech_convergence
- "技术新颖度/novelty" → V30_tech_novelty
- "创新绩效/创新产出/innovation output" → V16_tech_impact
- "专利质量/patent quality" → V16_tech_impact
- "技术多样性/diversification" → V09_tech_diversity
- "引用/citation" → V16_tech_impact
- "技术竞争力/competitiveness" → V16_tech_impact 或 V20_market_share
- 只有在完全无法映射时才使用 "unmapped_原始术语"

# 输出格式（严格JSON）

```json
{{
  "paper_title": "论文标题",
  "paper_domain": "Clean Energy/ICT/Biotech/Automotive/Materials/Pharma/General",
  "research_design": "empirical/theoretical/review",
  "causal_relations": [
    {{
      "source": "V01_tech_intensity",
      "target": "V16_tech_impact",
      "effect_type": "positive/negative/inverted_u/threshold",
      "effect_size": "large/medium/small/theoretical",
      "mechanism": "作用机制的简要描述",
      "evidence": "原文证据（关键句子）"
    }}
  ],
  "complex_relations": [
    {{
      "type": "mediation/moderation",
      "description": "中介或调节效应的描述",
      "path": "A → M → B 或 Z调节A→B",
      "evidence": "原文证据"
    }}
  ]
}}
```

# 注意事项
1. 只抽取论文中**明确提出或有数据支持**的关系
2. 变量ID必须使用V01-V25格式
3. 尽量映射到标准变量，减少unmapped
4. evidence字段引用原文，保持准确性
"""
    
    def _encode_pdf(self, pdf_path: str) -> str:
        """将 PDF 文件编码为 base64"""
        with open(pdf_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    def extract_from_pdf(self, pdf_path: str, total: int) -> Dict[str, Any]:
        """从单个 PDF 文件中抽取因果关系（线程安全）"""
        current = self.counter.increment()
        pdf_name = Path(pdf_path).name[:50]
        
        try:
            print(f"[{current}/{total}] 处理: {pdf_name}...")
            start_time = time.time()
            
            pdf_data = self._encode_pdf(pdf_path)
            
            # 每个线程创建独立的客户端
            client = self._get_client()
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": self._build_extraction_prompt()
                            }
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            result = self._parse_response(response_text, pdf_path)
            
            elapsed = time.time() - start_time
            rel_count = len(result.get("causal_relations", []))
            print(f"  ✓ [{current}/{total}] 成功: {rel_count}条关系 | {elapsed:.1f}秒")
            
            return result
            
        except Exception as e:
            print(f"  ✗ [{current}/{total}] 失败: {str(e)[:50]}")
            return {
                "success": False,
                "error": str(e),
                "paper_title": Path(pdf_path).stem
            }
    
    def _parse_response(self, response_text: str, pdf_path: str) -> Dict[str, Any]:
        """解析 Claude 的响应"""
        import re
        
        # 提取JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text.strip()
        
        # 解析JSON
        try:
            data = json.loads(json_str)
        except:
            # 尝试修复
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            try:
                data = json.loads(json_str)
            except:
                return {
                    "success": False,
                    "error": "JSON解析失败",
                    "paper_title": Path(pdf_path).stem
                }
        
        data["success"] = True
        data["file_path"] = str(pdf_path)
        return data
    
    def process_batch(self, pdf_files: List[str], max_workers: int = 5) -> List[Dict]:
        """并行处理多个PDF文件"""
        total = len(pdf_files)
        results = []
        
        print(f"\n开始并行处理 {total} 个文件 (线程数: {max_workers})")
        print("=" * 60)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_pdf = {
                executor.submit(self.extract_from_pdf, pdf, total): pdf 
                for pdf in pdf_files
            }
            
            # 收集结果
            for future in as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"  ✗ 异常: {Path(pdf).name[:30]} - {e}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "paper_title": Path(pdf).stem
                    })
        
        return results


def build_causal_graph(results: List[Dict], output_path: str):
    """从抽取结果构建因果图谱"""
    
    # 加载模板
    template_path = "sandbox/static/data/causal_ontology_extracted.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    
    # 统计
    path_evidence = defaultdict(lambda: {
        "papers": [],
        "evidence_texts": [],
        "domains": set(),
        "effect_types": [],
        "effect_sizes": [],
        "mechanisms": []
    })
    
    complex_relations = {
        "mediation_effects": [],
        "moderation_effects": []
    }
    
    success_count = 0
    total_relations = 0
    
    for result in results:
        if not result.get("success"):
            continue
        
        success_count += 1
        paper_title = result.get("paper_title", "Unknown")
        paper_domain = result.get("paper_domain", "General")
        
        # 处理因果关系
        for rel in result.get("causal_relations", []):
            source = rel.get("source", "")
            target = rel.get("target", "")
            
            # 跳过无效关系
            if not source or not target:
                continue
            
            total_relations += 1
            key = f"{source} → {target}"
            
            path_evidence[key]["papers"].append(paper_title)
            path_evidence[key]["evidence_texts"].append(rel.get("evidence", ""))
            path_evidence[key]["domains"].add(paper_domain)
            path_evidence[key]["effect_types"].append(rel.get("effect_type", "positive"))
            path_evidence[key]["effect_sizes"].append(rel.get("effect_size", "medium"))
            path_evidence[key]["mechanisms"].append(rel.get("mechanism", ""))
        
        # 处理复杂关系
        for complex_rel in result.get("complex_relations", []):
            rel_type = complex_rel.get("type", "")
            if rel_type == "mediation":
                complex_relations["mediation_effects"].append({
                    "paper": paper_title,
                    "domain": paper_domain,
                    "path": complex_rel.get("path", ""),
                    "description": complex_rel.get("description", ""),
                    "evidence": complex_rel.get("evidence", "")
                })
            elif rel_type == "moderation":
                complex_relations["moderation_effects"].append({
                    "paper": paper_title,
                    "domain": paper_domain,
                    "path": complex_rel.get("path", ""),
                    "description": complex_rel.get("description", ""),
                    "evidence": complex_rel.get("evidence", "")
                })
    
    # 构建因果路径
    causal_paths = []
    path_id = 1
    
    for path_key, evidence_data in sorted(path_evidence.items(), key=lambda x: len(x[1]["papers"]), reverse=True):
        parts = path_key.split(" → ")
        if len(parts) != 2:
            continue
        
        source, target = parts
        evidence_count = len(evidence_data["papers"])
        
        # 确定主要效应类型
        effect_type_counts = defaultdict(int)
        for et in evidence_data["effect_types"]:
            effect_type_counts[et] += 1
        main_effect_type = max(effect_type_counts, key=effect_type_counts.get) if effect_type_counts else "positive"
        
        # 确定效应大小
        size_map = {"small": 1, "medium": 2, "large": 3, "theoretical": 1.5}
        avg_size = sum(size_map.get(s, 2) for s in evidence_data["effect_sizes"]) / max(len(evidence_data["effect_sizes"]), 1)
        effect_size = "large" if avg_size >= 2.5 else ("medium" if avg_size >= 1.5 else "small")
        
        causal_path = {
            "path_id": f"P{path_id:02d}",
            "source": source,
            "target": target,
            "effect_type": main_effect_type,
            "effect_size": effect_size,
            "mechanism": evidence_data["mechanisms"][0] if evidence_data["mechanisms"] else "",
            "evidence": {
                "validated": evidence_count >= 2,
                "evidence_count": evidence_count,
                "supporting_papers": evidence_data["papers"][:5],
                "validated_domains": list(evidence_data["domains"]),
                "sample_evidence": evidence_data["evidence_texts"][:3]
            }
        }
        
        causal_paths.append(causal_path)
        path_id += 1
    
    # 更新图谱
    graph["causal_paths"] = causal_paths
    graph["complex_relations"] = complex_relations
    graph["meta"]["total_paths"] = len(causal_paths)
    graph["meta"]["last_updated"] = time.strftime("%Y-%m-%d")
    graph["extraction_statistics"] = {
        "total_papers_processed": len(results),
        "successful_extractions": success_count,
        "total_relations_extracted": total_relations,
        "total_complex_relations": len(complex_relations["mediation_effects"]) + len(complex_relations["moderation_effects"]),
        "processing_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 因果图谱已保存到: {output_path}")
    print(f"  - 因果路径: {len(causal_paths)} 条")
    print(f"  - 中介效应: {len(complex_relations['mediation_effects'])} 个")
    print(f"  - 调节效应: {len(complex_relations['moderation_effects'])} 个")
    
    return graph


def main():
    """主函数"""
    print("=" * 60)
    print("Claude PDF 因果关系抽取器 V3 (并行版)")
    print("=" * 60)
    
    extractor = ClaudePDFExtractorV3()
    
    # 获取PDF文件列表（前50篇）
    pdf_folder = Path("downloads")
    pdf_files = sorted(pdf_folder.glob("*.pdf"))[:50]
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    
    # 并行处理
    start_time = time.time()
    results = extractor.process_batch([str(f) for f in pdf_files], max_workers=5)
    total_time = time.time() - start_time
    
    # 保存原始结果
    output_dir = Path("outputs/causal_extraction_v3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result.get("success"):
            title = result.get("paper_title", "unknown")[:80]
            # 清理文件名
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
            output_file = output_dir / f"{safe_title}_v3.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)
    print(f"成功: {success_count}/{len(results)}")
    print(f"总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
    print(f"平均每篇: {total_time/len(results):.1f}秒")
    
    # 构建因果图谱
    print("\n" + "=" * 60)
    print("构建因果图谱...")
    print("=" * 60)
    
    graph = build_causal_graph(results, "sandbox/static/data/causal_ontology_extracted.json")
    
    # 保存汇总
    summary = {
        "meta": {
            "total_papers": len(results),
            "success_papers": success_count,
            "total_time_seconds": total_time,
            "avg_time_per_paper": total_time / len(results),
            "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "all_results": results
    }
    
    summary_file = output_dir / "extraction_summary_v3.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 汇总结果已保存到: {summary_file}")


if __name__ == "__main__":
    main()
