# 方法图谱重构提取方案

## 📋 目标

从50篇专利分析文献中提取**假设验证所需的方法知识**，构建适配因果推断任务的方法图谱。

---

## 📊 输入数据

### 输入1：文献PDF文件
**位置**：`batch_50_results/`
**数量**：50篇
**格式**：PDF文件 + 已有的JSON分析结果

### 输入2：因果图谱变量
**位置**：`sandbox/static/data/causal_ontology_extracted.json`
**内容**：30个变量定义
**示例**：
```json
{
  "id": "V09_tech_diversity",
  "label": "技术跨界度",
  "category": "mediator",
  "definition": "专利涉及的IPC分类的多样性",
  "measurement": {
    "metric": "ipc_entropy",
    "formula": "Shannon Entropy = -SUM(p_i * log(p_i))",
    "unit": "熵值"
  }
}
```

---

## 🎯 输出数据结构

### 输出1：变量测量方法（JSON）

**文件**：`outputs/variable_measurement_methods.json`

**结构**：
```json
{
  "meta": {
    "extraction_date": "2026-01-19",
    "source_papers": 50,
    "total_variables": 30,
    "extracted_methods": 25
  },
  "measurements": [
    {
      "variable_id": "V09_tech_diversity",
      "variable_name": "技术跨界度",
      "measurement_methods": [
        {
          "method_id": "M001",
          "method_name": "Shannon Entropy",
          "usage_frequency": 0.60,
          "recommendation_level": "推荐",
          "recommendation_reason": "最常用方法，理论基础扎实，考虑分布均匀性",
          "description": "计算IPC分类的信息熵来衡量技术多样性",
          "formula": "-SUM(p_i * log(p_i))",
          "formula_explanation": "p_i是第i个IPC类别的专利占比",
          "data_requirements": [
            {
              "data_type": "IPC分类号",
              "data_format": "字符串，分号分隔",
              "example": "G06F17/30; H04L29/06",
              "excel_column_candidates": [
                "IPC主分类号",
                "IPC分类号",
                "技术分类"
              ]
            }
          ],
          "calculation_steps": [
            "1. 提取IPC大类（前4位字符）",
            "2. 统计每个大类的专利数量",
            "3. 计算每个大类的占比 p_i",
            "4. 应用Shannon熵公式：-SUM(p_i * log2(p_i))"
          ],
          "python_implementation": {
            "library": "scipy.stats",
            "function": "entropy",
            "code_snippet": "from scipy.stats import entropy\nimport pandas as pd\n\ndef calculate_ipc_entropy(ipc_string):\n    if pd.isna(ipc_string):\n        return 0\n    ipc_classes = [ipc[:4] for ipc in str(ipc_string).split(';')]\n    class_counts = pd.Series(ipc_classes).value_counts()\n    probabilities = class_counts / class_counts.sum()\n    return entropy(probabilities, base=2)"
          },
          "evidence": {
            "paper_count": 14,
            "key_papers": [
              "Fleming (2001) - Recombinant uncertainty in technological search",
              "Verhoeven et al. (2016) - Measuring technological novelty"
            ],
            "citation_context": "技术多样性通常使用IPC分类的Shannon熵来测量"
          },
          "validation": {
            "typical_range": [0, 3.5],
            "interpretation": "值越大表示技术越多样化",
            "quality_check": "检查是否有异常高值（>4）或负值"
          }
        },
        {
          "method_id": "M002",
          "method_name": "IPC类别计数",
          "usage_frequency": 0.30,
          "recommendation_level": "备选",
          "recommendation_reason": "简单快速，适合初步分析或数据不完整时使用",
          "description": "简单计数专利涉及的IPC大类数量",
          "formula": "COUNT(DISTINCT IPC_class)",
          "data_requirements": [
            {
              "data_type": "IPC分类号",
              "data_format": "字符串，分号分隔",
              "example": "G06F17/30; H04L29/06"
            }
          ],
          "calculation_steps": [
            "1. 提取IPC大类（前4位）",
            "2. 去重",
            "3. 计数"
          ],
          "python_implementation": {
            "code_snippet": "def count_ipc_classes(ipc_string):\n    if pd.isna(ipc_string):\n        return 0\n    ipc_classes = set([ipc[:4] for ipc in str(ipc_string).split(';')])\n    return len(ipc_classes)"
          },
          "evidence": {
            "paper_count": 8,
            "key_papers": ["Lerner (1994)"]
          }
        },
        {
          "method_id": "M002b",
          "method_name": "Herfindahl指数 (HHI)",
          "usage_frequency": 0.10,
          "recommendation_level": "可选",
          "recommendation_reason": "经济学视角，与Shannon熵高度相关",
          "description": "使用Herfindahl指数衡量技术集中度（1-HHI即为多样性）",
          "formula": "1 - SUM(p_i^2)",
          "data_requirements": [
            {
              "data_type": "IPC分类号",
              "data_format": "字符串，分号分隔"
            }
          ],
          "python_implementation": {
            "code_snippet": "def calculate_hhi_diversity(ipc_string):\n    if pd.isna(ipc_string):\n        return 0\n    ipc_classes = [ipc[:4] for ipc in str(ipc_string).split(';')]\n    class_counts = pd.Series(ipc_classes).value_counts()\n    probabilities = class_counts / class_counts.sum()\n    hhi = (probabilities ** 2).sum()\n    return 1 - hhi  # 多样性 = 1 - 集中度"
          },
          "evidence": {
            "paper_count": 5,
            "key_papers": ["Jaffe (1986)"]
          }
        }
      ],
      "default_method": "M001",
      "method_selection_logic": {
        "default": "M001",
        "if_data_incomplete": "M002",
        "if_quick_analysis": "M002",
        "if_economic_perspective": "M002b"
      },
      "method_comparison": {
        "correlation_matrix": {
          "M001_vs_M002": 0.85,
          "M001_vs_M002b": 0.92,
          "M002_vs_M002b": 0.78
        },
        "pros_cons": {
          "M001": {
            "pros": ["理论严谨", "考虑分布", "文献支持多"],
            "cons": ["计算复杂", "需要完整数据"]
          },
          "M002": {
            "pros": ["简单直观", "计算快速", "数据要求低"],
            "cons": ["不考虑分布", "信息损失"]
          },
          "M002b": {
            "pros": ["经济学常用", "与熵值相关"],
            "cons": ["使用较少", "解释性不如熵"]
          }
        }
      }
    },
    {
      "variable_id": "V16_tech_impact",
      "variable_name": "技术影响力",
      "measurement_methods": [
        {
          "method_id": "M003",
          "method_name": "前向引用计数",
          "description": "统计专利被后续专利引用的次数",
          "formula": "COUNT(forward_citations)",
          "data_requirements": [
            {
              "data_type": "被引用专利数量",
              "data_format": "整数",
              "example": "15",
              "excel_column_candidates": [
                "被引用专利数量",
                "前向引用",
                "引用次数",
                "forward_citations"
              ]
            }
          ],
          "calculation_steps": [
            "1. 直接读取被引用数量字段",
            "2. 处理缺失值（填充为0）",
            "3. 可选：按申请年份标准化"
          ],
          "python_implementation": {
            "code_snippet": "def get_forward_citations(df):\n    return df['被引用专利数量'].fillna(0).astype(int)"
          },
          "evidence": {
            "paper_count": 35,
            "key_papers": [
              "Trajtenberg (1990) - A penny for your quotes",
              "Hall et al. (2005) - Market value and patent citations"
            ]
          },
          "validation": {
            "typical_range": [0, 100],
            "interpretation": "值越大表示技术影响力越大",
            "quality_check": "检查异常高值（>500）"
          }
        }
      ]
    }
  ]
}
```

### 输出2：统计分析方法（JSON）

**文件**：`outputs/statistical_analysis_methods.json`

**结构**：
```json
{
  "meta": {
    "extraction_date": "2026-01-19",
    "source_papers": 50,
    "total_methods": 15
  },
  "analysis_methods": [
    {
      "method_id": "A001",
      "method_name": "OLS回归分析",
      "method_type": "regression",
      "description": "普通最小二乘回归，用于检验自变量对因变量的影响",
      "applicable_scenarios": [
        "单跳假设验证（X → Y）",
        "控制变量分析",
        "线性关系检验"
      ],
      "formula": "Y = β0 + β1*X + β2*Control1 + β3*Control2 + ε",
      "assumptions": [
        "线性关系",
        "残差正态分布",
        "同方差性",
        "无多重共线性"
      ],
      "python_implementation": {
        "library": "statsmodels",
        "code_template": "import statsmodels.api as sm\n\n# 准备数据\nX = df[['independent_var', 'control1', 'control2']]\nX = sm.add_constant(X)  # 添加常数项\ny = df['dependent_var']\n\n# 拟合模型\nmodel = sm.OLS(y, X).fit()\n\n# 查看结果\nprint(model.summary())\n\n# 提取关键指标\ncoef = model.params['independent_var']  # 回归系数\np_value = model.pvalues['independent_var']  # p值\nr_squared = model.rsquared  # R²\n\n# 判断假设是否成立\nif p_value < 0.05 and coef > 0:\n    print('假设成立：X对Y有显著正向影响')"
      },
      "output_interpretation": {
        "coefficient": "回归系数，表示X每增加1个单位，Y平均变化多少",
        "p_value": "显著性水平，<0.05表示显著，<0.01表示高度显著",
        "r_squared": "解释力，表示X解释了Y多少百分比的变异",
        "confidence_interval": "95%置信区间，不包含0则显著"
      },
      "evidence": {
        "paper_count": 42,
        "usage_frequency": "84%",
        "key_papers": [
          "大部分实证研究论文"
        ]
      },
      "common_controls": [
        "申请年份（控制时间趋势）",
        "企业规模（控制规模效应）",
        "技术领域（控制行业差异）"
      ]
    },
    {
      "method_id": "A002",
      "method_name": "中介效应检验",
      "method_type": "mediation",
      "description": "检验X通过M影响Y的中介机制",
      "applicable_scenarios": [
        "多跳假设验证（X → M → Y）",
        "机制探索",
        "路径分析"
      ],
      "steps": [
        "Step 1: 检验 X → Y 的总效应（c路径）",
        "Step 2: 检验 X → M 的效应（a路径）",
        "Step 3: 检验 M → Y 的效应（b路径），控制X",
        "Step 4: 检验 X → Y 的直接效应（c'路径），控制M",
        "Step 5: 计算中介效应 = a × b"
      ],
      "python_implementation": {
        "library": "statsmodels + custom",
        "code_template": "import statsmodels.api as sm\nimport numpy as np\n\n# Step 1: 总效应 (c)\nX = sm.add_constant(df['X'])\ny = df['Y']\nmodel_c = sm.OLS(y, X).fit()\nc = model_c.params['X']\n\n# Step 2: a路径 (X → M)\nm = df['M']\nmodel_a = sm.OLS(m, X).fit()\na = model_a.params['X']\n\n# Step 3: b路径 (M → Y, 控制X)\nX_M = sm.add_constant(df[['X', 'M']])\nmodel_b = sm.OLS(y, X_M).fit()\nb = model_b.params['M']\nc_prime = model_b.params['X']  # 直接效应\n\n# Step 4: 计算中介效应\nindirect_effect = a * b\nmediation_ratio = indirect_effect / c\n\nprint(f'总效应: {c:.3f}')\nprint(f'直接效应: {c_prime:.3f}')\nprint(f'中介效应: {indirect_effect:.3f}')\nprint(f'中介比例: {mediation_ratio:.1%}')\n\n# Sobel检验\nse_indirect = np.sqrt(b**2 * model_a.bse['X']**2 + a**2 * model_b.bse['M']**2)\nz_score = indirect_effect / se_indirect\np_value = 2 * (1 - stats.norm.cdf(abs(z_score)))\n\nif p_value < 0.05:\n    print('中介效应显著')"
      },
      "evidence": {
        "paper_count": 12,
        "key_papers": [
          "Baron & Kenny (1986) - The moderator-mediator variable distinction"
        ]
      }
    },
    {
      "method_id": "A003",
      "method_name": "调节效应检验",
      "method_type": "moderation",
      "description": "检验M如何调节X对Y的影响",
      "applicable_scenarios": [
        "边界条件探索",
        "交互效应检验",
        "情境因素分析"
      ],
      "formula": "Y = β0 + β1*X + β2*M + β3*X*M + ε",
      "python_implementation": {
        "code_template": "import statsmodels.api as sm\n\n# 创建交互项\ndf['X_M_interaction'] = df['X'] * df['M']\n\n# 回归分析\nX = sm.add_constant(df[['X', 'M', 'X_M_interaction']])\ny = df['Y']\nmodel = sm.OLS(y, X).fit()\n\n# 查看交互项系数\ninteraction_coef = model.params['X_M_interaction']\ninteraction_p = model.pvalues['X_M_interaction']\n\nif interaction_p < 0.05:\n    print(f'调节效应显著: β3 = {interaction_coef:.3f}, p = {interaction_p:.3f}')\n    \n    # 简单斜率分析\n    m_low = df['M'].quantile(0.25)\n    m_high = df['M'].quantile(0.75)\n    \n    slope_low = model.params['X'] + model.params['X_M_interaction'] * m_low\n    slope_high = model.params['X'] + model.params['X_M_interaction'] * m_high\n    \n    print(f'M低时，X对Y的影响: {slope_low:.3f}')\n    print(f'M高时，X对Y的影响: {slope_high:.3f}')"
      },
      "evidence": {
        "paper_count": 8,
        "key_papers": [
          "Aiken & West (1991) - Multiple regression"
        ]
      }
    }
  ]
}
```

### 输出3：Neo4j导入脚本

**文件**：`scripts/import_method_graph_v2.py`

**功能**：将JSON数据导入Neo4j，构建新的图谱结构

**图谱结构**：
```
Variable --[HAS_MEASUREMENT]--> MeasurementMethod --[REQUIRES_DATA]--> DataField
Variable --[CAN_BE_ANALYZED_BY]--> AnalysisMethod
Hypothesis --[USES_VARIABLE]--> Variable
Hypothesis --[REQUIRES_ANALYSIS]--> AnalysisMethod
```

---

## 🔧 提取流程

### Step 1：设计提取Prompt

**文件**：`prompts/extract_measurement_methods.txt`

```
你是一个专利分析方法提取专家。请从以下论文中提取变量测量方法。

论文标题：{paper_title}
论文内容：{paper_content}

目标变量列表：
{variable_list}

请提取以下信息：

1. 变量测量方法
   - 变量名称
   - 测量指标
   - 计算公式
   - 数据来源
   - 计算步骤

2. 统计分析方法
   - 方法名称
   - 适用场景
   - 公式
   - 实现步骤

输出格式：JSON
{output_schema}
```

### Step 2：批量提取

**脚本**：`scripts/extract_methods_batch.py`

**伪代码**：
```python
import json
from pathlib import Path
import anthropic

# 1. 加载变量列表
with open('sandbox/static/data/causal_ontology_extracted.json') as f:
    ontology = json.load(f)
    variables = ontology['variables']

# 2. 加载已分析的论文
paper_results = list(Path('batch_50_results').glob('*_analysis_result.json'))

# 3. 初始化Claude
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# 4. 批量提取
all_measurements = []
all_analysis_methods = []

for paper_file in paper_results:
    with open(paper_file) as f:
        paper_data = json.load(f)
    
    # 构建prompt
    prompt = build_extraction_prompt(paper_data, variables)
    
    # 调用Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # 解析结果
    extracted = json.loads(response.content[0].text)
    all_measurements.extend(extracted['measurements'])
    all_analysis_methods.extend(extracted['analysis_methods'])
    
    print(f"✓ 处理完成: {paper_file.name}")

# 5. 合并和去重（处理多种方法）
merged_measurements = merge_measurements_with_ranking(all_measurements)
merged_methods = merge_methods(all_analysis_methods)

def merge_measurements_with_ranking(all_measurements):
    """
    合并同一变量的多种测量方法，并计算使用频率和推荐优先级
    """
    # 按变量分组
    by_variable = {}
    for m in all_measurements:
        var_id = m['variable_id']
        if var_id not in by_variable:
            by_variable[var_id] = []
        by_variable[var_id].append(m)
    
    # 处理每个变量
    result = []
    for var_id, methods in by_variable.items():
        # 按方法名称分组（同一方法可能被多篇论文使用）
        by_method_name = {}
        for m in methods:
            method_name = m['method_name']
            if method_name not in by_method_name:
                by_method_name[method_name] = {
                    'method': m,
                    'paper_count': 0,
                    'papers': []
                }
            by_method_name[method_name]['paper_count'] += 1
            by_method_name[method_name]['papers'].append(m.get('paper_title'))
        
        # 计算使用频率
        total_papers = len(paper_results)
        method_list = []
        for method_name, info in by_method_name.items():
            method = info['method']
            method['usage_frequency'] = info['paper_count'] / total_papers
            method['evidence']['paper_count'] = info['paper_count']
            method['evidence']['key_papers'] = info['papers'][:5]  # 保留前5篇
            method_list.append(method)
        
        # 按使用频率排序
        method_list.sort(key=lambda m: m['usage_frequency'], reverse=True)
        
        # 标注推荐级别
        if len(method_list) > 0:
            method_list[0]['recommendation_level'] = '推荐'
            method_list[0]['recommendation_reason'] = f"最常用方法（{method_list[0]['usage_frequency']:.0%}的论文使用）"
        if len(method_list) > 1:
            method_list[1]['recommendation_level'] = '备选'
            method_list[1]['recommendation_reason'] = f"次常用方法（{method_list[1]['usage_frequency']:.0%}的论文使用）"
        if len(method_list) > 2:
            for m in method_list[2:]:
                m['recommendation_level'] = '可选'
                m['recommendation_reason'] = f"较少使用（{m['usage_frequency']:.0%}的论文使用）"
        
        # 添加方法对比信息
        variable_entry = {
            'variable_id': var_id,
            'variable_name': methods[0]['variable_name'],
            'measurement_methods': method_list,
            'default_method': method_list[0]['method_id'] if method_list else None,
            'method_selection_logic': generate_selection_logic(method_list)
        }
        
        result.append(variable_entry)
    
    return result

# 6. 保存结果
save_json(merged_measurements, 'outputs/variable_measurement_methods.json')
save_json(merged_methods, 'outputs/statistical_analysis_methods.json')
```

### Step 3：验证和清洗

**脚本**：`scripts/validate_extracted_methods.py`

**检查项**：
1. 每个变量至少有1个测量方法
2. 公式格式正确
3. Python代码可执行
4. 数据字段名称合理
5. **使用频率总和合理**（同一变量的所有方法频率和应≈1.0）
6. **推荐级别已标注**（至少有一个"推荐"方法）
5. 文献引用完整

### Step 4：导入Neo4j

**脚本**：`scripts/import_method_graph_v2.py`

**Cypher语句示例**：
```cypher
// 创建Variable节点
CREATE (v:Variable {
  id: 'V09_tech_diversity',
  name: '技术跨界度',
  category: 'mediator'
})

// 创建MeasurementMethod节点
CREATE (m:MeasurementMethod {
  id: 'M001',
  name: 'Shannon Entropy',
  formula: '-SUM(p_i * log(p_i))',
  code: '...'
})

// 创建关系
CREATE (v)-[:HAS_MEASUREMENT]->(m)

// 创建DataField节点
CREATE (d:DataField {
  name: 'IPC主分类号',
  type: 'string',
  format: '分号分隔'
})

// 创建关系
CREATE (m)-[:REQUIRES_DATA]->(d)
```

---

## ⏱️ 时间估算

| 步骤 | 时间 | 说明 |
|------|------|------|
| 设计Prompt | 2小时 | 编写提取模板和示例 |
| 编写提取脚本 | 2小时 | 基于已有脚本修改 |
| 运行提取（50篇） | 1小时 | API调用，自动化 |
| 验证和清洗 | 3小时 | 人工检查和修正 |
| 导入Neo4j | 1小时 | 编写导入脚本 |
| 测试验证 | 2小时 | 端到端测试 |
| **总计** | **11小时** | **约1.5天** |

---

## 💰 成本估算

**Claude API调用：**
- 50篇论文 × 4000 tokens/篇 = 200K tokens输入
- 50篇论文 × 2000 tokens/篇 = 100K tokens输出
- 成本：约 $3-5

---

## ✅ 验收标准

1. **覆盖率**：30个变量中至少25个有测量方法
2. **质量**：每个方法都有公式、代码、文献支持
3. **可用性**：Python代码可以直接运行
4. **完整性**：包含数据字段映射和Excel列名
5. **可追溯**：每个方法都能追溯到原文献

---

## 🚀 下一步

提取完成后，可以：
1. 更新Strategist，使用新的方法图谱
2. 测试端到端流程
3. 生成示例研究报告
