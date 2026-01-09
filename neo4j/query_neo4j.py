"""
Neo4j 数据查询示例脚本
"""

from neo4j import GraphDatabase
from neo4j_config import NEO4J_CONFIG


def run_query(query, description):
    """执行查询并打印结果"""
    print(f"\n{'='*60}")
    print(f"📊 {description}")
    print(f"{'='*60}")
    
    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
    )
    
    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        
        if not records:
            print("  (无结果)")
        else:
            for record in records:
                print(f"  {dict(record)}")
    
    driver.close()


def main():
    """运行示例查询"""
    
    print("\n🔍 Neo4j 数据库查询示例")
    
    # 1. 统计各类节点数量
    run_query(
        """
        MATCH (n)
        RETURN labels(n)[0] AS 节点类型, count(n) AS 数量
        ORDER BY 数量 DESC
        """,
        "节点统计"
    )
    
    # 2. 统计各类关系数量
    run_query(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS 关系类型, count(r) AS 数量
        ORDER BY 数量 DESC
        """,
        "关系统计"
    )
    
    # 3. 查看所有论文
    run_query(
        """
        MATCH (p:Paper)
        RETURN p.title AS 论文标题, p.year AS 年份
        ORDER BY p.year DESC
        LIMIT 10
        """,
        "最新的 10 篇论文"
    )
    
    # 4. 统计最常用的方法
    run_query(
        """
        MATCH (ae:AnalysisEvent)-[:EXECUTES]->(m:Method)
        RETURN m.name AS 方法名称, count(ae) AS 使用次数
        ORDER BY 使用次数 DESC
        LIMIT 10
        """,
        "最常用的 10 种方法"
    )
    
    # 5. 统计最常用的数据字段
    run_query(
        """
        MATCH (d:Data)-[:FEEDS_INTO]->(ae:AnalysisEvent)
        RETURN d.name AS 数据字段, count(ae) AS 使用次数
        ORDER BY 使用次数 DESC
        LIMIT 10
        """,
        "最常用的 10 个数据字段"
    )
    
    # 6. 查看结论类型分布
    run_query(
        """
        MATCH (ae:AnalysisEvent)-[:YIELDS]->(c:Conclusion)
        RETURN c.type AS 结论类型, count(ae) AS 数量
        ORDER BY 数量 DESC
        """,
        "结论类型分布"
    )
    
    # 7. 查看某篇论文的完整分析链
    run_query(
        """
        MATCH (p:Paper)-[:CONDUCTS]->(ae:AnalysisEvent)
        WHERE p.title CONTAINS 'Green chasm'
        OPTIONAL MATCH (ae)-[:EXECUTES]->(m:Method)
        RETURN ae.step_id AS 步骤, ae.objective AS 目标, m.name AS 方法
        ORDER BY ae.step_id
        """,
        "'Green chasm' 论文的分析步骤"
    )
    
    print(f"\n{'='*60}")
    print("✓ 查询完成！")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
