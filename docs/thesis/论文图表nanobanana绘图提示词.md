# 硕士论文图表 nanobanana 绘图提示词（顶刊学术风格版）

基于论文LaTeX内容重构，严格遵循顶级期刊（Nature, Science, IEEE Transactions）学术配图规范。

## 学术配图核心原则

1. **极简主义**：去除所有装饰性元素，只保留必要信息
2. **高对比度**：使用灰度 + 最多3种强调色，确保黑白打印清晰
3. **矢量图风格**：清晰线条，无渐变、无阴影、无3D效果
4. **统一规范**：字体Arial/Helvetica，线宽1-2pt，严格对齐
5. **专业标注**：使用(a)(b)(c)子图编号，简洁图例
6. **数据墨水比最大化**：遵循Tufte可视化原则

---

## 图 3-1：系统总体架构图

**LaTeX位置**：`textfiles/3FirstResearch.tex` line 40-58

**提示词：**
```
Create a system architecture diagram in academic publication style (IEEE Transactions format):

STYLE REQUIREMENTS:
- Black and white with ONE accent color (dark blue #2E5090) for key components
- Clean vector graphics, no gradients, no shadows, no 3D effects
- Font: Arial or Helvetica, 10-11pt for labels
- Line width: 1.5pt for main boxes, 1pt for arrows
- Strict alignment: use grid layout
- Minimize decorative elements, maximize information density

LAYOUT: Horizontal three-layer architecture (left to right)

LAYER 1 - INPUT (Left, light gray boxes):
┌─────────────────┐
│ Research        │
│ Question        │
└─────────────────┘
┌─────────────────┐
│ Patent          │
│ Dataset         │
└─────────────────┘

LAYER 2 - PROCESSING (Center, main content):

(a) Foundation Layer (background, dashed boxes):
    ┌─ Data Awareness ─────────┐
    │ • DataPreview            │
    │ • GraphPreview           │
    └──────────────────────────┘
    ┌─ Knowledge Constraint ───┐
    │ • Causal Graph (30 vars) │
    │ • Method Graph (86 methods)│
    └──────────────────────────┘

(b) Agent Pipeline (foreground, solid boxes with dark blue fill):
    [Strategist] → [Methodologist] → [CodingAgent] → [Reviewer]

    Under each box, small text label:
    - Strategist: "Insight + Blueprint"
    - Methodologist: "Specification"
    - CodingAgent: "Code + Execution"
    - Reviewer: "Validation"

(c) Iteration (curved arrow):
    Round 1 → Round 2 (feedback arrow from Reviewer back to Strategist)
    Label: "Gap-driven Refinement"

LAYER 3 - OUTPUT (Right, light gray boxes):
┌─────────────────┐
│ Analysis        │
│ Report          │
└─────────────────┘
┌─────────────────┐
│ Executable      │
│ Code            │
└─────────────────┘

ARROWS:
- Solid arrows (→) for main data flow
- Dashed arrows (⇢) for foundation layer feeding into agents
- Curved arrow for iteration feedback

ANNOTATIONS:
- Use (a), (b), (c) to label three sub-components
- Minimal text, focus on structure
- All text in English with Chinese in parentheses only where necessary

REFERENCE STYLE: Similar to system architecture diagrams in:
- IEEE Transactions on Software Engineering
- ACM Transactions on Information Systems
- Nature Methods (computational tools)
```

---

## 图 3-2：数据感知方案生成流程图

**LaTeX位置**：`textfiles/3FirstResearch.tex` line 84-106

**提示词：**
```
Create a three-stage process flowchart in academic publication style (Nature Methods format):

STYLE REQUIREMENTS:
- Grayscale with ONE accent color (dark blue #2E5090) for key stages
- Vector graphics: clean lines, no gradients, no shadows
- Font: Arial 10pt, bold for stage headers
- Box style: rounded rectangles with 1.5pt borders
- Arrow style: solid 1pt lines with simple arrowheads
- Strict vertical alignment

LAYOUT: Vertical three-stage flow

┌─────────────────────────────────────────────┐
│ Stage 1: Data Fact Extraction              │ (dark blue header)
└─────────────────────────────────────────────┘

Three parallel boxes (light gray fill):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ DataPreview  │  │ GraphPreview │  │  Sampling    │
│ • Column     │  │ • Community  │  │ • Abstracts  │
│ • Correlation│  │ • Centrality │  │ • 20-30 IPC  │
└──────────────┘  └──────────────┘  └──────────────┘
        ↓                ↓                  ↓
        └────────────────┴──────────────────┘
                         ↓
              [Structured Data Facts]

┌─────────────────────────────────────────────┐
│ Stage 2: Insight Generation                │ (dark blue header)
└─────────────────────────────────────────────┘

Single box (white fill, dark border):
┌─────────────────────────────────────────────┐
│         LLM-driven Insight Generation       │
│                                             │
│  Input: Data facts                          │
│  Output: 5-8 testable insights              │
│  Types: Statistical | Graph | Content       │
└─────────────────────────────────────────────┘
                         ↓

┌─────────────────────────────────────────────┐
│ Stage 3: Blueprint Planning                │ (dark blue header)
└─────────────────────────────────────────────┘

Two input boxes merging:
┌──────────────┐  ┌──────────────┐
│   Insights   │  │ KG Constraints│
│   (Stage 2)  │  │ Causal+Method│
└──────────────┘  └──────────────┘
        ↓                ↓
        └────────────────┘
                ↓
    [DAG Blueprint Generation]
                ↓
         [Analysis Blueprint]

COMPARISON INSET (bottom right, small box):
┌─────────────────────────┐
│ Traditional:            │
│ Q → Plan                │
│                         │
│ Data-Aware:             │
│ Q + Data → I → Plan     │
└─────────────────────────┘

ANNOTATIONS:
- Label stages as (a), (b), (c)
- Use minimal text
- Key terms in bold
- Chinese terms in small parentheses only if necessary

REFERENCE STYLE: Similar to methodology flowcharts in:
- Nature Methods
- Science Advances (computational methods)
- PNAS (systems biology)
```

---

## 图 3-3：两轮迭代优化流程图

**LaTeX位置**：`textfiles/3FirstResearch.tex` line 108-128

**提示词：**
```
Create a two-round iteration flowchart in academic publication style (IEEE format):

STYLE REQUIREMENTS:
- Grayscale base + TWO accent colors: dark blue #2E5090 (Round 1), dark green #2D5F3F (Round 2)
- Vector graphics: clean boxes, 1.5pt borders, no shadows
- Font: Arial 10pt
- Strict horizontal alignment for two rounds
- Minimal decorative elements

LAYOUT: Horizontal two-panel with central connector

┌─────────────────────────────────────────────────────────────────┐
│                    (a) Round 1: Exploration                     │
└─────────────────────────────────────────────────────────────────┘

[Input] → [Generate DAG] → [Execute] → [Results R1]
           (2-3 tasks)      (M→C→R)

Details in box:
┌──────────────────────┐
│ Focus:               │
│ • Effect existence   │
│ • Main relationships │
│ • 2-3 core tasks     │
└──────────────────────┘

                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                  (b) Gap Analysis (中间环节)                     │
└─────────────────────────────────────────────────────────────────┘

[Analyze R1] → Identify gaps:
               • Signals not validated
               • Insights not covered
               • Confounding factors

                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                   (c) Round 2: Validation                       │
└─────────────────────────────────────────────────────────────────┘

[Refined DAG] → [Execute] → [Results R2]
(+ controls)     (M→C→R)

Details in box:
┌──────────────────────┐
│ Enhancements:        │
│ • Control variables  │
│ • Non-linear models  │
│ • Interaction terms  │
│ • Mechanism tests    │
└──────────────────────┘

                    ↓
              [Final Report]
         (R1 + R2 integrated)

FEEDBACK ARROW:
- Curved dashed arrow from "Gap Analysis" back to Round 1 box
- Label: "previous_results parameter"

KEY ANNOTATIONS:
- M = Methodologist, C = CodingAgent, R = Reviewer
- Use (a), (b), (c) labels for three stages
- Bottom note: "Effect Discovery → Mechanism Explanation"

REFERENCE STYLE: Similar to iterative algorithm flowcharts in:
- IEEE Transactions on Pattern Analysis and Machine Intelligence
- ACM Transactions on Knowledge Discovery from Data
```

---

## 图 4-1：跨列统计数据流图

**LaTeX位置**：`textfiles/4SecondResearch.tex` line 82-88

**提示词：**
```
Create a data flow diagram in academic publication style (similar to database/data processing papers):

STYLE REQUIREMENTS:
- Grayscale with dark blue #2E5090 for data flow arrows
- Vector graphics: rectangular boxes with 1.5pt borders
- Font: Arial 10pt, monospace for data types
- Clean parallel streams converging to single output
- No decorative elements

LAYOUT: Three parallel vertical streams converging

INPUT (Top):
┌─────────────────────────────────────┐
│        DataFrame (Patent Data)      │
└─────────────────────────────────────┘
              ↓  ↓  ↓
    ┌─────────┼─────────┼─────────┐
    ↓         ↓         ↓         ↓

STREAM 1 (Left):
┌──────────────────┐
│ Column-level     │
│ Statistics       │
├──────────────────┤
│ 1. Type Detection│
│ 2. Missing Check │
│ 3. Distribution  │
└──────────────────┘
         ↓
   [Column Profiles]

STREAM 2 (Center):
┌──────────────────┐
│ Cross-column     │
│ Relationships    │
├──────────────────┤
│ 1. Pearson r     │
│ 2. Group Compare │
│ 3. Time Trends   │
└──────────────────┘
         ↓
  [Relationship Signals]

STREAM 3 (Right):
┌──────────────────┐
│ Graph            │
│ Structure        │
├──────────────────┤
│ 1. Build Network │
│ 2. Communities   │
│ 3. Centrality    │
└──────────────────┘
         ↓
  [Topology Features]

CONVERGENCE (Bottom):
    ↓         ↓         ↓
    └─────────┼─────────┘
              ↓
┌─────────────────────────────────────┐
│    Structured Data Facts            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    LLM Insight Generation           │
└─────────────────────────────────────┘

ANNOTATIONS:
- Label streams as (a), (b), (c)
- Use simple box style, no rounded corners
- Arrows: solid 1pt lines
- Minimal text inside boxes

REFERENCE STYLE: Similar to data processing pipelines in:
- ACM SIGMOD (database systems)
- IEEE Transactions on Knowledge and Data Engineering
- VLDB Journal
```

---

## 图 4-2：自动构图逻辑图

**LaTeX位置**：`textfiles/4SecondResearch.tex` line 104-122

**提示词：**
```
Create a decision tree flowchart in academic publication style (algorithm flowchart format):

STYLE REQUIREMENTS:
- Grayscale with dark blue #2E5090 for decision diamonds
- Vector graphics: diamonds for decisions, rectangles for processes
- Font: Arial 10pt
- Line width: 1.5pt for boxes, 1pt for arrows
- Standard flowchart symbols (ISO 5807)

LAYOUT: Top-down decision tree

START:
┌─────────────────────────┐
│ Scan DataFrame Columns  │
└─────────────────────────┘
            ↓
      ◇─────────────◇
     /  Contains      \
    /   delimiter?     \
   /   (| or ;)         \
  ◇─────────────────────◇
   │                    │
  Yes                  No → [Skip]
   ↓
┌─────────────────────────┐
│ Extract & Sample        │
│ Elements                │
└─────────────────────────┘
            ↓
      ◇─────────────◇
     /  Element Type?  \
    /                   \
   ◇─────────────────────◇
   │         │          │
   │         │          │
Patent    Class      Name
  ID       Code
   ↓         ↓          ↓

(a) Patent ID Pattern:
┌─────────────────────┐
│ Pattern:            │
│ [A-Z]{2}\d+[A-Z]?   │
│ Example: CN120822A  │
└─────────────────────┘
         ↓
┌─────────────────────┐
│ Build Citation      │
│ Network (Directed)  │
└─────────────────────┘

(b) Classification Code:
┌─────────────────────┐
│ Pattern:            │
│ [A-H]\d{2}[A-Z]/\d+ │
│ Example: G06F21/60  │
└─────────────────────┘
         ↓
┌─────────────────────┐
│ Build Co-occurrence │
│ Network (Undirected)│
└─────────────────────┘

(c) Name Pattern:
┌─────────────────────┐
│ Pattern:            │
│ Short text, no /    │
│ Example: KIM,S.H.   │
└─────────────────────┘
         ↓
┌─────────────────────┐
│ Build Collaboration │
│ Network (Undirected)│
└─────────────────────┘

OUTPUT (Bottom):
         ↓
┌─────────────────────────┐
│ Graph Collection:       │
│ • Inventor Network      │
│ • IPC Network           │
│ • Citation Network      │
│ (6 graphs total)        │
└─────────────────────────┘

SYMBOLS:
- Rectangle: Process
- Diamond: Decision
- Arrows: 1pt solid lines
- Use standard flowchart conventions

REFERENCE STYLE: Similar to algorithm flowcharts in:
- Cormen et al., Introduction to Algorithms
- IEEE Software
- ACM Computing Surveys
```

---

## 图 4-3：因果图谱局部示例

**LaTeX位置**：`textfiles/4SecondResearch.tex` line 232-242

**提示词：**
```
Create a causal knowledge graph visualization in academic publication style (network science format):

STYLE REQUIREMENTS:
- Grayscale nodes with dark blue #2E5090 for key variables
- Vector graphics: circles for nodes, directed arrows for edges
- Font: Arial 9pt for node labels
- Arrow style: simple solid lines with arrowheads, 1pt width
- Force-directed or hierarchical layout
- Minimal decorative elements

GRAPH STRUCTURE:

NODES (10-12 variables shown, circular layout):
Display these key variables as circles:

Core Variables (dark blue fill):
- Technology Impact (技术影响力)
- Commercial Value (商业价值)
- Technology Diversity (技术多样性)

Supporting Variables (light gray fill):
- R&D Investment (研发投资)
- Firm Size (企业规模)
- Patent Age (专利年龄)
- Citation Count (被引次数)
- Legal Status (法律状态)
- Team Size (团队规模)
- Technology Intensity (技术强度)

EDGES (directed arrows showing causal relationships):
Show these key causal paths:
- R&D Investment → Technology Output
- Technology Diversity → Technology Impact
- Firm Size → Patent Quality
- Patent Age → Citation Count
- Technology Intensity → Commercial Value
- Team Size → Technology Diversity
- Legal Status → Commercial Value

LAYOUT:
- Use force-directed layout or hierarchical layout
- Central nodes: Technology Impact, Commercial Value
- Peripheral nodes: input variables
- Clear directional flow from inputs to outcomes

ANNOTATIONS:
- Top label: "Causal Knowledge Graph (因果图谱)"
- Bottom note: "30 variables, 99 causal paths (partial view shown)"
- Small text: "Extracted from 800+ patent analysis papers"

LEGEND (bottom right, small box):
┌──────────────────┐
│ ● Core variable  │
│ ○ Input variable │
│ → Causal path    │
└──────────────────┘

REFERENCE STYLE: Similar to causal graphs in:
- Pearl, Causality (textbook figures)
- Nature Human Behaviour (causal inference papers)
- Psychological Methods (SEM diagrams)
```

---

## 图 4-4：方法匹配示例图

**LaTeX位置**：`textfiles/4SecondResearch.tex` line 269-280

**提示词：**
```
Create a method matching diagram in academic publication style (taxonomy/mapping format):

STYLE REQUIREMENTS:
- Grayscale with dark blue #2E5090 for matching arrows
- Vector graphics: hierarchical tree + mapping arrows
- Font: Arial 9pt
- Clean box style with 1pt borders
- Minimal decorative elements

LAYOUT: Three-panel horizontal layout

┌─────────────────────────────────────────────────────────────────┐
│ (a) Method Graph Structure │ (b) Matching │ (c) Examples       │
└─────────────────────────────────────────────────────────────────┘

PANEL A - Method Taxonomy (Left, 40% width):

┌─────────────────────────┐
│ Statistical Methods     │
├─────────────────────────┤
│ Regression:             │
│  • OLS                  │
│  • Logistic             │
│  • Neg. Binomial        │
│                         │
│ Mediation:              │
│  • Bootstrap test       │
│  • Sobel test           │
│                         │
│ Moderation:             │
│  • Hierarchical reg.    │
│  • Interaction terms    │
└─────────────────────────┘

┌─────────────────────────┐
│ Variable Measurement    │
├─────────────────────────┤
│ Diversity:              │
│  • IPC count            │
│  • Shannon entropy      │
│                         │
│ Impact:                 │
│  • Citation count       │
│  • PageRank             │
└─────────────────────────┘

PANEL B - Matching Logic (Center, 20% width):

Hypothesis Type → Method

Show 3 arrows connecting left to right:
Arrow 1: "Mediation" →
Arrow 2: "Moderation" →
Arrow 3: "Non-linear" →

PANEL C - Examples (Right, 40% width):

Example 1:
┌─────────────────────────┐
│ Mediation Effect        │
├─────────────────────────┤
│ Hypothesis:             │
│ X → M → Y               │
│                         │
│ Matched Method:         │
│ Bootstrap mediation     │
└─────────────────────────┘

Example 2:
┌─────────────────────────┐
│ Moderation Effect       │
├─────────────────────────┤
│ Hypothesis:             │
│ X × Z → Y               │
│                         │
│ Matched Method:         │
│ Hierarchical regression │
└─────────────────────────┘

Example 3:
┌─────────────────────────┐
│ Count Data              │
├─────────────────────────┤
│ Hypothesis:             │
│ Overdispersed counts    │
│                         │
│ Matched Method:         │
│ Negative binomial       │
└─────────────────────────┘

BOTTOM ANNOTATION:
"86+ analysis methods with automatic recommendation"

REFERENCE STYLE: Similar to method taxonomy diagrams in:
- Psychological Methods (statistical methods)
- Organizational Research Methods
- Multivariate Behavioral Research
```

---

## 图 4-5：执行与纠错流程图

**LaTeX位置**：`textfiles/4SecondResearch.tex` line 324-334

**提示词：**
```
Create an execution and error correction flowchart in academic publication style:

STYLE REQUIREMENTS:
- Grayscale with green #2D5F3F for success path, red #8B2E2E for error path
- Vector graphics: standard flowchart symbols
- Font: Arial 10pt
- Line width: 1.5pt for boxes, 1pt for arrows
- Clear success/failure branching

LAYOUT: Vertical flow with loop

START:
┌─────────────────────────┐
│ Technical Specification │
│ from Methodologist      │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ CodingAgent:            │
│ Generate Python Code    │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ Execute in Sandbox      │
└─────────────────────────┘
            ↓
      ◇─────────◇
     /  Success?  \
    /              \
   ◇────────────────◇
   │                │
  Yes              No
   │                │
   ↓                ↓

SUCCESS PATH (Right, green):
┌─────────────────────────┐
│ Capture Results         │
│ • Output JSON           │
│ • Statistics            │
│ • Visualizations        │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ Success Rate: 100%      │
└─────────────────────────┘

ERROR PATH (Left, red):
┌─────────────────────────┐
│ Error Analysis          │
├─────────────────────────┤
│ • Column not found      │
│ • Type mismatch         │
│ • Package exception     │
└─────────────────────────┘
            ↓
┌─────────────────────────┐
│ Targeted Repair         │
│ • Parse error message   │
│ • Generate fix          │
└─────────────────────────┘
            ↓
      ◇─────────◇
     / Iteration  \
    /   < 15?      \
   ◇────────────────◇
   │                │
  Yes              No
   │                │
   ↓                ↓
[Loop back]    [Manual Review]
   to Execute

LOOP ARROW:
- Curved dashed arrow from "Targeted Repair" back to "Execute in Sandbox"
- Label: "Iterative Repair Loop"

ANNOTATIONS:
- Counter box showing "Iteration: n/15"
- Note: "All tasks converge to success"
- Bottom: "100% execution success rate achieved"

REFERENCE STYLE: Similar to error handling flowcharts in:
- IEEE Software
- ACM Transactions on Software Engineering
- Software: Practice and Experience
```

---

## 图 5-1：自动化指标对比图

**LaTeX位置**：`textfiles/5ThirdResearch.tex` line 98-105, 表5-2数据

**提示词：**
```
Create a radar chart in academic publication style (data visualization standard):

STYLE REQUIREMENTS:
- Grayscale with 4 distinct line styles + ONE accent color for best performer
- Vector graphics: clean polygon lines, 1.5pt width
- Font: Arial 9pt for axis labels
- No fill, only line outlines (for print clarity)
- Grid lines: light gray, 0.5pt
- Minimal decorative elements

CHART TYPE: 9-axis radar chart (spider chart)

AXES (9 dimensions, evenly spaced):
1. Column Coverage (0-0.5)
2. Method Diversity (0-6)
3. Description Detail (0-100)
4. Specificity Refs (0-16)
5. Control Variables (0-2)
6. Parameter Rich (0-13)
7. Outcome Specific (0-1)
8. Data Insights (0-3)
9. Task Count (0-5)

DATA (normalized to 0-1 scale for visualization):

D_baseline0 (solid gray line, 1.5pt):
[0.273, 3.000, 50.27, 2.667, 1.667, 8.333, 0.667, 0.000, 3.333]

A_template (dashed gray line, 1.5pt):
[0.273, 3.000, 65.43, 1.667, 1.667, 4.333, 0.167, 0.000, 3.000]

B_data_aware (dotted gray line, 1.5pt):
[0.258, 2.667, 48.60, 7.667, 1.333, 6.667, 0.500, 3.000, 2.667]

C_iterative (solid dark blue #2E5090, 2pt, emphasized):
[0.424, 5.667, 99.77, 15.333, 0.667, 12.333, 0.750, 3.000, 5.000]

VISUAL FEATURES:
- C line should be most prominent (thicker, colored)
- Other lines in grayscale with different dash patterns
- No polygon fill (line outlines only)
- Grid circles at 0.2, 0.4, 0.6, 0.8, 1.0
- Axis labels outside the chart

LEGEND (bottom, horizontal):
━━━ D_baseline0  ┄┄┄ A_template  ····· B_data_aware  ━━━ C_iterative

ANNOTATIONS:
- Small note: "Values normalized to [0,1] for visualization"
- Highlight C's superiority on most dimensions

REFERENCE STYLE: Similar to radar charts in:
- IEEE Transactions (performance comparison)
- Nature Methods (method benchmarking)
- PLOS ONE (multi-dimensional comparison)
```

---

## 图 5-2：六方案LLM总分柱状图

**LaTeX位置**：`textfiles/5ThirdResearch.tex` line 132-139

**提示词：**
```
Create a bar chart in academic publication style (Nature/Science format):

STYLE REQUIREMENTS:
- Grayscale bars with TWO accent colors for paradox highlighting
- Vector graphics: clean rectangular bars, no 3D effects
- Font: Arial 10pt for labels, 11pt bold for scores
- Bar width: uniform, with spacing
- Grid lines: horizontal only, light gray 0.5pt
- Minimal decorative elements

CHART LAYOUT:

X-AXIS: Six experimental modes (left to right, ascending order)
Y-AXIS: LLM-as-Judge Total Score (0-25)

BARS (with exact scores on top):

1. A_template: 15.33
   Color: Dark gray #505050

2. D_baseline0: 17.33
   Color: Medium gray #707070

3. B_data_aware: 18.67
   Color: Light gray #909090

4. E_ablate_data: 22.00
   Color: Light gray #A0A0A0

5. C_iterative: 22.33
   Color: Light gray #B0B0B0

6. F_ablate_kg: 23.67
   Color: Light gray #C0C0C0

ANNOTATIONS:

(a) Knowledge Constraint Paradox:
- Bracket connecting A and D bars
- Arrow pointing down between them
- Text: "A < D" with small note "KG constraint paradox"
- Position: above bars

(b) Knowledge Graph Removal Paradox:
- Bracket connecting C and F bars
- Arrow pointing up between them
- Text: "F > C" with small note "KG removal paradox"
- Position: above bars

REFERENCE LINE:
- Horizontal dashed line at y=22.33
- Label on right: "Complete System (C)"
- Line style: 1pt dashed gray

BOTTOM ANNOTATION:
- Small text: "6-way simultaneous evaluation"
- Note: "All modes evaluated together (n=3 questions)"

LEGEND (bottom, compact):
D: Pure LLM | A: +KG | B: +Data | C: +Iteration | E: C-Data | F: C-KG

AXIS LABELS:
- X-axis: "Experimental Mode"
- Y-axis: "Total Score (out of 25)"

REFERENCE STYLE: Similar to bar charts in:
- Nature (method comparison)
- Science (performance benchmarking)
- Cell (quantitative results)
```

---

## 图 5-3：五维评分雷达图

**LaTeX位置**：`textfiles/5ThirdResearch.tex` line 141-148, 表5-3数据

**提示词：**
```
Create a pentagon radar chart in academic publication style:

STYLE REQUIREMENTS:
- Grayscale with ONE accent color (dark blue #2E5090) for best performer
- Vector graphics: clean polygon lines, no fill
- Font: Arial 9pt for axis labels
- Line width: 1.5pt for lines
- Grid lines: light gray, 0.5pt
- Pentagon shape (5 axes)

CHART TYPE: Pentagon radar chart (5 dimensions)

AXES (5 dimensions, evenly spaced, scale 0-5):
1. Relevance (相关性) - top
2. Specificity (针对性) - top right
3. Method Soundness (方法合理性) - bottom right
4. Innovation (创新性) - bottom left
5. Depth (深度) - top left

DATA (4 modes):

D_baseline0 (solid gray line, 1pt):
- Relevance: 4.33
- Specificity: 3.33
- Method Soundness: 3.67
- Innovation: 2.67
- Depth: 3.33

A_template (dashed gray line, 1pt):
- Relevance: 3.67
- Specificity: 3.33
- Method Soundness: 2.67
- Innovation: 3.00
- Depth: 2.67

B_data_aware (dotted gray line, 1.5pt):
- Relevance: 4.00
- Specificity: 4.00
- Method Soundness: 3.33
- Innovation: 4.00
- Depth: 3.33

C_iterative (solid dark blue #2E5090, 2pt, emphasized):
- Relevance: 4.67
- Specificity: 4.33
- Method Soundness: 4.33
- Innovation: 4.67
- Depth: 4.33

VISUAL FEATURES:
- C line most prominent (thicker, colored)
- Other lines in grayscale with different patterns
- No polygon fill (line outlines only)
- Grid pentagons at 1, 2, 3, 4, 5
- Vertex markers: small circles at data points
- Axis labels outside the chart

HIGHLIGHT:
- Mark C's Innovation score (4.67) with a small star ★
- This is the maximum score achieved

LEGEND (bottom, horizontal, compact):
━━━ D_baseline0  ┄┄┄ A_template  ····· B_data_aware  ━━━ C_iterative

ANNOTATIONS:
- Small note: "Scale: 1-5 for each dimension"
- Bottom: "C achieves highest scores on 4/5 dimensions"

REFERENCE STYLE: Similar to radar charts in:
- Psychological Methods (multi-dimensional assessment)
- Journal of Applied Psychology (performance evaluation)
- Organizational Research Methods
```

---

## 使用说明

1. **工具**：将每个提示词复制到 nanobanana AI 绘图工具中
2. **风格一致性**：所有图表遵循顶刊学术风格，确保黑白打印清晰
3. **调整**：生成后可微调具体数值位置和标注，但保持整体风格不变
4. **分辨率**：确保输出为矢量图格式（SVG/PDF）或至少 300 DPI 的位图
5. **验证**：生成后检查是否符合期刊投稿要求（通常要求矢量图）

## 顶刊学术配图标准总结

### 配色方案
- **主色调**：灰度（黑、白、灰）
- **强调色**：最多1-2种（深蓝 #2E5090、深绿 #2D5F3F）
- **禁止**：渐变、彩虹色、鲜艳颜色

### 图形元素
- **线条**：1-2pt，实线/虚线/点线区分
- **字体**：Arial/Helvetica，9-11pt
- **形状**：简单几何形状，无圆角装饰
- **箭头**：简单三角形箭头，无花哨样式

### 布局原则
- **对齐**：严格网格对齐
- **留白**：充足的空白空间
- **标注**：使用(a)(b)(c)子图编号
- **图例**：简洁，通常放在底部或右侧

### 数据可视化
- **网格线**：浅灰色，0.5pt
- **坐标轴**：清晰刻度，单位明确
- **数据点**：可见但不突兀
- **误差线**：如有数据支持

### 打印友好
- **黑白可辨**：去除颜色后仍可区分
- **高对比度**：文字与背景对比度 > 4.5:1
- **矢量优先**：使用矢量图格式

## 参考期刊风格

| 期刊类型 | 典型风格特征 |
|---------|------------|
| Nature/Science | 极简黑白，少量颜色强调，高信息密度 |
| IEEE Transactions | 标准流程图符号，统一线宽，清晰标注 |
| ACM系列 | 专业框图，严格对齐，简洁图例 |
| Cell系列 | 清晰数据可视化，多子图组合 |
| PNAS | 科学插图风格，注重数据准确性 |

## 图表清单

| 图号 | 图表名称 | 类型 | 风格要点 |
|------|---------|------|---------|
| 3-1 | 系统总体架构图 | 系统架构 | 三层布局，深蓝强调核心组件 |
| 3-2 | 数据感知方案生成流程 | 流程图 | 三阶段垂直流，对比框 |
| 3-3 | 两轮迭代优化流程 | 流程图 | 双色区分两轮，反馈箭头 |
| 4-1 | 跨列统计数据流 | 数据流图 | 三并行流汇聚，深蓝箭头 |
| 4-2 | 自动构图逻辑 | 决策树 | 标准流程图符号，清晰分支 |
| 4-3 | 因果图谱局部示例 | 网络图 | 灰度节点+深蓝核心变量 |
| 4-4 | 方法匹配示例 | 分类映射 | 三面板布局，匹配箭头 |
| 4-5 | 执行与纠错流程 | 流程图 | 绿色成功路径+红色错误路径 |
| 5-1 | 自动化指标对比 | 雷达图 | 无填充线条，深蓝强调最优 |
| 5-2 | 六方案LLM总分 | 柱状图 | 灰度柱+悖论标注 |
| 5-3 | 五维评分雷达 | 雷达图 | 五边形，无填充，星标最高分 |

---

**文件创建时间**：2026-03-09
**版本**：顶刊学术风格版 v2.0
**适用期刊**：Nature, Science, IEEE Transactions, ACM系列等顶级期刊
