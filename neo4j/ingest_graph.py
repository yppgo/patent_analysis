"""
生产级 Neo4j 知识图谱入库脚本
Patent-DeepScientist 项目

架构设计:
- 基础设施节点 (全局共享): Intent, Method, Dataset, Data - 使用 MERGE
- 实例节点 (动态创建): Paper, AnalysisEvent, Conclusion - 使用 CREATE
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError


class KnowledgeGraphIngester:
    """知识图谱入库器 - 生产级实现"""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        初始化 Neo4j 连接
        
        Args:
            uri: Neo4j 数据库地址 (例如: bolt://localhost:7687)
            user: 用户名
            password: 密码
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 测试连接
            self.driver.verify_connectivity()
            print("✓ Neo4j 连接成功")
        except AuthError:
            raise Exception("❌ Neo4j 认证失败，请检查用户名和密码")
        except ServiceUnavailable:
            raise Exception("❌ Neo4j 服务不可用，请检查数据库是否启动")
        except Exception as e:
            raise Exception(f"❌ Neo4j 连接失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j 连接已关闭")
    
    def clear_database(self):
        """
        清空数据库中的所有数据
        ⚠️ 警告：此操作不可逆！
        """
        print("\n⚠️  警告：即将清空数据库中的所有数据！")
        confirm = input("确认清空？输入 'YES' 继续: ")
        
        if confirm == "YES":
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("✓ 数据库已清空")
        else:
            print("✗ 操作已取消")
    
    def initialize_schema(self):
        """
        初始化数据库 Schema
        创建唯一性约束，确保全局节点的唯一性
        """
        constraints = [
            "CREATE CONSTRAINT intent_name IF NOT EXISTS FOR (i:Intent) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT method_name IF NOT EXISTS FOR (m:Method) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT dataset_name IF NOT EXISTS FOR (d:Dataset) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT data_name IF NOT EXISTS FOR (dt:Data) REQUIRE dt.name IS UNIQUE",
            "CREATE CONSTRAINT paper_title IF NOT EXISTS FOR (p:Paper) REQUIRE p.title IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  ✓ 约束创建成功: {constraint.split('(')[1].split(')')[0]}")
                except Exception as e:
                    # 约束可能已存在，忽略错误
                    if "already exists" not in str(e).lower():
                        print(f"  ⚠ 约束创建警告: {e}")
        
        print("✓ Schema 初始化完成")
    
    def ingest_paper(self, json_data: Dict[str, Any]) -> bool:
        """
        入库单篇论文的分析数据
        
        Args:
            json_data: 包含 paper_meta, dataset_config 和 analysis_logic_chains 的字典
        
        Returns:
            bool: 入库是否成功
        """
        try:
            paper_meta = json_data.get("paper_meta", {})
            dataset_config = json_data.get("dataset_config", {})
            logic_chains = json_data.get("analysis_logic_chains", [])
            
            paper_title = paper_meta.get("title", "")
            paper_year = paper_meta.get("year", "")
            
            if not paper_title:
                print("  ⚠ 警告: 论文标题为空，跳过")
                return False
            
            with self.driver.session() as session:
                # 1. 创建/锁定 Paper 节点
                session.execute_write(
                    self._create_paper_node,
                    paper_title,
                    paper_year
                )
                
                # 2. 处理 Dataset 关系
                if dataset_config:
                    dataset_source = dataset_config.get("source", "")
                    if dataset_source:
                        session.execute_write(
                            self._link_paper_to_dataset,
                            paper_title,
                            dataset_source,
                            dataset_config
                        )
                
                # 3. 处理每个分析步骤
                for step in logic_chains:
                    session.execute_write(
                        self._ingest_analysis_step,
                        paper_title,
                        step
                    )
            
            print(f"  ✓ 成功入库: {paper_title[:60]}...")
            return True
            
        except Exception as e:
            print(f"  ✗ 入库失败: {e}")
            return False
    
    @staticmethod
    def _create_paper_node(tx, title: str, year: str):
        """
        创建 Paper 节点 (使用 MERGE 避免重复)
        
        Args:
            tx: Neo4j 事务
            title: 论文标题
            year: 发表年份
        """
        query = """
        MERGE (p:Paper {title: $title})
        ON CREATE SET 
            p.year = $year,
            p.created_at = datetime()
        ON MATCH SET
            p.updated_at = datetime()
        RETURN p
        """
        tx.run(query, title=title, year=year)
    
    @staticmethod
    def _link_paper_to_dataset(tx, paper_title: str, dataset_source: str, dataset_config: Dict):
        """
        连接 Paper 到全局 Dataset 节点
        
        Args:
            tx: Neo4j 事务
            paper_title: 论文标题
            dataset_source: 数据集来源 (例如: USPTO, EPO)
            dataset_config: 数据集配置信息
        """
        query = """
        MATCH (p:Paper {title: $paper_title})
        MERGE (d:Dataset {name: $dataset_source})
        ON CREATE SET
            d.created_at = datetime()
        MERGE (p)-[r:USES_DATASET]->(d)
        ON CREATE SET
            r.dataset_id = $dataset_id,
            r.query_condition = $query_condition,
            r.size = $size,
            r.time_range = $time_range,
            r.preprocessing = $preprocessing,
            r.notes = $notes,
            r.created_at = datetime()
        """
        tx.run(
            query,
            paper_title=paper_title,
            dataset_source=dataset_source,
            dataset_id=dataset_config.get("dataset_id", ""),
            query_condition=dataset_config.get("query_condition", ""),
            size=dataset_config.get("size", ""),
            time_range=dataset_config.get("time_range", ""),
            preprocessing=dataset_config.get("preprocessing", ""),
            notes=dataset_config.get("notes", "")
        )
    
    @staticmethod
    def _ingest_analysis_step(tx, paper_title: str, step: Dict):
        """
        入库单个分析步骤 (核心逻辑)
        
        架构:
        1. 锁定 Paper 节点
        2. 锁定全局基础设施节点 (Intent, Method, Dataset)
        3. 创建动态实例节点 (AnalysisEvent, Conclusion)
        4. 建立关系链
        5. 处理 Data 节点列表 (使用 UNWIND)
        
        Args:
            tx: Neo4j 事务
            paper_title: 论文标题
            step: 分析步骤字典
        """
        # 提取步骤信息
        step_id = step.get("step_id", 0)
        objective = step.get("objective", "")
        standardized_intent = step.get("standardized_intent", "")
        method_name = step.get("method_name", "")
        derived_conclusion = step.get("derived_conclusion", "")
        
        # 提取配置和指标 (转为 JSON 字符串)
        implementation_config = step.get("implementation_config", {})
        config_json = json.dumps(implementation_config, ensure_ascii=False)
        
        evaluation_metrics = step.get("evaluation_metrics", [])
        metrics_json = json.dumps(evaluation_metrics, ensure_ascii=False)
        
        # 提取输入数据列表
        inputs = step.get("inputs", [])
        if not isinstance(inputs, list):
            inputs = []
        
        # 主 Cypher 查询 - 原子操作
        query = """
        // 1. 锁定 Paper 节点
        MATCH (p:Paper {title: $paper_title})
        
        // 2. 锁定全局基础设施节点 (The Fixed Infrastructure)
        MERGE (i:Intent {name: $intent_name})
        ON CREATE SET i.created_at = datetime()
        
        MERGE (m:Method {name: $method_name})
        ON CREATE SET m.created_at = datetime()
        
        // 3. 创建动态实例节点 (AnalysisEvent)
        CREATE (e:AnalysisEvent {
            step_id: $step_id,
            objective: $objective,
            config: $config,
            metrics: $metrics,
            success_confidence: $success_confidence,
            created_at: datetime()
        })
        
        // 4. 创建 Conclusion 节点
        CREATE (c:Conclusion {
            text: $conclusion_text,
            created_at: datetime()
        })
        
        // 5. 建立关系链
        MERGE (p)-[:CONTAINS_EVENT]->(e)
        MERGE (e)-[:TARGETS_INTENT]->(i)
        MERGE (e)-[:USES_METHOD]->(m)
        MERGE (e)-[:PRODUCED_CONCLUSION]->(c)
        MERGE (c)-[:ADDRESSES_INTENT]->(i)
        
        // 6. 处理 Data 节点列表 (使用 FOREACH + MERGE)
        FOREACH (input_name IN $input_list |
            MERGE (dt:Data {name: input_name})
            ON CREATE SET dt.created_at = datetime()
            MERGE (e)-[:REQUIRES_INPUT]->(dt)
        )
        
        RETURN e, c
        """
        
        # 执行查询
        tx.run(
            query,
            paper_title=paper_title,
            step_id=step_id,
            objective=objective,
            intent_name=standardized_intent if standardized_intent else "未分类意图",
            method_name=method_name if method_name else "未指定方法",
            config=config_json,
            metrics=metrics_json,
            success_confidence=step.get("success_confidence", 0.0),
            conclusion_text=derived_conclusion if derived_conclusion else "无结论",
            input_list=inputs  # 传递列表给 FOREACH
        )
    
    def batch_ingest_from_folder(self, folder_path: str, pattern: str = "*_analysis_result.json") -> Dict[str, int]:
        """
        批量入库文件夹中的所有 JSON 文件
        
        Args:
            folder_path: 文件夹路径
            pattern: 文件匹配模式 (默认: *_analysis_result.json)
        
        Returns:
            Dict: 统计信息 {"success": 成功数, "failed": 失败数, "total": 总数}
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")
        
        # 获取所有匹配的 JSON 文件
        json_files = list(folder.glob(pattern))
        
        if not json_files:
            print(f"⚠ 警告: 在 {folder_path} 中没有找到匹配 '{pattern}' 的文件")
            return {"success": 0, "failed": 0, "total": 0}
        
        print(f"\n{'='*70}")
        print(f"开始批量入库: 找到 {len(json_files)} 个文件")
        print(f"{'='*70}\n")
        
        success_count = 0
        failed_count = 0
        
        for idx, json_file in enumerate(json_files, 1):
            print(f"[{idx}/{len(json_files)}] 处理: {json_file.name[:60]}...")
            
            try:
                # 读取 JSON 文件
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 入库
                if self.ingest_paper(data):
                    success_count += 1
                else:
                    failed_count += 1
                    
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON 解析错误: {e}")
                failed_count += 1
            except Exception as e:
                print(f"  ✗ 处理失败: {type(e).__name__}: {e}")
                failed_count += 1
        
        # 输出统计信息
        print(f"\n{'='*70}")
        print(f"批量入库完成!")
        print(f"  ✓ 成功: {success_count} 个文件")
        print(f"  ✗ 失败: {failed_count} 个文件")
        print(f"  总计: {len(json_files)} 个文件")
        print(f"{'='*70}\n")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(json_files)
        }


def main():
    """主函数 - 批量入库 50 条数据"""
    
    import sys
    
    # 从配置文件加载
    try:
        from neo4j_config import NEO4J_CONFIG
        uri = NEO4J_CONFIG["uri"]
        user = NEO4J_CONFIG["user"]
        password = NEO4J_CONFIG["password"]
    except ImportError:
        print("⚠ 警告: 未找到 neo4j_config.py，使用默认配置")
        uri = "bolt://localhost:7687"
        user = "neo4j"
        password = "12345678"
    
    # 批量入库文件夹
    batch_folder = "batch_50_results"
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  Patent-DeepScientist 知识图谱入库工具 v1.0                      ║
║  生产级 Neo4j 批量入库脚本                                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # 创建入库器
    ingester = None
    try:
        ingester = KnowledgeGraphIngester(uri, user, password)
        
        # 检查是否需要清空数据库
        if "--clear" in sys.argv:
            ingester.clear_database()
        
        # 初始化 Schema
        print("\n[步骤 1/2] 初始化数据库 Schema...")
        ingester.initialize_schema()
        
        # 批量入库
        print(f"\n[步骤 2/2] 批量入库数据...")
        stats = ingester.batch_ingest_from_folder(batch_folder)
        
        # 显示最终统计
        if stats["success"] > 0:
            print(f"\n🎉 入库成功! 共导入 {stats['success']} 篇论文的分析数据到知识图谱")
        
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
    finally:
        if ingester:
            ingester.close()


if __name__ == "__main__":
    main()
