"""
测试 strategist_graph.py 模块
"""

import json
from strategist_graph import build_graph, initialize_graph_tool, graph_tool


def test_basic_workflow():
    """测试基本工作流"""
    print("\n" + "="*60)
    print("🧪 测试 1: 基本工作流")
    print("="*60)
    
    # 构建图
    app = build_graph()
    
    # 测试输入
    test_input = {
        "user_goal": "分析固态电池的技术空白",
        "graph_context": "",
        "generated_idea": {},
        "critique": ""
    }
    
    # 执行
    result = app.invoke(test_input)
    
    # 验证结果
    assert "graph_context" in result, "缺少 graph_context"
    assert "generated_idea" in result, "缺少 generated_idea"
    assert len(result["graph_context"]) > 0, "graph_context 为空"
    
    print("\n✅ 测试通过！")
    print(f"  - 检索到的上下文长度: {len(result['graph_context'])} 字符")
    print(f"  - 生成的方案字段: {list(result['generated_idea'].keys())}")
    
    return result


def test_multiple_goals():
    """测试多个研究目标"""
    print("\n" + "="*60)
    print("🧪 测试 2: 多个研究目标")
    print("="*60)
    
    goals = [
        "研究人工智能在专利分析中的应用",
        "探索区块链技术的专利布局策略",
        "分析新能源汽车的技术演进路径"
    ]
    
    app = build_graph()
    results = []
    
    for i, goal in enumerate(goals, 1):
        print(f"\n  [{i}/{len(goals)}] 测试目标: {goal}")
        
        result = app.invoke({
            "user_goal": goal,
            "graph_context": "",
            "generated_idea": {},
            "critique": ""
        })
        
        results.append({
            "goal": goal,
            "idea": result["generated_idea"]
        })
        
        print(f"    ✓ 完成")
    
    # 保存所有结果
    with open("test_strategist_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 测试通过！结果已保存到 test_strategist_results.json")
    
    return results


def test_graph_tool_only():
    """仅测试 GraphTool 的检索功能"""
    print("\n" + "="*60)
    print("🧪 测试 3: GraphTool 检索功能")
    print("="*60)
    
    from strategist_graph import GraphTool
    
    # 创建新的 GraphTool 实例
    tool = GraphTool()
    
    try:
        # 测试最佳实践检索
        print("\n  📚 测试最佳实践检索...")
        best_practices = tool.retrieve_best_practices("patent", limit=3)
        print(f"    ✓ 找到 {len(best_practices)} 个案例")
        
        # 测试研究空白检索
        print("\n  🔬 测试研究空白检索...")
        research_gaps = tool.retrieve_research_gaps(limit=3)
        print(f"    ✓ 找到 {len(research_gaps)} 个空白")
        
        # 测试完整上下文检索
        print("\n  🔍 测试完整上下文检索...")
        context = tool.retrieve_context("分析专利技术")
        print(f"    ✓ 上下文长度: {len(context)} 字符")
        print(f"\n{context[:500]}...")
        
        print("\n✅ 测试通过！")
        
    finally:
        tool.close()


def main():
    """运行所有测试"""
    try:
        # 测试 1: 基本工作流
        result1 = test_basic_workflow()
        
        # 测试 2: GraphTool 单独测试
        test_graph_tool_only()
        
        # 测试 3: 多个目标（可选，耗时较长）
        # test_multiple_goals()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成！")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        if graph_tool:
            graph_tool.close()


if __name__ == "__main__":
    main()
