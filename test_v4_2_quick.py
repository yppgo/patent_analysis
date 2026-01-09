"""
快速测试 V4.2 - 最小化测试
"""
import sys
import os

# 设置路径
sys.path.append(os.path.abspath('.'))

print("=" * 60)
print("快速测试 Coding Agent V4.2")
print("=" * 60)

try:
    import pandas as pd
    from src.utils.llm_client import LLMClient
    from src.agents.coding_agent_v4_2 import CodingAgentV4_2
    
    print("\n[1/3] 初始化...")
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=5)
    print("✓ 初始化成功")
    
    print("\n[2/3] 准备测试数据...")
    test_data = pd.DataFrame({
        'x': [1, 2, 3],
        'y': [10, 20, 30]
    })
    print("✓ 数据准备完成")
    
    print("\n[3/3] 执行简单任务...")
    task = {
        'execution_spec': {
            'description': '计算 x 和 y 列的总和并打印'
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"状态: {'成功' if result['generated_code'] else '失败'}")
    print(f"迭代次数: {result['iteration_count']}")
    print(f"错误数: {len(result['error_history'])}")
    
    if result['generated_code']:
        print("\n生成的代码:")
        print("-" * 60)
        print(result['generated_code'][:300])
    
    print("\n✓ 测试完成！")
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
