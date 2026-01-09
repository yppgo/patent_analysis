"""
完整流程 - 使用 ReAct Coding Agent
从战略蓝图 → 执行规格 → ReAct代码生成 → 数据分析 → 报告生成
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 导入 ReAct Agent
from react_coding_agent import build_react_coding_agent

load_dotenv()


# ============================================================================
# 1. 状态定义
# ============================================================================

class FullPipelineState(TypedDict, total=False):
    """完整流程状态"""
    user_goal: str
    blueprint: dict
    steps: List[dict]
    all_specs: List[dict]
    all_codes: List[str]
    results: List[dict]
    report: str


# ============================================================================
# 2. LLM 配置
# ============================================================================

def get_llm() -> ChatOpenAI:
    """获取 LLM"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return ChatOpenAI(
        model="qwen-max",
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        openai_api_key=api_key,
        temperature=0.3,
    )


# ============================================================================
# 3. 节点实现
# ============================================================================

def load_blueprint_node(state: FullPipelineState) -> Dict:
    """加载战略蓝图"""
    print("\n" + "="*70)
    print("📋 [步骤 1/5] 加载战略蓝图")
    print("="*70)
    
    with open('strategist_real_output.json', 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    user_goal = blueprint.get('user_query', '')
    steps = blueprint['final_blueprint']['analysis_logic_chains']
    
    print(f"  ✓ 用户目标: {user_goal}")
    print(f"  ✓ 分析步骤: {len(steps)} 个")
    for i, step in enumerate(steps, 1):
        print(f"    {i}. {step['objective']}")
    
    return {
        'user_goal': user_goal,
        'blueprint': blueprint,
        'steps': steps
    }


def generate_specs_node(state: FullPipelineState) -> Dict:
    """生成执行规格"""
    print("\n" + "="*70)
    print("📐 [步骤 2/5] 生成执行规格 (Methodologist)")
    print("="*70)
    
    llm = get_llm()
    steps = state.get('steps', state.get('blueprint', {}).get('final_blueprint', {}).get('analysis_logic_chains', []))
    
    print(f"  调试: 找到 {len(steps)} 个步骤")
    
    all_specs = []
    
    for i, step in enumerate(steps, 1):
        print(f"\n  处理步骤 {i}/{len(steps)}: {step.get('objective', 'N/A')[:50]}...")
        
        prompt = f"""你是配方师。将研究步骤转化为执行规格。

**研究步骤:**
{json.dumps(step, indent=2, ensure_ascii=False)}

**输出 JSON:**
{{
  "step_id": {step.get('step_id')},
  "function_name": "函数名（小写下划线）",
  "required_libraries": ["库1", "库2"],
  "processing_steps": [
    {{"step_number": 1, "description": "步骤描述", "code_logic": "伪代码"}}
  ],
  "input_data_columns": ["标题", "摘要", "IPC"],
  "output_format": "Dict with keys: result, statistics"
}}

只输出 JSON。"""

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            spec = json.loads(content)
            all_specs.append(spec)
            print(f"    ✓ {spec.get('function_name', 'N/A')}")
            
        except Exception as e:
            print(f"    ⚠️ 失败: {e}")
            all_specs.append({"error": str(e), "step_id": step.get('step_id')})
    
    return {'all_specs': all_specs}


def generate_codes_with_react_node(state: FullPipelineState) -> Dict:
    """使用 ReAct Agent 生成代码"""
    print("\n" + "="*70)
    print("🤖 [步骤 3/5] 使用 ReAct Agent 生成代码")
    print("="*70)
    
    specs = state.get('all_specs', [])
    steps = state.get('steps', state.get('blueprint', {}).get('final_blueprint', {}).get('analysis_logic_chains', []))
    all_codes = []
    
    # 构建 ReAct Agent
    react_agent = build_react_coding_agent()
    
    for i, (spec, step) in enumerate(zip(specs, steps), 1):
        if 'error' in spec:
            print(f"\n  跳过步骤 {i} (规格生成失败)")
            all_codes.append("")
            continue
        
        print(f"\n  === 步骤 {i}/{len(specs)}: {step.get('objective', 'N/A')[:50]}... ===")
        
        try:
            # 调用 ReAct Agent
            result = react_agent.invoke({
                'execution_spec': spec,
                'current_step': step,
                'thought': '',
                'action': '',
                'observation': '',
                'generated_code': '',
                'code_issues': [],
                'iteration_count': 0,
                'is_code_valid': False
            })
            
            code = result['generated_code']
            all_codes.append(code)
            
            print(f"\n  ✅ 步骤 {i} 代码生成成功")
            print(f"    - 迭代次数: {result['iteration_count']}")
            print(f"    - 代码行数: {len(code.split(chr(10)))}")
            print(f"    - 质量检查: {'通过' if result['is_code_valid'] else '未通过'}")
            
        except Exception as e:
            print(f"    ⚠️ 生成失败: {e}")
            all_codes.append("")
    
    return {'all_codes': all_codes}


def execute_analysis_node(state: FullPipelineState) -> Dict:
    """执行分析"""
    print("\n" + "="*70)
    print("🔬 [步骤 4/5] 执行数据分析")
    print("="*70)
    
    # 加载数据
    print("\n  📥 加载数据...")
    df = pd.read_excel('data/clean_patents1_with_topics_filled.xlsx', sheet_name='clear')
    df = df[['标题(译)(简体中文)', '摘要(译)(简体中文)', 'IPC主分类号', 'Topic_Label']].copy()
    df.columns = ['标题', '摘要', 'IPC', '主题标签']
    df = df.dropna(subset=['标题', '摘要'])
    df = df.sample(n=min(500, len(df)), random_state=42)
    print(f"    ✓ 加载了 {len(df)} 条专利")
    
    # 准备执行环境
    import numpy as np
    from pyod.models.abod import ABOD
    from sentence_transformers import SentenceTransformer
    
    codes = state.get('all_codes', [])
    specs = state.get('all_specs', [])
    steps = state.get('steps', state.get('blueprint', {}).get('final_blueprint', {}).get('analysis_logic_chains', []))
    results = []
    
    for i, (code, spec, step) in enumerate(zip(codes, specs, steps), 1):
        if not code or 'error' in spec:
            print(f"\n  跳过步骤 {i}")
            results.append({"error": "代码未生成", "step_id": step.get('step_id')})
            continue
        
        print(f"\n  执行步骤 {i}: {step.get('objective', 'N/A')[:50]}...")
        
        try:
            # 创建执行环境
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
            
            # 执行代码
            exec(code, exec_globals)
            
            # 调用函数
            func_name = spec.get('function_name', 'analyze')
            if func_name in exec_globals:
                result = exec_globals[func_name](df)
                
                if 'error' in result:
                    print(f"    ⚠️ 函数执行出错: {result['error']}")
                    results.append({
                        "step_id": step.get('step_id'),
                        "error": result['error'],
                        "success": False
                    })
                else:
                    results.append({
                        "step_id": step.get('step_id'),
                        "objective": step.get('objective'),
                        "result": result,
                        "success": True
                    })
                    print(f"    ✅ 执行成功")
                    
                    # 显示结果摘要
                    if 'statistics' in result:
                        stats = result['statistics']
                        for key, value in stats.items():
                            print(f"      - {key}: {value}")
            else:
                print(f"    ⚠️ 函数 {func_name} 未找到")
                results.append({
                    "step_id": step.get('step_id'),
                    "error": f"函数 {func_name} 未找到",
                    "success": False
                })
                
        except Exception as e:
            print(f"    ⚠️ 执行失败: {e}")
            results.append({
                "step_id": step.get('step_id'),
                "error": str(e),
                "success": False
            })
    
    successful = len([r for r in results if r.get('success')])
    print(f"\n  ✓ 完成 {successful}/{len(results)} 个分析")
    
    return {'results': results}


def generate_report_node(state: FullPipelineState) -> Dict:
    """生成报告"""
    print("\n" + "="*70)
    print("📝 [步骤 5/5] 生成分析报告")
    print("="*70)
    
    blueprint = state.get('blueprint', {})
    results = state.get('results', [])
    steps = state.get('steps', blueprint.get('final_blueprint', {}).get('analysis_logic_chains', []))
    
    research_title = blueprint.get('final_blueprint', {}).get('research_title', '数据安全领域分析报告')
    user_goal = state.get('user_goal', blueprint.get('user_query', '数据安全领域分析'))
    report = f"""# {research_title}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析目标**: {user_goal}  
**分析系统**: Patent-DeepScientist with ReAct Agent v2.0

---

## 📊 执行摘要

本报告使用 **ReAct Coding Agent** 自动生成分析代码并执行。

### 系统特点

- ✅ **自我反思**: Agent 能够评估生成的代码质量
- ✅ **迭代优化**: 自动修复发现的问题
- ✅ **质量保证**: 7项自动化检查
- ✅ **端到端**: 从战略到报告的完整流程

### 执行统计

- **分析步骤**: {len(steps)} 个
- **成功执行**: {len([r for r in results if r.get('success')])} 个
- **分析专利**: 500 条

---

## 🎯 分析步骤与结果

"""
    
    for i, (step, result) in enumerate(zip(steps, results), 1):
        report += f"""
### 步骤 {i}: {step.get('objective', 'N/A')}

**方法**: {step.get('method_name', 'N/A')}  
**来源**: {step.get('evidence_source', 'N/A')}  
**置信度**: {step.get('success_confidence', 'N/A')}

**实施配置**:
```json
{json.dumps(step.get('implementation_config', {}), indent=2, ensure_ascii=False)}
```

**执行结果**:
"""
        
        if result.get('success'):
            report += "✅ **执行成功**\n\n"
            if 'result' in result and 'statistics' in result['result']:
                stats = result['result']['statistics']
                report += "**统计数据**:\n"
                for key, value in stats.items():
                    report += f"- {key}: {value}\n"
                report += "\n"
                
                # 如果有技术空白数据，显示 Top 5
                if 'gap_patents' in result['result']:
                    gaps = result['result']['gap_patents']
                    if gaps and len(gaps) > 0:
                        report += f"\n**识别出的技术空白** (Top 5):\n\n"
                        for j, gap in enumerate(gaps[:5], 1):
                            title = gap.get('title', 'N/A')
                            report += f"{j}. {title}\n"
                        report += "\n"
        else:
            report += f"⚠️ **执行失败**: {result.get('error', '未知错误')}\n\n"
        
        report += "---\n"
    
    # 添加 ReAct Agent 说明
    report += """
## 🤖 ReAct Agent 技术说明

本报告使用了基于 **ReAct (Reasoning + Acting)** 模式的代码生成智能体：

### ReAct 循环

```
Think (思考) → Act (行动) → Observe (观察) → Reflect (反思)
     ↑                                              ↓
     └──────────────── 如果需要改进 ────────────────┘
```

### 质量保证

每个生成的代码都经过 7 项质量检查：
1. ✅ 代码长度检查
2. ✅ 函数定义检查
3. ✅ 返回语句检查
4. ✅ 错误处理检查
5. ✅ 类型注解检查
6. ✅ 注释充分性检查
7. ✅ 语法正确性检查

### 优势

- **自我优化**: 最多3次迭代机会
- **高质量**: 自动检查和修复
- **可靠性**: 完整的错误处理

---

## 💡 关键发现

"""
    
    successful_steps = [r for r in results if r.get('success')]
    report += f"- 成功执行 {len(successful_steps)}/{len(results)} 个分析步骤\n"
    report += f"- 使用 ReAct Agent 自动生成和优化代码\n"
    report += f"- 分析了 500 条数据安全领域专利\n"
    
    # 如果有技术空白结果，添加总结
    for result in results:
        if result.get('success') and 'result' in result:
            if 'gap_patents' in result['result']:
                gaps = result['result']['gap_patents']
                report += f"- 识别出 {len(gaps)} 个潜在技术空白\n"
                break
    
    report += f"""

---

## 📁 附件

- 战略蓝图: `strategist_real_output.json`
- ReAct Agent: `react_coding_agent.py`
- 本报告: `data/ReAct完整分析报告.md`

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**系统版本**: Patent-DeepScientist with ReAct Agent v2.0
"""
    
    # 保存报告
    report_file = 'data/ReAct完整分析报告.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"  ✓ 报告已保存: {report_file}")
    
    return {'report': report}


# ============================================================================
# 4. 构建工作流
# ============================================================================

def build_full_pipeline():
    """构建完整流程"""
    print("\n🔧 构建完整流程 (with ReAct Agent)...")
    
    workflow = StateGraph(FullPipelineState)
    
    workflow.add_node("load_blueprint", load_blueprint_node)
    workflow.add_node("generate_specs", generate_specs_node)
    workflow.add_node("generate_codes_react", generate_codes_with_react_node)
    workflow.add_node("execute_analysis", execute_analysis_node)
    workflow.add_node("generate_report", generate_report_node)
    
    workflow.set_entry_point("load_blueprint")
    workflow.add_edge("load_blueprint", "generate_specs")
    workflow.add_edge("generate_specs", "generate_codes_react")
    workflow.add_edge("generate_codes_react", "execute_analysis")
    workflow.add_edge("execute_analysis", "generate_report")
    workflow.add_edge("generate_report", END)
    
    print("  ✓ 流程构建完成")
    
    return workflow.compile()


# ============================================================================
# 5. 主函数
# ============================================================================

def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 Patent-DeepScientist 完整流程 (with ReAct Agent)")
    print("="*70)
    
    app = build_full_pipeline()
    
    try:
        result = app.invoke({})
        
        print("\n" + "="*70)
        print("✅ 完整流程执行成功")
        print("="*70)
        
        print(f"\n📊 执行统计:")
        print(f"  - 分析步骤: {len(result.get('steps', []))}")
        print(f"  - 生成代码: {len([c for c in result.get('all_codes', []) if c])}")
        print(f"  - 成功分析: {len([r for r in result.get('results', []) if r.get('success')])}")
        
        print(f"\n📄 输出文件:")
        print(f"  - 完整报告: data/ReAct完整分析报告.md")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("🎉 流程结束")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
