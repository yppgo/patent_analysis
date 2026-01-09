"""
Neo4j 数据库配置文件
请根据你的实际环境修改这些配置
"""

# Neo4j 连接配置
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",  # Neo4j 数据库地址
    "user": "neo4j",                 # 用户名
    "password": "12345678"           # 密码
}

# 数据文件路径配置
DATA_CONFIG = {
    "single_file": "batch_50_results/'Green chasm' in clean-tech for air pollution_ Patent evidence of a long innovation cycle and a technological level gap_analysis_result.json",
    "batch_folder": "batch_50_results"
}
