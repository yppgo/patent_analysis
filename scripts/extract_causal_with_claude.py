#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Claude API 直接读取 PDF 文献并抽取因果关系
支持批量处理，生成因果知识图谱
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CausalRelation:
    """因果关系数据类"""
    source_variable: str
    target_variable: str
    relationship_type: str  # positive, negative, moderating, mediating
    strength: str  # strong, moderate, weak
    evidence: str  # 原文证据
    domain: str  # 研究领域
    paper_title: str


@dataclass
class ExtractionResult:
    """抽取结果"""
    paper_title: str
    paper_domain: str
    variables: List[Dict[str, str]]
    causal_relations: List[CausalRelation]
    hypotheses: List[str]
    success: bool
    error: Optional[str] = None


class ClaudePDFExtractor:
    """使用 Claude 从 PDF 中抽取因果关系"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        初始化
        
        Args:
            api_key: API Key，如果不提供则从环境变量读取
            base_url: API 代理地址，如果不提供则从环境变量读取
            model: 模型名称，默认 claude-sonnet-4-20250514
        """
        self.api_key = api_key or os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("JUHENEXT_BASE_URL") or "https://api.anthropic.com"
        
        if not self.api_key:
            raise ValueError("请提供 API Key (JUHENEXT_API_KEY 或 ANTHROPIC_API_KEY)")
        
        # 初始化客户端，支持自定义 base_url
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = model or os.getenv("CLAUDE_MODEL") or "claude-sonnet-4-20250514"
        
        print(f"使用 API: {self.base_url}")
        print(f"使用模型: {self.model}")
        
        # 预定义的变量本体
        self.variable_ontology = self._load_variable_ontology()
        
        # 统计数据
        self.all_relations: List[CausalRelation] = []
        self.variable_counts = defaultdict(int)
        self.path_counts = defaultdict(lambda: {"count": 0, "papers": [], "domains": set()})
    
    def _load_variable_ontology(self) -> Dict[str, Any]:
        """加载变量本体定义 - 扩充版"""
        return {
            # ========== 输入变量 (Input Variables) ==========
            "tech_intensity": {
                "label": "技术投入强度",
                "category": "input",
                "aliases": ["专利数量", "patent count", "R&D intensity", "技术投资", "patent portfolio", "技术存量"]
            },
            "firm_size": {
                "label": "企业规模",
                "category": "input",
                "aliases": ["company size", "组织规模", "员工数量", "firm scale", "enterprise size"]
            },
            "rd_investment": {
                "label": "研发投资强度",
                "category": "input",
                "aliases": ["R&D spending", "研发支出", "R&D expenditure", "research investment", "研发经费"]
            },
            "international_collab": {
                "label": "国际合作强度",
                "category": "input",
                "aliases": ["international collaboration", "跨国合作", "global partnership", "cross-border", "国际化"]
            },
            "university_collab": {
                "label": "产学研合作",
                "category": "input",
                "aliases": ["university-industry", "academic collaboration", "产学合作", "industry-academia", "校企合作"]
            },
            "policy_support": {
                "label": "政策支持",
                "category": "input",
                "aliases": ["government support", "政府补贴", "policy incentive", "regulation", "产业政策"]
            },
            "market_competition": {
                "label": "市场竞争强度",
                "category": "input",
                "aliases": ["competition intensity", "competitive pressure", "市场集中度", "HHI"]
            },
            "prior_experience": {
                "label": "先验经验",
                "category": "input",
                "aliases": ["prior knowledge", "existing capability", "技术积累", "knowledge base", "经验积累"]
            },
            
            # ========== 中介变量 (Mediator Variables) ==========
            "tech_diversity": {
                "label": "技术跨界度",
                "category": "mediator",
                "aliases": ["IPC entropy", "技术多样性", "technology diversity", "跨领域", "technological breadth"]
            },
            "science_linkage": {
                "label": "科学关联度",
                "category": "mediator",
                "aliases": ["NPL citations", "科学引用", "science linkage", "non-patent literature", "科学基础"]
            },
            "tech_cycle_time": {
                "label": "技术迭代速度",
                "category": "mediator",
                "aliases": ["TCT", "technology cycle time", "技术周期", "citation lag", "innovation speed", "创新速度"]
            },
            "knowledge_recombination": {
                "label": "知识重组度",
                "category": "mediator",
                "aliases": ["knowledge recombination", "知识整合", "combinatorial innovation", "knowledge integration"]
            },
            "tech_novelty": {
                "label": "技术新颖度",
                "category": "mediator",
                "aliases": ["novelty", "originality", "创新性", "newness", "技术原创性"]
            },
            "knowledge_spillover": {
                "label": "知识溢出",
                "category": "mediator",
                "aliases": ["spillover", "knowledge diffusion", "技术扩散", "knowledge transfer", "技术转移"]
            },
            "absorptive_capacity": {
                "label": "吸收能力",
                "category": "mediator",
                "aliases": ["absorptive capacity", "learning capability", "学习能力", "知识吸收"]
            },
            
            # ========== 结果变量 (Outcome Variables) ==========
            "tech_impact": {
                "label": "技术影响力",
                "category": "outcome",
                "aliases": ["forward citations", "被引次数", "citation count", "patent impact", "PII", "影响因子"]
            },
            "tech_breakthrough": {
                "label": "技术突破性",
                "category": "outcome",
                "aliases": ["breakthrough innovation", "颠覆性创新", "radical innovation"]
            },
            "commercial_value": {
                "label": "商业价值",
                "category": "outcome",
                "aliases": ["patent value", "专利价值", "market value", "维持年限", "economic value", "licensing"]
            },
            "tech_independence": {
                "label": "技术独立性",
                "category": "outcome",
                "aliases": ["technological independence", "自主创新", "indigenous innovation", "self-reliance", "技术自主"]
            },
            "catching_up": {
                "label": "技术追赶能力",
                "category": "outcome",
                "aliases": ["catch-up", "catching up", "latecomer", "后发优势", "追赶", "技术赶超"]
            },
            "tech_competitiveness": {
                "label": "技术竞争力",
                "category": "outcome",
                "aliases": ["competitiveness", "competitive advantage", "竞争优势", "technology strength", "TS"]
            },
            "innovation_performance": {
                "label": "创新绩效",
                "category": "outcome",
                "aliases": ["innovation performance", "创新产出", "R&D performance", "研发绩效"]
            },
            "market_share": {
                "label": "市场份额",
                "category": "outcome",
                "aliases": ["market share", "市场占有率", "market position", "市场地位"]
            },
            "tech_convergence": {
                "label": "技术融合度",
                "category": "outcome",
                "aliases": ["technology convergence", "技术融合", "cross-domain", "跨界融合"]
            },
            "tech_maturity": {
                "label": "技术成熟度",
                "category": "outcome",
                "aliases": ["technology maturity", "技术成熟", "TRL", "technology readiness", "产业化程度"]
            },
            
            # ========== 调节变量 (Moderator Variables) ==========
            "industry_type": {
                "label": "产业类型",
                "category": "moderator",
                "aliases": ["industry sector", "行业类型", "sector", "产业领域"]
            },
            "tech_regime": {
                "label": "技术体制",
                "category": "moderator",
                "aliases": ["technological regime", "技术范式", "technology paradigm", "技术轨道"]
            },
            "country_development": {
                "label": "国家发展水平",
                "category": "moderator",
                "aliases": ["development level", "发展阶段", "developed/developing", "经济发展水平"]
            }
        }
    
    def _encode_pdf(self, pdf_path: str) -> str:
        """将 PDF 文件编码为 base64"""
        with open(pdf_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    def _build_extraction_prompt(self) -> str:
        """构建抽取提示词 - 改进版"""
        
        # 构建变量列表，按类别分组
        input_vars = []
        mediator_vars = []
        outcome_vars = []
        moderator_vars = []
        
        for var_id, var_info in self.variable_ontology.items():
            aliases = ", ".join(var_info["aliases"][:4])
            line = f"    - {var_id} ({var_info['label']}): {aliases}"
            if var_info["category"] == "input":
                input_vars.append(line)
            elif var_info["category"] == "mediator":
                mediator_vars.append(line)
            elif var_info["category"] == "outcome":
                outcome_vars.append(line)
            elif var_info["category"] == "moderator":
                moderator_vars.append(line)
        
        variables_str = f"""
  【输入变量 Input】
{chr(10).join(input_vars)}

  【中介变量 Mediator】
{chr(10).join(mediator_vars)}

  【结果变量 Outcome】
{chr(10).join(outcome_vars)}

  【调节变量 Moderator】
{chr(10).join(moderator_vars)}
"""
        
        return f"""# 角色
你是一位专精于专利计量学、技术创新和科学计量学的资深学者，擅长从学术论文中识别和抽取因果关系。

# 任务
仔细阅读这篇学术论文，系统性地抽取：
1. 研究假设（完整的因果表述）
2. 变量识别与映射
3. 因果关系及其证据

# 标准变量本体
请将论文中的变量映射到以下标准变量（优先使用这些ID）：
{variables_str}

# 详细抽取要求

## 1. 假设抽取（重要！）
假设必须是**完整的因果陈述**，格式为：
- "X 对 Y 有正向/负向影响"
- "X 通过 M 影响 Y（中介效应）"
- "Z 调节 X 对 Y 的影响（调节效应）"

示例：
- ✅ "H1: 技术迭代速度(TCT)对后发国家的技术追赶能力有负向影响"
- ✅ "H2: 产学研合作通过提升科学关联度，间接促进技术影响力"
- ❌ "H1: 技术周期很长"（这不是因果假设）

## 2. 变量映射规则
- 优先映射到标准本体中的变量ID
- 如果论文变量与标准变量语义相近，使用标准ID
- 只有完全无法映射时，才使用论文原始术语（英文小写+下划线）

## 3. 因果关系抽取
每条关系需包含：
- source_variable: 原因变量
- target_variable: 结果变量
- relationship_type: positive/negative/moderating/mediating
- strength: strong(p<0.01)/moderate(p<0.05)/weak(p<0.1)/theoretical(理论推导)
- evidence: 原文关键句子（英文保持原文，中文翻译）

## 4. 研究领域判断
- Clean Energy: 清洁能源、可再生能源、环保技术
- ICT: 信息通信、5G、物联网、人工智能
- Biotech: 生物技术、医药、基因
- Automotive: 汽车、电动车、交通
- Materials: 新材料、纳米技术
- General: 方法论、跨领域研究

# 输出格式（严格JSON）

```json
{{
  "paper_title": "论文完整标题",
  "paper_domain": "领域",
  "research_question": "论文的核心研究问题（一句话概括）",
  "variables_identified": [
    {{
      "original_term": "论文原始术语",
      "mapped_to": "标准变量ID",
      "role": "independent/dependent/mediator/moderator",
      "measurement": "如何测量（如有）"
    }}
  ],
  "hypotheses": [
    {{
      "id": "H1",
      "statement": "完整的因果假设陈述",
      "source_var": "原因变量ID",
      "target_var": "结果变量ID",
      "direction": "positive/negative",
      "supported": true/false,
      "evidence": "支持/反驳该假设的证据"
    }}
  ],
  "causal_relations": [
    {{
      "source_variable": "原因变量ID",
      "target_variable": "结果变量ID",
      "relationship_type": "positive/negative/moderating/mediating",
      "strength": "strong/moderate/weak/theoretical",
      "evidence": "原文证据"
    }}
  ]
}}
```

# 注意事项
1. 只抽取论文中**明确提出或有实证支持**的关系
2. 假设必须是完整的因果陈述，不是简单的描述性结论
3. 如果论文是方法论文章，关注方法论证的因果逻辑
4. evidence 字段引用原文，保持学术准确性
5. 如果某个字段信息不足，可以标注为 null，但不要编造
"""

    def extract_from_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        从单个 PDF 文件中抽取因果关系
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            ExtractionResult 对象
        """
        try:
            # 编码 PDF
            pdf_data = self._encode_pdf(pdf_path)
            
            # 调用 Claude API
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
            
            # 解析响应
            response_text = message.content[0].text
            
            # 提取 JSON
            result = self._parse_response(response_text, pdf_path)
            return result
            
        except Exception as e:
            return ExtractionResult(
                paper_title=Path(pdf_path).stem,
                paper_domain="Unknown",
                variables=[],
                causal_relations=[],
                hypotheses=[],
                success=False,
                error=str(e)
            )
    
    def _parse_response(self, response_text: str, pdf_path: str) -> ExtractionResult:
        """解析 Claude 的响应 - 增强版"""
        
        import re
        
        # 保存原始响应用于调试
        debug_file = Path("outputs/causal_extraction") / f"{Path(pdf_path).stem}_debug.txt"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        # 尝试多种方式提取 JSON
        json_str = None
        
        # 方式1: ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        
        # 方式2: ``` ... ``` (无json标记)
        if not json_str:
            json_match = re.search(r'```\s*({\s*".*?})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
        
        # 方式3: 直接找 { ... } 结构
        if not json_str:
            json_match = re.search(r'(\{[\s\S]*"paper_title"[\s\S]*\})', response_text)
            if json_match:
                json_str = json_match.group(1)
        
        # 方式4: 整个响应就是 JSON
        if not json_str:
            json_str = response_text.strip()
        
        # 清理 JSON 字符串
        json_str = json_str.strip()
        
        # 尝试解析
        data = None
        parse_errors = []
        
        # 尝试1: 直接解析
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            parse_errors.append(f"直接解析: {e}")
        
        # 尝试2: 修复常见问题
        if not data:
            try:
                # 修复: true/false/null
                fixed = json_str
                fixed = re.sub(r'\bTrue\b', 'true', fixed)
                fixed = re.sub(r'\bFalse\b', 'false', fixed)
                fixed = re.sub(r'\bNone\b', 'null', fixed)
                # 修复: 尾部逗号
                fixed = re.sub(r',\s*}', '}', fixed)
                fixed = re.sub(r',\s*]', ']', fixed)
                data = json.loads(fixed)
            except json.JSONDecodeError as e:
                parse_errors.append(f"修复后解析: {e}")
        
        # 尝试3: 截取到最后一个 }
        if not data:
            try:
                last_brace = json_str.rfind('}')
                if last_brace > 0:
                    truncated = json_str[:last_brace+1]
                    data = json.loads(truncated)
            except json.JSONDecodeError as e:
                parse_errors.append(f"截取解析: {e}")
        
        if not data:
            error_msg = f"JSON 解析失败: {'; '.join(parse_errors)}"
            print(f"    调试文件: {debug_file}")
            return ExtractionResult(
                paper_title=Path(pdf_path).stem,
                paper_domain="Unknown",
                variables=[],
                causal_relations=[],
                hypotheses=[],
                success=False,
                error=error_msg
            )
        
        # 构建因果关系列表
        causal_relations = []
        for rel in data.get("causal_relations", []):
            causal_relations.append(CausalRelation(
                source_variable=rel.get("source_variable", ""),
                target_variable=rel.get("target_variable", ""),
                relationship_type=rel.get("relationship_type", "positive"),
                strength=rel.get("strength", "moderate"),
                evidence=rel.get("evidence", ""),
                domain=data.get("paper_domain", "General"),
                paper_title=data.get("paper_title", Path(pdf_path).stem)
            ))
        
        # 处理假设（支持新旧两种格式）
        hypotheses = data.get("hypotheses", [])
        
        return ExtractionResult(
            paper_title=data.get("paper_title", Path(pdf_path).stem),
            paper_domain=data.get("paper_domain", "General"),
            variables=data.get("variables_identified", []),
            causal_relations=causal_relations,
            hypotheses=hypotheses,
            success=True
        )
    
    def extract_from_folder(
        self, 
        folder_path: str, 
        limit: int = None,
        output_dir: str = "outputs/causal_extraction"
    ) -> Dict[str, Any]:
        """
        批量处理文件夹中的 PDF 文件
        
        Args:
            folder_path: PDF 文件夹路径
            limit: 限制处理数量（用于测试）
            output_dir: 输出目录
            
        Returns:
            统计结果
        """
        folder = Path(folder_path)
        pdf_files = list(folder.glob("*.pdf"))
        
        if limit:
            pdf_files = pdf_files[:limit]
        
        print(f"找到 {len(pdf_files)} 个 PDF 文件")
        print("=" * 60)
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        success_count = 0
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"[{idx}/{len(pdf_files)}] 处理: {pdf_file.name[:50]}...")
            
            result = self.extract_from_pdf(str(pdf_file))
            
            if result.success:
                success_count += 1
                print(f"  ✓ 成功: 发现 {len(result.causal_relations)} 条因果关系")
                
                # 累积统计
                for rel in result.causal_relations:
                    self.all_relations.append(rel)
                    self.variable_counts[rel.source_variable] += 1
                    self.variable_counts[rel.target_variable] += 1
                    
                    path_key = f"{rel.source_variable} -> {rel.target_variable}"
                    self.path_counts[path_key]["count"] += 1
                    self.path_counts[path_key]["papers"].append(result.paper_title)
                    self.path_counts[path_key]["domains"].add(result.paper_domain)
            else:
                print(f"  ✗ 失败: {result.error}")
            
            # 保存单篇结果
            result_file = output_path / f"{pdf_file.stem}_causal.json"
            self._save_result(result, result_file)
            
            results.append(result)
            
            # 避免 API 限流
            time.sleep(1)
        
        # 生成汇总
        summary = self._generate_summary(results, output_path)
        
        print("\n" + "=" * 60)
        print(f"处理完成: {success_count}/{len(pdf_files)} 成功")
        print(f"总计发现 {len(self.all_relations)} 条因果关系")
        
        return summary
    
    def _save_result(self, result: ExtractionResult, output_path: Path):
        """保存单篇抽取结果"""
        data = {
            "paper_title": result.paper_title,
            "paper_domain": result.paper_domain,
            "variables": result.variables,
            "causal_relations": [
                {
                    "source": rel.source_variable,
                    "target": rel.target_variable,
                    "type": rel.relationship_type,
                    "strength": rel.strength,
                    "evidence": rel.evidence
                }
                for rel in result.causal_relations
            ],
            "hypotheses": result.hypotheses,
            "success": result.success,
            "error": result.error
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_summary(self, results: List[ExtractionResult], output_path: Path) -> Dict[str, Any]:
        """生成汇总统计和因果图谱"""
        
        # 统计
        summary = {
            "meta": {
                "total_papers": len(results),
                "success_count": sum(1 for r in results if r.success),
                "total_relations": len(self.all_relations),
                "extraction_method": "claude_pdf_direct"
            },
            "variable_frequency": dict(sorted(
                self.variable_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "path_statistics": {},
            "domain_distribution": defaultdict(int)
        }
        
        # 路径统计
        for path_key, data in sorted(
            self.path_counts.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        ):
            summary["path_statistics"][path_key] = {
                "count": data["count"],
                "validated": data["count"] >= 3,
                "domains": list(data["domains"]),
                "sample_papers": data["papers"][:3]
            }
        
        # 领域分布
        for result in results:
            if result.success:
                summary["domain_distribution"][result.paper_domain] += 1
        
        summary["domain_distribution"] = dict(summary["domain_distribution"])
        
        # 保存汇总
        summary_file = output_path / "extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 生成因果图谱
        ontology = self._generate_causal_ontology(output_path)
        
        return summary
    
    def _generate_causal_ontology(self, output_path: Path) -> Dict[str, Any]:
        """生成因果本体论/知识图谱"""
        
        # 构建变量节点
        variables = []
        for var_id, count in self.variable_counts.items():
            var_info = self.variable_ontology.get(var_id, {})
            variables.append({
                "id": var_id,
                "label": var_info.get("label", var_id),
                "category": var_info.get("category", "unknown"),
                "evidence_count": count,
                "source": "extracted_by_claude"
            })
        
        # 构建因果路径
        causal_paths = []
        for path_key, data in self.path_counts.items():
            source, target = path_key.split(" -> ")
            causal_paths.append({
                "path_id": f"P_{len(causal_paths)+1:03d}",
                "source": source,
                "target": target,
                "evidence": {
                    "validated": data["count"] >= 3,
                    "evidence_count": data["count"],
                    "sample_papers": data["papers"][:5],
                    "validated_domains": list(data["domains"])
                }
            })
        
        # 构建本体论
        ontology = {
            "meta": {
                "name": "Claude-Extracted Causal Ontology",
                "version": "1.0",
                "description": "使用 Claude API 从专利分析论文中直接抽取的因果关系图谱",
                "extraction_method": "claude_pdf_direct",
                "model": self.model,
                "total_papers_analyzed": len(set(
                    rel.paper_title for rel in self.all_relations
                ))
            },
            "variables": sorted(variables, key=lambda x: x["evidence_count"], reverse=True),
            "causal_paths": sorted(causal_paths, key=lambda x: x["evidence"]["evidence_count"], reverse=True),
            "statistics": {
                "total_variables": len(variables),
                "total_paths": len(causal_paths),
                "validated_paths": sum(1 for p in causal_paths if p["evidence"]["validated"]),
                "domain_coverage": dict(defaultdict(int))
            }
        }
        
        # 计算领域覆盖
        for rel in self.all_relations:
            ontology["statistics"]["domain_coverage"][rel.domain] = \
                ontology["statistics"]["domain_coverage"].get(rel.domain, 0) + 1
        
        # 保存
        ontology_file = output_path / "claude_extracted_ontology.json"
        with open(ontology_file, 'w', encoding='utf-8') as f:
            json.dump(ontology, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 因果图谱已保存到: {ontology_file}")
        
        return ontology


def main():
    """主函数"""
    
    print("=" * 60)
    print("Claude PDF 因果关系抽取器")
    print("=" * 60)
    
    # 检查 API Key（优先使用聚合AI代理）
    api_key = os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("JUHENEXT_BASE_URL")
    
    if not api_key:
        print("错误: 请设置 API Key")
        print("在 .env 文件中添加:")
        print("  JUHENEXT_API_KEY=your_key_here")
        print("  JUHENEXT_BASE_URL=https://api.juheai.top")
        return
    
    # 初始化抽取器（自动读取环境变量）
    extractor = ClaudePDFExtractor()
    
    # 设置路径
    pdf_folder = "downloads"
    
    if not Path(pdf_folder).exists():
        print(f"错误: 文件夹 {pdf_folder} 不存在")
        return
    
    # 批量处理（先测试 3 篇）
    print("\n开始处理 PDF 文件...")
    print("提示: 首次运行建议设置 limit=3 进行测试\n")
    
    summary = extractor.extract_from_folder(
        folder_path=pdf_folder,
        limit=3,  # 测试时限制数量，正式运行时设为 None
        output_dir="outputs/causal_extraction"
    )
    
    # 打印统计
    print("\n" + "=" * 60)
    print("抽取结果统计")
    print("=" * 60)
    
    print(f"\n[变量频次] Top 10:")
    for var, count in list(summary["variable_frequency"].items())[:10]:
        var_info = extractor.variable_ontology.get(var, {})
        label = var_info.get("label", var)
        print(f"  - {label}: {count}次")
    
    print(f"\n[因果路径] Top 10:")
    for path, data in list(summary["path_statistics"].items())[:10]:
        status = "✓" if data["validated"] else "?"
        print(f"  [{status}] {path}: {data['count']}篇")
    
    print(f"\n[领域分布]:")
    for domain, count in summary["domain_distribution"].items():
        print(f"  - {domain}: {count}篇")
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
