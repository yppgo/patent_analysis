"""
测试 CodingAgentV4.1 - 验证豆包建议的改进
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.agents.coding_agent_v4_1 import CodingAgentV4_1
from src.utils.llm_client import LLMClient


def test_enhanced_code_extraction():
    """测试增强的代码提取功能"""
    print("=" * 80)
    print("测试 1: 增强的代码提取")
    print("=" * 80)
    
    llm_client = LLMClient()
    agent = CodingAgentV4_1(llm_client=llm_client, max_iterations=2)
    
    # 测试不同格式的代码
    test_cases = [
        # 1. Markdown 代码块（python 标记）
        """
这是一些解释文字...

```python
import pandas as pd

def test_func(df):
    return {'result': 'ok'}
```

更多解释...
        """,
        
        # 2. Markdown 代码块（无标记）
        """
```
import pandas as pd

def test_func(df):
    return {'result': 'ok'}
```
        """,
        
        # 3. 纯文本代码
        """
下面是代码：

import pandas as pd
import numpy as np

def test_func(df):
    return {'result': 'ok'}
        """,
        
        # 4. 混合格式
        """
**说明**: 这是一个测试函数

import pandas as pd

def test_func(df):
    # 这是注释
    return {'result': 'ok'}
        """
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        code = agent._extract_code_enhanced(test_case)
        if code:
            print(f"  ✅ 成功提取 ({len(code)} 字符)")
            print(f"  前50字符: {code[:50]}...")
        else:
            print(f"  ❌ 提取失败")
    
    print("\n" + "=" * 80)


def test_error_parsing():
    """测试错误解析功能"""
    print("\n" + "=" * 80)
    print("测试 2: 错误解析")
    print("=" * 80)
    
    llm_client = LLMClient()
    agent = CodingAgentV4_1(llm_client=llm_client, max_iterations=2)
    
    # 测试不同类型的错误
    test_errors = [
        "KeyError: '标题'",
        "SyntaxError: invalid syntax",
        "TypeError: unsupported operand type(s)",
        "ValueError: invalid literal for int()",
        "ImportError: No module named 'sklearn'",
        "Some unknown error occurred"
    ]
    
    for error_msg in test_errors:
        error_type, detail = agent._parse_error(error_msg)
        fix_prompt = agent._get_error_fix_prompt(error_type, ['col1', 'col2'])
        print(f"\n错误: {error_msg}")
        print(f"  类型: {error_type}")
        print(f"  修复提示: {fix_prompt[:60]}...")
    
    print("\n" + "=" * 80)


def test_repeated_error_detection():
    """测试重复错误检测"""
    print("\n" + "=" * 80)
    print("测试 3: 重复错误检测")
    print("=" * 80)
    
    llm_client = LLMClient()
    agent = CodingAgentV4_1(llm_client=llm_client, max_iterations=2)
    
    # 模拟错误历史
    agent.error_history = [
        {'type': 'KeyError', 'detail': "KeyError: '标题'"},
        {'type': 'SyntaxError', 'detail': "SyntaxError: invalid syntax"},
        {'type': 'KeyError', 'detail': "KeyError: '摘要'"},
    ]
    
    print("\n错误历史:")
    for i, err in enumerate(agent.error_history, 1):
        print(f"  {i}. {err['type']}: {err['detail']}")
    
    print("\n检测结果:")
    print(f"  KeyError 是否重复: {agent._is_repeated_error('KeyError')}")
    print(f"  SyntaxError 是否重复: {agent._is_repeated_error('SyntaxError')}")
    print(f"  TypeError 是否重复: {agent._is_repeated_error('TypeError')}")
    
    print("\n" + "=" * 80)


def test_v4_1_with_real_data():
    """测试 V4.1 完整功能（需要 LLM）"""
    print("\n" + "=" * 80)
    print("测试 4: V4.1 完整功能（真实数据）")
    print("=" * 80)
    
    # 创建测试数据
    test_data = pd.DataFrame({
        '标题(译)(简体中文)': ['专利A', '专利B', '专利C'],
        '摘要(译)(简体中文)': ['这是摘要A', '这是摘要B', '这是摘要C'],
        '申请日期': ['2020-01-01', '2020-02-01', '2020-03-01']
    })
    
    # 创建 agent
    llm_client = LLMClient()
    agent = CodingAgentV4_1(
        llm_client=llm_client,
        test_data=test_data,
        max_iterations=3
    )
    
    # 执行规格
    execution_spec = {
        'function_name': 'count_patents',
        'description': '统计专利数量',
        'input_columns': ['标题(译)(简体中文)'],
        'output': {
            'total_count': '总数量',
            'titles': '标题列表'
        }
    }
    
    print("\n开始执行...")
    result = agent.process({
        'execution_spec': execution_spec,
        'test_data': test_data
    })
    
    print("\n执行结果:")
    print(f"  迭代次数: {result['iteration_count']}")
    print(f"  代码有效: {result['is_code_valid']}")
    print(f"  错误历史: {len(result['error_history'])} 个错误")
    
    if result['error_history']:
        print("\n  错误详情:")
        for i, err in enumerate(result['error_history'], 1):
            print(f"    {i}. {err['type']}")
    
    if result['generated_code']:
        print(f"\n  生成的代码 ({len(result['generated_code'])} 字符):")
        print(f"  {result['generated_code'][:200]}...")
    
    print("\n" + "=" * 80)


def compare_v4_and_v4_1():
    """对比 V4 和 V4.1 的改进"""
    print("\n" + "=" * 80)
    print("对比: V4 vs V4.1")
    print("=" * 80)
    
    improvements = [
        ("代码提取", "简单字符串截取", "多格式正则匹配（markdown/纯文本）"),
        ("错误处理", "通用错误信息", "分类错误 + 针对性修复提示"),
        ("重试策略", "固定次数重试", "智能重试 + 重复错误检测"),
        ("迭代终止", "仅次数限制", "次数 + 重复错误 + 无法修复错误"),
        ("错误历史", "无", "完整的错误历史记录"),
        ("列名提示", "通用提示", "实际列名注入到错误提示中"),
    ]
    
    print("\n改进对比:")
    print(f"{'功能':<12} {'V4':<25} {'V4.1':<40}")
    print("-" * 80)
    for feature, v4, v4_1 in improvements:
        print(f"{feature:<12} {v4:<25} {v4_1:<40}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CodingAgentV4.1 测试套件")
    print("基于豆包建议的改进验证")
    print("=" * 80)
    
    # 运行测试
    test_enhanced_code_extraction()
    test_error_parsing()
    test_repeated_error_detection()
    compare_v4_and_v4_1()
    
    # 可选：完整功能测试（需要 LLM）
    print("\n" + "=" * 80)
    print("完整功能测试需要调用 LLM，已跳过")
    print("如需运行，请手动调用: test_v4_1_with_real_data()")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)
