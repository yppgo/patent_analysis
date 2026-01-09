"""
Coding Agent V4.2 使用示例
展示如何在实际项目中使用 V4.2
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.utils.llm_client import LLMClient
from src.agents.coding_agent_v4_2 import CodingAgentV4_2


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 70)
    print("示例 1: 基本使用 - 简单的数据统计")
    print("=" * 70)
    
    # 初始化
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=10)
    
    # 准备测试数据
    test_data = pd.DataFrame({
        'year': [2020, 2020, 2021, 2021, 2022, 2022, 2023],
        'category': ['A', 'B', 'A', 'B', 'A', 'B', 'A'],
        'value': [100, 150, 120, 180, 140, 200, 160]
    })
    
    # 定义任务
    task = {
        'execution_spec': {
            'function_name': 'analyze_data',
            'description': """
            请完成以下分析：
            1. 统计每年的数据条数
            2. 计算每个类别的平均值
            3. 打印结果
            """,
            'inputs': ['df'],
            'outputs': ['统计结果']
        },
        'test_data': test_data
    }
    
    # 执行
    result = agent.process(task)
    
    # 查看结果
    print("\n结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 代码长度: {len(result['generated_code'])} 字符")


def example_2_with_file_output():
    """示例 2: 带文件输出"""
    print("\n" + "=" * 70)
    print("示例 2: 带文件输出 - 保存分析结果")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=15)
    
    # 模拟专利数据
    test_data = pd.DataFrame({
        'patent_id': [f'P{i:04d}' for i in range(1, 51)],
        'year': [2020 + (i % 4) for i in range(50)],
        'citations': [i * 2 for i in range(50)],
        'category': ['Tech', 'Bio', 'Chem'][i % 3] for i in range(50)
    })
    
    task = {
        'execution_spec': {
            'function_name': 'analyze_patents',
            'description': """
            分析专利数据：
            1. 统计每年每个类别的专利数量
            2. 计算每个类别的平均引用数
            3. 保存结果到指定文件
            """,
            'inputs': ['df'],
            'outputs': ['category_stats']
        },
        'test_data': test_data,
        'current_step': {
            'implementation_config': {
                'output_files': {
                    'results_csv': 'outputs/example_category_stats.csv',
                    'results_columns': ['category', 'year', 'patent_count', 'avg_citations'],
                    'format_notes': '每行代表一个类别在某一年的统计数据'
                }
            }
        }
    }
    
    result = agent.process(task)
    
    print("\n结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    
    # 检查输出文件
    from pathlib import Path
    if Path('outputs/example_category_stats.csv').exists():
        print("\n✅ 输出文件已创建")
        df_result = pd.read_csv('outputs/example_category_stats.csv')
        print(f"- 结果行数: {len(df_result)}")
        print(f"- 结果列名: {list(df_result.columns)}")
        print("\n前5行:")
        print(df_result.head())


def example_3_with_dependencies():
    """示例 3: 带依赖关系（模拟多步骤分析）"""
    print("\n" + "=" * 70)
    print("示例 3: 多步骤分析 - 使用前一步的结果")
    print("=" * 70)
    
    from pathlib import Path
    Path('outputs').mkdir(exist_ok=True)
    
    # 步骤 1: 生成主题分类结果（模拟）
    print("\n[步骤 1] 模拟生成主题分类结果...")
    topic_results = pd.DataFrame({
        'patent_id': [f'P{i:04d}' for i in range(1, 51)],
        'topic_id': [i % 3 for i in range(50)],
        'topic_prob': [0.6 + (i % 4) * 0.1 for i in range(50)]
    })
    topic_results.to_csv('outputs/example_step_1_topics.csv', index=False)
    print("✅ 主题分类结果已保存")
    
    # 步骤 2: 基于主题结果进行趋势分析
    print("\n[步骤 2] 基于主题结果进行趋势分析...")
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=15)
    
    # 主数据
    main_data = pd.DataFrame({
        'patent_id': [f'P{i:04d}' for i in range(1, 51)],
        'year': [2020 + (i % 4) for i in range(50)],
        'citations': [i * 2 for i in range(50)]
    })
    
    task = {
        'execution_spec': {
            'function_name': 'analyze_topic_trends',
            'description': """
            基于主题分类结果，分析主题趋势：
            1. 加载主数据和前一步的主题结果
            2. 按 patent_id 合并数据
            3. 统计每个主题每年的专利数量
            4. 计算每个主题的平均引用数
            5. 保存结果
            """,
            'inputs': ['df', 'topic_results'],
            'outputs': ['topic_trends']
        },
        'test_data': main_data,
        'current_step': {
            'implementation_config': {
                'input_data_source': {
                    'main_data': 'main_data',
                    'main_data_columns': ['patent_id', 'year', 'citations'],
                    'dependencies': [
                        {
                            'file': 'outputs/example_step_1_topics.csv',
                            'columns': ['patent_id', 'topic_id', 'topic_prob'],
                            'description': '前一步的主题分类结果'
                        }
                    ]
                },
                'output_files': {
                    'results_csv': 'outputs/example_step_2_trends.csv',
                    'results_columns': ['topic_id', 'year', 'patent_count', 'avg_citations'],
                    'format_notes': '每行代表一个主题在某一年的统计数据'
                }
            }
        }
    }
    
    result = agent.process(task)
    
    print("\n结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    
    # 检查输出文件
    if Path('outputs/example_step_2_trends.csv').exists():
        print("\n✅ 趋势分析结果已创建")
        df_result = pd.read_csv('outputs/example_step_2_trends.csv')
        print(f"- 结果行数: {len(df_result)}")
        print(f"- 结果列名: {list(df_result.columns)}")
        print("\n前5行:")
        print(df_result.head())
    
    # 清理示例文件
    print("\n[清理] 删除示例文件...")
    try:
        os.remove('outputs/example_step_1_topics.csv')
        os.remove('outputs/example_step_2_trends.csv')
        if Path('outputs/example_category_stats.csv').exists():
            os.remove('outputs/example_category_stats.csv')
        print("✅ 清理完成")
    except:
        pass


def example_4_error_recovery():
    """示例 4: 错误恢复能力展示"""
    print("\n" + "=" * 70)
    print("示例 4: 错误恢复 - 处理列名问题")
    print("=" * 70)
    
    client = LLMClient.from_env()
    agent = CodingAgentV4_2(llm_client=client, max_iterations=10)
    
    # 故意使用容易出错的列名
    test_data = pd.DataFrame({
        'Patent ID': [1, 2, 3, 4, 5],  # 有空格
        'Title Text': ['A', 'B', 'C', 'D', 'E'],
        'Year Published': [2020, 2021, 2022, 2023, 2024]
    })
    
    task = {
        'execution_spec': {
            'function_name': 'test_error_recovery',
            'description': """
            统计每年的专利数量。
            注意：列名可能包含空格，需要正确处理。
            """,
            'inputs': ['df'],
            'outputs': ['yearly_counts']
        },
        'test_data': test_data
    }
    
    result = agent.process(task)
    
    print("\n结果:")
    print(f"- 状态: {'✅ 成功' if result['is_code_valid'] else '❌ 失败'}")
    print(f"- 迭代次数: {result['iteration_count']}")
    print(f"- 错误历史: {len(result['error_history'])} 个错误")
    
    if result['error_history']:
        print("\n错误恢复过程:")
        for i, err in enumerate(result['error_history'], 1):
            print(f"  {i}. {err['type']}: {err['detail'][:80]}...")


def main():
    """运行所有示例"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Coding Agent V4.2 使用示例                                       ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 示例 1: 基本使用
        example_1_basic_usage()
        
        # 示例 2: 带文件输出
        example_2_with_file_output()
        
        # 示例 3: 多步骤分析
        example_3_with_dependencies()
        
        # 示例 4: 错误恢复
        example_4_error_recovery()
        
        print("\n" + "=" * 70)
        print("🎉 所有示例完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
