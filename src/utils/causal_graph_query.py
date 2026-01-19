"""
因果图谱查询器
用于从因果本体论中检索因果关系和研究假设
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class CausalGraphQuery:
    """因果图谱查询器"""
    
    def __init__(self, ontology_path: str = "sandbox/static/data/causal_ontology_extracted.json"):
        """
        初始化因果图谱查询器
        
        Args:
            ontology_path: 因果本体论文件路径
        """
        self.ontology_path = ontology_path
        self.ontology = self._load_ontology()
        self.variables = {v['id']: v for v in self.ontology['variables']}
        self.paths = self.ontology['causal_paths']
        
        # 构建邻接表（用于路径搜索）
        self.adjacency = self._build_adjacency_list()
    
    def _load_ontology(self) -> Dict:
        """加载因果本体论"""
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_adjacency_list(self) -> Dict[str, List[Dict]]:
        """构建邻接表"""
        adjacency = {}
        for path in self.paths:
            source = path['source']
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append(path)
        return adjacency
    
    def get_variable(self, var_id: str) -> Optional[Dict]:
        """
        获取变量定义
        
        Args:
            var_id: 变量ID（如 "V03_rd_investment"）
            
        Returns:
            变量定义字典，如果不存在则返回 None
        """
        return self.variables.get(var_id)
    
    def find_direct_path(self, source: str, target: str) -> Optional[Dict]:
        """
        查找两个变量之间的直接因果路径
        
        Args:
            source: 源变量ID
            target: 目标变量ID
            
        Returns:
            因果路径字典，如果不存在则返回 None
        """
        for path in self.paths:
            if path['source'] == source and path['target'] == target:
                return path
        return None
    
    def find_all_paths(self, source: str, target: str, max_depth: int = 3) -> List[List[Dict]]:
        """
        查找两个变量之间的所有因果路径（包括中介路径）
        
        使用 BFS 搜索，最多搜索 max_depth 层
        
        Args:
            source: 源变量ID
            target: 目标变量ID
            max_depth: 最大搜索深度
            
        Returns:
            路径列表，每个路径是一个因果关系列表
        """
        all_paths = []
        
        # BFS 队列：(当前节点, 当前路径, 已访问节点)
        queue = [(source, [], set([source]))]
        
        while queue:
            current, path, visited = queue.pop(0)
            
            # 达到目标
            if current == target and path:
                all_paths.append(path)
                continue
            
            # 达到最大深度
            if len(path) >= max_depth:
                continue
            
            # 扩展邻居
            if current in self.adjacency:
                for edge in self.adjacency[current]:
                    next_node = edge['target']
                    if next_node not in visited:
                        new_path = path + [edge]
                        new_visited = visited | {next_node}
                        queue.append((next_node, new_path, new_visited))
        
        return all_paths
    
    def get_paths_from_variable(self, var_id: str) -> List[Dict]:
        """
        获取从某个变量出发的所有因果路径
        
        Args:
            var_id: 变量ID
            
        Returns:
            因果路径列表
        """
        return [p for p in self.paths if p['source'] == var_id]
    
    def get_paths_to_variable(self, var_id: str) -> List[Dict]:
        """
        获取指向某个变量的所有因果路径
        
        Args:
            var_id: 变量ID
            
        Returns:
            因果路径列表
        """
        return [p for p in self.paths if p['target'] == var_id]
    
    def search_variables_by_keyword(self, keyword: str) -> List[Dict]:
        """
        根据关键词搜索变量
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的变量列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for var in self.ontology['variables']:
            # 搜索变量标签和定义
            if (keyword_lower in var['label'].lower() or 
                keyword_lower in var['definition'].lower()):
                results.append(var)
        
        return results
    
    def suggest_hypotheses(self, user_goal: str, top_k: int = 5) -> List[Dict]:
        """
        根据用户目标推荐研究假设
        
        简单版本：基于关键词匹配
        高级版本：可以集成 LLM 进行语义理解
        
        Args:
            user_goal: 用户研究目标
            top_k: 返回前 k 个假设
            
        Returns:
            假设列表，每个假设包含因果路径和相关信息
        """
        # 提取关键词（简单版本：分词）
        keywords = user_goal.lower().split()
        
        # 评分：匹配的关键词越多，分数越高
        scored_paths = []
        for path in self.paths:
            # 跳过未映射的变量
            if path['source'] not in self.variables or path['target'] not in self.variables:
                continue
            
            score = 0
            source_var = self.variables[path['source']]
            target_var = self.variables[path['target']]
            
            # 检查源变量
            for keyword in keywords:
                if keyword in source_var['label'].lower():
                    score += 2
                if keyword in source_var['definition'].lower():
                    score += 1
            
            # 检查目标变量
            for keyword in keywords:
                if keyword in target_var['label'].lower():
                    score += 2
                if keyword in target_var['definition'].lower():
                    score += 1
            
            # 检查机制描述
            if path.get('mechanism'):
                for keyword in keywords:
                    if keyword in path['mechanism'].lower():
                        score += 1
            
            if score > 0:
                scored_paths.append((score, path))
        
        # 按分数排序
        scored_paths.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前 k 个
        return [
            {
                'score': score,
                'path': path,
                'source_var': self.variables[path['source']],
                'target_var': self.variables[path['target']]
            }
            for score, path in scored_paths[:top_k]
        ]
    
    def get_mediation_paths(self, source: str, target: str) -> List[Dict]:
        """
        查找中介路径（A → M → B）
        
        Args:
            source: 源变量ID
            target: 目标变量ID
            
        Returns:
            中介路径列表，每个包含 source → mediator → target
        """
        mediation_paths = []
        
        # 查找所有长度为2的路径
        all_paths = self.find_all_paths(source, target, max_depth=2)
        
        for path in all_paths:
            if len(path) == 2:
                mediator = path[0]['target']
                mediation_paths.append({
                    'source': source,
                    'mediator': mediator,
                    'target': target,
                    'path_1': path[0],
                    'path_2': path[1],
                    'mediator_var': self.variables[mediator]
                })
        
        return mediation_paths
    
    def get_moderation_effects(self, source: str, target: str) -> List[Dict]:
        """
        查找调节效应（M 调节 A → B）
        
        从 complex_relations 中提取
        
        Args:
            source: 源变量ID
            target: 目标变量ID
            
        Returns:
            调节效应列表
        """
        moderation_effects = []
        
        # 遍历所有路径，查找 complex_relations
        for path in self.paths:
            if path['source'] == source and path['target'] == target:
                # 检查是否有 complex_relations（某些路径可能没有）
                # 这里需要从原始数据中查找
                pass
        
        # TODO: 需要从原始抽取结果中获取 complex_relations
        # 当前版本的 causal_ontology_extracted.json 只有路径，没有复杂关系
        
        return moderation_effects
    
    def format_hypothesis(self, path: Dict) -> str:
        """
        格式化因果路径为研究假设
        
        Args:
            path: 因果路径字典
            
        Returns:
            格式化的假设文本
        """
        source_var = self.variables[path['source']]
        target_var = self.variables[path['target']]
        
        effect_type = path['effect_type']
        effect_size = path['effect_size']
        
        # 效应类型映射
        effect_map = {
            'positive': '正向影响',
            'negative': '负向影响',
            'inverted_u': '倒U型影响',
            'threshold': '阈值效应'
        }
        
        effect_text = effect_map.get(effect_type, effect_type)
        
        hypothesis = f"H: {source_var['label']}对{target_var['label']}有{effect_text}（效应大小：{effect_size}）"
        
        if path.get('mechanism'):
            hypothesis += f"\n   机制：{path['mechanism']}"
        
        if path.get('evidence', {}).get('evidence_count'):
            count = path['evidence']['evidence_count']
            hypothesis += f"\n   证据：{count}篇文献支持"
        
        return hypothesis
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取因果图谱统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_variables': len(self.variables),
            'total_paths': len(self.paths),
            'validated_paths': sum(1 for p in self.paths if p.get('evidence', {}).get('validated')),
            'variable_categories': {
                'input': sum(1 for v in self.variables.values() if v['category'] == 'input'),
                'mediator': sum(1 for v in self.variables.values() if v['category'] == 'mediator'),
                'outcome': sum(1 for v in self.variables.values() if v['category'] == 'outcome'),
                'moderator': sum(1 for v in self.variables.values() if v['category'] == 'moderator')
            },
            'effect_types': {
                'positive': sum(1 for p in self.paths if p['effect_type'] == 'positive'),
                'negative': sum(1 for p in self.paths if p['effect_type'] == 'negative'),
                'inverted_u': sum(1 for p in self.paths if p['effect_type'] == 'inverted_u'),
                'threshold': sum(1 for p in self.paths if p['effect_type'] == 'threshold')
            }
        }
    
    # ==================== 假设生成器 V2（6种策略）====================
    
    def generate_hypotheses_v2(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整的6步假设生成流程
        
        Args:
            user_input: {
                "domain": "量子计算",
                "intent": "技术趋势分析" 或 "影响力驱动因素分析"
            }
        
        Returns:
            {
                "step1_input": {...},
                "step2_analysis": {...},
                "step3_matching": {...},
                "step4_literature": {...},
                "step5_hypotheses": [...],
                "step6_recommendation": {...}
            }
        """
        # Step 1: 用户输入
        step1 = {
            "domain": user_input.get("domain", ""),
            "intent": user_input.get("intent", ""),
            "timestamp": "2026-01-19"
        }
        
        # Step 2: 意图分析
        step2 = self._analyze_intent(step1)
        
        # Step 3: 变量匹配
        step3 = self._match_variables(step2)
        
        # Step 4: 文献检查
        step4 = self._check_literature(step3)
        
        # Step 5: 假设生成（6种策略）
        step5 = self._generate_all_hypotheses(step3, step4)
        
        # Step 6: 排序推荐
        step6 = self._rank_and_recommend(step5)
        
        return {
            "step1_input": step1,
            "step2_analysis": step2,
            "step3_matching": step3,
            "step4_literature": step4,
            "step5_hypotheses": step5,
            "step6_recommendation": step6
        }
    
    def _analyze_intent(self, user_input: Dict) -> Dict:
        """
        Step 2: 意图分析
        
        从用户输入中提取关键词和研究意图
        """
        domain = user_input.get("domain", "")
        intent = user_input.get("intent", "")
        
        # 提取关键词
        keywords = [domain]
        if "趋势" in intent or "trend" in intent.lower():
            keywords.extend(["趋势分析", "时间序列"])
        if "影响" in intent or "impact" in intent.lower():
            keywords.extend(["影响力", "驱动因素"])
        if "空白" in intent or "gap" in intent.lower():
            keywords.extend(["技术空白", "机会识别"])
        
        # 识别目标变量
        outcome_var = None
        if "影响力" in intent or "impact" in intent.lower():
            outcome_var = "V16_tech_impact"
        elif "突破" in intent or "breakthrough" in intent.lower():
            outcome_var = "V17_tech_breakthrough"
        elif "价值" in intent or "value" in intent.lower():
            outcome_var = "V19_commercial_value"
        
        return {
            "detected_intent": intent,
            "extracted_keywords": keywords,
            "matched_outcome_variable": outcome_var
        }
    
    def _match_variables(self, analysis: Dict) -> Dict:
        """
        Step 3: 变量匹配
        
        根据关键词匹配相关变量
        """
        outcome_var_id = analysis.get("matched_outcome_variable")
        
        # 获取目标变量
        outcome_var = None
        if outcome_var_id and outcome_var_id in self.variables:
            outcome_var = self.variables[outcome_var_id]
        
        # 找到所有指向目标变量的路径
        candidate_predictors = []
        if outcome_var_id:
            paths_to_outcome = self.get_paths_to_variable(outcome_var_id)
            for path in paths_to_outcome:
                source_var = self.variables.get(path['source'])
                if source_var and source_var not in candidate_predictors:
                    candidate_predictors.append(source_var)
        
        # 找到调节变量（category = moderator）
        candidate_moderators = [
            v for v in self.variables.values()
            if v.get('category') == 'moderator'
        ]
        
        # 找到中介变量（category = mediator）
        candidate_mediators = [
            v for v in self.variables.values()
            if v.get('category') == 'mediator'
        ]
        
        return {
            "outcome_variable": outcome_var,
            "candidate_predictors": candidate_predictors[:10],  # 限制数量
            "candidate_moderators": candidate_moderators,
            "candidate_mediators": candidate_mediators
        }
    
    def _check_literature(self, matching: Dict) -> Dict:
        """
        Step 4: 文献检查
        
        检查哪些路径已验证，哪些未探索
        """
        outcome_var = matching.get("outcome_variable")
        if not outcome_var:
            return {"validated_paths": [], "unexplored_paths": []}
        
        outcome_var_id = outcome_var['id']
        
        # 检查所有指向目标变量的路径
        validated_paths = []
        unexplored_paths = []
        
        for predictor in matching.get("candidate_predictors", []):
            predictor_id = predictor['id']
            path = self.find_direct_path(predictor_id, outcome_var_id)
            
            if path:
                evidence = path.get('evidence', {})
                is_validated = evidence.get('validated', False)
                evidence_count = evidence.get('evidence_count', 0)
                
                if is_validated and evidence_count > 5:
                    validated_paths.append({
                        "source": predictor_id,
                        "target": outcome_var_id,
                        "path": path,
                        "evidence_count": evidence_count
                    })
                else:
                    unexplored_paths.append({
                        "source": predictor_id,
                        "target": outcome_var_id,
                        "path": path,
                        "reason": "文献证据不足" if evidence_count <= 5 else "未验证"
                    })
            else:
                # 没有直接路径，可能是未探索的
                unexplored_paths.append({
                    "source": predictor_id,
                    "target": outcome_var_id,
                    "path": None,
                    "reason": "文献中未研究"
                })
        
        return {
            "validated_paths": validated_paths,
            "unexplored_paths": unexplored_paths
        }
    
    def _generate_all_hypotheses(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        Step 5: 生成所有假设（6种策略）
        """
        hypotheses = []
        
        # 策略1: 理论迁移
        h1 = self._strategy_theory_transfer(matching, literature)
        if h1:
            hypotheses.extend(h1)
        
        # 策略2: 路径探索
        h2 = self._strategy_path_exploration(matching, literature)
        if h2:
            hypotheses.extend(h2)
        
        # 策略3: 边界条件
        h3 = self._strategy_boundary_condition(matching, literature)
        if h3:
            hypotheses.extend(h3)
        
        # 策略4: 中介机制
        h4 = self._strategy_mediation(matching, literature)
        if h4:
            hypotheses.extend(h4)
        
        # 策略5: 反事实推理
        h5 = self._strategy_counterfactual(matching, literature)
        if h5:
            hypotheses.extend(h5)
        
        # 策略6: 交互效应
        h6 = self._strategy_interaction(matching, literature)
        if h6:
            hypotheses.extend(h6)
        
        return hypotheses
    
    def _strategy_theory_transfer(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略1: 理论迁移
        
        将已验证的理论应用到新领域（假设用户的领域是新的）
        """
        hypotheses = []
        validated_paths = literature.get("validated_paths", [])
        
        # 只取1个最佳的已验证路径
        for i, vpath in enumerate(validated_paths[:1]):  # 从2个减少到1个
            source_var = self.variables.get(vpath['source'])
            target_var = self.variables.get(vpath['target'])
            path = vpath['path']
            
            if source_var and target_var:
                hypothesis = {
                    "id": f"H_transfer_{i+1}",
                    "statement": f"{source_var['label']}对{target_var['label']}有{self._effect_type_cn(path['effect_type'])}影响",
                    "type": "theory_transfer",
                    "strategy_description": "理论迁移：将已验证的理论应用到新领域",
                    "novelty_score": 0.7,
                    "variables": {
                        "independent": [vpath['source']],
                        "dependent": [vpath['target']],
                        "moderator": [],
                        "mediator": []
                    },
                    "theoretical_basis": source_var.get('definition', ''),
                    "evidence": {
                        "validated": True,
                        "evidence_count": vpath['evidence_count'],
                        "note": "已在其他领域验证，迁移到新领域"
                    },
                    "mechanism": path.get('mechanism', '')
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _strategy_path_exploration(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略2: 路径探索
        
        探索文献中未研究过的因果路径
        """
        hypotheses = []
        unexplored_paths = literature.get("unexplored_paths", [])
        
        # 只取1个最有潜力的未探索路径
        for i, upath in enumerate(unexplored_paths[:1]):  # 从2个减少到1个
            source_var = self.variables.get(upath['source'])
            target_var = self.variables.get(upath['target'])
            
            if source_var and target_var:
                hypothesis = {
                    "id": f"H_exploration_{i+1}",
                    "statement": f"{source_var['label']}对{target_var['label']}的影响（探索性假设）",
                    "type": "path_exploration",
                    "strategy_description": "路径探索：发现文献空白",
                    "novelty_score": 0.85,
                    "variables": {
                        "independent": [upath['source']],
                        "dependent": [upath['target']],
                        "moderator": [],
                        "mediator": []
                    },
                    "theoretical_basis": f"基于{source_var.get('definition', '')}的理论推导",
                    "evidence": {
                        "validated": False,
                        "evidence_count": 0,
                        "note": upath['reason']
                    },
                    "mechanism": "待探索"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _strategy_boundary_condition(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略3: 边界条件
        
        为已知关系寻找调节变量
        """
        hypotheses = []
        validated_paths = literature.get("validated_paths", [])
        moderators = matching.get("candidate_moderators", [])
        
        # 取第1个已验证路径和第1个调节变量
        if validated_paths and moderators:
            vpath = validated_paths[0]
            moderator = moderators[0]
            
            source_var = self.variables.get(vpath['source'])
            target_var = self.variables.get(vpath['target'])
            
            if source_var and target_var:
                hypothesis = {
                    "id": "H_moderation_1",
                    "statement": f"{moderator['label']}调节{source_var['label']}对{target_var['label']}的影响",
                    "type": "moderation",
                    "strategy_description": "边界条件：揭示理论的适用范围",
                    "novelty_score": 0.65,
                    "variables": {
                        "independent": [vpath['source']],
                        "dependent": [vpath['target']],
                        "moderator": [moderator['id']],
                        "mediator": []
                    },
                    "theoretical_basis": f"{moderator.get('definition', '')}影响作用强度",
                    "evidence": {
                        "validated": False,
                        "evidence_count": 0,
                        "note": "调节效应待验证"
                    },
                    "mechanism": f"{moderator['label']}改变{source_var['label']}的作用强度"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _strategy_mediation(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略4: 中介机制
        
        揭示因果关系的中介机制（2跳路径：X → M → Y）
        """
        hypotheses = []
        outcome_var = matching.get("outcome_variable")
        mediators = matching.get("candidate_mediators", [])
        
        if not outcome_var or not mediators:
            return hypotheses
        
        outcome_var_id = outcome_var['id']
        
        # 找到所有中介路径
        mediation_paths = []
        for mediator in mediators[:5]:  # 检查前5个中介变量
            mediator_id = mediator['id']
            # 查找 X → M → Y 的路径
            for predictor in matching.get("candidate_predictors", [])[:10]:
                predictor_id = predictor['id']
                # 检查是否存在 X → M 和 M → Y
                path_xm = self.find_direct_path(predictor_id, mediator_id)
                path_my = self.find_direct_path(mediator_id, outcome_var_id)
                
                if path_xm and path_my:
                    # 计算路径质量分数
                    quality_score = self._calculate_mediation_quality(path_xm, path_my)
                    
                    mediation_paths.append({
                        "source": predictor_id,
                        "mediator": mediator_id,
                        "target": outcome_var_id,
                        "path_xm": path_xm,
                        "path_my": path_my,
                        "quality_score": quality_score
                    })
        
        # 按质量分数排序（优先选择高质量路径）
        mediation_paths.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # 生成前2个中介假设（从3个减少到2个）
        for i, mpath in enumerate(mediation_paths[:2]):  # 增加到3个
            source_var = self.variables.get(mpath['source'])
            mediator_var = self.variables.get(mpath['mediator'])
            target_var = self.variables.get(mpath['target'])
            
            if source_var and mediator_var and target_var:
                # 根据路径质量调整新颖性评分
                base_novelty = 0.75
                quality_bonus = (mpath['quality_score'] - 50) / 100  # 质量分数转换为bonus
                novelty_score = min(0.85, max(0.65, base_novelty + quality_bonus))
                
                hypothesis = {
                    "id": f"H_mediation_{i+1}",
                    "statement": f"{mediator_var['label']}中介{source_var['label']}对{target_var['label']}的影响",
                    "type": "mediation",
                    "strategy_description": "中介机制：打开因果黑箱",
                    "novelty_score": round(novelty_score, 2),
                    "variables": {
                        "independent": [mpath['source']],
                        "dependent": [mpath['target']],
                        "moderator": [],
                        "mediator": [mpath['mediator']]
                    },
                    "theoretical_basis": f"{source_var['label']} → {mediator_var['label']} → {target_var['label']}",
                    "evidence": {
                        "validated": False,
                        "evidence_count": 0,
                        "note": f"中介路径待验证（路径质量分数：{mpath['quality_score']:.1f}）"
                    },
                    "mechanism": f"{source_var['label']}通过促进{mediator_var['label']}来提升{target_var['label']}",
                    "path_quality": {
                        "score": mpath['quality_score'],
                        "path_xm_evidence": mpath['path_xm'].get('evidence', {}).get('evidence_count', 0),
                        "path_my_evidence": mpath['path_my'].get('evidence', {}).get('evidence_count', 0)
                    }
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _calculate_mediation_quality(self, path_xm: Dict, path_my: Dict) -> float:
        """
        计算中介路径的质量分数（0-100）
        
        考虑因素：
        1. 文献证据数量
        2. 效应大小
        3. 是否已验证
        
        Args:
            path_xm: X → M 路径
            path_my: M → Y 路径
            
        Returns:
            质量分数（0-100）
        """
        score = 0.0
        
        # 因素1：文献证据（最高40分）
        evidence_xm = path_xm.get('evidence', {}).get('evidence_count', 0)
        evidence_my = path_my.get('evidence', {}).get('evidence_count', 0)
        evidence_score = min(40, (evidence_xm + evidence_my) * 2)
        score += evidence_score
        
        # 因素2：效应大小（最高30分）
        effect_size_map = {'large': 30, 'medium': 20, 'small': 10}
        effect_xm = effect_size_map.get(path_xm.get('effect_size', 'medium'), 20)
        effect_my = effect_size_map.get(path_my.get('effect_size', 'medium'), 20)
        effect_score = (effect_xm + effect_my) / 2
        score += effect_score
        
        # 因素3：验证状态（最高30分）
        validated_xm = path_xm.get('evidence', {}).get('validated', False)
        validated_my = path_my.get('evidence', {}).get('validated', False)
        if validated_xm and validated_my:
            score += 30
        elif validated_xm or validated_my:
            score += 15
        
        return round(score, 1)
    
    def _strategy_counterfactual(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略5: 反事实推理
        
        基于理论推导反直觉的假设
        """
        hypotheses = []
        # 这个策略需要数据支持，暂时生成一个示例
        
        # 示例：在某些条件下，常见的正向关系可能变为负向
        validated_paths = literature.get("validated_paths", [])
        if validated_paths:
            vpath = validated_paths[0]
            source_var = self.variables.get(vpath['source'])
            target_var = self.variables.get(vpath['target'])
            
            if source_var and target_var:
                hypothesis = {
                    "id": "H_counterfactual_1",
                    "statement": f"在特定条件下，{source_var['label']}对{target_var['label']}可能有负向影响（反直觉假设）",
                    "type": "counterfactual",
                    "strategy_description": "反事实推理：发现反直觉现象",
                    "novelty_score": 0.9,
                    "variables": {
                        "independent": [vpath['source']],
                        "dependent": [vpath['target']],
                        "moderator": [],
                        "mediator": []
                    },
                    "theoretical_basis": "在特定情境下，常见关系可能逆转",
                    "evidence": {
                        "validated": False,
                        "evidence_count": 0,
                        "note": "需要数据验证的反直觉假设"
                    },
                    "mechanism": "待数据分析发现"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _strategy_interaction(self, matching: Dict, literature: Dict) -> List[Dict]:
        """
        策略6: 交互效应
        
        探索多个变量的联合作用
        """
        hypotheses = []
        predictors = matching.get("candidate_predictors", [])
        outcome_var = matching.get("outcome_variable")
        
        if len(predictors) >= 2 and outcome_var:
            # 取前2个预测变量
            var1 = predictors[0]
            var2 = predictors[1]
            
            hypothesis = {
                "id": "H_interaction_1",
                "statement": f"{var1['label']}与{var2['label']}的交互作用对{outcome_var['label']}有影响",
                "type": "interaction",
                "strategy_description": "交互效应：探索协同作用",
                "novelty_score": 0.8,
                "variables": {
                    "independent": [var1['id'], var2['id']],
                    "dependent": [outcome_var['id']],
                    "moderator": [],
                    "mediator": []
                },
                "theoretical_basis": f"{var1['label']}和{var2['label']}可能产生协同效应",
                "evidence": {
                    "validated": False,
                    "evidence_count": 0,
                    "note": "交互效应待验证"
                },
                "mechanism": f"{var1['label']}和{var2['label']}共同作用产生更强效果"
            }
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _rank_and_recommend(self, hypotheses: List[Dict]) -> Dict:
        """
        Step 6: 分层推荐
        
        采用三层推荐策略：
        1. 核心推荐（3个）：综合分最高、新颖性最高、质量最高
        2. 备选推荐（2-3个）：其他高分假设
        3. 完整列表：所有假设供参考
        """
        if not hypotheses:
            return {
                "core_recommendations": [],
                "alternative_recommendations": [],
                "all_hypotheses": [],
                "summary": "未生成假设"
            }
        
        # 为每个假设计算综合分和质量分
        for h in hypotheses:
            novelty = h['novelty_score']
            quality = h.get('path_quality', {}).get('score', 50)  # 单跳假设默认50分
            
            # 平衡型综合分（新颖性60% + 质量40%）
            balanced_score = novelty * 0.6 + (quality / 100) * 0.4
            
            h['evaluation'] = {
                'novelty_score': novelty,
                'quality_score': quality,
                'balanced_score': round(balanced_score, 3)
            }
        
        # 排序
        by_balanced = sorted(hypotheses, key=lambda h: h['evaluation']['balanced_score'], reverse=True)
        by_novelty = sorted(hypotheses, key=lambda h: h['evaluation']['novelty_score'], reverse=True)
        by_quality = sorted(hypotheses, key=lambda h: h['evaluation']['quality_score'], reverse=True)
        
        # 核心推荐（3个）
        core_recommendations = []
        selected_ids = set()
        
        # 1. 综合分最高
        if by_balanced:
            top_balanced = by_balanced[0]
            core_recommendations.append({
                "rank": 1,
                "priority": "核心推荐",
                "hypothesis": top_balanced,
                "reason": f"综合分最高（{top_balanced['evaluation']['balanced_score']:.3f}），平衡创新与可靠性",
                "recommendation_type": "balanced"
            })
            selected_ids.add(top_balanced['id'])
        
        # 2. 新颖性最高（如果与综合分最高不同）
        if by_novelty:
            top_novelty = by_novelty[0]
            if top_novelty['id'] not in selected_ids:
                core_recommendations.append({
                    "rank": 2,
                    "priority": "核心推荐",
                    "hypothesis": top_novelty,
                    "reason": f"新颖性最高（{top_novelty['evaluation']['novelty_score']}），潜在突破性发现",
                    "recommendation_type": "innovative"
                })
                selected_ids.add(top_novelty['id'])
            else:
                # 如果重复，选第二高新颖性的
                if len(by_novelty) > 1:
                    second_novelty = by_novelty[1]
                    core_recommendations.append({
                        "rank": 2,
                        "priority": "核心推荐",
                        "hypothesis": second_novelty,
                        "reason": f"新颖性高（{second_novelty['evaluation']['novelty_score']}），探索性研究价值",
                        "recommendation_type": "innovative"
                    })
                    selected_ids.add(second_novelty['id'])
        
        # 3. 质量最高（如果与前两个不同）
        if by_quality:
            for candidate in by_quality:
                if candidate['id'] not in selected_ids:
                    core_recommendations.append({
                        "rank": 3,
                        "priority": "核心推荐",
                        "hypothesis": candidate,
                        "reason": f"质量最高（{candidate['evaluation']['quality_score']:.1f}分），理论基础扎实",
                        "recommendation_type": "conservative"
                    })
                    selected_ids.add(candidate['id'])
                    break
        
        # 备选推荐（2-3个）
        alternative_recommendations = []
        for h in by_balanced[1:]:  # 跳过第一个（已在核心推荐中）
            if h['id'] not in selected_ids and len(alternative_recommendations) < 3:
                alternative_recommendations.append({
                    "hypothesis": h,
                    "reason": f"综合分{h['evaluation']['balanced_score']:.3f}，可作为备选方案"
                })
                selected_ids.add(h['id'])
        
        # 生成推荐总结
        summary = self._generate_recommendation_summary(core_recommendations, alternative_recommendations)
        
        return {
            "core_recommendations": core_recommendations,
            "alternative_recommendations": alternative_recommendations,
            "all_hypotheses": by_balanced,  # 按综合分排序的完整列表
            "summary": summary,
            "total_count": len(hypotheses),
            "core_count": len(core_recommendations),
            "alternative_count": len(alternative_recommendations)
        }
    
    def _generate_recommendation_summary(self, core: List[Dict], alternatives: List[Dict]) -> str:
        """生成推荐总结"""
        if not core:
            return "未生成推荐"
        
        summary_parts = [
            f"共生成 {len(core)} 个核心推荐假设",
        ]
        
        if core:
            top = core[0]['hypothesis']
            summary_parts.append(
                f"最推荐：{top['id']} - {top['statement']} "
                f"(综合分{top['evaluation']['balanced_score']:.3f})"
            )
        
        if alternatives:
            summary_parts.append(f"另有 {len(alternatives)} 个备选方案")
        
        return "；".join(summary_parts)
    
    def _effect_type_cn(self, effect_type: str) -> str:
        """将效应类型转换为中文"""
        mapping = {
            "positive": "正向",
            "negative": "负向",
            "inverted_u": "倒U型",
            "threshold": "阈值"
        }
        return mapping.get(effect_type, effect_type)


# 使用示例
if __name__ == "__main__":
    # 初始化查询器
    query = CausalGraphQuery()
    
    # 统计信息
    print("=== 因果图谱统计 ===")
    stats = query.get_statistics()
    print(f"变量总数: {stats['total_variables']}")
    print(f"路径总数: {stats['total_paths']}")
    print(f"已验证路径: {stats['validated_paths']}")
    print()
    
    # 查找直接路径
    print("=== 查找直接路径 ===")
    path = query.find_direct_path("V03_rd_investment", "V16_tech_impact")
    if path:
        print(query.format_hypothesis(path))
    print()
    
    # 查找中介路径
    print("=== 查找中介路径 ===")
    mediation = query.get_mediation_paths("V03_rd_investment", "V16_tech_impact")
    print(f"找到 {len(mediation)} 条中介路径")
    for m in mediation[:3]:
        print(f"  {m['source']} → {m['mediator']} → {m['target']}")
    print()
    
    # 推荐假设
    print("=== 推荐研究假设 ===")
    hypotheses = query.suggest_hypotheses("研发投资对技术影响力的影响", top_k=3)
    for i, hyp in enumerate(hypotheses, 1):
        print(f"{i}. {query.format_hypothesis(hyp['path'])}")
        print()
