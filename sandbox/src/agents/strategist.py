import json
import os
# 如果你没有安装 langchain，可以用这个假的 BaseAgent 代替
# from src.agents.base_agent import BaseAgent 

class Strategist:
    def __init__(self, graph_path="static/data/causal_graph.json"):
        self.graph_path = graph_path
        self.causal_graph = self._load_graph()

    def _load_graph(self):
        if not os.path.exists(self.graph_path):
            raise FileNotFoundError(f"找不到图谱文件: {self.graph_path}")
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze(self, user_query):
        """核心思考逻辑：从 Query 到 Plan"""
        print(f"🤖 [Strategist] 收到指令: '{user_query}'，正在检索因果图谱...")
        
        plan = {
            "query": user_query,
            "tasks": [],     # 要执行的函数列表
            "edges": []      # 要验证的假设逻辑
        }

        # 简单的规则匹配：遍历图谱里所有的边
        # (在真实 LLM 版中，这里会用 GPT-4 挑选最相关的边)
        for edge in self.causal_graph['edges']:
            source_id = edge['source']
            target_id = edge['target']
            
            # 找到对应的节点定义
            source_node = next(n for n in self.causal_graph['nodes'] if n['id'] == source_id)
            target_node = next(n for n in self.causal_graph['nodes'] if n['id'] == target_id)
            
            # 提取函数名
            func_src = source_node['binding']['func']
            func_tgt = target_node['binding']['func']
            
            # 加入任务列表 (去重)
            if func_src not in plan['tasks']: plan['tasks'].append(func_src)
            if func_tgt not in plan['tasks']: plan['tasks'].append(func_tgt)
            
            # 记录这条逻辑链，方便后续填空
            plan['edges'].append({
                "source_label": source_node['label'],
                "target_label": target_node['label'],
                "func_src": func_src,
                "func_tgt": func_tgt,
                "template": edge['template']
            })
            
        print(f"🤖 [Strategist] 规划完成。生成了 {len(plan['tasks'])} 个计算任务。")
        return plan