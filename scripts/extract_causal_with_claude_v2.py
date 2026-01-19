#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Claude API 直接读取 PDF 文献并抽取因果关系 - V2 优化版
- 统一变量ID格式（V01-V25）
- 明确标注中介/调节效应
- 输出格式与图谱一致
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CausalRelation:
    """因果关系数据类"""
    source: str  # V01 格式
    target: str  # V16 格式
    effect_type: str  # positive, negative, inverted_u, moderating, mediating
    effect_size: str  # large, medium, small
    mechanism: str  # 作用机制
    evidence: str  # 原文证据
    paper_title: str
    domain: str


class ClaudePDFExtractorV2:
    """使用 Claude 从 PDF 中抽取因果关系 - V2 优化版"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """初始化"""
        self.api_key = api_key or os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("JUHENEXT_BASE_URL") or "https://api.anthropic.com"
        
        if not self.api_key:
            raise ValueError("请提供 API Key")
        
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = model or os.getenv("CLAUDE_MODEL") or "claude-sonnet-4-20250514"
        
        print(f"使用 API: {self.base_url}")
        print(f"使用模型: {self.model}")
        
        # 加载标准变量本体（从图谱文件）
        self.variable_ontology = self._load_ontology_from_graph()
        
        # 统计数据
        self.all_relations: List[CausalRelation] = []
        self.variable_counts = defaultdict(int)
        self.path_counts = defaultdict(lambda: {"count": 0, "papers": [], "domains": set()})
    
    def _load_ontology_from_graph(self) -> Dict[str, Any]:
        """从完整图谱加载变量本体"""
        graph_path = "sandbox/static/data/complete_causal_ontology.json"
        
        if not Path(graph_path).exists():
            print(f"警告: 图谱文件不存在 {graph_path}，使用默认本体")
            return self._get_default_ontology()
        
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph = json.load(f)
            
            ontology = {}
            for var in graph.get("variables", []):
                var_id = var["id"]
                ontology[var_id] = {
                    "label": var["label"],
                    "category": var["category"],
                    "definition": var.get("definition", ""),
                    "measurement": var.get("measurement", {})
                }
            
            print(f"✓ 从图谱加载了 {len(ontology)} 个变量")
            return ontology
            
        except Exception as e:
            print(f"警告: 加载图谱失败 {e}，使用默认本体")
            return self._get_default_ontology()
    
    def _get_default_ontology(self) -> Dict[str, Any]:
        """默认变量本体（备用）- 扩展版"""
        return {
            # 输入变量
            "V01_tech_intensity": {"label": "技术投入强度", "category": "input"},
            "V02_firm_size": {"label": "企业规模", "category": "input"},
            "V03_rd_investment": {"label": "研发投资强度", "category": "input"},
            "V04_international_collab": {"label": "国际合作强度", "category": "input"},
            "V05_university_collab": {"label": "产学研合作", "category": "input"},
            "V06_prior_experience": {"label": "先验经验", "category": "input"},
            "V07_policy_support": {"label": "政策支持", "category": "input"},
            "V08_market_competition": {"label": "市场竞争强度", "category": "input"},
            # 中介变量
            "V09_tech_diversity": {"label": "技术跨界度", "category": "mediator"},
            "V10_science_linkage": {"label": "科学关联度", "category": "mediator"},
            "V11_knowledge_recombination": {"label": "知识重组度", "category": "mediator"},
            "V12_tech_cycle_time": {"label": "技术迭代速度", "category": "mediator"},
            "V13_rd_efficiency": {"label": "研发效率", "category": "mediator"},
            "V14_tech_breadth": {"label": "技术广度", "category": "mediator"},
            "V15_tech_depth": {"label": "技术深度", "category": "mediator"},
            # 结果变量
            "V16_tech_impact": {"label": "技术影响力", "category": "outcome"},
            "V17_tech_breakthrough": {"label": "技术突破性", "category": "outcome"},
            "V18_tech_independence": {"label": "技术独立性", "category": "outcome"},
            "V19_commercial_value": {"label": "商业价值", "category": "outcome"},
            "V20_market_share": {"label": "市场份额", "category": "outcome"},
            "V21_licensing_revenue": {"label": "许可收益", "category": "outcome"},
            # 调节变量
            "V22_tech_maturity": {"label": "技术成熟度", "category": "moderator"},
            "V23_industry_type": {"label": "产业类型", "category": "moderator"},
            "V24_firm_type": {"label": "组织类型", "category": "moderator"},
            "V25_geographic_location": {"label": "地理位置", "category": "moderator"},
        }
    
    def _build_extraction_prompt(self) -> str:
        """构建抽取提示词 - V2 优化版"""
        
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

# 因果关系类型定义

## 1. 直接效应 (Direct Effect)
- **positive**: A增加导致B增加
- **negative**: A增加导致B减少
- **inverted_u**: A与B呈倒U型关系（先增后减）
- **threshold**: 存在阈值效应

## 2. 中介效应 (Mediation)
- **mediating**: A通过M影响B
- 必须同时存在：A→M 和 M→B 两条路径
- 示例："研发投入(V03) → 技术跨界度(V09) → 技术影响力(V16)"

## 3. 调节效应 (Moderation)
- **moderating**: Z改变A→B的强度或方向
- 示例："技术成熟度(V22)调节 跨界度(V09)→影响力(V16)"

# 抽取规则

1. **变量映射（严格要求）**：
   - 必须使用标准变量ID（如 V01_tech_intensity）
   - 优先映射到最接近的标准变量，不要轻易使用unmapped
   - 映射指南：
     * "技术差距/技术水平" → V16_tech_impact 或 V18_tech_independence
     * "追赶能力/后发优势" → V18_tech_independence
     * "先发优势/先动者优势" → V06_prior_experience
     * "技术成熟度/生命周期" → V22_tech_maturity
     * "知识溢出/知识转移" → V10_science_linkage 或 V11_knowledge_recombination
   - 只有在完全无法映射时才使用 "unmapped_原始术语"

2. **效应大小判断**：
   - large: 显著性p<0.01 或 效应量>0.5
   - medium: 显著性p<0.05 或 效应量0.3-0.5
   - small: 显著性p<0.1 或 效应量<0.3
   - theoretical: 理论推导，无实证检验

3. **机制描述**：
   - 用一句话说明"为什么A影响B"
   - 引用论文的理论或实证发现

# 输出格式（严格JSON）

```json
{{
  "paper_title": "论文标题",
  "paper_domain": "Clean Energy/ICT/Biotech/Automotive/Materials/General",
  "research_design": "empirical/theoretical/review",
  "variables_identified": [
    {{
      "original_term": "论文原始术语",
      "mapped_to": "V01_tech_intensity",
      "role": "independent/dependent/mediator/moderator"
    }}
  ],
  "causal_relations": [
    {{
      "source": "V01_tech_intensity",
      "target": "V16_tech_impact",
      "effect_type": "positive/negative/inverted_u/moderating/mediating",
      "effect_size": "large/medium/small/theoretical",
      "mechanism": "作用机制的简要描述",
      "evidence": "原文证据（关键句子）"
    }}
  ],
  "complex_relations": [
    {{
      "type": "mediation",
      "path": "V03_rd_investment → V09_tech_diversity → V16_tech_impact",
      "evidence": "中介效应的证据"
    }},
    {{
      "type": "moderation",
      "moderator": "V22_tech_maturity",
      "moderated_path": "V09_tech_diversity → V16_tech_impact",
      "direction": "negative",
      "evidence": "调节效应的证据"
    }}
  ]
}}
```

# 注意事项
1. 只抽取论文中**明确提出或有数据支持**的关系
2. 中介/调节效应必须有明确证据，不要推测
3. 变量ID必须使用V01-V25格式
4. evidence字段引用原文，保持准确性
"""
    
    def _encode_pdf(self, pdf_path: str) -> str:
        """将 PDF 文件编码为 base64"""
        with open(pdf_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """从单个 PDF 文件中抽取因果关系"""
        try:
            pdf_data = self._encode_pdf(pdf_path)
            
            message = self.client.messages.create(
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
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "paper_title": Path(pdf_path).stem
            }
    
    def _parse_response(self, response_text: str, pdf_path: str) -> Dict[str, Any]:
        """解析 Claude 的响应"""
        import re
        
        # 保存调试文件
        debug_file = Path("outputs/causal_extraction_v2") / f"{Path(pdf_path).stem}_debug.txt"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
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
        return data


def main():
    """主函数"""
    print("=" * 60)
    print("Claude PDF 因果关系抽取器 V2")
    print("=" * 60)
    
    extractor = ClaudePDFExtractorV2()
    
    # 测试3篇
    pdf_folder = Path("downloads")
    pdf_files = list(pdf_folder.glob("*.pdf"))[:3]
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("=" * 60)
    
    output_dir = Path("outputs/causal_extraction_v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    success_count = 0
    
    import datetime
    start_time = time.time()
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        paper_start = time.time()
        print(f"[{idx}/{len(pdf_files)}] 处理: {pdf_file.name[:50]}...")
        
        result = extractor.extract_from_pdf(str(pdf_file))
        
        paper_time = time.time() - paper_start
        
        if result.get("success"):
            print(f"  ✓ 成功: {len(result.get('causal_relations', []))} 条因果关系 | 耗时: {paper_time:.1f}秒")
            success_count += 1
        else:
            print(f"  ✗ 失败: {result.get('error')} | 耗时: {paper_time:.1f}秒")
        
        # 保存结果
        output_file = output_dir / f"{pdf_file.stem}_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        results.append(result)
        time.sleep(1)
    
    total_time = time.time() - start_time
    
    # 统计分析
    print("\n" + "=" * 60)
    print("抽取结果统计")
    print("=" * 60)
    
    # 统计变量使用频次
    var_counts = defaultdict(int)
    path_counts = defaultdict(lambda: {"count": 0, "papers": [], "domains": set()})
    
    for result in results:
        if not result.get("success"):
            continue
        
        paper_title = result.get("paper_title", "Unknown")
        paper_domain = result.get("paper_domain", "General")
        
        # 统计变量
        for rel in result.get("causal_relations", []):
            source = rel.get("source", "")
            target = rel.get("target", "")
            
            if source.startswith("V"):
                var_counts[source] += 1
            if target.startswith("V"):
                var_counts[target] += 1
            
            # 统计路径
            path_key = f"{source} → {target}"
            path_counts[path_key]["count"] += 1
            path_counts[path_key]["papers"].append(paper_title[:50])
            path_counts[path_key]["domains"].add(paper_domain)
    
    # 输出统计
    print(f"\n处理成功: {success_count}/{len(pdf_files)}")
    print(f"总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
    print(f"平均每篇: {total_time/len(pdf_files):.1f}秒")
    print(f"\n[变量使用频次] Top 10:")
    for var, count in sorted(var_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        var_label = extractor.variable_ontology.get(var, {}).get("label", var)
        print(f"  - {var} ({var_label}): {count}次")
    
    print(f"\n[因果路径] Top 10:")
    for path, info in sorted(path_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
        print(f"  - {path}: {info['count']}篇 | 领域: {', '.join(info['domains'])}")
    
    # 保存聚合结果
    summary = {
        "meta": {
            "total_papers": len(pdf_files),
            "success_papers": success_count,
            "extraction_date": time.strftime("%Y-%m-%d"),
            "model": extractor.model
        },
        "variable_statistics": dict(var_counts),
        "path_statistics": {
            path: {
                "count": info["count"],
                "papers": info["papers"],
                "domains": list(info["domains"])
            }
            for path, info in path_counts.items()
        },
        "all_results": results
    }
    
    summary_file = output_dir / "extraction_summary_v2.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 聚合结果已保存到: {summary_file}")
    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
