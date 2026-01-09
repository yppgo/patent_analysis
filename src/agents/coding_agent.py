"""
Coding Agent V2 - 编码智能体
基于 LangGraph create_react_agent 的简化实现
"""

import json
import pandas as pd
from typing import Dict, Any, List
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent


class CodingAgentV2(BaseAgent):
    """
    编码智能体 V2（执行者）
    
    使用 LangGraph 的 create_react_agent 自动管理 ReAct 流程：
    - 工具：generate_code, test_code, check_code
    - LLM 自动决定工具调用顺序和时机
    
    核心创新：运行时测试 + 自动修复
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=3, logger=None):
        """
        初始化 Coding Agent V2
        
        Args:
            llm_client: LLM 客户端
            test_data: 测试数据（DataFrame）
            max_iterations: 最大迭代次数
            logger: 日志记录器
        """
        super().__init__("CodingAgentV2", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        
        # 存储当前执行上下文
        self.current_execution_spec = None
        self.current_test_data = None
        self.iteration_count = 0
        self.generated_code = ""
        self.execution_result = None
        
        # 创建工具和 agent
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理执行规格，生成高质量代码
        
        Args:
            input_data: {
                "execution_spec": {...},
                "current_step": {...},
                "test_data": DataFrame (可选)
            }
            
        Returns:
            {
                "generated_code": str,
                "iteration_count": int,
                "is_code_valid": bool,
                "code_issues": List[str],
                "runtime_error": str,
                "execution_result": Dict (可选)
            }
        """
        execution_spec = input_data.get('execution_spec', {})
        test_data = input_data.get('test_data', self.test_data)
        
        # 设置执行上下文
        self.current_execution_spec = execution_spec
        self.current_test_data = test_data
        self.iteration_count = 0
        self.generated_code = ""
        self.execution_result = None
        
        func_name = execution_spec.get('function_name', 'N/A')
        print(f"\n{'='*60}")
        print(f"开始生成代码: {func_name}")
        print(f"{'='*60}")
        self.log(f"开始生成代码: {func_name}")
        
        # 构建初始消息（包含系统提示和数据预览）
        has_test_data = test_data is not None and len(test_data) > 0
        
        # 生成数据预览
        data_preview = ""
        if has_test_data:
            data_preview = f"""
数据预览：
- 数据形状: {test_data.shape[0]} 行 × {test_data.shape[1]} 列
- 列名: {list(test_data.columns)}
- 数据类型: {dict(test_data.dtypes.astype(str))}
- 前3行样本:
{test_data.head(3).to_string()}

重要提示：
- 数据已经加载在变量 df 中
- 请根据实际的列名编写代码
- 使用 df.iloc[i] 访问行，使用 df['列名'] 访问列
"""
        
        initial_message = f"""你是专业的 Python 代码生成专家。

请根据以下执行规格生成高质量的 Python 代码：

执行规格：
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}
{data_preview}
测试数据状态：{'✅ 已提供测试数据，必须进行运行时测试' if has_test_data else '❌ 无测试数据，只进行静态检查'}

工作流程：
1. 使用 generate_code 工具生成代码
2. 使用 check_code 工具进行静态检查
3. {'使用 test_code 工具进行运行时测试（必须执行）' if has_test_data else '跳过运行时测试（无测试数据）'}
4. 如果发现问题，使用 generate_code 重新生成（传入问题描述）
5. 重复直到代码通过所有检查或达到最大迭代次数

注意：
- 最多迭代 {self.max_iterations} 次
- 优先修复运行时错误
- 确保代码有完整的错误处理
- {'必须调用 test_code 工具测试代码' if has_test_data else '无需运行时测试'}

请严格按照工作流程执行，不要跳过任何步骤！"""
        
        # 调用 agent
        result = self.agent.invoke({
            "messages": [("user", initial_message)]
        })
        
        # 从消息历史中提取结果
        final_result = self._extract_final_result(result)
        
        print(f"\n{'='*60}")
        print(f"代码生成完成: 迭代 {self.iteration_count} 次")
        print(f"代码有效: {final_result['is_code_valid']}")
        print(f"{'='*60}\n")
        self.log(f"代码生成完成: 迭代 {self.iteration_count} 次")
        
        return final_result
    
    def _create_tools(self) -> List:
        """创建工具列表"""
        
        # 保存 self 引用
        agent_self = self
        
        @tool
        def generate_code(issues_to_fix: str = "") -> str:
            """
            生成 Python 代码
            
            Args:
                issues_to_fix: 需要修复的问题描述（可选）
            
            Returns:
                生成的代码
            """
            print(f"\n⚡ [工具] 生成代码... (第 {agent_self.iteration_count + 1} 次)")
            agent_self.log("⚡ [工具] 生成代码...")
            agent_self.iteration_count += 1
            
            if agent_self.iteration_count > agent_self.max_iterations:
                msg = f"已达到最大迭代次数 ({agent_self.max_iterations})，停止生成"
                print(f"  ⚠️ {msg}")
                return msg
            
            execution_spec = agent_self.current_execution_spec
            
            prompt = f"""你是 Python 工程师。生成代码。

**执行规格:**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}
"""
            
            if issues_to_fix:
                prompt += f"""
**需要修复的问题:**
{issues_to_fix}

**请特别注意修复这些问题！**
"""
            
            prompt += f"""
**代码要求:**
1. 函数签名必须是: def {execution_spec.get('function_name', 'analyze')}(df: pd.DataFrame) -> Dict[str, Any]
2. 必须有完整的类型注解和中文注释
3. 必须有 try-except 错误处理
4. 使用 df.iloc[i] 而不是 df.loc[i]
5. 不要包含任何 import 语句
6. 只输出函数代码，不要有任何其他内容

**重要**: 直接输出函数代码，不要用 markdown 代码块包裹，不要有任何解释文字。"""
            
            try:
                response = agent_self.llm.invoke(prompt)
                code = agent_self._extract_code(response.content if hasattr(response, 'content') else str(response))
                agent_self.generated_code = code
                lines = len(code.split(chr(10)))
                print(f"  ✓ 代码生成成功 ({lines} 行)")
                agent_self.log(f"  ✓ 代码生成成功 ({lines} 行)")
                return code
            except Exception as e:
                print(f"  ⚠️ 代码生成失败: {e}")
                agent_self.log(f"  ⚠️ 代码生成失败: {e}", "warning")
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
            print("\n🧪 [工具] 运行时测试...")
            agent_self.log("🧪 [工具] 运行时测试...")
            
            test_data = agent_self.current_test_data
            if test_data is None or len(test_data) == 0:
                print("  ⚠️ 没有测试数据，跳过")
                agent_self.log("  ⚠️ 没有测试数据，跳过")
                return "没有测试数据，跳过运行时测试"
            
            print(f"  📊 使用 {len(test_data)} 条数据测试...")
            agent_self.log(f"  📊 使用 {len(test_data)} 条数据测试...")
            
            try:
                exec_globals = agent_self._prepare_execution_environment(test_data)
                exec(code, exec_globals)
                
                func_name = agent_self.current_execution_spec.get('function_name', 'analyze')
                if func_name in exec_globals:
                    result = exec_globals[func_name](test_data)
                    
                    if isinstance(result, dict) and 'error' in result:
                        error_msg = result['error']
                        print(f"  ⚠️ 函数返回错误: {error_msg}")
                        agent_self.log(f"  ⚠️ 函数返回错误: {error_msg}")
                        return f"运行时错误: {error_msg}"
                    else:
                        print("  ✅ 运行时测试通过")
                        agent_self.log("  ✅ 运行时测试通过")
                        agent_self.execution_result = agent_self._serialize_result(result)
                        return "运行时测试通过"
                else:
                    error_msg = f"函数 {func_name} 未找到"
                    print(f"  ⚠️ {error_msg}")
                    agent_self.log(f"  ⚠️ {error_msg}")
                    return f"错误: {error_msg}"
            except Exception as e:
                error_msg = str(e)
                print(f"  ⚠️ 运行时错误: {error_msg}")
                agent_self.log(f"  ⚠️ 运行时错误: {error_msg}")
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
            print("\n👀 [工具] 静态检查...")
            agent_self.log("👀 [工具] 静态检查...")
            
            issues = agent_self._static_code_check(code, agent_self.current_execution_spec)
            
            if not issues:
                print("  ✅ 静态检查通过")
                agent_self.log("  ✅ 静态检查通过")
                return "静态检查通过"
            else:
                print(f"  ⚠️ 发现 {len(issues)} 个问题")
                agent_self.log(f"  ⚠️ 发现 {len(issues)} 个问题")
                for issue in issues:
                    print(f"    - {issue}")
                    agent_self.log(f"    - {issue}")
                return "发现问题:\n" + "\n".join(f"- {issue}" for issue in issues)
        
        return [generate_code, test_code, check_code]
    
    def _build_agent(self):
        """使用 create_react_agent 构建 agent"""
        
        # 获取底层的 ChatOpenAI 实例
        llm_instance = self.llm.get_llm() if hasattr(self.llm, 'get_llm') else self.llm
        
        # 使用 create_react_agent 创建 agent
        # 系统提示会在 process 方法中通过初始消息传递
        agent = create_react_agent(
            llm_instance,
            self.tools
        )
        
        return agent
    
    def _extract_final_result(self, agent_result: Dict) -> Dict[str, Any]:
        """从 agent 结果中提取最终结果"""
        messages = agent_result.get("messages", [])
        
        # 查找最后的工具调用结果
        last_test_result = ""
        last_check_result = ""
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # 记录最后的测试和检查结果
            if "运行时测试通过" in content:
                last_test_result = "通过"
            elif "运行时错误" in content:
                last_test_result = content
            
            if "静态检查通过" in content:
                last_check_result = "通过"
            elif "发现问题" in content:
                last_check_result = content
        
        # 判断代码是否有效：最后的检查和测试都通过
        is_code_valid = (
            self.generated_code and
            last_check_result == "通过" and
            (last_test_result == "通过" or last_test_result == "")
        )
        
        # 提取错误信息
        runtime_error = last_test_result if last_test_result != "通过" and last_test_result != "" else ""
        code_issues = [last_check_result] if last_check_result != "通过" and last_check_result != "" else []
        
        return {
            'generated_code': self.generated_code,
            'iteration_count': self.iteration_count,
            'is_code_valid': is_code_valid,
            'code_issues': code_issues,
            'runtime_error': runtime_error,
            'execution_result': self.execution_result
        }

    def _extract_code(self, response: str) -> str:
        """从响应中提取代码"""
        code = response.strip()
        
        if code.startswith("```"):
            lines = code.split("\n")
            code_lines = []
            in_code = False
            
            for line in lines:
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)
            
            code = "\n".join(code_lines)
        
        # 移除 import 语句
        code_lines = code.split("\n")
        filtered_lines = []
        for line in code_lines:
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                filtered_lines.append(line)
        
        return "\n".join(filtered_lines)
    
    def _static_code_check(self, code: str, execution_spec: Dict) -> List[str]:
        """静态代码检查"""
        issues = []
        
        # 基本检查
        if not code or len(code.strip()) < 50:
            issues.append("代码为空或过短")
        
        func_name = execution_spec.get('function_name', 'analyze')
        if f"def {func_name}" not in code:
            issues.append(f"缺少函数定义: {func_name}")
        
        if "return" not in code:
            issues.append("缺少 return 语句")
        
        if "try:" not in code or "except" not in code:
            issues.append("缺少错误处理")
        
        if "Dict" not in code and "dict" not in code.lower():
            issues.append("缺少返回类型注解")
        
        # 语法检查
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            issues.append(f"语法错误: {e}")
        
        return issues
    
    def _serialize_result(self, result: Any) -> Dict[str, Any]:
        """
        序列化执行结果，使其可以JSON化
        
        处理常见的数据类型：
        - DataFrame -> dict
        - numpy array -> list
        - 其他复杂对象 -> str
        """
        import numpy as np
        
        if result is None:
            return {'type': 'none', 'value': None}
        
        if isinstance(result, dict):
            serialized = {}
            for key, value in result.items():
                if isinstance(value, pd.DataFrame):
                    # DataFrame转为字典，保留前100行
                    serialized[key] = {
                        'type': 'dataframe',
                        'shape': value.shape,
                        'columns': list(value.columns),
                        'sample': value.head(100).to_dict('records')
                    }
                elif isinstance(value, (np.ndarray, list)):
                    # 数组转为列表，保留前100个元素
                    arr = np.array(value) if not isinstance(value, np.ndarray) else value
                    serialized[key] = {
                        'type': 'array',
                        'shape': arr.shape if hasattr(arr, 'shape') else len(arr),
                        'sample': arr.flatten()[:100].tolist() if hasattr(arr, 'flatten') else list(value)[:100]
                    }
                elif isinstance(value, (int, float, str, bool)):
                    serialized[key] = value
                else:
                    # 其他类型转为字符串
                    serialized[key] = {
                        'type': 'object',
                        'value': str(value)[:500]  # 限制长度
                    }
            return serialized
        else:
            # 非字典结果
            return {
                'type': 'raw',
                'value': str(result)[:1000]
            }
    
    def _prepare_execution_environment(self, test_data):
        """准备代码执行环境"""
        import numpy as np
        
        # 导入常用的分析库
        try:
            from pyod.models.abod import ABOD
        except ImportError:
            class MockABOD:
                def __init__(self, *args, **kwargs): pass
                def fit_predict(self, data): return [1] * len(data)
            ABOD = MockABOD
        
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            class MockSentenceTransformer:
                def __init__(self, *args, **kwargs): pass
                def encode(self, texts): return [[0.1] * 384] * len(texts)
            SentenceTransformer = MockSentenceTransformer
        
        # 导入gensim相关
        try:
            from gensim import corpora
            from gensim.models import LdaModel
            from gensim.utils import simple_preprocess
        except ImportError:
            corpora = None
            LdaModel = None
            simple_preprocess = None
        
        # 导入nltk相关
        try:
            from nltk.corpus import stopwords
        except ImportError:
            class MockStopwords:
                @staticmethod
                def words(lang): return []
            stopwords = MockStopwords()
        
        # 导入sklearn相关
        try:
            from sklearn.cluster import DBSCAN
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            DBSCAN = None
            TfidfVectorizer = None
            cosine_similarity = None
        
        # 导入其他常用库
        try:
            import re
        except ImportError:
            re = None
        
        return {
            'pd': pd,
            'np': np,
            'df': test_data,
            'Dict': Dict,
            'List': List,
            'Any': Any,
            'Tuple': tuple,
            # 分析库
            'ABOD': ABOD,
            'SentenceTransformer': SentenceTransformer,
            'corpora': corpora,
            'LdaModel': LdaModel,
            'simple_preprocess': simple_preprocess,
            'stopwords': stopwords,
            'DBSCAN': DBSCAN,
            'TfidfVectorizer': TfidfVectorizer,
            'cosine_similarity': cosine_similarity,
            're': re,
            '__builtins__': __builtins__
        }
