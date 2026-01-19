#!/usr/bin/env python3
"""
变量匹配器 - 从用户问题中检索相关变量
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple


class VariableMatcher:
    """从用户研究问题中匹配因果图谱中的变量"""
    
    def __init__(self, ontology_path: str = "static/data/complete_causal_ontology.json"):
        """加载因果本体论"""
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        
        # 构建检索索引
        self._build_index()
    
    def _build_index(self):
        """构建变量检索索引"""
        self.variable_index = {}
        
        for var in self.ontology['variables']:
            # 索引：变量ID → 变量对象
            self.variable_index[var['id']] = var
            
            # 索引：关键词 → 变量ID列表
            keywords = self._extract_keywords(var)
            for keyword in keywords:
                if keyword not in self.variable_index:
                    self.variable_index[keyword] = []
                self.variable_index[keyword].append(var['id'])
    
    def _extract_keywords(self, variable: Dict) -> List[str]:
        """从变量中提取关键词"""
        keywords = []
        
        # 1. 变量标签
        keywords.append(variable['label'].lower())
        
        # 2. 变量定义中的关键词
        definition_words = variable['definition'].lower().split()
        keywords.extend([w for w in definition_words if len(w) > 2])
        
        # 3. 测量指标
        keywords.append(variable['measurement']['metric'].lower())
        
        # 4. 理论名称中的关键词
        theory_words = variable['theory']['name'].lower().split()
        keywords.extend([w for w in theory_words if len(w) > 3])
        
        return list(set(keywords))  # 去重
    
    def match_variables(self, user_question: str) -> Dict:
        """
        从用户问题中匹配相关变量
        
        Args:
            user_question: 用户的研究问题
            
        Returns:
            匹配结果，包含因变量、自变量、调节变量等
        """
        # 步骤1：意图识别
        intent = self._identify_intent(user_question)
        
        # 步骤2：提取关键词
        keywords = self._extract_question_keywords(user_question)
        
        # 步骤3：匹配因变量（研究目标）
        outcome_var = self._match_outcome_variable(intent, keywords)
        
        # 步骤4：匹配自变量（潜在驱动因素）
        predictor_vars = self._match_predictor_variables(outcome_var, keywords)
        
        # 步骤5：匹配调节变量
        moderator_vars = self._match_moderator_variables(keywords)
        
        # 步骤6：推荐因果路径
        relevant_paths = self._recommend_paths(outcome_var, predictor_vars)
        
        return {
            'user_question': user_question,
            'intent': intent,
            'keywords': keywords,
            'outcome_variable': outcome_var,
            'predictor_variables': predictor_vars,
            'moderator_variables': moderator_vars,
            'relevant_paths': relevant_paths
        }
    
    def _identify_intent(self, question: str) -> str:
        """识别研究意图"""
        question_lower = question.lower()
        
        # 意图关键词映射
        intent_patterns = {
            'impact_drivers': ['影响', '驱动', '因素', '决定', 'impact', 'driver', 'factor'],
            'mechanism': ['如何', '机制', '过程', 'how', 'mechanism', 'process'],
            'comparison': ['比较', '差异', '对比', 'compare', 'difference'],
            'prediction': ['预测', '趋势', '未来', 'predict', 'trend', 'future'],
            'evaluation': ['评估', '测量', '衡量', 'evaluate', 'measure', 'assess']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(p in question_lower for p in patterns):
                return intent
        
        return 'general'
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """从问题中提取关键词"""
        # 简化版：分词 + 过滤停用词
        stopwords = {'的', '是', '在', '有', '和', '与', '对', '等', '及', '或'}
        words = question.replace('？', ' ').replace('?', ' ').split()
        keywords = [w.lower() for w in words if w not in stopwords and len(w) > 1]
        return keywords
    
    def _match_outcome_variable(self, intent: str, keywords: List[str]) -> Dict:
        """匹配因变量（研究目标）"""
        # 根据意图和关键词匹配结果变量
        outcome_vars = [v for v in self.ontology['variables'] if v['category'] == 'outcome']
        
        # 关键词匹配评分
        scores = []
        for var in outcome_vars:
            score = 0
            var_text = f"{var['label']} {var['definition']}".lower()
            
            for keyword in keywords:
                if keyword in var_text:
                    score += 1
            
            scores.append((var, score))
        
        # 返回得分最高的
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0] if scores else outcome_vars[0]
    
    def _match_predictor_variables(self, outcome_var: Dict, keywords: List[str]) -> List[Dict]:
        """匹配自变量（潜在驱动因素）"""
        # 查找指向该结果变量的因果路径
        relevant_paths = [
            p for p in self.ontology['causal_paths']
            if p.get('target') == outcome_var['id']
        ]
        
        # 提取这些路径的源变量
        predictor_ids = [p['source'] for p in relevant_paths]
        predictors = [self.variable_index[vid] for vid in predictor_ids if vid in self.variable_index]
        
        # 如果没有直接路径，返回所有输入和中介变量
        if not predictors:
            predictors = [
                v for v in self.ontology['variables']
                if v['category'] in ['input', 'mediator']
            ][:5]  # 限制数量
        
        return predictors
    
    def _match_moderator_variables(self, keywords: List[str]) -> List[Dict]:
        """匹配调节变量"""
        moderators = [v for v in self.ontology['variables'] if v['category'] == 'moderator']
        
        # 简单返回所有调节变量（可以根据关键词进一步筛选）
        return moderators
    
    def _recommend_paths(self, outcome_var: Dict, predictor_vars: List[Dict]) -> List[Dict]:
        """推荐相关的因果路径"""
        relevant_paths = []
        
        predictor_ids = [v['id'] for v in predictor_vars]
        
        for path in self.ontology['causal_paths']:
            # 直接路径：predictor → outcome
            if (path.get('source') in predictor_ids and 
                path.get('target') == outcome_var['id']):
                relevant_paths.append(path)
            
            # 中介路径：predictor → mediator → outcome
            if path.get('source') in predictor_ids:
                # 查找从该中介变量到结果变量的路径
                mediator_id = path.get('target')
                for p2 in self.ontology['causal_paths']:
                    if (p2.get('source') == mediator_id and 
                        p2.get('target') == outcome_var['id']):
                        relevant_paths.append({
                            'type': 'mediation',
                            'path1': path,
                            'path2': p2
                        })
        
        return relevant_paths


def demo():
    """演示变量匹配"""
    matcher = VariableMatcher()
    
    # 测试问题
    test_questions = [
        "什么因素影响技术影响力？",
        "国际合作如何提升专利价值？",
        "技术跨界度对创新有什么作用？",
        "如何提高研发效率？"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print(f"{'='*60}")
        
        result = matcher.match_variables(question)
        
        print(f"\n意图: {result['intent']}")
        print(f"关键词: {', '.join(result['keywords'])}")
        
        print(f"\n因变量（研究目标）:")
        outcome = result['outcome_variable']
        print(f"  - {outcome['id']}: {outcome['label']}")
        print(f"    定义: {outcome['definition']}")
        
        print(f"\n自变量（潜在驱动因素）:")
        for var in result['predictor_variables'][:3]:
            print(f"  - {var['id']}: {var['label']}")
        
        print(f"\n调节变量:")
        for var in result['moderator_variables']:
            print(f"  - {var['id']}: {var['label']}")
        
        print(f"\n相关因果路径: {len(result['relevant_paths'])}条")
        for i, path in enumerate(result['relevant_paths'][:3], 1):
            if path.get('type') == 'mediation':
                print(f"  {i}. 中介路径（复杂）")
            else:
                source = matcher.variable_index[path['source']]
                target = matcher.variable_index[path['target']]
                print(f"  {i}. {source['label']} → {target['label']} ({path['effect_type']})")


if __name__ == '__main__':
    demo()
