import sys
import io
import contextlib
import traceback
import pandas as pd
import numpy as np

class PythonREPL:
    """
    持久化的 Python 交互式解释器 (Sandbox)。
    核心能力：在内存中维护 globals 字典，实现变量状态保留。
    """
    def __init__(self):
        # 初始化全局变量空间，预加载常用库，模仿 Jupyter 环境
        self.globals = {
            "pd": pd,
            "np": np,
            "sys": sys,
            "__builtins__": __builtins__,
        }
        self.locals = {}

    def run(self, code: str) -> str:
        """
        在沙箱中执行代码并捕获输出 (stdout + stderr)
        """
        io_buffer = io.StringIO()
        
        try:
            # 捕获标准输出和错误，模拟终端回显
            with contextlib.redirect_stdout(io_buffer), contextlib.redirect_stderr(io_buffer):
                # 🔥 关键修复：不使用 locals，所有变量都存储在 globals 中
                # 这样列表推导式就能访问到所有变量
                exec(code, self.globals)
            
            output = io_buffer.getvalue()
            # 如果代码没有打印任何东西，给一个反馈表明执行成功
            return output if output.strip() else "✅ 代码已执行 (无输出，请使用 print 查看结果)"
            
        except Exception:
            # 捕获运行时错误（如变量未定义、语法错误）
            error_msg = traceback.format_exc()
            return f"{io_buffer.getvalue()}\n❌ 运行时错误:\n{error_msg}"

    def get_var(self, name: str):
        """(调试用) 获取当前沙箱中的变量值"""
        return self.locals.get(name) or self.globals.get(name)
    
    def reset(self):
        """重置 REPL 环境，清除所有用户定义的变量"""
        self.globals = {
            "pd": pd,
            "np": np,
            "sys": sys,
            "__builtins__": __builtins__,
        }
        self.locals = {}