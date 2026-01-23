"""
快速测试：验证qwen-max模型的效果
只测试前2个任务，避免超时
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
import pandas as pd
from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent
from src.agents.coding_agent_v4_2 import CodingAgentV4_2

def test_qwen_quick():
    print("=" * 80)
    print("快速测试：Strategist -> Methodologist -> Coding Agent (qwen-max)")
    print("=" * 80)
    
    # 初始化
    print("\n初始化组件...")
    strategist = StrategistAgent()
    methodologist = MethodologistAgent()
    coding_agent = CodingAgentV4_2()
    
    # 加载测试数据
    print("加载测试数据...")
    df = pd.read_excel('data/new_data.XLSX')
    print(f"数据加载成功: {df.shape}")
    
    # Step 1: Strategist
    print("\n" + "=" * 80)
    print("Step 1: Strategist 生成蓝图")
    print("=" * 80)
    
    user_goal = "分析量子计算领域的技术影响力驱动因素"
    data_path = "data/new_data.XLSX"
    
    start = time.time()
    blueprint = strategist.process({
        'user_goal': user_goal,
        'data_path': data_path,
        'test_data': df
    })
    strategist_time = time.time() - start
    
    print(f"\n蓝图生成成功 (耗时: {strategist_time:.1f}s)")
    task_graph = blueprint['blueprint']['task_graph']
    print(f"任务数量: {len(task_graph)}")
    
    # 只测试前2个任务
    task_graph = task_graph[:2]
    print(f"测试任务: {[t['task_id'] for t in task_graph]}")
    
    # Step 2: Methodologist
    print("\n" + "=" * 80)
    print("Step 2: Methodologist 生成技术规格")
    print("=" * 80)
    
    specs = []
    for i, task in enumerate(task_graph, 1):
        print(f"\n处理任务 {i}/{len(task_graph)}: {task['task_id']}")
        
        start = time.time()
        spec_result = methodologist.process({'task_node': task})
        method_time = time.time() - start
        
        spec = spec_result['technical_spec']
        if 'error' in spec:
            print(f"  失败 (耗时: {method_time:.1f}s)")
            print(f"  错误: {spec['error']}")
            continue
        
        print(f"  成功 (耗时: {method_time:.1f}s)")
        print(f"  函数名: {spec['function_name']}")
        specs.append(spec_result)
    
    # Step 3: Coding Agent
    print("\n" + "=" * 80)
    print("Step 3: Coding Agent 执行代码生成")
    print("=" * 80)
    
    for i, (task, spec_result) in enumerate(zip(task_graph, specs), 1):
        print(f"\n执行任务 {i}/{len(specs)}: {task['task_id']}")
        
        spec = spec_result['technical_spec']
        
        start = time.time()
        result = coding_agent.process({
            'task_node': task,
            'technical_spec': spec,
            'test_data': df
        })
        coding_time = time.time() - start
        
        if result.get('success'):
            print(f"  成功 (耗时: {coding_time:.1f}s)")
            print(f"  输出: {result.get('output_file', 'N/A')}")
        else:
            print(f"  失败 (耗时: {coding_time:.1f}s)")
            print(f"  错误: {result.get('error', 'Unknown')}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_qwen_quick()
