#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Methodologist Agent 处理 Strategist 生成的真实蓝图

目标：
1. 验证Methodologist能否正确处理Strategist生成的DAG任务节点
2. 识别类别中介变量的处理问题
3. 评估技术规格质量
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

# 导入Methodologist
from src.agents.methodologist import MethodologistAgent


def load_strategist_blueprint():
    """加载Strategist生成的蓝图"""
    blueprint_file = "outputs/strategist_dual_graph_test_result.json"
    
    if not os.path.exists(blueprint_file):
        raise FileNotFoundError(f"蓝图文件不存在: {blueprint_file}")
    
    with open(blueprint_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_task_1_variable_calculation():
    """测试Task 1：变量计算"""
    print("=" * 80)
    print("测试 Task 1: 变量计算")
    print("=" * 80)
    
    # 加载蓝图
    blueprint = load_strategist_blueprint()
    task_graph = blueprint['blueprint']['task_graph']
    task_1 = task_graph[0]
    
    print(f"\n📋 任务信息:")
    print(f"  Task ID: {task_1['task_id']}")
    print(f"  Task Type: {task_1['task_type']}")
    print(f"  Question: {task_1['question']}")
    print(f"  输入变量: {task_1['input_variables']}")
    print(f"  输出变量: {task_1['output_variables']}")
    
    # 初始化Methodologist
    llm = get_llm_client()
    methodologist = MethodologistAgent(llm)
    
    # 处理任务
    print(f"\n🔧 Methodologist处理中...")
    result = methodologist.process({'task_node': task_1})
    
    # 验证结果
    print(f"\n✓ 验证技术规格")
    spec = result['technical_spec']
    
    # 检查必要字段
    required_fields = ['function_name', 'function_signature', 'logic_flow', 'required_libraries']
    for field in required_fields:
        if field in spec:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    # 检查是否识别类别变量
    spec_str = json.dumps(spec, ensure_ascii=False)
    if '类别' in spec_str or 'categorical' in spec_str.lower() or 'category' in spec_str.lower():
        print(f"  ✅ 识别了类别变量")
    else:
        print(f"  ⚠️  未明确识别类别变量")
    
    # 检查V09处理
    if 'V09' in spec_str:
        print(f"  ✅ 提到了V09变量")
    else:
        print(f"  ⚠️  未提到V09变量")
    
    # 打印逻辑流程
    print(f"\n📝 逻辑流程:")
    for i, step in enumerate(spec.get('logic_flow', []), 1):
        print(f"  {i}. {step}")
    
    # 打印所需库
    print(f"\n📦 所需库: {spec.get('required_libraries', [])}")
    
    # 保存结果
    output_file = "outputs/methodologist_task_1_spec.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 技术规格已保存到: {output_file}")
    
    return result


def test_task_2_mediation_analysis():
    """测试Task 2：中介分析"""
    print("\n" + "=" * 80)
    print("测试 Task 2: 中介分析")
    print("=" * 80)
    
    # 加载蓝图
    blueprint = load_strategist_blueprint()
    task_graph = blueprint['blueprint']['task_graph']
    task_2 = task_graph[1]
    
    print(f"\n📋 任务信息:")
    print(f"  Task ID: {task_2['task_id']}")
    print(f"  Task Type: {task_2['task_type']}")
    print(f"  Question: {task_2['question']}")
    print(f"  输入变量: {task_2['input_variables']}")
    print(f"  输出变量: {task_2['output_variables']}")
    print(f"  依赖: {task_2['dependencies']}")
    
    # 提取中介分析配置
    config = task_2['implementation_config']
    print(f"\n🔍 中介分析配置:")
    print(f"  算法: {config['algorithm']}")
    print(f"  自变量: {config['independent_var']}")
    print(f"  中介变量: {config['mediator_var']}")
    print(f"  因变量: {config['dependent_var']}")
    print(f"  控制变量: {config['control_vars']}")
    
    # 初始化Methodologist
    llm = get_llm_client()
    methodologist = MethodologistAgent(llm)
    
    # 处理任务
    print(f"\n🔧 Methodologist处理中...")
    result = methodologist.process({'task_node': task_2})
    
    # 验证结果
    print(f"\n✓ 验证技术规格")
    spec = result['technical_spec']
    
    # 检查必要字段
    required_fields = ['function_name', 'function_signature', 'logic_flow', 'required_libraries']
    for field in required_fields:
        if field in spec:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    # 检查中介分析关键点
    spec_str = json.dumps(spec, ensure_ascii=False)
    
    print(f"\n🔍 中介分析关键检查:")
    
    # 1. 是否识别V09是类别变量
    if '类别' in spec_str or 'categorical' in spec_str.lower():
        print(f"  ✅ 识别V09是类别变量")
    else:
        print(f"  ⚠️  未明确识别V09是类别变量")
    
    # 2. 是否提到虚拟变量编码
    if '虚拟变量' in spec_str or 'dummy' in spec_str.lower() or 'get_dummies' in spec_str:
        print(f"  ✅ 提到虚拟变量编码")
    else:
        print(f"  ⚠️  未提到虚拟变量编码")
    
    # 3. 是否提到多项回归或逻辑回归
    if '多项' in spec_str or 'multinomial' in spec_str.lower() or '逻辑回归' in spec_str or 'logistic' in spec_str.lower():
        print(f"  ✅ 提到多项/逻辑回归（a路径）")
    else:
        print(f"  ⚠️  未提到多项/逻辑回归")
    
    # 4. 是否提到Bootstrap
    if 'bootstrap' in spec_str.lower():
        print(f"  ✅ 提到Bootstrap方法")
    else:
        print(f"  ⚠️  未提到Bootstrap方法")
    
    # 5. 是否提到中介效应
    if '中介' in spec_str or 'mediation' in spec_str.lower():
        print(f"  ✅ 提到中介效应")
    else:
        print(f"  ⚠️  未提到中介效应")
    
    # 打印逻辑流程
    print(f"\n📝 逻辑流程:")
    for i, step in enumerate(spec.get('logic_flow', []), 1):
        print(f"  {i}. {step}")
    
    # 打印所需库
    print(f"\n📦 所需库: {spec.get('required_libraries', [])}")
    
    # 保存结果
    output_file = "outputs/methodologist_task_2_spec.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 技术规格已保存到: {output_file}")
    
    return result


def evaluate_spec_quality(spec: dict) -> dict:
    """评估技术规格质量"""
    print("\n" + "=" * 80)
    print("技术规格质量评估")
    print("=" * 80)
    
    score = 0
    max_score = 100
    issues = []
    
    # 1. 完整性检查（30分）
    required_fields = ['function_name', 'function_signature', 'logic_flow', 'required_libraries']
    completeness_score = 0
    for field in required_fields:
        if field in spec:
            completeness_score += 7.5
        else:
            issues.append(f"缺少字段: {field}")
    score += completeness_score
    print(f"\n1. 完整性: {completeness_score}/30")
    
    # 2. 逻辑流程质量（30分）
    logic_flow = spec.get('logic_flow', [])
    if len(logic_flow) >= 5:
        logic_score = 30
    elif len(logic_flow) >= 3:
        logic_score = 20
    else:
        logic_score = 10
        issues.append(f"逻辑流程步骤太少: {len(logic_flow)}")
    score += logic_score
    print(f"2. 逻辑流程: {logic_score}/30 ({len(logic_flow)}步)")
    
    # 3. 输入输出契约（20分）
    contract_score = 0
    if 'input_contract' in spec:
        contract_score += 10
    else:
        issues.append("缺少输入契约")
    
    if 'output_contract' in spec:
        contract_score += 10
    else:
        issues.append("缺少输出契约")
    score += contract_score
    print(f"3. 输入输出契约: {contract_score}/20")
    
    # 4. 错误处理（10分）
    if 'error_handling' in spec:
        error_score = 10
    else:
        error_score = 0
        issues.append("缺少错误处理")
    score += error_score
    print(f"4. 错误处理: {error_score}/10")
    
    # 5. 文档质量（10分）
    if 'docstring' in spec and len(spec.get('docstring', '')) > 50:
        doc_score = 10
    else:
        doc_score = 5
        issues.append("文档字符串不够详细")
    score += doc_score
    print(f"5. 文档质量: {doc_score}/10")
    
    print(f"\n总分: {score}/{max_score} ({score/max_score*100:.1f}%)")
    
    if issues:
        print(f"\n⚠️  发现的问题:")
        for issue in issues:
            print(f"  - {issue}")
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': score / max_score * 100,
        'issues': issues
    }


def main():
    """主测试流程"""
    print("\n" + "🚀 开始测试 Methodologist Agent 处理 Strategist 蓝图" + "\n")
    
    try:
        # 测试Task 1
        result_1 = test_task_1_variable_calculation()
        quality_1 = evaluate_spec_quality(result_1['technical_spec'])
        
        # 测试Task 2
        result_2 = test_task_2_mediation_analysis()
        quality_2 = evaluate_spec_quality(result_2['technical_spec'])
        
        # 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        avg_quality = (quality_1['percentage'] + quality_2['percentage']) / 2
        print(f"\nTask 1 质量: {quality_1['percentage']:.1f}%")
        print(f"Task 2 质量: {quality_2['percentage']:.1f}%")
        print(f"平均质量: {avg_quality:.1f}%")
        
        if avg_quality >= 90:
            print(f"\n✅ 技术规格质量优秀（>= 90%）")
        elif avg_quality >= 80:
            print(f"\n⚠️  技术规格质量良好（80-90%），需要小幅优化")
        else:
            print(f"\n❌ 技术规格质量不足（< 80%），需要优化Prompt")
        
        # 识别需要优化的地方
        print(f"\n📋 需要优化的地方:")
        all_issues = quality_1['issues'] + quality_2['issues']
        if all_issues:
            for issue in set(all_issues):
                print(f"  - {issue}")
        else:
            print(f"  无明显问题")
        
        print("\n" + "=" * 80)
        print("🎉 测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
