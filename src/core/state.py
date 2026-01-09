"""
工作流状态定义
定义整个系统的数据流和状态管理
"""

from typing import TypedDict, List, Dict, Any, Optional


class WorkflowState(TypedDict, total=False):
    """
    完整工作流的状态
    
    数据流：
    user_goal → blueprint → execution_specs → generated_codes → analysis_results → final_report
    """
    
    # ========== 输入 ==========
    user_goal: str                      # 用户研究目标
    test_data: Any                      # 测试数据（用于代码执行）
    
    # ========== Strategist 输出 ==========
    graph_context: str                  # 从知识图谱检索的上下文
    blueprint: Dict[str, Any]           # 战略蓝图（包含多个分析步骤）
    
    # ========== Methodologist 输出 ==========
    execution_specs: List[Dict]         # 执行规格列表（每个步骤一个）
    
    # ========== Coding Agent 输出 ==========
    generated_codes: List[str]          # 生成的代码列表
    code_metadata: List[Dict]           # 代码元数据（迭代次数、质量等）
    
    # ========== 执行结果 ==========
    analysis_results: List[Dict]        # 分析结果列表
    
    # ========== Reviewer 输出 ==========
    verification_result: Dict[str, Any] # 验证结果
    final_report: str                   # 最终分析报告
    writeback_status: str               # 回写状态
    
    # ========== 元数据 ==========
    errors: List[str]                   # 错误列表
    warnings: List[str]                 # 警告列表
    execution_time: float               # 执行时间（秒）


class StrategistState(TypedDict, total=False):
    """Strategist Agent 的内部状态"""
    user_goal: str
    search_keywords: List[str]
    graph_context: str
    blueprint: Dict[str, Any]
    iteration_count: int


class MethodologistState(TypedDict, total=False):
    """Methodologist Agent 的内部状态"""
    step: Dict[str, Any]                # 输入的步骤
    execution_spec: Dict[str, Any]      # 输出的执行规格
    iteration_count: int


class CodingAgentState(TypedDict, total=False):
    """Coding Agent 的内部状态（ReAct 模式）"""
    execution_spec: Dict[str, Any]
    current_step: Dict[str, Any]
    test_data: Any                      # 测试数据
    
    # ReAct 循环
    thought: str                        # 思考
    action: str                         # 行动
    observation: str                    # 观察
    
    # 代码生成
    generated_code: str
    code_issues: List[str]
    runtime_error: str
    
    # 代码执行结果
    execution_result: Optional[Dict[str, Any]]  # 代码实际运行的结果
    
    # 控制
    iteration_count: int
    is_code_valid: bool
