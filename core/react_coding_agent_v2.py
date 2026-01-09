"""
ReAct Coding Agent V2 - 增强版
新增功能：运行时测试和自动修复
"""

import os
import json
import pandas as pd
import numpy as np
from typing import TypedDict, Dict, Any, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================================
# 状态定义
# ============================================================================

class ReactCodingStateV2(TypedDict):
    """ReAct Coding Agent V2 状态"""
    execution_spec: dict
    current_step: dict
    test_data: pd.DataFrame  # 新增：测试数据
    
    thought: str
    action: str
    observation: str
    
    generated_code: str
    code_issues: List[str]
    runtime_error: str  # 新增：运行时错误
    iteration_count: int
    is_code_valid: bool


# ============================================================================
# LLM 配置
# ============================================================================

def get_llm() -> ChatOpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return ChatOpenAI(
        model="qwen-max",
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        openai_api_key=api_key,
        temperature=0.3,
    )


# ============================================================================
# 节点实现
# ============================================================================

def think_node_v2(state: ReactCodingStateV2) -> Dict[str, Any]:
    """思考节点 V2"""
    print("\n" + "="*70)
    print("🤔 [思考] 分析任务需求...")
    print("="*70)
    
    execution_spec = state['execution_spec']
    current_step = state['current_step']
    iteration = state.get('iteration_count', 0)
    previous_issues = state.get('code_issues', [])
    runtime_error = state.get('runtime_error', '')
    
    llm = get_llm()
    
    prompt = f"""你是资深 Python 工程师。分析任务需求，规划代码结构。

**执行规格:**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}

**原始步骤:**
{json.dumps(current_step, indent=2, ensure_ascii=False)}

"""
    
    if iteration > 0:
        if previous_issues:
            prompt += f"""
**上一次代码的静态检查问题:**
{chr(10).join(f'- {issue}' for issue in previous_issues)}
"""
        if runtime_error:
            prompt += f"""
**上一次代码的运行时错误:**
{runtime_error}

**重要**: 请特别注意修复这个运行时错误！
"""
    
    prompt += """
**输出 JSON:**
{
  "task_understanding": "任务理解",
  "key_challenges": ["挑战1", "挑战2"],
  "code_structure": {
    "main_function": "主函数功能",
    "error_handling": "错误处理策略"
  },
  "implementation_plan": ["步骤1", "步骤2"]
}

只输出 JSON。"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        thought = json.loads(content)
        print(f"  ✓ 任务理解: {thought.get('task_understanding', 'N/A')[:80]}...")
        
        return {
            'thought': json.dumps(thought, ensure_ascii=False),
            'iteration_count': iteration
        }
        
    except Exception as e:
        print(f"  ⚠️ 思考失败: {e}")
        return {
            'thought': f"思考失败: {e}",
            'iteration_count': iteration
        }


def act_node_v2(state: ReactCodingStateV2) -> Dict[str, Any]:
    """行动节点 V2"""
    print("\n" + "="*70)
    print("⚡ [行动] 生成代码...")
    print("="*70)
    
    execution_spec = state['execution_spec']
    thought = state['thought']
    previous_issues = state.get('code_issues', [])
    runtime_error = state.get('runtime_error', '')
    
    llm = get_llm()
    
    prompt = f"""你是 Python 工程师。根据思考结果生成代码。

**思考结果:**
{thought}

**执行规格:**
{json.dumps(execution_spec, indent=2, ensure_ascii=False)}

"""
    
    if previous_issues or runtime_error:
        prompt += "**需要修复的问题:**\n"
        if previous_issues:
            for issue in previous_issues:
                prompt += f"- {issue}\n"
        if runtime_error:
            prompt += f"- 运行时错误: {runtime_error}\n"
        prompt += "\n**请特别注意修复这些问题！**\n\n"
    
    prompt += f"""
**代码要求:**
1. 函数签名: def {execution_spec.get('function_name', 'analyze')}(df: pd.DataFrame) -> Dict[str, Any]
2. 完整类型注解
3. 详细中文注释
4. 完整错误处理
5. **重要**: 使用 df.iloc[i] 而不是 df.loc[i] 来访问行
6. **重要**: 检查索引是否越界
7. 不要包含 import 语句

只输出函数代码。"""

    try:
        response = llm.invoke(prompt)
        code = response.content.strip()
        
        if code.startswith("```"):
            lines = code.split("\n")
            code_lines = []
            in_code = False
            for line in lines:
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)
            code = "\n".join(code_lines)
        
        # 移除 import 语句
        code_lines = code.split("\n")
        filtered_lines = []
        for line in code_lines:
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                filtered_lines.append(line)
        code = "\n".join(filtered_lines)
        
        print(f"  ✓ 代码生成成功 ({len(code.split(chr(10)))} 行)")
        
        return {
            'generated_code': code,
            'action': 'generate_code'
        }
        
    except Exception as e:
        print(f"  ⚠️ 代码生成失败: {e}")
        return {
            'generated_code': '',
            'action': f'generate_code_failed: {e}'
        }


def test_runtime_node(state: ReactCodingStateV2) -> Dict[str, Any]:
    """新增：运行时测试节点"""
    print("\n" + "="*70)
    print("🧪 [测试] 运行时测试...")
    print("="*70)
    
    code = state['generated_code']
    execution_spec = state['execution_spec']
    test_data = state.get('test_data')
    
    if test_data is None or len(test_data) == 0:
        print("  ⚠️ 没有测试数据，跳过运行时测试")
        return {'runtime_error': ''}
    
    print(f"  📊 使用 {len(test_data)} 条数据进行测试...")
    
    try:
        # 准备执行环境
        from pyod.models.abod import ABOD
        from sentence_transformers import SentenceTransformer
        
        exec_globals = {
            'pd': pd,
            'np': np,
            'df': test_data,
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
        func_name = execution_spec.get('function_name', 'analyze')
        if func_name in exec_globals:
            result = exec_globals[func_name](test_data)
            
            if 'error' in result:
                error_msg = result['error']
                print(f"  ⚠️ 函数返回错误: {error_msg}")
                return {'runtime_error': error_msg}
            else:
                print(f"  ✅ 运行时测试通过")
                return {'runtime_error': ''}
        else:
            error_msg = f"函数 {func_name} 未找到"
            print(f"  ⚠️ {error_msg}")
            return {'runtime_error': error_msg}
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠️ 运行时错误: {error_msg}")
        return {'runtime_error': error_msg}


def observe_node_v2(state: ReactCodingStateV2) -> Dict[str, Any]:
    """观察节点 V2 - 包含运行时检查"""
    print("\n" + "="*70)
    print("👀 [观察] 检查代码质量...")
    print("="*70)
    
    code = state['generated_code']
    execution_spec = state['execution_spec']
    runtime_error = state.get('runtime_error', '')
    
    issues = []
    
    # 静态检查
    if not code or len(code.strip()) < 50:
        issues.append("代码为空或过短")
    
    func_name = execution_spec.get('function_name', 'analyze')
    if f"def {func_name}" not in code:
        issues.append(f"缺少函数定义: {func_name}")
    
    if "return" not in code:
        issues.append("缺少 return 语句")
    
    if "try:" not in code or "except" not in code:
        issues.append("缺少错误处理")
    
    if "Dict" not in code and "dict" not in code.lower():
        issues.append("缺少返回类型注解")
    
    # 语法检查
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        issues.append(f"语法错误: {e}")
    
    # 运行时检查
    if runtime_error:
        issues.append(f"运行时错误: {runtime_error}")
    
    is_valid = len(issues) == 0
    
    if is_valid:
        print("  ✅ 代码质量检查通过（包括运行时测试）")
        observation = "代码质量良好，所有检查通过"
    else:
        print(f"  ⚠️ 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"    - {issue}")
        observation = f"发现 {len(issues)} 个问题需要修复"
    
    return {
        'observation': observation,
        'code_issues': issues,
        'is_code_valid': is_valid
    }


def reflect_node_v2(state: ReactCodingStateV2) -> Dict[str, Any]:
    """反思节点 V2"""
    print("\n" + "="*70)
    print("🔄 [反思] 评估是否需要重新生成...")
    print("="*70)
    
    is_valid = state['is_code_valid']
    iteration = state['iteration_count']
    max_iterations = 3
    
    if is_valid:
        print("  ✅ 代码质量合格（包括运行时测试），流程结束")
        return {'iteration_count': iteration}
    
    if iteration >= max_iterations:
        print(f"  ⚠️ 已达到最大迭代次数 ({max_iterations})，使用当前代码")
        return {'iteration_count': iteration, 'is_code_valid': True}
    
    print(f"  🔄 代码需要改进，开始第 {iteration + 1} 次迭代")
    return {'iteration_count': iteration + 1}


def should_continue_v2(state: ReactCodingStateV2) -> str:
    """条件边"""
    is_valid = state.get('is_code_valid', False)
    iteration = state.get('iteration_count', 0)
    max_iterations = 3
    
    if is_valid or iteration >= max_iterations:
        return "end"
    else:
        return "continue"


# ============================================================================
# 构建工作流
# ============================================================================

def build_react_coding_agent_v2():
    """构建 ReAct Coding Agent V2"""
    print("\n🔧 构建 ReAct Coding Agent V2 (with Runtime Testing)...")
    
    workflow = StateGraph(ReactCodingStateV2)
    
    workflow.add_node("think", think_node_v2)
    workflow.add_node("act", act_node_v2)
    workflow.add_node("test_runtime", test_runtime_node)  # 新增
    workflow.add_node("observe", observe_node_v2)
    workflow.add_node("reflect", reflect_node_v2)
    
    workflow.set_entry_point("think")
    
    workflow.add_edge("think", "act")
    workflow.add_edge("act", "test_runtime")  # 新增：先测试
    workflow.add_edge("test_runtime", "observe")  # 再观察
    workflow.add_edge("observe", "reflect")
    
    workflow.add_conditional_edges(
        "reflect",
        should_continue_v2,
        {
            "continue": "think",
            "end": END
        }
    )
    
    print("  ✓ ReAct V2 工作流构建完成")
    print("  流程: Think → Act → Test → Observe → Reflect → [继续/结束]")
    
    return workflow.compile()


# ============================================================================
# 测试函数
# ============================================================================

def test_react_v2():
    """测试 ReAct Agent V2"""
    print("\n" + "="*70)
    print("🧪 测试 ReAct Coding Agent V2")
    print("="*70)
    
    # 准备测试数据
    test_data = pd.DataFrame({
        '标题': ['专利A', '专利B', '专利C', '专利D', '专利E'] * 4,
        '摘要': ['摘要A', '摘要B', '摘要C', '摘要D', '摘要E'] * 4,
        'IPC': ['G06F', 'H04L', 'G06F', 'H04L', 'G06F'] * 4
    })
    
    test_spec = {
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
    
    test_step = {
        "objective": "发现潜在的技术空白",
        "method_name": "Angle-based Outlier Detection"
    }
    
    # 构建并执行
    agent = build_react_coding_agent_v2()
    
    try:
        result = agent.invoke({
            'execution_spec': test_spec,
            'current_step': test_step,
            'test_data': test_data,  # 提供测试数据
            'thought': '',
            'action': '',
            'observation': '',
            'generated_code': '',
            'code_issues': [],
            'runtime_error': '',
            'iteration_count': 0,
            'is_code_valid': False
        })
        
        print("\n" + "="*70)
        print("📊 执行结果")
        print("="*70)
        print(f"  迭代次数: {result['iteration_count']}")
        print(f"  代码有效: {result['is_code_valid']}")
        print(f"  运行时错误: {result.get('runtime_error', '无')}")
        
        # 保存代码
        output_file = "react_v2_generated_code.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# ReAct Coding Agent V2 生成的代码\n\n")
            f.write("from typing import Dict, List, Any\n")
            f.write("import pandas as pd\n")
            f.write("import numpy as np\n")
            f.write("from pyod.models.abod import ABOD\n")
            f.write("from sentence_transformers import SentenceTransformer\n\n")
            f.write(result['generated_code'])
        
        print(f"\n  ✓ 代码已保存: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_react_v2()
