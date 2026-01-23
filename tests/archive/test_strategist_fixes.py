#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Strategist的修复效果
验证3个问题是否得到解决：
1. V09计算方法是否正确（Shannon熵或IPC大类数量）
2. 控制变量是否增加到2-3个
3. 输出是否包含effect_size和mediation_ratio
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.strategist import StrategistAgent
from src.graphs.causal_graph_query import CausalGraphQuery
from src.graphs.method_graph_query import MethodGraphQuery
from anthropic import Anthropic
import os


def test_strategist_fixes():
    """测试Strategist的修复效果"""
    
    print("=" * 80)
    print("测试Strategist修复效果")
    print("=" * 80)
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    llm_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    causal_graph = CausalGraphQuery()
    method_graph = MethodGraphQuery()
    
    strategist = StrategistAgent(
        llm_client=llm_client,
        causal_graph=causal_graph,
        method_graph=method_graph
    )
    print("✓ 组件初始化完成")
    
    # 2. 生成蓝图
    print("\n2. 生成蓝图...")
    user_input = {
        "user_goal": "分析量子计算领域中技术影响力的关键驱动因素",
        "use_dag": True
    }
    
    result = strategist.process(user_input)
    blueprint = result['blueprint']
    
    print("✓ 蓝图生成完成")
    
    # 3. 评审修复效果
    print("\n" + "=" * 80)
    print("修复效果评审")
    print("=" * 80)
    
    issues = []
    score = 0
    max_score = 0
    
    # 检查1：V09计算方法
    print("\n【检查1】V09_tech_diversity的计算方法")
    max_score += 30
    
    task_1 = blueprint['task_graph'][0]
    v09_config = None
    for var in task_1['implementation_config'].get('variables_to_calculate', []):
        if var['variable_id'] == 'V09_tech_diversity':
            v09_config = var
            break
    
    if v09_config:
        formula = v09_config.get('formula', '')
        method = v09_config.get('calculation_method', '')
        
        print(f"  计算方法: {method}")
        print(f"  公式: {formula}")
        
        # 检查是否使用了Shannon熵或IPC大类数量
        if 'entropy' in formula.lower() or 'shannon' in method.lower():
            print("  ✅ 使用Shannon熵（最佳方案）")
            score += 30
        elif 'count' in formula.lower() and 'distinct' in formula.lower():
            print("  ✅ 使用IPC大类数量（备选方案）")
            score += 25
        elif '.str[0]' in formula and 'categorical' not in formula.lower():
            print("  ❌ 仍然只提取IPC首字母（问题未修复）")
            issues.append("V09仍然使用IPC首字母提取，而不是Shannon熵")
            score += 0
        else:
            print(f"  ⚠️ 使用了其他方法: {formula}")
            score += 15
    else:
        print("  ❌ 未找到V09的配置")
        issues.append("未找到V09的配置")
    
    # 检查2：控制变量数量
    print("\n【检查2】控制变量数量")
    max_score += 30
    
    # 查找假设检验任务
    hypothesis_task = None
    for task in blueprint['task_graph']:
        if task['task_type'] in ['hypothesis_test', 'mediation_analysis']:
            hypothesis_task = task
            break
    
    if hypothesis_task:
        control_vars = hypothesis_task['implementation_config'].get('control_vars', [])
        print(f"  控制变量: {control_vars}")
        print(f"  数量: {len(control_vars)}")
        
        if len(control_vars) >= 2:
            print("  ✅ 控制变量数量充足（≥2个）")
            score += 30
        elif len(control_vars) == 1:
            print("  ⚠️ 控制变量较少（1个）")
            score += 15
        else:
            print("  ❌ 没有控制变量")
            issues.append("缺少控制变量")
            score += 0
    else:
        print("  ⚠️ 未找到假设检验任务")
        score += 0
    
    # 检查3：效应量和中介比例
    print("\n【检查3】输出是否包含effect_size和mediation_ratio")
    max_score += 40
    
    if hypothesis_task:
        output_content = hypothesis_task['implementation_config'].get('output_content', {})
        
        # 检查effect_size
        has_effect_size = False
        if 'effect_size' in str(output_content):
            has_effect_size = True
            print("  ✅ 包含effect_size字段")
            score += 20
        else:
            print("  ❌ 缺少effect_size字段")
            issues.append("输出缺少effect_size字段")
        
        # 检查mediation_ratio（如果是中介分析）
        has_mediation_ratio = False
        if hypothesis_task['task_type'] == 'mediation_analysis' or 'mediation' in hypothesis_task.get('description', '').lower():
            if 'mediation_ratio' in str(output_content):
                has_mediation_ratio = True
                print("  ✅ 包含mediation_ratio字段")
                score += 20
            else:
                print("  ❌ 缺少mediation_ratio字段")
                issues.append("中介分析输出缺少mediation_ratio字段")
        else:
            print("  ⚠️ 不是中介分析任务，跳过mediation_ratio检查")
            score += 20  # 不扣分
    else:
        print("  ❌ 未找到假设检验任务")
    
    # 4. 总结
    print("\n" + "=" * 80)
    print("评审总结")
    print("=" * 80)
    
    percentage = (score / max_score) * 100
    print(f"\n总分: {score}/{max_score} ({percentage:.1f}%)")
    
    if percentage >= 90:
        grade = "优秀 ⭐⭐⭐⭐⭐"
    elif percentage >= 80:
        grade = "良好 ⭐⭐⭐⭐"
    elif percentage >= 70:
        grade = "中等 ⭐⭐⭐"
    elif percentage >= 60:
        grade = "及格 ⭐⭐"
    else:
        grade = "不及格 ⭐"
    
    print(f"评级: {grade}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✅ 所有问题已修复！")
    
    # 5. 保存结果
    output_file = "outputs/strategist_fixes_test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'score': score,
            'max_score': max_score,
            'percentage': percentage,
            'grade': grade,
            'issues': issues,
            'blueprint': blueprint
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {output_file}")
    
    return percentage >= 90


if __name__ == "__main__":
    success = test_strategist_fixes()
    sys.exit(0 if success else 1)
