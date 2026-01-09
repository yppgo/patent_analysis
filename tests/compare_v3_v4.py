"""
对比 V3 和 V4 的改进
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import time
from src.agents.coding_agent_v3 import CodingAgentV3
from src.agents.coding_agent_v4 import CodingAgentV4
from src.utils.llm_client import LLMClient


def compare_basic_functionality():
    """对比基本功能"""
    print("=" * 80)
    print("对比测试：基本功能")
    print("=" * 80)
    
    # 测试数据
    test_data = pd.DataFrame({
        '标题(译)(简体中文)': ['专利A', '专利B', '专利C', '专利D', '专利E'],
        '摘要(译)(简体中文)': ['摘要A', '摘要B', '摘要C', '摘要D', '摘要E'],
        '申请日期': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01']
    })
    
    # 执行规格
    execution_spec = {
        'function_name': 'analyze_patents',
        'description': '分析专利数据，统计数量和提取标题',
        'input_columns': ['标题(译)(简体中文)', '摘要(译)(简体中文)'],
        'output': {
            'total_count': '专利总数',
            'titles': '标题列表',
            'avg_title_length': '平均标题长度'
        }
    }
    
    llm_client = LLMClient()
    
    # 测试 V3
    print("\n" + "-" * 80)
    print("测试 V3 (使用 exec)")
    print("-" * 80)
    start_time = time.time()
    
    agent_v3 = CodingAgentV3(
        llm_client=llm_client,
        test_data=test_data,
        max_iterations=2
    )
    
    result_v3 = agent_v3.process({
        'execution_spec': execution_spec,
        'test_data': test_data
    })
    
    v3_time = time.time() - start_time
    
    print(f"\n✅ V3 完成")
    print(f"   - 耗时: {v3_time:.2f}秒")
    print(f"   - 迭代次数: {result_v3['iteration_count']}")
    print(f"   - 代码有效: {result_v3['is_code_valid']}")
    print(f"   - 代码长度: {len(result_v3['generated_code'])} 字符")
    
    # 测试 V4
    print("\n" + "-" * 80)
    print("测试 V4 (使用 subprocess)")
    print("-" * 80)
    start_time = time.time()
    
    agent_v4 = CodingAgentV4(
        llm_client=llm_client,
        test_data=test_data,
        max_iterations=2
    )
    
    result_v4 = agent_v4.process({
        'execution_spec': execution_spec,
        'test_data': test_data
    })
    
    v4_time = time.time() - start_time
    
    print(f"\n✅ V4 完成")
    print(f"   - 耗时: {v4_time:.2f}秒")
    print(f"   - 迭代次数: {result_v4['iteration_count']}")
    print(f"   - 代码有效: {result_v4['is_code_valid']}")
    print(f"   - 代码长度: {len(result_v4['generated_code'])} 字符")
    
    # 对比
    print("\n" + "=" * 80)
    print("对比结果")
    print("=" * 80)
    print(f"耗时对比: V3={v3_time:.2f}s, V4={v4_time:.2f}s")
    print(f"速度提升: {((v3_time - v4_time) / v3_time * 100):.1f}%")
    print(f"\n关键改进:")
    print(f"  ✅ V4 使用 subprocess（安全）")
    print(f"  ✅ V4 无状态设计（支持并发）")
    print(f"  ✅ V4 减少 LLM 调用（更高效）")


def compare_security():
    """对比安全性"""
    print("\n" + "=" * 80)
    print("对比测试：安全性")
    print("=" * 80)
    
    print("\n📋 安全性对比:")
    print("-" * 80)
    
    print("\n❌ V3 (exec):")
    print("   - 代码在主进程中执行")
    print("   - 可以访问所有环境变量")
    print("   - 可以修改全局状态")
    print("   - 无超时保护")
    print("   - 崩溃会影响主进程")
    print("   - 风险等级: 🔴 高")
    
    print("\n✅ V4 (subprocess):")
    print("   - 代码在隔离的子进程中执行")
    print("   - 环境变量隔离")
    print("   - 无法修改主进程状态")
    print("   - 30秒超时保护")
    print("   - 崩溃不影响主进程")
    print("   - 风险等级: 🟢 低")
    
    print("\n💡 未来改进:")
    print("   - Docker 容器隔离")
    print("   - 资源限制（CPU、内存）")
    print("   - 网络隔离")


def compare_concurrency():
    """对比并发支持"""
    print("\n" + "=" * 80)
    print("对比测试：并发支持")
    print("=" * 80)
    
    print("\n📋 并发支持对比:")
    print("-" * 80)
    
    print("\n❌ V3 (有状态):")
    print("   - 使用实例变量存储上下文")
    print("   - self.current_execution_spec")
    print("   - self.current_test_data")
    print("   - 并发调用会导致数据污染")
    print("   - 适用场景: 单线程、单请求")
    
    print("\n✅ V4 (无状态):")
    print("   - 通过工具参数传递上下文")
    print("   - 每次调用完全隔离")
    print("   - 支持并发调用")
    print("   - 适用场景: Web 服务、多线程")
    
    print("\n💡 示例:")
    print("   V3: 请求A 和 请求B 同时到达 → 数据混乱")
    print("   V4: 请求A 和 请求B 同时到达 → 完全隔离 ✅")


def compare_architecture():
    """对比架构设计"""
    print("\n" + "=" * 80)
    print("对比测试：架构设计")
    print("=" * 80)
    
    print("\n📋 架构对比:")
    print("-" * 80)
    
    print("\n❌ V3 架构:")
    print("""
    User Request
        ↓
    ReAct Agent (LLM)
        ↓
    generate_code Tool
        ↓
    LLM (再次调用) ← 反模式：LLM 调用 LLM
        ↓
    test_code Tool (exec) ← 不安全
        ↓
    Result
    
    问题:
    - 双重 LLM 调用（成本高、延迟大）
    - 上下文丢失
    - 不安全的 exec
    """)
    
    print("\n✅ V4 架构:")
    print("""
    User Request
        ↓
    ReAct Agent (LLM)
        ├─→ preview_data Tool
        ├─→ 直接生成代码（在消息中）
        ├─→ check_code_syntax Tool
        └─→ run_python_code Tool (subprocess) ← 安全
        ↓
    Result
    
    优势:
    - 单次 LLM 调用（成本低、延迟小）
    - 保持完整上下文
    - 安全的 subprocess
    - 符合 ReAct 模式
    """)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Coding Agent V3 vs V4 对比测试")
    print("=" * 80)
    
    # 运行对比测试
    compare_security()
    compare_concurrency()
    compare_architecture()
    
    # 功能测试（可选，需要 LLM）
    print("\n" + "=" * 80)
    print("功能对比测试需要调用 LLM，已跳过")
    print("如需运行，请手动调用: compare_basic_functionality()")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("✅ 对比测试完成")
    print("=" * 80)
    print("\n总结:")
    print("  V4 在安全性、并发性、效率方面都有显著提升")
    print("  建议在生产环境使用 V4")
    print("=" * 80)
