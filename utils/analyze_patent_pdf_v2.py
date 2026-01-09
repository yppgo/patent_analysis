#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专利PDF分析工具 V2.0
✨ 新增 Dataset 节点支持
"""

# ... (前面的代码保持不变，只修改 analyze_patent_with_qwen 函数中的 prompt)

def analyze_patent_with_qwen_v2(text):
    """
    使用Qwen模型分析专利文本 - V2.0 增强版
    ✨ 新增 Dataset 节点提取
    """
    # ... (前面的代码保持不变)
    
    # 构造优化后的 prompt
    prompt = f"""
# Role (角色)
你是一位专精于"文献计量学"、"专利数据挖掘"及"机器学习"领域的**首席算法架构师**。

# Task (任务)
你的任务是深度解构一篇【学术论文的摘要/方法章节】，并从中提取出**可被AI智能体复现**的"分析实验逻辑链"。
你需要像填写"实验记录单"一样，精准识别作者的**数据集来源**、**分析意图**、**数据输入**、**方法配置（含库和参数）**以及**量化评估结果**。

# Constraints (约束)
1. **面向执行**：提取的细节必须足以指导另一个AI写出代码。
2. **参数结构化**：将文本描述的参数转化为 Key-Value 结构。
3. **指标量化**：必须提取具体的数值结果。
4. **格式严格**：输出标准 JSON，严禁包含 Markdown 标记。
5. **✨ 数据集追溯**：必须提取数据集的来源、规模、查询条件和预处理步骤。

【严重警告：防幻觉约束】
1. 事实核查：你只能提取文中**明确写出**的内容。
2. 指标真实性：如果文中没有计算出具体的数值，严禁编造数字。
3. 方法定性：如果作者通过人工阅读进行分类，method_name 必须标记为 "Manual Expert Review"。
4. 宁缺毋滥：如果某一步骤的信息不全，宁可字段留空，也不要生成虚假信息。

# Ontology (本体词表)

## 1. [数据集来源] (dataset_sources) ✨ 新增
[
    "USPTO (美国专利商标局)",
    "EPO (欧洲专利局)",
    "JPO (日本特许厅)",
    "CNIPA / SIPO (中国国家知识产权局)",
    "WIPO / PCT (世界知识产权组织)",
    "Derwent Innovation Index",
    "Google Patents",
    "PatSnap",
    "Orbit Intelligence",
    "Web of Science (WOS)",
    "Scopus",
    "PubMed",
    "arXiv",
    "公司财报数据库",
    "股票市场数据库",
    "其他 (请在 notes 中说明)"
]

## 2. [数据字段] (data_fields)
# 指作者在分析步骤中作为变量"具体处理"了哪些字段
[
    # --- 核心人员与机构 ---
    "申请人 / 专利权人 (Applicant / Assignee)",
    "发明人 (Inventor)",
    "代理机构 / 代理人 (Agent / Attorney)",
    # --- 时间与编号 ---
    "申请日 (Application Date)",
    "公开日 (Publication Date)",
    "授权日 (Grant Date)",
    "优先权日 (Priority Date)",
    "申请号 (Application Number)",
    "公开号 (Publication Number)",
    "授权号 (Grant Number)",
    # --- 技术分类 ---
    "IPC (国际专利分类号)",
    "CPC (合作专利分类号)",
    "USPC (美国专利分类号)",
    "FI / F-Term (日本专利分类)",
    # --- 文本内容 ---
    "标题 (Title)",
    "摘要 (Abstract)",
    "权利要求 (Claims)",
    "独立权利要求 (Independent Claims)",
    "从属权利要求 (Dependent Claims)",
    "说明书 (Description / Specification)",
    "数据库关键词 (Keywords / Keywords Plus)",
    # --- 引文与网络 ---
    "后向引文 / 专利引用 (Backward Citations)",
    "前向引文 / 被引 (Forward Citations)",
    "非专利引文 (Non-Patent Literature / NPL)",
    # --- 家族与布局 ---
    "专利家族 (Patent Family)",
    "简单家族 (Simple Family)",
    "扩展家族 (Extended Family)",
    "家族大小 (Family Size)",
    "申请国家 / 专利局 (Assignee Country / Office)",
    # --- 法律与价值 ---
    "法律状态 (Legal Status)",
    "法律事件 (Legal Events)",
    "转让信息 (Assignment Information)",
    "专利类型 (Patent Type)"
]

## 3. [核心算法/方法] (method_name)
[
    # --- 计量与统计 ---
    "HHI / CRn (市场集中度)", "TCT (技术生命周期)", "TLC (S曲线/技术寿命)",
    "CPP / PII (引文影响指数)", "RCA (显示性比较优势)", "Growth Rate (增长率)",
    "回归分析 (Regression Analysis)", "Granger因果检验",
    # --- 文本挖掘 & NLP ---
    "TF-IDF", "LDA (主题模型)", "LSA/LSI", "BERTopic",
    "Word2Vec", "Doc2Vec", "BERT/Transformer", "SAO结构分析",
    "NER (命名实体识别)", "K-Means (文本聚类)",
    # --- 网络与降维 ---
    "SNA (社会网络分析)", "K-Core分解", "Louvain社区发现", "主路径分析 (Main Path)",
    "PCA (主成分分析)", "MDS (多维尺度)", "t-SNE", "VOSviewer布局",
    # --- 其他常用方法 ---
    "IPC/CPC共现分析 (Classification Co-occurrence)",
    "申请人/发明人合作网络 (Collaboration Network)",
    "引文分析 (Citation Analysis)",
    "统计分析 (Statistical Analysis)",
    "专利地图 / 可视化 (Patent Mapping/Visualization)",
    "Manual Expert Review (人工专家审查)"
]

## 4. [评估指标] (metric_names)
[
    "R-Squared", "P-value", "F1-Score", "Accuracy", "Coherence Score (一致性)",
    "Perplexity (困惑度)", "Silhouette Score (轮廓系数)", "Modularity (模块度)",
    "TCT Value (周期年数)", "HHI Value (指数值)", "Correlation Coefficient (相关系数)",
    "Growth Rate (%)", "Precision", "Recall", "AUC"
]

## 5. [输出结果: 研究结论] (conclusions)
[
    "技术趋势（上升/快速发展）",
    "技术趋势（下降/衰退）",
    "技术空白（已识别）",
    "方法有效性（已验证）",
    "正相关性（已发现）",
    "负相关性（已发现）",
    "关键参与者/核心技术（已识别）",
    "技术融合现象（已证实）",
    "市场垄断/集中（已证实）"
]

# Output Format (输出格式) ✨ 新增 datasets 字段

{{
  "paper_meta": {{
    "title": "...", 
    "year": "..."
  }},
  
  "datasets": [
    {{
      "dataset_id": "D1",
      "name": "数据集的简短名称（如 'USPTO Patents 2010-2020'）",
      "source": "数据来源（从本体选，如 'USPTO'）",
      "query_condition": "检索条件（如 '关键词: solid-state battery; IPC: H01M'）",
      "size": "数据规模（如 '5,000 patents', '1,200 papers'）",
      "time_range": "时间范围（如 '2010-2020'）",
      "preprocessing": "预处理步骤（如 '去重、清洗、过滤非英文'）",
      "notes": "其他说明"
    }}
  ],
  
  "analysis_logic_chains": [
    {{
      "step_id": 1,
      "objective": "该步骤的具体分析目的",
      
      "dataset_used": "使用的数据集ID（如 'D1'，对应 datasets 数组）",
      
      "method_name": "标准算法名 (从本体选)",
      
      "implementation_config": {{
          "library": "使用的工具或库。若未提及填 null。",
          "parameters": {{
              "key": "value"
          }},
          "notes": "其他实施细节描述。"
      }},
      
      "data_fields_used": ["使用了哪些数据字段 (从本体选)"],
      
      "evaluation_metrics": [
          {{
              "metric_name": "指标名称",
              "metric_value": "具体的数值结果",
              "significance": "该数值说明了什么？"
          }}
      ],
      
      "derived_conclusion": "该步骤最终导出的定性结论。"
    }}
  ]
}}

# Examples (示例 - Few-Shot)

## 示例 1: 包含数据集信息的完整案例
### Input:
"We retrieved 5,000 solid-state battery patents from USPTO (2010-2020) using the keyword 'solid-state battery' and IPC code H01M. After removing duplicates and non-English patents, we applied LDA (K=50) to identify technology topics. The coherence score was 0.58."

### Output JSON:
{{
  "paper_meta": {{
    "title": "Solid-State Battery Technology Analysis",
    "year": "2023"
  }},
  
  "datasets": [
    {{
      "dataset_id": "D1",
      "name": "USPTO Solid-State Battery Patents 2010-2020",
      "source": "USPTO (美国专利商标局)",
      "query_condition": "关键词: solid-state battery; IPC: H01M",
      "size": "5,000 patents",
      "time_range": "2010-2020",
      "preprocessing": "去重、过滤非英文专利",
      "notes": "初始检索结果可能更多，经过清洗后得到5000件"
    }}
  ],
  
  "analysis_logic_chains": [
    {{
      "step_id": 1,
      "objective": "识别固态电池技术主题",
      "dataset_used": "D1",
      "method_name": "LDA (主题模型)",
      "implementation_config": {{
          "library": "Gensim (推测)",
          "parameters": {{
              "num_topics": 50
          }},
          "notes": "未明确说明库，但LDA常用Gensim实现"
      }},
      "data_fields_used": ["摘要 (Abstract)", "权利要求 (Claims)"],
      "evaluation_metrics": [
          {{
              "metric_name": "Coherence Score",
              "metric_value": "0.58",
              "significance": "主题划分具有较高的语义连贯性"
          }}
      ],
      "derived_conclusion": "成功识别出50个核心技术主题"
    }}
  ]
}}

# Input Data (待分析摘要)
{text}

请严格按照以上JSON格式输出，不要包含任何其他内容。
    """
    
    # ... (后续代码保持不变)
