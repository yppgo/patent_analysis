#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：Strategist → Methodologist → Coding Agent V4.2

目标：
1. 验证完整流程可以正常运行
2. 评估 Coding Agent V4.2 的代码生成质量
3. 确认生成的代码可以成功执行
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.utils.llm_client import get_llm_client
from src.graphs.causal_graph_query import CausalGraphQuery
from src.graphs.method_graph_query import MethodGraphQuery
from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def load_test_data(data_file: str, sheet_name: str = "sheet1") -> pd.DataFrame:
    """加载测试数据"""
    try:
        df = pd.read_excel(data_file, sheet_name=sheet_name)
        print(f"  ✅ 数据加载成功: {df.shape}")
        print(f"  列名: {list(df.columns)[:10]}...")
        return df
    except Exception as e:
        print(f"  ❌ 数据加载失败: {e}")
        return None


def test_full_pipeline():
    """测试从 Strategist 到 Coding Agent V4.2 的完整流程"""
    print("\n" + "=" * 80)
    print("🚀 端到端测试：Strategist → Methodologist → Coding Agent V4.2")
    print("=" * 80)
    
    # 创建输出目录
    Path('outputs').mkdir(exist_ok=True)
    
    # 初始化组件
    print("\n📦 Step 0: 初始化组件")
    print("-" * 40)
    
    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    
    # 加载图谱
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")
    
    # 初始化 Agents
    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)
    
    print("  ✅ Strategist Agent (V5.0)")
    print("  ✅ Methodologist Agent (V5.0)")
    print("  ✅ Coding Agent (V4.2)")
    print("  ✅ 因果图谱（30变量，135路径）")
    print("  ✅ 方法图谱（50篇论文）")
    
    # 加载测试数据
    print("\n📊 加载测试数据")
    data_file = "data/new_data.XLSX"
    test_data = load_test_data(data_file, "sheet1")
    
    if test_data is None:
        print("❌ 无法加载测试数据，终止测试")
        return
    
    # Step 1: Strategist 生成蓝图
    print("\n" + "=" * 80)
    print("📋 Step 1: Strategist 生成 DAG 蓝图")
    print("=" * 80)
    
    user_input = {
        "user_goal": "分析量子计算领域的技术影响力驱动因素",
        "data_file": data_file,
        "sheet_name": "sheet1",
        "use_dag": True
    }
    
    print(f"\n📝 用户输入:")
    print(f"  目标: {user_input['user_goal']}")
    print(f"  数据: {user_input['data_file']}")
    
    start_time = time.time()
    blueprint_result = strategist.process(user_input)
    strategist_time = time.time() - start_time
    
    # 验证蓝图
    assert 'blueprint' in blueprint_result, "缺少 blueprint 字段"
    blueprint = blueprint_result['blueprint']
    assert 'task_graph' in blueprint, "缺少 task_graph 字段"
    task_graph = blueprint['task_graph']
    
    print(f"\n✅ 蓝图生成成功 (耗时: {strategist_time:.1f}s)")
    print(f"  任务数量: {len(task_graph)}")
    print(f"  研究目标: {blueprint.get('research_objective', 'N/A')[:60]}...")
    
    # 打印任务列表
    print(f"\n📋 任务列表:")
    for i, task in enumerate(task_graph, 1):
        print(f"  {i}. {task['task_id']}: {task['task_type']}")
        print(f"     问题: {task['question'][:50]}...")
        print(f"     依赖: {task.get('dependencies', [])}")
    
    # 保存蓝图
    blueprint_file = "outputs/full_pipeline_blueprint.json"
    with open(blueprint_file, 'w', encoding='utf-8') as f:
        json.dump(blueprint_result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 蓝图已保存: {blueprint_file}")
    
    # Step 2: Methodologist 生成技术规格
    print("\n" + "=" * 80)
    print("📋 Step 2: Methodologist 生成技术规格")
    print("=" * 80)
    
    specs = []
    methodologist_times = []
    
    for i, task in enumerate(task_graph, 1):
        print(f"\n🔧 处理任务 {i}/{len(task_graph)}: {task['task_id']}")
        
        start_time = time.time()
        spec_result = methodologist.process({'task_node': task})
        methodologist_times.append(time.time() - start_time)
        
        # 验证技术规格
        assert 'technical_spec' in spec_result, f"任务 {task['task_id']} 缺少 technical_spec"
        spec = spec_result['technical_spec']
        
        # 检查是否有错误
        if 'error' in spec:
            print(f"  ❌ 技术规格生成失败 (耗时: {methodologist_times[-1]:.1f}s)")
            print(f"     错误: {spec['error']}")
            if 'raw_response' in spec:
                print(f"     原始响应（前500字符）:")
                print(f"     {spec['raw_response'][:500]}")
            # 保存错误信息
            spec_file = f"outputs/full_pipeline_{task['task_id']}_spec_error.json"
            with open(spec_file, 'w', encoding='utf-8') as f:
                json.dump(spec_result, f, ensure_ascii=False, indent=2)
            print(f"     💾 错误已保存: {spec_file}")
            continue
        
        print(f"  ✅ 技术规格生成成功 (耗时: {methodologist_times[-1]:.1f}s)")
        print(f"     函数名: {spec['function_name']}")
        print(f"     逻辑步骤: {len(spec.get('logic_flow', []))}步")
        
        specs.append(spec_result)
        
        # 保存技术规格
        spec_file = f"outputs/full_pipeline_{task['task_id']}_spec.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec_result, f, ensure_ascii=False, indent=2)
        print(f"     💾 已保存: {spec_file}")
    
    # Step 3: Coding Agent V4.2 执行代码生成
    print("\n" + "=" * 80)
    print("📋 Step 3: Coding Agent V4.2 生成并执行代码")
    print("=" * 80)
    
    coding_results = []
    coding_times = []
    success_count = 0
    
    for i, (task, spec_result) in enumerate(zip(task_graph, specs), 1):
        print(f"\n🔧 执行任务 {i}/{len(task_graph)}: {task['task_id']}")
        print(f"  函数名: {spec_result['technical_spec']['function_name']}")
        
        # 清理旧结果文件
        task_id = task['task_id']
        expected_output_file = (
            spec_result.get('technical_spec', {}).get('output_file')
            or task.get('implementation_config', {}).get('output_file')
            or f"outputs/{task_id}_results.csv"
        )
        old_result_file = Path(expected_output_file)
        if old_result_file.exists():
            old_result_file.unlink()
            print(f"  🗑️ 清理旧文件: {old_result_file}")
        
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
            coding_times.append(time.time() - start_time)
            
            is_valid = result.get('is_code_valid', False)
            iteration_count = result.get('iteration_count', 0)
            runtime_error = result.get('runtime_error', '')
            
            if is_valid:
                success_count += 1
                print(f"  ✅ 代码生成并执行成功 (耗时: {coding_times[-1]:.1f}s, 迭代: {iteration_count}次)")
            else:
                print(f"  ❌ 代码执行失败 (耗时: {coding_times[-1]:.1f}s, 迭代: {iteration_count}次)")
                if runtime_error:
                    print(f"     错误: {runtime_error[:100]}...")
            
            coding_results.append(result)
            
            # 保存生成的代码
            if result.get('generated_code'):
                code_file = f"outputs/full_pipeline_{task_id}.py"
                with open(code_file, 'w', encoding='utf-8') as f:
                    f.write(result['generated_code'])
                print(f"     💾 代码已保存: {code_file}")
            
        except Exception as e:
            coding_times.append(time.time() - start_time)
            print(f"  ❌ 执行异常: {e}")
            coding_results.append({'error': str(e), 'is_code_valid': False})
    
    # Step 4: 评估结果
    print("\n" + "=" * 80)
    print("📊 Step 4: 测试结果评估")
    print("=" * 80)
    
    total_tasks = len(task_graph)
    success_rate = success_count / total_tasks * 100 if total_tasks > 0 else 0
    
    print(f"\n📈 性能指标:")
    print(f"  Strategist 耗时: {strategist_time:.1f}s")
    print(f"  Methodologist 平均耗时: {sum(methodologist_times)/len(methodologist_times):.1f}s")
    print(f"  Coding Agent 平均耗时: {sum(coding_times)/len(coding_times):.1f}s")
    print(f"  总耗时: {strategist_time + sum(methodologist_times) + sum(coding_times):.1f}s")
    
    print(f"\n🎯 质量指标:")
    print(f"  任务总数: {total_tasks}")
    print(f"  成功数量: {success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    
    # 检查输出文件
    print(f"\n📁 输出文件检查:")
    for task in task_graph:
        task_id = task['task_id']
        expected_output_file = (
            task.get('implementation_config', {}).get('output_file')
            or f"outputs/{task_id}_results.csv"
        )
        result_file = Path(expected_output_file)
        code_file = Path(f"outputs/full_pipeline_{task_id}.py")
        
        if result_file.exists():
            suffix = result_file.suffix.lower()
            if suffix == '.csv':
                df = pd.read_csv(result_file)
                print(f"  ✅ {result_file}: {df.shape[0]}行, {df.shape[1]}列")
            else:
                size = result_file.stat().st_size
                print(f"  ✅ {result_file}: 存在 (大小: {size} 字节)")
        else:
            print(f"  ❌ {result_file}: 不存在")
        
        if code_file.exists():
            print(f"  ✅ {code_file}: 存在")
        else:
            print(f"  ❌ {code_file}: 不存在")
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    
    if success_rate >= 80:
        print(f"\n✅ 测试通过！成功率: {success_rate:.1f}%")
        print("  建议：当前方案可用，继续优化细节")
    elif success_rate >= 50:
        print(f"\n⚠️ 测试部分通过。成功率: {success_rate:.1f}%")
        print("  建议：分析失败原因，优化 Prompt 或启用 execution_plan")
    else:
        print(f"\n❌ 测试未通过。成功率: {success_rate:.1f}%")
        print("  建议：深入分析问题，考虑架构调整")
    
    # 保存测试报告
    report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_goal': user_input['user_goal'],
        'total_tasks': total_tasks,
        'success_count': success_count,
        'success_rate': success_rate,
        'strategist_time': strategist_time,
        'methodologist_times': methodologist_times,
        'coding_times': coding_times,
        'total_time': strategist_time + sum(methodologist_times) + sum(coding_times),
        'coding_results': [
            {
                'task_id': task['task_id'],
                'is_valid': r.get('is_code_valid', False),
                'iteration_count': r.get('iteration_count', 0),
                'error': r.get('runtime_error', '') or r.get('error', '')
            }
            for task, r in zip(task_graph, coding_results)
        ]
    }
    
    report_file = "outputs/full_pipeline_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 测试报告已保存: {report_file}")
    
    return report


if __name__ == "__main__":
    test_full_pipeline()
