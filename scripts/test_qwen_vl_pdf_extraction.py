#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 qwen-vl-ocr-2025-11-20 模型从PDF提取因果关系
"""

import os
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 尝试导入 dashscope
try:
    import dashscope
    from dashscope import MultiModalConversation, Files
    DASHSCOPE_AVAILABLE = True
except ImportError:
    print("[WARN] 未安装 dashscope，请运行: pip install dashscope")
    DASHSCOPE_AVAILABLE = False

load_dotenv()


class QwenVLPDFExtractor:
    """使用通义千问VL模型从PDF中抽取因果关系"""
    
    def __init__(self, api_key: str = None, model: str = "qwen-vl-ocr-2025-11-20"):
        """
        初始化
        
        Args:
            api_key: DashScope API Key
            model: 模型名称
        """
        if not DASHSCOPE_AVAILABLE:
            raise ImportError("请先安装 dashscope: pip install dashscope")
        
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数")
        
        dashscope.api_key = self.api_key
        self.model = model
        
        print(f"[OK] 使用模型: {self.model}")
        print(f"[OK] API Key: {self.api_key[:10]}...")
        
        # 加载变量本体
        self.variable_ontology = self._load_ontology()
    
    def _load_ontology(self) -> Dict[str, Any]:
        """加载变量本体"""
        graph_path = "src/graphs/data/causal/causal_ontology_extracted.json"
        
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
            
            print(f"[OK] 加载了 {len(ontology)} 个变量")
            return ontology
            
        except Exception as e:
            print(f"[WARN] 加载本体失败: {e}")
            return {}
    
    def _build_extraction_prompt(self) -> str:
        """构建抽取提示词"""
        from collections import defaultdict
        
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
从这篇PDF论文中抽取因果关系，特别关注：
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
2. 变量ID必须使用标准格式（V01-V30）
3. 尽量映射到标准变量，减少unmapped
4. evidence字段引用原文，保持准确性
5. 仔细阅读PDF内容，识别所有相关的因果关系
"""
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        从PDF文件提取因果关系
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取结果字典
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"PDF文件不存在: {pdf_path}",
                "paper_title": pdf_path.stem
            }
        
        print(f"\n[INFO] 处理PDF: {pdf_path.name}")
        print(f"   路径: {pdf_path}")
        
        try:
            start_time = time.time()
            
            # 读取PDF文件并转换为base64
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            import base64
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # 构建消息 - 使用正确的格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:application/pdf;base64,{pdf_base64}",
                            "type": "image"
                        },
                        {
                            "text": self._build_extraction_prompt()
                        }
                    ]
                }
            ]
            
            print("   正在调用API...")
            
            # 调用通义千问VL API
            response = MultiModalConversation.call(
                model=self.model,
                messages=messages,
                max_tokens=4096
            )
            
            elapsed = time.time() - start_time
            
            # 检查响应
            if response.status_code == 200:
                result_text = response.output.choices[0].message.content[0].text
                
                # 解析JSON响应
                result = self._parse_response(result_text, pdf_path)
                result["success"] = True
                result["api_time"] = elapsed
                result["model"] = self.model
                
                print(f"   [OK] 成功 ({elapsed:.1f}秒)")
                if result.get("causal_relations"):
                    print(f"   [OK] 提取到 {len(result['causal_relations'])} 条因果关系")
                
                return result
            else:
                error_msg = f"API错误: {response.status_code} - {response.message}"
                print(f"   [ERROR] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "paper_title": pdf_path.stem,
                    "api_time": elapsed
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"   [ERROR] 异常: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "paper_title": pdf_path.stem
            }
    
    def _parse_response(self, response_text: str, pdf_path: Path) -> Dict[str, Any]:
        """解析API响应"""
        try:
            # 尝试提取JSON（可能在代码块中）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 添加元数据
            result["file_path"] = str(pdf_path)
            result["extraction_model"] = self.model
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON解析失败，返回原始文本
            return {
                "success": False,
                "error": f"JSON解析失败: {e}",
                "raw_response": response_text[:500],  # 只保存前500字符
                "paper_title": pdf_path.stem
            }


def main():
    """主函数 - 测试单个PDF"""
    print("=" * 60)
    print("通义千问VL PDF因果关系提取测试")
    print("=" * 60)
    
    if not DASHSCOPE_AVAILABLE:
        print("\n[ERROR] 请先安装 dashscope:")
        print("   pip install dashscope")
        return
    
    # 初始化提取器
    try:
        extractor = QwenVLPDFExtractor(model="qwen-vl-ocr-2025-11-20")
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        return
    
    # 从命令行参数获取PDF路径
    test_pdf = None
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if pdf_path.exists() and pdf_path.suffix.lower() == '.pdf':
            test_pdf = pdf_path
            print(f"\n[OK] 使用命令行参数指定的PDF: {test_pdf}")
        else:
            print(f"\n[ERROR] 指定的PDF文件不存在或格式错误: {pdf_path}")
            return
    
    # 如果没有命令行参数，查找PDF文件
    if not test_pdf:
        # 先检查根目录
        root_pdfs = list(Path(".").glob("*.pdf"))
        if root_pdfs:
            pdf_files = root_pdfs
            print(f"\n[OK] 在根目录找到 {len(pdf_files)} 个PDF文件")
        else:
            # 再检查其他文件夹
            pdf_folders = [
                Path("downloads"),
                Path("data"),
            ]
            
            pdf_files = []
            for folder in pdf_folders:
                if folder.exists():
                    pdfs = list(folder.glob("*.pdf"))
                    if pdfs:
                        pdf_files.extend(pdfs)
                        print(f"\n[OK] 在 {folder} 找到 {len(pdfs)} 个PDF文件")
        
        if not pdf_files:
            print("\n[WARN] 未找到PDF文件")
            print("   使用方法:")
            print("   python scripts/test_qwen_vl_pdf_extraction.py <pdf_path>")
            print("\n   或者将PDF文件放在以下任一文件夹:")
            for folder in pdf_folders:
                print(f"   - {folder}")
            return
        
        # 选择第一个PDF进行测试
        test_pdf = pdf_files[0]
    
    print(f"\n[INFO] 测试文件: {test_pdf.name}")
    
    # 提取因果关系
    result = extractor.extract_from_pdf(str(test_pdf))
    
    # 保存结果
    output_dir = Path("outputs/qwen_vl_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{test_pdf.stem}_qwen_vl.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 结果已保存到: {output_file}")
    
    # 显示摘要
    if result.get("success"):
        print("\n" + "=" * 60)
        print("提取结果摘要")
        print("=" * 60)
        print(f"论文标题: {result.get('paper_title', 'N/A')}")
        print(f"研究领域: {result.get('paper_domain', 'N/A')}")
        print(f"研究设计: {result.get('research_design', 'N/A')}")
        print(f"因果关系数: {len(result.get('causal_relations', []))}")
        print(f"复杂关系数: {len(result.get('complex_relations', []))}")
        print(f"API耗时: {result.get('api_time', 0):.1f}秒")
        
        if result.get('causal_relations'):
            print("\n因果关系:")
            for i, rel in enumerate(result['causal_relations'][:5], 1):  # 只显示前5个
                print(f"  {i}. {rel.get('source')} -> {rel.get('target')} ({rel.get('effect_type')})")
    else:
        print(f"\n[ERROR] 提取失败: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
