import json
import pandas as pd
import numpy as np
import os

# ==========================================
# 1. 模拟数据库 (Mock Data)
# 假装这是你清洗好的 Excel 数据
# ==========================================
def load_mock_data():
    print(">>> [System] 正在加载模拟数据...")
    data = {
        'title': [
            '6G Network Arch', 'AI based 6G', 'Terahertz comms', 
            '6G Security', 'Blockchain for 6G'
        ],
        'ipc': ['H04W', 'G06N', 'H04W', 'H04L', 'G06Q'], # 模拟跨界
        'is_domestic': [False, False, True, False, False] # 模拟引用本国专利情况 (只有1个是本国)
    }
    return pd.DataFrame(data)

# ==========================================
# 2. 工具箱 (The Metrics Tools)
# 这里放具体的计算公式
# ==========================================
def calc_tech_intensity(df):
    return len(df)

def calc_tech_independence(df):
    # 计算本国引用占比
    if len(df) == 0: return 0
    return round(df['is_domestic'].mean(), 2)

def calc_ipc_entropy(df):
    # 计算技术跨界度 (熵值)
    counts = df['ipc'].value_counts()
    probs = counts / len(df)
    entropy = -np.sum(probs * np.log2(probs + 1e-9))
    return round(entropy, 2)

# 函数注册表
TOOL_MAP = {
    "calc_tech_intensity": calc_tech_intensity,
    "calc_tech_independence": calc_tech_independence,
    "calc_ipc_entropy": calc_ipc_entropy
}

# ==========================================
# 3. 核心逻辑 (The Mini-Agent System)
# ==========================================
def run_sandbox_simulation(user_query="6G"):
    print(f"\n======== 🧪 开始沙盒测试: {user_query} ========")
    
    # --- Step A: 加载图谱 ---
    graph_path = os.path.join(os.path.dirname(__file__), 'causal_graph.json')
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    print("✅ 因果图谱加载成功")

    # --- Step B: 准备数据 ---
    df = load_mock_data()
    print(f"✅ 数据准备就绪 (共 {len(df)} 条记录)")

    # --- Step C: 模拟 Strategist (遍历图谱寻找假设) ---
    print("\n>>> [Strategist] 正在扫描图谱生成假设...")
    
    results = {}
    reports = []

    # 遍历每一条边，试图验证它
    for edge in graph['edges']:
        source_id = edge['source']
        target_id = edge['target']
        
        # 1. 找到节点对应的函数
        source_node = next(n for n in graph['nodes'] if n['id'] == source_id)
        target_node = next(n for n in graph['nodes'] if n['id'] == target_id)
        
        func_source = TOOL_MAP[source_node['binding']['func']]
        func_target = TOOL_MAP[target_node['binding']['func']]
        
        # 2. 执行计算 (Coding Agent 工作)
        val_source = func_source(df)
        val_target = func_target(df)
        
        print(f"    - 计算路径: {source_node['label']} -> {target_node['label']}")
        print(f"      [{source_node['label']}] = {val_source}")
        print(f"      [{target_node['label']}] = {val_target}")
        
        # 3. 生成报告 (Reporter 工作)
        # 简单的填槽逻辑
        hypothesis = edge['template'].format(
            user_query=user_query,
            val_source=val_source,
            val_target=val_target
        )
        reports.append(hypothesis)

    # --- Step D: 最终输出 ---
    print("\n======== 📄 最终生成的洞察报告 ========")
    for i, rep in enumerate(reports, 1):
        print(f"洞察 {i}: {rep}")
    print("==========================================")

if __name__ == "__main__":
    run_sandbox_simulation("6G通信")