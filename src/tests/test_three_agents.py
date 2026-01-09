"""
三 Agent 协作测试
测试 Strategist -> Methodologist -> Coding Agent 的完整流程
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 添加 src 目录到路径
src_root = Path(__file__).parent.parent
sys.path.insert(0, str(src_root))

from agents.strategist import StrategistAgent
from agents.methodologist import MethodologistAgent
from agents.coding_agent import CodingAgentV2
from utils.llm_client import get_llm_client
from utils.neo4j_connector import Neo4jConnector
from core.workflow import build_full_workflow


def create_test_data():
    """创建测试数据"""
    return pd.DataFrame({
        'title': [
            'Deep Learning for Patent Classification',
            'Machine Learning in Technology Analysis',
            'AI-based Patent Mining System'
        ],
        'abstract': [
            'This paper presents a deep learning approach for automatic patent classification.',
            'We propose a machine learning framework for analyzing technology trends.',
            'An artificial intelligence system for mining patent information is developed.'
        ],
        'year': [2020, 2021, 2022],
        'citations': [15, 8, 3]
    })


def test_strategist_only():
    """测试 Strategist Agent"""
    print("\n" + "="*80)
    print("测试 1: Strategist Agent")
    print("="*80)
    
    # 初始化
    llm = get_llm_client()
    neo4j = Neo4jConnector()
    strategist = StrategistAgent(llm, neo4j)
    
    # 用户目标
    user_goal = "分析专利数据中的技术空白，识别未被充分研究的技术领域"
    
    # 执行
    result = strategist.process({'user_goal': user_goal})
    
    # 输出结果
    blueprint = result['blueprint']
    print(f"\n📋 战略蓝图:")
    print(f"  - 研究目标: {blueprint.get('research_objective', 'N/A')}")
    print(f"  - 分析步骤数: {len(blueprint.get('analysis_logic_chains', []))}")
    
    for i, step in enumerate(blueprint.get('analysis_logic_chains', []), 1):
        print(f"\n  步骤 {i}: {step.get('objective', 'N/A')}")
        print(f"    方法: {step.get('method', 'N/A')}")
    
    neo4j.close()
    return blueprint


def test_methodologist_only(blueprint):
    """测试 Methodologist Agent"""
    print("\n" + "="*80)
    print("测试 2: Methodologist Agent")
    print("="*80)
    
    # 初始化
    llm = get_llm_client()
    methodologist = MethodologistAgent(llm)
    
    # 处理步骤
    steps = blueprint.get('analysis_logic_chains', [])
    execution_specs = methodologist.process_multiple(steps)
    
    # 输出结果
    print(f"\n🔧 执行规格:")
    for i, spec in enumerate(execution_specs, 1):
        if 'error' in spec:
            print(f"\n  规格 {i}: ❌ 生成失败")
            print(f"    错误: {spec['error']}")
        else:
            print(f"\n  规格 {i}: ✅ {spec.get('function_name', 'N/A')}")
            print(f"    库依赖: {', '.join(spec.get('required_libraries', []))}")
            print(f"    处理步骤数: {len(spec.get('processing_steps', []))}")
    
    return execution_specs


def test_coding_agent_only(execution_specs, blueprint):
    """测试 Coding Agent"""
    print("\n" + "="*80)
    print("测试 3: Coding Agent V2")
    print("="*80)
    
    # 初始化
    llm = get_llm_client()
    test_data = create_test_data()
    coding_agent = CodingAgentV2(llm, test_data=test_data, max_iterations=2)
    
    # 生成代码
    steps = blueprint.get('analysis_logic_chains', [])
    
    for i, (spec, step) in enumerate(zip(execution_specs, steps), 1):
        print(f"\n{'='*60}")
        print(f"生成代码 {i}/{len(execution_specs)}")
        print(f"{'='*60}")
        
        if 'error' in spec:
            print(f"❌ 跳过（规格生成失败）")
            continue
        
        result = coding_agent.process({
            'execution_spec': spec,
            'current_step': step,
            'test_data': test_data
        })
        
        print(f"\n📝 代码生成结果:")
        print(f"  - 迭代次数: {result['iteration_count']}")
        print(f"  - 代码有效: {result['is_code_valid']}")
        print(f"  - 代码行数: {len(result['generated_code'].split(chr(10)))}")
        
        if result['code_issues']:
            print(f"  - 问题: {len(result['code_issues'])} 个")
            for issue in result['code_issues'][:3]:
                print(f"    • {issue}")
        
        if result['runtime_error']:
            print(f"  - 运行时错误: {result['runtime_error']}")
        
        # 显示代码片段
        code_lines = result['generated_code'].split('\n')
        print(f"\n  代码预览 (前 10 行):")
        for line in code_lines[:10]:
            print(f"    {line}")
        if len(code_lines) > 10:
            print(f"    ... (还有 {len(code_lines) - 10} 行)")


def test_full_workflow():
    """测试完整工作流"""
    print("\n" + "="*80)
    print("测试 4: 完整工作流 (Strategist -> Methodologist -> Coding)")
    print("="*80)
    
    # 初始化所有 Agent
    llm = get_llm_client()
    neo4j = Neo4jConnector()
    test_data = create_test_data()
    
    strategist = StrategistAgent(llm, neo4j)
    methodologist = MethodologistAgent(llm)
    coding_agent = CodingAgentV2(llm, test_data=test_data, max_iterations=2)
    
    # 构建工作流
    workflow = build_full_workflow(strategist, methodologist, coding_agent)
    
    # 执行工作流
    user_goal = "分析专利数据中的技术空白"
    
    print(f"\n🎯 用户目标: {user_goal}")
    print(f"📊 测试数据: {len(test_data)} 条记录")
    print(f"\n开始执行工作流...\n")
    
    result = workflow.invoke({
        'user_goal': user_goal,
        'test_data': test_data,
        'blueprint': {},
        'graph_context': '',
        'execution_specs': [],
        'generated_codes': [],
        'code_metadata': []
    })
    
    # 输出结果
    print(f"\n{'='*80}")
    print("工作流执行完成")
    print(f"{'='*80}")
    
    blueprint = result['blueprint']
    print(f"\n📋 战略蓝图:")
    print(f"  - 研究目标: {blueprint.get('research_objective', 'N/A')[:80]}...")
    print(f"  - 分析步骤: {len(blueprint.get('analysis_logic_chains', []))} 个")
    
    print(f"\n🔧 执行规格:")
    for i, spec in enumerate(result['execution_specs'], 1):
        if 'error' not in spec:
            print(f"  {i}. {spec.get('function_name', 'N/A')}")
    
    print(f"\n💻 生成代码:")
    for i, (code, metadata) in enumerate(zip(result['generated_codes'], result['code_metadata']), 1):
        if code:
            print(f"  {i}. ✅ {len(code.split(chr(10)))} 行代码")
            print(f"     迭代: {metadata.get('iteration_count', 0)} 次")
            print(f"     有效: {metadata.get('is_valid', False)}")
        else:
            print(f"  {i}. ❌ 生成失败")
    
    neo4j.close()
    
    return result


if __name__ == "__main__":
    print("\n" + "="*80)
    print("三 Agent 协作系统测试")
    print("="*80)
    
    # 选择测试模式
    print("\n选择测试模式:")
    print("1. 测试 Strategist Agent")
    print("2. 测试 Methodologist Agent")
    print("3. 测试 Coding Agent V2")
    print("4. 测试完整工作流")
    print("5. 运行所有测试")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice == "1":
        test_strategist_only()
    elif choice == "2":
        blueprint = test_strategist_only()
        test_methodologist_only(blueprint)
    elif choice == "3":
        blueprint = test_strategist_only()
        execution_specs = test_methodologist_only(blueprint)
        test_coding_agent_only(execution_specs, blueprint)
    elif choice == "4":
        test_full_workflow()
    elif choice == "5":
        blueprint = test_strategist_only()
        execution_specs = test_methodologist_only(blueprint)
        test_coding_agent_only(execution_specs, blueprint)
        test_full_workflow()
    else:
        print("无效选项")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
