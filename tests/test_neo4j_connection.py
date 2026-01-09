"""
测试 Neo4j 数据库连接
"""

from neo4j import GraphDatabase


def test_connection(uri: str, user: str, password: str):
    """
    测试 Neo4j 连接是否正常
    
    Args:
        uri: Neo4j 数据库地址
        user: 用户名
        password: 密码
    """
    print("正在测试 Neo4j 连接...")
    print(f"URI: {uri}")
    print(f"User: {user}")
    
    try:
        # 尝试连接
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 执行简单查询
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            record = result.single()
            print(f"\n✓ {record['message']}")
            
            # 获取数据库信息
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"  Neo4j {record['edition']}: {record['versions'][0]}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"\n✗ 连接失败: {type(e).__name__}")
        print(f"  错误信息: {e}")
        print("\n请检查:")
        print("  1. Neo4j 服务是否已启动")
        print("  2. URI 地址是否正确")
        print("  3. 用户名和密码是否正确")
        print("  4. 防火墙是否允许 7687 端口")
        return False


def main():
    """主函数"""
    
    # 尝试从配置文件加载
    try:
        from neo4j_config import NEO4J_CONFIG
        uri = NEO4J_CONFIG["uri"]
        user = NEO4J_CONFIG["user"]
        password = NEO4J_CONFIG["password"]
    except ImportError:
        print("未找到配置文件，使用默认配置")
        uri = "bolt://localhost:7687"
        user = "neo4j"
        password = input("请输入 Neo4j 密码: ")
    
    test_connection(uri, user, password)


if __name__ == "__main__":
    main()
