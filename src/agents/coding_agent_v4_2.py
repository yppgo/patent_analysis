"""
Coding Agent V4.2 - 融合终端和文件操作能力

新增特性：
1. [Python REPL] - 有状态的代码执行环境
2. [Shell命令] - 终端操作能力（ls, mkdir, pip install 等）
3. [文件操作] - 读写文件、检查文件存在性
4. [V4.1功能] - 保留 V4.1 的所有核心功能（错误检测、文件路径注入等）
"""

import json
import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent
from src.tools.repl import PythonREPL
from src.tools.os_tools import OSTools


# 错误类型映射与修复提示
ERROR_FIX_PROMPTS = {
    "SyntaxError": "检测到语法错误，请修正代码语法，确保所有括号/引号闭合，缩进正确",
    "KeyError": "检测到键不存在错误，请检查DataFrame列名是否正确映射，实际列名：{actual_columns}",
    "TypeError": "检测到类型错误，请检查函数参数类型和返回值类型",
    "AttributeError": "检测到属性错误，请检查对象是否有该属性/方法",
    "ValueError": "检测到值错误，请检查输入数据的值是否合法",
    "ImportError": "检测到导入错误，请检查库是否已安装或导入语句是否正确",
    "ModuleNotFoundError": "检测到模块未找到，请使用 execute_shell 工具安装：pip install <package>",
    "FileNotFoundError": "检测到文件未找到，请使用 execute_shell 检查文件路径",
}


class CodingAgentV4_2(BaseAgent):
    """
    Coding Agent V4.2 - 终端增强版
    
    核心能力：
    1. Python REPL（有状态执行）
    2. Shell 命令（文件系统操作）
    3. 智能错误恢复（V4.1 继承）
    4. 文件路径注入（V4.1 继承）
    """
    
    def __init__(self, llm_client, test_data=None, max_iterations=15, logger=None):
        super().__init__("CodingAgentV4.2", llm_client, logger)
        self.test_data = test_data
        self.max_iterations = max_iterations
        
        # 核心组件
        self.repl = PythonREPL()  # 有状态的 Python 环境
        self.raw_llm = llm_client.get_llm() if hasattr(llm_client, 'get_llm') else llm_client
        
        # 错误历史（用于检测重复错误）
        self.error_history = []
        
        # 创建工具和 agent
        self.tools = self._create_tools()
        self.agent = self._build_agent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行规格，生成并执行代码"""
        execution_spec = input_data.get('execution_spec', {})
        test_data = input_data.get('test_data', self.test_data)
        previous_result = input_data.get('previous_result')
        previous_error = input_data.get('previous_error')
        current_step = input_data.get('current_step', {})
        
        # 更新 test_data
        if test_data is not None:
            self.test_data = test_data
        
        func_name = execution_spec.get('function_name', 'N/A')
        self.log(f"🚀 [开始] 生成代码: {func_name}")
        
        # 重置错误历史和 REPL 环境
        self.error_history = []
        self.repl.reset()  # 每次任务开始时重置环境
        
        # 构建上下文信息
        context_info = self._build_context_info(previous_result, previous_error)
        
        # 获取实际列名
        actual_columns = list(test_data.columns) if test_data is not None else []
        
        # 构建初始提示
        initial_message = self._build_initial_prompt(
            execution_spec, 
            context_info,
            test_data,
            actual_columns,
            current_step
        )
        
        # 调用 agent
        # 设置更高的递归限制以避免过早终止
        recursion_limit = max(50, self.max_iterations + 20)
        result = self.agent.invoke({
            "messages": [("user", initial_message)],
            "configurable": {
                "execution_spec": execution_spec,
                "test_data": test_data,
                "max_iterations": self.max_iterations,
                "actual_columns": actual_columns
            }
        }, config={"recursion_limit": recursion_limit})
        
        # 提取最终结果
        final_result = self._extract_final_result(result)
        
        self.log(f"✅ [完成] 代码生成完成")
        
        return final_result
    
    def _create_tools(self) -> List:
        """创建工具列表"""
        
        @tool
        def run_python(code: str) -> str:
            """
            在有状态的 Python REPL 中执行代码。
            变量会在多次调用间保持。
            
            ⚠️ 重要：必须使用 print() 才能看到输出！
            
            Args:
                code: Python 代码
            
            Returns:
                执行结果或错误信息
            """
            self.log("=" * 60)
            self.log("🐍 [Python REPL] 执行代码")
            self.log("=" * 60)
            
            # 打印代码内容
            code_preview = code[:300] + "\n..." if len(code) > 300 else code
            self.log(f"代码:\n{code_preview}")
            self.log("-" * 60)
            
            try:
                output = self.repl.run(code)
                
                # 打印执行结果
                output_preview = output[:500] + "\n..." if len(output) > 500 else output
                self.log(f"输出:\n{output_preview}")
                self.log("=" * 60)
                
                # 检查是否有错误
                if "Error" in output or "Traceback" in output:
                    # 解析错误类型
                    error_type, detail = self._parse_error(output)
                    
                    # 记录错误历史
                    self.error_history.append({
                        'type': error_type,
                        'detail': detail,
                        'full_error': output
                    })
                    
                    # 检测重复错误
                    if self._is_repeated_error(error_type):
                        self.log(f"  ⚠️ 检测到重复错误: {error_type}")
                        return f"❌ 重复错误（{error_type}），已尝试 {len(self.error_history)} 次。\n\n{output}\n\n🛑 请彻底重新思考解决方案。"
                    
                    # 获取修复提示
                    fix_prompt = ERROR_FIX_PROMPTS.get(error_type, "请检查代码逻辑")
                    if error_type == "KeyError" and self.test_data is not None:
                        fix_prompt = fix_prompt.format(actual_columns=list(self.test_data.columns))
                    
                    self.log(f"  ⚠️ 执行失败: {error_type}")
                    return f"❌ {error_type}:\n{output}\n\n💡 修复建议: {fix_prompt}"
                
                self.log("  ✅ 执行成功")
                # 返回输出，如果没有输出则返回成功标记
                return output if output.strip() else "✅ 代码已执行 (无输出，请使用 print 查看结果)"
            
            except Exception as e:
                self.log(f"  ⚠️ 执行异常: {e}")
                return f"❌ 执行异常: {e}"

        
        @tool
        def execute_shell(command: str) -> str:
            """
            执行 Shell 命令（如 ls, mkdir, pip install, cat 等）。
            
            常用命令：
            - ls / dir: 列出文件
            - mkdir: 创建目录
            - pip install: 安装包
            - cat / type: 查看文件内容
            - pwd / cd: 查看/切换目录
            
            Args:
                command: Shell 命令
            
            Returns:
                命令输出
            """
            self.log("=" * 60)
            self.log(f"💻 [Shell] 执行命令")
            self.log("=" * 60)
            self.log(f"命令: {command}")
            self.log("-" * 60)
            
            output = OSTools.execute_bash(command)
            
            # 打印完整输出（限制长度）
            output_preview = output[:500] + "\n..." if len(output) > 500 else output
            self.log(f"输出:\n{output_preview}")
            self.log("=" * 60)
            
            return output
        
        @tool
        def read_file(filepath: str, lines: int = None) -> str:
            """
            读取文件内容。
            
            Args:
                filepath: 文件路径
                lines: 读取的行数（可选，默认全部）
            
            Returns:
                文件内容
            """
            self.log("=" * 60)
            self.log(f"📖 [文件读取] {filepath}")
            self.log("=" * 60)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if lines:
                        content = ''.join(f.readlines()[:lines])
                    else:
                        content = f.read()
                
                content_preview = content[:300] + "\n..." if len(content) > 300 else content
                self.log(f"内容 (前300字符):\n{content_preview}")
                self.log(f"✅ [OK] 读取成功，总长度: {len(content)} 字符")
                self.log("=" * 60)
                return content
            
            except FileNotFoundError:
                self.log(f"❌ [ERROR] 文件不存在: {filepath}")
                self.log("=" * 60)
                return f"❌ [ERROR] 文件不存在: {filepath}"
            except Exception as e:
                self.log(f"❌ [ERROR] 读取失败: {e}")
                self.log("=" * 60)
                return f"❌ [ERROR] 读取失败: {e}"
        
        @tool
        def write_file(filepath: str, content: str) -> str:
            """
            写入文件内容。
            
            Args:
                filepath: 文件路径
                content: 要写入的内容
            
            Returns:
                操作结果
            """
            self.log("=" * 60)
            self.log(f"✍️ [文件写入] {filepath}")
            self.log("=" * 60)
            
            try:
                # 确保目录存在
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.log(f"✅ [OK] 写入成功，长度: {len(content)} 字符")
                self.log("=" * 60)
                return f"✅ [OK] 文件已保存: {filepath}"
            
            except Exception as e:
                self.log(f"❌ [ERROR] 写入失败: {e}")
                self.log("=" * 60)
                return f"❌ [ERROR] 写入失败: {e}"
        
        @tool
        def check_file_exists(filepath: str) -> str:
            """
            检查文件或目录是否存在。
            
            Args:
                filepath: 文件路径
            
            Returns:
                存在性检查结果
            """
            path = Path(filepath)
            
            if path.exists():
                if path.is_file():
                    size = path.stat().st_size
                    return f"✅ 文件存在: {filepath} (大小: {size} 字节)"
                elif path.is_dir():
                    files = list(path.iterdir())
                    return f"✅ 目录存在: {filepath} (包含 {len(files)} 个项目)"
            else:
                return f"❌ 不存在: {filepath}"
        
        return [
            run_python,
            execute_shell,
            read_file,
            write_file,
            check_file_exists
        ]
    
    def _build_agent(self):
        """构建 ReAct agent"""
        return create_react_agent(self.raw_llm, self.tools)
    
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
            if isinstance(previous_result, pd.DataFrame):
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
        
        # 从原始步骤中提取输出文件路径
        output_files_info = ""
        input_data_info = ""
        
        if current_step and 'implementation_config' in current_step:
            config = current_step['implementation_config']
            
            # 输出文件信息
            if 'output_files' in config:
                output_files = config['output_files']
                results_columns = output_files.get('results_columns', [])
                
                # 检查是否有多列需要展开（如 keyword_0, keyword_1...）
                needs_expansion = len(results_columns) > 1 and any('_' in col for col in results_columns)
                
                output_files_info = f"""
**⚠️ 重要：必须使用以下文件路径保存结果**
- 结果CSV: `{output_files.get('results_csv', 'outputs/results.csv')}`
- 结果列名: {results_columns}
- 列数据类型: {output_files.get('column_types', {})}
- 模型PKL: `{output_files.get('model_pkl', 'outputs/model.pkl') if output_files.get('model_pkl') else '无需保存模型'}`

"""
                if needs_expansion:
                    # 构建示例代码，避免 f-string 转义问题
                    example_columns = str(results_columns)
                    output_files_info += f"""
**🔥 特别注意：结果需要展开成 {len(results_columns)} 列！**

如果你的分析生成了列表数据（如每个文档的多个关键词），必须展开成多列：

❌ 错误做法（单列包含列表字符串）：
```python
results_df = pd.DataFrame({{'keywords': [['词1', '词2'], ['词3', '词4']]}}
# 保存后：keywords 列包含 "['词1', '词2']" 这样的字符串
```

✅ 正确做法（展开成多列）：
```python
# 假设 keywords_list = [['词1', '词2', '词3'], ['词4', '词5', '词6'], ...]
results_dict = {{}}
for i, col_name in enumerate({example_columns}):
    results_dict[col_name] = [doc[i] if len(doc) > i else '' for doc in keywords_list]
results_df = pd.DataFrame(results_dict)
# 保存后：keyword_0, keyword_1, keyword_2 三列，每列一个关键词
```

"""
                
                if 'format_notes' in output_files:
                    output_files_info += f"**📋 数据格式要求：**\n{output_files['format_notes']}\n\n"
                
                # 构建列名字符串，避免 f-string 转义问题
                columns_str = str(results_columns)
                output_files_info += f"""
**🚨 关键要求：只保存必要的列！**

保存结果时，必须只包含以下列：
1. ID 列：`序号`, `公开(公告)号`（用于后续合并）
2. 新生成的列：{columns_str}

❌ 不要保存原始数据列（如标题、摘要等长文本）
❌ 不要保存整个 DataFrame
❌ 不要保存 Python 对象（如 Timestamp、列表）

✅ 正确的数据类型：
- 数值：int, float
- 文本：str
- 日期：转换为字符串格式（如 '2023-01-01'）

✅ 正确示例：
```python
# 只选择 ID 列和新生成的列
results_df = df[['序号', '公开(公告)号'] + {columns_str}]
results_df.to_csv('指定路径', index=False)
```

**代码中必须使用这些精确的路径和列名！**
"""
            
            # 输入数据信息
            if 'input_data_source' in config:
                input_source = config['input_data_source']
                input_data_info = f"""
**📥 输入数据源（必须严格遵循）：**
- 主数据文件: `{input_source.get('main_data', '')}`
- 需要的主数据列: {input_source.get('main_data_columns', [])}

"""
                dependencies = input_source.get('dependencies', [])
                if dependencies:
                    input_data_info += """**依赖的前置步骤结果：**
前置步骤的结果文件只包含 ID 列和新生成的列，需要通过 ID 与主数据合并！

"""
                    for dep in dependencies:
                        input_data_info += f"- 文件: `{dep.get('file', '')}`\n"
                        input_data_info += f"  需要的列: {dep.get('columns', [])}\n"
                        input_data_info += f"  说明: {dep.get('description', '')}\n"
                    
                    input_data_info += """
**⚠️ 正确的加载方式：**
```python
# 1. 加载主数据（包含所有原始列）
df = pd.read_excel('主数据文件路径', sheet_name='clear')

# 2. 加载依赖文件（只包含 ID + 新列）
dep_df = pd.read_csv('依赖文件路径')
# dep_df 结构：序号, 公开(公告)号, 新生成的列...

# 3. 通过 ID 合并（保留主数据的所有列）
df = pd.merge(df, dep_df, on=['序号', '公开(公告)号'], how='left')
# 现在 df 包含：原始数据 + 依赖步骤的结果列
```

这样可以同时访问原始数据和前置步骤的结果！
"""
        
        # 获取系统信息
        import getpass
        import platform
        
        system_info = f"""
**执行环境：**
- 操作系统: {platform.system()} {platform.release()}
- Python版本: {platform.python_version()}
- 工作目录: {Path.cwd()}
"""
        
        prompt = f"""你是世界级的 Python 数据分析专家，能够通过执行代码完成任何数据分析任务。

**你的能力：**
- ✅ 你有完整的权限执行任何必要的代码
- ✅ 你可以安装新的Python包
- ✅ 你可以访问文件系统和执行Shell命令
- ✅ 你能够完成任何数据分析任务

**核心原则（来自世界顶级编程实践）：**
1. **小步快跑**：永远不要试图在一个代码块中完成所有事情
2. **打印验证**：每一步都要打印信息，确认结果
3. **持续迭代**：第一次很少成功，从小步骤中学习并继续
4. **失败重试**：如果失败了，分析错误，调整策略，再试一次

{system_info}

🚨 **最重要的要求（必须严格遵守）：**

1. **保存结果时只包含必要的列**
   - 必须包含：ID 列（`序号`, `公开(公告)号`）+ 新生成的列
   - 禁止包含：原始数据列（标题、摘要等）、前置步骤的列
   
2. **多值数据必须展开成多列**
   - 如果生成了列表数据（如关键词列表），必须展开成独立的列
   - 禁止保存为单列的列表字符串

📋 **执行规格：**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}

{context_info}
{input_data_info}
{output_files_info}

🛠️ **你的工具箱：**
1. `run_python(code)` - 执行 Python 代码（有状态，变量会保持）
   - 查看数据：run_python("print(df.head())")
   - 查看列名：run_python("print(df.columns)")
   - 查看数据类型：run_python("print(df.dtypes)")
2. `execute_shell(command)` - 执行终端命令（ls, mkdir, pip install 等）
3. `read_file(filepath)` - 读取文件内容
4. `write_file(filepath, content)` - 写入文件
5. `check_file_exists(filepath)` - 检查文件是否存在

🎯 **你的任务流程：**

**第1步：环境准备**
- 使用 `execute_shell` 检查输出目录是否存在
- 如果不存在，使用 `execute_shell('mkdir outputs')` 创建
- 使用 `check_file_exists` 检查依赖文件是否存在

**第2步：数据探索**
- 使用 `run_python("print(df.head())")` 查看数据
- 使用 `run_python("print(df.columns)")` 查看列名
- 了解实际列名：{actual_columns}

**第3步：编写和测试代码**
- 使用 `run_python` 逐步编写代码
- 先加载数据，打印确认
- 再执行分析，打印中间结果
- 最后保存结果到指定路径

**第4步：验证结果**
- 使用 `check_file_exists` 确认文件已保存
- 使用 `read_file` 查看前几行，确认格式正确
- **验证列数**：确保只有 ID 列 + 新生成的列

⚠️ **关键要求（基于Open Interpreter最佳实践）：**

1. **小步执行，持续验证**
   - 🚫 不要试图一次性完成所有代码
   - ✅ 写一小段，执行，打印结果，观察，再继续
   - ✅ 每个代码块应该只做一件事
   - 💡 你永远不会第一次就成功，这是正常的！

2. **必须打印中间结果**
   - 每次 `run_python` 都要用 print() 查看结果
   - 打印数据形状、列名、前几行、统计信息
   - 这样你才能知道下一步该做什么

3. **使用实际列名**：{actual_columns}

4. **保存到指定路径**：严格使用上面指定的文件路径

5. **🔥 只保存必要的列**
   - 必须包含：ID 列（`序号`, `公开(公告)号`）+ 新生成的列
   - 禁止包含：原始数据列、前置步骤的列

6. **处理依赖**：如果需要前一步的结果，先检查文件是否存在，再加载

7. **遇到错误时**
   - 仔细阅读错误信息
   - 打印相关变量的值和类型
   - 调整代码，再试一次
   - 如果同样的方法失败多次，换一个完全不同的方法

📝 **代码执行模式（小步快跑）：**

```python
# ❌ 错误示例：试图一次完成所有事情
# 这样做你看不到中间结果，出错了也不知道哪里错了
df = pd.read_excel('data.xlsx')
df['new_col'] = some_complex_operation(df)
results = analyze(df)
results.to_csv('output.csv')
```

```python
# ✅ 正确示例：小步执行，每步验证

# 步骤1：加载数据
import pandas as pd
df = pd.read_excel('data.xlsx')
print(f"✅ 数据加载成功: {df.shape}")
print(f"列名: {list(df.columns)}")
```

```python
# 步骤2：查看数据
print("前5行数据:")
print(df.head())
print("\n数据类型:")
print(df.dtypes)
```

```python
# 步骤3：执行一小部分分析
# 先在一个样本上测试
sample = df.head(10)
result = some_operation(sample)
print(f"样本结果: {result}")
# 看起来正确，再应用到全部数据
```

```python
# 步骤4：应用到全部数据
df['new_col'] = some_operation(df)
print(f"✅ 新列生成完成")
print(f"新列的统计: {df['new_col'].describe()}")
```

```python
# 步骤5：保存结果（只保存必要的列）
results_df = df[['序号', '公开(公告)号', 'new_col']]
results_df.to_csv('output.csv', index=False)
print(f"✅ 结果已保存: {results_df.shape}")
```

**为什么要这样做？**
- 你能看到每一步的结果
- 出错时能立即发现问题在哪
- 可以根据中间结果调整策略
- 更容易调试和修复

**记住：你是在探索和学习，不是在执行预定的脚本！**

```python
# 步骤2：加载依赖数据（如果需要）
prev_results = pd.read_csv('outputs/step_1_topic_results.csv')
print(f"前置结果加载成功: {{prev_results.shape}}")
print(f"列名: {{list(prev_results.columns)}}")

# 合并数据（通过 ID 列）
# ⚠️ 前置结果只包含 ID + 新列，需要与主数据合并才能访问原始列
df = pd.merge(df, prev_results, on=['序号', '公开(公告)号'], how='left')
print(f"合并后: {{df.shape}}")
print(f"现在可以同时访问原始数据和前置步骤的结果")
```

```python
# 步骤3：执行分析
# ... 你的分析代码 ...
print("分析完成")
```

```python
# 步骤4：保存结果
import joblib

# ⚠️ 重要：只保存 ID 列和新生成的列！
# 
# ❌ 错误示例：
# df.to_csv('path.csv')  # 保存了所有列，包括原始数据
# results_df = pd.DataFrame({{'keywords': keywords_list}})  # 单列包含列表
#
# ✅ 正确示例：
# results_df = df[['序号', '公开(公告)号', 'new_col1', 'new_col2']]  # 只选择必要的列
# 
# 如果有多列需要展开（如 keyword_0, keyword_1...）：
# results_dict = {{'序号': df['序号'], '公开(公告)号': df['公开(公告)号']}}
# for i in range(5):
#     results_dict[f'keyword_{{i}}'] = [doc[i] if len(doc) > i else '' for doc in keywords_list]
# results_df = pd.DataFrame(results_dict)

# 示例：只保存 ID 和新列
results_df = df[['序号', '公开(公告)号', 'new_column1', 'new_column2']]
results_df.to_csv('指定的路径', index=False)
print(f"结果已保存: {{results_df.shape}}")

# 如果有模型
if 'model' in locals():
    joblib.dump(model, '指定的路径')
    print("模型已保存")
```

```python
# 步骤5：验证保存的文件
import os
if os.path.exists('指定的路径'):
    print(f"文件存在")
    # 读取并验证列数
    verify_df = pd.read_csv('指定的路径')
    print(f"保存的列: {{list(verify_df.columns)}}")
    print(f"列数: {{len(verify_df.columns)}}")
    print(f"前几行:")
    print(verify_df.head())
else:
    print(f"文件不存在")
```

**🎯 完成标准：**
当你完成以下所有步骤后，任务就完成了：
1. ✅ 数据已加载
2. ✅ 分析已完成
3. ✅ 结果已保存到指定路径
4. ✅ 文件已验证（列数和内容正确）

**🛑 停止条件（何时任务完成）：**

当你完成以下所有步骤后，**立即返回最终答案并停止**：
1. ✅ 数据已加载并验证
2. ✅ 分析已完成并打印了结果
3. ✅ 结果已保存到指定路径
4. ✅ 文件已验证（使用read_file查看前几行，确认列数和内容正确）

**最终答案格式：**
```
✅ 任务完成！

结果文件：outputs/step_X_results.csv
数据形状：(行数, 列数)
保存的列：['序号', '公开(公告)号', '新列1', '新列2']

验证通过：
- 文件存在 ✓
- 列数正确 ✓
- 数据格式正确 ✓
```

**⚠️ 完成验证后，不要执行任何额外的测试、分析或探索代码！**

---

开始执行吧！记住：
- 🐢 小步快跑，每步都要print确认
- 🔄 第一次失败是正常的，继续尝试
- 🎯 完成验证后立即停止并返回最终答案
        
        return prompt
    
    def _extract_final_result(self, agent_result: Dict) -> Dict[str, Any]:
        """从 agent 结果中提取最终结果"""
        messages = agent_result.get("messages", [])
        
        generated_code = []
        last_tool_result = ""
        iteration_count = 0
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # 提取代码块
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if tool_call['name'] == 'run_python':
                        code = tool_call['args'].get('code', '')
                        if code:
                            generated_code.append(code)
                            iteration_count += 1
            
            # 记录最后一个工具调用的结果
            if 'tool' in str(type(msg)).lower() or 'ToolMessage' in str(type(msg)):
                last_tool_result = content
        
        # 合并所有代码块
        full_code = "\n\n# ===== 下一步 =====\n\n".join(generated_code)
        
        # 判断代码是否有效：
        # 1. 有代码生成
        # 2. 最后的工具结果不包含错误标记
        # 3. 如果最后一个工具是read_file且成功，说明已经验证完成
        has_error = "❌" in last_tool_result or "Error" in last_tool_result or "Traceback" in last_tool_result
        has_verification = "✅ [OK] 读取成功" in last_tool_result or "文件存在" in last_tool_result
        is_code_valid = generated_code and not has_error
        
        # 如果已经验证了结果文件，认为任务完成
        if has_verification and not has_error:
            is_code_valid = True
        
        return {
            'generated_code': full_code,
            'iteration_count': iteration_count,
            'is_code_valid': is_code_valid,
            'runtime_error': last_tool_result if has_error else '',
            'error_history': self.error_history
        }
    
    def _parse_error(self, error_msg: str) -> Tuple[str, str]:
        """解析错误信息"""
        for error_type in ERROR_FIX_PROMPTS.keys():
            if error_type in error_msg:
                lines = error_msg.strip().split("\n")
                detail = lines[-1] if lines else error_msg
                return error_type, detail
        
        return "UnknownError", error_msg[:200]
    
    def _is_repeated_error(self, error_type: str, threshold: int = 2) -> bool:
        """检查是否为重复错误"""
        count = sum(1 for err in self.error_history if err['type'] == error_type)
        return count >= threshold
