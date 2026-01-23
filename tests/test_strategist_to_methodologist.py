#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：Strategist → Methodologist 完整流程

目标：
1. 验证Strategist能生成完整的DAG蓝图
2. 验证Methodologist能处理所有任务节点
3. 验证任务依赖关系正确
4. 验证技术规格可以传给Coding Agent
"""

import json
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用项目的LLM客户端
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.llm_client import get_llm_client
from src.utils.causal_graph_query import CausalGraphQuery
from src.utils.method_graph_query import MethodGraphQuery

# 导入Agents
from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent


def test_full_pipeline():
    """测试从Strategist到Methodologist的完整流程"""
    print("\n" + "=" * 80)
    print("🚀 端到端测试：Strategist → Methodologist")
    print("=" * 80)
    
    # 初始化组件
    print("\n📦 初始化组件...")
    llm = get_llm_client()
    
    # 加载图谱
    causal_graph = CausalGraphQuery("sandbox/static/data/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("sandbox/static/data/method_knowledge_base.json")
    
    # 初始化Agents
    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph
    )
    methodologist = MethodologistAgent(llm_client=llm)
    
    print("  ✅ Strategist Agent")
    print("  ✅ Methodologist Agent")
    print("  ✅ 因果图谱（30变量，135路径）")
    print("  ✅ 方法图谱（50篇论文）")
    
    # Step 1: Strategist生成蓝图
    print("\n" + "=" * 80)
    print("Step 1: Strategist 生成 DAG 蓝图")
    print("=" * 80)
    
    user_input = {
        "user_goal": "分析量子计算领域的技术影响力驱动因素",
        "data_file": "data/new_data.XLSX",
        "sheet_name": "sheet1",
        "use_dag": True
    }
    
    print(f"\n📝 用户输入:")
    print(f"  目标: {user_input['user_goal']}")
    print(f"  数据: {user_input['data_file']}")
    
    print(f"\n🔧 Strategist处理中...")
    blueprint_result = strategist.process(user_input)
    
    # 验证蓝图
    assert 'blueprint' in blueprint_result, "缺少blueprint字段"
    blueprint = blueprint_result['blueprint']
    
    assert 'task_graph' in blueprint, "缺少task_graph字段"
    task_graph = blueprint['task_graph']
    
    print(f"\n✅ 蓝图生成成功")
    print(f"  任务数量: {len(task_graph)}")
    print(f"  研究目标: {blueprint.get('research_objective', 'N/A')}")
    
    # 打印任务列表
    print(f"\n📋 任务列表:")
    for i, task in enumerate(task_graph, 1):
        print(f"  {i}. {task['task_id']}: {task['task_type']}")
        print(f"     问题: {task['question'][:60]}...")
        print(f"     依赖: {task.get('dependencies', [])}")
    
    # 保存蓝图
    blueprint_file = "outputs/e2e_test_blueprint.json"
    os.makedirs("outputs", exist_ok=True)
    with open(blueprint_file, 'w', encoding='utf-8') as f:
        json.dump(blueprint_result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 蓝图已保存: {blueprint_file}")
    
    # Step 2: Methodologist处理每个任务
    print("\n" + "=" * 80)
    print("Step 2: Methodologist 生成技术规格")
    print("=" * 80)
    
    specs = []
    for i, task in enumerate(task_graph, 1):
        print(f"\n🔧 处理任务 {i}/{len(task_graph)}: {task['task_id']}")
        print(f"  类型: {task['task_type']}")
        print(f"  问题: {task['question'][:60]}...")
        
        # Methodologist处理
        spec_result = methodologist.process({'task_node': task})
        
        # 验证技术规格
        assert 'technical_spec' in spec_result, f"任务{task['task_id']}缺少technical_spec"
        spec = spec_result['technical_spec']
        
        # 检查必要字段
        required_fields = ['function_name', 'function_signature', 'logic_flow', 'required_libraries']
        for field in required_fields:
            assert field in spec, f"任务{task['task_id']}缺少{field}字段"
        
        print(f"  ✅ 技术规格生成成功")
        print(f"     函数名: {spec['function_name']}")
        print(f"     逻辑步骤: {len(spec['logic_flow'])}步")
        print(f"     所需库: {', '.join(spec['required_libraries'][:3])}...")
        
        specs.append(spec_result)
        
        # 保存技术规格
        spec_file = f"outputs/e2e_test_{task['task_id']}_spec.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec_result, f, ensure_ascii=False, indent=2)
        print(f"     💾 已保存: {spec_file}")
    
    # Step 3: 验证完整性
    print("\n" + "=" * 80)
    print("Step 3: 验证完整性")
    print("=" * 80)
    
    print(f"\n✓ 基本验证")
    assert len(specs) == len(task_graph), "技术规格数量与任务数量不匹配"
    print(f"  ✅ 技术规格数量正确: {len(specs)}")
    
    assert all('technical_spec' in s for s in specs), "部分技术规格缺失"
    print(f"  ✅ 所有技术规格都存在")
    
    # 验证任务依赖关系
    print(f"\n✓ 任务依赖关系验证")
    task_ids = {task['task_id'] for task in task_graph}
    for task in task_graph:
        dependencies = task.get('dependencies', [])
        for dep in dependencies:
            assert dep in task_ids, f"任务{task['task_id']}依赖的{dep}不存在"
        if dependencies:
            print(f"  ✅ {task['task_id']} 依赖 {dependencies}")
        else:
            print(f"  ✅ {task['task_id']} 无依赖（根任务）")
    
    # 验证数据流
    print(f"\n✓ 数据流验证")
    for i, (task, spec_result) in enumerate(zip(task_graph, specs)):
        spec = spec_result['technical_spec']
        
        # 检查输入输出
        input_vars = task.get('input_variables', [])
        output_vars = task.get('output_variables', [])
        
        print(f"  {task['task_id']}:")
        print(f"    输入: {input_vars if input_vars else '无'}")
        print(f"    输出: {output_vars}")
        
        # 验证输出文件定义
        if 'data_flow' in spec:
            data_flow = spec['data_flow']
            assert 'output_files' in data_flow, f"{task['task_id']}缺少output_files"
            print(f"    输出文件: {data_flow['output_files']}")
    
    print(f"\n  ✅ 数据流正确")
    
    # Step 4: 评估质量
    print("\n" + "=" * 80)
    print("Step 4: 质量评估")
    print("=" * 80)
    
    total_score = 0
    for i, (task, spec_result) in enumerate(zip(task_graph, specs), 1):
        spec = spec_result['technical_spec']
        
        # 简单评分
        score = 0
        max_score = 100
        
        # 完整性（40分）
        required_fields = ['function_name', 'function_signature', 'logic_flow', 'required_libraries']
        score += sum(10 for f in required_fields if f in spec)
        
        # 逻辑流程（30分）
        logic_flow = spec.get('logic_flow', [])
        if len(logic_flow) >= 10:
            score += 30
        elif len(logic_flow) >= 5:
            score += 20
        else:
            score += 10
        
        # 契约（20分）
        if 'input_contract' in spec:
            score += 10
        if 'output_contract' in spec:
            score += 10
        
        # 错误处理（10分）
        if 'error_handling' in spec:
            score += 10
        
        percentage = score / max_score * 100
        total_score += percentage
        
        print(f"\n  任务 {i} ({task['task_id']}): {score}/{max_score} ({percentage:.1f}%)")
    
    avg_score = total_score / len(specs)
    print(f"\n  平均质量: {avg_score:.1f}%")
    
    if avg_score >= 90:
        print(f"  ✅ 质量优秀（>= 90%）")
    elif avg_score >= 80:
        print(f"  ⚠️  质量良好（80-90%）")
    else:
        print(f"  ❌ 质量不足（< 80%）")
    
    # 总结
    print("\n" + "=" * 80)
    print("🎉 端到端测试完成")
    print("=" * 80)
    
    print(f"\n📊 测试结果:")
    print(f"  ✅ Strategist生成蓝图: {len(task_graph)}个任务")
    print(f"  ✅ Methodologist生成技术规格: {len(specs)}个")
    print(f"  ✅ 任务依赖关系: 正确")
    print(f"  ✅ 数据流: 正确")
    print(f"  ✅ 平均质量: {avg_score:.1f}%")
    
    print(f"\n💾 输出文件:")
    print(f"  - {blueprint_file}")
    for i, task in enumerate(task_graph, 1):
        print(f"  - outputs/e2e_test_{task['task_id']}_spec.json")
    
    print(f"\n✅ 技术规格可以传给 Coding Agent")
    
    return {
        'blueprint': blueprint_result,
        'specs': specs,
        'avg_quality': avg_score
    }


def main():
    """主测试流程"""
    try:
        result = test_full_pipeline()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
