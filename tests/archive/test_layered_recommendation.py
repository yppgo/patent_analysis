"""测试分层推荐系统"""
from src.graphs.causal_graph_query import CausalGraphQuery
import json

query = CausalGraphQuery()

# 生成假设
result = query.generate_hypotheses_v2({
    "domain": "量子计算",
    "intent": "技术影响力驱动因素分析"
})

print("="*80)
print("分层推荐系统测试")
print("="*80)

# Step 5: 假设生成统计
hypotheses = result['step5_hypotheses']
print(f"\n📊 Step 5: 假设生成")
print(f"  总假设数: {len(hypotheses)}")

type_count = {}
for h in hypotheses:
    h_type = h['type']
    type_count[h_type] = type_count.get(h_type, 0) + 1

print(f"  策略分布:")
for h_type, count in type_count.items():
    print(f"    - {h_type}: {count}个")

# Step 6: 分层推荐
recommendation = result['step6_recommendation']

print(f"\n" + "="*80)
print("🎯 Step 6: 分层推荐结果")
print("="*80)

print(f"\n总结: {recommendation['summary']}")
print(f"  - 核心推荐: {recommendation['core_count']}个")
print(f"  - 备选推荐: {recommendation['alternative_count']}个")
print(f"  - 总假设数: {recommendation['total_count']}个")

# 核心推荐（3个）
print(f"\n" + "="*80)
print("⭐ 核心推荐（必选，3个）")
print("="*80)

for rec in recommendation['core_recommendations']:
    h = rec['hypothesis']
    eval_data = h['evaluation']
    
    print(f"\n{rec['rank']}. {h['id']}: {h['statement']}")
    print(f"   推荐理由: {rec['reason']}")
    print(f"   推荐类型: {rec['recommendation_type']}")
    print(f"   评分:")
    print(f"     - 综合分: {eval_data['balanced_score']:.3f}")
    print(f"     - 新颖性: {eval_data['novelty_score']}")
    print(f"     - 质量: {eval_data['quality_score']:.1f}")
    print(f"   策略: {h['type']}")
    print(f"   路径: {h['theoretical_basis']}")

# 备选推荐
if recommendation['alternative_recommendations']:
    print(f"\n" + "="*80)
    print("💡 备选推荐（可选）")
    print("="*80)
    
    for i, rec in enumerate(recommendation['alternative_recommendations'], 1):
        h = rec['hypothesis']
        eval_data = h['evaluation']
        
        print(f"\n{i}. {h['id']}: {h['statement']}")
        print(f"   推荐理由: {rec['reason']}")
        print(f"   评分: 综合{eval_data['balanced_score']:.3f} | 新颖性{eval_data['novelty_score']} | 质量{eval_data['quality_score']:.1f}")

# 使用建议
print(f"\n" + "="*80)
print("📝 使用建议")
print("="*80)

print("""
1. 毕业论文/项目验收
   → 选择核心推荐的前2个（综合分最高 + 质量最高）
   → 确保能完成，降低风险

2. 学术论文发表
   → 选择核心推荐的全部3个
   → 既有创新又有保障

3. 探索性研究
   → 核心推荐3个 + 备选1-2个
   → 追求突破性发现
""")

# 保存结果
output_file = "outputs/layered_recommendation_result.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n💾 完整结果已保存到: {output_file}")
print("\n✅ 分层推荐系统测试完成！")
