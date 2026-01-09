import pandas as pd
import numpy as np

# --- 0. 模拟数据生成器 (为了让你直接能跑) ---
def get_demo_data(query):
    """生成模拟的专利数据 DataFrame"""
    print(f"   [Data] 正在为 '{query}' 生成模拟数据...")
    data = {
        'patent_id': [f'P{i}' for i in range(1, 101)],
        'ipc': ['H04W']*40 + ['G06N']*30 + ['H04L']*20 + ['A61K']*10, # 模拟不同的IPC
        # 模拟引用国别：0代表外国，1代表本国
        'citation_country_code': [1]*20 + [0]*80, 
        'citations': np.random.randint(0, 50, 100)
    }
    return pd.DataFrame(data)

# --- 1. 具体的计算函数 (对应 JSON 里的 binding) ---

def calc_tech_intensity(df, query):
    """计算核心技术强度 (Total Count)"""
    return len(df)

def calc_tech_independence(df, query):
    """计算技术独立性 (本国引用占比)"""
    if 'citation_country_code' not in df.columns: return 0.0
    # 假设 1 是本国
    domestic_ratio = df['citation_country_code'].mean()
    return round(domestic_ratio, 4)

def calc_ipc_entropy(df, query):
    """计算技术跨界度 (IPC 信息熵)"""
    if 'ipc' not in df.columns: return 0.0
    counts = df['ipc'].value_counts()
    probs = counts / len(df)
    # Shannon Entropy
    entropy = -np.sum(probs * np.log2(probs + 1e-9)) 
    return round(entropy, 4)

# --- 2. 注册表 (供 Agent 调用) ---
METRICS_MAP = {
    "calc_tech_intensity": calc_tech_intensity,
    "calc_tech_independence": calc_tech_independence,
    "calc_ipc_entropy": calc_ipc_entropy
}