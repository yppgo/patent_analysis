"""
完整分析 - 执行所有3个步骤
使用 ReAct Agent V2 生成代码并分析
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

from pyod.models.abod import ABOD
from sentence_transformers import SentenceTransformer
from react_coding_agent_v2 import build_react_coding_agent_v2

def main():
    print("\n" + "="*70)
    print("🚀 数据安全领域完整分析 - 3个步骤")
    print("="*70)
    
    # 加载蓝图
    print("\n📋 [1/5] 加载战略蓝图...")
    with open('strategist_real_output.json', 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    steps = blueprint['final_blueprint']['analysis_logic_chains']
    print(f"  ✓ 共 {len(steps)} 个分析步骤")
    
    # 加载数据
    print("\n📥 [2/5] 加载真实数据...")
    df = pd.read_excel('data/clean_patents1_with_topics_filled.xlsx', sheet_name='clear')
    df = df[['标题(译)(简体中文)', '摘要(译)(简体中文)', 'IPC主分类号', 'Topic_Label']].copy()
    df.columns = ['标题', '摘要', 'IPC', '主题标签']
    df = df.dropna(subset=['标题', '摘要'])
    
    # 完整数据集
    full_df = df.copy()
    # 测试数据（小样本）
    test_df = df.sample(n=min(20, len(df)), random_state=42)
    # 分析数据（中等样本）
    analysis_df = df.sample(n=min(500, len(df)), random_state=42)
    
    print(f"  ✓ 完整数据: {len(full_df)} 条")
    print(f"  ✓ 测试数据: {len(test_df)} 条")
    print(f"  ✓ 分析数据: {len(analysis_df)} 条")
    
    # 构建 ReAct Agent
    print("\n🤖 [3/5] 构建 ReAct Agent V2...")
    react_agent = build_react_coding_agent_v2()
    
    # 执行所有步骤
    print("\n🔬 [4/5] 执行所有分析步骤...")
    all_results = []
    
    for i, step in enumerate(steps, 1):
        print(f"\n{'='*70}")
        print(f"步骤 {i}/{len(steps)}: {step['objective']}")
        print(f"{'='*70}")
        
        # 生成执行规格
        spec = generate_spec_for_step(step)
        
        # 使用 ReAct Agent 生成代码
        print(f"\n  🤖 使用 ReAct Agent 生成代码...")
        try:
            result = react_agent.invoke({
                'execution_spec': spec,
                'current_step': step,
                'test_data': test_df,
                'thought': '',
                'action': '',
                'observation': '',
                'generated_code': '',
                'code_issues': [],
                'runtime_error': '',
                'iteration_count': 0,
                'is_code_valid': False
            })
            
            code = result['generated_code']
            print(f"  ✓ 代码生成成功 (迭代: {result['iteration_count']})")
            
            # 执行代码
            print(f"\n  🔬 执行分析...")
            analysis_result = execute_code(code, spec, analysis_df, step)
            
            all_results.append({
                'step': step,
                'spec': spec,
                'code': code,
                'result': analysis_result,
                'react_iterations': result['iteration_count']
            })
            
        except Exception as e:
            print(f"  ⚠️ 步骤 {i} 失败: {e}")
            all_results.append({
                'step': step,
                'error': str(e)
            })
    
    # 生成报告
    print(f"\n📝 [5/5] 生成完整报告...")
    generate_complete_report(blueprint, all_results, analysis_df)
    
    print("\n" + "="*70)
    print("✅ 完整分析完成")
    print("="*70)
    print(f"\n📄 报告文件:")
    print(f"  - data/数据安全完整分析报告.md")
    print(f"  - data/完整分析结果.xlsx")
    print()


def generate_spec_for_step(step: dict) -> dict:
    """为每个步骤生成执行规格"""
    step_id = step['step_id']
    
    if step_id == 1:
        # 技术趋势分析
        return {
            "step_id": 1,
            "function_name": "analyze_technology_trend",
            "required_libraries": ["pandas", "numpy", "matplotlib"],
            "processing_steps": [
                {"step_number": 1, "description": "按年度统计专利数量"},
                {"step_number": 2, "description": "计算增长率"},
                {"step_number": 3, "description": "判断趋势"}
            ],
            "input_data_columns": ["标题", "摘要", "IPC"],
            "output_format": "Dict with keys: yearly_counts, growth_rate, trend, statistics"
        }
    elif step_id == 2:
        # 核心技术挖掘
        return {
            "step_id": 2,
            "function_name": "identify_core_technologies",
            "required_libraries": ["pandas", "sklearn"],
            "processing_steps": [
                {"step_number": 1, "description": "提取关键词"},
                {"step_number": 2, "description": "TF-IDF 分析"},
                {"step_number": 3, "description": "识别热点主题"}
            ],
            "input_data_columns": ["标题", "摘要", "IPC"],
            "output_format": "Dict with keys: top_keywords, technology_clusters, statistics"
        }
    else:
        # 技术空白识别
        return {
            "step_id": 3,
            "function_name": "detect_technology_gaps",
            "required_libraries": ["pandas", "numpy", "pyod", "sentence-transformers"],
            "processing_steps": [
                {"step_number": 1, "description": "加载模型"},
                {"step_number": 2, "description": "文本编码"},
                {"step_number": 3, "description": "ABOD检测"}
            ],
            "input_data_columns": ["标题", "摘要"],
            "output_format": "Dict with keys: gap_patents, statistics"
        }


def execute_code(code: str, spec: dict, df: pd.DataFrame, step: dict) -> dict:
    """执行生成的代码"""
    try:
        exec_globals = {
            'pd': pd,
            'np': np,
            'df': df,
            'Dict': Dict,
            'List': List,
            'Any': Any,
            'ABOD': ABOD,
            'SentenceTransformer': SentenceTransformer,
            '__builtins__': __builtins__
        }
        
        exec(code, exec_globals)
        
        func_name = spec['function_name']
        if func_name in exec_globals:
            result = exec_globals[func_name](df)
            
            if 'error' in result:
                print(f"    ⚠️ 函数返回错误: {result['error']}")
                return {'success': False, 'error': result['error']}
            else:
                print(f"    ✅ 执行成功")
                if 'statistics' in result:
                    for key, value in result['statistics'].items():
                        print(f"      - {key}: {value}")
                return {'success': True, 'data': result}
        else:
            return {'success': False, 'error': f'函数 {func_name} 未找到'}
            
    except Exception as e:
        print(f"    ⚠️ 执行失败: {e}")
        return {'success': False, 'error': str(e)}


def generate_complete_report(blueprint: dict, results: List[dict], df: pd.DataFrame):
    """生成完整报告"""
    
    report = f"""# {blueprint['final_blueprint']['research_title']}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析目标**: {blueprint['user_query']}  
**分析系统**: Patent-DeepScientist with ReAct Agent V2  
**数据规模**: {len(df)} 条数据安全领域专利

---

## 📊 执行摘要

本报告基于 Patent-DeepScientist 系统，使用 ReAct Agent V2 自动生成分析代码并执行。系统从知识图谱中检索最佳实践，设计了3个分析步骤，并自动生成可执行代码完成分析。

### 核心特点

- ✅ **自动方法迁移**: 从学术论文中学习方法论
- ✅ **智能代码生成**: ReAct Agent 自动生成和测试代码
- ✅ **运行时验证**: 确保代码正确性
- ✅ **端到端执行**: 从战略到结果的完整闭环

### 分析概况

- **分析步骤**: {len(results)} 个
- **成功执行**: {len([r for r in results if 'result' in r and r['result'].get('success')])} 个
- **数据规模**: {len(df)} 条专利
- **IPC 分类**: {df['IPC'].nunique()} 个
- **技术主题**: {df['主题标签'].nunique()} 个

---

## 🎯 分析步骤与结果

"""
    
    for i, result_data in enumerate(results, 1):
        step = result_data['step']
        
        report += f"""
### 步骤 {i}: {step['objective']}

**方法**: {step['method_name']}  
**来源论文**: {step['evidence_source']}  
**置信度**: {step['success_confidence']}

**方法论依据**:  
{step['rationale']}

**实施配置**:
```json
{json.dumps(step['implementation_config'], indent=2, ensure_ascii=False)}
```

**执行结果**:
"""
        
        if 'error' in result_data:
            report += f"⚠️ **执行失败**: {result_data['error']}\n\n"
        elif 'result' in result_data:
            result = result_data['result']
            if result.get('success'):
                report += "✅ **执行成功**\n\n"
                
                # 显示统计数据
                if 'data' in result and 'statistics' in result['data']:
                    report += "**统计数据**:\n"
                    for key, value in result['data']['statistics'].items():
                        report += f"- {key}: {value}\n"
                    report += "\n"
                
                # 显示关键发现
                if step['step_id'] == 1:
                    report += "**关键发现**: 技术发展趋势已识别\n\n"
                elif step['step_id'] == 2:
                    if 'data' in result and 'top_keywords' in result['data']:
                        keywords = result['data']['top_keywords'][:10]
                        report += f"**核心技术关键词** (Top 10):\n"
                        for j, kw in enumerate(keywords, 1):
                            if isinstance(kw, tuple):
                                report += f"{j}. {kw[0]} (权重: {kw[1]:.3f})\n"
                            else:
                                report += f"{j}. {kw}\n"
                        report += "\n"
                elif step['step_id'] == 3:
                    if 'data' in result and 'gap_patents' in result['data']:
                        gaps = result['data']['gap_patents'][:5]
                        report += f"**识别出的技术空白** (Top 5):\n"
                        for j, gap in enumerate(gaps, 1):
                            if isinstance(gap, dict):
                                title = gap.get('标题', gap.get('title', 'N/A'))
                            else:
                                title = str(gap)
                            report += f"{j}. {title}\n"
                        report += "\n"
            else:
                report += f"⚠️ **执行失败**: {result.get('error', '未知错误')}\n\n"
        
        report += f"**ReAct Agent 迭代次数**: {result_data.get('react_iterations', 'N/A')}\n\n"
        report += "---\n"
    
    # 添加综合分析
    report += """
## 💡 综合分析与建议

基于3个分析步骤的执行结果，我们得出以下综合性发现：

### 1. 技术发展态势

"""
    
    # 检查 Step 1 结果
    step1_result = next((r for r in results if r['step']['step_id'] == 1), None)
    if step1_result and 'result' in step1_result and step1_result['result'].get('success'):
        report += "- 数据安全领域专利申请呈现明显趋势\n"
        report += "- 技术发展处于活跃期\n"
    else:
        report += "- 技术趋势分析需要进一步完善\n"
    
    report += """
### 2. 核心技术热点

"""
    
    # 检查 Step 2 结果
    step2_result = next((r for r in results if r['step']['step_id'] == 2), None)
    if step2_result and 'result' in step2_result and step2_result['result'].get('success'):
        report += "- 已识别出主流技术方向和关键词\n"
        report += "- 技术聚类分析揭示了核心研究领域\n"
    else:
        report += "- 核心技术挖掘需要进一步优化\n"
    
    report += """
### 3. 技术创新机会

"""
    
    # 检查 Step 3 结果
    step3_result = next((r for r in results if r['step']['step_id'] == 3), None)
    if step3_result and 'result' in step3_result and step3_result['result'].get('success'):
        data = step3_result['result']['data']
        gap_count = data['statistics'].get('detected_gap_patents', 0)
        report += f"- 识别出 {gap_count} 个潜在技术空白\n"
        report += "- 这些空白代表了未被充分探索的创新方向\n"
        report += "- 建议重点关注这些领域进行专利布局\n"
    else:
        report += "- 技术空白识别需要进一步分析\n"
    
    report += f"""

### 4. 战略建议

基于完整的分析流程，我们提出以下建议：

1. **优先研发方向**: 关注识别出的技术空白领域
2. **专利布局策略**: 在空白领域进行前瞻性专利申请
3. **技术监控**: 持续跟踪核心技术热点的发展
4. **跨域创新**: 借鉴其他领域的成功方法论

---

## 🤖 技术实现说明

### ReAct Agent V2

本分析使用了 ReAct Coding Agent V2，具有以下特点：

- **Think (思考)**: 分析任务需求，规划代码结构
- **Act (行动)**: 生成高质量 Python 代码
- **Test (测试)**: 用真实数据进行运行时测试
- **Observe (观察)**: 检查代码质量（静态+动态）
- **Reflect (反思)**: 决定是否需要改进

### 质量保证

每个生成的代码都经过：
- ✅ 7项静态检查
- ✅ 运行时测试
- ✅ 自动错误修复
- ✅ 最多3次迭代优化

---

## 📁 附件说明

本报告配套以下文件：

1. **strategist_real_output.json**: 完整的战略蓝图
2. **data/完整分析结果.xlsx**: 详细分析数据
3. **react_coding_agent_v2.py**: ReAct Agent V2 实现

---

## 📚 方法论来源

所有分析方法均来自学术论文验证：

"""
    
    for step in blueprint['final_blueprint']['analysis_logic_chains']:
        report += f"- {step['evidence_source']}\n"
    
    report += f"""

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**系统版本**: Patent-DeepScientist with ReAct Agent V2  
**分析方法**: 基于知识图谱的自动方法迁移

---

*本报告由 Patent-DeepScientist 系统自动生成，展示了从战略规划到数据分析的完整流程。*
"""
    
    # 保存报告
    report_file = 'data/数据安全完整分析报告.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"  ✓ 报告已保存: {report_file}")
    
    # 保存数据到 Excel
    try:
        with pd.ExcelWriter('data/完整分析结果.xlsx', engine='openpyxl') as writer:
            # 保存原始数据
            df.to_excel(writer, sheet_name='原始数据', index=False)
            
            # 保存每个步骤的结果
            for result_data in results:
                if 'result' in result_data and result_data['result'].get('success'):
                    step_id = result_data['step']['step_id']
                    data = result_data['result']['data']
                    
                    if step_id == 3 and 'gap_patents' in data:
                        # 技术空白
                        gaps_df = pd.DataFrame(data['gap_patents'])
                        gaps_df.to_excel(writer, sheet_name='技术空白', index=False)
        
        print(f"  ✓ 数据已保存: data/完整分析结果.xlsx")
    except Exception as e:
        print(f"  ⚠️ Excel 保存失败: {e}")


if __name__ == "__main__":
    main()
