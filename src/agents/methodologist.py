"""
Methodologist Agent - 方法论智能体
负责将战略蓝图转化为详细的技术执行规格
"""

import json
from typing import Dict, Any
from src.agents.base_agent import BaseAgent


class MethodologistAgent(BaseAgent):
    """
    方法论智能体（配方师）
    
    职责：
    1. 解析战略蓝图中的每个步骤
    2. 提取 implementation_config
    3. 将自然语言描述转化为具体的代码逻辑
    4. 输出详细的执行规格
    """
    
    def __init__(self, llm_client, logger=None):
        """
        初始化 Methodologist
        
        Args:
            llm_client: LLM 客户端
            logger: 日志记录器
        """
        super().__init__("Methodologist", llm_client, logger)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个分析步骤，生成执行规格
        
        Args:
            input_data: {
                "step": {...},  # 来自蓝图的单个步骤
                "previous_output": {...},  # 前一步的输出规格（可选）
                "step_index": int  # 步骤索引（可选）
            }
            
        Returns:
            {"execution_spec": {...}}  # 详细的执行规格
        """
        step = input_data.get('step', {})
        previous_output = input_data.get('previous_output')
        step_index = input_data.get('step_index', 1)
        
        self.log(f"开始处理步骤: {step.get('objective', 'N/A')}")
        
        # 生成执行规格（传递前置依赖信息）
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
        处理多个步骤，确保步骤间数据流一致
        
        Args:
            steps: 步骤列表
            
        Returns:
            执行规格列表
        """
        specs = []
        
        for i, step in enumerate(steps, 1):
            self.log(f"处理步骤 {i}/{len(steps)}: {step.get('objective', 'N/A')}")
            
            # 传递前一步的输出规格（如果存在）
            previous_output = specs[-1].get('output_specification') if specs else None
            
            result = self.process({
                'step': step,
                'previous_output': previous_output,
                'step_index': i
            })
            specs.append(result['execution_spec'])
        
        return specs
    
    def _generate_execution_spec(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细的执行规格"""
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
3. 如果前一步输出 Dict，这一步应该接收 Dict 或从 Dict 中提取数据
4. 如果前一步输出 DataFrame，这一步应该接收 DataFrame
5. 函数应该能处理参数为 None 的情况（在测试时可能没有前置结果）
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
5. **特别注意步骤间的文件依赖关系**
6. 指定输入输出格式

**关于新的数据流模式:**
- input_data_source.main_data: 主数据文件路径
- input_data_source.main_data_columns: 需要使用的主数据列
- input_data_source.dependencies: 需要加载的前置步骤文件
- output_files.results_csv: 保存新列的文件路径
- output_files.model_pkl: 保存模型的文件路径

**输出格式 (严格 JSON):**
{{
  "step_id": {actual_step.get('step_id')},
  "function_name": "建议的主函数名称（如 detect_technology_gaps）",
  "function_signature": "完整的函数签名（如 def detect_technology_gaps(df: pd.DataFrame) -> Dict[str, Any]）",
  "description": "函数功能描述",
  "required_libraries": ["库1", "库2", "库3"],
  "library_versions": {{
    "库1": "版本号或latest",
    "库2": "版本号或latest"
  }},
  "input_specification": {{
    "data_structure": "输入数据结构（如 DataFrame）",
    "required_columns": ["列1", "列2"],
    "load_dependencies": ["需要加载的文件路径"],
    "sample_data_description": "如何生成合成数据的描述"
  }},
  "processing_steps": [
    {{
      "step_number": 1,
      "description": "步骤描述",
      "code_logic": "伪代码或关键代码片段",
      "key_parameters": {{"参数名": "参数值"}}
    }}
  ],
  "output_specification": {{
    "data_structure": "输出数据结构（dict）",
    "expected_format": "预期格式描述",
    "return_keys": ["key1", "key2"],
    "save_to_files": {{
      "results_csv": "保存新列的文件路径",
      "model_pkl": "保存模型的文件路径（如果有）"
    }}
  }},
  "error_handling": ["需要处理的异常类型1", "异常类型2"],
  "validation_criteria": ["验证标准1", "验证标准2"],
  "performance_notes": "性能考虑和优化建议"
}}

请直接输出 JSON，不要包含任何其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            
            # 处理 AIMessage 对象
            if hasattr(response, 'content'):
                content = response.content
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
            
            # 验证必要字段
            required_fields = ['function_name', 'required_libraries', 'processing_steps']
            for field in required_fields:
                if field not in execution_spec:
                    self.log(f"警告: 缺少必要字段 {field}", "warning")
            
            return execution_spec
            
        except json.JSONDecodeError as e:
            self.log(f"JSON 解析失败: {e}", "error")
            return {
                'error': f'JSON 解析失败: {e}',
                'raw_response': response,
                'step_id': step.get('step_id')
            }
        except Exception as e:
            self.log(f"执行规格生成失败: {e}", "error")
            return {
                'error': str(e),
                'step_id': step.get('step_id')
            }
    
    def validate_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证执行规格的完整性
        
        Args:
            spec: 执行规格
            
        Returns:
            验证结果 {"valid": bool, "issues": []}
        """
        issues = []
        
        # 检查必要字段
        required_fields = [
            'function_name', 'required_libraries', 'processing_steps',
            'input_specification', 'output_specification'
        ]
        
        for field in required_fields:
            if field not in spec:
                issues.append(f"缺少必要字段: {field}")
        
        # 检查函数名格式
        if 'function_name' in spec:
            func_name = spec['function_name']
            if not func_name.isidentifier():
                issues.append(f"函数名格式不正确: {func_name}")
        
        # 检查处理步骤
        if 'processing_steps' in spec:
            steps = spec['processing_steps']
            if not isinstance(steps, list) or len(steps) == 0:
                issues.append("processing_steps 应该是非空列表")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
