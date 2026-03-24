#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：Strategist → Methodologist → Coding Agent V4.2

目标：
1. 验证完整流程可以正常运行
2. 评估 Coding Agent V4.2 的代码生成质量
3. 确认生成的代码可以成功执行
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from scripts.jos.experiment_registry import get_mode_config
from src.utils.llm_client import get_llm_client
from src.graphs.causal_graph_query import CausalGraphQuery
from src.graphs.method_graph_query import MethodGraphQuery
from src.agents.strategist import StrategistAgent
from src.agents.methodologist import MethodologistAgent
from src.agents.coding_agent_v4_2 import CodingAgentV4_2
from src.utils.data_preview import DataPreview


def load_test_data(data_file: str, sheet_name: str = "sheet1") -> pd.DataFrame:
    """加载测试数据"""
    try:
        df = pd.read_excel(data_file, sheet_name=sheet_name)
        print(f"  [OK] 数据加载成功: {df.shape}")
        print(f"  列名: {list(df.columns)[:10]}...")
        return df
    except Exception as e:
        print(f"  [FAIL] 数据加载失败: {e}")
        return None


def test_full_pipeline():
    """测试从 Strategist 到 Coding Agent V4.2 的完整流程"""
    print("\n" + "=" * 80)
    print("🚀 端到端测试：Strategist → Methodologist → Coding Agent V4.2")
    print("=" * 80)
    
    # 创建输出目录
    Path('outputs').mkdir(exist_ok=True)
    
    # 初始化组件
    print("\n📦 Step 0: 初始化组件")
    print("-" * 40)
    
    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    
    # 加载图谱
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")
    
    # 初始化 Agents
    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)
    
    print("  ✅ Strategist Agent (V5.0)")
    print("  ✅ Methodologist Agent (V5.0)")
    print("  ✅ Coding Agent (V4.2)")
    print("  ✅ 因果图谱（30变量，135路径）")
    print("  ✅ 方法图谱（50篇论文）")
    
    # 加载测试数据
    print("\n📊 加载测试数据")
    data_file = "data/new_data.XLSX"
    test_data = load_test_data(data_file, "sheet1")
    
    if test_data is None:
        print("❌ 无法加载测试数据，终止测试")
        return
    
    # Step 1: Strategist 生成蓝图
    print("\n" + "=" * 80)
    print("📋 Step 1: Strategist 生成 DAG 蓝图")
    print("=" * 80)
    
    user_input = {
        "user_goal": "分析量子计算领域的技术影响力驱动因素",
        "data_file": data_file,
        "sheet_name": "sheet1",
        "use_dag": True
    }
    
    print(f"\n📝 用户输入:")
    print(f"  目标: {user_input['user_goal']}")
    print(f"  数据: {user_input['data_file']}")
    
    start_time = time.time()
    blueprint_result = strategist.process(user_input)
    strategist_time = time.time() - start_time
    
    # 验证蓝图
    assert 'blueprint' in blueprint_result, "缺少 blueprint 字段"
    blueprint = blueprint_result['blueprint']
    assert 'task_graph' in blueprint, "缺少 task_graph 字段"
    task_graph = blueprint['task_graph']
    
    print(f"\n✅ 蓝图生成成功 (耗时: {strategist_time:.1f}s)")
    print(f"  任务数量: {len(task_graph)}")
    print(f"  研究目标: {blueprint.get('research_objective', 'N/A')[:60]}...")
    
    # 打印任务列表
    print(f"\n📋 任务列表:")
    for i, task in enumerate(task_graph, 1):
        print(f"  {i}. {task['task_id']}: {task['task_type']}")
        print(f"     问题: {task['question'][:50]}...")
        print(f"     依赖: {task.get('dependencies', [])}")
    
    # 保存蓝图
    blueprint_file = "outputs/full_pipeline_blueprint.json"
    with open(blueprint_file, 'w', encoding='utf-8') as f:
        json.dump(blueprint_result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 蓝图已保存: {blueprint_file}")
    
    # Step 2: Methodologist 生成技术规格
    print("\n" + "=" * 80)
    print("📋 Step 2: Methodologist 生成技术规格")
    print("=" * 80)
    
    specs = []
    methodologist_times = []
    
    for i, task in enumerate(task_graph, 1):
        print(f"\n🔧 处理任务 {i}/{len(task_graph)}: {task['task_id']}")
        
        start_time = time.time()
        spec_result = methodologist.process({'task_node': task})
        methodologist_times.append(time.time() - start_time)
        
        # 验证技术规格
        assert 'technical_spec' in spec_result, f"任务 {task['task_id']} 缺少 technical_spec"
        spec = spec_result['technical_spec']
        
        # 检查是否有错误
        if 'error' in spec:
            print(f"  ❌ 技术规格生成失败 (耗时: {methodologist_times[-1]:.1f}s)")
            print(f"     错误: {spec['error']}")
            if 'raw_response' in spec:
                print(f"     原始响应（前500字符）:")
                print(f"     {spec['raw_response'][:500]}")
            # 保存错误信息
            spec_file = f"outputs/full_pipeline_{task['task_id']}_spec_error.json"
            with open(spec_file, 'w', encoding='utf-8') as f:
                json.dump(spec_result, f, ensure_ascii=False, indent=2)
            print(f"     💾 错误已保存: {spec_file}")
            continue
        
        print(f"  ✅ 技术规格生成成功 (耗时: {methodologist_times[-1]:.1f}s)")
        print(f"     函数名: {spec['function_name']}")
        print(f"     逻辑步骤: {len(spec.get('logic_flow', []))}步")
        
        specs.append(spec_result)
        
        # 保存技术规格
        spec_file = f"outputs/full_pipeline_{task['task_id']}_spec.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec_result, f, ensure_ascii=False, indent=2)
        print(f"     💾 已保存: {spec_file}")
    
    # Step 3: Coding Agent V4.2 执行代码生成
    print("\n" + "=" * 80)
    print("📋 Step 3: Coding Agent V4.2 生成并执行代码")
    print("=" * 80)
    
    coding_results = []
    coding_times = []
    success_count = 0
    
    for i, (task, spec_result) in enumerate(zip(task_graph, specs), 1):
        print(f"\n🔧 执行任务 {i}/{len(task_graph)}: {task['task_id']}")
        print(f"  函数名: {spec_result['technical_spec']['function_name']}")
        
        # 清理旧结果文件
        task_id = task['task_id']
        expected_output_file = (
            spec_result.get('technical_spec', {}).get('output_file')
            or task.get('implementation_config', {}).get('output_file')
            or f"outputs/{task_id}_results.csv"
        )
        old_result_file = Path(expected_output_file)
        if old_result_file.exists():
            old_result_file.unlink()
            print(f"  🗑️ 清理旧文件: {old_result_file}")
        
        # 准备输入
        coding_input = {
            'execution_spec': spec_result['technical_spec'],
            'current_step': task,
            'test_data': test_data,
            'previous_result': coding_results[-1] if coding_results else None
        }
        
        start_time = time.time()
        try:
            result = coding_agent.process(coding_input)
            coding_times.append(time.time() - start_time)
            
            is_valid = result.get('is_code_valid', False)
            iteration_count = result.get('iteration_count', 0)
            runtime_error = result.get('runtime_error', '')
            
            if is_valid:
                success_count += 1
                print(f"  ✅ 代码生成并执行成功 (耗时: {coding_times[-1]:.1f}s, 迭代: {iteration_count}次)")
            else:
                print(f"  ❌ 代码执行失败 (耗时: {coding_times[-1]:.1f}s, 迭代: {iteration_count}次)")
                if runtime_error:
                    print(f"     错误: {runtime_error[:100]}...")
            
            coding_results.append(result)
            
            # 保存生成的代码
            if result.get('generated_code'):
                code_file = f"outputs/full_pipeline_{task_id}.py"
                with open(code_file, 'w', encoding='utf-8') as f:
                    f.write(result['generated_code'])
                print(f"     💾 代码已保存: {code_file}")
            
        except Exception as e:
            coding_times.append(time.time() - start_time)
            print(f"  ❌ 执行异常: {e}")
            coding_results.append({'error': str(e), 'is_code_valid': False})
    
    # Step 4: 评估结果
    print("\n" + "=" * 80)
    print("📊 Step 4: 测试结果评估")
    print("=" * 80)
    
    total_tasks = len(task_graph)
    success_rate = success_count / total_tasks * 100 if total_tasks > 0 else 0
    
    print(f"\n📈 性能指标:")
    print(f"  Strategist 耗时: {strategist_time:.1f}s")
    print(f"  Methodologist 平均耗时: {sum(methodologist_times)/len(methodologist_times):.1f}s")
    print(f"  Coding Agent 平均耗时: {sum(coding_times)/len(coding_times):.1f}s")
    print(f"  总耗时: {strategist_time + sum(methodologist_times) + sum(coding_times):.1f}s")
    
    print(f"\n🎯 质量指标:")
    print(f"  任务总数: {total_tasks}")
    print(f"  成功数量: {success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    
    # 检查输出文件
    print(f"\n📁 输出文件检查:")
    for task in task_graph:
        task_id = task['task_id']
        expected_output_file = (
            task.get('implementation_config', {}).get('output_file')
            or f"outputs/{task_id}_results.csv"
        )
        result_file = Path(expected_output_file)
        code_file = Path(f"outputs/full_pipeline_{task_id}.py")
        
        if result_file.exists():
            suffix = result_file.suffix.lower()
            if suffix == '.csv':
                df = pd.read_csv(result_file)
                print(f"  ✅ {result_file}: {df.shape[0]}行, {df.shape[1]}列")
            else:
                size = result_file.stat().st_size
                print(f"  ✅ {result_file}: 存在 (大小: {size} 字节)")
        else:
            print(f"  ❌ {result_file}: 不存在")
        
        if code_file.exists():
            print(f"  ✅ {code_file}: 存在")
        else:
            print(f"  ❌ {code_file}: 不存在")
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    
    if success_rate >= 80:
        print(f"\n✅ 测试通过！成功率: {success_rate:.1f}%")
        print("  建议：当前方案可用，继续优化细节")
    elif success_rate >= 50:
        print(f"\n⚠️ 测试部分通过。成功率: {success_rate:.1f}%")
        print("  建议：分析失败原因，优化 Prompt 或启用 execution_plan")
    else:
        print(f"\n❌ 测试未通过。成功率: {success_rate:.1f}%")
        print("  建议：深入分析问题，考虑架构调整")
    
    # 保存测试报告
    report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_goal': user_input['user_goal'],
        'total_tasks': total_tasks,
        'success_count': success_count,
        'success_rate': success_rate,
        'strategist_time': strategist_time,
        'methodologist_times': methodologist_times,
        'coding_times': coding_times,
        'total_time': strategist_time + sum(methodologist_times) + sum(coding_times),
        'coding_results': [
            {
                'task_id': task['task_id'],
                'is_valid': r.get('is_code_valid', False),
                'iteration_count': r.get('iteration_count', 0),
                'error': r.get('runtime_error', '') or r.get('error', '')
            }
            for task, r in zip(task_graph, coding_results)
        ]
    }
    
    report_file = "outputs/full_pipeline_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 测试报告已保存: {report_file}")
    
    return report


def _strip_json_fence(content: str) -> str:
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def _normalize_blueprint_data_source(blueprint: Dict[str, Any], data_file: str, sheet_name: str) -> Dict[str, Any]:
    if not isinstance(blueprint, dict):
        return blueprint
    for task in blueprint.get("task_graph", []):
        config = task.setdefault("implementation_config", {})
        config["data_source"] = data_file
        config["sheet_name"] = sheet_name
    return blueprint


def _format_previous_results(previous_results: List[Dict[str, Any]]) -> str:
    if not previous_results:
        return "（无上一轮执行反馈）"
    lines = []
    for item in previous_results:
        lines.append(f"- {item.get('task_id', '?')}: {item.get('question', '')}")
        lines.append(f"  状态: {item.get('status', 'unknown')}")
        findings = item.get("key_findings", "")
        if findings:
            lines.append(f"  结果摘要: {findings[:300]}")
    return "\n".join(lines)


def _build_single_agent_blueprint(
    strategist,
    user_goal: str,
    data_file: str,
    sheet_name: str,
    available_columns: List[str],
    previous_results: Optional[List[Dict[str, Any]]] = None,
    round_num: int = 1,
) -> Dict[str, Any]:
    strategist.data_file = data_file
    strategist.sheet_name = sheet_name
    columns_semantic = strategist._describe_columns_semantics(available_columns)

    data_preview_text = None
    try:
        data_preview_text = DataPreview.from_file(data_file, sheet_name).to_prompt_string()
    except Exception as exc:
        strategist.log(f"⚠️ Single-agent baseline 的 DataPreview 生成失败: {exc}", "warning")

    is_feedback_round = round_num > 1 and previous_results
    task_count_hint = "2-3" if is_feedback_round else "2-4"
    feedback_section = _format_previous_results(previous_results or [])

    prompt_template = """你是一名单智能体专利分析代理。你不能调用知识图谱、方法图谱或预生成的数据洞察模块，
只能基于研究问题、真实列名、数据预览以及{feedback_source}来一次性规划分析任务。

**研究目标**
{user_goal}

**当前数据文件**
- data_file: {data_file}
- sheet_name: {sheet_name}

**真实列名及语义**
{columns_semantic}

**数据预览**
{data_preview_text}

**执行反馈**
{feedback_section}

**规划要求**
1. 采用 ReAct 风格的“先审题、再自检、再给出任务图”的单智能体规划方式，但最终只输出 JSON。
2. 不能使用任何外部知识图谱、因果假设或额外的数据洞察结论。
3. 所有列名必须直接从上面的真实列名中复制，不能自创列名。
4. 任务数控制在 {task_count_hint} 个。
5. 每个任务必须输出结论性结果，优先 JSON 汇总，不要输出大规模中间矩阵。
6. 如果提供了执行反馈，第二轮只能围绕“修复失败任务、深化第一轮有效发现、补足关键空白”来设计，不要完全重写主题。
7. 数据源路径必须写为 `{data_file}`，sheet 名必须写为 `{sheet_name}`。

**输出格式（严格 JSON）**
{{
  "thinking_trace": {{
    "problem_framing": "对研究目标的理解",
    "data_audit": "对关键列和可用证据的审计",
    "strategy_rationale": "为什么这样拆解任务",
    "self_check": "如何避免常识性结论和无效任务"
  }},
  "research_objective": "研究目标简述",
  "expected_outcomes": ["预期成果1", "预期成果2"],
  "task_graph": [
    {{
      "task_id": "task_1",
      "task_type": "analysis",
      "question": "本任务回答的问题",
      "input_variables": [],
      "output_variables": ["result_1"],
      "dependencies": [],
      "description": "任务说明",
      "implementation_config": {{
        "data_source": "{data_file}",
        "sheet_name": "{sheet_name}",
        "columns_to_load": ["<列名1>", "<列名2>"],
        "parameters": {{}},
        "output_format": "json",
        "output_file": "outputs/task_1_result.json",
        "output_content": {{
          "key_findings": "关键发现"
        }}
      }}
    }}
  ]
}}

只输出 JSON，不要其他文字。"""

    last_blueprint: Dict[str, Any] = {"research_objective": user_goal, "task_graph": []}
    for attempt in range(3):
        retry_note = ""
        if attempt > 0:
            retry_note = (
                "\n\n补充要求：上一次输出存在列名或依赖问题。请严格检查 task_graph 的依赖、"
                "输入输出变量和 columns_to_load。"
            )
        prompt = prompt_template.format(
            feedback_source="执行反馈" if is_feedback_round else "真实数据证据",
            user_goal=user_goal,
            data_file=data_file,
            sheet_name=sheet_name,
            columns_semantic=columns_semantic,
            data_preview_text=data_preview_text or "（未提供数据预览）",
            feedback_section=feedback_section,
            task_count_hint=task_count_hint,
        ) + retry_note
        response = strategist.llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = _strip_json_fence(content)
        try:
            blueprint = json.loads(content)
        except json.JSONDecodeError:
            last_blueprint = {
                "error": "single_agent_json_decode_failed",
                "raw_response": content,
                "research_objective": user_goal,
                "task_graph": [],
            }
            continue

        blueprint = _normalize_blueprint_data_source(blueprint, data_file, sheet_name)
        last_blueprint = blueprint
        if strategist._check_graph_integrity(blueprint, available_columns):
            break

    return {
        "blueprint": last_blueprint,
        "data_preview": data_preview_text,
    }


def _collect_previous_results(round_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    previous_results = []
    for task, coding_result in zip(round_result.get("task_graph", []), round_result.get("coding_results", [])):
        previous_results.append({
            "task_id": task.get("task_id", ""),
            "question": task.get("question", ""),
            "status": "success" if coding_result.get("is_code_valid") else "failed",
            "key_findings": coding_result.get("execution_output", "")[:500] if coding_result.get("is_code_valid") else "",
        })
    return previous_results


def run_single_experiment(
    mode: str,
    user_goal: str,
    strategist,
    methodologist,
    coding_agent,
    test_data,
    *,
    data_file: str = "data/new_data.xlsx",
    sheet_name: str = "sheet1",
):
    """
    运行单次实验

    Args:
        mode: "D_baseline0" | "A_template" | "B_data_aware" | "C_iterative" |
              "E_ablate_data" | "F_ablate_kg" | "G_react_single_agent" | "H_execution_feedback"
        user_goal: 研究问题
    """
    print(f"\n{'='*80}")
    print(f"实验模式: {mode} | 问题: {user_goal}")
    print(f"{'='*80}")

    mode_config = get_mode_config(mode)
    available_columns = list(test_data.columns)

    def run_round(strategist_input, round_label="", planner_kind="strategist"):
        """执行一轮完整的 Strategist → Methodologist → CodingAgent"""
        print(f"\n--- {round_label} Strategist ---")
        t0 = time.time()
        if planner_kind == "strategist":
            blueprint_result = strategist.process(strategist_input)
        elif planner_kind == "single_agent":
            blueprint_result = _build_single_agent_blueprint(
                strategist=strategist,
                user_goal=strategist_input["user_goal"],
                data_file=strategist_input["data_file"],
                sheet_name=strategist_input["sheet_name"],
                available_columns=available_columns,
                previous_results=strategist_input.get("previous_results"),
                round_num=int(strategist_input.get("round", 1)),
            )
        else:
            raise ValueError(f"未知 planner_kind: {planner_kind}")
        t_strat = time.time() - t0
        blueprint = blueprint_result.get('blueprint', {})
        task_graph = blueprint.get('task_graph', [])
        print(f"  生成 {len(task_graph)} 个任务 ({t_strat:.1f}s)")

        if blueprint_result.get('data_insights'):
            n_ins = len(blueprint_result['data_insights'].get('insights', []))
            print(f"  数据洞察: {n_ins} 条")

        # Methodologist
        print(f"\n--- {round_label} Methodologist ---")
        specs = []
        for task in task_graph:
            spec_result = methodologist.process({'task_node': task})
            if 'error' not in spec_result.get('technical_spec', {}):
                specs.append(spec_result)
            else:
                print(f"  任务 {task['task_id']} 规格生成失败")
                specs.append(spec_result)

        # CodingAgent
        print(f"\n--- {round_label} CodingAgent ---")
        coding_results = []
        success_count = 0
        for i, (task, spec_result) in enumerate(zip(task_graph, specs)):
            if 'error' in spec_result.get('technical_spec', {}):
                coding_results.append({'is_code_valid': False, 'error': 'spec failed'})
                continue
            coding_input = {
                'execution_spec': spec_result['technical_spec'],
                'current_step': task,
                'test_data': test_data,
                'previous_result': coding_results[-1] if coding_results else None
            }
            try:
                result = coding_agent.process(coding_input)
                coding_results.append(result)
                if result.get('is_code_valid', False):
                    success_count += 1
                    print(f"  {task['task_id']}: OK ({result.get('iteration_count',0)} iters)")
                else:
                    print(f"  {task['task_id']}: FAIL")
            except Exception as e:
                coding_results.append({'is_code_valid': False, 'error': str(e)})
                print(f"  {task['task_id']}: EXCEPTION {e}")

        return {
            'blueprint_result': blueprint_result,
            'task_graph': task_graph,
            'specs': specs,
            'coding_results': coding_results,
            'success_count': success_count,
            'total_tasks': len(task_graph),
            'strategist_time': t_strat,
        }

    base_input = {
        "user_goal": user_goal,
        "data_file": data_file,
        "sheet_name": sheet_name,
        "use_dag": True,
    }
    if mode_config.disable_data_insights:
        base_input["disable_data_insights"] = True
    if mode_config.disable_causal_hypotheses:
        base_input["disable_causal_hypotheses"] = True

    label_prefix = mode.split("_", 1)[0]
    rounds = []
    first_round_input = dict(base_input)
    if mode_config.rounds > 1:
        first_round_input["round"] = 1
    first_round = run_round(
        first_round_input,
        round_label=f"[{label_prefix}-R1]" if mode_config.rounds > 1 else f"[{label_prefix}]",
        planner_kind=mode_config.planner_kind,
    )
    rounds.append(first_round)

    if mode_config.rounds > 1:
        previous_results = _collect_previous_results(first_round)
        second_round_input = dict(base_input)
        second_round_input["round"] = 2
        second_round_input["previous_results"] = previous_results
        second_round = run_round(
            second_round_input,
            round_label=f"[{label_prefix}-R2]",
            planner_kind=mode_config.planner_kind,
        )
        rounds.append(second_round)

    return {"mode": mode, "rounds": rounds}


def run_comparison_experiment():
    """运行 A/B/C/D 四方案对比实验"""
    print("\n" + "=" * 80)
    print("四方案对比实验")
    print("=" * 80)

    Path('outputs').mkdir(exist_ok=True)

    # 初始化组件
    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")

    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph,
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)

    test_data = load_test_data("data/new_data.XLSX", "sheet1")
    if test_data is None:
        print("无法加载测试数据")
        return

    # 研究问题
    questions = [
        "分析数据安全领域的技术影响力驱动因素",
        "识别数据安全领域的技术融合趋势",
        "评估不同国家/地区在数据安全领域的竞争态势",
    ]

    modes = ["D_baseline0", "A_template", "B_data_aware", "C_iterative", "E_ablate_data", "F_ablate_kg"]
    all_results = []

    for q_idx, question in enumerate(questions, 1):
        for mode in modes:
            print(f"\n{'#'*80}")
            print(f"问题 {q_idx}/{len(questions)} × 模式 {mode}")
            print(f"{'#'*80}")
            try:
                exp_result = run_single_experiment(
                    mode, question, strategist, methodologist, coding_agent, test_data
                )
                exp_result['question'] = question
                all_results.append(exp_result)

                # 保存每次实验结果
                fname = f"outputs/experiment_q{q_idx}_{mode}.json"
                with open(fname, 'w', encoding='utf-8') as f:
                    # 简化保存（去掉大对象）
                    save_data = {
                        'mode': mode,
                        'question': question,
                        'rounds': [{
                            'total_tasks': r['total_tasks'],
                            'success_count': r['success_count'],
                            'strategist_time': r['strategist_time'],
                            'has_insights': 'data_insights' in r['blueprint_result'],
                            'has_graph_preview': 'graph_preview' in r['blueprint_result'],
                            'blueprint': r['blueprint_result'].get('blueprint', {}),
                        } for r in exp_result['rounds']]
                    }
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                print(f"保存: {fname}")
            except Exception as e:
                print(f"实验失败: {e}")
                import traceback
                traceback.print_exc()

    # 汇总对比
    print("\n" + "=" * 80)
    print("实验汇总")
    print("=" * 80)
    print(f"{'问题':<30} {'模式':<15} {'任务数':<8} {'成功数':<8} {'成功率':<8} {'有洞察':<8}")
    print("-" * 90)
    for r in all_results:
        q_short = r['question'][:28]
        for rd in r['rounds']:
            rate = f"{rd['success_count']/rd['total_tasks']*100:.0f}%" if rd['total_tasks'] > 0 else "N/A"
            has_ins = "data_insights" in rd['blueprint_result']
            print(f"{q_short:<30} {r['mode']:<15} {rd['total_tasks']:<8} {rd['success_count']:<8} {rate:<8} {str(has_ins):<8}")

    # 保存汇总
    summary_file = "outputs/experiment_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        summary = [{
            'question': r['question'],
            'mode': r['mode'],
            'rounds': [{
                'total_tasks': rd['total_tasks'],
                'success_count': rd['success_count'],
            } for rd in r['rounds']]
        } for r in all_results]
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n汇总已保存: {summary_file}")


def run_baseline0_only():
    """仅运行 D_baseline0 的 3 组实验（不重跑已有的 A/B/C）"""
    print("\n" + "=" * 80)
    print("Baseline0 纯 LLM 基线实验")
    print("=" * 80)

    Path('outputs').mkdir(exist_ok=True)

    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")

    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph,
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)

    test_data = load_test_data("data/new_data.XLSX", "sheet1")
    if test_data is None:
        print("无法加载测试数据")
        return

    questions = [
        "分析数据安全领域的技术影响力驱动因素",
        "识别数据安全领域的技术融合趋势",
        "评估不同国家/地区在数据安全领域的竞争态势",
    ]

    mode = "D_baseline0"
    for q_idx, question in enumerate(questions, 1):
        print(f"\n{'#'*80}")
        print(f"问题 {q_idx}/{len(questions)} × 模式 {mode}")
        print(f"{'#'*80}")
        try:
            exp_result = run_single_experiment(
                mode, question, strategist, methodologist, coding_agent, test_data
            )
            exp_result['question'] = question

            fname = f"outputs/experiment_q{q_idx}_{mode}.json"
            with open(fname, 'w', encoding='utf-8') as f:
                save_data = {
                    'mode': mode,
                    'question': question,
                    'rounds': [{
                        'total_tasks': r['total_tasks'],
                        'success_count': r['success_count'],
                        'strategist_time': r['strategist_time'],
                        'has_insights': 'data_insights' in r['blueprint_result'],
                        'has_graph_preview': 'graph_preview' in r['blueprint_result'],
                        'blueprint': r['blueprint_result'].get('blueprint', {}),
                    } for r in exp_result['rounds']]
                }
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"保存: {fname}")
        except Exception as e:
            print(f"实验失败: {e}")
            import traceback
            traceback.print_exc()

    print("\nBaseline0 实验完成！")


def run_ablation_only():
    """仅运行 E_ablate_data 和 F_ablate_kg 的 6 组消融实验"""
    print("\n" + "=" * 80)
    print("消融实验：E_ablate_data + F_ablate_kg")
    print("=" * 80)

    Path('outputs').mkdir(exist_ok=True)

    llm = get_llm_client()
    coding_llm = get_llm_client(env_prefix="CODING_")
    causal_graph = CausalGraphQuery("src/graphs/data/causal/causal_ontology_extracted.json")
    method_graph = MethodGraphQuery("src/graphs/data/method/method_knowledge_base.json")

    strategist = StrategistAgent(
        llm_client=llm,
        causal_graph=causal_graph,
        method_graph=method_graph,
    )
    methodologist = MethodologistAgent(llm_client=llm)
    coding_agent = CodingAgentV4_2(llm_client=coding_llm, max_iterations=15)

    test_data = load_test_data("data/new_data.XLSX", "sheet1")
    if test_data is None:
        print("无法加载测试数据")
        return

    questions = [
        "分析数据安全领域的技术影响力驱动因素",
        "识别数据安全领域的技术融合趋势",
        "评估不同国家/地区在数据安全领域的竞争态势",
    ]

    ablation_modes = ["E_ablate_data", "F_ablate_kg"]
    for q_idx, question in enumerate(questions, 1):
        for mode in ablation_modes:
            print(f"\n{'#'*80}")
            print(f"问题 {q_idx}/{len(questions)} × 模式 {mode}")
            print(f"{'#'*80}")
            try:
                exp_result = run_single_experiment(
                    mode, question, strategist, methodologist, coding_agent, test_data
                )
                exp_result['question'] = question

                fname = f"outputs/experiment_q{q_idx}_{mode}.json"
                with open(fname, 'w', encoding='utf-8') as f:
                    save_data = {
                        'mode': mode,
                        'question': question,
                        'rounds': [{
                            'total_tasks': r['total_tasks'],
                            'success_count': r['success_count'],
                            'strategist_time': r['strategist_time'],
                            'has_insights': 'data_insights' in r['blueprint_result'],
                            'has_graph_preview': 'graph_preview' in r['blueprint_result'],
                            'blueprint': r['blueprint_result'].get('blueprint', {}),
                        } for r in exp_result['rounds']]
                    }
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                print(f"保存: {fname}")
            except Exception as e:
                print(f"实验失败: {e}")
                import traceback
                traceback.print_exc()

    print("\n消融实验完成！")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        run_comparison_experiment()
    elif len(sys.argv) > 1 and sys.argv[1] == "--baseline0":
        run_baseline0_only()
    elif len(sys.argv) > 1 and sys.argv[1] == "--ablation":
        run_ablation_only()
    else:
        test_full_pipeline()
