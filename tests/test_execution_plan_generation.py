"""
测试 Execution Plan 生成功能

验证 Methodologist 能否正确生成执行计划
"""

import json
import sys
from pathlib import Path

# 直接导入需要的模块，避免 neo4j 导入问题
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from typing import Dict, Any, List


def test_execution_plan_generation():
    """测试执行计划生成"""
    
    print("=" * 80)
    print("测试：Execution Plan 生成")
    print("=" * 80)
    
    # 1. 加载测试数据
    print("\n[步骤 1] 加载测试数据")
    
    # 加载 Strategist 生成的蓝图
    blueprint_file = Path("outputs/e2e_test_blueprint.json")
    if not blueprint_file.exists():
        print(f"❌ 蓝图文件不存在: {blueprint_file}")
        return
    
    with open(blueprint_file, 'r', encoding='utf-8') as f:
        blueprint_data = json.load(f)
    
    task_graph = blueprint_data['blueprint']['task_graph']
    print(f"✅ 加载蓝图成功，包含 {len(task_graph)} 个任务")
    
    # 加载 Methodologist 生成的技术规格
    task_1_spec_file = Path("outputs/e2e_test_task_1_spec.json")
    task_2_spec_file = Path("outputs/e2e_test_task_2_spec.json")
    
    if not task_1_spec_file.exists() or not task_2_spec_file.exists():
        print(f"❌ 技术规格文件不存在")
        return
    
    with open(task_1_spec_file, 'r', encoding='utf-8') as f:
        task_1_data = json.load(f)
    
    with open(task_2_spec_file, 'r', encoding='utf-8') as f:
        task_2_data = json.load(f)
    
    technical_specs = [
        task_1_data['technical_spec'],
        task_2_data['technical_spec']
    ]
    
    print(f"✅ 加载技术规格成功，共 {len(technical_specs)} 个")
    
    # 2. 创建一个简化的 Methodologist 实例（不需要 LLM）
    print("\n[步骤 2] 创建 Methodologist 实例")
    
    # 直接导入 Methodologist 类定义
    import importlib.util
    spec = importlib.util.spec_from_file_location("methodologist", "src/agents/methodologist.py")
    methodologist_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(methodologist_module)
    
    # 创建一个 mock LLM client（不会被使用）
    class MockLLM:
        def invoke(self, prompt):
            return ""
    
    methodologist = methodologist_module.MethodologistAgent(MockLLM())
    print("✅ Methodologist 实例创建完成")
    
    # 3. 生成执行计划
    print("\n[步骤 3] 生成执行计划")
    execution_plan = methodologist.generate_execution_plan(task_graph, technical_specs)
    
    # 4. 验证执行计划结构
    print("\n[步骤 4] 验证执行计划结构")
    
    required_keys = ['metadata', 'execution_order', 'data_flow_graph', 'tasks', 'validation_rules']
    missing_keys = [key for key in required_keys if key not in execution_plan]
    
    if missing_keys:
        print(f"❌ 执行计划缺少必要字段: {missing_keys}")
        return
    
    print("✅ 执行计划包含所有必要字段")
    
    # 5. 打印执行计划摘要
    print("\n[步骤 5] 执行计划摘要")
    print(f"  - 计划版本: {execution_plan['metadata']['plan_version']}")
    print(f"  - 任务总数: {execution_plan['metadata']['total_tasks']}")
    print(f"  - 生成时间: {execution_plan['metadata']['generated_at']}")
    print(f"  - 执行顺序: {execution_plan['execution_order']}")
    print(f"  - 数据流节点数: {len(execution_plan['data_flow_graph']['nodes'])}")
    print(f"  - 数据流边数: {len(execution_plan['data_flow_graph']['edges'])}")
    print(f"  - 验证规则数: {len(execution_plan['validation_rules'])}")
    
    # 6. 打印详细信息
    print("\n[步骤 6] 执行计划详细信息")
    
    print("\n📋 执行顺序:")
    for i, task_id in enumerate(execution_plan['execution_order'], 1):
        print(f"  {i}. {task_id}")
    
    print("\n📊 数据流图:")
    for node in execution_plan['data_flow_graph']['nodes']:
        print(f"  - {node['task_id']}:")
        print(f"    输入: {node['input_files']}")
        print(f"    输出: {node['output_files']}")
    
    print("\n🔗 数据依赖:")
    for edge in execution_plan['data_flow_graph']['edges']:
        print(f"  - {edge['from']} → {edge['to']}: {edge['data']}")
    
    print("\n✅ 验证规则:")
    for task_id, rules in execution_plan['validation_rules'].items():
        print(f"  - {task_id}:")
        print(f"    必须存在的文件: {rules['output_files_must_exist']}")
        print(f"    输出契约: {len(rules['output_contract'])} 条")
        print(f"    错误处理: {len(rules['error_handling'])} 条")
    
    # 7. 保存执行计划
    print("\n[步骤 7] 保存执行计划")
    output_file = Path("outputs/execution_plan.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(execution_plan, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 执行计划已保存: {output_file}")
    
    # 8. 评估执行计划质量
    print("\n[步骤 8] 评估执行计划质量")
    
    quality_score = 100
    issues = []
    
    # 检查执行顺序是否合理
    if len(execution_plan['execution_order']) != len(task_graph):
        issues.append("执行顺序中的任务数量与任务图不匹配")
        quality_score -= 20
    
    # 检查数据流图是否完整
    if len(execution_plan['data_flow_graph']['nodes']) != len(task_graph):
        issues.append("数据流图节点数量与任务图不匹配")
        quality_score -= 20
    
    # 检查验证规则是否完整
    if len(execution_plan['validation_rules']) != len(task_graph):
        issues.append("验证规则数量与任务图不匹配")
        quality_score -= 20
    
    # 检查任务列表是否包含技术规格
    for task in execution_plan['tasks']:
        if 'technical_spec' not in task:
            issues.append(f"任务 {task['task_id']} 缺少技术规格")
            quality_score -= 10
    
    print(f"\n📊 执行计划质量评分: {quality_score}/100")
    
    if issues:
        print("\n⚠️ 发现的问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 执行计划质量优秀，无问题")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
    return execution_plan, quality_score


if __name__ == "__main__":
    execution_plan, quality_score = test_execution_plan_generation()
    
    if quality_score >= 90:
        print("\n🎉 测试通过！执行计划生成功能正常工作")
    elif quality_score >= 70:
        print("\n⚠️ 测试部分通过，执行计划需要改进")
    else:
        print("\n❌ 测试失败，执行计划存在严重问题")
