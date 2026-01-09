"""
测试 Strategist V4.1 的改进功能
重点测试：列名注入、output_artifacts 生成
"""

import json
from unittest.mock import Mock, MagicMock
from src.agents.strategist import StrategistAgent


def test_column_injection():
    """测试真实列名注入功能"""
    
    # Mock LLM 返回
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = json.dumps({
        "research_objective": "识别技术空白",
        "expected_outcomes": ["技术空白列表"],
        "analysis_logic_chains": [
            {
                "step_id": 1,
                "objective": "主题分类",
                "method": "LDA",
                "implementation_config": {
                    "algorithm": "LDA",
                    "input_columns": ["摘要(译)(简体中文)"],  # 使用真实列名
                    "output_columns": ["topic_label"],
                    "output_artifacts": ["lda_model"],
                    "parameters": {"n_topics": 5}
                },
                "depends_on": []
            }
        ]
    })
    mock_llm.invoke.return_value = mock_response
    
    # 初始化 Strategist
    strategist = StrategistAgent(mock_llm, neo4j_connector=None)
    
    # 模拟真实数据的列名（中文）
    real_columns = ["标题(译)(简体中文)", "摘要(译)(简体中文)", "申请人", "申请日"]
    
    # 调用 process（注入列名）
    result = strategist.process({
        'user_goal': '分析数据安全领域的技术空白',
        'available_columns': real_columns
    })
    
    # 验证：Prompt 中包含真实列名
    call_args = mock_llm.invoke.call_args[0][0]
    assert "摘要(译)(简体中文)" in call_args, "Prompt 应包含真实列名"
    assert "patent_abstracts" not in call_args, "Prompt 不应包含示例列名"
    
    # 验证：生成的蓝图使用真实列名
    blueprint = result['blueprint']
    step1_config = blueprint['analysis_logic_chains'][0]['implementation_config']
    assert "摘要(译)(简体中文)" in step1_config['input_columns'], "蓝图应使用真实列名"
    
    print("✅ 列名注入测试通过")


def test_output_artifacts():
    """测试 output_artifacts 字段生成"""
    
    # Mock LLM 返回（包含 output_artifacts）
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = json.dumps({
        "research_objective": "技术空白识别",
        "expected_outcomes": ["空白列表"],
        "analysis_logic_chains": [
            {
                "step_id": 1,
                "objective": "主题建模",
                "method": "LDA",
                "implementation_config": {
                    "algorithm": "LDA",
                    "input_columns": ["abstract"],
                    "output_columns": ["topic_label", "topic_probs"],
                    "output_artifacts": ["lda_model", "dictionary"],  # 关键字段
                    "parameters": {"n_topics": 5}
                },
                "depends_on": []
            },
            {
                "step_id": 2,
                "objective": "异常检测",
                "method": "ABOD",
                "implementation_config": {
                    "algorithm": "ABOD",
                    "input_columns": ["topic_probs"],
                    "output_columns": ["is_outlier"],
                    "output_artifacts": ["abod_model"],  # 关键字段
                    "parameters": {"contamination": 0.1}
                },
                "depends_on": [1]
            }
        ]
    })
    mock_llm.invoke.return_value = mock_response
    
    # 初始化 Strategist
    strategist = StrategistAgent(mock_llm, neo4j_connector=None)
    
    # 调用 process
    result = strategist.process({
        'user_goal': '识别技术空白',
        'available_columns': ['abstract', 'title']
    })
    
    # 验证：每个步骤都有 output_artifacts
    blueprint = result['blueprint']
    for step in blueprint['analysis_logic_chains']:
        config = step['implementation_config']
        assert 'output_artifacts' in config, f"步骤 {step['step_id']} 缺少 output_artifacts"
        print(f"步骤 {step['step_id']} 的 output_artifacts: {config['output_artifacts']}")
    
    # 验证：步骤 1 产生模型，步骤 2 使用步骤 1 的输出
    step1 = blueprint['analysis_logic_chains'][0]
    step2 = blueprint['analysis_logic_chains'][1]
    
    assert "lda_model" in step1['implementation_config']['output_artifacts']
    assert "topic_probs" in step1['implementation_config']['output_columns']
    assert "topic_probs" in step2['implementation_config']['input_columns']
    assert 1 in step2['depends_on']
    
    print("✅ output_artifacts 测试通过")


def test_quality_check_v4_1():
    """测试 V4.1 的质量检查（验证 output_artifacts）"""
    
    strategist = StrategistAgent(Mock(), neo4j_connector=None)
    
    # 测试 1: 缺少 output_artifacts（应失败）
    bad_blueprint = {
        "research_objective": "测试",
        "analysis_logic_chains": [
            {
                "step_id": 1,
                "objective": "测试",
                "method": "LDA",
                "implementation_config": {
                    "algorithm": "LDA",
                    "input_columns": ["abstract"],
                    "output_columns": ["topic"]
                    # 缺少 output_artifacts
                }
            },
            {
                "step_id": 2,
                "objective": "测试2",
                "method": "ABOD",
                "implementation_config": {
                    "algorithm": "ABOD",
                    "input_columns": ["topic"],
                    "output_columns": ["outlier"]
                    # 缺少 output_artifacts
                }
            }
        ]
    }
    
    assert not strategist._check_quality(bad_blueprint), "应检测到缺少 output_artifacts"
    print("✅ 质量检查正确拒绝了缺少 output_artifacts 的蓝图")
    
    # 测试 2: 包含 output_artifacts（应通过）
    good_blueprint = {
        "research_objective": "测试",
        "analysis_logic_chains": [
            {
                "step_id": 1,
                "objective": "测试",
                "method": "LDA",
                "implementation_config": {
                    "algorithm": "LDA",
                    "input_columns": ["abstract"],
                    "output_columns": ["topic"],
                    "output_artifacts": ["lda_model"]  # 有模型
                }
            },
            {
                "step_id": 2,
                "objective": "测试2",
                "method": "ABOD",
                "implementation_config": {
                    "algorithm": "ABOD",
                    "input_columns": ["topic"],
                    "output_columns": ["outlier"],
                    "output_artifacts": []  # 无模型也可以（空列表）
                }
            }
        ]
    }
    
    assert strategist._check_quality(good_blueprint), "应通过质量检查"
    print("✅ 质量检查正确接受了包含 output_artifacts 的蓝图")


def test_prompt_contains_key_instructions():
    """测试 Prompt 是否包含关键指令"""
    
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = json.dumps({
        "research_objective": "测试",
        "analysis_logic_chains": [
            {
                "step_id": 1,
                "objective": "测试",
                "method": "LDA",
                "implementation_config": {
                    "algorithm": "LDA",
                    "input_columns": ["abstract"],
                    "output_columns": ["topic"],
                    "output_artifacts": []
                }
            },
            {
                "step_id": 2,
                "objective": "测试2",
                "method": "ABOD",
                "implementation_config": {
                    "algorithm": "ABOD",
                    "input_columns": ["topic"],
                    "output_columns": ["outlier"],
                    "output_artifacts": []
                }
            }
        ]
    })
    mock_llm.invoke.return_value = mock_response
    
    strategist = StrategistAgent(mock_llm, neo4j_connector=None)
    
    # 调用 process
    strategist.process({
        'user_goal': '测试',
        'available_columns': ['abstract', 'title']
    })
    
    # 获取 Prompt
    prompt = mock_llm.invoke.call_args[0][0]
    
    # 验证关键指令
    key_phrases = [
        "当前数据可用列名",
        "严禁幻觉列名",
        "output_artifacts",
        "output_columns",
        "数据流思维"
    ]
    
    for phrase in key_phrases:
        assert phrase in prompt, f"Prompt 应包含关键指令: {phrase}"
        print(f"✅ Prompt 包含: {phrase}")
    
    print("✅ Prompt 包含所有关键指令")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 Strategist V4.1 改进功能")
    print("=" * 60)
    
    test_column_injection()
    print()
    
    test_output_artifacts()
    print()
    
    test_quality_check_v4_1()
    print()
    
    test_prompt_contains_key_instructions()
    print()
    
    print("=" * 60)
    print("所有测试通过！✅")
    print("=" * 60)
