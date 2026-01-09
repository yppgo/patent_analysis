"""
Coding Agent V4.1 - 基于豆包反馈的智能优化版本

新增改进：
1. 🔧 增强的 LLM 响应解析（支持多格式代码提取）
2. 🚨 智能错误恢复与分级重试策略
3. 📊 错误类型识别与针对性修复提示
4. 🔄 迭代终止条件优化（避免无效重试）
"""

import json
import sys
import tempfile
import subprocess
import os
import re
import pandas as pd
from io import StringIO
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent


# 错误类型映射与修复提示
ERROR_FIX_PROMPTS = {
    "SyntaxError": "检测到语法错误，请修正代码语法，确保所有括号/引号闭合，缩进正确",
    "KeyError": "检测到键不存在错误，请检查DataFrame列名是否正确映射，实际列名：{actual_columns}",
    "TypeError": "检测到类型错误，请检查函数参数类型和返回值类型，确保与执行规格匹配",
    "AttributeError": "检测到属性错误，请检查对象是否有该属性/方法",
    "ValueError": "检测到值错误，请检查输入数据的值是否合法（如空数据、负数等）",
    "ImportError": "检测到导入错误，请检查库是否已安装或导入语句是否正确",
    "ModuleNotFoundError": "检测到模块未找到，请确认依赖库已安装",
    "RuntimeError": "检测到运行时错误，请检查算法参数是否合理，数据是否为空",
    "IndexError": "检测到索引错误，请检查数组/列表索引是否越界",
    "ZeroDivisionError": "检测到除零错误，请添加分母为零的检查"
}


class CodingAgentV4_1(BaseAgent):
    """
    编码智能体 V4.1 - 智能优化版本
    
    核心特性：
    1. 增强的代码提取（支持多格式）
    2. 智能错误恢复（分级重试）
    3. 错误类型识别（针对性修复）
    4. 优化的迭代策略（避免无效重试）
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=5, logger=None, use_subprocess=False):
        super().__init__("CodingAgentV4.1", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        self.use_subprocess = use_subprocess  # 是否使用 subprocess（默认不使用）
        
        # 获取原始 LLM 实例
        self.raw_llm = llm_client.get_llm() if hasattr(llm_client, 'get_llm') else llm_client
        
        # 错误历史（用于检测重复错误）
        self.error_history = []
        
        # 创建工具和 agent
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行规格，生成高质量代码"""
        execution_spec = input_data.get('execution_spec', {})
        test_data = input_data.get('test_data', self.test_data)
        previous_result = input_data.get('previous_result')
        previous_error = input_data.get('previous_error')
        current_step = input_data.get('current_step', {})  # 获取原始步骤信息
        
        # 更新 test_data（如果传入了新数据）
        if test_data is not None:
            self.test_data = test_data
        
        func_name = execution_spec.get('function_name', 'N/A')
        self.log(f"🚀 开始生成代码: {func_name}")
        
        # 重置错误历史
        self.error_history = []
        
        # 构建上下文信息
        context_info = self._build_context_info(previous_result, previous_error)
        
        # 获取实际列名（用于错误提示）
        actual_columns = list(test_data.columns) if test_data is not None else []
        
        # 构建初始提示（传入原始步骤信息以获取文件路径）
        initial_message = self._build_initial_prompt(
            execution_spec, 
            context_info,
            test_data,
            actual_columns,
            current_step  # 传入原始步骤
        )
        
        # 调用 agent（设置合理的递归限制）
        result = self.agent.invoke({
            "messages": [("user", initial_message)],
            "configurable": {
                "execution_spec": execution_spec,
                "test_data": test_data,
                "max_iterations": self.max_iterations,
                "actual_columns": actual_columns
            }
        }, config={"recursion_limit": 15})  # 合理的递归限制：最多15次工具调用
        
        # 检查是否有成功消息（提前停止的标志）
        messages = result.get("messages", [])
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if "✅ 运行时测试通过" in content and "任务完成" in content:
                self.log("  [检测] 发现成功标志，提前结束")
                break
        
        # 提取最终结果
        final_result = self._extract_final_result(result)
        
        self.log(f"✅ 代码生成完成")
        
        return final_result
    
    def _create_tools(self) -> List:
        """创建工具列表"""
        
        @tool
        def run_python_code(
            code: str,
            function_name: str = "analyze",
            timeout: int = 30
        ) -> str:
            """
            在隔离的 subprocess 中安全执行 Python 代码
            
            Args:
                code: 要执行的 Python 代码
                function_name: 要调用的函数名
                timeout: 超时时间（秒）
            
            Returns:
                执行结果或错误信息
                
            重要：如果返回 "✅ 运行时测试通过"，说明代码已经成功，
            你应该立即停止，不要再调用任何工具！
            """
            self.log("🧪 [工具] 安全执行代码...")
            
            # 直接从 self.test_data 获取数据
            test_data = self.test_data
            if test_data is None or len(test_data) == 0:
                return "⚠️ 没有测试数据，跳过执行"
            
            # 根据配置选择执行方式
            if self.use_subprocess:
                return self._run_in_subprocess(code, test_data, function_name, timeout)
            else:
                return self._run_in_process(code, test_data, function_name)
            
            # 1. 创建临时数据文件
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".parquet", 
                    delete=False, 
                    mode='wb'
                ) as tmp_data:
                    test_data.to_parquet(tmp_data.name)
                    data_path = tmp_data.name
            except Exception as e:
                self.log(f"  [ERROR] 数据准备失败: {e}")
                return f"❌ 数据准备失败: {e}"
            
            # 2. 包装用户代码
            wrapper_code = self._create_wrapper_code(code, data_path, function_name)
            
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
                    env={
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'PATH': os.environ.get('PATH', '')
                    }
                )
                
                stdout = result.stdout
                stderr = result.stderr
                
                if result.returncode != 0:
                    # 提取错误类型和详细信息
                    error_type, error_detail = self._parse_error(stderr)
                    
                    # 记录错误历史
                    self.error_history.append({
                        'type': error_type,
                        'detail': error_detail,
                        'full_error': stderr
                    })
                    
                    # 检查是否为重复错误
                    if self._is_repeated_error(error_type):
                        self.log(f"  ⚠️ 检测到重复错误: {error_type}")
                        return f"❌ 重复错误（{error_type}），建议检查根本原因:\n{stderr}"
                    
                    self.log(f"  ⚠️ 执行失败: {error_type}")
                    return f"❌ {error_type}:\n{stderr}\n{stdout}"
                
                if "EXECUTION_SUCCESS" in stdout:
                    self.log("  ✅ 执行成功")
                    return "✅ 运行时测试通过！代码已经成功执行，任务完成！请立即停止，不要再调用任何工具。"
                else:
                    return f"⚠️ 代码执行完成但未检测到成功标志\n输出:\n{stdout}\n{stderr}"
            
            except subprocess.TimeoutExpired:
                self.log(f"  ⚠️ 执行超时")
                return f"❌ 代码执行超时（{timeout}秒）- 可能存在死循环或计算量过大"
            
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
    
    def _run_in_process(self, code: str, test_data: pd.DataFrame, function_name: str) -> str:
        """在当前进程中执行代码（简单快速，但不安全）"""
        try:
            # 准备执行环境
            exec_globals = {
                'pd': pd,
                'np': __import__('numpy'),
                'df': test_data,  # 提供测试数据作为全局变量
                'Dict': Dict,
                'List': List,
                'Any': Any,
                'Tuple': Tuple,
                'Optional': Optional,
                'joblib': __import__('joblib'),
                'Path': Path,
                '__builtins__': __builtins__
            }
            
            # 直接执行代码（不再调用函数）
            exec(code, exec_globals)
            
            self.log("  ✅ 执行成功")
            return "✅ 运行时测试通过！代码已经成功执行，任务完成！请立即停止，不要再调用任何工具。"
        
        except KeyError as e:
            error_msg = f"KeyError: {e} - 可能是列名不匹配"
            self.log(f"  [WARNING] {error_msg}")
            
            # 记录错误历史
            self.error_history.append({
                'type': 'KeyError',
                'detail': str(e),
                'full_error': error_msg
            })
            
            # 获取实际列名
            actual_cols = list(test_data.columns) if test_data is not None else []
            fix_prompt = f"检查DataFrame列名是否正确映射，实际列名：{actual_cols}"
            
            # 检测重复错误（检查最近3次错误）
            recent_errors = [err['detail'] for err in self.error_history[-3:]]
            if len(recent_errors) >= 2:
                # 如果最近2次错误相同，立即停止
                if recent_errors[-1] == recent_errors[-2]:
                    return f"❌ 检测到连续重复的 KeyError，已尝试 {len(self.error_history)} 次。\n实际列名: {actual_cols}\n\n🛑 停止重试。请使用正确的列名彻底重新编写代码。"
            
            return f"❌ {error_msg}\n\n💡 修复建议: {fix_prompt}\n\n请修复代码并重新测试。"
        
        except Exception as e:
            error_msg = str(e)
            error_type_name = type(e).__name__
            self.log(f"  [WARNING] 运行时错误: {error_msg}")
            
            # 解析错误类型
            error_type, detail = self._parse_error(error_type_name + ": " + error_msg)
            
            # 记录错误历史
            self.error_history.append({
                'type': error_type,
                'detail': detail,
                'full_error': error_msg
            })
            
            # 获取修复提示
            fix_prompt = ERROR_FIX_PROMPTS.get(error_type_name, "请检查代码逻辑")
            if error_type_name == "KeyError":
                fix_prompt = fix_prompt.format(actual_columns=list(test_data.columns))
            
            # 检测重复错误（检查最近3次错误）
            recent_errors = [err['detail'] for err in self.error_history[-3:]]
            if len(recent_errors) >= 2:
                # 如果最近2次错误相同，立即停止
                if recent_errors[-1] == recent_errors[-2]:
                    return f"❌ 检测到连续重复错误，已尝试 {len(self.error_history)} 次。\n错误: {error_msg}\n\n🛑 停止重试。请检查代码逻辑，确保：\n1. 文件路径正确\n2. 列名正确\n3. 数据类型匹配"
            
            return f"❌ 运行时错误 ({error_type_name}): {error_msg}\n\n💡 修复建议: {fix_prompt}\n\n请修复代码并重新测试。"
    
    def _run_in_subprocess(self, code: str, test_data: pd.DataFrame, function_name: str, timeout: int) -> str:
        """在 subprocess 中执行代码（安全但较慢）"""
    
    def _build_agent(self):
        """构建 ReAct agent"""
        agent = create_react_agent(self.raw_llm, self.tools)
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
        test_data: Optional[pd.DataFrame],
        actual_columns: List[str],
        current_step: Dict = None
    ) -> str:
        """构建初始提示"""
        
        # 序列化测试数据
        test_data_json = None
        if test_data is not None and len(test_data) > 0:
            test_data_json = test_data.head(10).to_json(orient='split')
        
        # 从原始步骤中提取输出文件路径
        output_files_info = ""
        input_data_info = ""
        
        if current_step and 'implementation_config' in current_step:
            config = current_step['implementation_config']
            
            # 输出文件信息
            if 'output_files' in config:
                output_files = config['output_files']
                output_files_info = f"""
**⚠️ 重要：必须使用以下文件路径保存结果**
- 结果CSV: `{output_files.get('results_csv', 'outputs/results.csv')}`
- 结果列名: {output_files.get('results_columns', [])}
- 列数据类型: {output_files.get('column_types', {})}
- 模型PKL: `{output_files.get('model_pkl', 'outputs/model.pkl') if output_files.get('model_pkl') else '无需保存模型'}`
- 模型对象: {output_files.get('model_objects', [])}

"""
                # 添加格式说明
                if 'format_notes' in output_files:
                    output_files_info += f"**📋 数据格式要求：**\n{output_files['format_notes']}\n\n"
                
                output_files_info += "**代码中必须使用这些精确的路径和列名！**\n"
            
            # 输入数据信息
            if 'input_data_source' in config:
                input_source = config['input_data_source']
                input_data_info = f"""
**📥 输入数据源（必须严格遵循）：**
- 主数据文件: `{input_source.get('main_data', '')}`
- 需要的主数据列: {input_source.get('main_data_columns', [])}

"""
                # 依赖的前置步骤
                dependencies = input_source.get('dependencies', [])
                if dependencies:
                    input_data_info += "**依赖的前置步骤结果：**\n"
                    for dep in dependencies:
                        input_data_info += f"- 文件: `{dep.get('file', '')}`\n"
                        input_data_info += f"  需要的列: {dep.get('columns', [])}\n"
                        input_data_info += f"  说明: {dep.get('description', '')}\n"
                    input_data_info += "\n**⚠️ 代码必须加载这些依赖文件并使用指定的列！**\n"
        
        prompt = f"""你是专业的 Python 代码生成专家。

📋 **执行规格：**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}

{context_info}
{input_data_info}
{output_files_info}

🎯 **你的任务：**
1. 首先使用 preview_data 工具查看数据结构（了解实际列名）
2. 编写完整的分析代码（独立脚本，不是函数）
3. 使用 check_code_syntax 检查代码语法
4. 使用 run_python_code 在真实数据上测试代码
5. **如果看到 "✅ 运行时测试通过"**：
   - 🎉 任务完成！立即停止，不要再调用任何工具
   - 代码已经成功，无需继续改进
6. **如果测试失败**：
   - 仔细阅读错误信息
   - 修复代码
   - 重新测试
   - 最多重试 {self.max_iterations} 次

⚠️ **关键**：一旦看到 "✅ 运行时测试通过"，立即停止！不要继续优化代码！

📝 **代码要求（完全独立的脚本）：**
生成的代码必须是**完全独立可运行的 Python 脚本**，不定义函数。

**⚠️ 关键要求：代码必须自己加载数据，不能依赖外部传入的变量！**

**代码结构：**
```python
import pandas as pd
import joblib
from pathlib import Path

# 确保输出目录存在
Path('outputs').mkdir(exist_ok=True)

print("开始执行分析...")

# 1. 加载主数据（必须包含，不能注释掉！）
df = pd.read_excel('data/clean_patents1_with_topics_filled.xlsx', sheet_name='clear')

# 2. 如果需要前一步的结果，从文件加载并合并
# ⚠️ 重要：根据需求决定是否需要合并
# 
# 情况1：只需要前一步的结果（不需要原始数据）
# prev_results = pd.read_csv('outputs/step_1_topic_results.csv')
# df = prev_results  # 直接使用前一步的结果
# 
# 情况2：需要同时使用原始数据和前一步的结果
# prev_results = pd.read_csv('outputs/step_1_topic_results.csv')
# # 按行索引合并（因为行顺序一致）
# df = pd.concat([df, prev_results], axis=1)
# # 现在 df 包含原始列 + 新列
# 
# 情况2：需要同时使用原始数据和前一步的结果
# prev_results = pd.read_csv('outputs/step_1_topic_results.csv')
# # 按行索引合并（因为行顺序一致）
# df = pd.concat([df, prev_results], axis=1)
# # 现在 df 包含原始列 + 新列

# 3. 执行分析
# 使用实际列名: {actual_columns}
# ... 你的分析代码 ...

# 4. 保存结果到文件（使用指定的路径）
results_df = pd.DataFrame({{
    'new_column_1': new_column_1,
    'new_column_2': new_column_2
}})
results_df.to_csv('指定的路径', index=False)
print("新列已保存")

# 5. 保存模型（如果有）
if 'trained_model' in locals():
    joblib.dump(trained_model, '指定的路径')
    print("模型已保存")

print("✅ 分析完成")
```

⚠️ **关键要求：**
- **不要定义函数**，直接写执行代码
- 使用全局变量 `df`（测试时会提供）
- 保存结果到指定的文件路径
- 不要返回任何值
- 使用实际列名: {actual_columns}
- 添加 print 语句显示进度

⚠️ **关键要求：**
⚠️ **重要提示：**
- 必须先预览数据，了解实际列名
- 实际列名: {actual_columns}
- 不要假设列名，使用实际存在的列
- 代码应该健壮，处理各种边界情况
- 如果遇到错误，仔细阅读错误信息并针对性修复
- **使用前一步结果时**：
  * 如果只需要前一步的结果，直接加载 CSV 即可，不需要合并
  * 如果需要同时使用原始数据和前一步结果，用 `pd.concat([df, prev_results], axis=1)` 合并
  * 前一步的 CSV 只包含新生成的列，没有元数据列

开始吧！"""
        
        return prompt
    
    def _create_wrapper_code(
        self, 
        user_code: str, 
        data_path: str, 
        function_name: str
    ) -> str:
        """创建包装代码"""
        
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
            args = [df] + [None] * (len(params) - 1)
            result = func(*args)
        
        if isinstance(result, dict) and 'error' in result:
            print(f"函数返回错误: {{result['error']}}")
            sys.exit(1)
        else:
            print("EXECUTION_SUCCESS")
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
            
            # 提取代码（使用增强的提取逻辑）
            # V4.1: 不再要求 def 和 return，因为生成的是独立脚本
            if "import " in content or "from " in content:
                code = self._extract_code_enhanced(content)
                if code:
                    generated_code = code
                    iteration_count += 1
                    self.log(f"  [提取] 第 {iteration_count} 次提取到代码，长度: {len(code)}")
            
            # 提取错误信息
            if "运行时错误" in content or "❌" in content:
                runtime_error = content
            elif "发现问题" in content:
                code_issues.append(content)
        
        if not generated_code:
            self.log("  [WARNING] 未能从消息中提取到任何代码！", "warning")
        
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
            'runtime_error': runtime_error,
            'error_history': self.error_history
        }
    
    def _extract_code_enhanced(self, content: str) -> Optional[str]:
        """
        增强的代码提取逻辑，支持多格式解析
        
        Args:
            content: LLM 响应内容
        
        Returns:
            提取的代码或 None
        """
        # 1. 处理 markdown 代码块
        code_patterns = [
            r"```python\n(.*?)\n```",  # 带python标记的代码块
            r"```\n(.*?)\n```",        # 无标记的代码块
            r"```py\n(.*?)\n```"       # py缩写标记
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                code = match.group(1).strip()
                self.log("  [OK] 从 markdown 代码块提取代码")
                return code
        
        # 2. 处理纯文本代码（无代码块）
        lines = content.split("\n")
        code_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # 开始代码块的标志
            if stripped.startswith(("import ", "from ", "def ", "class ")):
                in_code = True
            
            # 跳过解释性文字
            if in_code and not stripped.startswith(("#", "**", "//", "---", "注意", "说明")):
                code_lines.append(line)
        
        if code_lines:
            code = "\n".join(code_lines).strip()
            self.log("  [OK] 从纯文本提取代码")
            return code
        
        # 3. 最后尝试：查找第一个 import 或 def 到最后
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ", "def ")):
                code = "\n".join(lines[i:]).strip()
                self.log("  [OK] 从第一个 import/def 提取代码")
                return code
        
        self.log("  [WARNING] 未提取到有效代码", "warning")
        return None
    
    def _parse_error(self, error_msg: str) -> Tuple[str, str]:
        """
        解析错误信息，提取错误类型和详细信息
        
        Args:
            error_msg: 错误消息
        
        Returns:
            (错误类型, 错误详情)
        """
        # 常见错误类型
        for error_type in ERROR_FIX_PROMPTS.keys():
            if error_type in error_msg:
                # 提取详细信息（通常在最后一行）
                lines = error_msg.strip().split("\n")
                detail = lines[-1] if lines else error_msg
                return error_type, detail
        
        return "UnknownError", error_msg[:200]
    
    def _is_repeated_error(self, error_type: str, threshold: int = 2) -> bool:
        """
        检查是否为重复错误
        
        Args:
            error_type: 错误类型
            threshold: 重复次数阈值
        
        Returns:
            是否为重复错误
        """
        count = sum(1 for err in self.error_history if err['type'] == error_type)
        return count >= threshold
    
    def _get_error_fix_prompt(
        self, 
        error_type: str, 
        actual_columns: List[str] = None
    ) -> str:
        """
        根据错误类型获取修复提示
        
        Args:
            error_type: 错误类型
            actual_columns: 实际列名列表
        
        Returns:
            修复提示
        """
        prompt = ERROR_FIX_PROMPTS.get(error_type)
        if prompt:
            return prompt.format(actual_columns=actual_columns or [])
        return f"检测到未知错误：{error_type}，请修复后重新生成代码"
