import json
import time
import getpass
import platform
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.base_agent import BaseAgent
from src.tools.repl import PythonREPL
from src.tools.os_tools import OSTools

class CodingAgentV5(BaseAgent):
    """
    Coding Agent V5 (Open Interpreter Soul)
    
    融合了 Open Interpreter 的核心 Prompt，强调：
    1. Full Permission (全权限)
    2. Tiny Steps (小步快跑)
    3. Stateful Execution (有状态执行)
    """
    
    def __init__(self, llm_client, max_iterations=20, logger=None):
        super().__init__("CodingAgentV5", llm_client, logger)
        self.max_iterations = max_iterations
        
        # 核心组件
        self.repl = PythonREPL()
        self.raw_llm = llm_client.get_llm() if hasattr(llm_client, 'get_llm') else llm_client
        self.tools = self._create_tools()
        self.agent = create_react_agent(self.raw_llm, self.tools)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务"""
        start_time = time.time()
        
        # 提取目标
        if isinstance(input_data, str):
            user_goal = input_data
        else:
            user_goal = input_data.get('execution_spec', {}).get('description', str(input_data))
        
        self.log(f"🚀 [启动 V5] 目标: {user_goal}")

        # 获取环境上下文
        work_dir = OSTools.execute_bash('pwd')
        user_name = getpass.getuser()
        os_name = platform.system()

        # 🔥 【核心融合】Open Interpreter 原版 Prompt + 我们的工具定义
        # 我直接套用了 default_system_message.py 的核心段落
        system_prompt = f"""
You are Open Interpreter, a world-class programmer that can complete any goal by executing code.
For advanced requests, start by writing a plan.
When you execute code, it will be executed **on the user's machine**. The user has given you **full and complete permission** to execute any code necessary to complete the task. Execute the code.
You can access the internet. Run **any code** to achieve the goal, and if at first you don't succeed, try again and again.
You can install new packages.
When a user refers to a filename, they're likely referring to an existing file in the directory you're currently executing code in.

**CRITICAL INSTRUCTIONS**:
As for actually executing code to carry out that plan, for *stateful* languages (like python, shell) **it's critical not to try to do everything in one code block.** You should try something, print information about it, then continue from there in **tiny, informed steps**. 
You will never get it on the first try, and attempting it in one go will often lead to errors you cant see.

User's Name: {user_name}
User's OS: {os_name}
Current Directory: {work_dir}

🛠️ **Your Tool Definitions**:
1. `run_python`: Executes Python code in a persistent Jupyter-like environment.
   - Variables are preserved across calls (Stateful).
   - **YOU MUST USE `print()`** to see the output of your code. If you don't print, you won't see anything.
2. `execute_shell`: Executes system Bash commands.
   - Use this to inspect files (`ls`, `head`), install packages (`pip`), or manage directories.

⚠️ **Final Requirement**:
When you have completed the goal, please start your final response with "Task Completed" and provide the answer.
"""

        try:
            # ReAct 循环
            result = self.agent.invoke(
                {"messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_goal)
                ]},
                config={"recursion_limit": self.max_iterations}
            )
            
            # 结果处理
            execution_time = time.time() - start_time
            code_history = self._extract_code_history(result["messages"])
            self.log(f"✅ [完成] 耗时 {execution_time:.2f}s | 步数: {len(code_history)}")
            
            return {
                "status": "success",
                "final_response": result["messages"][-1].content,
                "code_history": code_history
            }
            
        except Exception as e:
            self.log(f"❌ [失败] {e}", level="error")
            return {"status": "error", "error": str(e)}

    def _create_tools(self) -> List:
        @tool
        def run_python(code: str) -> str:
            """
            Executes Python code. STATEFUL environment.
            Use print() to output results.
            """
            print(f"\n🐍 \033[92m[Python]\033[0m Executing...")
            print(f"\033[90m{code}\033[0m")
            return self.repl.run(code)

        @tool
        def execute_shell(command: str) -> str:
            """
            Executes Shell commands (ls, pip, head, etc).
            """
            print(f"\n💻 \033[93m[Shell]\033[0m {command}")
            return OSTools.execute_bash(command)

        return [run_python, execute_shell]

    def _extract_code_history(self, messages) -> List[str]:
        code_blocks = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if tool_call['name'] == 'run_python':
                        code_blocks.append(tool_call['args'].get('code'))
        return code_blocks