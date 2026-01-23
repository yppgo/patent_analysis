"""
Methodologist Agent V5.0 - 方法论智能体（技术架构师）
负责将 DAG 任务节点转化为详细的技术规格书

核心改进：
1. 支持 DAG 模式：处理 task_node（包含 input_variables 和 output_variables）
2. 生成技术规格书（Technical Spec）而不是可执行代码
3. 输出伪代码逻辑（logic_flow）供 Coding Agent 使用
4. 保持向后兼容（Legacy 模式）
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from src.agents.base_agent import BaseAgent
from src.utils.data_preview import DataPreview


class MethodologistAgent(BaseAgent):
    """
    方法论智能体 V5.0（技术架构师）
    
    职责：
    1. 解析 DAG 任务节点（V5）或传统步骤（Legacy）
    2. 生成详细的技术规格书（Technical Spec）
    3. 定义函数签名、输入输出契约、逻辑流程
    4. 不生成完整代码，只生成伪代码逻辑
    """
    
    def __init__(self, llm_client, logger=None):
        """
        初始化 Methodologist V5.0
        
        Args:
            llm_client: LLM 客户端
            logger: 日志记录器
        """
        super().__init__("Methodologist_V5", llm_client, logger)
        self._data_preview_cache: Dict[Tuple[str, str], str] = {}
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务，生成技术规格
        
        支持双模式：
        - DAG 模式（新）：输入包含 task_node
        - Legacy 模式（旧）：输入包含 step
        
        Args:
            input_data: {
                "task_node": {...},  # DAG 模式（V5）
                "step": {...},       # Legacy 模式（V4）
                "previous_output": {...},  # 前一步的输出规格（可选）
                "step_index": int  # 步骤索引（可选）
            }
            
        Returns:
            {"technical_spec": {...}}  # 技术规格书
        """
        # 路由逻辑：DAG 模式 vs Legacy 模式
        if 'task_node' in input_data:
            self.log("[V5.0] 使用 DAG 模式处理任务节点")
            return self._process_dag_task(input_data)
        elif 'step' in input_data:
            self.log("[V5.0] 使用 Legacy 模式处理步骤（向后兼容）")
            return self._process_legacy_step(input_data)
        else:
            raise ValueError("输入数据必须包含 'task_node' (DAG 模式) 或 'step' (Legacy 模式)")
    
    def _process_dag_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 DAG 任务节点（V5 模式）
        
        Args:
            input_data: {
                "task_node": {
                    "task_id": str,
                    "task_type": str,
                    "question": str,
                    "description": str,
                    "input_variables": List[str],
                    "output_variables": List[str],
                    "dependencies": List[str],
                    "implementation_config": {...}
                }
            }
            
        Returns:
            {"technical_spec": {...}}
        """
        task_node = input_data['task_node']
        
        self.log(f"处理 DAG 任务: {task_node.get('task_id')} - {task_node.get('question', 'N/A')}")
        
        # 生成技术规格
        technical_spec = self._generate_technical_spec(task_node)
        
        # 验证规格完整性
        validation = self._validate_spec_integrity(technical_spec)
        if not validation['valid']:
            self.log(f"规格验证失败: {validation['issues']}", "warning")
        
        self.log(f"生成技术规格: {technical_spec.get('function_name', 'N/A')}")
        
        return {
            'technical_spec': technical_spec,
            'validation': validation
        }
    
    def _generate_technical_spec(self, task_node: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成技术规格书（核心方法）
        
        关键：生成 function_signature 和 logic_flow（伪代码），而非完整代码
        
        Args:
            task_node: DAG 任务节点
            
        Returns:
            技术规格 JSON
        """
        task_id = task_node.get('task_id', 'unknown')
        task_type = task_node.get('task_type', 'unknown')
        question = task_node.get('question', '')
        description = task_node.get('description', '')
        input_variables = task_node.get('input_variables', [])
        output_variables = task_node.get('output_variables', [])
        dependencies = task_node.get('dependencies', [])
        config = task_node.get('implementation_config', {})

        # 数据预览（统计 + 关键列样例）
        data_preview_text: Optional[str] = None
        try:
            data_source = config.get('data_source')
            sheet_name = config.get('sheet_name')
            if isinstance(data_source, str) and data_source:
                cache_key = (data_source, str(sheet_name or ""))
                if cache_key in self._data_preview_cache:
                    data_preview_text = self._data_preview_cache[cache_key]
                else:
                    data_preview_text = DataPreview.from_file(data_source, sheet_name).to_prompt_string()
                    self._data_preview_cache[cache_key] = data_preview_text
        except Exception as e:
            self.log(f"⚠️ DataPreview 生成失败: {e}", "warning")
        
        prompt = f"""你是一位资深的系统架构师（System Architect）。你的任务是为数据分析任务生成详细的**技术规格书（Technical Specification）**。

**⚠️ 重要约束：**
1. **不要生成完整的 Python 代码**
2. **只生成函数签名和伪代码逻辑**
3. **专注于架构设计和数据契约**

---

## 任务信息

**任务 ID**: {task_id}
**任务类型**: {task_type}
**要回答的问题**: {question}
**任务描述**: {description}

**输入变量**: {input_variables}
**输出变量**: {output_variables}
**依赖任务**: {dependencies}

**实现配置**:
{json.dumps(config, indent=2, ensure_ascii=False)}

---

## 数据预览（结构统计 + 关键列样例）
{data_preview_text or "（未提供数据预览）"}

---

## ⚠️ 变量类型识别指南（重要！）

在生成技术规格前，请先识别变量类型：

### 1. 如何识别变量类型

**从 formula 推断**：
- **类别变量（Categorical）**：
  - 包含 `.str` 操作（如 `'IPC主分类号'.str[:4]`）
  - 提取文本的一部分（如前4位）
  - 结果是字符串（如 'G06F', 'H01L'）
  
- **数值变量（Numeric）**：
  - 数值计算（如 `2026 - pd.to_datetime('授权日').dt.year`）
  - 数学运算（如 `1.0 / len(...)`）
  - 结果是整数或浮点数

**从 description 推断**：
- 如果提到"类别变量"、"分组"、"虚拟变量" → 类别变量
- 如果提到"数值"、"计算"、"年龄" → 数值变量

### 2. 类别变量的特殊处理

**在 input_contract 中**：
- ✅ 正确："列X可以是字符串类型（类别变量）"
- ❌ 错误："所有列必须是数值型"

**在 logic_flow 中**：
- 必须包含类别变量的处理步骤
- 例如："将类别变量X转换为虚拟变量（pd.get_dummies）"
- 例如："检查类别变量X的唯一值数量"

**在中介分析中**：
- 如果中介变量是类别变量：
  - a路径（X→M）：使用多项逻辑回归或序数回归
  - b路径（M→Y）：将M转换为虚拟变量
- 在 logic_flow 中明确说明这些步骤

### 3. 示例

**类别变量示例**：
```
formula: "'IPC主分类号'.str[:4]"
→ 识别为类别变量
→ input_contract: "V09_tech_diversity可以是字符串类型（IPC大类，如'G06F'）"
→ logic_flow: "将V09转换为虚拟变量用于回归分析"
```

**数值变量示例**：
```
formula: "2026 - pd.to_datetime('授权日').dt.year"
→ 识别为数值变量
→ input_contract: "V22_tech_maturity必须是数值型（整数）"
→ logic_flow: "直接使用V22进行回归分析"
```

---

## 你的任务

生成一个 JSON 格式的技术规格书，包含以下内容：

### 1. 函数定义

**⚠️ 关键约束：函数签名必须包含所有必要参数**

- `function_name`: 函数名（如 `execute_task_1_load_data`）
- `function_signature`: 带类型提示的函数签名
  
**函数参数规则**：
- 如果任务需要读取文件：必须包含文件路径参数（如 `data_file: str, sheet_name: str`）
- 如果任务依赖前一个任务的输出：必须包含输入数据参数（如 `variables_df: pd.DataFrame`）
- 如果任务是根任务（无依赖）且需要读取数据：必须包含数据源参数
- ❌ 错误示例：`def execute_task_1() -> Dict:` （缺少参数）
- ✅ 正确示例：`def execute_task_1(data_file: str, sheet_name: str) -> Dict:`

- `docstring`: 函数文档字符串

### 2. 输入契约（Input Contract）
- 明确输入数据的约束
- 例如："Input DataFrame must have 'ipc_code' column"
- 例如："Input file must be CSV format with UTF-8 encoding"

### 3. 逻辑流程（Logic Flow）
- **关键**：这里只写伪代码步骤，不写完整 Python 代码
- 例如：
  1. "Validate input DataFrame has required columns"
  2. "Load data from Excel file using pandas"
  3. "Group by 'date' column and count patents"
  4. "Save results to JSON file"
  5. "Return summary dict with total_patents and date_range"

**⚠️ 类别变量处理的关键约束**：
- 如果涉及类别变量的虚拟变量编码：
  - ✅ 必须使用：`pd.get_dummies(drop_first=True)` （避免多重共线性）
  - ❌ 禁止使用：`pd.get_dummies(drop_first=False)` （会导致共线性问题）
- 如果涉及类别中介变量的中介分析：
  - a路径（X→M，M是类别）：明确使用"多项逻辑回归"（不要说"或卡方检验"）
  - 间接效应计算：明确使用"差值法（总效应 - 直接效应）"（不要说"或乘积法"）

**⚠️ 回归/假设检验任务的强约束（减少 CodingAgent 试错）**：

- 如果自变量是**类别变量**（如 IPC 大类/Topic）：
  - ✅ 优先使用 statsmodels 公式并显式声明类别：`y ~ C(ipc_var) + controls`（而不是手写 dummy 列名拼接）
  - ✅ 若类别数过多（>20）：必须在逻辑流程中包含“Top-K + Other”的降维策略（默认 K=10 或 15）
- 缺失值策略：
  - ✅ 在逻辑流程中明确 `dropna(subset=required_columns)`，并在结果中报告删除了多少行
  - ❌ 不要把“存在缺失值”作为直接失败条件（避免反复 ValueError）
- 标准化/效应量：
  - ✅ 若需要标准化系数，必须包含“std==0 列跳过或替换为 0”的保护步骤（避免除零/NaN 导致模型报错）
- 结果落地与校验：
  - ✅ 必须保存到配置指定的 output_file
  - ✅ logic_flow 最后必须包含“读取已保存文件并校验关键字段存在”的步骤（例如 key 缺失则抛错）

### 4. 输出契约（Output Contract）
- 明确输出数据的结构
- 例如："Returns Dict with keys: 'total_patents' (int), 'date_range' (str)"
- 例如："Saves JSON file to outputs/task_1_data_summary.json"

### 5. 变量命名一致性

**⚠️ 严格约束：变量名必须与配置中的定义完全一致**

- 从 `implementation_config` 中提取变量名时，必须使用 `variable_id` 字段的值
- 不要自己创造新的变量名或添加后缀
- ❌ 错误：配置中是 `V09_tech_diversity`，但你写成 `V09_tech_diversity_group`
- ✅ 正确：配置中是 `V09_tech_diversity`，你就写 `V09_tech_diversity`

### 6. 所需库
- 列出需要的 Python 库

---

## 输出格式（严格 JSON）

{{
  "task_id": "{task_id}",
  "function_name": "execute_{task_id}_<descriptive_name>",
  "function_signature": "def execute_{task_id}_<name>(<params>) -> <return_type>:",
  "docstring": "\"\"\"\\n任务描述\\n\\nArgs:\\n    param1: 描述\\n\\nReturns:\\n    返回值描述\\n\"\"\"",
  "input_contract": [
    "约束1：输入数据必须...",
    "约束2：必须包含列..."
  ],
  "logic_flow": [
    "1. 验证输入数据",
    "2. 加载数据文件",
    "3. 执行核心算法",
    "4. 保存结果到文件",
    "5. 返回汇总信息"
  ],
  "output_contract": [
    "返回 Dict，包含以下键：",
    "  - key1 (type): 描述",
    "  - key2 (type): 描述",
    "保存文件到：<file_path>"
  ],
  "required_libraries": [
    "pandas",
    "numpy",
    "scikit-learn"
  ],
  "data_flow": {{
    "input_files": ["从配置中提取的输入文件"],
    "output_files": ["从配置中提取的输出文件"],
    "input_variables_mapping": {{"variable_name": "data_source"}},
    "output_variables_mapping": {{"variable_name": "data_destination"}}
  }},
  "algorithm_details": {{
    "algorithm_name": "从配置中提取",
    "parameters": {{"param1": "value1"}},
    "notes": "算法说明"
  }},
  "error_handling": [
    "处理文件不存在的情况",
    "处理列名不匹配的情况"
  ]
}}

**⚠️ 边界情况处理指南（必须包含）:**

在 `error_handling` 数组中，必须考虑以下边界情况：

1. **数据质量问题**：
   - 缺失值处理
   - 异常值处理（如负数、超出范围）
   - 数据类型不匹配

2. **类别变量特殊情况**：
   - 类别数量过多（>20个）：考虑合并或筛选
   - 类别数量过少（<2个）：无法进行分析
   - 样本量不平衡：某些类别样本量过少

3. **统计分析问题**：
   - 模型收敛失败
   - 多重共线性
   - 样本量不足

4. **文件操作问题**：
   - 文件不存在
   - 文件格式错误
   - 权限问题

**示例**：
```json
"error_handling": [
  "处理输入文件不存在或无法读取的情况（抛出FileNotFoundError）",
  "处理必需列缺失的情况（抛出ValueError并列出缺失列）",
  "处理V09类别数量过多（>20）的情况（记录警告并考虑合并小类别）",
  "处理V09类别数量不足（<2）的情况（抛出ValueError，无法进行分析）",
  "处理某些类别样本量过少（<30）的情况（记录警告）",
  "处理Bootstrap过程中模型收敛失败的情况（跳过该样本并记录）",
  "处理多重共线性问题（检查VIF值，如果>10则警告）"
]
```

**示例（仅供参考格式）:**

{{
  "task_id": "task_1",
  "function_name": "execute_task_1_load_data",
  "function_signature": "def execute_task_1_load_data(data_file: str, sheet_name: str) -> Dict[str, Any]:",
  "docstring": "\"\"\"\\n加载专利数据并生成基本统计摘要\\n\\nArgs:\\n    data_file: Excel文件路径\\n    sheet_name: 工作表名称\\n\\nReturns:\\n    Dict: 包含 total_patents, date_range, yearly_distribution\\n\"\"\"",
  "input_contract": [
    "数据文件必须存在于指定路径",
    "必须包含 '序号' 和 '授权日' 列"
  ],
  "logic_flow": [
    "1. 使用 pandas 读取 Excel 文件（data_file, sheet_name）",
    "2. 验证必需列存在",
    "3. 统计专利总数",
    "4. 提取时间范围（最早和最晚日期）",
    "5. 按年份分组统计专利数量",
    "6. 保存结果到 JSON 文件",
    "7. 返回包含统计信息的 Dict"
  ],
  "output_contract": [
    "返回 Dict，包含：",
    "  - total_patents (int): 专利总数",
    "  - date_range (str): 时间范围",
    "  - yearly_distribution (Dict[int, int]): 年度分布",
    "保存 JSON 文件到 outputs/task_1_data_summary.json"
  ],
  "required_libraries": ["pandas", "json"],
  "data_flow": {{
    "input_files": ["data/patents.xlsx"],
    "output_files": ["outputs/task_1_data_summary.json", "outputs/task_1_df_raw.csv"]
  }}
}}

**⚠️ 类别变量处理示例（重要参考）:**

如果任务涉及类别变量（如 V09_tech_diversity 的 formula 是 `'IPC主分类号'.str[:4]`）：

{{
  "task_id": "task_2",
  "function_name": "execute_task_2_mediation_analysis",
  "function_signature": "def execute_task_2_mediation_analysis(variables_df: pd.DataFrame) -> Dict[str, Any]:",
  "docstring": "\"\"\"\\n执行中介分析，验证类别中介变量的中介效应\\n\\nArgs:\\n    variables_df: 包含自变量、中介变量、因变量的DataFrame\\n\\nReturns:\\n    Dict: 包含中介分析结果\\n\"\"\"",
  "input_contract": [
    "输入DataFrame必须包含列：'V22_tech_maturity', 'V09_tech_diversity', 'V16_tech_impact'",
    "V22_tech_maturity和V16_tech_impact必须是数值型",
    "V09_tech_diversity可以是字符串类型（类别变量，如'G06F', 'H01L'）",
    "所有列不得包含缺失值"
  ],
  "logic_flow": [
    "1. 验证输入DataFrame包含所有必需列",
    "2. 检查V09_tech_diversity的唯一值数量（类别数）",
    "3. 将V09_tech_diversity转换为虚拟变量（使用pd.get_dummies，drop_first=True以避免多重共线性）",
    "4. 构建中介分析模型：",
    "   - 总效应模型（X→Y）：V16 ~ V22 + controls",
    "   - a路径模型（X→M）：使用多项逻辑回归，因为M是类别变量",
    "   - b路径模型（M→Y）：V16 ~ V22 + [V09虚拟变量] + controls",
    "   - 直接效应模型：同b路径模型",
    "5. 使用Bootstrap方法（5000次）估计间接效应",
    "6. 计算间接效应 = 总效应 - 直接效应（差值法，因为M是类别变量）",
    "7. 计算各路径的系数、p值和效应量",
    "8. 保存结果到JSON文件",
    "9. 返回结果字典"
  ],
  "required_libraries": ["pandas", "numpy", "statsmodels", "sklearn", "scipy"],
  "algorithm_details": {{
    "algorithm_name": "Bootstrap Mediation Analysis with Categorical Mediator",
    "parameters": {{
      "bootstrap_samples": 5000,
      "confidence_level": 0.95,
      "mediator_type": "categorical"
    }},
    "notes": "因为中介变量V09是类别变量，a路径使用多项逻辑回归，b路径使用虚拟变量编码（drop_first=True），间接效应使用差值法计算"
  }}
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            
            # 正确处理响应
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # 清理响应
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            technical_spec = json.loads(content)
            return technical_spec
            
        except json.JSONDecodeError as e:
            self.log(f"JSON 解析失败: {e}", "error")
            return {
                'error': f'JSON 解析失败: {e}',
                'raw_response': content if 'content' in locals() else str(response),
                'task_id': task_id
            }
        except Exception as e:
            self.log(f"技术规格生成失败: {e}", "error")
            return {
                'error': str(e),
                'task_id': task_id
            }
    
    def _validate_spec_integrity(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证技术规格的完整性
        
        Args:
            spec: 技术规格
            
        Returns:
            {"valid": bool, "issues": List[str]}
        """
        issues = []
        
        # 检查必要字段
        required_fields = [
            'function_name',
            'function_signature',
            'logic_flow',
            'required_libraries'
        ]
        
        for field in required_fields:
            if field not in spec:
                issues.append(f"缺少必要字段: {field}")
        
        # 检查 logic_flow 是否为列表
        if 'logic_flow' in spec:
            if not isinstance(spec['logic_flow'], list):
                issues.append("logic_flow 必须是列表")
            elif len(spec['logic_flow']) == 0:
                issues.append("logic_flow 不能为空")
        
        # 检查函数名格式
        if 'function_name' in spec:
            func_name = spec['function_name']
            if not func_name.replace('_', '').isalnum():
                issues.append(f"函数名格式不正确: {func_name}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def generate_execution_plan(self, task_graph: List[Dict[str, Any]], technical_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成执行计划（Execution Plan）
        
        将 task_graph 和 technical_specs 整合成一个清晰的执行计划，
        供 Coding Agent 理解全局执行流程、数据依赖和验证规则。
        
        Args:
            task_graph: Strategist 生成的任务图（来自 blueprint['task_graph']）
            technical_specs: Methodologist 生成的技术规格列表
            
        Returns:
            execution_plan: {
                "metadata": {...},
                "execution_order": [...],
                "data_flow_graph": {...},
                "tasks": [...],
                "validation_rules": {...}
            }
        """
        self.log("[生成执行计划] 开始整合任务图和技术规格")
        
        # 1. 元信息
        metadata = {
            "plan_version": "1.0",
            "total_tasks": len(task_graph),
            "generated_at": self._get_timestamp(),
            "description": "执行计划：定义任务执行顺序、数据流和验证规则"
        }
        
        # 2. 执行顺序（基于依赖关系的拓扑排序）
        execution_order = self._build_execution_order(task_graph)
        
        # 3. 数据流图（输入输出文件映射）
        data_flow_graph = self._build_data_flow_graph(task_graph, technical_specs)
        
        # 4. 任务列表（整合 task_node + technical_spec）
        tasks = []
        for task_node in task_graph:
            task_id = task_node.get('task_id')
            
            # 查找对应的技术规格
            tech_spec = next((spec for spec in technical_specs if spec.get('task_id') == task_id), None)
            
            if tech_spec is None:
                self.log(f"  ⚠️ 警告：任务 {task_id} 没有对应的技术规格", "warning")
                continue
            
            # 整合任务信息
            task_entry = {
                "task_id": task_id,
                "task_type": task_node.get('task_type'),
                "question": task_node.get('question'),
                "description": task_node.get('description'),
                "dependencies": task_node.get('dependencies', []),
                "technical_spec": tech_spec
            }
            
            tasks.append(task_entry)
        
        # 5. 验证规则（每个任务的输出验证）
        validation_rules = self._generate_validation_rules(task_graph, technical_specs)
        
        execution_plan = {
            "metadata": metadata,
            "execution_order": execution_order,
            "data_flow_graph": data_flow_graph,
            "tasks": tasks,
            "validation_rules": validation_rules
        }
        
        self.log(f"[生成执行计划] 完成，共 {len(tasks)} 个任务")
        
        return execution_plan
    
    def _build_execution_order(self, task_graph: List[Dict[str, Any]]) -> List[str]:
        """
        构建执行顺序（拓扑排序）
        
        Args:
            task_graph: 任务图
            
        Returns:
            按依赖关系排序的 task_id 列表
        """
        # 简单实现：按 dependencies 长度排序（依赖少的先执行）
        sorted_tasks = sorted(task_graph, key=lambda t: len(t.get('dependencies', [])))
        return [t['task_id'] for t in sorted_tasks]
    
    def _build_data_flow_graph(self, task_graph: List[Dict[str, Any]], technical_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建数据流图
        
        Args:
            task_graph: 任务图
            technical_specs: 技术规格列表
            
        Returns:
            数据流图：{
                "nodes": [{"task_id": ..., "input_files": [...], "output_files": [...]}],
                "edges": [{"from": task_id, "to": task_id, "data": file_path}]
            }
        """
        nodes = []
        edges = []
        
        for task_node in task_graph:
            task_id = task_node.get('task_id')
            
            # 查找对应的技术规格
            tech_spec = next((spec for spec in technical_specs if spec.get('task_id') == task_id), None)
            
            if tech_spec is None:
                continue
            
            # 提取数据流信息
            data_flow = tech_spec.get('data_flow', {})
            input_files = data_flow.get('input_files', [])
            output_files = data_flow.get('output_files', [])
            
            nodes.append({
                "task_id": task_id,
                "input_files": input_files,
                "output_files": output_files
            })
            
            # 构建边（依赖关系）
            dependencies = task_node.get('dependencies', [])
            for dep_task_id in dependencies:
                # 查找依赖任务的输出文件
                dep_spec = next((spec for spec in technical_specs if spec.get('task_id') == dep_task_id), None)
                if dep_spec:
                    dep_output_files = dep_spec.get('data_flow', {}).get('output_files', [])
                    for output_file in dep_output_files:
                        edges.append({
                            "from": dep_task_id,
                            "to": task_id,
                            "data": output_file
                        })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def _generate_validation_rules(self, task_graph: List[Dict[str, Any]], technical_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成验证规则
        
        Args:
            task_graph: 任务图
            technical_specs: 技术规格列表
            
        Returns:
            验证规则：{
                "task_id": {
                    "output_files_must_exist": [...],
                    "output_columns_must_include": [...],
                    "output_types": {...}
                }
            }
        """
        validation_rules = {}
        
        for task_node in task_graph:
            task_id = task_node.get('task_id')
            
            # 查找对应的技术规格
            tech_spec = next((spec for spec in technical_specs if spec.get('task_id') == task_id), None)
            
            if tech_spec is None:
                continue
            
            # 提取验证信息
            data_flow = tech_spec.get('data_flow', {})
            output_files = data_flow.get('output_files', [])
            
            # 从 output_contract 提取列名和类型
            output_contract = tech_spec.get('output_contract', [])
            
            validation_rules[task_id] = {
                "output_files_must_exist": output_files,
                "output_contract": output_contract,
                "error_handling": tech_spec.get('error_handling', [])
            }
        
        return validation_rules
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ==================== Legacy 模式方法（保持向后兼容）====================
    
    def _process_legacy_step(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理传统步骤（Legacy 模式，向后兼容）
        
        Args:
            input_data: {
                "step": {...},
                "previous_output": {...},
                "step_index": int
            }
            
        Returns:
            {"execution_spec": {...}}
        """
        step = input_data.get('step', {})
        previous_output = input_data.get('previous_output')
        step_index = input_data.get('step_index', 1)
        
        self.log(f"处理 Legacy 步骤: {step.get('objective', 'N/A')}")
        
        # 生成执行规格（使用旧逻辑）
        execution_spec = self._generate_execution_spec({
            'step': step,
            'previous_output': previous_output,
            'step_index': step_index
        })
        
        self.log(f"生成执行规格: {execution_spec.get('function_name', 'N/A')}")
        
        return {
            'execution_spec': execution_spec
        }
    
    def process_multiple(self, steps: list) -> list:
        """
        处理多个步骤（Legacy 模式）
        
        Args:
            steps: 步骤列表
            
        Returns:
            执行规格列表
        """
        specs = []
        
        for i, step in enumerate(steps, 1):
            self.log(f"处理步骤 {i}/{len(steps)}: {step.get('objective', 'N/A')}")
            
            # 传递前一步的输出规格
            previous_output = specs[-1].get('output_specification') if specs else None
            
            result = self.process({
                'step': step,
                'previous_output': previous_output,
                'step_index': i
            })
            specs.append(result['execution_spec'])
        
        return specs
    
    def _generate_execution_spec(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细的执行规格（Legacy 模式）"""
        previous_output = step.get('previous_output')
        step_index = step.get('step_index', 1)
        actual_step = step.get('step', step)
        
        # 构建前置依赖说明
        dependency_note = ""
        if previous_output:
            dependency_note = f"""
**⚠️ 重要：数据依赖关系**
这是第 {step_index} 步，它依赖于前一步的输出。

前一步的输出规格：
{json.dumps(previous_output, indent=2, ensure_ascii=False)}

**你必须确保：**
1. 如果这一步需要前一步的结果，函数签名应该包含对应的参数
2. 参数类型必须与前一步的输出类型匹配
3. 函数应该能处理参数为 None 的情况（在测试时可能没有前置结果）
"""
        
        prompt = f"""你是精通数据科学和软件工程的"配方师"（Methodologist）。
你的任务是将研究方案转化为详细的技术执行规格。

**输入的研究步骤:**
{json.dumps(actual_step, indent=2, ensure_ascii=False)}
{dependency_note}

**你的任务:**
1. 解析 implementation_config 中的所有参数
2. 理解 input_data_source（数据来源）和 output_files（输出文件）
3. 将 notes 中的自然语言描述转化为具体的代码逻辑
4. 定义清晰的函数签名和数据流

**输出格式 (严格 JSON):**
{{
  "step_id": {actual_step.get('step_id')},
  "function_name": "建议的主函数名称",
  "function_signature": "完整的函数签名",
  "description": "函数功能描述",
  "required_libraries": ["库1", "库2"],
  "input_specification": {{
    "data_structure": "输入数据结构",
    "required_columns": ["列1", "列2"]
  }},
  "processing_steps": [
    {{
      "step_number": 1,
      "description": "步骤描述",
      "code_logic": "伪代码"
    }}
  ],
  "output_specification": {{
    "data_structure": "输出数据结构",
    "return_keys": ["key1", "key2"]
  }}
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            
            # 正确处理响应
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # 清理响应
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            execution_spec = json.loads(content)
            return execution_spec
            
        except json.JSONDecodeError as e:
            self.log(f"JSON 解析失败: {e}", "error")
            return {
                'error': f'JSON 解析失败: {e}',
                'raw_response': content,
                'step_id': actual_step.get('step_id')
            }
        except Exception as e:
            self.log(f"执行规格生成失败: {e}", "error")
            return {
                'error': str(e),
                'step_id': actual_step.get('step_id')
            }
