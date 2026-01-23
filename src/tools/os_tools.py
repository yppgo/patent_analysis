import subprocess
import os
import glob
import re
from pathlib import Path

class OSTools:
    """
    系统级操作工具箱 (Shell & File System)
    """
    
    @staticmethod
    def execute_bash(command: str, timeout: int = 60) -> str:
        """
        执行 Shell 命令 (如 pip install, ls, cat)
        """
        try:
            # 简单拦截极度危险命令
            if command.strip().startswith(("rm -rf /", ":(){:|:&};:")):
                return "❌ 安全拦截: 禁止执行高危破坏性命令"

            # Windows 命令适配
            if os.name == 'nt':  # Windows 系统
                # 替换常见的 Unix 命令为 Windows 命令
                cmd = command.strip()

                # ls / ls -la / ls -l / ls -la path -> dir path
                # Windows 的 dir 不支持 -la 这类开关（会报“无效开关”），因此直接丢弃 unix flags。
                m = re.match(r"^ls(\s+.+)?$", cmd)
                if m:
                    rest = (m.group(1) or "").strip()
                    if not rest:
                        command = "dir"
                    else:
                        tokens = rest.split()
                        path_tokens = [t for t in tokens if not t.startswith('-')]
                        if path_tokens:
                            command = "dir " + " ".join(path_tokens)
                        else:
                            command = "dir"

                # head -n 5 file -> powershell Get-Content -TotalCount 5 file
                m = re.match(r"^head\s+-n\s+(\d+)\s+(.+)$", cmd)
                if m:
                    n = m.group(1)
                    file_path = m.group(2).strip().strip('"')
                    command = f'powershell -NoProfile -Command "Get-Content -TotalCount {n} -Path \"{file_path}\""'

                if cmd.startswith('mkdir -p '):
                    # Windows 的 mkdir 自动创建父目录
                    command = cmd.replace('mkdir -p ', 'mkdir ', 1)
                elif cmd.startswith('cat '):
                    command = cmd.replace('cat ', 'type ', 1)
                elif cmd == 'pwd':
                    command = 'cd'
            
            # 根据系统选择合适的编码
            # Windows 中文系统使用 GBK，其他系统使用 UTF-8
            encoding = 'gbk' if os.name == 'nt' else 'utf-8'
            
            # 运行命令
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                encoding=encoding,
                errors='replace' # 防止编码错误导致 crash
            )
            
            output = result.stdout
            if result.stderr:
                # 过滤掉一些无关紧要的 Windows 警告
                stderr = result.stderr
                # 忽略 mkdir 的"已存在"警告
                if not ('已经存在' in stderr or 'already exists' in stderr.lower()):
                    output += f"\n⚠️ Stderr:\n{stderr}"
            
            return output.strip() if output.strip() else "✅ 命令执行完成 (无输出)"
            
        except subprocess.TimeoutExpired:
            return f"❌ 命令执行超时 ({timeout}s)"
        except Exception as e:
            return f"❌ 系统错误: {str(e)}"

    @staticmethod
    def list_files(path="."):
        """列出目录结构"""
        try:
            if not os.path.exists(path):
                return f"❌ 路径不存在: {path}"
            
            files = []
            # 使用 scandir 获取更详细的文件信息
            with os.scandir(path) as it:
                for entry in it:
                    if not entry.name.startswith('.'): # 忽略隐藏文件
                        name = entry.name + ("/" if entry.is_dir() else "")
                        files.append(name)
            return f"📂 目录清单 ({os.path.abspath(path)}):\n" + "\n".join(files)
        except Exception as e:
            return f"❌ 无法列出目录: {e}"

    @staticmethod
    def save_file(filepath: str, content: str):
        """写入文件 (用于创建测试数据)"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ 文件已保存: {filepath}"
        except Exception as e:
            return f"❌ 写入失败: {e}"