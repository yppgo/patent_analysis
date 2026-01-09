"""
三 Agent 协作系统
基于 LangGraph 的智能专利分析代码生成系统
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from src.agents import (
    BaseAgent,
    StrategistAgent,
    MethodologistAgent,
    CodingAgentV2
)

from src.core import (
    CodingAgentState,
    WorkflowState,
    build_full_workflow
)

from src.utils import (
    get_llm_client,
    Neo4jConnector
)

__all__ = [
    # Agents
    'BaseAgent',
    'StrategistAgent',
    'MethodologistAgent',
    'CodingAgentV2',
    
    # Core
    'CodingAgentState',
    'WorkflowState',
    'build_full_workflow',
    
    # Utils
    'get_llm_client',
    'Neo4jConnector',
]
