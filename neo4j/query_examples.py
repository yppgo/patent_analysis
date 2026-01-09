"""
知识图谱查询示例
提供常用的 Cypher 查询示例
"""

from neo4j import GraphDatabase
from neo4j_config import NEO4J_CONFIG
import json


class KnowledgeGraphQuery:
    """知识图谱查询工具"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"],
            auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
        )
    
    def close(self):
        self.driver.close()
    
    def query_1_papers_by_intent(self, intent_name: str):
        """查询使用特定意图的所有论文"""
        print(f"\n📋 查询 1: 使用意图 '{intent_name}' 的论文")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:CONTAINS_EVENT]->(e:AnalysisEvent)-[:TARGETS_INTENT]->(i:Intent {name: $intent})
                RETURN DISTINCT p.title as title, p.year as year
                ORDER BY p.year DESC
            """, intent=intent_name)
            
            papers = list(result)
            print(f"找到 {len(papers)} 篇论文:\n")
            for idx, record in enumerate(papers, 1):
                print(f"{idx:2d}. [{record['year']}] {record['title'][:70]}...")
    
    def query_2_method_combinations(self):
        """查询常见的方法组合（同一篇论文中使用的多个方法）"""
        print(f"\n🔬 查询 2: 常见的方法组合")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:CONTAINS_EVENT]->(e:AnalysisEvent)-[:USES_METHOD]->(m:Method)
                WITH p, collect(DISTINCT m.name) as methods
                WHERE size(methods) > 1
                RETURN methods, count(p) as paper_count
                ORDER BY paper_count DESC
                LIMIT 10
            """)
            
            for idx, record in enumerate(result, 1):
                methods = record['methods']
                count = record['paper_count']
                print(f"\n{idx}. 使用次数: {count}")
                for method in methods:
                    print(f"   - {method}")
    
    def query_3_intent_method_matrix(self):
        """查询意图-方法关联矩阵"""
        print(f"\n🎯 查询 3: 意图-方法关联矩阵 (Top 5 意图 × Top 5 方法)")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Intent)<-[:TARGETS_INTENT]-(e:AnalysisEvent)-[:USES_METHOD]->(m:Method)
                RETURN i.name as intent, m.name as method, count(*) as count
                ORDER BY count DESC
                LIMIT 20
            """)
            
            print(f"\n{'意图':<40s} | {'方法':<40s} | 次数")
            print("-" * 100)
            for record in result:
                print(f"{record['intent']:<40s} | {record['method']:<40s} | {record['count']:3d}")
    
    def query_4_data_input_patterns(self):
        """查询输入数据的使用模式"""
        print(f"\n📊 查询 4: 不同意图下的常用输入数据")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Intent)<-[:TARGETS_INTENT]-(e:AnalysisEvent)-[:REQUIRES_INPUT]->(d:Data)
                WITH i.name as intent, d.name as data_type, count(*) as usage_count
                ORDER BY intent, usage_count DESC
                RETURN intent, collect({data: data_type, count: usage_count})[0..5] as top_data
            """)
            
            for record in result:
                intent = record['intent']
                top_data = record['top_data']
                print(f"\n{intent}:")
                for item in top_data:
                    print(f"  - {item['data']}: {item['count']} 次")
    
    def query_5_paper_analysis_depth(self):
        """查询论文的分析深度（分析步骤数量）"""
        print(f"\n📈 查询 5: 论文分析深度分布")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:CONTAINS_EVENT]->(e:AnalysisEvent)
                WITH p, count(e) as step_count
                RETURN step_count, count(p) as paper_count
                ORDER BY step_count
            """)
            
            print(f"\n{'分析步骤数':<15s} | {'论文数量':<10s} | 分布")
            print("-" * 60)
            for record in result:
                steps = record['step_count']
                count = record['paper_count']
                bar = "█" * count
                print(f"{steps:<15d} | {count:<10d} | {bar}")
    
    def query_6_dataset_method_preference(self):
        """查询不同数据集偏好使用的方法"""
        print(f"\n💾 查询 6: 不同数据集常用的分析方法")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Dataset)<-[:USES_DATASET]-(p:Paper)-[:CONTAINS_EVENT]->(e:AnalysisEvent)-[:USES_METHOD]->(m:Method)
                WITH d.name as dataset, m.name as method, count(*) as usage_count
                ORDER BY dataset, usage_count DESC
                RETURN dataset, collect({method: method, count: usage_count})[0..3] as top_methods
            """)
            
            for record in result:
                dataset = record['dataset']
                top_methods = record['top_methods']
                if top_methods:
                    print(f"\n{dataset}:")
                    for item in top_methods:
                        print(f"  - {item['method']}: {item['count']} 次")
    
    def query_7_conclusion_types(self):
        """查询结论类型分布"""
        print(f"\n💡 查询 7: 结论关键词分析")
        print("-" * 70)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Conclusion)
                RETURN c.text as conclusion
            """)
            
            # 简单的关键词统计
            keywords = {
                "趋势": 0,
                "空白": 0,
                "有效": 0,
                "验证": 0,
                "识别": 0,
                "评估": 0,
                "分析": 0,
                "预测": 0
            }
            
            total = 0
            for record in result:
                conclusion = record['conclusion']
                total += 1
                for keyword in keywords:
                    if keyword in conclusion:
                        keywords[keyword] += 1
            
            print(f"\n总结论数: {total}")
            print(f"\n关键词出现频率:")
            for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                bar = "█" * int(percentage / 2)
                print(f"  {keyword:<10s}: {count:3d} 次 ({percentage:5.1f}%) {bar}")
    
    def query_8_find_similar_papers(self, paper_title: str):
        """查找与指定论文相似的论文（基于意图和方法）"""
        print(f"\n🔍 查询 8: 查找相似论文")
        print("-" * 70)
        print(f"参考论文: {paper_title[:60]}...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p1:Paper {title: $title})-[:CONTAINS_EVENT]->(e1:AnalysisEvent)
                MATCH (e1)-[:TARGETS_INTENT]->(i:Intent)
                MATCH (e1)-[:USES_METHOD]->(m:Method)
                
                MATCH (p2:Paper)-[:CONTAINS_EVENT]->(e2:AnalysisEvent)
                WHERE p2 <> p1
                MATCH (e2)-[:TARGETS_INTENT]->(i)
                MATCH (e2)-[:USES_METHOD]->(m)
                
                WITH p2, count(DISTINCT i) + count(DISTINCT m) as similarity_score
                RETURN p2.title as title, p2.year as year, similarity_score
                ORDER BY similarity_score DESC
                LIMIT 5
            """, title=paper_title)
            
            print(f"\n相似论文 (按相似度排序):\n")
            for idx, record in enumerate(result, 1):
                print(f"{idx}. [{record['year']}] {record['title'][:60]}...")
                print(f"   相似度得分: {record['similarity_score']}")


def main():
    """运行示例查询"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  知识图谱查询示例                                                 ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    query_tool = KnowledgeGraphQuery()
    
    try:
        # 运行各种查询
        query_tool.query_1_papers_by_intent("技术趋势分析 (Trend Analysis)")
        query_tool.query_2_method_combinations()
        query_tool.query_3_intent_method_matrix()
        query_tool.query_4_data_input_patterns()
        query_tool.query_5_paper_analysis_depth()
        query_tool.query_6_dataset_method_preference()
        query_tool.query_7_conclusion_types()
        
        # 查找相似论文
        query_tool.query_8_find_similar_papers(
            "A Trend Analysis Method for IoT Technologies Using Patent Dataset with Goal and Approach Concepts"
        )
        
        print("\n" + "="*70)
        print("✓ 所有查询完成")
        print("="*70 + "\n")
        
    finally:
        query_tool.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
