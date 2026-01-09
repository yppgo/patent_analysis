"""
完整系统测试 - 使用真实数据
测试 4 Agent 协作流程：Strategist → Methodologist → CodingAgent → Reviewer
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 添加 src 到路径
sys.path.insert(0, 'src')

from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent
from src.agents.coding_agent_v4_2 import CodingAgentV4_2  # 升级到 V4.2（终端增强版）
from src.agents.reviewer import ReviewerAgent
from src.utils.llm_client import get_llm_client
from src.utils.neo4j_connector import Neo4jConnector
from src.core.workflow import build_full_workflow


def load_test_data():
    """加载测试数据"""
    print("\n📊 加载测试数据...")
    
    data_file = "data/clean_patents1_with_topics_filled.xlsx"
    
    try:
        # 读取 'clear' sheet
        df = pd.read_excel(data_file, sheet_name='clear')
        print(f"   ✅ 成功加载: {len(df)} 条专利数据 (来自 'clear' sheet)")
        print(f"   📋 列名: {list(df.columns)[:5]}...")
        
        # 只取前 50 条用于测试
        df_sample = df.head(10)
        print(f"   🎯 使用样本: {len(df_sample)} 条数据")
        
        return df_sample
    
    except Exception as e:
        print(f"   ⚠️ 加载失败: {e}")
        print(f"   💡 将不使用测试数据（CodingAgent 会生成 Mock 数据）")
        return None


def test_full_workflow():
    """测试完整的 4 Agent 工作流"""
    
    print("="*80)
    print("完整系统测试 - 4 Agent 协作 (使用 V4.2)")
    print("="*80)
    
    # 用户查询
    user_goal = "分析专利数据中的技术空白，识别未被充分研究的技术领域"
    
    print(f"\n🎯 用户目标: {user_goal}")
    
    # 加载数据
    test_data = load_test_data()
    
    # 初始化组件
    print("\n🔧 初始化组件...")
    try:
        llm = get_llm_client()
        print("   ✅ LLM 客户端")
        
        neo4j = Neo4jConnector()
        print("   ✅ Neo4j 连接器")
        
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False
    
    # 初始化 Agent
    print("\n🤖 初始化 Agent...")
    strategist = StrategistAgent(llm, neo4j)
    print("   ✅ Strategist Agent")
    
    methodologist = MethodologistAgent(llm)
    print("   ✅ Methodologist Agent")
    
    coding_agent = CodingAgentV4_2(llm, test_data=test_data, max_iterations=15)
    print("   ✅ CodingAgent V4.2 (终端增强版 - REPL)")
    
    reviewer = ReviewerAgent(llm, neo4j)
    print("   ✅ Reviewer Agent")
    
    # 构建工作流
    print("\n🔄 构建工作流...")
    workflow = build_full_workflow(strategist, methodologist, coding_agent, reviewer)
    print("   ✅ 4 Agent 工作流已构建")
    
    # 准备真实列名（V4.1 改进）
    available_columns = list(test_data.columns) if test_data is not None else None
    if available_columns:
        print(f"\n📋 注入真实列名到 Strategist:")
        print(f"   {available_columns[:5]}... (共 {len(available_columns)} 列)")
    
    # 执行工作流
    print("\n" + "="*80)
    print("开始执行工作流")
    print("="*80 + "\n")
    
    try:
        result = workflow.invoke({
            'user_goal': user_goal,
            'available_columns': available_columns,  # V4.1: 注入真实列名
            'test_data': test_data,
            'blueprint': {},
            'graph_context': '',
            'execution_specs': [],
            'generated_codes': [],
            'code_metadata': []
        }, config={
            "recursion_limit": 50  # 增加递归限制，防止复杂任务超时
        })
        
        print("\n" + "="*80)
        print("执行完成")
        print("="*80)
        
        # 显示结果
        display_results(result)
        
        # 保存结果
        save_results(result)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_results(result):
    """显示执行结果"""
    
    # 1. 战略蓝图
    print("\n" + "-"*80)
    print("📋 战略蓝图")
    print("-"*80)
    
    blueprint = result.get('blueprint', {})
    print(f"研究目标: {blueprint.get('research_objective', 'N/A')}")
    
    logic_chains = blueprint.get('analysis_logic_chains', [])
    print(f"\n分析步骤 ({len(logic_chains)} 个):")
    for i, step in enumerate(logic_chains, 1):
        print(f"  {i}. {step.get('objective', 'N/A')}")
        print(f"     方法: {step.get('method', 'N/A')}")
    
    # 2. 执行规格
    print("\n" + "-"*80)
    print("🔧 执行规格")
    print("-"*80)
    
    specs = result.get('execution_specs', [])
    print(f"生成规格: {len(specs)} 个")
    for i, spec in enumerate(specs, 1):
        if 'error' not in spec:
            print(f"  {i}. {spec.get('function_name', 'N/A')}")
            print(f"     库: {', '.join(spec.get('library_requirements', [])[:3])}")
    
    # 3. 代码生成
    print("\n" + "-"*80)
    print("💻 代码生成")
    print("-"*80)
    
    codes = result.get('generated_codes', [])
    metadata = result.get('code_metadata', [])
    
    valid_count = sum(1 for code in codes if code)
    print(f"成功生成: {valid_count}/{len(codes)}")
    
    for i, meta in enumerate(metadata, 1):
        if 'error' not in meta:
            status = "✅" if meta.get('is_valid', False) else "⚠️"
            print(f"  {status} 步骤 {i}: 迭代 {meta.get('iteration_count', 0)} 次")
            if meta.get('issues'):
                for issue in meta['issues']:
                    print(f"       - {issue}")
    
    # 4. 审查结果
    print("\n" + "-"*80)
    print("⚖️ 审查结果")
    print("-"*80)
    
    verification = result.get('verification_result', {})
    
    passed = verification.get('passed', False)
    success_rate = verification.get('success_rate', 0)
    
    print(f"验证状态: {'✅ 通过' if passed else '⚠️ 部分通过'}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"成功步骤: {verification.get('successful_steps', 0)}/{verification.get('total_steps', 0)}")
    
    semantic = verification.get('semantic_check', {})
    if semantic:
        print(f"\n语义验证:")
        print(f"  相关性: {'✅' if semantic.get('relevant', False) else '❌'}")
        print(f"  置信度: {semantic.get('confidence', 0):.1%}")
        print(f"  理由: {semantic.get('reasoning', 'N/A')[:100]}...")
    
    issues = verification.get('issues', [])
    if issues:
        print(f"\n问题列表:")
        for issue in issues:
            print(f"  - {issue}")
    
    # 5. 最终报告
    print("\n" + "-"*80)
    print("📄 最终报告")
    print("-"*80)
    
    final_report = result.get('final_report', '')
    if final_report:
        # 显示前 500 字符
        preview = final_report[:500]
        print(preview)
        if len(final_report) > 500:
            print(f"\n... (完整报告共 {len(final_report)} 字符)")
    else:
        print("未生成报告")
    
    print(f"\n回写状态: {result.get('writeback_status', 'N/A')}")


def save_results(result):
    """保存结果到文件"""
    
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "-"*80)
    print("💾 保存结果")
    print("-"*80)
    
    import json
    
    def clean_for_json(obj):
        """清理对象使其可以 JSON 序列化"""
        import pandas as pd
        import numpy as np
        
        if isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, tuple):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            # DataFrame 转为字典
            return {
                'type': 'DataFrame',
                'shape': obj.shape,
                'columns': list(obj.columns),
                'data': obj.head(5).to_dict('records')  # 只保存前5行
            }
        elif isinstance(obj, pd.Series):
            return {
                'type': 'Series',
                'data': obj.head(5).to_dict()
            }
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif hasattr(obj, '__dict__'):
            # 对象转为字符串
            return str(obj)
        else:
            return obj
    
    # 保存蓝图
    blueprint_file = output_dir / "blueprint.json"
    with open(blueprint_file, 'w', encoding='utf-8') as f:
        json.dump(clean_for_json(result['blueprint']), f, ensure_ascii=False, indent=2)
    print(f"✅ {blueprint_file}")
    
    # 保存分析结果
    if 'analysis_results' in result and result['analysis_results']:
        results_file = output_dir / "analysis_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(clean_for_json(result['analysis_results']), f, ensure_ascii=False, indent=2)
        print(f"✅ {results_file}")
    
    # 保存执行规格
    specs_file = output_dir / "execution_specs.json"
    with open(specs_file, 'w', encoding='utf-8') as f:
        json.dump(clean_for_json(result['execution_specs']), f, ensure_ascii=False, indent=2)
    print(f"✅ {specs_file}")
    
    # 注意：生成的代码已经在 workflow 中保存为 outputs/step_*.py，无需重复保存
    
    # 保存元数据
    metadata_file = output_dir / "code_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(clean_for_json(result['code_metadata']), f, ensure_ascii=False, indent=2)
    print(f"✅ {metadata_file}")
    
    # 保存验证结果
    if 'verification_result' in result:
        verification_file = output_dir / "verification_result.json"
        with open(verification_file, 'w', encoding='utf-8') as f:
            json.dump(clean_for_json(result['verification_result']), f, ensure_ascii=False, indent=2)
        print(f"✅ {verification_file}")
    
    # 保存最终报告
    if 'final_report' in result and result['final_report']:
        report_file = output_dir / "final_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(result['final_report'])
        print(f"✅ {report_file}")
    
    print(f"\n📁 所有结果已保存到: {output_dir}")


def main():
    """主函数"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Patent-DeepScientist 完整系统测试                                ║
║  4 Agent 协作 + 真实数据                                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_full_workflow()
    
    if success:
        print("\n" + "="*80)
        print("🎉 测试成功完成！")
        print("="*80)
        print("\n查看结果:")
        print("  - 输出目录: outputs/")
        print("  - 最终报告: outputs/final_report.md")
        print("  - 验证结果: outputs/verification_result.json")
        print("  - 分析步骤: outputs/step_*.py")
        print("  - 分析结果: outputs/step_*_results.csv")
        return 0
    else:
        print("\n" + "="*80)
        print("❌ 测试失败")
        print("="*80)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

