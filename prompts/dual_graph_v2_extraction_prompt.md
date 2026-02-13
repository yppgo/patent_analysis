# Dual Graph v2 Extraction Prompt (Claude PDF)

You are a patent scientometrics + causal inference + methodology specialist.

You will be given ONE PDF paper. Your task is to extract a **dual_graph_v2 delta** as a SINGLE valid JSON object.

## ⚠️ CRITICAL: Variable Mapping Rules (MUST FOLLOW)

**PRIMARY RULE: You MUST map ALL variables to V01-V33 before creating new variables.**

1. **First Priority**: Map to V01-V30 (standard patent analysis variables)
2. **Second Priority**: Use V31-V33 (interface variables) when relevant
3. **Last Resort**: Only create V34+ variables if NO mapping is possible after careful consideration

**Mapping Process:**
- Read the paper carefully
- For each concept mentioned, check if it matches V01-V33 semantically
- Use abstract/general concepts from V01-V33, not specific technical details
- Only create V34+ if the concept is truly domain-specific and cannot be abstracted

## Standard Variables (V01-V30) - MUST USE THESE FIRST

### Input Variables (V01-V08)
- **V01_tech_intensity**: 技术投入强度 - Patent output scale in a specific technology field
- **V02_firm_size**: 企业规模 - Total patents of applicant (cross-domain)
- **V03_rd_investment**: 研发投资强度 - R&D expenditure as % of revenue
- **V04_international_collab**: 国际合作强度 - Ratio of patents with foreign inventors
- **V05_university_collab**: 产学研合作 - Ratio of patents with universities/research institutes
- **V06_prior_experience**: 先验经验 - Historical patent count of applicant in the field
- **V07_policy_support**: 政策支持 - Ratio of patents with government funding
- **V08_market_competition**: 市场竞争强度 - Number of applicants (HHI index)

### Mediator Variables (V09-V15)
- **V09_tech_diversity**: 技术跨界度 - Diversity of IPC classifications (Shannon entropy)
- **V10_science_linkage**: 科学关联度 - Ratio of non-patent literature (NPL) citations
- **V11_knowledge_recombination**: 知识重组度 - Ratio of new IPC combinations
- **V12_tech_cycle_time**: 技术迭代速度 - Average age of cited patents (TCT)
- **V13_rd_efficiency**: 研发效率 - Patents per inventor (output per input)
- **V14_tech_breadth**: 技术广度 - Number of IPC classes covered
- **V15_tech_depth**: 技术深度 - Concentration of patents in main IPC class

### Outcome Variables (V16-V21, V26, V28, V30)
- **V16_tech_impact**: 技术影响力 - Forward citations count
- **V17_tech_breakthrough**: 技术突破性 - Disruptive index (CD Index)
- **V18_tech_independence**: 技术独立性 - Ratio of domestic citations
- **V19_commercial_value**: 商业价值 - Patent maintenance years
- **V20_market_share**: 市场份额 - Applicant's patent share in the field
- **V21_licensing_revenue**: 许可收益 - Licensing and transfer income
- **V26_catching_up**: 技术追赶能力 - Catch-up performance of latecomers
- **V28_tech_convergence**: 技术融合度 - Convergence degree across technology fields
- **V30_tech_novelty**: 技术新颖度 - Novelty score based on citation patterns

### Moderator Variables (V22-V25)
- **V22_tech_maturity**: 技术成熟度 - Patent growth rate (last 5 years)
- **V23_industry_type**: 产业类型 - High-tech/traditional industry classification
- **V24_firm_type**: 组织类型 - Firm/university/research institute/individual
- **V25_geographic_location**: 地理位置 - Applicant's country/region

### Additional Mediator Variables (V27, V29)
- **V27_tacit_knowledge**: 隐性知识 - Ratio of hard-to-codify knowledge
- **V29_knowledge_spillover**: 知识溢出 - Diffusion degree to other entities/fields

## Interface Variables (V31-V33) - Use When Relevant

- **V31_Methodology_Interface** (type=method): Links causal graph to method graph
- **V32_Data_Constraint** (type=resource): Data granularity/constraints (e.g., CPC vs IPC)
- **V33_External_Validation** (type=context): External validation standards (e.g., clinical validation)

## Variable Mapping Guide (IMPORTANT!)

**When you encounter these concepts, map them to:**

- **Latency/delay/time intervals** → V12_tech_cycle_time (技术迭代速度)
- **Error rate/reliability** → V16_tech_impact (技术影响力) or V19_commercial_value (商业价值)
- **Scheduling/access methods** → V09_tech_diversity (技术跨界度) or V11_knowledge_recombination (知识重组度)
- **Coding/encoding parameters** → V09-V15 (mediator variables, as technical mechanisms)
- **Multi-point/network configurations** → V14_tech_breadth (技术广度) or V28_tech_convergence (技术融合度)
- **Technology integration** → V28_tech_convergence (技术融合度)
- **Performance metrics** → V16_tech_impact (技术影响力) or V19_commercial_value (商业价值)
- **Technical mechanisms** → V09-V15 (mediator variables)
- **Resource constraints** → V32_Data_Constraint (if data-related) or V01_tech_intensity (if resource-related)

**Examples:**
- "TTI (Transmission Time Interval)" → V12_tech_cycle_time (time-related mechanism)
- "HARQ feedback latency" → V12_tech_cycle_time (latency = time-related)
- "Block Error Rate (BLER)" → V16_tech_impact (reliability = impact dimension)
- "Grant-free scheduling" → V09_tech_diversity or V11_knowledge_recombination (scheduling method = mechanism)
- "TSN integration" → V28_tech_convergence (integration = convergence)
- "End-to-end latency" → V12_tech_cycle_time (latency = time-related)

## Output rules (strict)
- Output MUST be valid JSON (no markdown fences, no commentary).
- Do NOT invent numeric results. If not stated, use `null` or omit optional subfields.
- **MUST map to V01-V33 first**. Only create V34+ if truly impossible to map.
- New variables must start at `V34_...` (e.g. `V34_data_granularity`) ONLY if no V01-V33 match exists.
- New methods must use `M_` prefix (e.g. `M_DL_clustering`).
- Pipelines must use `PPL_` prefix (e.g. `PPL_Granularity_Cluster_Eval`).

## Required output schema (top-level)
{
  "paper_meta": { ... },
  "graph_A_delta": {
    "variables": [ ... ],
    "causal_edges": [ ... ],
    "complex_relations": [ ... ]
  },
  "graph_B_delta": {
    "methods": [ ... ],
    "pipelines": [ ... ]
  }
}

## paper_meta
{
  "title": "paper title",
  "year": 2016,
  "domain": "ICT/Clean Energy/Biotech/Automotive/Materials/General",
  "doi": "10.xxxx/xxxxx" | null
}

## Graph A v2: variables
Each variable:
{
  "id": "V12_tech_cycle_time",  // MUST use V01-V33 first!
  "label": "技术迭代速度",
  "type": "resource|mechanism|performance|context|method",
  "definition": "short definition",
  "measurement": {
    "metric": "optional metric name" | null,
    "formula": "optional formula" | null,
    "unit": "optional unit" | null
  },
  "source": ["paper title"],
  "tags": ["optional", "keywords"]
}

**⚠️ CRITICAL: Variable Definition Rules**
- **Variables are conceptual** - they describe "what" not "how to calculate"
- **DO NOT include metadata_fields** in variable definition (metadata fields belong in Graph B measurement methods)
- **measurement.formula** provides conceptual measurement approach (e.g., "Shannon Entropy"), but does NOT specify which metadata fields to use
- **One variable can have multiple measurement methods** in Graph B, each using different metadata fields

**Note on type mapping:**
- V01-V08 (input) → type="resource"
- V09-V15, V27, V29 (mediator) → type="mechanism"
- V16-V21, V26, V28, V30 (outcome) → type="performance"
- V22-V25 (moderator) → type="context"
- V31-V33 (interface) → use specified types

## Graph A v2: causal_edges (direct effects)
Each edge:
{
  "edge_id": "E001",
  "source": "Vxx_xxx",
  "target": "Vyy_yyy",
  "effect_type": "positive|negative|inverted_u|threshold|unknown",
  "effect_size": "small|medium|large|theoretical|unknown",
  "mechanism": "one-sentence mechanism" | null,
  "evidence": {
    "validated": true|false,
    "evidence_count": 1,
    "papers": ["paper title"],
    "sample_quotes": ["verbatim quote(s) that justify the relation"],
    "domains": ["ICT"]
  },
  "interfaces": {
    "method_bridge": {
      "used": true|false,
      "specific_method_key": "M_xxx or short key like DL_clustering" | null,
      "link_to_method_graph": true|false
    },
    "data_constraint": {
      "used": true|false,
      "specific_constraint": "e.g., CPC vs IPC granularity" | null,
      "link_var_id": "V32_Data_Constraint"
    },
    "external_validation": {
      "used": true|false,
      "specific_standard": "e.g., clinical validation" | null,
      "link_var_id": "V33_External_Validation"
    }
  }
}

## Graph A v2: complex_relations (mediation/moderation/interaction)
Use this unified representation:

- mediation:
{
  "id": "CR001",
  "type": "mediation",
  "pattern": { "source": "V_A", "mediator": "V_M", "target": "V_B" },
  "evidence": { "papers": ["paper title"], "description": "A affects B via M" }
}

- moderation:
{
  "id": "CR002",
  "type": "moderation",
  "pattern": { "source": "V_A", "moderator": "V_Z", "target": "V_B" },
  "evidence": { "papers": ["paper title"], "description": "Z moderates A -> B" }
}

- interaction:
{
  "id": "CR003",
  "type": "interaction",
  "pattern": { "sources": ["V_A", "V_Z"], "target": "V_B" },
  "evidence": { "papers": ["paper title"], "description": "A and Z interactively affect B" }
}

## Graph B v2: methods (HIGH-LEVEL ONLY, PATENT / STATISTICAL METHODS)

You MUST extract only methods that are about **patent data analysis / scientometrics / empirical statistics on data**.

Good scope for methods:
- **Measurement methods**: how to compute V09, V12, V16, etc. from patent / bibliometric data
  - e.g., "IPC entropy calculation", "patent age calculation", "forward citation count", "co-classification network construction"
- **Analysis methods**: statistical / ML models applied on variables (regression, mediation/moderation analysis, clustering, topic modeling, network analysis, time series, panel models, etc.)
- **Preprocessing methods**: text preprocessing, feature engineering, dimensionality reduction, normalization, etc.

Out of scope (MUST NOT become methods in Graph B):
- **Engineering / protocol / system design tricks**, such as:
  - "HARQ optimization", "grant-free scheduling configuration", "TTI value tuning", "TSN queueing design"
  - Any 5G/URLLC physical layer or MAC layer mechanism design
- Vendor-specific implementation details
- Very narrow, one-off engineering tweaks

For these out-of-scope items:
- Encode their effects ONLY via:
  - `graph_A_delta.variables` (e.g., latency, reliability, integration level)
  - `graph_A_delta.causal_edges[*].mechanism` / `sample_quotes` / `tags`
- **Do NOT** create a `methods[*]` node for them.

Each method node in Graph B should:
- Be reusable across many different papers and domains
- Describe a general data/statistical method or workflow, not a protocol-level engineering solution

Each method (high-level template):
{
  "id": "M_regression_quadratic",            // method family / template
  "name": "Quadratic Regression for Nonlinear Effects",
  "family": "regression|topic_modeling|classification|network_analysis|time_series|causal_inference|clustering|preprocessing|other",
  "category": "measurement_method|analysis_method|preprocessing",
  "description": "how the paper uses this GENERAL method family (not low-level engineering tweaks)",
  "metadata_fields_required": ["IPC分类号"],  // ⚠️ CRITICAL: 
  // - For measurement_method: MUST list patent metadata columns needed (e.g., ["IPC分类号", "授权日"])
  // - For analysis_method: usually empty [] (because input is variables, not metadata)
  // Common patent metadata fields: "序号", "公开(公告)号", "授权日", "申请日", "IPC分类号", "CPC分类号",
  //   "申请(专利权)人", "发明人", "被引用专利数量", "引用专利数量", "名称", "摘要", etc.
  "applicable_variables": {
    "input_vars": ["V09_tech_diversity", "V22_tech_maturity"],   // For analysis_method: which variables are needed
    "output_vars": ["V16_tech_impact"],                           // For measurement_method: which variable(s) this calculates (usually ONE)
    "constraint_vars": ["V32_Data_Constraint"],
    "performance_vars": ["V16_tech_impact", "V19_commercial_value"]
  },
  "implementation": {
    "pseudo_code": "optional HIGH-LEVEL steps, e.g., fit y ~ x + x^2 + controls",
    "formula": "optional formula, e.g., Shannon Entropy = -SUM(p_i * log(p_i))",  // For measurement_method: calculation formula
    "libraries": ["optional, e.g., statsmodels", "sklearn"],
    "typical_parameters": { "example_param": "example_value" }   // can include paper-specific settings here
  },
  "evidence": {
    "papers": ["paper title"],
    "domains": ["ICT"]
  },
  "synonyms": ["nonlinear_regression", "quadratic_model"]
}

## Graph B v2: pipelines (optional, HIGH-LEVEL WORKFLOWS)

Only if the paper clearly describes a **generalizable multi-step workflow** (not just one-off engineering steps).

Good examples:
- "Variable construction → descriptive statistics → regression analysis → robustness checks"
- "Text preprocessing → topic modeling → network construction → centrality analysis"

Bad examples (do NOT create pipelines for these):
- "Tune TTI from 1ms to 0.125ms"
- "Set HARQ repetition = 3"

Pipeline:
{
  "id": "PPL_Variable_Reg_Robustness",
  "name": "Variable Construction and Regression Analysis Pipeline",
  "steps": [
    { "order": 1, "method_id": "M_variable_construction", "description": "Construct V09, V12, V16 from raw patent data" },
    { "order": 2, "method_id": "M_regression_quadratic", "description": "Estimate nonlinear effects with control variables" },
    { "order": 3, "method_id": "M_robustness_checks", "description": "Run robustness checks such as subsample analysis or alternative measures" }
  ],
  "related_causal_edges": ["E001"]
}
