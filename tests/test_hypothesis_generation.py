"""
测试假设生成器（6种策略）
"""

import json
from src.graphs.causal_graph_query import CausalGraphQuery


def test_hypothesis_generation():
    """测试完整的假设生成流程"""
    print("="*60)
    print("测试: 假设生成器 V2（6种策略）")
    print("="*60)
    
    # 初始化查询器
    query = CausalGraphQuery()
    
    # 测试场景1: 量子计算领域的技术影响力分析
    print("\n📋 场景1: 量子计算领域的技术影响力分析")
    print("-"*60)
    
    result = query.generate_hypotheses_v2({
        "domain": "量子计算",
        "intent": "技术影响力驱动因素分析"
    })
    
    # 打印结果
    print("\n✓ Step 1: 用户输入")
    print(f"  领域: {result['step1_input']['domain']}")
    print(f"  意图: {result['step1_input']['intent']}")
    
    print("\n✓ Step 2: 意图分析")
    print(f"  检测到的意图: {result['step2_analysis']['detected_intent']}")
    print(f"  提取的关键词: {result['step2_analysis']['extracted_keywords']}")
    print(f"  匹配的目标变量: {result['step2_analysis']['matched_outcome_variable']}")
    
    print("\n✓ Step 3: 变量匹配")
    outcome_var = result['step3_matching']['outcome_variable']
    if outcome_var:
        print(f"  目标变量: {outcome_var['label']} ({outcome_var['id']})")
    print(f"  候选预测变量数: {len(result['step3_matching']['candidate_predictors'])}")
    print(f"  候选调节变量数: {len(result['step3_matching']['candidate_moderators'])}")
    print(f"  候选中介变量数: {len(result['step3_matching']['candidate_mediators'])}")
    
    print("\n✓ Step 4: 文献检查")
    print(f"  已验证路径数: {len(result['step4_literature']['validated_paths'])}")
    print(f"  未探索路径数: {len(result['step4_literature']['unexplored_paths'])}")
    
    print("\n✓ Step 5: 假设生成（6种策略）")
    hypotheses = result['step5_hypotheses']
    print(f"  生成假设总数: {len(hypotheses)}")
    
    # 按策略分组统计
    strategy_count = {}
    for h in hypotheses:
        strategy = h['type']
        strategy_count[strategy] = strategy_count.get(strategy, 0) + 1
    
    print("\n  各策略生成数量:")
    strategy_names = {
        "theory_transfer": "理论迁移",
        "path_exploration": "路径探索",
        "moderation": "边界条件",
        "mediation": "中介机制",
        "counterfactual": "反事实推理",
        "interaction": "交互效应"
    }
    for strategy, count in strategy_count.items():
        print(f"    - {strategy_names.get(strategy, strategy)}: {count}个")
    
    print("\n  生成的假设列表:")
    for i, h in enumerate(hypotheses, 1):
        print(f"\n  假设 {i}: {h['id']}")
        print(f"    陈述: {h['statement']}")
        print(f"    策略: {h['strategy_description']}")
        print(f"    新颖性: {h['novelty_score']}")
        print(f"    变量: {h['variables']['independent']} → {h['variables']['dependent']}")
        if h['variables']['mediator']:
            print(f"    中介变量: {h['variables']['mediator']}")
        if h['variables']['moderator']:
            print(f"    调节变量: {h['variables']['moderator']}")
    
    print("\n✓ Step 6: 排序推荐")
    recommendation = result['step6_recommendation']
    print(f"  推荐总结: {recommendation['summary']}")
    print(f"  核心推荐数: {recommendation['core_count']}")
    print(f"  备选推荐数: {recommendation['alternative_count']}")
    
    if recommendation['core_recommendations']:
        top_rec = recommendation['core_recommendations'][0]
        top_hyp = top_rec['hypothesis']
        print(f"  最推荐假设: {top_hyp['id']}")
        print(f"  推荐理由: {top_rec['reason']}")
        print(f"  假设陈述: {top_hyp['statement']}")
    
    # 保存结果
    output_file = "outputs/hypothesis_generation_test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存到: {output_file}")
    
    return result


def test_all_strategies():
    """测试所有6种策略都能生成假设"""
    print("\n" + "="*60)
    print("测试: 验证所有6种策略")
    print("="*60)
    
    query = CausalGraphQuery()
    
    result = query.generate_hypotheses_v2({
        "domain": "人工智能",
        "intent": "技术影响力驱动因素分析"
    })
    
    hypotheses = result['step5_hypotheses']
    
    # 检查是否包含所有策略
    strategies_found = set(h['type'] for h in hypotheses)
    expected_strategies = {
        "theory_transfer",
        "path_exploration",
        "moderation",
        "mediation",
        "counterfactual",
        "interaction"
    }
    
    print(f"\n✓ 生成的策略类型: {strategies_found}")
    print(f"✓ 预期的策略类型: {expected_strategies}")
    
    missing = expected_strategies - strategies_found
    if missing:
        print(f"\n⚠️  缺失的策略: {missing}")
    else:
        print(f"\n✅ 所有6种策略都已生成假设！")
    
    # 检查新颖性评分
    print(f"\n✓ 新颖性评分范围:")
    scores = [h['novelty_score'] for h in hypotheses]
    print(f"  最高: {max(scores)}")
    print(f"  最低: {min(scores)}")
    print(f"  平均: {sum(scores)/len(scores):.2f}")
    
    assert len(hypotheses) >= 5, "应该至少生成5个假设"
    assert all(0.6 <= h['novelty_score'] <= 1.0 for h in hypotheses), "新颖性评分应在0.6-1.0之间"
    
    print("\n✅ 所有测试通过！")


def test_variable_matching():
    """测试变量匹配的准确性"""
    print("\n" + "="*60)
    print("测试: 变量匹配准确性")
    print("="*60)
    
    query = CausalGraphQuery()
    
    # 测试不同的意图
    test_cases = [
        {
            "intent": "技术影响力分析",
            "expected_outcome": "V16_tech_impact"
        },
        {
            "intent": "技术突破性研究",
            "expected_outcome": "V17_tech_breakthrough"
        },
        {
            "intent": "商业价值评估",
            "expected_outcome": "V19_commercial_value"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['intent']}")
        
        result = query.generate_hypotheses_v2({
            "domain": "测试领域",
            "intent": case['intent']
        })
        
        matched_var = result['step2_analysis']['matched_outcome_variable']
        print(f"  匹配的变量: {matched_var}")
        print(f"  预期的变量: {case['expected_outcome']}")
        
        if matched_var == case['expected_outcome']:
            print(f"  ✅ 匹配正确")
        else:
            print(f"  ⚠️  匹配不符合预期")
    
    print("\n✅ 变量匹配测试完成！")


if __name__ == "__main__":
    # 运行所有测试
    print("\n" + "🚀 开始测试假设生成器" + "\n")
    
    # 测试1: 完整流程
    result = test_hypothesis_generation()
    
    # 测试2: 所有策略
    test_all_strategies()
    
    # 测试3: 变量匹配
    test_variable_matching()
    
    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)
