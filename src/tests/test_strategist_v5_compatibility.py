"""
测试 Strategist V5.0 的向后兼容性

验证：
1. Legacy 模式（use_dag=False）生成 analysis_logic_chains
2. DAG 模式（use_dag=True）生成 task_graph
3. 默认行为保持向后兼容
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.strategist import StrategistAgent
from src.utils.llm_client import get_llm_client
from src.utils.logger import setup_logger

# 尝试导入 Neo4j（可选）
try:
    from src.utils.neo4j_connector import Neo4jConnector
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


def get_strategist_with_neo4j():
    """创建带 Neo4j 连接的 Strategist（如果可用）"""
    llm = get_llm_client()
    logger = setup_logger("test_strategist_v5")
    
    neo4j = None
    if NEO4J_AVAILABLE:
        try:
            neo4j = Neo4jConnector()
            print("✓ Neo4j 连接成功")
        except Exception as e:
            print(f"⚠️ Neo4j 连接失败: {e}")
    
    # 创建 Strategist，会自动从数据文件读取列名
    return StrategistAgent(llm, neo4j_connector=neo4j, logger=logger)


def test_legacy_mode():
    """测试 Legacy 模式（默认行为）"""
    print("\n" + "="*60)
    print("测试 1: Legacy 模式（use_dag=False，默认）")
    print("="*60)
    
    strategist = get_strategist_with_neo4j()
    
    # 不指定 use_dag，应该默认使用 Legacy 模式
    # 也不指定 available_columns，让 Strategist 自动从数据文件读取
    result = strategist.process({
        'user_goal': '分析数据安全领域的技术趋势'
    })
    
    blueprint = result['blueprint']
    
    # 验证：应该包含 analysis_logic_chains
    assert 'analysis_logic_chains' in blueprint, "Legacy 模式应该生成 analysis_logic_chains"
    assert 'task_graph' not in blueprint, "Legacy 模式不应该生成 task_graph"
    
    logic_chains = blueprint['analysis_logic_chains']
    print(f"✓ 生成了 {len(logic_chains)} 个分析步骤（analysis_logic_chains）")
    
    # 验证步骤结构
    if logic_chains:
        step = logic_chains[0]
        assert 'step_id' in step
        assert 'objective' in step
        assert 'method' in step
        assert 'implementation_config' in step
        print(f"✓ 步骤结构完整")
    
    print("✓ Legacy 模式测试通过")
    return True


def test_dag_mode():
    """测试 DAG 模式"""
    print("\n" + "="*60)
    print("测试 2: DAG 模式（use_dag=True）")
    print("="*60)
    
    strategist = get_strategist_with_neo4j()
    
    # 显式指定 use_dag=True
    # 不指定 available_columns，让 Strategist 自动从数据文件读取
    result = strategist.process({
        'user_goal': '分析数据安全领域的技术趋势',
        'use_dag': True
    })
    
    blueprint = result['blueprint']
    
    # 验证：应该包含 task_graph
    assert 'task_graph' in blueprint, "DAG 模式应该生成 task_graph"
    
    task_graph = blueprint['task_graph']
    print(f"✓ 生成了 {len(task_graph)} 个任务节点（task_graph）")
    
    # 验证任务节点结构
    if task_graph:
        task = task_graph[0]
        assert 'task_id' in task
        assert 'input_variables' in task
        assert 'output_variables' in task
        assert 'dependencies' in task
        print(f"✓ 任务节点结构完整")
        print(f"  - task_id: {task['task_id']}")
        print(f"  - input_variables: {task['input_variables']}")
        print(f"  - output_variables: {task['output_variables']}")
    
    # 验证 thinking_trace
    if 'thinking_trace' in blueprint:
        print(f"✓ 包含 thinking_trace（CoT）")
    
    print("✓ DAG 模式测试通过")
    return True


def test_explicit_legacy_mode():
    """测试显式指定 Legacy 模式"""
    print("\n" + "="*60)
    print("测试 3: 显式指定 Legacy 模式（use_dag=False）")
    print("="*60)
    
    strategist = get_strategist_with_neo4j()
    
    # 显式指定 use_dag=False
    # 不指定 available_columns，让 Strategist 自动从数据文件读取
    result = strategist.process({
        'user_goal': '识别技术空白',
        'use_dag': False
    })
    
    blueprint = result['blueprint']
    
    # 验证：应该包含 analysis_logic_chains
    assert 'analysis_logic_chains' in blueprint, "显式 Legacy 模式应该生成 analysis_logic_chains"
    
    print(f"✓ 生成了 {len(blueprint['analysis_logic_chains'])} 个分析步骤")
    print("✓ 显式 Legacy 模式测试通过")
    return True


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Strategist V5.0 向后兼容性测试")
    print("="*60)
    
    try:
        # 测试 1: 默认 Legacy 模式
        test_legacy_mode()
        
        # 测试 2: DAG 模式
        test_dag_mode()
        
        # 测试 3: 显式 Legacy 模式
        test_explicit_legacy_mode()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        print("\n总结:")
        print("  - Legacy 模式（默认）: 生成 analysis_logic_chains")
        print("  - DAG 模式（use_dag=True）: 生成 task_graph")
        print("  - 向后兼容性: ✓ 保持")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
