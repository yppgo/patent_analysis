"""
Reviewer Agent - 审查者智能体
负责验证结果和生成最终分析报告
"""

import json
from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent


def extract_content(response) -> str:
    """
    从 LLM 响应中提取文本内容
    
    处理各种可能的响应类型：
    - AIMessage 对象
    - 字符串
    - 其他对象
    """
    if hasattr(response, 'content'):
        # AIMessage 对象
        content = response.content
        # content 可能还是个对象，再次检查
        if hasattr(content, 'strip'):
            return str(content)
        else:
            return str(content)
    else:
        return str(response)


class ReviewerAgent(BaseAgent):
    """
    审查者智能体（报告生成者）
    
    职责：
    1. 验证执行结果是否回答了用户问题
    2. 生成人类可读的最终分析报告
    3. （未来）回写知识图谱，积累新的分析经验
    
    工作流程：
    用户查询 + 执行结果 → 验证 → 生成报告 → (未来：回写图谱)
    """
    
    def __init__(self, llm_client, neo4j_connector=None, logger=None):
        """
        初始化 Reviewer
        
        Args:
            llm_client: LLM 客户端
            neo4j_connector: Neo4j 连接器（可选，用于未来的回写功能）
            logger: 日志记录器
        """
        super().__init__("Reviewer", llm_client, logger)
        self.neo4j = neo4j_connector
    
    def _load_analysis_results(self) -> str:
        """
        读取所有生成的 CSV 文件，返回格式化的数据摘要
        重点：统计信息 + 关键发现，而不是原始数据
        """
        import pandas as pd
        from pathlib import Path
        import glob
        
        results = []
        
        # 查找所有 step_*.csv 文件
        csv_files = glob.glob('outputs/step_*_results.csv')
        
        if not csv_files:
            return "（未找到分析结果文件）"
        
        for csv_file in sorted(csv_files):
            try:
                df = pd.read_csv(csv_file)
                
                # 提取文件名中的步骤号
                step_name = Path(csv_file).stem
                
                # 生成数据摘要
                summary = f"\n### {step_name}\n"
                summary += f"- 文件: {csv_file}\n"
                summary += f"- 总行数: {len(df)}\n"
                summary += f"- 列名: {list(df.columns)}\n\n"
                
                # 基本统计（所有数据）
                if len(df.columns) > 0:
                    summary += f"**统计摘要（基于全部 {len(df)} 行数据）：**\n"
                    for col in df.columns:
                        if df[col].dtype in ['int64', 'float64']:
                            summary += f"  * {col}:\n"
                            summary += f"    - 最小值: {df[col].min():.4f}\n"
                            summary += f"    - 最大值: {df[col].max():.4f}\n"
                            summary += f"    - 平均值: {df[col].mean():.4f}\n"
                            summary += f"    - 标准差: {df[col].std():.4f}\n"
                        elif df[col].dtype == 'bool' or col.startswith('is_'):
                            # 布尔类型或标志列
                            value_counts = df[col].value_counts()
                            summary += f"  * {col}:\n"
                            for val, count in value_counts.items():
                                pct = count / len(df) * 100
                                summary += f"    - {val}: {count} ({pct:.1f}%)\n"
                        else:
                            unique_count = df[col].nunique()
                            summary += f"  * {col}: {unique_count} 个唯一值\n"
                            # 如果唯一值不多，显示分布
                            if unique_count <= 10:
                                value_counts = df[col].value_counts().head(5)
                                summary += f"    - 前5个值: {dict(value_counts)}\n"
                
                # 显示关键样本（头尾各3行）
                summary += f"\n**数据样本（头3行）：**\n```\n{df.head(3).to_string(max_colwidth=40)}\n```\n"
                
                if len(df) > 6:
                    summary += f"\n**数据样本（尾3行）：**\n```\n{df.tail(3).to_string(max_colwidth=40)}\n```\n"
                
                # 特殊分析：如果有异常检测结果
                if 'is_outlier' in df.columns:
                    outliers = df[df['is_outlier'] == 1]
                    summary += f"\n**关键发现：**\n"
                    summary += f"  - 检测到 {len(outliers)} 个异常值（占比 {len(outliers)/len(df)*100:.1f}%）\n"
                    if len(outliers) > 0 and 'patent_id' in df.columns:
                        summary += f"  - 异常专利ID: {list(outliers['patent_id'].head(10))}\n"
                
                # 特殊分析：如果有主题分布
                if 'dominant_topic' in df.columns:
                    topic_dist = df['dominant_topic'].value_counts()
                    summary += f"\n**关键发现：**\n"
                    summary += f"  - 主题分布:\n"
                    for topic, count in topic_dist.items():
                        pct = count / len(df) * 100
                        summary += f"    * 主题 {topic}: {count} 个专利 ({pct:.1f}%)\n"
                
                results.append(summary)
                
            except Exception as e:
                results.append(f"\n### {csv_file}\n- 读取失败: {e}\n")
        
        return "\n".join(results)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理执行结果，生成最终报告
        
        Args:
            input_data: {
                "user_goal": str,           # 用户原始查询
                "blueprint": dict,          # 战略蓝图
                "execution_specs": list,    # 执行规格
                "generated_codes": list,    # 生成的代码
                "code_metadata": list       # 代码元数据
            }
            
        Returns:
            {
                "verification_result": dict,  # 验证结果
                "final_report": str,          # 最终报告
                "writeback_status": str       # 回写状态（暂未实现）
            }
        """
        # 保存input_data供其他方法使用
        self._current_input = input_data
        
        user_goal = input_data.get('user_goal', '')
        blueprint = input_data.get('blueprint', {})
        code_metadata = input_data.get('code_metadata', [])
        generated_codes = input_data.get('generated_codes', [])
        
        self.log(f"开始审查结果: {user_goal[:50]}...")
        
        # 步骤 1: 验证执行结果
        verification = self._verify_execution(user_goal, blueprint, code_metadata)
        self.log(f"验证完成: {'✅ 通过' if verification['passed'] else '⚠️ 部分通过'}")
        
        # 步骤 2: 生成最终报告
        final_report = self._generate_final_report(
            user_goal, 
            blueprint, 
            code_metadata,
            generated_codes,
            verification
        )
        self.log("最终报告生成完成")
        
        # 步骤 3: 回写知识图谱（暂未实现）
        writeback_status = self._writeback_to_graph(
            user_goal,
            blueprint,
            verification
        )
        
        return {
            'verification_result': verification,
            'final_report': final_report,
            'writeback_status': writeback_status
        }
    
    def _verify_execution(
        self, 
        user_goal: str, 
        blueprint: Dict, 
        code_metadata: List[Dict]
    ) -> Dict[str, Any]:
        """
        验证执行结果
        
        检查：
        1. 所有步骤是否成功执行
        2. 代码质量是否合格
        3. 结果是否回答了用户问题
        """
        # 统计执行情况
        total_steps = len(code_metadata)
        successful_steps = sum(1 for meta in code_metadata if meta.get('is_valid', False))
        failed_steps = total_steps - successful_steps
        
        # 计算成功率
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        
        # 收集问题
        issues = []
        for i, meta in enumerate(code_metadata, 1):
            if not meta.get('is_valid', False):
                issues.append(f"步骤 {i}: {', '.join(meta.get('issues', ['未知错误']))}")
        
        # 判断是否通过
        passed = success_rate >= 80  # 80% 以上算通过
        
        # 使用 LLM 进行语义验证
        semantic_check = self._semantic_verification(user_goal, blueprint, code_metadata)
        
        return {
            'passed': passed and semantic_check['relevant'],
            'success_rate': success_rate,
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'issues': issues,
            'semantic_check': semantic_check
        }
    
    def _semantic_verification(
        self,
        user_goal: str,
        blueprint: Dict,
        code_metadata: List[Dict]
    ) -> Dict[str, Any]:
        """
        语义验证：使用 LLM 判断结果是否回答了用户问题
        """
        prompt = f"""你是专利分析领域的专家。请判断以下分析结果是否回答了用户的问题。

**用户问题:**
{user_goal}

**分析方案:**
研究目标: {blueprint.get('research_objective', 'N/A')}
分析步骤: {len(blueprint.get('analysis_logic_chains', []))} 个

**执行情况:**
成功步骤: {sum(1 for m in code_metadata if m.get('is_valid', False))}/{len(code_metadata)}

**判断要求:**
1. 分析方案是否针对用户问题
2. 执行的步骤是否合理
3. 结果是否能回答用户问题

**输出格式（严格 JSON）:**
{{
  "relevant": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "判断理由"
}}

只输出 JSON，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = extract_content(response).strip()
            
            # 清理响应
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            self.log(f"语义验证失败: {e}", "warning")
            return {
                'relevant': True,  # 默认认为相关
                'confidence': 0.5,
                'reasoning': f'验证失败: {e}'
            }
    
    def _generate_final_report(
        self,
        user_goal: str,
        blueprint: Dict,
        code_metadata: List[Dict],
        generated_codes: List[str],
        verification: Dict
    ) -> str:
        """
        生成最终分析报告
        
        报告包括：
        1. 执行摘要
        2. 分析方法（详细参数配置）
        3. 实际分析结果（从 CSV 文件读取）
        4. 主要发现
        5. 结论和建议
        """
        # 读取所有生成的 CSV 文件
        analysis_data = self._load_analysis_results()
        
        # 提取详细的方法配置信息
        method_details = self._extract_method_details(blueprint)
        
        # 提取执行规格信息
        execution_specs = self._current_input.get('execution_specs', []) if hasattr(self, '_current_input') else []
        execution_specs_info = self._format_execution_specs(execution_specs)
        
        prompt = f"""你是专利分析领域的资深研究员。请根据以下**真实分析数据**生成一份专业的分析报告。

**重要提示：报告必须基于下面提供的真实数据，特别是实际的分析结果。**

**用户研究目标:**
{user_goal}

**分析蓝图（报告结构应遵循这个蓝图）:**
{json.dumps(blueprint, indent=2, ensure_ascii=False)}

**实际分析结果（从文件读取）:**
{analysis_data}

**执行情况:**
- 总步骤数: {len(code_metadata)}
- 成功步骤: {sum(1 for m in code_metadata if m.get('is_valid', False))}
- 验证状态: {'通过' if verification.get('passed') else '部分通过'}

**报告要求:**
1. **严格按照蓝图的步骤组织报告**：蓝图中有几个步骤，报告就有几个对应的章节
2. **基于实际数据**：报告中的所有数字、发现都必须来自"实际分析结果"
3. **具体而非抽象**：
   - ❌ "识别了技术空白"
   - ✅ "识别了3个技术空白（is_outlier=True），占比6%"
4. **包含关键发现**：从数据中提取最重要的洞察
5. **结构清晰**：使用 Markdown 格式
6. **长度适中**：1000-2000字

**报告结构（必须遵循）:**
# 专利分析报告

## 1. 执行摘要
（基于实际数据的简要总结，包含关键数字）

## 2. 研究目标
（用户的研究目标）

## 3. 分析方法与结果
（按照蓝图的步骤顺序，每个步骤一个小节）

### 3.1 步骤1: [蓝图中的步骤1名称]
- **方法**: [蓝图中的方法]
- **参数**: [蓝图中的参数]
- **结果**: [从实际数据中提取的结果]
- **发现**: [关键洞察]

### 3.2 步骤2: [蓝图中的步骤2名称]
- **方法**: [蓝图中的方法]
- **参数**: [蓝图中的参数]
- **结果**: [从实际数据中提取的结果]
- **发现**: [关键洞察]

（以此类推）

## 4. 主要发现
（综合所有步骤的关键洞察）

## 5. 结论与建议
（基于发现的建议）

请生成报告：

**分析方案:**
研究目标: {blueprint.get('research_objective', 'N/A')}
预期成果: {', '.join(blueprint.get('expected_outcomes', []))}

**详细分析方法配置:**
{method_details}

**执行规格详情:**
{execution_specs_info}

**执行情况统计:**
- 总步骤数: {verification['total_steps']}
- 成功步骤: {verification['successful_steps']}
- 失败步骤: {verification['failed_steps']}
- 成功率: {verification['success_rate']:.1f}%
- 验证状态: {'✅ 通过' if verification['passed'] else '⚠️ 部分通过'}
- 代码迭代次数: {self._format_iteration_stats(code_metadata)}

**问题列表:**
{chr(10).join(f'- {issue}' for issue in verification['issues']) if verification['issues'] else '✅ 所有步骤执行成功，无错误'}

**语义验证结果:**
- 相关性: {'✅ 相关' if verification['semantic_check']['relevant'] else '❌ 不相关'}
- 置信度: {verification['semantic_check']['confidence']:.1%}
- 理由: {verification['semantic_check']['reasoning']}

**代码质量指标:**
{self._format_code_quality(code_metadata)}

**实际执行结果:**
{analysis_data}

**报告要求:**
1. **必须基于上述真实数据**，特别是"实际执行结果"部分
2. 如果有执行结果，在"主要发现"部分详细展示这些数据
3. 如果没有执行结果，说明分析框架已建立，需要实际运行才能得到具体发现
4. 使用专业但易懂的语言
5. 结构清晰，包含具体的量化指标
6. 突出方法的科学性和执行的成功率
7. 如果有失败步骤，说明原因和影响
8. 报告长度：600-1000 字

**报告结构:**
# 专利分析报告

## 1. 执行摘要
[概述分析目标、采用的方法和执行情况]

## 2. 研究目标与预期成果
[明确说明研究目标和预期产出]

## 3. 分析方法与技术配置
[详细说明每个步骤的方法、算法、参数配置]
- 步骤1: [方法名] - [算法] - [关键参数]
- 步骤2: [方法名] - [算法] - [关键参数]
- ...

## 4. 执行情况与质量指标
[提供具体的执行统计数据]
- 成功率、步骤数、迭代次数
- 代码质量指标
- 验证结果

## 5. 分析框架评估
[说明建立的分析框架的科学性和完整性，但明确指出需要实际数据运行才能得到具体发现]

## 6. 结论与建议
[总结分析框架的价值，提供下一步建议]

请生成报告："""

        try:
            response = self.llm.invoke(prompt)
            content = extract_content(response)
            return content.strip()
            
        except Exception as e:
            self.log(f"报告生成失败: {e}", "error")
            return self._generate_fallback_report(
                user_goal, 
                blueprint, 
                verification
            )
    
    def _format_analysis_steps(self, logic_chains: List[Dict]) -> str:
        """格式化分析步骤"""
        if not logic_chains:
            return "无"
        
        formatted = []
        for i, step in enumerate(logic_chains, 1):
            formatted.append(
                f"{i}. {step.get('objective', 'N/A')} "
                f"(方法: {step.get('method', 'N/A')})"
            )
        
        return "\n".join(formatted)
    
    def _extract_method_details(self, blueprint: Dict) -> str:
        """
        提取详细的方法配置信息
        """
        logic_chains = blueprint.get('analysis_logic_chains', [])
        if not logic_chains:
            return "无详细配置信息"
        
        details = []
        for i, step in enumerate(logic_chains, 1):
            config = step.get('implementation_config', {})
            params = config.get('parameters', {})
            
            detail = f"""
步骤 {i}: {step.get('objective', 'N/A')}
  - 方法: {step.get('method', 'N/A')}
  - 算法: {config.get('algorithm', 'N/A')}
  - 参数配置: {json.dumps(params, ensure_ascii=False) if params else '默认参数'}
  - 数据需求: {', '.join(config.get('data_requirements', []))}
  - 输出格式: {config.get('output_format', 'N/A')}
  - 依赖步骤: {step.get('depends_on', [])}
"""
            details.append(detail.strip())
        
        return "\n\n".join(details)
    
    def _format_execution_specs(self, execution_specs: List[Dict]) -> str:
        """
        格式化执行规格信息
        """
        if not execution_specs:
            return "执行规格信息不可用"
        
        specs = []
        for i, spec in enumerate(execution_specs, 1):
            libraries = ', '.join(spec.get('required_libraries', []))
            processing_steps = len(spec.get('processing_steps', []))
            
            spec_info = f"""
步骤 {i}: {spec.get('function_name', 'N/A')}
  - 函数签名: {spec.get('function_signature', 'N/A')}
  - 依赖库: {libraries}
  - 处理子步骤数: {processing_steps}
  - 输入数据结构: {spec.get('input_specification', {}).get('data_structure', 'N/A')}
  - 输出数据结构: {spec.get('output_specification', {}).get('data_structure', 'N/A')}
"""
            specs.append(spec_info.strip())
        
        return "\n\n".join(specs)
    
    def _format_iteration_stats(self, code_metadata: List[Dict]) -> str:
        """
        格式化代码迭代统计
        """
        if not code_metadata:
            return "无迭代数据"
        
        iterations = [meta.get('iteration_count', 0) for meta in code_metadata]
        total_iterations = sum(iterations)
        max_iterations = max(iterations) if iterations else 0
        
        return f"总计 {total_iterations} 次迭代，最大单步迭代 {max_iterations} 次"
    
    def _format_code_quality(self, code_metadata: List[Dict]) -> str:
        """
        格式化代码质量指标
        """
        if not code_metadata:
            return "无质量数据"
        
        quality_info = []
        for i, meta in enumerate(code_metadata, 1):
            is_valid = meta.get('is_valid', False)
            issues = meta.get('issues', [])
            runtime_error = meta.get('runtime_error', '')
            iteration_count = meta.get('iteration_count', 0)
            
            status = "✅ 有效" if is_valid else "❌ 无效"
            quality_info.append(
                f"步骤 {i}: {status} | 迭代次数: {iteration_count} | "
                f"问题数: {len(issues)} | "
                f"运行时错误: {'无' if not runtime_error else '有'}"
            )
        
        return "\n".join(quality_info)
    
    def _format_analysis_results(self, analysis_results: List[Dict]) -> str:
        """
        格式化实际执行结果
        """
        if not analysis_results or all(r is None for r in analysis_results):
            return "⚠️ 代码未实际执行，无执行结果数据"
        
        formatted = []
        for i, result in enumerate(analysis_results, 1):
            if result is None:
                formatted.append(f"步骤 {i}: 未执行")
                continue
            
            # 解析结果 - 支持多种类型
            result_info = [f"步骤 {i}:"]
            
            # 处理不同类型的结果
            if isinstance(result, dict):
                # 字典类型
                for key, value in result.items():
                    if isinstance(value, dict):
                        if value.get('type') == 'dataframe':
                            shape = value.get('shape', 'unknown')
                            columns = value.get('columns', [])
                            result_info.append(f"  - {key}: DataFrame {shape}, 列: {columns[:5]}...")
                        elif value.get('type') == 'array':
                            shape = value.get('shape', 'unknown')
                            sample = value.get('sample', [])
                            result_info.append(f"  - {key}: Array {shape}, 样本: {sample[:5]}...")
                        elif value.get('type') == 'object':
                            result_info.append(f"  - {key}: {value.get('value', 'N/A')[:100]}...")
                        else:
                            result_info.append(f"  - {key}: {value}")
                    else:
                        result_info.append(f"  - {key}: {value}")
            elif isinstance(result, list):
                # 列表类型
                result_info.append(f"  类型: List")
                result_info.append(f"  长度: {len(result)}")
                if result:
                    result_info.append(f"  样本: {result[:3]}...")
            else:
                # 其他类型
                result_info.append(f"  类型: {type(result).__name__}")
                result_info.append(f"  值: {str(result)[:200]}...")
            
            formatted.append("\n".join(result_info))
        
        return "\n\n".join(formatted)
    
    def _generate_fallback_report(
        self,
        user_goal: str,
        blueprint: Dict,
        verification: Dict
    ) -> str:
        """
        生成备用报告（当 LLM 失败时）
        """
        report = f"""# 专利分析报告

## 1. 执行摘要

本次分析针对用户目标："{user_goal}"

研究目标：{blueprint.get('research_objective', 'N/A')}

## 2. 分析方法

本次分析共包含 {verification['total_steps']} 个步骤：

{self._format_analysis_steps(blueprint.get('analysis_logic_chains', []))}

## 3. 执行情况

- 成功步骤：{verification['successful_steps']}/{verification['total_steps']}
- 成功率：{verification['success_rate']:.1f}%
- 验证状态：{'✅ 通过' if verification['passed'] else '⚠️ 部分通过'}

## 4. 问题说明

{chr(10).join(f'- {issue}' for issue in verification['issues']) if verification['issues'] else '执行过程顺利，未发现问题。'}

## 5. 结论

{'分析成功完成，结果可用于后续研究。' if verification['passed'] else '分析部分完成，建议检查失败步骤并重新执行。'}
"""
        return report
    
    def _writeback_to_graph(
        self,
        user_goal: str,
        blueprint: Dict,
        verification: Dict
    ) -> str:
        """
        回写知识图谱（暂未实现）
        
        未来功能：
        1. 将成功的分析经验写入图谱
        2. 创建新的 Paper 节点（代表本次分析）
        3. 创建 AnalysisEvent 节点
        4. 建立与 Intent、Method 的关系
        5. 记录 Conclusion
        
        Args:
            user_goal: 用户目标
            blueprint: 战略蓝图
            verification: 验证结果
            
        Returns:
            回写状态信息
        """
        if not self.neo4j:
            return "⏸️ 回写功能未启用（Neo4j 连接器未提供）"
        
        if not verification['passed']:
            return "⏸️ 回写跳过（验证未通过）"
        
        # TODO: 实现回写逻辑
        # 1. 创建 Paper 节点（本次分析）
        # 2. 创建 AnalysisEvent 节点
        # 3. 建立关系
        # 4. 记录结论
        
        self.log("回写功能暂未实现", "info")
        return "⏸️ 回写功能开发中"
    
    def generate_summary(self, final_report: str, max_length: int = 200) -> str:
        """
        生成报告摘要
        
        Args:
            final_report: 完整报告
            max_length: 最大长度
            
        Returns:
            摘要文本
        """
        prompt = f"""请将以下报告总结为 {max_length} 字以内的摘要：

{final_report}

只输出摘要，不要其他文字。"""

        try:
            response = self.llm.invoke(prompt)
            content = extract_content(response)
            return content.strip()
        except Exception as e:
            self.log(f"摘要生成失败: {e}", "warning")
            # 简单截取前 max_length 字符
            return final_report[:max_length] + "..."

