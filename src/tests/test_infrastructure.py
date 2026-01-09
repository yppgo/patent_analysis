import sys
import os

# --- 路径黑魔法：确保能导入 src 目录下的模块 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)
# -------------------------------------------

try:
    from src.tools.repl import PythonREPL
    from src.tools.os_tools import OSTools
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print(f"当前 sys.path: {sys.path}")
    print(f"项目根目录: {project_root}")
    raise

def test_infrastructure():
    print("🚀 [开始] 基础设施自检...\n")
    
    # --- 1. 测试 REPL 的记忆力 ---
    print("1️⃣ [测试] Python REPL 状态保持能力")
    repl = PythonREPL()
    
    # 动作 A: 定义变量
    code_1 = "x = 100\ny = 200"
    print(f"   > 执行定义:\n{code_1}")
    out1 = repl.run(code_1)
    
    # 动作 B: 使用变量 (看它是否记得 x 和 y)
    code_2 = "print(f'计算结果: {x + y}')"
    print(f"   > 执行计算:\n{code_2}")
    out2 = repl.run(code_2)
    print(f"   [输出]: {out2.strip()}")
    
    # 评价指标
    if "300" in out2:
        print("   ✅ REPL 记忆测试通过")
    else:
        print("   ❌ REPL 记忆测试失败！")
        return

    print("-" * 30)

    # --- 2. 测试 OS Tools 的控制力 ---
    print("2️⃣ [测试] OS Tools 文件操作能力")
    
    # 动作: 创建一个假数据文件
    csv_content = "id,value\n1,10\n2,20"
    print("   > 正在创建 test_data.csv ...")
    OSTools.save_file("test_data.csv", csv_content)
    
    # 动作: 检查文件是否由 ls 列出
    ls_out = OSTools.list_files(".")
    
    # 评价指标
    if "test_data.csv" in ls_out:
        print("   ✅ 文件创建与列表测试通过")
    else:
        print(f"   ❌ 文件系统测试失败！\n目录内容:\n{ls_out}")
        return

    print("-" * 30)

    # --- 3. 测试 联合能力 (Agent 模拟) ---
    print("3️⃣ [测试] 联合能力 (模拟 Agent 读文件)")
    
    # 模拟 Agent 自己写代码读文件 (关键！不再依赖外部传 df)
    agent_code = """
import pandas as pd
# Agent 自己决定去读刚才创建的文件
df = pd.read_csv('test_data.csv')
print(f"读取行数: {len(df)}")
print(f"Value总和: {df['value'].sum()}")
"""
    print("   > Agent 正在执行 pandas 读取代码...")
    agent_out = repl.run(agent_code)
    print(f"   [Agent输出]:\n{agent_out.strip()}")
    
    # 评价指标
    if "读取行数: 2" in agent_out and "Value总和: 30" in agent_out:
        print("\n🎉 恭喜！联合能力测试通过！系统已具备 Open Interpreter 核心能力。")
    else:
        print("\n❌ 联合测试失败！")

    # 清理垃圾
    try: os.remove("test_data.csv") 
    except: pass

if __name__ == "__main__":
    test_infrastructure()