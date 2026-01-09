"""
Coding Agent V3 - 基于 LangGraph create_react_agent 的简化实现
"""

import json
import pandas as pd
from typing import Dict, Any, List, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent


class CodingAgentV3(BaseAgent):
    """
    编码智能体 V3 - 使用 LangGraph 预构建的 ReAct agent
    
    核心改进：
    1. 使用 create_react_agent 替代手动状态图
    2. 将节点函数转换为工具（tools）
    3. LLM 自动决定工具调用顺序
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=3, logger=None):
        super().__init__("CodingAgentV3", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        
        # 存储当前执行上下文
        self.current_execution_spec = None
        self.current_test_data = None
        self.iteration_count = 0
        
        # 获取原始 LLM 实例（用于 create_react_agent）
        self.raw_llm = llm_client.get_llm() if hasattr(llm_client, 'get_llm') else llm_client
        
        # 创建工具和 agent
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行规格，生成高质量代码"""
        execution_spec = input_data.get('execution_spec', {})
        test_data = input_data.get('test_data', self.test_data)
        previous_result = input_data.get('previous_result')  # 新增：前一步的实际输出
        previous_error = input_data.get('previous_error')  # 新增：前一次执行的错误
        
        # 设置执行上下文
        self.current_execution_spec = execution_spec
        self.current_test_data = test_data
        self.current_previous_result = previous_result
        self.current_previous_error = previous_error
        self.iteration_count = 0
        
        func_name = execution_spec.get('function_name', 'N/A')
        self.log(f"开始生成代码: {func_name}")
        
        # 构建初始消息 (包含系统提示)
        # 构建前置信息
        context_info = ""
        if previous_result is not None:
            context_info += f"""
**📦 前一步的实际输出：**
类型: {type(previous_result)}
"""
            if isinstance(previous_result, dict):
                context_info += f"键: {list(previous_result.keys())}\n"
                # 显示部分数据
                for key, value in list(previous_result.items())[:3]:
                    context_info += f"  - {key}: {type(value)}\n"
            elif isinstance(previous_result, pd.DataFrame):
                context_info += f"形状: {previous_result.shape}\n"
                context_info += f"列: {list(previous_result.columns)}\n"
        
        if previous_error:
            context_info += f"""
**⚠️ 前一次执行的错误：**
{previous_error}

请特别注意修复这个错误！
"""
        
        initial_message = f"""{self.system_message}

请根据以下执行规格生成高质量的 Python 代码：

执行规格：
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}
{context_info}

要求：
1. 使用 generate_code 工具生成代码
2. 使用 test_code 工具进行运行时测试（如果有测试数据）
3. 使用 check_code 工具进行静态检查
4. 如果发现问题，重新生成改进的代码
5. 最多迭代 {self.max_iterations} 次

请开始！"""
        
        # 调用 agent
        result = self.agent.invoke({
            "messages": [("user", initial_message)]
        })
        
        # 从消息历史中提取结果
        final_result = self._extract_final_result(result)
        
        self.log(f"代码生成完成: 迭代 {self.iteration_count} 次")
        
        return final_result
    
    def _create_tools(self) -> List:
        """创建工具列表"""
        
        @tool
        def generate_code(issues_to_fix: str = "") -> str:
            """
            生成 Python 代码
            
            Args:
                issues_to_fix: 需要修复的问题描述（可选）
            
            Returns:
                生成的代码
            """
            self.log("⚡ [工具] 生成代码...")
            self.iteration_count += 1
            
            if self.iteration_count > self.max_iterations:
                return "已达到最大迭代次数，停止生成"
            
            execution_spec = self.current_execution_spec
            previous_result = self.current_previous_result
            
            # 构建前置结果信息
            prev_result_info = ""
            if previous_result is not None:
                prev_result_info = f"""
**🔗 前一步的实际输出（你需要处理这个数据）：**
类型: {type(previous_result).__name__}
"""
                if isinstance(previous_result, tuple):
                    prev_result_info += f"Tuple 长度: {len(previous_result)}\n"
                    prev_result_info += "Tuple 元素:\n"
                    for i, item in enumerate(previous_result):
                        prev_result_info += f"  [{i}] {type(item).__name__}"
                        if isinstance(item, pd.DataFrame):
                            prev_result_info += f" - 形状: {item.shape}, 列: {list(item.columns)[:5]}\n"
                        elif isinstance(item, dict):
                            prev_result_info += f" - 键: {list(item.keys())[:5]}\n"
                        else:
                            prev_result_info += f" - {str(item)[:50]}...\n"
                    
                    prev_result_info += """
**🔥 Tuple 处理示例：**
```python
def your_function(df, previous_result=None):
    if previous_result is not None:
        # 解包 tuple
        item1, item2 = previous_result
        # 或者按索引访问
        dataframe_part = previous_result[0]
        dict_part = previous_result[1]
```
"""
                elif isinstance(previous_result, dict):
                    prev_result_info += f"字典键: {list(previous_result.keys())}\n"
                    prev_result_info += "示例数据:\n"
                    for key, value in list(previous_result.items())[:2]:
                        prev_result_info += f"  {key}: {type(value).__name__} - {str(value)[:100]}...\n"
                elif isinstance(previous_result, pd.DataFrame):
                    prev_result_info += f"DataFrame 形状: {previous_result.shape}\n"
                    prev_result_info += f"列名: {list(previous_result.columns)}\n"
                    prev_result_info += f"前3行:\n{previous_result.head(3).to_string()}\n"
                
                prev_result_info += """
**重要提示：**
- 如果函数需要这个结果作为参数，请添加对应的参数（如 previous_result = None）
- 函数内部应该检查参数是否为 None
- **如果是 tuple，必须先解包**
- 使用实际的列名（不要假设列名）
- 如果为 None，可以返回空结果或使用默认逻辑
"""
            
            prompt = f"""你是 Python 工程师。生成代码。

**执行规格:**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}
{prev_result_info}
"""
            
            if issues_to_fix:
                prompt += f"""
**需要修复的问题:**
{issues_to_fix}

**请特别注意修复这些问题！**
"""
            
            prompt += f"""
**代码要求:**
1. 生成完整可运行的 Python 代码
2. 包含所有必要的 import 语句（pandas, numpy, sklearn 等）
3. 函数签名: def {execution_spec.get('function_name', 'analyze')}(df: pd.DataFrame, ...) -> Dict[str, Any]
4. 完整的类型注解（from typing import Dict, List, Any, Tuple, Optional）
5. 完整的中文注释和文档字符串
6. 完整的错误处理（try-except）
7. 使用 df.iloc[i] 而不是 df.loc[i]
8. 代码应该可以直接保存为 .py 文件运行

**🚨 关键：列名映射**
执行规格中的列名可能是假设的，你必须映射到实际列名：

常见映射规则（基于 preview_data 看到的实际列名）：
- '专利标题' → '标题(译)(简体中文)'
- '摘要' → '摘要(译)(简体中文)'
- '全文' → 如果不存在，使用 '标题(译)(简体中文)' + '摘要(译)(简体中文)' 的组合

**必须**：
1. 先查看 preview_data 的输出，了解实际列名
2. 将执行规格中的假设列名映射到实际列名
3. 在代码中使用实际列名，不要使用假设列名
4. 如果某个列不存在，用相似的列或组合列代替

**🔗 多参数函数处理**：
如果函数需要多个参数（如依赖前一步的结果）：
- 其他参数应该有默认值 None
- 函数内部应该处理 None 的情况（如果为 None，则在函数内部构建）
- 例如：`def detect_gaps(df, graph=None):`
  - 如果 graph 为 None，在函数内部从 df 构建 graph
  - 如果 graph 不为 None，直接使用

**输出格式:**
直接输出纯 Python 代码，不要有任何解释、说明或 markdown 标记。
不要使用 ```python 代码块标记。
只输出可以直接执行的 Python 代码。"""
            
            try:
                response = self.llm.invoke(prompt)
                code = self._extract_code(response.content if hasattr(response, 'content') else str(response))
                self.log(f"  ✓ 代码生成成功 ({len(code.split(chr(10)))} 行)")
                return code
            except Exception as e:
                self.log(f"  ⚠️ 代码生成失败: {e}", "warning")
                return f"代码生成失败: {e}"
        
        @tool
        def test_code(code: str) -> str:
            """
            使用真实数据测试代码
            
            Args:
                code: 要测试的代码
            
            Returns:
                测试结果（成功或错误信息）
            """
            self.log("🧪 [工具] 运行时测试...")
            
            test_data = self.current_test_data
            if test_data is None or len(test_data) == 0:
                self.log("  ⚠️ 没有测试数据，跳过")
                return "没有测试数据，跳过运行时测试"
            
            self.log(f"  📊 使用 {len(test_data)} 条数据测试...")
            
            try:
                exec_globals = self._prepare_execution_environment(test_data)
                exec(code, exec_globals)
                
                func_name = self.current_execution_spec.get('function_name', 'analyze')
                if func_name in exec_globals:
                    func = exec_globals[func_name]
                    
                    # 智能处理函数参数
                    import inspect
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    
                    if len(params) == 1:
                        # 单参数函数，直接调用
                        result = func(test_data)
                    else:
                        # 多参数函数，其他参数传 None（函数应该处理 None 的情况）
                        args = [test_data]
                        for param_name in params[1:]:
                            param = sig.parameters[param_name]
                            if param.default != inspect.Parameter.empty:
                                # 有默认值，不传
                                break
                            else:
                                # 传 None
                                args.append(None)
                        
                        result = func(*args)
                    
                    # 检查结果是否包含错误
                    if isinstance(result, dict) and 'error' in result:
                        error_msg = result['error']
                        self.log(f"  ⚠️ 函数返回错误: {error_msg}")
                        return f"运行时错误: {error_msg}"
                    else:
                        self.log("  ✅ 运行时测试通过")
                        return "运行时测试通过"
                else:
                    error_msg = f"函数 {func_name} 未找到"
                    self.log(f"  ⚠️ {error_msg}")
                    return f"错误: {error_msg}"
            except KeyError as e:
                # KeyError 通常表示数据依赖问题
                error_msg = f"KeyError: {e} - 可能是前一步的输出格式不匹配"
                self.log(f"  ⚠️ 运行时错误: {error_msg}")
                return f"运行时错误: {error_msg}"
            except Exception as e:
                error_msg = str(e)
                self.log(f"  ⚠️ 运行时错误: {error_msg}")
                return f"运行时错误: {error_msg}"
        
        @tool
        def check_code(code: str) -> str:
            """
            静态检查代码质量
            
            Args:
                code: 要检查的代码
            
            Returns:
                检查结果（问题列表或"通过"）
            """
            self.log("👀 [工具] 静态检查...")
            
            issues = self._static_code_check(code, self.current_execution_spec)
            
            if not issues:
                self.log("  ✅ 静态检查通过")
                return "静态检查通过"
            else:
                self.log(f"  ⚠️ 发现 {len(issues)} 个问题")
                for issue in issues:
                    self.log(f"    - {issue}")
                return "发现问题:\n" + "\n".join(f"- {issue}" for issue in issues)
        
        @tool
        def preview_data() -> str:
            """
            预览测试数据的结构和内容
            
            Returns:
                数据预览信息（列名、数据类型、前几行数据）
            """
            self.log("📊 [工具] 预览数据...")
            
            test_data = self.current_test_data
            if test_data is None or len(test_data) == 0:
                return "没有可用的测试数据"
            
            try:
                preview = f"""数据预览:
- 行数: {len(test_data)}
- 列数: {len(test_data.columns)}
- 列名: {list(test_data.columns)}
- 数据类型:
{test_data.dtypes.to_string()}

前5行数据:
{test_data.head().to_string()}
"""
                self.log("  ✅ 数据预览完成")
                return preview
            except Exception as e:
                error_msg = f"数据预览失败: {e}"
                self.log(f"  ⚠️ {error_msg}")
                return error_msg
        
        return [preview_data, generate_code, test_code, check_code]
    
    def _build_agent(self):
        """使用 create_react_agent 构建 agent"""
        
        # 系统提示将在 process 方法中添加到初始消息
        self.system_message = f"""你是专业的 Python 代码生成专家。

你的任务是生成完整可运行的 Python 代码。

工作流程：
1. 🔍 **首先使用 preview_data 工具查看数据结构**（了解实际的列名、数据类型、前几行数据）
2. 使用 generate_code 生成完整的代码（包含所有 import，使用实际的列名）
3. 使用 check_code 进行静态检查
4. 🧪 **使用 test_code 进行运行时测试**（验证代码能在真实数据上运行）
5. 如果发现问题，使用 generate_code 重新生成（传入问题描述）
6. 重复直到代码通过所有检查或达到最大迭代次数

注意：
- 最多迭代 {self.max_iterations} 次
- **必须先预览数据，了解实际的列名和数据结构**
- 生成的代码必须使用实际的列名（不要假设列名）
- 代码必须包含所有必要的 import 语句
- 代码应该是完整可运行的，可以直接保存为 .py 文件
- 确保代码有完整的错误处理
- **运行时测试很重要**：确保代码能在真实数据上运行"""
        
        # 使用 create_react_agent 创建 agent (只传入必需参数)
        agent = create_react_agent(
            self.raw_llm,  # 使用原始 LLM 实例
            self.tools
        )
        
        return agent
    
    def _extract_final_result(self, agent_result: Dict) -> Dict[str, Any]:
        """从 agent 结果中提取最终结果"""
        messages = agent_result.get("messages", [])
        
        # 查找最后生成的代码
        generated_code = ""
        runtime_error = ""
        code_issues = []
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # 提取代码
            if "def " in content and "return" in content:
                generated_code = self._extract_code(content)
            
            # 提取错误信息
            if "运行时错误" in content:
                runtime_error = content
            elif "发现问题" in content:
                code_issues.append(content)
        
        # 判断代码是否有效
        is_code_valid = (
            generated_code and
            not runtime_error and
            not code_issues
        )
        
        return {
            'generated_code': generated_code,
            'iteration_count': self.iteration_count,
            'is_code_valid': is_code_valid,
            'code_issues': code_issues,
            'runtime_error': runtime_error,
            'execution_result': None  # TODO: 保存执行结果
        }
    
    def _extract_code(self, response: str) -> str:
        """从响应中提取代码 - 双重防护"""
        code = response.strip()
        
        # 方法1: 查找代码块标记
        if "```" in code:
            lines = code.split("\n")
            code_lines = []
            in_code = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    if not in_code:
                        # 开始代码块
                        in_code = True
                    else:
                        # 结束代码块
                        break
                    continue
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                code = "\n".join(code_lines)
        
        # 方法2: 如果没有代码块，查找第一个 import 或 def 开始的位置
        if not code.startswith(("import ", "from ", "def ")):
            lines = code.split("\n")
            start_idx = -1
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(("import ", "from ", "def ")):
                    start_idx = i
                    break
            
            if start_idx >= 0:
                code = "\n".join(lines[start_idx:])
        
        # 方法3: 移除开头的中文解释
        lines = code.split("\n")
        filtered_lines = []
        started = False
        
        for line in lines:
            stripped = line.strip()
            # 如果遇到 import 或 def，开始收集
            if not started and (stripped.startswith(("import ", "from ", "def ", "#"))):
                started = True
            
            if started:
                filtered_lines.append(line)
        
        if filtered_lines:
            code = "\n".join(filtered_lines)
        
        return code.strip()
    
    def _static_code_check(self, code: str, execution_spec: Dict) -> List[str]:
        """静态代码检查"""
        issues = []
        
        if not code or len(code.strip()) < 50:
            issues.append("代码为空或过短")
        
        func_name = execution_spec.get('function_name', 'analyze')
        if f"def {func_name}" not in code:
            issues.append(f"缺少函数定义: {func_name}")
        
        if "return" not in code:
            issues.append("缺少 return 语句")
        
        if "try:" not in code or "except" not in code:
            issues.append("缺少错误处理")
        
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            issues.append(f"语法错误: {e}")
        
        return issues
    
    def _prepare_execution_environment(self, test_data):
        """准备代码执行环境 - 导入真实的库"""
        import numpy as np
        from typing import Dict, List, Any, Tuple, Optional, Set
        
        # 导入常用的数据科学库
        try:
            from gensim import corpora, models
            from gensim.utils import simple_preprocess
        except ImportError:
            corpora = None
            models = None
            simple_preprocess = None
        
        try:
            from nltk.corpus import stopwords
        except ImportError:
            stopwords = None
        
        try:
            from sklearn.cluster import DBSCAN, AgglomerativeClustering
            from sklearn.ensemble import IsolationForest
        except ImportError:
            DBSCAN = None
            AgglomerativeClustering = None
            IsolationForest = None
        
        try:
            from pyod.models.abod import ABOD
        except ImportError:
            ABOD = None
        
        env = {
            'pd': pd,
            'np': np,
            'df': test_data,
            'Dict': Dict,
            'List': List,
            'Any': Any,
            'Tuple': Tuple,
            'Optional': Optional,
            'Set': Set,
            '__builtins__': __builtins__
        }
        
        # 只添加成功导入的库
        if corpora: env['corpora'] = corpora
        if models: env['models'] = models
        if simple_preprocess: env['simple_preprocess'] = simple_preprocess
        if stopwords: env['stopwords'] = stopwords
        if DBSCAN: env['DBSCAN'] = DBSCAN
        if AgglomerativeClustering: env['AgglomerativeClustering'] = AgglomerativeClustering
        if IsolationForest: env['IsolationForest'] = IsolationForest
        if ABOD: env['ABOD'] = ABOD
        
        return env
