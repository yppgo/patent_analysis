"""
双图谱整合测试
演示因果图谱和方法图谱的协同工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graphs.causal_graph_query import CausalGraphQuery
from src.utils.variable_mapper import VariableMapper
from src.utils.neo4j_connector import Neo4jConnector
from dotenv import load_dotenv

load_dotenv()


def test_causal_graph_query():
    """测试因果图谱查询"""
    print("\n" + "="*60)
    print("测试 1: 因果图谱查询")
    print("="*60)
    
    query = CausalGraphQuery()
    
    # 1. 统计信息
    print("\n📊 因果图谱统计:")
    stats = query.get_statistics()
    print(f"  变量总数: {stats['total_variables']}")
    print(f"  路径总数: {stats['total_paths']}")
    print(f"  已验证路径: {stats['validated_paths']}")
    print(f"  变量类别: {stats['variable_categories']}")
    
    # 2. 查找直接路径
    print("\n🔍 查找直接路径: V03_rd_investment → V16_tech_impact")
    path = query.find_direct_path("V03_rd_investment", "V16_tech_impact")
    if path:
        print(query.format_hypothesis(path))
    else:
        print("  未找到直接路径")
    
    # 3. 查找中介路径
    print("\n🔍 查找中介路径: V03_rd_investment → ? → V16_tech_impact")
    mediation = query.get_mediation_paths("V03_rd_investment", "V16_tech_impact")
    print(f"  找到 {len(mediation)} 条中介路径:")
    for i, m in enumerate(mediation[:3], 1):
        mediator_label = m['mediator_var']['label']
        print(f"    {i}. V03 → {m['mediator']} ({mediator_label}) → V16")
    
    # 4. 推荐研究假设
    print("\n💡 推荐研究假设:")
    user_goal = "研究研发投资对技术影响力的影响"
    hypotheses = query.suggest_hypotheses(user_goal, top_k=3)
    for i, hyp in enumerate(hypotheses, 1):
        print(f"\n  假设 {i} (匹配分数: {hyp['score']}):")
        print(f"  {query.format_hypothesis(hyp['path'])}")


def test_variable_mapper():
    """测试变量映射器"""
    print("\n" + "="*60)
    print("测试 2: 变量映射器")
    print("="*60)
    
    mapper = VariableMapper()
    
    # 1. 统计信息
    print("\n📊 变量映射统计:")
    stats = mapper.get_statistics()
    print(f"  变量总数: {stats['total_variables']}")
    print(f"  计算类型分布: {stats['calculation_types']}")
    
    # 2. 查询变量映射
    print("\n🔍 查询变量映射: V03_rd_investment")
    config = mapper.generate_task_config("V03_rd_investment")
    print(f"  变量标签: {config['variable_label']}")
    print(f"  数据字段: {config['input_columns']}")
    print(f"  计算方法: {config['calculation']}")
    print(f"  计算类型: {config['calculation_type']}")
    
    # 3. 检查数据可用性
    print("\n✓ 检查数据可用性:")
    available_columns = [
        "序号", "公开(公告)号", "申请(专利权)人", "授权日", 
        "IPC分类号", "名称", "摘要", "发明人", "地址"
    ]
    
    test_vars = ["V03_rd_investment", "V09_tech_diversity", "V16_tech_impact"]
    for var_id in test_vars:
        availability = mapper.check_data_availability(var_id, available_columns)
        status = "✓" if availability['is_available'] else "✗"
        print(f"  {status} {availability['variable_label']}: ", end="")
        if availability['is_available']:
            print("数据完整")
        else:
            print(f"缺失 {availability['missing_columns']}")
    
    # 4. 获取假设所需字段
    print("\n📋 获取假设所需字段:")
    print("  假设: V03_rd_investment → V09_tech_diversity → V16_tech_impact")
    required = mapper.get_required_columns_for_hypothesis(
        "V03_rd_investment", 
        "V16_tech_impact",
        mediators=["V09_tech_diversity"]
    )
    print(f"  所需字段: {required}")


def test_neo4j_method_graph():
    """测试方法图谱查询（Neo4j）"""
    print("\n" + "="*60)
    print("测试 3: 方法图谱查询（Neo4j）")
    print("="*60)
    
    try:
        neo4j = Neo4jConnector()
        
        # 1. 检索相关案例
        print("\n🔍 检索关键词: '研发投资'")
        cases = neo4j.retrieve_best_practices("研发投资", limit=2)
        
        if cases:
            print(f"  找到 {len(cases)} 个相关案例:")
            for i, case in enumerate(cases, 1):
                print(f"\n  案例 {i}: {case['paper_title']}")
                logic_chain = case.get('full_logic_chain', [])
                print(f"  分析步骤数: {len(logic_chain)}")
                for step in logic_chain[:3]:  # 只显示前3步
                    print(f"    - 步骤 {step.get('step_id')}: {step.get('objective')}")
                    print(f"      方法: {step.get('method_name', step.get('method'))}")
        else:
            print("  未找到相关案例")
        
        neo4j.close()
        
    except Exception as e:
        print(f"  ⚠️ Neo4j 连接失败: {e}")
        print("  提示: 请确保 Neo4j 已启动，并设置了正确的环境变量")


def test_dual_graph_integration():
    """测试双图谱整合"""
    print("\n" + "="*60)
    print("测试 4: 双图谱整合演示")
    print("="*60)
    
    # 用户输入
    user_goal = "研究研发投资对技术影响力的影响，考虑技术多样性的中介作用"
    print(f"\n👤 用户目标: {user_goal}")
    
    # Step 1: 因果图谱推理
    print("\n" + "-"*60)
    print("Step 1: 因果图谱推理（Why）")
    print("-"*60)
    
    causal_query = CausalGraphQuery()
    
    # 1.1 推荐假设
    hypotheses = causal_query.suggest_hypotheses(user_goal, top_k=3)
    print(f"\n💡 推荐 {len(hypotheses)} 个研究假设:")
    for i, hyp in enumerate(hypotheses, 1):
        print(f"\n  H{i}: {causal_query.format_hypothesis(hyp['path'])}")
    
    # 1.2 识别中介路径
    mediation = causal_query.get_mediation_paths("V03_rd_investment", "V16_tech_impact")
    print(f"\n🔗 识别到 {len(mediation)} 条中介路径:")
    for i, m in enumerate(mediation[:2], 1):
        mediator_label = m['mediator_var']['label']
        print(f"  {i}. {m['source']} → {m['mediator']} ({mediator_label}) → {m['target']}")
    
    # Step 2: 变量映射
    print("\n" + "-"*60)
    print("Step 2: 变量映射（抽象变量 → 数据字段）")
    print("-"*60)
    
    mapper = VariableMapper()
    
    # 2.1 获取所需字段
    required_columns = mapper.get_required_columns_for_hypothesis(
        "V03_rd_investment",
        "V16_tech_impact",
        mediators=["V09_tech_diversity"]
    )
    print(f"\n📋 所需数据字段: {required_columns}")
    
    # 2.2 生成任务配置
    print("\n⚙️ 任务配置:")
    for var_id in ["V03_rd_investment", "V09_tech_diversity", "V16_tech_impact"]:
        config = mapper.generate_task_config(var_id)
        print(f"\n  {config['variable_label']} ({var_id}):")
        print(f"    输入字段: {config['input_columns']}")
        print(f"    计算方法: {config['calculation']}")
    
    # Step 3: 方法图谱检索
    print("\n" + "-"*60)
    print("Step 3: 方法图谱检索（How）")
    print("-"*60)
    
    try:
        neo4j = Neo4jConnector()
        
        # 3.1 检索相关案例（使用实际存在的关键词）
        keywords = ["技术", "专利", "分析"]
        print(f"\n🔍 检索关键词: {keywords}")
        
        all_cases = []
        for keyword in keywords[:2]:  # 只检索前2个关键词
            cases = neo4j.retrieve_best_practices(keyword, limit=1)
            all_cases.extend(cases)
        
        if all_cases:
            print(f"\n📚 找到 {len(all_cases)} 个方法案例:")
            for i, case in enumerate(all_cases, 1):
                print(f"\n  案例 {i}: {case['paper_title']}")
                logic_chain = case.get('full_logic_chain', [])
                for step in logic_chain[:2]:  # 只显示前2步
                    print(f"    步骤 {step.get('step_id')}: {step.get('method_name', step.get('method'))}")
        
        neo4j.close()
        
    except Exception as e:
        print(f"  ⚠️ Neo4j 连接失败: {e}")
        print("  （跳过方法图谱检索）")
    
    # Step 4: 生成研究方案（模拟）
    print("\n" + "-"*60)
    print("Step 4: 生成研究方案（整合双图谱）")
    print("-"*60)
    
    print("\n📝 研究方案草图:")
    print("""
  Task 1: 数据准备
    - 加载数据: data/clean_patents1_with_topics_filled.xlsx
    - 所需字段: ['序号', '公开(公告)号', '申请(专利权)人', 'IPC分类号', '被引用专利']
    - 输出: outputs/task_1_data_summary.json
  
  Task 2: 计算自变量（V03_rd_investment）
    - 方法: 聚合分析
    - 计算: COUNT(专利) / COUNT(DISTINCT 申请人)
    - 输出: outputs/task_2_rd_investment.csv
  
  Task 3: 计算中介变量（V09_tech_diversity）
    - 方法: 熵计算
    - 计算: Shannon Entropy of IPC
    - 输出: outputs/task_3_tech_diversity.csv
  
  Task 4: 计算因变量（V16_tech_impact）
    - 方法: 引用分析
    - 计算: COUNT(前向引用)
    - 输出: outputs/task_4_tech_impact.csv
  
  Task 5: 中介效应检验
    - 方法: Baron & Kenny 三步法
    - 步骤 1: V03 → V16 (总效应)
    - 步骤 2: V03 → V09 (路径a)
    - 步骤 3: V03 + V09 → V16 (路径b和直接效应)
    - 输出: outputs/task_5_mediation_analysis.json
    """)
    
    print("\n✓ 双图谱整合完成！")
    print("  - 因果图谱提供了理论假设和变量定义")
    print("  - 变量映射器连接了抽象变量和数据字段")
    print("  - 方法图谱提供了具体的分析方法和步骤")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("双图谱整合测试")
    print("="*60)
    
    # 测试 1: 因果图谱查询
    test_causal_graph_query()
    
    # 测试 2: 变量映射器
    test_variable_mapper()
    
    # 测试 3: 方法图谱查询
    test_neo4j_method_graph()
    
    # 测试 4: 双图谱整合
    test_dual_graph_integration()
    
    print("\n" + "="*60)
    print("✓ 所有测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
