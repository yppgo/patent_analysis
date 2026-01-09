"""
Neo4j 连接器
封装知识图谱的查询操作
"""

import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnector:
    """Neo4j 知识图谱连接器"""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        初始化 Neo4j 连接
        
        Args:
            uri: Neo4j URI（可选，默认从环境变量读取）
            user: 用户名（可选，默认从环境变量读取）
            password: 密码（可选，默认从环境变量读取）
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        
        if not self.password:
            raise ValueError("请设置 NEO4J_PASSWORD 环境变量或传入 password 参数")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        """关闭连接"""
        self.driver.close()
    
    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        执行 Cypher 查询
        
        Args:
            query: Cypher 查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def retrieve_best_practices(self, keyword: str, limit: int = 3) -> List[Dict]:
        """
        检索最佳实践案例
        
        Args:
            keyword: 检索关键词
            limit: 返回数量限制
            
        Returns:
            最佳实践案例列表
        """
        query = """
        MATCH (p:Paper)-[:CONDUCTS]->(target_ae:AnalysisEvent)
        WHERE target_ae.objective CONTAINS $keyword 
           OR p.title CONTAINS $keyword
           OR target_ae.method_name CONTAINS $keyword
        
        WITH DISTINCT p
        MATCH (p)-[:CONDUCTS]->(all_ae:AnalysisEvent)
        
        OPTIONAL MATCH (all_ae)-[:EXECUTES]->(m:Method)
        OPTIONAL MATCH (all_ae)-[:YIELDS]->(c:Conclusion)
        OPTIONAL MATCH (d:Data)-[:FEEDS_INTO]->(all_ae)
        
        WITH p, all_ae, m, c, collect(DISTINCT d.name) AS data_fields
        ORDER BY all_ae.step_id ASC
        
        RETURN 
            p.title AS paper_title,
            p.year AS paper_year,
            collect({
                step_id: all_ae.step_id,
                objective: all_ae.objective,
                method_name: all_ae.method_name,
                method: m.name,
                config: all_ae.config,
                metrics: all_ae.metrics,
                inputs: data_fields,
                conclusion_type: c.type,
                conclusion: c.content
            }) AS full_logic_chain
        ORDER BY p.year DESC
        LIMIT $limit
        """
        
        return self.run_query(query, {"keyword": keyword, "limit": limit})
    
    @classmethod
    def from_config(cls, config: Dict[str, str]) -> 'Neo4jConnector':
        """
        从配置字典创建连接器
        
        Args:
            config: 包含 uri, user, password 的字典
            
        Returns:
            Neo4jConnector 实例
        """
        return cls(
            uri=config['uri'],
            user=config['user'],
            password=config['password']
        )

    
    def retrieve_best_practices(self, keyword: str, limit: int = 3) -> List[Dict]:
        """
        检索最佳实践案例
        
        V4.1 优化：全链检索 (Full Logic Chain Retrieval)
        一旦某篇论文的某个步骤命中了关键词，就返回该论文的【完整分析逻辑链】。
        
        Args:
            keyword: 检索关键词
            limit: 返回结果数量限制
            
        Returns:
            案例列表，每个案例包含完整的分析逻辑链
        """
        query = """
        // 1. 锚定：先找到包含关键词的那个具体步骤，锁定对应的论文
        // 使用 toLower 进行不区分大小写的匹配
        MATCH (p:Paper)-[:CONDUCTS]->(target_ae:AnalysisEvent)
        WHERE toLower(target_ae.objective) CONTAINS toLower($keyword)
           OR toLower(p.title) CONTAINS toLower($keyword)
           OR toLower(coalesce(target_ae.notes, '')) CONTAINS toLower($keyword)
        
        // 2. 扩展：基于找到的论文，把它所有的步骤都找出来
        WITH DISTINCT p
        MATCH (p)-[:CONDUCTS]->(all_ae:AnalysisEvent)
        
        // 3. 关联：获取每个步骤的详细信息（方法、数据）
        OPTIONAL MATCH (all_ae)-[:EXECUTES]->(m:Method)
        OPTIONAL MATCH (d:Data)-[:FEEDS_INTO]->(all_ae)
        
        // 4. 聚合：按 step_id 排序，重组为完整的 Story
        WITH p, all_ae, m, collect(DISTINCT d.name) AS data_fields
        ORDER BY all_ae.step_id ASC
        
        // 5. 返回结构化数据：一篇论文一行，包含一个 steps 数组
        RETURN 
            p.title AS paper_title,
            p.year AS paper_year,
            collect({
                step_id: all_ae.step_id,
                objective: all_ae.objective,
                method: m.name,
                config: all_ae.config,
                metrics: all_ae.metrics,
                inputs: data_fields,
                notes: all_ae.notes
            }) AS full_logic_chain
        ORDER BY p.year DESC
        LIMIT $limit
        """
        
        return self.run_query(query, {"keyword": keyword, "limit": limit})
