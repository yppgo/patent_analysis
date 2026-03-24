from __future__ import annotations

from dataclasses import dataclass
from scripts.jos.common import ensure_dirs


QUESTION_TEMPLATES = (
    "分析{domain}领域的技术影响力驱动因素",
    "识别{domain}领域的技术融合趋势",
    "评估不同国家/地区在{domain}领域的竞争态势",
    "判断{domain}领域关键技术所处的生命周期阶段",
    "评估{domain}领域专利组合的风险与薄弱环节",
)

CROSS_DOMAIN_BUGZILLA_QUESTION_TEMPLATES = (
    "分析{domain}中的缺陷严重性或问题影响因素",
    "识别{domain}中的缺陷类型与模块演化趋势",
    "评估不同项目或组件在{domain}中的质量差异",
)


@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    label: str
    domain_name: str
    data_file: str
    sheet_name: str
    description: str
    question_templates: tuple[str, ...] = QUESTION_TEMPLATES
    source_dataset: str | None = None
    source_sheet_name: str | None = None
    filter_column: str | None = None
    filter_value: str | None = None

    @property
    def questions(self) -> list[str]:
        return [template.format(domain=self.domain_name) for template in self.question_templates]

    def to_dict(self) -> dict[str, str | None]:
        return {
            "dataset_id": self.dataset_id,
            "label": self.label,
            "domain_name": self.domain_name,
            "data_file": self.data_file,
            "sheet_name": self.sheet_name,
            "description": self.description,
            "source_dataset": self.source_dataset,
            "source_sheet_name": self.source_sheet_name,
            "filter_column": self.filter_column,
            "filter_value": self.filter_value,
            "question_count": len(self.question_templates),
            "question_templates": list(self.question_templates),
        }


@dataclass(frozen=True)
class ModeConfig:
    mode: str
    label: str
    family: str
    planner_kind: str
    rounds: int
    disable_data_insights: bool = False
    disable_causal_hypotheses: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "mode": self.mode,
            "label": self.label,
            "family": self.family,
            "planner_kind": self.planner_kind,
            "rounds": self.rounds,
            "disable_data_insights": self.disable_data_insights,
            "disable_causal_hypotheses": self.disable_causal_hypotheses,
            "description": self.description,
        }


ensure_dirs()

_transfer_dataset_path = "outputs/jos_artifacts/datasets/jos_transfer_iot_auto.xlsx"
_cross_domain_bugzilla_path = "outputs/jos_artifacts/datasets/cross_domain_bugzilla.xlsx"

DATASET_CONFIGS: dict[str, DatasetConfig] = {
    "main_data_security": DatasetConfig(
        dataset_id="main_data_security",
        label="主数据集：数据安全专利",
        domain_name="数据安全",
        data_file="data/new_data.xlsx",
        sheet_name="sheet1",
        description="当前 90 组主实验所使用的数据安全专利数据集。",
    ),
    "transfer_iot_auto": DatasetConfig(
        dataset_id="transfer_iot_auto",
        label="子领域稳定性数据集：物联网与智能汽车安全专利",
        domain_name="物联网与智能汽车安全",
        data_file=_transfer_dataset_path,
        sheet_name="transfer_iot_auto",
        description="从 clean_patents1_with_topics_filled.xlsx 中筛选 Topic_Label_filled=物联网(IoT)与智能汽车 的相邻技术子领域稳定性验证数据集。",
        source_dataset="data/clean_patents1_with_topics_filled.xlsx",
        source_sheet_name="hit_patent",
        filter_column="Topic_Label_filled",
        filter_value="物联网(IoT)与智能汽车",
    ),
    "cross_domain_bugzilla": DatasetConfig(
        dataset_id="cross_domain_bugzilla",
        label="跨领域数据集：Bugzilla 缺陷数据",
        domain_name="软件缺陷分析",
        data_file=_cross_domain_bugzilla_path,
        sheet_name="cross_domain_bugzilla",
        description="基于 Eclipse 或 Mozilla Bugzilla 导出的软件工程结构化缺陷数据集，用于真跨领域小规模验证。",
        question_templates=CROSS_DOMAIN_BUGZILLA_QUESTION_TEMPLATES,
    ),
}


MODE_CONFIGS: dict[str, ModeConfig] = {
    "D_baseline0": ModeConfig(
        mode="D_baseline0",
        label="D_baseline0",
        family="main",
        planner_kind="strategist",
        rounds=1,
        disable_data_insights=True,
        disable_causal_hypotheses=True,
        description="纯 LLM 规划基线，不使用数据洞察和知识图谱。",
    ),
    "A_template": ModeConfig(
        mode="A_template",
        label="A_template",
        family="main",
        planner_kind="strategist",
        rounds=1,
        disable_data_insights=True,
        description="知识约束单轮方案。",
    ),
    "B_data_aware": ModeConfig(
        mode="B_data_aware",
        label="B_data_aware",
        family="main",
        planner_kind="strategist",
        rounds=1,
        description="数据感知单轮方案。",
    ),
    "C_iterative": ModeConfig(
        mode="C_iterative",
        label="C_iterative",
        family="main",
        planner_kind="strategist",
        rounds=2,
        description="完整系统，两轮迭代。",
    ),
    "E_ablate_data": ModeConfig(
        mode="E_ablate_data",
        label="E_ablate_data",
        family="ablation",
        planner_kind="strategist",
        rounds=2,
        disable_data_insights=True,
        description="去除数据感知的两轮消融。",
    ),
    "F_ablate_kg": ModeConfig(
        mode="F_ablate_kg",
        label="F_ablate_kg",
        family="ablation",
        planner_kind="strategist",
        rounds=2,
        disable_causal_hypotheses=True,
        description="去除知识图谱约束的两轮消融。",
    ),
    "G_react_single_agent": ModeConfig(
        mode="G_react_single_agent",
        label="G_react_single_agent",
        family="external",
        planner_kind="single_agent",
        rounds=1,
        description="外部基线 1：单智能体一次性规划，不使用知识图谱与数据洞察模块。",
    ),
    "H_execution_feedback": ModeConfig(
        mode="H_execution_feedback",
        label="H_execution_feedback",
        family="external",
        planner_kind="single_agent",
        rounds=2,
        description="外部基线 2：单智能体 + 执行反馈两轮迭代，不使用知识图谱与数据洞察模块。",
    ),
}


MODE_BUNDLES: dict[str, list[str]] = {
    "thesis_six": [
        "D_baseline0",
        "A_template",
        "B_data_aware",
        "C_iterative",
        "E_ablate_data",
        "F_ablate_kg",
    ],
    "external_baselines_main": [
        "D_baseline0",
        "A_template",
        "B_data_aware",
        "C_iterative",
        "G_react_single_agent",
        "H_execution_feedback",
    ],
    "external_mechanism_only": [
        "G_react_single_agent",
        "H_execution_feedback",
    ],
    "subdomain_stability_full": [
        "D_baseline0",
        "B_data_aware",
        "C_iterative",
        "H_execution_feedback",
    ],
    "cross_domain_minimal": [
        "D_baseline0",
        "C_iterative",
    ],
}


REPEAT_HINTS: dict[str, int] = {
    "thesis_six": 5,
    "external_baselines_main": 5,
    "external_mechanism_only": 5,
    "subdomain_stability_full": 3,
    "cross_domain_minimal": 3,
}


def get_dataset_config(dataset_id: str) -> DatasetConfig:
    try:
        return DATASET_CONFIGS[dataset_id]
    except KeyError as exc:
        raise ValueError(f"未知数据集配置: {dataset_id}") from exc


def get_mode_config(mode: str) -> ModeConfig:
    try:
        return MODE_CONFIGS[mode]
    except KeyError as exc:
        raise ValueError(f"未知模式配置: {mode}") from exc


def get_questions(dataset_id: str) -> list[str]:
    return get_dataset_config(dataset_id).questions


def get_question_indexes(dataset_id: str) -> list[int]:
    return list(range(1, len(get_questions(dataset_id)) + 1))


def get_mode_bundle(bundle_name: str) -> list[str]:
    try:
        return MODE_BUNDLES[bundle_name]
    except KeyError as exc:
        raise ValueError(f"未知模式组合: {bundle_name}") from exc


def resolve_modes(explicit_modes: list[str] | None = None, mode_bundle: str | None = None) -> list[str]:
    if explicit_modes:
        return explicit_modes
    if mode_bundle:
        return get_mode_bundle(mode_bundle)
    return get_mode_bundle("thesis_six")


def list_config_snapshot() -> dict[str, object]:
    return {
        "datasets": {key: value.to_dict() for key, value in DATASET_CONFIGS.items()},
        "modes": {key: value.to_dict() for key, value in MODE_CONFIGS.items()},
        "bundles": MODE_BUNDLES,
        "repeat_hints": REPEAT_HINTS,
    }
