#!/usr/bin/env python3
"""测试因果本体论数据加载"""
import json
from pathlib import Path

# 加载数据
data_file = Path(__file__).parent / "static/data/complete_causal_ontology.json"

print(f"📂 加载文件: {data_file}")
print(f"📍 文件存在: {data_file.exists()}")

if data_file.exists():
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✅ 数据加载成功!")
    print(f"\n📊 统计信息:")
    print(f"  - 变量总数: {len(data['variables'])}")
    print(f"  - 因果路径: {len(data['causal_paths'])}")
    print(f"  - 版本: {data['meta']['version']}")
    
    print(f"\n📋 变量分类:")
    categories = {}
    for var in data['variables']:
        cat = var['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        print(f"  - {cat}: {count}个")
    
    print(f"\n🔗 路径类型:")
    validated = sum(1 for p in data['causal_paths'] if p.get('evidence', {}).get('validated', False))
    exploratory = len(data['causal_paths']) - validated
    print(f"  - 已验证: {validated}条")
    print(f"  - 探索性: {exploratory}条")
    
    print(f"\n🎯 示例变量:")
    for var in data['variables'][:3]:
        print(f"  - {var['id']}: {var['label']} ({var['category']})")
    
    print(f"\n🔗 示例路径:")
    for path in data['causal_paths'][:3]:
        source = next(v for v in data['variables'] if v['id'] == path['source'])
        target = next(v for v in data['variables'] if v['id'] == path['target'])
        print(f"  - {source['label']} → {target['label']} ({path['effect_type']})")
    
    print(f"\n✅ 所有测试通过!")
else:
    print(f"\n❌ 文件不存在!")
