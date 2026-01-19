"""
展示 DAG 模式的实际输出结构

运行后会生成 JSON 文件，方便查看完整的 DAG 结构
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.strategist import StrategistAgent
from src.utils.llm_client import get_llm_client
from src.utils.logger import setup_logger

# 尝试导入 Neo4j
try:
    from src.utils.neo4j_connector import Neo4jConnector
    neo4j = Neo4jConnector()
    print("✓ Neo4j 连接成功")
except Exception as e:
    neo4j = None
    print(f"⚠️ Neo4j 未连接: {e}")

# 初始化
llm = get_llm_client()
logger = setup_logger("show_dag")

# 创建 Strategist（会自动从数据文件读取列名）
strategist = StrategistAgent(llm, neo4j_connector=neo4j, logger=logger)

print("\n" + "="*80)
print("生成 DAG 模式输出...")
print("（Strategist 会自动从数据文件读取列名）")
print("="*80)

# 生成 DAG 蓝图（不指定 available_columns）
result = strategist.process({
    'user_goal': '分析数据安全领域的技术趋势和创新热点',
    'use_dag': True
})

blueprint = result['blueprint']

# 保存完整输出
output_file = 'outputs/dag_output_example.json'
os.makedirs('outputs', exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(blueprint, f, ensure_ascii=False, indent=2)

print(f"\n✓ 完整输出已保存到: {output_file}")
print("\n" + "="*80)
print("DAG 结构预览")
print("="*80)

# 打印关键信息
if 'thinking_trace' in blueprint:
    print("\n【思考过程】")
    for key, value in blueprint['thinking_trace'].items():
        print(f"  {key}: {str(value)[:100]}...")

print(f"\n【研究目标】")
print(f"  {blueprint.get('research_objective', 'N/A')}")

if 'task_graph' in blueprint:
    print(f"\n【任务图】共 {len(blueprint['task_graph'])} 个任务")
    for task in blueprint['task_graph']:
        print(f"\n  任务: {task['task_id']}")
        print(f"    类型: {task.get('task_type', 'N/A')}")
        print(f"    输入: {task.get('input_variables', [])}")
        print(f"    输出: {task.get('output_variables', [])}")
        print(f"    依赖: {task.get('dependencies', [])}")

print(f"\n\n查看完整 JSON: {output_file}")
