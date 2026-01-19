#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理因果图谱 - 移除包含unmapped变量的路径
"""

import json
import shutil
from datetime import datetime

def clean_causal_graph():
    """清理因果图谱"""
    
    print("=" * 80)
    print("因果图谱清理工具")
    print("=" * 80)
    
    # 加载原始图谱
    input_file = "sandbox/static/data/causal_ontology_extracted.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    
    print(f"\n加载原始图谱: {input_file}")
    
    # 备份原始文件
    backup_file = f"sandbox/static/data/causal_ontology_extracted_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(input_file, backup_file)
    print(f"✓ 已备份到: {backup_file}")
    
    # 获取标准变量ID
    standard_vars = {v['id'] for v in graph.get('variables', [])}
    print(f"\n标准变量数: {len(standard_vars)}")
    
    # 统计原始数据
    original_paths = graph.get('causal_paths', [])
    print(f"原始路径数: {len(original_paths)}")
    
    # 过滤路径：只保留source和target都是标准变量的路径
    valid_paths = []
    removed_paths = []
    
    for path in original_paths:
        source = path.get('source')
        target = path.get('target')
        
        if source in standard_vars and target in standard_vars:
            valid_paths.append(path)
        else:
            removed_paths.append({
                'path': f"{source} → {target}",
                'reason': []
            })
            if source not in standard_vars:
                removed_paths[-1]['reason'].append(f"source={source}")
            if target not in standard_vars:
                removed_paths[-1]['reason'].append(f"target={target}")
    
    print(f"\n清理结果:")
    print(f"  保留路径: {len(valid_paths)}")
    print(f"  移除路径: {len(removed_paths)}")
    print(f"  保留率: {len(valid_paths)/len(original_paths)*100:.1f}%")
    
    # 显示部分移除的路径
    if removed_paths:
        print(f"\n移除的路径示例（前10条）:")
        for i, item in enumerate(removed_paths[:10], 1):
            print(f"  {i}. {item['path']}")
            print(f"     原因: {', '.join(item['reason'])}")
    
    # 更新图谱
    graph['causal_paths'] = valid_paths
    graph['meta']['total_paths'] = len(valid_paths)
    graph['meta']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    # 添加清理记录
    if 'cleaning_history' not in graph['meta']:
        graph['meta']['cleaning_history'] = []
    
    graph['meta']['cleaning_history'].append({
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'action': 'remove_unmapped_paths',
        'original_paths': len(original_paths),
        'cleaned_paths': len(valid_paths),
        'removed_paths': len(removed_paths)
    })
    
    # 保存清理后的图谱
    output_file = input_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 清理后的图谱已保存到: {output_file}")
    
    # 验证清理结果
    print("\n" + "=" * 80)
    print("验证清理结果")
    print("=" * 80)
    
    # 检查是否还有unmapped变量
    path_vars = set()
    for path in valid_paths:
        path_vars.add(path.get('source'))
        path_vars.add(path.get('target'))
    
    unmapped_vars = {v for v in path_vars if v.startswith('unmapped_')}
    
    if unmapped_vars:
        print(f"⚠️ 警告: 仍有 {len(unmapped_vars)} 个unmapped变量")
        for var in sorted(unmapped_vars):
            print(f"  - {var}")
    else:
        print(f"✓ 所有路径都只使用标准变量")
    
    print(f"\n最终统计:")
    print(f"  标准变量: {len(standard_vars)}")
    print(f"  路径中使用的变量: {len(path_vars)}")
    print(f"  有效路径: {len(valid_paths)}")
    
    print("\n" + "=" * 80)
    print("清理完成！")
    print("=" * 80)
    
    return len(valid_paths), len(removed_paths)


if __name__ == "__main__":
    valid, removed = clean_causal_graph()
    print(f"\n总结: 保留{valid}条路径，移除{removed}条路径")
