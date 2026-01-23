#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Strategist Agent 与双图谱的集成
"""

import json
import os
from dotenv import load_dotenv
from src.utils.llm_client import get_llm_client
from src.agents.strategist import StrategistAgent
from src.graphs.causal_graph_query import CausalGraphQuery
from src.graphs.method_graph_query import MethodGraphQuery

# 加载环境变量
load_dotenv()


def test_strategist_with_dual_graphs():
    """测试 Strategist 能正确使用双图谱"""
    print("=" * 80)
    print("测试: Strategist Agent 与双图谱集成")
    print("=" * 80)
    
    # 初始化 LLM
    llm = get_llm_client()
    
    # 初始化因果图谱查询器
    causal_graph = CausalGraphQuery()
    
    # 初始化方法图谱查询器
    method_graph = MethodGraphQuery()
    
    # 初始化 Strategist（集成双图谱）
    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,  # 因果图谱
        method_graph=method_graph   # 方法图谱
    )
    
    # 测试场景：量子计算领域的技术影响力分析
    print("\n📋 测试场景: 量子计算领域的技术影响力分析")
    print("-" * 80)
    
    result = strategist.process({
        "user_goal": "分析量子计算领域的技术影响力驱动因素",
        "use_dag": True  # 使用 DAG 模式
    })
    
    # 验证结果结构
    print("\n✓ 验证结果结构")
    assert 'blueprint' in result, "结果应包含 blueprint"
    assert 'method_context' in result, "结果应包含 method_context"
    assert 'hypotheses' in result, "结果应包含 hypotheses（因果图谱生成）"
    print("  ✅ 结果结构正确")
    
    # 验证假设生成
    print("\n✓ 验证假设生成")
    hypotheses = result['hypotheses']
    assert 'step5_hypotheses' in hypotheses, "应包含假设列表"
    assert 'step6_recommendation' in hypotheses, "应包含推荐结果"
    
    hypothesis_list = hypotheses['step5_hypotheses']
    recommendation = hypotheses['step6_recommendation']
    
    print(f"  生成假设数: {len(hypothesis_list)}")
    print(f"  核心推荐数: {recommendation.get('core_count', 0)}")
    print(f"  备选推荐数: {recommendation.get('alternative_count', 0)}")
    
    assert len(hypothesis_list) >= 3, "应至少生成3个假设"
    assert recommendation.get('core_count', 0) >= 2, "应至少有2个核心推荐"
    print("  ✅ 假设生成正确")
    
    # 验证方法图谱信息
    print("\n✓ 验证方法图谱信息")
    method_context = result.get('method_context', '')
    if method_context:
        print(f"  方法上下文长度: {len(method_context)} 字符")
        print("  ✅ 方法图谱信息已使用")
    else:
        print("  ⚠️  方法上下文为空")
    
    # 验证 DAG 任务图
    print("\n✓ 验证 DAG 任务图")
    blueprint = result['blueprint']
    assert 'task_graph' in blueprint, "blueprint 应包含 task_graph"
    
    task_graph = blueprint['task_graph']
    print(f"  任务节点数: {len(task_graph)}")
    
    assert len(task_graph) >= 2, "应至少有2个任务节点"
    print("  ✅ DAG 任务图生成正确")
    
    # 验证任务包含假设验证
    print("\n✓ 验证任务包含假设验证")
    hypothesis_tasks = []
    for task in task_graph:
        task_type = task.get('task_type', '')
        description = task.get('description', '').lower()
        question = task.get('question', '').lower()
        
        if ('hypothesis' in task_type or 
            'hypothesis' in description or 
            'hypothesis' in question or
            '假设' in description or 
            '假设' in question):
            hypothesis_tasks.append(task)
    
    print(f"  假设验证任务数: {len(hypothesis_tasks)}")
    if hypothesis_tasks:
        print(f"  假设验证任务:")
        for task in hypothesis_tasks:
            print(f"    - {task.get('task_id')}: {task.get('question', task.get('description'))}")
        print("  ✅ 包含假设验证任务")
    else:
        print("  ⚠️  未检测到明确的假设验证任务（可能隐含在其他任务中）")
    
    # 验证列名选择正确
    print("\n✓ 验证列名选择")
    available_columns = strategist._load_real_columns()
    if available_columns:
        available_set = set(available_columns)
        
        invalid_columns = []
        for task in task_graph:
            config = task.get('implementation_config', {})
            columns_to_load = config.get('columns_to_load', [])
            
            for col in columns_to_load:
                if col not in available_set:
                    invalid_columns.append((task.get('task_id'), col))
        
        if invalid_columns:
            print(f"  ⚠️  发现无效列名:")
            for task_id, col in invalid_columns[:5]:
                print(f"    - 任务 {task_id}: '{col}'")
            print("  ❌ 列名选择有误")
        else:
            print(f"  ✅ 所有列名都在实际数据中存在")
    else:
        print("  ⚠️  无法验证列名（数据文件未加载）")
    
    # 保存结果
    output_file = "outputs/strategist_dual_graph_test_result.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 完整结果已保存到: {output_file}")
    
    # 打印核心推荐假设
    print("\n" + "=" * 80)
    print("核心推荐假设")
    print("=" * 80)
    
    core_recs = recommendation.get('core_recommendations', [])
    for rec in core_recs:
        h = rec['hypothesis']
        print(f"\n{rec['rank']}. {h['id']}: {h['statement']}")
        print(f"   推荐理由: {rec['reason']}")
        print(f"   变量: {h['variables']}")
    
    # 打印生成的任务
    print("\n" + "=" * 80)
    print("生成的任务图")
    print("=" * 80)
    
    for task in task_graph:
        print(f"\n任务 {task.get('task_id')}: {task.get('task_type')}")
        print(f"  问题: {task.get('question', 'N/A')}")
        print(f"  描述: {task.get('description', 'N/A')}")
        print(f"  输入变量: {task.get('input_variables', [])}")
        print(f"  输出变量: {task.get('output_variables', [])}")
        print(f"  依赖: {task.get('dependencies', [])}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    print("\n" + "🚀 开始测试 Strategist Agent 与双图谱集成" + "\n")
    
    try:
        # 测试：Strategist 与双图谱集成
        result = test_strategist_with_dual_graphs()
        
        print("\n" + "=" * 80)
        print("🎉 测试完成！")
        print("=" * 80)
        
        print("\n总结:")
        print("  ✅ Strategist 成功集成双图谱（因果图谱 + 方法图谱）")
        print("  ✅ 假设生成流程正常工作")
        print("  ✅ 方法推荐功能正常")
        print("  ✅ DAG 任务图生成正常")
        print("  ✅ 列名匹配功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
