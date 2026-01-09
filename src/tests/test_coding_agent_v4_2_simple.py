"""
Coding Agent V4.2 简单测试
快速验证核心功能
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from pathlib import Path
from src.utils.llm_client import LLMClient
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def test_1_basic_python_execution():
    """测试 1: 基本 Python 代码执行"""
    print("\n" + "=" * 70)
    print("🧪 测试 1: 基本 Python 代码执行")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=5)
    
    test_data = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
    task = {
        'execution_spec': {
            'description': '计算 x 列和 y 列的总和，并打印结果'
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    success = result['generated_code'] and result['iteration_count'] > 0
    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"迭代次数: {result['iteration_count']}")
    
    return success


def test_2_file_creation():
    """测试 2: 文件创建"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: 文件创建")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=8)
    
    test_data = pd.DataFrame({
        'category': ['A', 'B', 'A', 'B', 'C'],
        'value': [100, 150, 120, 180, 200]
    })
    
    # 确保目录存在
    Path('test_outputs').mkdir(exist_ok=True)
    
    task = {
        'execution_spec': {
            'description': """
            统计每个 category 的平均 value，
            并保存结果到 test_outputs/category_avg.csv
            """
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    file_exists = Path('test_outputs/category_avg.csv').exists()
    success = result['generated_code'] and file_exists
    
    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"文件创建: {'✅' if file_exists else '❌'}")
    print(f"迭代次数: {result['iteration_count']}")
    
    # 清理
    try:
        if file_exists:
            os.remove('test_outputs/category_avg.csv')
    except:
        pass
    
    return success


def test_3_shell_commands():
    """测试 3: Shell 命令执行"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: Shell 命令执行")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=5)
    
    test_data = pd.DataFrame({'x': [1, 2, 3]})
    
    task = {
        'execution_spec': {
            'description': """
            使用 execute_shell 工具：
            1. 检查当前目录
            2. 列出 outputs 目录的内容（如果存在）
            """
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    success = result['generated_code'] and result['iteration_count'] > 0
    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"迭代次数: {result['iteration_count']}")
    
    return success


def test_4_stateful_execution():
    """测试 4: 有状态执行"""
    print("\n" + "=" * 70)
    print("🧪 测试 4: 有状态执行（变量保持）")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=8)
    
    test_data = pd.DataFrame({'x': [1, 2, 3]})
    
    task = {
        'execution_spec': {
            'description': """
            分两步执行：
            1. 定义一个变量 result = 100
            2. 在下一步中使用这个变量，打印 result + 50
            
            这测试 REPL 的状态保持能力
            """
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    # 检查是否有多次代码执行（说明是分步的）
    success = result['generated_code'] and result['iteration_count'] >= 2
    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"迭代次数: {result['iteration_count']} (应该 >= 2)")
    
    return success


def main():
    """运行所有简单测试"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Coding Agent V4.2 简单测试                                       ║
║  快速验证核心功能                                                 ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    try:
        # 测试 1: 基本执行
        results.append(("基本 Python 执行", test_1_basic_python_execution()))
        
        # 测试 2: 文件创建
        results.append(("文件创建", test_2_file_creation()))
        
        # 测试 3: Shell 命令
        results.append(("Shell 命令", test_3_shell_commands()))
        
        # 测试 4: 有状态执行
        results.append(("有状态执行", test_4_stateful_execution()))
        
        # 总结
        print("\n" + "=" * 70)
        print("📊 测试总结")
        print("=" * 70)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{name:<20s}: {status}")
        
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！V4.2 工作正常！")
        else:
            print(f"\n⚠️ {total - passed} 个测试失败")
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
