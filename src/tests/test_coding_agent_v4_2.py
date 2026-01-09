"""
Coding Agent V4.2 测试
测试终端和文件操作能力
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 设置 UTF-8 编码（解决 Windows GBK 编码问题）
if sys.platform == 'win32':
    import io
    # 使用 line_buffering=True 确保实时输出
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# 确保能导入 src 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.llm_client import LLMClient
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def test_basic_file_operations():
    """测试基本的文件操作能力"""
    print("=" * 70)
    print("[测试 1] 基本文件操作")
    print("=" * 70)
    
    # 初始化
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=10)
    
    # 准备测试数据
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10, 20, 30, 40, 50],
        'category': ['A', 'B', 'A', 'B', 'C']
    })
    
    # 任务：创建目录、保存文件、验证
    task = {
        'execution_spec': {
            'function_name': 'test_file_ops',
            'description': """
            请完成以下任务：
            1. 检查 test_outputs 目录是否存在，如果不存在则创建
            2. 将测试数据保存到 test_outputs/test_data.csv
            3. 读取刚保存的文件，验证内容正确
            4. 打印文件的前3行
            """,
            'inputs': ['df'],
            'outputs': ['保存的文件路径']
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    print("\n" + "=" * 70)
    print("[测试结果]")
    
    # 检查是否有代码生成
    has_code = result['generated_code'] and len(result['generated_code']) > 0
    
    # 检查文件是否创建
    file_created = Path('test_outputs/test_data.csv').exists()
    
    # 综合判断
    is_success = has_code and file_created and result['iteration_count'] > 0
    
    print(f"- 状态: {'[成功]' if is_success else '[失败]'}")
    print(f"- 代码生成: {'[OK]' if has_code else '[FAIL]'}")
    print(f"- 文件创建: {'[OK]' if file_created else '[FAIL]'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 错误历史: {len(result['error_history'])} 个错误")
    
    if result['generated_code']:
        print("\n生成的代码:")
        print("-" * 70)
        code_preview = result['generated_code'][:500] + "..." if len(result['generated_code']) > 500 else result['generated_code']
        print(code_preview)
    
    # 清理
    try:
        import shutil
        if Path('test_outputs').exists():
            shutil.rmtree('test_outputs')
    except:
        pass


def test_package_installation():
    """测试包安装能力"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: 包安装和使用")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=10)
    
    test_data = pd.DataFrame({
        'text': ['hello world', 'test data', 'python code'],
        'score': [0.8, 0.6, 0.9]
    })
    
    task = {
        'execution_spec': {
            'function_name': 'test_package',
            'description': """
            请完成以下任务：
            1. 检查是否安装了 tabulate 包
            2. 如果没有安装，使用 pip install tabulate 安装
            3. 使用 tabulate 将数据格式化为表格并打印
            """,
            'inputs': ['df'],
            'outputs': ['格式化的表格']
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    print("\n" + "=" * 70)
    print("📊 测试结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")


def test_multi_step_analysis():
    """测试多步骤分析（模拟真实场景）"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: 多步骤分析（真实场景模拟）")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=20)  # 增加到 20
    
    # 模拟专利数据
    test_data = pd.DataFrame({
        'patent_id': [f'P{i:04d}' for i in range(1, 101)],  # 使用 P0001 格式
        'title': [f'Patent Title {i}' for i in range(1, 101)],
        'year': [2020 + (i % 5) for i in range(100)],
        'citations': [i * 2 for i in range(100)],
        'abstract': [f'This is abstract {i}' for i in range(100)]
    })
    
    # 模拟前一步的主题分析结果
    prev_results = pd.DataFrame({
        'patent_id': [f'P{i:04d}' for i in range(1, 101)],  # 使用相同的格式
        'topic_id': [(i % 5) for i in range(100)],
        'topic_prob': [0.6 + (i % 4) * 0.1 for i in range(100)]
    })
    
    # 保存前一步结果（模拟依赖）
    Path('test_outputs').mkdir(exist_ok=True)
    prev_results.to_csv('test_outputs/step_1_topics.csv', index=False)
    
    task = {
        'execution_spec': {
            'function_name': 'analyze_topics',
            'description': """
            基于主题分析结果，进行趋势分析：
            1. 使用提供的测试数据（df 变量已经包含主数据）
            2. 加载前一步的主题结果：test_outputs/step_1_topics.csv
            3. 按 patent_id 合并数据
            4. 统计每个主题每年的专利数量
            5. 计算每个主题的平均引用数
            6. 保存结果到 test_outputs/topic_trends.csv
            
            注意：不要重新加载 Excel 文件，直接使用 df 变量！
            """,
            'inputs': ['df', 'previous_topics'],
            'outputs': ['topic_trends']
        },
        'test_data': test_data,
        'current_step': {
            'implementation_config': {
                'input_data_source': {
                    'main_data': 'test_data',
                    'main_data_columns': ['patent_id', 'year', 'citations'],
                    'dependencies': [
                        {
                            'file': 'test_outputs/step_1_topics.csv',
                            'columns': ['patent_id', 'topic_id', 'topic_prob'],
                            'description': '前一步的主题分析结果'
                        }
                    ]
                },
                'output_files': {
                    'results_csv': 'test_outputs/topic_trends.csv',
                    'results_columns': ['topic_id', 'year', 'patent_count', 'avg_citations'],
                    'format_notes': '每行代表一个主题在某一年的统计数据'
                }
            }
        }
    }
    
    result = agent.process(task)
    
    print("\n" + "=" * 70)
    print("📊 测试结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 错误历史: {len(result['error_history'])} 个错误")
    
    # 检查输出文件
    if Path('test_outputs/topic_trends.csv').exists():
        print("\n✅ 输出文件已创建")
        df_result = pd.read_csv('test_outputs/topic_trends.csv')
        print(f"- 结果行数: {len(df_result)}")
        print(f"- 结果列名: {list(df_result.columns)}")
        print("\n前5行:")
        print(df_result.head())
    else:
        print("\n❌ 输出文件未创建")
    
    # 清理
    try:
        import shutil
        if Path('test_outputs').exists():
            shutil.rmtree('test_outputs')
    except:
        pass


def test_error_recovery():
    """测试错误恢复能力"""
    print("\n" + "=" * 70)
    print("🧪 测试 4: 错误恢复能力")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=10)
    
    # 故意使用容易出错的列名
    test_data = pd.DataFrame({
        'Patent ID': [1, 2, 3],  # 注意：有空格
        'Title Text': ['A', 'B', 'C'],
        'Year Published': [2020, 2021, 2022]
    })
    
    task = {
        'execution_spec': {
            'function_name': 'test_error',
            'description': """
            请完成以下任务：
            1. 预览数据，了解实际列名（注意可能有空格）
            2. 统计每年的专利数量
            3. 打印结果
            
            注意：列名可能包含空格，需要正确处理
            """,
            'inputs': ['df'],
            'outputs': ['统计结果']
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    print("\n" + "=" * 70)
    print("📊 测试结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 错误历史: {len(result['error_history'])} 个错误")
    
    if result['error_history']:
        print("\n错误历史:")
        for i, err in enumerate(result['error_history'], 1):
            print(f"  {i}. {err['type']}: {err['detail'][:100]}")


def main():
    """运行所有测试"""
    # 强制刷新输出
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Coding Agent V4.2 测试套件                                       ║
║  测试终端和文件操作能力                                           ║
╚══════════════════════════════════════════════════════════════════╝
    """, flush=True)
    
    try:
        # 测试 1: 基本文件操作
        test_basic_file_operations()
        
        # 测试 2: 包安装
        # test_package_installation()  # 可选，避免频繁安装包
        
        # 测试 3: 多步骤分析
        test_multi_step_analysis()
        
        # 测试 4: 错误恢复
        test_error_recovery()
        
        print("\n" + "=" * 70)
        print("🎉 所有测试完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
