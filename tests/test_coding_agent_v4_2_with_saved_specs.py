#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Coding Agent V4.2：使用已保存的技术规格

直接加载 Strategist → Methodologist 生成的文件，跳过网络敏感阶段
"""

import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.utils.llm_client import LLMClient
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def test_coding_agent_with_saved_specs():
    """使用已保存的技术规格测试 Coding Agent V4.2"""
    print("\n" + "=" * 80)
    print("🚀 Coding Agent V4.2 测试（使用已保存的技术规格）")
    print("=" * 80)
    
    # 加载已保存的文件
    print("\n📦 加载已保存的文件...")
    
    blueprint_file = "outputs/e2e_test_blueprint.json"
    spec_files = [
        "outputs/e2e_test_task_1_spec.json",
        "outputs/e2e_test_task_2_spec.json"
    ]
    
    # 加载蓝图
    with open(blueprint_file, 'r', encoding='utf-8') as f:
        blueprint_result = json.load(f)
    blueprint = blueprint_result['blueprint']
    task_graph = blueprint['task_graph']
    print(f"  ✅ 蓝图加载成功: {len(task_graph)} 个任务")
    
    # 加载技术规格
    specs = []
    for spec_file in spec_files:
        with open(spec_file, 'r', encoding='utf-8') as f:
            specs.append(json.load(f))
    print(f"  ✅ 技术规格加载成功: {len(specs)} 个")
    
    # 加载测试数据
    data_file = "data/new_data.XLSX"
    test_data = pd.read_excel(data_file, sheet_name="sheet1")
    print(f"  ✅ 数据加载成功: {test_data.shape}")
    
    # 初始化 Coding Agent V4.2
    print("\n📦 初始化 Coding Agent V4.2...")
    llm = LLMClient.from_env()
    coding_agent = CodingAgentV4_2(llm_client=llm, max_iterations=15)
    print("  ✅ Coding Agent V4.2 初始化成功")
    
    # 执行每个任务
    print("\n" + "=" * 80)
    print("📋 执行代码生成和运行")
    print("=" * 80)
    
    coding_results = []
    coding_times = []
    success_count = 0
    
    for i, (task, spec_result) in enumerate(zip(task_graph, specs), 1):
        print(f"\n{'='*60}")
        print(f"🔧 执行任务 {i}/{len(task_graph)}: {task['task_id']}")
        print(f"{'='*60}")
        print(f"  函数名: {spec_result['technical_spec']['function_name']}")
        print(f"  问题: {task['question'][:60]}...")
        
        # 清理旧结果文件
        task_id = task['task_id']
        for old_file in Path("outputs").glob(f"*{task_id}*results*"):
            old_file.unlink()
            print(f"  🗑️ 清理: {old_file.name}")
        
        # 准备输入
        coding_input = {
            'execution_spec': spec_result['technical_spec'],
            'current_step': task,
            'test_data': test_data,
            'previous_result': coding_results[-1] if coding_results else None
        }
        
        start_time = time.time()
        try:
            result = coding_agent.process(coding_input)
            elapsed = time.time() - start_time
            coding_times.append(elapsed)
            
            is_valid = result.get('is_code_valid', False)
            iteration_count = result.get('iteration_count', 0)
            runtime_error = result.get('runtime_error', '')
            
            if is_valid:
                success_count += 1
                print(f"\n  ✅ 成功！(耗时: {elapsed:.1f}s, 迭代: {iteration_count}次)")
            else:
                print(f"\n  ❌ 失败 (耗时: {elapsed:.1f}s, 迭代: {iteration_count}次)")
                if runtime_error:
                    print(f"     错误: {runtime_error[:150]}...")
            
            coding_results.append(result)
            
            # 保存生成的代码
            if result.get('generated_code'):
                code_file = f"outputs/coding_v4_2_{task_id}.py"
                with open(code_file, 'w', encoding='utf-8') as f:
                    f.write(result['generated_code'])
                print(f"  💾 代码已保存: {code_file}")
            
        except Exception as e:
            coding_times.append(time.time() - start_time)
            print(f"  ❌ 异常: {e}")
            coding_results.append({'error': str(e), 'is_code_valid': False})
    
    # 评估结果
    print("\n" + "=" * 80)
    print("📊 测试结果")
    print("=" * 80)
    
    total_tasks = len(task_graph)
    success_rate = success_count / total_tasks * 100
    
    print(f"\n🎯 成功率: {success_count}/{total_tasks} ({success_rate:.0f}%)")
    print(f"⏱️ 总耗时: {sum(coding_times):.1f}s")
    print(f"⏱️ 平均耗时: {sum(coding_times)/len(coding_times):.1f}s/任务")
    
    # 检查输出文件
    print(f"\n📁 输出文件:")
    for task in task_graph:
        task_id = task['task_id']
        for f in Path("outputs").glob(f"*{task_id}*"):
            size = f.stat().st_size
            print(f"  {'✅' if size > 0 else '❌'} {f.name} ({size} bytes)")
    
    # 总结
    if success_rate >= 80:
        print(f"\n✅ 测试通过！Coding Agent V4.2 质量达标")
    elif success_rate >= 50:
        print(f"\n⚠️ 测试部分通过，需要优化")
    else:
        print(f"\n❌ 测试未通过，需要分析问题")
    
    return {
        'success_count': success_count,
        'total_tasks': total_tasks,
        'success_rate': success_rate,
        'coding_times': coding_times
    }


if __name__ == "__main__":
    test_coding_agent_with_saved_specs()
