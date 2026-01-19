"""
方法图谱查询器
用于从方法知识库中检索变量测量方法和统计分析方法
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class MethodGraphQuery:
    """方法图谱查询器"""
    
    def __init__(self, knowledge_base_path: str = "sandbox/static/data/method_knowledge_base.json"):
        """
        初始化方法图谱查询器
        
        Args:
            knowledge_base_path: 方法知识库文件路径
        """
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_base = self._load_knowledge_base()
        self.variable_methods = self.knowledge_base.get('variable_measurement_methods', {})
        self.analysis_methods = self.knowledge_base.get('statistical_analysis_methods', [])
    
    def _load_knowledge_base(self) -> Dict:
        """加载方法知识库"""
        with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_variable_methods(self, var_id: str) -> Optional[Dict]:
        """
        获取变量的测量方法
        
        Args:
            var_id: 变量ID（如 "V16_tech_impact"）
            
        Returns:
            变量测量方法字典，如果不存在则返回 None
        """
        return self.variable_methods.get(var_id)
    
    def get_recommended_method(self, var_id: str) -> Optional[Dict]:
        """
        获取变量的推荐测量方法（使用频率最高的）
        
        Args:
            var_id: 变量ID
            
        Returns:
            推荐的测量方法，如果不存在则返回 None
        """
        var_methods = self.get_variable_methods(var_id)
        if not var_methods:
            return None
        
        methods = var_methods.get('measurement_methods', [])
        if not methods:
            return None
        
        # 按使用频率排序，返回第一个
        sorted_methods = sorted(methods, key=lambda m: m.get('usage_frequency', 0), reverse=True)
        return sorted_methods[0]
    
    def search_analysis_methods(self, method_type: str = None, keyword: str = None) -> List[Dict]:
        """
        搜索统计分析方法
        
        Args:
            method_type: 方法类型（如 "regression", "mediation", "moderation"）
            keyword: 搜索关键词
            
        Returns:
            匹配的分析方法列表
        """
        results = []
        
        for method in self.analysis_methods:
            # 按类型过滤
            if method_type and method.get('method_type') != method_type:
                continue
            
            # 按关键词过滤
            if keyword:
                keyword_lower = keyword.lower()
                method_name = method.get('method_name', '').lower()
                description = method.get('description', '').lower()
                
                if keyword_lower not in method_name and keyword_lower not in description:
                    continue
            
            results.append(method)
        
        return results
    
    def get_methods_for_hypothesis(self, hypothesis: Dict) -> Dict[str, Any]:
        """
        为假设获取相关的测量方法和分析方法
        
        Args:
            hypothesis: 假设字典，包含 variables 字段
            
        Returns:
            {
                "variable_methods": {...},  # 变量测量方法
                "analysis_methods": [...]   # 推荐的分析方法
            }
        """
        variables = hypothesis.get('variables', {})
        h_type = hypothesis.get('type', '')
        
        # 收集所有变量的测量方法
        variable_methods = {}
        all_vars = (variables.get('independent', []) + 
                   variables.get('dependent', []) + 
                   variables.get('mediator', []) + 
                   variables.get('moderator', []))
        
        for var_id in all_vars:
            method = self.get_recommended_method(var_id)
            if method:
                variable_methods[var_id] = method
        
        # 根据假设类型推荐分析方法
        analysis_methods = []
        
        if h_type == 'mediation':
            # 中介分析方法
            analysis_methods = self.search_analysis_methods(method_type='mediation')
        elif h_type == 'moderation':
            # 调节分析方法
            analysis_methods = self.search_analysis_methods(method_type='moderation')
        elif h_type in ['theory_transfer', 'path_exploration', 'counterfactual', 'interaction']:
            # 回归分析方法
            analysis_methods = self.search_analysis_methods(method_type='regression')
        
        return {
            'variable_methods': variable_methods,
            'analysis_methods': analysis_methods[:3]  # 返回前3个
        }
    
    def format_methods_for_prompt(self, hypothesis: Dict) -> str:
        """
        格式化方法信息用于 Prompt
        
        Args:
            hypothesis: 假设字典
            
        Returns:
            格式化的方法文本
        """
        methods_info = self.get_methods_for_hypothesis(hypothesis)
        
        lines = []
        lines.append("【方法图谱 - 推荐的测量和分析方法】")
        lines.append("")
        
        # 变量测量方法
        variable_methods = methods_info.get('variable_methods', {})
        if variable_methods:
            lines.append("变量测量方法:")
            for var_id, method in variable_methods.items():
                lines.append(f"  {var_id}:")
                lines.append(f"    方法: {method.get('method_name', 'N/A')}")
                
                formula = method.get('formula', '')
                if formula:
                    lines.append(f"    公式: {formula}")
                
                data_fields = method.get('data_fields_used', [])
                if data_fields:
                    if isinstance(data_fields, list):
                        fields_str = ', '.join(data_fields[:3])
                    else:
                        fields_str = str(data_fields)
                    lines.append(f"    数据字段: {fields_str}")
                
                lines.append("")
        
        # 统计分析方法
        analysis_methods = methods_info.get('analysis_methods', [])
        if analysis_methods:
            lines.append("推荐的统计分析方法:")
            for i, method in enumerate(analysis_methods, 1):
                lines.append(f"  {i}. {method.get('method_name', 'N/A')}")
                lines.append(f"     类型: {method.get('method_type', 'N/A')}")
                
                description = method.get('description', '')
                if description:
                    lines.append(f"     说明: {description[:100]}...")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取方法图谱统计信息
        
        Returns:
            统计信息字典
        """
        meta = self.knowledge_base.get('meta', {})
        
        # 统计分析方法类型分布
        method_type_count = {}
        for method in self.analysis_methods:
            method_type = method.get('method_type', 'unknown')
            method_type_count[method_type] = method_type_count.get(method_type, 0) + 1
        
        return {
            'total_papers_processed': meta.get('total_papers_processed', 0),
            'total_variables_with_methods': meta.get('total_variables_with_methods', 0),
            'total_analysis_methods': meta.get('total_analysis_methods', 0),
            'total_data_fields': meta.get('total_data_fields', 0),
            'method_type_distribution': method_type_count
        }


# 使用示例
if __name__ == "__main__":
    # 初始化查询器
    query = MethodGraphQuery()
    
    # 统计信息
    print("=== 方法图谱统计 ===")
    stats = query.get_statistics()
    print(f"处理论文数: {stats['total_papers_processed']}")
    print(f"变量覆盖数: {stats['total_variables_with_methods']}")
    print(f"分析方法数: {stats['total_analysis_methods']}")
    print(f"数据字段数: {stats['total_data_fields']}")
    print()
    
    # 查询变量测量方法
    print("=== 查询变量测量方法 ===")
    method = query.get_recommended_method("V16_tech_impact")
    if method:
        print(f"变量: V16_tech_impact")
        print(f"推荐方法: {method.get('method_name')}")
        print(f"公式: {method.get('formula', 'N/A')}")
        print(f"数据字段: {method.get('data_fields_used', [])}")
    print()
    
    # 搜索分析方法
    print("=== 搜索中介分析方法 ===")
    mediation_methods = query.search_analysis_methods(method_type='mediation')
    print(f"找到 {len(mediation_methods)} 个中介分析方法")
    for m in mediation_methods:
        print(f"  - {m.get('method_name')}")
    print()
    
    # 为假设获取方法
    print("=== 为假设获取方法 ===")
    hypothesis = {
        'type': 'mediation',
        'variables': {
            'independent': ['V09_tech_diversity'],
            'dependent': ['V16_tech_impact'],
            'mediator': ['V13_rd_efficiency']
        }
    }
    
    methods_info = query.get_methods_for_hypothesis(hypothesis)
    print(f"变量测量方法数: {len(methods_info['variable_methods'])}")
    print(f"推荐分析方法数: {len(methods_info['analysis_methods'])}")
