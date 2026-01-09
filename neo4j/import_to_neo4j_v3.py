"""
专利分析逻辑链导入 Neo4j 脚本 - V3.1
✨ 支持全局 Dataset 节点
"""

import json
from neo4j import GraphDatabase
from typing import Dict, List, Any


class PatentAnalysisImporterV3:
    """专利分析数据导入器 V3.1 - 支持全局 Dataset 节点"""
    
    def __init__(self, uri: str, user: str, password: str):
        """初始化 Neo4j 连接"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._initialize_global_datasets()
    
    def close(self):
        """关闭数据库连接"""
        self.driver.close()
    
    def _initialize_global_datasets(self):
        """初始化全局 Dataset 节点（如果不存在）"""
        global_datasets = [
            {
                "name": "USPTO", 
                "full_name": "United States Patent and Trademark Office", 
                "type": "Patent Database",
                "url": "https://www.uspto.gov",
                "api_endpoint": "https://developer.uspto.gov/api-catalog",
                "access_method": "API / Web Interface"
            },
            {
                "name": "EPO", 
                "full_name": "European Patent Office", 
                "type": "Patent Database",
                "url": "https://www.epo.org",
                "api_endpoint": "https://ops.epo.org",
                "access_method": "OPS API"
            },
            {
                "name": "JPO", 
                "full_name": "Japan Patent Office", 
                "type": "Patent Database",
                "url": "https://www.jpo.go.jp",
                "api_endpoint": "https://www.j-platpat.inpit.go.jp",
                "access_method": "J-PlatPat"
            },
            {
                "name": "CNIPA", 
                "full_name": "China National Intellectual Property Administration", 
                "type": "Patent Database",
                "url": "https://www.cnipa.gov.cn",
                "api_endpoint": "http://epub.cnipa.gov.cn",
                "access_method": "Web Interface"
            },
            {
                "name": "WIPO", 
                "full_name": "World Intellectual Property Organization", 
                "type": "Patent Database",
                "url": "https://www.wipo.int",
                "api_endpoint": "https://patentscope.wipo.int",
                "access_method": "PATENTSCOPE"
            },
            {
                "name": "Derwent Innovation Index", 
                "full_name": "Derwent Innovation Index", 
                "type": "Patent Database",
                "url": "https://clarivate.com/derwent",
                "api_endpoint": "Subscription Required",
                "access_method": "Commercial Platform"
            },
            {
                "name": "Google Patents", 
                "full_name": "Google Patents", 
                "type": "Patent Database",
                "url": "https://patents.google.com",
                "api_endpoint": "https://patents.google.com",
                "access_method": "Web Scraping / BigQuery"
            },
            {
                "name": "PatSnap", 
                "full_name": "PatSnap", 
                "type": "Patent Database",
                "url": "https://www.patsnap.com",
                "api_endpoint": "Subscription Required",
                "access_method": "Commercial API"
            },
            {
                "name": "Orbit Intelligence", 
                "full_name": "Orbit Intelligence", 
                "type": "Patent Database",
                "url": "https://www.questel.com",
                "api_endpoint": "Subscription Required",
                "access_method": "Commercial Platform"
            },
            {
                "name": "Web of Science", 
                "full_name": "Clarivate Web of Science", 
                "type": "Scientific Literature Database",
                "url": "https://www.webofscience.com",
                "api_endpoint": "https://developer.clarivate.com/apis/wos",
                "access_method": "WoS API"
            },
            {
                "name": "Scopus", 
                "full_name": "Elsevier Scopus", 
                "type": "Scientific Literature Database",
                "url": "https://www.scopus.com",
                "api_endpoint": "https://dev.elsevier.com/scopus.html",
                "access_method": "Scopus API"
            },
            {
                "name": "PubMed", 
                "full_name": "PubMed", 
                "type": "Scientific Literature Database",
                "url": "https://pubmed.ncbi.nlm.nih.gov",
                "api_endpoint": "https://www.ncbi.nlm.nih.gov/home/develop/api/",
                "access_method": "E-utilities API"
            },
            {
                "name": "arXiv", 
                "full_name": "arXiv", 
                "type": "Preprint Repository",
                "url": "https://arxiv.org",
                "api_endpoint": "https://arxiv.org/help/api",
                "access_method": "arXiv API"
            },
        ]
        
        with self.driver.session() as session:
            for dataset in global_datasets:
                session.execute_write(self._create_global_dataset, dataset)
    
    @staticmethod
    def _create_global_dataset(tx, dataset: Dict):
        """创建全局 Dataset 节点（如果不存在）"""
        query = """
        MERGE (d:Dataset {name: $name})
        ON CREATE SET 
            d.full_name = $full_name,
            d.type = $type,
            d.url = $url,
            d.api_endpoint = $api_endpoint,
            d.access_method = $access_method,
            d.created_at = datetime()
        """
        tx.run(query, 
               name=dataset["name"],
               full_name=dataset["full_name"],
               type=dataset["type"],
               url=dataset["url"],
               api_endpoint=dataset["api_endpoint"],
               access_method=dataset["access_method"])
    
    def import_analysis_data(self, json_data: Dict[str, Any]):
        """
        导入完整的分析数据到 Neo4j
        
        Args:
            json_data: 包含 paper_meta, dataset_config 和 analysis_logic_chains 的字典
        """
        paper_meta = json_data.get("paper_meta", {})
        dataset_config = json_data.get("dataset_config", {})
        logic_chains = json_data.get("analysis_logic_chains", [])
        
        with self.driver.session() as session:
            # 1. 创建 Paper 节点
            paper_title = paper_meta.get("title", "")
            paper_year = paper_meta.get("year", "")
            session.execute_write(self._create_paper, paper_title, paper_year)
            
            # 2. 连接 Paper 到 Dataset（如果有 dataset_config）
            if dataset_config:
                dataset_id = dataset_config.get("dataset_id", "")
                if dataset_id:
                    session.execute_write(
                        self._link_paper_to_dataset,
                        paper_title,
                        dataset_id,
                        json.dumps(dataset_config, ensure_ascii=False)
                    )
            
            # 3. 遍历每个分析步骤
            for step in logic_chains:
                session.execute_write(
                    self._create_analysis_event_with_relations,
                    paper_title,
                    step
                )
    
    @staticmethod
    def _create_paper(tx, title: str, year: str):
        """创建 Paper 节点"""
        query = """
        MERGE (p:Paper {title: $title})
        ON CREATE SET p.year = $year
        """
        tx.run(query, title=title, year=year)
    
    @staticmethod
    def _link_paper_to_dataset(tx, paper_title: str, dataset_id: str, dataset_config_json: str):
        """连接 Paper 到全局 Dataset 节点"""
        query = """
        MATCH (p:Paper {title: $paper_title})
        MATCH (d:Dataset)
        WHERE d.name = $dataset_id OR d.name CONTAINS $dataset_id
        MERGE (p)-[r:USES]->(d)
        ON CREATE SET r.config = $dataset_config
        """
        tx.run(query,
               paper_title=paper_title,
               dataset_id=dataset_id,
               dataset_config=dataset_config_json)
    
    @staticmethod
    def _create_analysis_event_with_relations(tx, paper_title: str, step: Dict):
        """创建 AnalysisEvent 节点及其关系"""
        
        # 提取步骤信息
        step_id = step.get("step_id", 0)
        objective = step.get("objective", "")
        method_name = step.get("method_name", "")
        derived_conclusion = step.get("derived_conclusion", "")
        
        # dataset_config 已经在 Paper 层面处理，这里不再需要
        
        # 提取 method_config
        method_config = step.get("method_config", {})
        method_config_json = json.dumps(method_config, ensure_ascii=False)
        
        # 提取 evaluation_metrics
        metrics = step.get("evaluation_metrics", [])
        metrics_json = json.dumps(metrics, ensure_ascii=False)
        
        # 1. 创建 AnalysisEvent 节点
        query_ae = """
        MATCH (p:Paper {title: $paper_title})
        CREATE (ae:AnalysisEvent {
            step_id: $step_id,
            objective: $objective,
            method_name: $method_name,
            config: $method_config,
            metrics: $metrics,
            derived_conclusion: $derived_conclusion
        })
        CREATE (p)-[:CONDUCTS]->(ae)
        RETURN ae
        """
        
        result = tx.run(query_ae,
                       paper_title=paper_title,
                       step_id=step_id,
                       objective=objective,
                       method_name=method_name,
                       method_config=method_config_json,
                       metrics=metrics_json,
                       derived_conclusion=derived_conclusion)
        
        # 3. 创建 Method 节点并建立关系
        if method_name:
            query_method = """
            MATCH (ae:AnalysisEvent)
            WHERE ae.step_id = $step_id AND ae.objective = $objective
            MERGE (m:Method {name: $method_name})
            MERGE (ae)-[:EXECUTES]->(m)
            """
            tx.run(query_method,
                   step_id=step_id,
                   objective=objective,
                   method_name=method_name)
        
        # 4. 创建 Data 节点并建立关系
        data_fields = step.get("data_fields_used", [])
        for field in data_fields:
            query_data = """
            MATCH (ae:AnalysisEvent)
            WHERE ae.step_id = $step_id AND ae.objective = $objective
            MERGE (d:Data {name: $field})
            MERGE (d)-[:FEEDS_INTO]->(ae)
            """
            tx.run(query_data,
                   step_id=step_id,
                   objective=objective,
                   field=field)
        
        # 5. 创建 Conclusion 节点并建立关系
        if derived_conclusion:
            query_conclusion = """
            MATCH (ae:AnalysisEvent)
            WHERE ae.step_id = $step_id AND ae.objective = $objective
            CREATE (c:Conclusion {
                content: $conclusion,
                type: $conclusion_type
            })
            CREATE (ae)-[:YIELDS]->(c)
            """
            # 简单分类结论类型
            conclusion_type = "General"
            if "空白" in derived_conclusion or "gap" in derived_conclusion.lower():
                conclusion_type = "技术空白（已识别）"
            elif "趋势" in derived_conclusion or "trend" in derived_conclusion.lower():
                conclusion_type = "技术趋势"
            elif "有效" in derived_conclusion or "effective" in derived_conclusion.lower():
                conclusion_type = "方法有效性（已验证）"
            
            tx.run(query_conclusion,
                   step_id=step_id,
                   objective=objective,
                   conclusion=derived_conclusion,
                   conclusion_type=conclusion_type)


def import_from_json_file(json_file_path: str, uri: str, user: str, password: str):
    """
    从 JSON 文件导入数据到 Neo4j
    
    Args:
        json_file_path: JSON 文件路径
        uri: Neo4j 数据库地址
        user: 用户名
        password: 密码
    """
    # 读取 JSON 文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 创建导入器并导入数据
    importer = PatentAnalysisImporterV3(uri, user, password)
    try:
        importer.import_analysis_data(json_data)
        print(f"✓ 成功导入: {json_file_path}")
    except Exception as e:
        print(f"✗ 导入失败: {json_file_path}")
        print(f"  错误: {e}")
    finally:
        importer.close()


if __name__ == "__main__":
    # 示例用法
    from neo4j_config import NEO4J_CONFIG
    
    # 测试导入单个文件
    json_file = "strategist_output.json"
    
    import_from_json_file(
        json_file,
        NEO4J_CONFIG["uri"],
        NEO4J_CONFIG["user"],
        NEO4J_CONFIG["password"]
    )
