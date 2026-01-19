"""
变量映射器
连接因果图谱的抽象变量和实际数据字段
"""

import json
from typing import List, Dict, Any, Optional


class VariableMapper:
    """变量映射器：抽象变量 ↔ 数据字段"""
    
    # 默认映射表（可以从文件加载）
    DEFAULT_MAPPING = {
        "V01_tech_intensity": {
            "label": "技术投入强度",
            "data_fields": ["序号", "公开(公告)号"],
            "calculation": "COUNT(DISTINCT 公开(公告)号)",
            "calculation_type": "aggregation",
            "description": "专利数量",
            "python_code": "df['公开(公告)号'].nunique()"
        },
        "V02_firm_size": {
            "label": "企业规模",
            "data_fields": ["申请(专利权)人", "公开(公告)号"],
            "calculation": "COUNT(专利) GROUP BY 申请人",
            "calculation_type": "aggregation",
            "description": "申请人的专利总量",
            "python_code": "df.groupby('申请(专利权)人')['公开(公告)号'].count()"
        },
        "V03_rd_investment": {
            "label": "研发投资强度",
            "data_fields": ["申请(专利权)人", "序号"],
            "calculation": "COUNT(专利) / COUNT(DISTINCT 申请人)",
            "calculation_type": "ratio",
            "description": "人均专利产出（代理指标）",
            "python_code": "len(df) / df['申请(专利权)人'].nunique()",
            "note": "真实的研发投资数据需要外部数据源"
        },
        "V04_international_collab": {
            "label": "国际合作强度",
            "data_fields": ["发明人", "地址"],
            "calculation": "COUNT(专利 with 多国发明人) / COUNT(总专利)",
            "calculation_type": "ratio",
            "description": "涉及外国发明人的专利占比",
            "python_code": "# 需要解析发明人和地址字段",
            "note": "需要解析发明人国籍信息"
        },
        "V05_university_collab": {
            "label": "产学研合作",
            "data_fields": ["申请(专利权)人"],
            "calculation": "COUNT(专利 with 大学/研究所) / COUNT(总专利)",
            "calculation_type": "ratio",
            "description": "涉及大学/研究所的专利占比",
            "python_code": "df['申请(专利权)人'].str.contains('大学|研究所|学院').sum() / len(df)"
        },
        "V06_prior_experience": {
            "label": "先验经验",
            "data_fields": ["申请(专利权)人", "申请日", "公开(公告)号"],
            "calculation": "COUNT(历史专利) GROUP BY 申请人",
            "calculation_type": "time_series",
            "description": "申请人在该领域的历史专利数量",
            "python_code": "# 需要时间窗口分析"
        },
        "V07_policy_support": {
            "label": "政策支持",
            "data_fields": ["名称", "摘要"],
            "calculation": "COUNT(专利 with 政府资助关键词) / COUNT(总专利)",
            "calculation_type": "text_analysis",
            "description": "政府资助项目相关专利占比",
            "python_code": "# 需要文本分析识别政府资助关键词"
        },
        "V08_market_competition": {
            "label": "市场竞争强度",
            "data_fields": ["申请(专利权)人", "公开(公告)号"],
            "calculation": "HHI = SUM((firm_patents / total_patents)^2)",
            "calculation_type": "aggregation",
            "description": "赫芬达尔指数（HHI）",
            "python_code": "# 计算市场集中度"
        },
        "V09_tech_diversity": {
            "label": "技术跨界度",
            "data_fields": ["IPC分类号"],
            "calculation": "Shannon Entropy = -SUM(p_i * log(p_i))",
            "calculation_type": "entropy",
            "description": "IPC分类的多样性",
            "python_code": "from scipy.stats import entropy; entropy(ipc_counts)"
        },
        "V10_science_linkage": {
            "label": "科学关联度",
            "data_fields": ["引用文献"],
            "calculation": "COUNT(NPL引用) / COUNT(总引用)",
            "calculation_type": "ratio",
            "description": "非专利文献引用比例",
            "python_code": "# 需要解析引用文献，区分专利和非专利文献"
        },
        "V11_knowledge_recombination": {
            "label": "知识重组度",
            "data_fields": ["IPC分类号"],
            "calculation": "COUNT(新IPC组合) / COUNT(总IPC组合)",
            "calculation_type": "network_analysis",
            "description": "新IPC组合占比",
            "python_code": "# 需要构建IPC共现网络"
        },
        "V12_tech_cycle_time": {
            "label": "技术迭代速度",
            "data_fields": ["授权日", "引用文献"],
            "calculation": "MEDIAN(当前年份 - 被引专利年份)",
            "calculation_type": "time_series",
            "description": "引用专利的平均年龄（TCT）",
            "python_code": "# 需要解析引用专利的年份"
        },
        "V13_rd_efficiency": {
            "label": "研发效率",
            "data_fields": ["发明人", "公开(公告)号"],
            "calculation": "COUNT(专利) / COUNT(DISTINCT 发明人)",
            "calculation_type": "ratio",
            "description": "人均专利产出",
            "python_code": "len(df) / df['发明人'].str.split(';').explode().nunique()"
        },
        "V14_tech_breadth": {
            "label": "技术广度",
            "data_fields": ["IPC分类号"],
            "calculation": "COUNT(DISTINCT IPC大类)",
            "calculation_type": "aggregation",
            "description": "IPC大类数量",
            "python_code": "df['IPC分类号'].str[:4].nunique()"
        },
        "V15_tech_depth": {
            "label": "技术深度",
            "data_fields": ["IPC分类号"],
            "calculation": "MAX(IPC类别专利数) / COUNT(总专利)",
            "calculation_type": "ratio",
            "description": "主要IPC类别的专利集中度",
            "python_code": "df['IPC分类号'].value_counts().max() / len(df)"
        },
        "V16_tech_impact": {
            "label": "技术影响力",
            "data_fields": ["被引用专利"],
            "calculation": "COUNT(前向引用)",
            "calculation_type": "aggregation",
            "description": "被引用次数",
            "python_code": "df['被引用专利'].str.split(';').str.len().sum()",
            "note": "需要解析被引用专利字段"
        },
        "V17_tech_breakthrough": {
            "label": "技术突破性",
            "data_fields": ["引用文献", "被引用专利"],
            "calculation": "CD Index = (Nf - Nb) / (Nf + Nb + Nc)",
            "calculation_type": "network_analysis",
            "description": "颠覆性指数",
            "python_code": "# 需要构建引用网络计算CD指数"
        },
        "V18_tech_independence": {
            "label": "技术独立性",
            "data_fields": ["引用文献", "地址"],
            "calculation": "COUNT(国内引用) / COUNT(总引用)",
            "calculation_type": "ratio",
            "description": "引用本国专利的比例",
            "python_code": "# 需要解析引用专利的国家信息"
        },
        "V19_commercial_value": {
            "label": "商业价值",
            "data_fields": ["授权日", "法律状态"],
            "calculation": "AVG(专利维持年限)",
            "calculation_type": "time_series",
            "description": "专利维持年限",
            "python_code": "# 需要计算专利维持时间"
        },
        "V20_market_share": {
            "label": "市场份额",
            "data_fields": ["申请(专利权)人", "公开(公告)号"],
            "calculation": "firm_patents / total_field_patents",
            "calculation_type": "ratio",
            "description": "申请人专利占该领域比例",
            "python_code": "df.groupby('申请(专利权)人').size() / len(df)"
        },
        "V22_tech_maturity": {
            "label": "技术成熟度",
            "data_fields": ["授权日", "公开(公告)号"],
            "calculation": "(近5年专利数 - 前5年专利数) / 前5年专利数",
            "calculation_type": "time_series",
            "description": "专利增长率",
            "python_code": "# 需要时间窗口分析"
        },
        "V23_industry_type": {
            "label": "产业类型",
            "data_fields": ["IPC分类号"],
            "calculation": "基于IPC分类映射",
            "calculation_type": "classification",
            "description": "高科技/传统产业分类",
            "python_code": "# 需要IPC到产业的映射表"
        },
        "V24_firm_type": {
            "label": "组织类型",
            "data_fields": ["申请(专利权)人"],
            "calculation": "基于申请人名称分类",
            "calculation_type": "classification",
            "description": "企业/大学/研究所/个人",
            "python_code": "# 需要实体类型识别"
        },
        "V25_geographic_location": {
            "label": "地理位置",
            "data_fields": ["地址"],
            "calculation": "基于地址提取",
            "calculation_type": "text_analysis",
            "description": "申请人所在国家/地区",
            "python_code": "# 需要地址解析"
        }
    }
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        初始化变量映射器
        
        Args:
            mapping_file: 映射文件路径（可选，默认使用内置映射）
        """
        if mapping_file:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.mapping = json.load(f)
        else:
            self.mapping = self.DEFAULT_MAPPING
    
    def get_data_fields(self, variable_id: str) -> List[str]:
        """
        获取变量对应的数据字段
        
        Args:
            variable_id: 变量ID（如 "V03_rd_investment"）
            
        Returns:
            数据字段列表
        """
        if variable_id not in self.mapping:
            return []
        return self.mapping[variable_id]['data_fields']
    
    def get_calculation_method(self, variable_id: str) -> str:
        """
        获取变量的计算方法
        
        Args:
            variable_id: 变量ID
            
        Returns:
            计算方法描述
        """
        if variable_id not in self.mapping:
            return ""
        return self.mapping[variable_id]['calculation']
    
    def get_python_code(self, variable_id: str) -> str:
        """
        获取变量的Python计算代码
        
        Args:
            variable_id: 变量ID
            
        Returns:
            Python代码片段
        """
        if variable_id not in self.mapping:
            return ""
        return self.mapping[variable_id].get('python_code', '')
    
    def get_calculation_type(self, variable_id: str) -> str:
        """
        获取变量的计算类型
        
        Args:
            variable_id: 变量ID
            
        Returns:
            计算类型（aggregation, ratio, entropy, network_analysis等）
        """
        if variable_id not in self.mapping:
            return "unknown"
        return self.mapping[variable_id].get('calculation_type', 'unknown')
    
    def generate_task_config(self, variable_id: str) -> Dict[str, Any]:
        """
        生成任务配置（供 Strategist 使用）
        
        Args:
            variable_id: 变量ID
            
        Returns:
            任务配置字典
        """
        if variable_id not in self.mapping:
            return {}
        
        var_info = self.mapping[variable_id]
        
        return {
            'variable_id': variable_id,
            'variable_label': var_info['label'],
            'input_columns': var_info['data_fields'],
            'calculation': var_info['calculation'],
            'calculation_type': var_info.get('calculation_type', 'unknown'),
            'description': var_info['description'],
            'python_code': var_info.get('python_code', ''),
            'note': var_info.get('note', '')
        }
    
    def get_required_columns_for_hypothesis(self, source_var: str, target_var: str, 
                                           mediators: List[str] = None) -> List[str]:
        """
        获取验证某个假设所需的所有数据字段
        
        Args:
            source_var: 源变量ID
            target_var: 目标变量ID
            mediators: 中介变量ID列表（可选）
            
        Returns:
            所需数据字段列表（去重）
        """
        required_columns = set()
        
        # 源变量
        required_columns.update(self.get_data_fields(source_var))
        
        # 目标变量
        required_columns.update(self.get_data_fields(target_var))
        
        # 中介变量
        if mediators:
            for mediator in mediators:
                required_columns.update(self.get_data_fields(mediator))
        
        return list(required_columns)
    
    def check_data_availability(self, variable_id: str, available_columns: List[str]) -> Dict[str, Any]:
        """
        检查数据可用性
        
        Args:
            variable_id: 变量ID
            available_columns: 可用的数据列名列表
            
        Returns:
            可用性检查结果
        """
        required_columns = self.get_data_fields(variable_id)
        available_set = set(available_columns)
        required_set = set(required_columns)
        
        missing_columns = required_set - available_set
        
        return {
            'variable_id': variable_id,
            'variable_label': self.mapping[variable_id]['label'],
            'is_available': len(missing_columns) == 0,
            'required_columns': required_columns,
            'missing_columns': list(missing_columns),
            'coverage': (len(required_set & available_set) / len(required_set)) if required_set else 0
        }
    
    def suggest_alternative_variables(self, variable_id: str, available_columns: List[str]) -> List[str]:
        """
        推荐替代变量（当某个变量的数据不可用时）
        
        Args:
            variable_id: 原始变量ID
            available_columns: 可用的数据列名列表
            
        Returns:
            替代变量ID列表
        """
        # 简单版本：找到数据可用的同类别变量
        # TODO: 可以基于理论相似性进行更智能的推荐
        
        alternatives = []
        available_set = set(available_columns)
        
        for var_id, var_info in self.mapping.items():
            if var_id == variable_id:
                continue
            
            required_set = set(var_info['data_fields'])
            if required_set.issubset(available_set):
                alternatives.append(var_id)
        
        return alternatives
    
    def export_mapping(self, output_file: str):
        """
        导出映射表到文件
        
        Args:
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)
    
    def get_all_variables(self) -> List[str]:
        """获取所有变量ID"""
        return list(self.mapping.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取映射统计信息
        
        Returns:
            统计信息字典
        """
        calc_types = {}
        for var_info in self.mapping.values():
            calc_type = var_info.get('calculation_type', 'unknown')
            calc_types[calc_type] = calc_types.get(calc_type, 0) + 1
        
        return {
            'total_variables': len(self.mapping),
            'calculation_types': calc_types,
            'variables_with_code': sum(1 for v in self.mapping.values() if v.get('python_code'))
        }


# 使用示例
if __name__ == "__main__":
    # 初始化映射器
    mapper = VariableMapper()
    
    # 统计信息
    print("=== 变量映射统计 ===")
    stats = mapper.get_statistics()
    print(f"变量总数: {stats['total_variables']}")
    print(f"计算类型分布: {stats['calculation_types']}")
    print()
    
    # 查询变量映射
    print("=== 查询变量映射 ===")
    var_id = "V03_rd_investment"
    config = mapper.generate_task_config(var_id)
    print(f"变量: {config['variable_label']}")
    print(f"数据字段: {config['input_columns']}")
    print(f"计算方法: {config['calculation']}")
    print(f"Python代码: {config['python_code']}")
    print()
    
    # 检查数据可用性
    print("=== 检查数据可用性 ===")
    available_columns = ["序号", "公开(公告)号", "申请(专利权)人", "授权日", "IPC分类号"]
    availability = mapper.check_data_availability("V09_tech_diversity", available_columns)
    print(f"变量: {availability['variable_label']}")
    print(f"是否可用: {availability['is_available']}")
    print(f"缺失字段: {availability['missing_columns']}")
    print()
    
    # 获取假设所需字段
    print("=== 获取假设所需字段 ===")
    required = mapper.get_required_columns_for_hypothesis(
        "V03_rd_investment", 
        "V16_tech_impact",
        mediators=["V09_tech_diversity"]
    )
    print(f"所需字段: {required}")
