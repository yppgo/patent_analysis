#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目清理脚本
删除无关的测试文件和临时文件
"""

import os
import shutil

# 要删除的临时测试文件（根目录）
temp_test_files = [
    "check_actual_scores.py",
    "check_causal_graph_variables.py",
    "check_data_fields.py",
    "check_graph_structure.py",
    "check_intent_workflow.py",
    "debug_quality_calculation.py",
    "test_all_mediation_paths.py",
    "test_mediation_paths.py",
    "test_mediation_quality.py",
    "test_quality_scoring_explanation.py",
    "test_recommendation_strategies.py",
    "test_prompt_loading.py",
    "test_neo4j_simple.py",
    "test_method_graph_query.py",
    "test_method_graph_usability.py",
    "test_method_extraction.py",
    "test_graph_compatibility.py",
]

# 要保留的核心测试文件
keep_test_files = [
    "test_hypothesis_generation.py",  # 核心：假设生成测试
    "test_layered_recommendation.py",  # 核心：分层推荐测试
    "test_dual_graph_integration.py",  # 核心：双图谱集成测试
    "test_strategist_with_dual_graphs.py",  # 核心：Strategist测试
    "test_full_system_with_real_data.py",  # 核心：完整系统测试
]

# 要删除的旧文档
old_docs = [
    "docs/PROMPT_FIX_SUMMARY.md",  # 临时文档
]

def cleanup():
    """执行清理"""
    deleted_count = 0
    
    print("=" * 60)
    print("项目清理脚本")
    print("=" * 60)
    
    # 删除临时测试文件
    print("\n1. 清理临时测试文件...")
    for file in temp_test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✓ 删除: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")
        else:
            print(f"  - 不存在: {file}")
    
    # 删除旧文档
    print("\n2. 清理旧文档...")
    for file in old_docs:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✓ 删除: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败: {file} - {e}")
    
    # 显示保留的核心测试文件
    print("\n3. 保留的核心测试文件:")
    for file in keep_test_files:
        if os.path.exists(file):
            print(f"  ✓ 保留: {file}")
        else:
            print(f"  ⚠ 不存在: {file}")
    
    print("\n" + "=" * 60)
    print(f"清理完成！共删除 {deleted_count} 个文件")
    print("=" * 60)
    
    # 显示当前测试文件列表
    print("\n当前测试文件列表:")
    test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
    for f in sorted(test_files):
        status = "✓ 核心" if f in keep_test_files else "  其他"
        print(f"  {status}: {f}")

if __name__ == "__main__":
    cleanup()
