"""
测试 V4.1 全链检索功能
"""

from strategist_graph import GraphTool
import json

def test_full_chain_retrieval():
    """测试完整逻辑链检索"""
    print("\n" + "="*60)
    print("🧪 测试 V4.1 全链检索 (Full Logic Chain)")
    print("="*60)
    
    tool = GraphTool()
    
    # 测试检索
    keyword = "技术"
    print(f"\n🔍 检索关键词: {keyword}")
    results = tool.retrieve_best_practices(keyword, limit=2)
    
    print(f"\n✓ 检索到 {len(results)} 篇论文")
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"论文 {i}: {result.get('paper_title', 'N/A')}")
        print(f"年份: {result.get('paper_year', 'N/A')}")
        
        logic_chain = result.get('full_logic_chain', [])
        print(f"\n完整逻辑链: {len(logic_chain)} 个步骤")
        
        for step in logic_chain:
            print(f"\n  【Step {step.get('step_id', '?')}】")
            print(f"    目标: {step.get('objective', 'N/A')[:80]}...")
            print(f"    方法: {step.get('method', 'N/A')}")
            
            if step.get('config'):
                config_str = str(step.get('config'))[:100]
                print(f"    配置: {config_str}...")
            
            if step.get('metrics'):
                print(f"    指标: {step.get('metrics')}")
            
            inputs = step.get('inputs', [])
            if inputs:
                print(f"    输入: {', '.join(inputs[:3])}...")
    
    tool.close()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    test_full_chain_retrieval()
