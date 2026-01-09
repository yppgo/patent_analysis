"""
批量导入专利分析数据到 Neo4j
处理整个文件夹中的所有 JSON 文件
"""

import json
import os
from pathlib import Path
from import_to_neo4j import PatentAnalysisImporter


def batch_import_from_folder(folder_path: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
    """
    批量导入文件夹中的所有 JSON 文件
    
    Args:
        folder_path: 包含 JSON 文件的文件夹路径
        neo4j_uri: Neo4j 数据库地址
        neo4j_user: 用户名
        neo4j_password: 密码
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"错误: 文件夹不存在 - {folder_path}")
        return
    
    # 获取所有 JSON 文件
    json_files = list(folder.glob("*_analysis_result.json"))
    
    if not json_files:
        print(f"警告: 在 {folder_path} 中没有找到 JSON 文件")
        return
    
    print(f"找到 {len(json_files)} 个 JSON 文件")
    print("=" * 60)
    
    # 创建导入器
    importer = PatentAnalysisImporter(neo4j_uri, neo4j_user, neo4j_password)
    
    success_count = 0
    error_count = 0
    
    try:
        for idx, json_file in enumerate(json_files, 1):
            try:
                print(f"\n[{idx}/{len(json_files)}] 处理: {json_file.name}")
                
                # 读取 JSON 文件
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 导入数据
                importer.import_analysis_data(data)
                success_count += 1
                
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON 解析错误: {e}")
                error_count += 1
            except Exception as e:
                print(f"  ✗ 导入失败: {type(e).__name__}: {e}")
                error_count += 1
    
    finally:
        # 关闭连接
        importer.close()
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print(f"导入完成!")
    print(f"  成功: {success_count} 个文件")
    print(f"  失败: {error_count} 个文件")
    print(f"  总计: {len(json_files)} 个文件")


def main():
    """主函数"""
    
    # 尝试从配置文件加载，否则使用默认值
    try:
        from neo4j_config import NEO4J_CONFIG, DATA_CONFIG
        NEO4J_URI = NEO4J_CONFIG["uri"]
        NEO4J_USER = NEO4J_CONFIG["user"]
        NEO4J_PASSWORD = NEO4J_CONFIG["password"]
        BATCH_FOLDER = DATA_CONFIG["batch_folder"]
    except ImportError:
        # 如果配置文件不存在，使用默认值
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "your_password"  # 请修改为你的密码
        BATCH_FOLDER = "batch_50_results"
    
    print("批量导入专利分析数据到 Neo4j")
    print("=" * 60)
    
    batch_import_from_folder(
        folder_path=BATCH_FOLDER,
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD
    )


if __name__ == "__main__":
    main()
