#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为缺失的5个变量添加默认测量方法
"""

import json
from datetime import datetime

# 5个变量的默认测量方法
DEFAULT_METHODS = {
    "V03_rd_investment": {
        "variable_id": "V03_rd_investment",
        "variable_name": "研发投资强度",
        "total_methods": 2,
        "default_method": "专利申请数作为代理变量",
        "method_selection_logic": "优先使用专利申请数（数据可得），如有财务数据则使用R&D强度",
        "measurement_methods": [
            {
                "method_name": "专利申请数作为代理变量",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "default",
                "recommendation_reason": "默认方案：专利申请数可作为研发投入的代理指标",
                "formula": "RD_Proxy = COUNT(patents)",
                "formula_explanation": "统计特定时期内的专利申请数量",
                "data_source": "专利申请数据",
                "data_fields_used": [
                    "申请日 (Application Date)",
                    "申请人 / 专利权人 (Applicant / Assignee)"
                ],
                "calculation_steps": [
                    "1. 按申请人分组统计专利数量",
                    "2. 按时间窗口（如年度）统计",
                    "3. 专利数量越多表示研发投入越大"
                ],
                "interpretation": "专利申请数与研发投入正相关，可作为代理变量",
                "notes": "⚠️ 默认方案：未从文献提取，基于领域常识"
            },
            {
                "method_name": "R&D强度（需要外部数据）",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "alternative",
                "recommendation_reason": "标准方案：需要企业财务数据",
                "formula": "RD_Intensity = R&D_Expenditure / Revenue",
                "formula_explanation": "研发支出占营收的比例",
                "data_source": "企业财务报表",
                "data_fields_used": [],
                "calculation_steps": [
                    "1. 获取企业年度研发支出",
                    "2. 获取企业年度营收",
                    "3. 计算比例"
                ],
                "interpretation": "比例越高表示研发投入强度越大",
                "notes": "⚠️ 需要外部财务数据，专利数据库通常不包含"
            }
        ],
        "method_comparison": {
            "correlation": "专利数与R&D支出通常呈正相关（r>0.6）",
            "pros_cons": "专利数易获取但有滞后性；R&D强度更准确但数据难获取"
        }
    },
    
    "V05_university_collab": {
        "variable_id": "V05_university_collab",
        "variable_name": "产学研合作",
        "total_methods": 2,
        "default_method": "产学合作专利占比",
        "method_selection_logic": "优先使用发明人地址匹配方法",
        "measurement_methods": [
            {
                "method_name": "产学合作专利占比",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "default",
                "recommendation_reason": "默认方案：通过发明人地址识别产学合作",
                "formula": "Univ_Collab = COUNT(patents with university) / COUNT(total patents)",
                "formula_explanation": "包含大学/研究所发明人的专利占比",
                "data_source": "发明人地址信息",
                "data_fields_used": [
                    "发明人 (Inventor)",
                    "申请人 / 专利权人 (Applicant / Assignee)"
                ],
                "calculation_steps": [
                    "1. 提取发明人地址或申请人名称",
                    "2. 匹配大学/研究所关键词（如'University', '大学', 'Institute'）",
                    "3. 统计包含产学合作的专利数量",
                    "4. 计算占比"
                ],
                "typical_range": [0, 1],
                "interpretation": "比例越高表示产学研合作越频繁",
                "notes": "⚠️ 默认方案：未从文献提取，基于领域常识"
            },
            {
                "method_name": "产学合作网络密度",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "alternative",
                "recommendation_reason": "高级方案：构建合作网络分析",
                "formula": "Network_Density = 2*E / (N*(N-1))",
                "formula_explanation": "E为企业-大学合作边数，N为节点数",
                "data_source": "合作网络数据",
                "data_fields_used": [
                    "发明人 (Inventor)",
                    "申请人 / 专利权人 (Applicant / Assignee)"
                ],
                "calculation_steps": [
                    "1. 构建企业-大学合作网络",
                    "2. 计算网络密度",
                    "3. 密度越高表示合作越紧密"
                ],
                "interpretation": "网络密度反映产学研合作的紧密程度",
                "notes": "⚠️ 需要网络分析，计算复杂度较高"
            }
        ],
        "method_comparison": {
            "correlation": "两种方法高度相关",
            "pros_cons": "占比方法简单直观；网络方法更全面但复杂"
        }
    },
    
    "V17_tech_breakthrough": {
        "variable_id": "V17_tech_breakthrough",
        "variable_name": "技术突破性",
        "total_methods": 2,
        "default_method": "颠覆性指数（CD Index）",
        "method_selection_logic": "优先使用CD Index，需要引用数据",
        "measurement_methods": [
            {
                "method_name": "颠覆性指数（CD Index）",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "default",
                "recommendation_reason": "默认方案：Funk & Owen-Smith (2017)提出的标准指标",
                "formula": "CD = (Nf - Nb) / (Nf + Nb + Nc)",
                "formula_explanation": "Nf=只引用焦点专利的后续专利数, Nb=只引用焦点专利引用的专利数, Nc=同时引用两者的专利数",
                "data_source": "专利引用网络",
                "data_fields_used": [
                    "前向引文 / 被引 (Forward Citations)",
                    "后向引文 / 专利引用 (Backward Citations)"
                ],
                "calculation_steps": [
                    "1. 获取焦点专利的前向引用（被引专利）",
                    "2. 获取焦点专利的后向引用（引用的专利）",
                    "3. 分析被引专利的引用模式",
                    "4. 计算Nf, Nb, Nc",
                    "5. 应用CD公式"
                ],
                "typical_range": [-1, 1],
                "interpretation": "CD>0表示颠覆性创新，CD<0表示渐进性创新",
                "notes": "⚠️ 默认方案：基于Funk & Owen-Smith (2017)的标准方法"
            },
            {
                "method_name": "新IPC组合占比",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "alternative",
                "recommendation_reason": "简化方案：基于技术分类的新颖性",
                "formula": "Breakthrough = COUNT(new IPC combinations) / COUNT(total IPC pairs)",
                "formula_explanation": "专利中首次出现的IPC组合占比",
                "data_source": "IPC分类数据",
                "data_fields_used": [
                    "IPC (国际专利分类号)"
                ],
                "calculation_steps": [
                    "1. 提取专利的IPC分类",
                    "2. 生成IPC两两组合",
                    "3. 检查该组合是否在历史数据中首次出现",
                    "4. 计算新组合占比"
                ],
                "interpretation": "新组合占比越高表示技术突破性越强",
                "notes": "⚠️ 简化方案，可能低估突破性"
            }
        ],
        "method_comparison": {
            "correlation": "两种方法中度相关（r≈0.4-0.6）",
            "pros_cons": "CD Index更准确但计算复杂；IPC方法简单但粗糙"
        }
    },
    
    "V18_tech_independence": {
        "variable_id": "V18_tech_independence",
        "variable_name": "技术独立性",
        "total_methods": 2,
        "default_method": "本国引用占比",
        "method_selection_logic": "优先使用本国引用占比",
        "measurement_methods": [
            {
                "method_name": "本国引用占比",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "default",
                "recommendation_reason": "默认方案：引用本国专利的比例反映技术独立性",
                "formula": "Independence = COUNT(domestic citations) / COUNT(total citations)",
                "formula_explanation": "引用本国专利占所有引用的比例",
                "data_source": "专利引用数据",
                "data_fields_used": [
                    "后向引文 / 专利引用 (Backward Citations)",
                    "申请国家 / 专利局 (Assignee Country / Office)"
                ],
                "calculation_steps": [
                    "1. 获取专利的后向引用列表",
                    "2. 识别每个被引专利的国家",
                    "3. 统计本国专利数量",
                    "4. 计算占比"
                ],
                "typical_range": [0, 1],
                "interpretation": "比例越高表示技术越独立，对外国技术依赖越少",
                "notes": "⚠️ 默认方案：未从文献提取，基于领域常识"
            },
            {
                "method_name": "自引用率",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "alternative",
                "recommendation_reason": "替代方案：引用自己专利的比例",
                "formula": "Self_Citation = COUNT(self citations) / COUNT(total citations)",
                "formula_explanation": "引用同一申请人专利的比例",
                "data_source": "专利引用数据",
                "data_fields_used": [
                    "后向引文 / 专利引用 (Backward Citations)",
                    "申请人 / 专利权人 (Applicant / Assignee)"
                ],
                "calculation_steps": [
                    "1. 获取专利的后向引用",
                    "2. 匹配申请人名称",
                    "3. 统计自引用数量",
                    "4. 计算占比"
                ],
                "interpretation": "自引用率高表示技术积累深厚，独立性强",
                "notes": "⚠️ 自引用率也可能反映技术封闭性"
            }
        ],
        "method_comparison": {
            "correlation": "两种方法弱相关",
            "pros_cons": "本国引用反映国家层面独立性；自引用反映企业层面独立性"
        }
    },
    
    "V26_catching_up": {
        "variable_id": "V26_catching_up",
        "variable_name": "技术追赶能力",
        "total_methods": 2,
        "default_method": "专利增长率对比",
        "method_selection_logic": "优先使用增长率对比方法",
        "measurement_methods": [
            {
                "method_name": "专利增长率对比",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "default",
                "recommendation_reason": "默认方案：后发者增长率高于领先者表示追赶",
                "formula": "Catching_Up = Growth_Rate_Follower - Growth_Rate_Leader",
                "formula_explanation": "后发者专利增长率减去领先者增长率",
                "data_source": "专利申请数据",
                "data_fields_used": [
                    "申请日 (Application Date)",
                    "申请人 / 专利权人 (Applicant / Assignee)",
                    "申请国家 / 专利局 (Assignee Country / Office)"
                ],
                "calculation_steps": [
                    "1. 识别领先者和后发者（基于专利数量或时间）",
                    "2. 计算各自的专利年增长率",
                    "3. 计算增长率差值",
                    "4. 正值表示追赶，负值表示差距扩大"
                ],
                "interpretation": "值越大表示追赶速度越快",
                "notes": "⚠️ 默认方案：未从文献提取，基于追赶理论"
            },
            {
                "method_name": "技术差距缩小速度",
                "usage_frequency": 0,
                "usage_papers": [],
                "recommendation_level": "alternative",
                "recommendation_reason": "高级方案：直接测量技术差距变化",
                "formula": "Gap_Reduction = (Gap_t0 - Gap_t1) / Gap_t0",
                "formula_explanation": "技术差距缩小的比例",
                "data_source": "专利质量指标",
                "data_fields_used": [
                    "前向引文 / 被引 (Forward Citations)",
                    "申请人 / 专利权人 (Applicant / Assignee)"
                ],
                "calculation_steps": [
                    "1. 计算初始时期的技术差距（如引用数差异）",
                    "2. 计算后期的技术差距",
                    "3. 计算差距缩小比例"
                ],
                "interpretation": "比例越大表示追赶越成功",
                "notes": "⚠️ 需要定义技术差距的度量标准"
            }
        ],
        "method_comparison": {
            "correlation": "两种方法高度相关",
            "pros_cons": "增长率方法简单；差距方法更直接但需要定义差距"
        }
    }
}


def add_default_methods():
    """添加默认测量方法到方法知识库"""
    
    print("=" * 80)
    print("添加默认测量方法")
    print("=" * 80)
    
    # 加载方法知识库
    kb_file = "sandbox/static/data/method_knowledge_base.json"
    with open(kb_file, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    print(f"\n加载方法知识库: {kb_file}")
    print(f"当前变量数: {kb['meta']['total_variables_with_methods']}")
    
    # 添加默认方法
    added_count = 0
    for var_id, methods in DEFAULT_METHODS.items():
        if var_id not in kb['variable_measurement_methods']:
            kb['variable_measurement_methods'][var_id] = methods
            added_count += 1
            print(f"  ✓ 添加 {var_id}: {methods['variable_name']}")
        else:
            print(f"  ⚠ 跳过 {var_id}: 已存在")
    
    # 更新元数据
    kb['meta']['total_variables_with_methods'] = len(kb['variable_measurement_methods'])
    kb['meta']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    if 'default_methods_added' not in kb['meta']:
        kb['meta']['default_methods_added'] = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'variables': list(DEFAULT_METHODS.keys()),
            'note': '这些方法未从文献提取，基于领域知识补充'
        }
    
    # 保存
    with open(kb_file, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 已添加 {added_count} 个变量的默认方法")
    print(f"✓ 更新后变量总数: {kb['meta']['total_variables_with_methods']}")
    print(f"✓ 已保存到: {kb_file}")
    
    print("\n" + "=" * 80)
    print("添加完成！")
    print("=" * 80)
    
    return added_count


if __name__ == "__main__":
    count = add_default_methods()
    print(f"\n总结: 成功添加 {count} 个变量的默认测量方法")
