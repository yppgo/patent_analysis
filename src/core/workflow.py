"""
工作流编排 - 执行即迭代版本
使用 LangGraph 编排三个 Agent 的协作
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.core.state import WorkflowState
import pandas as pd


def build_full_workflow(strategist, methodologist, coding_agent, reviewer=None):
    """
    构建完整的四 Agent 协作工作流
    
    Args:
        strategist: Strategist Agent 实例
        methodologist: Methodologist Agent 实例
        coding_agent: Coding Agent 实例
        reviewer: Reviewer Agent 实例（可选）
        
    Returns:
        编译后的工作流
    """
    
    def strategist_node(state: WorkflowState) -> Dict[str, Any]:
        """Strategist 节点"""
        result = strategist.process({'user_goal': state['user_goal']})
        
        # 立即保存蓝图到文件（方便调试）
        import json
        from pathlib import Path
        Path('outputs').mkdir(exist_ok=True)
        with open('outputs/blueprint.json', 'w', encoding='utf-8') as f:
            json.dump(result['blueprint'], f, ensure_ascii=False, indent=2)
        print("  💾 蓝图已保存: outputs/blueprint.json")
        
        return {
            'blueprint': result['blueprint'],
            'graph_context': result.get('graph_context', '')
        }
    
    def methodologist_node(state: WorkflowState) -> Dict[str, Any]:
        """Methodologist 节点"""
        blueprint = state['blueprint']
        steps = blueprint.get('analysis_logic_chains', [])
        
        # 处理所有步骤
        execution_specs = methodologist.process_multiple(steps)
        
        # 立即保存执行规格到文件（方便调试）
        import json
        from pathlib import Path
        Path('outputs').mkdir(exist_ok=True)
        with open('outputs/execution_specs.json', 'w', encoding='utf-8') as f:
            json.dump(execution_specs, f, ensure_ascii=False, indent=2)
        print("  💾 执行规格已保存: outputs/execution_specs.json")
        
        return {'execution_specs': execution_specs}
    
    def coding_node(state: WorkflowState) -> Dict[str, Any]:
        """Coding Agent 节点 - 执行即迭代版本（带数据持久化）"""
        execution_specs = state['execution_specs']
        blueprint = state['blueprint']
        steps = blueprint.get('analysis_logic_chains', [])
        test_data = state.get('test_data')
        
        # 调试日志
        print(f"[DEBUG] coding_node: test_data is None = {test_data is None}")
        if test_data is not None:
            print(f"[DEBUG] coding_node: type(test_data) = {type(test_data)}")
            print(f"[DEBUG] coding_node: len(test_data) = {len(test_data)}")
        
        # 🔥 关键修复：创建 DataFrame 的副本，用于累积所有步骤的结果
        current_df = test_data.copy() if test_data is not None else None
        
        generated_codes = []
        code_metadata = []
        analysis_results = []
        
        # 准备执行环境（不传递 df，让代码自己加载）
        import joblib
        from pathlib import Path
        
        exec_globals = {
            'pd': pd,
            'joblib': joblib,
            'Path': Path,
            '__builtins__': __builtins__
        }
        
        for i, (spec, step) in enumerate(zip(execution_specs, steps), 1):
            if 'error' in spec:
                generated_codes.append('')
                code_metadata.append({'error': spec['error']})
                analysis_results.append(None)
                continue
            
            # 获取前一步的结果
            previous_result = analysis_results[-1] if analysis_results else None
            
            print(f"[执行] 步骤 {i}: {spec.get('function_name', 'unknown')}")
            
            # 清理该步骤的旧结果文件，避免误判
            step_id = step.get('step_id', i)
            old_result_file = Path(f"outputs/step_{step_id}_results.csv")
            if old_result_file.exists():
                try:
                    old_result_file.unlink()
                    print(f"  🗑️ 已删除旧结果文件: {old_result_file}")
                except Exception as e:
                    print(f"  ⚠️ 无法删除旧文件: {e}")
            
            # 🔥 执行即迭代：最多尝试 3 次
            max_iterations = 3
            final_code = None
            final_result = None
            iteration_count = 0
            
            for iteration in range(max_iterations):
                iteration_count = iteration + 1
                
                if iteration > 0:
                    print(f"  🔄 迭代 {iteration + 1}/{max_iterations}")
                
                # 传递当前步骤信息
                result = coding_agent.process({
                    'execution_spec': spec,
                    'current_step': step,
                    'test_data': current_df,
                    'previous_result': previous_result,
                    'previous_error': final_result.get('error') if final_result and isinstance(final_result, dict) and 'error' in final_result else None
                })
                
                code = result['generated_code']
                final_code = code
                is_code_valid = result.get('is_code_valid', False)
                runtime_error = result.get('runtime_error', '')
                
                # 保存生成的代码到文件
                if code:
                    step_id = step.get('step_id', i)
                    code_file = f"outputs/step_{step_id}.py"
                    with open(code_file, 'w', encoding='utf-8') as f:
                        f.write(code)
                    print(f"  💾 代码已保存: {code_file}")
                
                # 代码已在 Coding Agent 的 REPL 中执行，不需要再次执行
                # 检查执行结果
                if not code:
                    final_result = {'error': '代码生成失败'}
                    print(f"  ❌ 代码生成失败")
                    if iteration < max_iterations - 1:
                        continue
                    else:
                        break
                
                # 检查 Coding Agent 的执行状态
                if not is_code_valid:
                    final_result = {'error': f'代码执行失败: {runtime_error}'}
                    print(f"  ❌ 代码执行失败")
                    if iteration < max_iterations - 1:
                        continue
                    else:
                        break
                
                try:
                    # 读取生成的结果文件，获取列信息
                    step_id = step.get('step_id', i)
                    result_file = f"outputs/step_{step_id}_results.csv"
                    
                    result_info = {'success': True}
                    if Path(result_file).exists():
                        result_df = pd.read_csv(result_file)
                        result_info['columns'] = list(result_df.columns)
                        result_info['shape'] = result_df.shape
                        result_info['file'] = result_file
                        print(f"  📊 结果文件: {result_file}, 列: {result_info['columns']}")
                        print(f"  ✅ 执行成功")
                        final_result = result_info
                        break  # 成功，退出迭代循环
                    else:
                        print(f"  ⚠️ 结果文件不存在: {result_file}")
                        result_info['success'] = False
                        result_info['error'] = f"结果文件不存在: {result_file}"
                        final_result = result_info
                        
                        # 如果还有迭代机会，继续循环
                        if iteration < max_iterations - 1:
                            continue
                        else:
                            break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ 验证失败: {error_msg}")
                    
                    final_result = {'error': error_msg}
                    
                    # 如果还有迭代机会，继续循环
                    if iteration < max_iterations - 1:
                        continue
                    else:
                        break
            
            # 保存结果
            generated_codes.append(final_code or '')
            code_metadata.append({
                'iteration_count': iteration_count,
                'is_valid': final_result and (not isinstance(final_result, dict) or 'error' not in final_result),
                'issues': [],
                'runtime_error': final_result.get('error', '') if isinstance(final_result, dict) else ''
            })
            analysis_results.append(final_result)
        
        # 返回结果（不再需要累积 DataFrame）
        return {
            'generated_codes': generated_codes,
            'code_metadata': code_metadata,
            'analysis_results': analysis_results
        }
    
    def reviewer_node(state: WorkflowState) -> Dict[str, Any]:
        """Reviewer 节点"""
        if reviewer is None:
            return {
                'verification_result': {'passed': True, 'message': 'Reviewer 未启用'},
                'final_report': '报告生成功能未启用',
                'writeback_status': '回写功能未启用'
            }
        
        result = reviewer.process({
            'user_goal': state['user_goal'],
            'blueprint': state['blueprint'],
            'execution_specs': state['execution_specs'],
            'generated_codes': state['generated_codes'],
            'code_metadata': state['code_metadata'],
            'analysis_results': state.get('analysis_results', [])
        })
        
        return {
            'verification_result': result['verification_result'],
            'final_report': result['final_report'],
            'writeback_status': result['writeback_status']
        }
    
    # 构建工作流
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("methodologist", methodologist_node)
    workflow.add_node("coding", coding_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # 设置入口
    workflow.set_entry_point("strategist")
    
    # 添加边
    workflow.add_edge("strategist", "methodologist")
    workflow.add_edge("methodologist", "coding")
    workflow.add_edge("coding", "reviewer")
    workflow.add_edge("reviewer", END)
    
    return workflow.compile()
