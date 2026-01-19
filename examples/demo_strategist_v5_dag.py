"""
演示 Strategist V5.0 的 DAG 模式输出

展示 DAG 模式生成的完整结构，包括：
- thinking_trace（思考过程）
- task_graph（任务图）
- 变量流（input_variables, output_variables）
- 依赖关系（dependencies）
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.strategist import StrategistAgent
from src.utils.llm_client import get_llm_client
from src.utils.logger import setup_logger
from src.utils.neo4j_connector import Neo4jConnector


def demo_dag_mode():
    """演示 DAG 模式"""
    print("\n" + "="*80)
    print("Strategist V5.0 - DAG 模式演示")
    print("="*80)
    
    # 初始化
    llm = get_llm_client()
    logger = setup_logger("demo_strategist_v5")
    
    # 尝试连接 Neo4j
    neo4j = None
    try:
        neo4j = Neo4jConnector()
        print("✓ Neo4j 连接成功")
    except Exception as e:
        print(f"⚠️ Neo4j 连接失败: {e}")
        print("  将在没有知识图谱的情况下运行")
    
    # 创建 Strategist（会自动从数据文件读取列名）
    strategist = StrategistAgent(llm, neo4j_connector=neo4j, logger=logger)
    
    # 测试场景
    user_goal = "分析数据安全领域的技术趋势和创新热点"
    
    print(f"\n用户目标: {user_goal}")
    print("正在生成 DAG 蓝图...")
    print("（Strategist 会自动从数据文件读取列名）")
    
    # 调用 DAG 模式（不指定 available_columns，让它自动读取）
    result = strategist.process({
        'user_goal': user_goal,
        'use_dag': True  # 启用 DAG 模式
    })
    
    blueprint = result['blueprint']
    
    # 保存完整结果
    output_file = 'outputs/strategist_v5_dag_demo.json'
    os.makedirs('outputs', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blueprint, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 完整结果已保存到: {output_file}")
    
    # 打印关键信息
    print("\n" + "="*80)
    print("DAG 蓝图结构")
    print("="*80)
    
    # 1. Thinking Trace
    if 'thinking_trace' in blueprint:
        print("\n【1. 思考过程 (Thinking Trace)】")
        thinking = blueprint['thinking_trace']
        for key, value in thinking.items():
            print(f"\n  {key}:")
            print(f"    {value[:200]}..." if len(str(value)) > 200 else f"    {value}")
    
    # 2. 研究目标
    print(f"\n【2. 研究目标】")
    print(f"  {blueprint.get('research_objective', 'N/A')}")
    
    # 3. 预期成果
    if 'expected_outcomes' in blueprint:
        print(f"\n【3. 预期成果】")
        for i, outcome in enumerate(blueprint['expected_outcomes'], 1):
            print(f"  {i}. {outcome}")
    
    # 4. 任务图 (Task Graph)
    if 'task_graph' in blueprint:
        task_graph = blueprint['task_graph']
        print(f"\n【4. 任务图 (Task Graph)】")
        print(f"  总任务数: {len(task_graph)}")
        
        for task in task_graph:
            print(f"\n  ┌─ 任务: {task['task_id']}")
            print(f"  │  类型: {task.get('task_type', 'N/A')}")
            print(f"  │  描述: {task.get('description', 'N/A')[:80]}...")
            print(f"  │")
            print(f"  │  输入变量: {task.get('input_variables', [])}")
            print(f"  │  输出变量: {task.get('output_variables', [])}")
            print(f"  │  依赖任务: {task.get('dependencies', [])}")
            print(f"  └─")
    
    # 5. 变量流分析
    print(f"\n【5. 变量流分析】")
    if 'task_graph' in blueprint:
        all_vars = set()
        for task in task_graph:
            all_vars.update(task.get('output_variables', []))
        print(f"  总变量数: {len(all_vars)}")
        print(f"  变量列表: {sorted(all_vars)}")
    
    # 6. 依赖关系可视化
    print(f"\n【6. 依赖关系图】")
    if 'task_graph' in blueprint:
        print("\n  执行顺序（拓扑排序）:")
        for i, task in enumerate(task_graph, 1):
            deps = task.get('dependencies', [])
            if deps:
                print(f"    {i}. {task['task_id']} (依赖: {', '.join(deps)})")
            else:
                print(f"    {i}. {task['task_id']} (起始节点)")
    
    print("\n" + "="*80)
    print("演示完成！")
    print("="*80)
    print(f"\n查看完整 JSON: {output_file}")
    
    return blueprint


def compare_legacy_vs_dag():
    """对比 Legacy 模式和 DAG 模式的输出"""
    print("\n" + "="*80)
    print("Legacy 模式 vs DAG 模式对比")
    print("="*80)
    
    llm = get_llm_client()
    logger = setup_logger("compare_modes")
    
    # 尝试连接 Neo4j
    neo4j = None
    try:
        neo4j = Neo4jConnector()
        print("✓ Neo4j 连接成功")
    except Exception as e:
        print(f"⚠️ Neo4j 连接失败: {e}")
    
    strategist = StrategistAgent(llm, neo4j_connector=neo4j, logger=logger)
    
    user_goal = "识别技术空白"
    available_columns = ['序号', '名称', '摘要']
    
    # Legacy 模式
    print("\n【Legacy 模式】")
    result_legacy = strategist.process({
        'user_goal': user_goal,
        'available_columns': available_columns,
        'use_dag': False
    })
    
    legacy_blueprint = result_legacy['blueprint']
    print(f"  输出字段: {list(legacy_blueprint.keys())}")
    if 'analysis_logic_chains' in legacy_blueprint:
        print(f"  步骤数: {len(legacy_blueprint['analysis_logic_chains'])}")
        print(f"  步骤结构示例:")
        if legacy_blueprint['analysis_logic_chains']:
            step = legacy_blueprint['analysis_logic_chains'][0]
            print(f"    - step_id: {step.get('step_id')}")
            print(f"    - objective: {step.get('objective', '')[:50]}...")
            print(f"    - method: {step.get('method')}")
            print(f"    - depends_on: {step.get('depends_on', [])}")
    
    # DAG 模式
    print("\n【DAG 模式】")
    result_dag = strategist.process({
        'user_goal': user_goal,
        'available_columns': available_columns,
        'use_dag': True
    })
    
    dag_blueprint = result_dag['blueprint']
    print(f"  输出字段: {list(dag_blueprint.keys())}")
    if 'task_graph' in dag_blueprint:
        print(f"  任务数: {len(dag_blueprint['task_graph'])}")
        print(f"  任务结构示例:")
        if dag_blueprint['task_graph']:
            task = dag_blueprint['task_graph'][0]
            print(f"    - task_id: {task.get('task_id')}")
            print(f"    - task_type: {task.get('task_type')}")
            print(f"    - input_variables: {task.get('input_variables', [])}")
            print(f"    - output_variables: {task.get('output_variables', [])}")
            print(f"    - dependencies: {task.get('dependencies', [])}")
    
    # 保存对比结果
    comparison = {
        'legacy_mode': legacy_blueprint,
        'dag_mode': dag_blueprint
    }
    
    output_file = 'outputs/strategist_v5_comparison.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 对比结果已保存到: {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Strategist V5.0 DAG 模式演示')
    parser.add_argument('--mode', choices=['dag', 'compare'], default='dag',
                        help='演示模式: dag=仅 DAG 模式, compare=对比两种模式')
    
    args = parser.parse_args()
    
    if args.mode == 'dag':
        demo_dag_mode()
    elif args.mode == 'compare':
        compare_legacy_vs_dag()
