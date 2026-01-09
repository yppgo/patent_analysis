import pandas as pd
from src.tools.metrics_definitions import METRICS_MAP, get_demo_data

class CodingAgent:
    def __init__(self):
        pass

    def execute(self, plan):
        """执行计算任务"""
        print(f"💻 [CodingAgent] 开始执行代码...")
        
        query = plan['query']
        tasks = plan['tasks']
        results = {}
        
        # 1. 获取数据 (这里调用的是模拟数据生成器)
        df = get_demo_data(query)
        
        # 2. 逐个执行任务
        for func_name in tasks:
            if func_name in METRICS_MAP:
                func = METRICS_MAP[func_name]
                try:
                    val = func(df, query)
                    results[func_name] = val
                    print(f"   > 执行 {func_name} ... 结果: {val}")
                except Exception as e:
                    print(f"   x 执行 {func_name} 失败: {e}")
            else:
                print(f"   ? 未知函数: {func_name}")
                
        return results