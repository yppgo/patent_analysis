"""
Coding Agent V4 - 基于 Geimin 反馈的生产级改进

核心改进：
1. ✅ 安全性：使用 subprocess 替代 exec，防止代码注入
2. ✅ 状态管理：移除实例变量，通过工具参数传递上下文
3. ✅ 简化架构：让 Agent 直接生成代码，工具只负责测试和检查
"""

import json
import sys
import tempfile
import subprocess
import os
import pandas as pd
from io import StringIO
from typing import Dict, Any, List, Optional
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent


class CodingAgentV4(BaseAgent):
    """
    编码智能体 V4 - 生产级实现
    
    关键改进：
    1. 安全的代码执行（subprocess + 沙箱）
    2. 无状态工具设计（避免并发污染）
    3. 简化的工具链（Agent 自己写代码）
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=3, logger=None):
        super().__init__("CodingAgentV4", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        
        # 获取原始 LLM 实例（用于 create_react_agent）
        self.raw_llm = llm_client.get_llm() if hasattr(llm_client, 'get_llm') else llm_client
        
        # 创建工具和 agent
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行规格，生成高质量代码"""
        execution_spec = input_data.get('execution_spec', {})
        test_data = input_data.get('test_data', self.test_data)
        previous_result = input_data.get('previous_result')
        previous_error = input_data.get('previous_error')
        
        # 更新 test_data（如果传入了新数据）
        if test_data is not None:
            self.test_data = test_data
        
        func_name = execution_spec.get('function_name', 'N/A')
        self.log(f"🚀 开始生成代码: {func_name}")
        
        # 构建上下文信息
        context_info = self._build_context_info(previous_result, previous_error)
        
        # 构建初始提示
        initial_message = self._build_initial_prompt(
            execution_spec, 
            context_info,
            test_data
        )
        
        # 调用 agent（状态在 LangGraph 中流转）
        result = self.agent.invoke({
            "messages": [("user", initial_message)],
            # 通过配置传递上下文（而不是实例变量）
            "configurable": {
                "execution_spec": execution_spec,
                "test_data": test_data,
                "max_iterations": self.max_iterations
            }
        })
        
        # 提取最终结果
        final_result = self._extract_final_result(result)
        
        self.log(f"✅ 代码生成完成")
        
        return final_result
    
    def _create_tools(self) -> List:
        """创建工具列表 - 无状态设计"""
        
        # 注意：这里我们不再有 generate_code 工具
        # Agent 会直接在消息中生成代码，然后调用测试工具
        
        @tool
        def run_python_code(
            code: str,
            test_data_json: str = None,
            function_name: str = "analyze",
            timeout: int = 30
        ) -> str:
            """
            在隔离的 subprocess 中安全执行 Python 代码
            
            Args:
                code: 要执行的 Python 代码
                test_data_json: 测试数据的 JSON 字符串（可选）
                function_name: 要调用的函数名
                timeout: 超时时间（秒）
            
            Returns:
                执行结果或错误信息
            """
            self.log("🧪 [工具] 安全执行代码（subprocess）...")
            
            if not test_data_json:
                return "⚠️ 没有测试数据，跳过执行"
            
            # 1. 创建临时数据文件
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".parquet", 
                    delete=False, 
                    mode='wb'
                ) as tmp_data:
                    # 使用 StringIO 避免 FutureWarning
                    # 处理可能的 JSON 格式问题
                    try:
                        df = pd.read_json(StringIO(test_data_json), orient='split')
                    except (ValueError, AttributeError) as e:
                        # 如果 orient='split' 失败，尝试其他格式
                        try:
                            df = pd.read_json(StringIO(test_data_json))
                        except Exception as e2:
                            return f"❌ 数据解析失败: {e2}"
                    
                    df.to_parquet(tmp_data.name)
                    data_path = tmp_data.name
            except Exception as e:
                return f"❌ 数据准备失败: {e}"
            
            # 2. 包装用户代码
            wrapper_code = self._create_wrapper_code(
                code, 
                data_path, 
                function_name
            )
            
            # 3. 写入临时代码文件
            with tempfile.NamedTemporaryFile(
                suffix=".py", 
                mode='w', 
                encoding='utf-8', 
                delete=False
            ) as tmp_code:
                tmp_code.write(wrapper_code)
                code_path = tmp_code.name
            
            try:
                # 4. 使用 subprocess 执行
                result = subprocess.run(
                    [sys.executable, code_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    # 安全：不继承环境变量
                    env={
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'PATH': os.environ.get('PATH', '')
                    }
                )
                
                stdout = result.stdout
                stderr = result.stderr
                
                if result.returncode != 0:
                    self.log(f"  ⚠️ 执行失败: {stderr}")
                    return f"❌ 运行时错误:\n{stderr}\n{stdout}"
                
                if "EXECUTION_SUCCESS" in stdout:
                    self.log("  ✅ 执行成功")
                    return "✅ 运行时测试通过"
                else:
                    return f"⚠️ 代码执行完成但未检测到成功标志\n输出:\n{stdout}\n{stderr}"
            
            except subprocess.TimeoutExpired:
                self.log(f"  ⚠️ 执行超时")
                return f"❌ 代码执行超时（{timeout}秒）"
            
            except Exception as e:
                self.log(f"  ⚠️ 执行异常: {e}")
                return f"❌ 执行异常: {e}"
            
            finally:
                # 清理临时文件
                try:
                    os.remove(data_path)
                    os.remove(code_path)
                except:
                    pass
        
        @tool
        def check_code_syntax(code: str) -> str:
            """
            静态检查代码语法和基本结构
            
            Args:
                code: 要检查的代码
            
            Returns:
                检查结果
            """
            self.log("👀 [工具] 静态检查...")
            
            issues = []
            
            # 基本检查
            if not code or len(code.strip()) < 50:
                issues.append("代码为空或过短")
            
            if "def " not in code:
                issues.append("缺少函数定义")
            
            if "return" not in code:
                issues.append("缺少 return 语句")
            
            # 语法检查
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                issues.append(f"语法错误: {e}")
            
            if not issues:
                self.log("  ✅ 静态检查通过")
                return "✅ 静态检查通过"
            else:
                self.log(f"  ⚠️ 发现 {len(issues)} 个问题")
                return "❌ 发现问题:\n" + "\n".join(f"- {issue}" for issue in issues)
        
        @tool
        def preview_data() -> str:
            """
            预览测试数据的结构
            
            Returns:
                数据预览信息
            """
            self.log("📊 [工具] 预览数据...")
            
            # 直接从 self.test_data 获取数据
            test_data = self.test_data
            if test_data is None or len(test_data) == 0:
                return "❌ 没有可用的测试数据"
            
            try:
                preview = f"""📊 数据预览:
- 行数: {len(test_data)}
- 列数: {len(test_data.columns)}
- 列名: {list(test_data.columns)}

数据类型:
{test_data.dtypes.to_string()}

前5行数据:
{test_data.head().to_string()}
"""
                self.log("  ✅ 数据预览完成")
                return preview
            
            except Exception as e:
                return f"❌ 数据预览失败: {e}"
        
        return [preview_data, check_code_syntax, run_python_code]
    
    def _build_agent(self):
        """构建 ReAct agent"""
        agent = create_react_agent(self.raw_llm, self.tools)  # 使用原始 LLM 实例
        return agent
    
    def _build_context_info(
        self, 
        previous_result: Any, 
        previous_error: Optional[str]
    ) -> str:
        """构建上下文信息"""
        context_info = ""
        
        if previous_result is not None:
            context_info += f"""
📦 **前一步的实际输出：**
类型: {type(previous_result).__name__}
"""
            if isinstance(previous_result, tuple):
                context_info += f"Tuple 长度: {len(previous_result)}\n"
                for i, item in enumerate(previous_result):
                    context_info += f"  [{i}] {type(item).__name__}"
                    if isinstance(item, pd.DataFrame):
                        context_info += f" - 形状: {item.shape}\n"
            elif isinstance(previous_result, dict):
                context_info += f"键: {list(previous_result.keys())}\n"
            elif isinstance(previous_result, pd.DataFrame):
                context_info += f"形状: {previous_result.shape}\n"
                context_info += f"列: {list(previous_result.columns)}\n"
        
        if previous_error:
            context_info += f"""
⚠️ **前一次执行的错误：**
{previous_error}

请特别注意修复这个错误！
"""
        
        return context_info
    
    def _build_initial_prompt(
        self,
        execution_spec: Dict,
        context_info: str,
        test_data: Optional[pd.DataFrame]
    ) -> str:
        """构建初始提示"""
        
        # 序列化测试数据（如果有）
        test_data_json = None
        if test_data is not None and len(test_data) > 0:
            test_data_json = test_data.head(10).to_json(orient='split')
        
        prompt = f"""你是专业的 Python 代码生成专家。

📋 **执行规格：**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}

{context_info}

🎯 **你的任务：**
1. 首先使用 preview_data 工具查看数据结构（了解实际列名）
2. 直接在消息中编写完整的 Python 代码
3. 使用 check_code_syntax 检查代码语法
4. 使用 run_python_code 在真实数据上测试代码
5. 如果测试失败，分析错误并重新编写代码
6. 最多迭代 {self.max_iterations} 次

📝 **代码要求：**
- 完整的 Python 代码（包含所有 import）
- 函数签名: `def {execution_spec.get('function_name', 'analyze')}(df: pd.DataFrame, ...) -> Dict[str, Any]`
- 完整的类型注解和中文注释
- 完整的错误处理（try-except）
- 使用实际的列名（从 preview_data 获取）
- 可以直接保存为 .py 文件运行

⚠️ **重要提示：**
- 必须先预览数据，了解实际列名
- 不要假设列名，使用实际存在的列
- 代码应该健壮，处理各种边界情况

开始吧！"""
        
        return prompt
    
    def _create_wrapper_code(
        self, 
        user_code: str, 
        data_path: str, 
        function_name: str
    ) -> str:
        """创建包装代码，用于在 subprocess 中执行"""
        
        wrapper = f"""
import pandas as pd
import numpy as np
import sys
import traceback

# 加载数据
try:
    df = pd.read_parquet(r'{data_path}')
except Exception as e:
    print(f"系统错误: 数据加载失败 - {{e}}")
    sys.exit(1)

# --- 用户代码开始 ---
{user_code}
# --- 用户代码结束 ---

# 执行函数
try:
    if '{function_name}' in locals():
        func = locals()['{function_name}']
        
        # 智能参数处理
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        if len(params) == 1:
            result = func(df)
        else:
            # 多参数函数，其他参数传 None
            args = [df] + [None] * (len(params) - 1)
            result = func(*args)
        
        # 检查结果
        if isinstance(result, dict) and 'error' in result:
            print(f"函数返回错误: {{result['error']}}")
            sys.exit(1)
        else:
            print("EXECUTION_SUCCESS")
            # 可以打印结果的摘要
            if isinstance(result, dict):
                print(f"结果包含 {{len(result)}} 个键")
    else:
        print(f"错误: 未找到函数 '{function_name}'")
        sys.exit(1)

except Exception as e:
    print(f"运行时错误: {{e}}")
    traceback.print_exc()
    sys.exit(1)
"""
        return wrapper
    
    def _extract_final_result(self, agent_result: Dict) -> Dict[str, Any]:
        """从 agent 结果中提取最终结果"""
        messages = agent_result.get("messages", [])
        
        generated_code = ""
        runtime_error = ""
        code_issues = []
        iteration_count = 0
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # 提取代码
            if "def " in content and "return" in content:
                code = self._extract_code(content)
                if code:
                    generated_code = code
                    iteration_count += 1
            
            # 提取错误信息
            if "运行时错误" in content or "❌" in content:
                runtime_error = content
            elif "发现问题" in content:
                code_issues.append(content)
        
        is_code_valid = (
            generated_code and
            not runtime_error and
            not code_issues
        )
        
        return {
            'generated_code': generated_code,
            'iteration_count': iteration_count,
            'is_code_valid': is_code_valid,
            'code_issues': code_issues,
            'runtime_error': runtime_error
        }
    
    def _extract_code(self, response: str) -> str:
        """从响应中提取代码"""
        code = response.strip()
        
        # 查找代码块
        if "```" in code:
            lines = code.split("\n")
            code_lines = []
            in_code = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    if not in_code:
                        in_code = True
                    else:
                        break
                    continue
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                code = "\n".join(code_lines)
        
        # 查找第一个 import 或 def
        if not code.startswith(("import ", "from ", "def ")):
            lines = code.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith(("import ", "from ", "def ")):
                    code = "\n".join(lines[i:])
                    break
        
        return code.strip()
