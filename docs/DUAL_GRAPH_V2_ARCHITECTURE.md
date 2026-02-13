# Dual Graph v2 架构设计文档

## 📋 核心设计原则

### 1. 三层架构分离

```
┌─────────────────────────────────────────────────────────┐
│  因果图谱（Graph A）- 理论层                              │
│  作用：回答"为什么"（Why）                                │
│  内容：变量（V01-V33）、因果边、复杂关系                  │
│  特点：概念层，理论驱动，不关心"怎么算"                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  方法图谱（Graph B）- 方法层                              │
│  作用：回答"怎么做"（How）                                │
│  内容：测量方法、分析方法、流程                          │
│  特点：操作层，数据驱动，明确"怎么算"                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  专利元数据（原始数据表）                                 │
│  作用：提供原始数据                                       │
│  内容：IPC分类号、被引用专利数量、授权日等列             │
└─────────────────────────────────────────────────────────┘
```

### 2. 数据流设计

```
专利元数据（原始数据表）
    ↓ [测量方法]
变量（Graph A: V01-V33）
    ↓ [因果假设]
因果边（Graph A: A → B）
    ↓ [分析方法]
研究结论
```

## 🎯 Graph A（因果图谱）- 理论层

### 核心定位
- **作用**：描述"研究问题"本身
- **内容**：变量定义、因果关系、理论机制
- **特点**：概念层，不关心具体计算

### 变量定义（Variables）

```json
{
  "id": "V09_tech_diversity",
  "label": "技术跨界度",
  "type": "mechanism",
  "definition": "专利涉及的IPC分类的多样性",
  "measurement": {
    "metric": "ipc_entropy",
    "formula": "Shannon Entropy = -SUM(p_i * log(p_i))",
    "unit": "熵值"
  },
  "source": ["paper title"],
  "tags": ["diversity", "IPC"]
}
```

**关键设计决策**：
- ✅ **变量定义保持概念纯净**：只描述"是什么"，不绑定具体元数据字段
- ✅ **measurement 字段**：提供概念层面的测量方式（公式、单位），但不指定具体数据字段
- ❌ **不包含 metadata_fields**：变量不应该直接绑定元数据字段，因为一个变量可能有多种测量方法

### 因果边（Causal Edges）

```json
{
  "edge_id": "E001",
  "source": "V09_tech_diversity",
  "target": "V16_tech_impact",
  "effect_type": "positive",
  "effect_size": "medium",
  "mechanism": "技术多样性提升整体性能",
  "evidence": { ... },
  "interfaces": {
    "method_bridge": {
      "used": true,
      "specific_method_key": "M_regression_linear",
      "link_to_method_graph": true
    }
  }
}
```

**关键设计决策**：
- ✅ **method_bridge**：通过 `specific_method_key` 链接到 Graph B 的分析方法
- ✅ **不包含元数据字段**：因果边只描述变量间的关系，不关心数据来源

## 🔧 Graph B（方法图谱）- 方法层

### 核心定位
- **作用**：描述"如何解决研究问题"
- **内容**：测量方法、分析方法、流程
- **特点**：操作层，明确需要哪些数据、怎么算

### 测量方法（Measurement Methods）

**作用**：从专利元数据字段 → 计算出变量（V01-V33）

```json
{
  "id": "M_measure_V09_IPC_entropy",
  "name": "Measure V09 from IPC Entropy",
  "family": "measurement",
  "category": "measurement_method",
  "description": "Calculate V09_tech_diversity using Shannon entropy of IPC classifications",
  
  "metadata_fields_required": ["IPC分类号"],  // ⚠️ 关键：明确需要哪些元数据字段
  
  "applicable_variables": {
    "input_vars": [],                          // 测量方法通常不需要其他变量作为输入
    "output_vars": ["V09_tech_diversity"],    // 明确输出哪个变量
    "constraint_vars": [],
    "performance_vars": []
  },
  
  "implementation": {
    "pseudo_code": "1. Split IPC分类号 by '|', 2. Count IPC codes per patent, 3. Calculate Shannon entropy",
    "formula": "Shannon Entropy = -SUM(p_i * log(p_i)) where p_i = count(IPC_i) / total_IPCs",
    "libraries": ["scipy.stats.entropy", "pandas"],
    "typical_parameters": { "base": 2 }
  },
  
  "evidence": {
    "papers": ["paper title"],
    "domains": ["ICT"]
  },
  "synonyms": ["IPC_entropy", "shannon_entropy_IPC"]
}
```

**关键设计决策**：
- ✅ **metadata_fields_required**：必须明确列出需要的专利元数据字段
- ✅ **output_vars**：明确输出哪个变量（通常是一个）
- ✅ **一个变量可以有多个测量方法**：例如 V09 可以有：
  - `M_measure_V09_IPC_entropy`（需要 IPC分类号）
  - `M_measure_V09_IPC_count`（需要 IPC分类号）
  - `M_measure_V09_CPC_entropy`（需要 CPC分类号）

### 分析方法（Analysis Methods）

**作用**：从变量 → 验证因果假设

```json
{
  "id": "M_regression_linear",
  "name": "Linear Regression",
  "family": "regression",
  "category": "analysis_method",
  "description": "Estimate linear causal effect between variables",
  
  "metadata_fields_required": [],  // ⚠️ 分析方法不需要元数据字段，只需要变量
  
  "applicable_variables": {
    "input_vars": ["V09_tech_diversity", "V22_tech_maturity"],  // 需要哪些变量作为输入
    "output_vars": ["V16_tech_impact"],                          // 输出哪个变量
    "constraint_vars": ["V32_Data_Constraint"],
    "performance_vars": ["V16_tech_impact"]
  },
  
  "implementation": {
    "pseudo_code": "fit y ~ x + controls",
    "formula": "V16 = β₀ + β₁*V09 + β₂*V22 + ε",
    "libraries": ["statsmodels", "sklearn"],
    "typical_parameters": { "fit_intercept": true }
  },
  
  "evidence": {
    "papers": ["paper title"],
    "domains": ["ICT"]
  },
  "synonyms": ["OLS", "linear_model"]
}
```

**关键设计决策**：
- ✅ **metadata_fields_required**：分析方法通常为空（因为输入是变量，不是元数据）
- ✅ **input_vars**：明确需要哪些变量（这些变量已经通过测量方法计算好了）

## 🔗 连接机制

### 1. 测量方法 → 变量

```
M_measure_V09_IPC_entropy
    ↓ (output_vars)
V09_tech_diversity
```

### 2. 变量 → 因果边

```
V09_tech_diversity → V16_tech_impact
    ↓ (method_bridge.specific_method_key)
M_regression_linear
```

### 3. 完整流程

```
专利元数据["IPC分类号"]
    ↓ M_measure_V09_IPC_entropy
V09_tech_diversity
    ↓ E001 (V09 → V16)
V16_tech_impact
    ↓ M_regression_linear
研究结论
```

## 📊 元数据字段归属决策

### ✅ 正确设计：元数据字段放在 Graph B（方法图谱）

**理由**：
1. **一个变量可以有多种测量方法**：V09 可以用 IPC 熵、IPC 计数、CPC 熵等，每种方法需要不同的元数据字段
2. **保持 Graph A 的概念纯净**：变量定义不应该绑定具体数据字段
3. **符合数据流设计**：元数据 → 测量方法 → 变量 → 分析方法 → 结论

### ❌ 错误设计：元数据字段放在 Graph A（因果图谱）

**问题**：
1. 一个变量只能绑定一种元数据字段，无法支持多种测量方法
2. 破坏了概念层和操作层的分离
3. 无法灵活应对不同数据源（有些数据有 IPC，有些有 CPC）

## 🎯 设计总结

### Graph A（因果图谱）
- ✅ 变量定义：概念层，不包含 metadata_fields
- ✅ 因果边：描述变量间关系，通过 method_bridge 链接到 Graph B
- ✅ 保持理论层的纯净性

### Graph B（方法图谱）
- ✅ 测量方法：明确 metadata_fields_required，输出变量
- ✅ 分析方法：明确 input_vars（变量），不直接使用元数据
- ✅ 操作层的完整性

### 数据流
```
元数据字段 → 测量方法（Graph B）→ 变量（Graph A）→ 因果边（Graph A）→ 分析方法（Graph B）→ 结论
```

## 📝 Prompt 更新要求

1. **Graph A 变量定义**：移除 `metadata_fields` 字段
2. **Graph B 测量方法**：必须包含 `metadata_fields_required` 字段
3. **Graph B 分析方法**：`metadata_fields_required` 通常为空（因为输入是变量）
