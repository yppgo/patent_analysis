import sys
import os
import time

# 确保能导入 src 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.llm_client import LLMClient
from src.agents.coding_agent_v5 import CodingAgentV5
from src.tools.os_tools import OSTools

def setup_real_world_messy_data():
    """
    [场景模拟] 创建一个"脏"数据文件
    模拟真实情况：
    1. 文件名不规范 (sales_2024_v2_FINAL.log) - 并不是 .csv
    2. 数据含脏值 ('unknown', 'ERROR')
    3. 列名有空格 (' Product Name ', ' Revenue ')
    """
    print(">>> [场景搭建] 正在生成混淆的业务数据...")
    
    content = """Date, Region , Product Name , Revenue ,Qty
2024-01-01,North,Widget A,1000,50
2024-01-02,North,Widget A,1200,60
2024-01-03,South,Widget B,unknown,10
2024-01-04,South,Widget B,800,40
2024-01-05,East,Widget A,1100,55
2024-01-06,East,Widget C,ERROR,20
2024-01-07,North,Widget C,950,45
"""
    # 故意保存为 .log 后缀，考验 Agent 的灵活性
    filename = "sales_2024_v2_FINAL.log"
    OSTools.save_file(filename, content)
    return filename

def test_real_world_scenario():
    print("==========================================")
    print("🕵️‍♂️ CodingAgent V5 - 真实数据清洗与分析测试")
    print("==========================================\n")

    # 1. 准备环境
    filename = setup_real_world_messy_data()
    
    # 2. 初始化 Agent
    try:
        # 自动读取 .env 配置
        client = LLMClient.from_env()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("请检查你的 .env 文件是否配置了 API KEY")
        return

    agent = CodingAgentV5(llm_client=client, max_iterations=20)

    # 3. 下达一个"模糊且困难"的任务
    # 注意：我没有告诉它文件名叫什么，只说"目录下有个销售日志"
    user_goal = """
    当前目录下有一个 2024 年的销售日志文件（具体文件名我忘了，你自己找找，可能是 .log 结尾）。
    
    请帮我完成以下任务：
    1. 找到并读取这个文件。
    2. 清洗数据：
       - 'Revenue' 列包含一些脏数据（如 unknown, ERROR），请把它们剔除或设为 0。
       - 注意列名可能包含多余的空格，请修复。
    3. 分析数据：
       - 统计每个 Region（区域）的总收入 (Total Revenue)。
       - 找出销量 (Qty) 最高的 Date（日期）。
    4. 最后把统计结果打印出来。
    """
    
    print(f">>> [用户指令]\n{user_goal.strip()}\n")
    print("-" * 60)
    
    # 4. 启动执行
    start_time = time.time()
    result = agent.process(user_goal)
    end_time = time.time()
    
    print("-" * 60)
    print(f"\n✅ 测试结束 (耗时 {end_time - start_time:.2f}s)")
    
    # 5. 展示结果
    if result['status'] == 'success':
        print("\n📝 [Agent 最终回复]:")
        print(result['final_response'])
        
        print("\n🔍 [执行轨迹审计]:")
        for i, code in enumerate(result.get('code_history', [])):
            print(f"\n[Step {i+1} Python Code]:")
            print(code.strip())
    else:
        print(f"\n❌ 任务失败: {result.get('error')}")

    # 清理测试文件
    try: os.remove(filename)
    except: pass

if __name__ == "__main__":
    test_real_world_scenario()