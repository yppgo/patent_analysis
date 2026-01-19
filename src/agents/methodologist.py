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
from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent


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

## 你的任务

生成一个 JSON 格式的技术规格书，包含以下内容：

### 1. 函数定义
- `function_name`: 函数名（如 `execute_task_1_load_data`）
- `function_signature`: 带类型提示的函数签名（如 `def func(df: pd.DataFrame) -> Dict[str, Any]:`）
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

### 4. 输出契约（Output Contract）
- 明确输出数据的结构
- 例如："Returns Dict with keys: 'total_patents' (int), 'date_range' (str)"
- 例如："Saves JSON file to outputs/task_1_data_summary.json"

### 5. 所需库
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

**示例（仅供参考格式）:**

{{
  "task_id": "task_1",
  "function_name": "execute_task_1_load_data",
  "function_signature": "def execute_task_1_load_data() -> Dict[str, Any]:",
  "docstring": "\"\"\"\\n加载专利数据并生成基本统计摘要\\n\\nReturns:\\n    Dict: 包含 total_patents, date_range, yearly_distribution\\n\"\"\"",
  "input_contract": [
    "数据文件必须存在于 data/patents.xlsx",
    "必须包含 '序号' 和 '授权日' 列"
  ],
  "logic_flow": [
    "1. 使用 pandas 读取 Excel 文件",
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

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
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
                'raw_response': content,
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
            content = response.content if hasattr(response, 'content') else str(response)
            
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
