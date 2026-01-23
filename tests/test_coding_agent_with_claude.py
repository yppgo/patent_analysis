#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Coding Agent V4.2 使用 Claude 作为基模
"""

import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.utils.llm_client import ClaudeLLMClient
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def test_coding_agent_with_claude():
    """使用 Claude 测试 Coding Agent V4.2"""
    print("\n" + "=" * 80)
    print("🚀 Coding Agent V4.2 测试（Claude 基模）")
    print("=" * 80)
    
    # 加载已保存的文件
    print("\n📦 加载已保存的文件...")
    
    spec_file = "outputs/e2e_test_task_2_spec.json"
    
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec_result = json.load(f)
    print(f"  ✅ 技术规格加载成功")
    
    # 加载 Task 1 的结果作为输入
    variables_file = "outputs/task_1_variables.csv"
    variables_df = pd.read_csv(variables_file)
    print(f"  ✅ 变量数据加载成功: {variables_df.shape}")
    
    # 初始化 Claude 客户端（通过聚合 AI 代理）
    print("\n📦 初始化 Claude LLM 客户端（通过代理）...")
    try:
        claude_llm = ClaudeLLMClient.from_env(
            model="claude-sonnet-4-20250514",
            temperature=0.3,
            use_proxy=True  # 使用聚合 AI 代理
        )
        print(f"  ✅ Claude 客户端初始化成功 (provider: {claude_llm.provider})")
    except Exception as e:
        print(f"  ❌ Claude 初始化失败: {e}")
        print("  请确保已设置 JUHENEXT_API_KEY 环境变量")
        return
    
    # 初始化 Coding Agent V4.2
    print("\n📦 初始化 Coding Agent V4.2 (Claude)...")
    coding_agent = CodingAgentV4_2(
        llm_client=claude_llm, 
        max_iterations=10  # Claude 应该需要更少的迭代
    )
    print("  ✅ Coding Agent V4.2 初始化成功")
    
    # 准备任务
    task = {
        'task_id': 'task_2',
        'question': '假设1（技术成熟度通过技术跨界度中介影响技术影响力）是否成立？'
    }
    
    # 执行任务
    print("\n" + "=" * 80)
    print("🔧 执行假设检验任务")
    print("=" * 80)
    print(f"  函数名: {spec_result['technical_spec']['function_name']}")
    print(f"  问题: {task['question'][:60]}...")
    
    # 准备输入
    coding_input = {
        'execution_spec': spec_result['technical_spec'],
        'current_step': task,
        'test_data': variables_df,
        'previous_result': None
    }
    
    start_time = time.time()
    try:
        result = coding_agent.process(coding_input)
        elapsed = time.time() - start_time
        
        is_valid = result.get('is_code_valid', False)
        iteration_count = result.get('iteration_count', 0)
        runtime_error = result.get('runtime_error', '')
        
        print(f"\n{'='*60}")
        if is_valid:
            print(f"✅ 成功！(耗时: {elapsed:.1f}s, 迭代: {iteration_count}次)")
        else:
            print(f"❌ 失败 (耗时: {elapsed:.1f}s, 迭代: {iteration_count}次)")
            if runtime_error:
                print(f"   错误: {runtime_error[:200]}...")
        
        # 保存生成的代码
        if result.get('generated_code'):
            code_file = "outputs/coding_claude_task_2.py"
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(result['generated_code'])
            print(f"  💾 代码已保存: {code_file}")
        
        # 检查结果文件
        result_file = Path("outputs/task_2_mediation_analysis.json")
        if result_file.exists():
            print(f"\n📊 结果文件已生成:")
            with open(result_file, 'r', encoding='utf-8') as f:
                hypothesis_result = json.load(f)
            print(json.dumps(hypothesis_result, indent=2, ensure_ascii=False)[:500])
        
        print(f"\n{'='*60}")
        print(f"📊 测试结果:")
        print(f"  迭代次数: {iteration_count}")
        print(f"  耗时: {elapsed:.1f}s")
        print(f"  成功: {'✅' if is_valid else '❌'}")
        
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_coding_agent_with_claude()
