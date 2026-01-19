#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Claude API 从 PDF 文献中抽取变量测量方法和统计分析方法
- 支持并行处理（5线程）
- 自动合并多篇论文的方法
- 处理同一变量的多种测量方法
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import anthropic
from dotenv import load_dotenv

load_dotenv()

# 线程安全的计数器
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value


class MethodExtractor:
    """从 PDF 中抽取变量测量方法和统计分析方法"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """初始化"""
        self.api_key = api_key or os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("JUHENEXT_BASE_URL") or "https://api.anthropic.com"
        
        if not self.api_key:
            raise ValueError("请提供 API Key")
        
        self.model = model or os.getenv("CLAUDE_MODEL") or "claude-3-5-sonnet-20241022"
        
        print(f"使用 API: {self.base_url}")
        print(f"使用模型: {self.model}")
        
        # 加载变量定义
        self.variables = self._load_variables()
        
        # 加载提取Prompt
        self.system_prompt, self.user_prompt_template = self._load_prompts()
        
        # 线程安全的结果收集
        self.results_lock = threading.Lock()
        self.all_results = []
        self.counter = ThreadSafeCounter()
    
    def _get_client(self):
        """为每个线程创建独立的客户端"""
        return anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _load_variables(self) -> Dict[str, Any]:
        """加载30个变量定义"""
        ontology_path = "sandbox/static/data/causal_ontology_extracted.json"
        
        try:
            with open(ontology_path, 'r', encoding='utf-8') as f:
                graph = json.load(f)
            
            variables = {}
            for var in graph.get("variables", []):
                var_id = var["id"]
                variables[var_id] = {
                    "label": var["label"],
                    "category": var["category"],
                    "definition": var.get("definition", "")
                }
            
            print(f"✓ 加载了 {len(variables)} 个变量定义")
            return variables
            
        except Exception as e:
            print(f"警告: 加载变量定义失败 {e}")
            return {}
    
    def _load_prompts(self) -> tuple:
        """加载提取Prompt"""
        prompt_path = "prompts/extract_measurement_methods_prompt.md"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分离 System Prompt 和完整的 User Prompt（包括格式要求）
            parts = content.split("## System Prompt")
            if len(parts) < 2:
                raise ValueError("Prompt格式错误")
            
            system_part = parts[1].split("---")[0].strip()
            
            # User Prompt包含所有内容（从User Prompt Template到结束）
            user_part_start = content.find("## User Prompt Template")
            if user_part_start == -1:
                raise ValueError("找不到User Prompt Template")
            
            user_part = content[user_part_start:].replace("## User Prompt Template", "").strip()
            
            print(f"✓ 加载了提取Prompt")
            return system_part, user_part
            
        except Exception as e:
            print(f"警告: 加载Prompt失败 {e}")
            return "", ""
    
    def _build_variable_list(self) -> str:
        """构建变量列表字符串"""
        var_by_category = defaultdict(list)
        for var_id, var_info in self.variables.items():
            category = var_info["category"]
            var_by_category[category].append(
                f"  - {var_id}: {var_info['label']} - {var_info['definition']}"
            )
        
        return f"""
【输入变量 Input】
{chr(10).join(var_by_category.get('input', []))}

【中介变量 Mediator】
{chr(10).join(var_by_category.get('mediator', []))}

【结果变量 Outcome】
{chr(10).join(var_by_category.get('outcome', []))}

【调节变量 Moderator】
{chr(10).join(var_by_category.get('moderator', []))}
"""
    
    def _encode_pdf(self, pdf_path: str) -> str:
        """将 PDF 文件编码为 base64"""
        with open(pdf_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    
    def extract_from_pdf(self, pdf_path: str, total: int) -> Dict[str, Any]:
        """从单个 PDF 文件中抽取方法（线程安全）"""
        current = self.counter.increment()
        pdf_name = Path(pdf_path).name[:50]
        
        try:
            print(f"[{current}/{total}] 处理: {pdf_name}...")
            start_time = time.time()
            
            pdf_data = self._encode_pdf(pdf_path)
            
            # 构建用户Prompt（不使用format，直接替换）
            variable_list = self._build_variable_list()
            user_prompt = self.user_prompt_template.replace("{paper_title}", Path(pdf_path).stem)
            user_prompt = user_prompt.replace("{paper_year}", "Unknown")
            user_prompt = user_prompt.replace("{paper_abstract}", "")
            user_prompt = user_prompt.replace("{paper_methods_section}", "")
            user_prompt = user_prompt.replace("{variable_list}", variable_list)
            
            # 每个线程创建独立的客户端
            client = self._get_client()
            
            message = client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # 保存原始响应用于调试
            debug_file = Path("outputs") / f"debug_response_{current}.txt"
            debug_file.parent.mkdir(exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"  调试: 原始响应已保存到 {debug_file}")
            
            result = self._parse_response(response_text, pdf_path)
            
            elapsed = time.time() - start_time
            method_count = len(result.get("measurement_methods", []))
            analysis_count = len(result.get("analysis_methods", []))
            print(f"  ✓ [{current}/{total}] 成功: {method_count}个测量方法, {analysis_count}个分析方法 | {elapsed:.1f}秒")
            
            return result
            
        except Exception as e:
            print(f"  ✗ [{current}/{total}] 失败: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "paper_info": {
                    "title": Path(pdf_path).stem,
                    "has_measurement_methods": False,
                    "has_analysis_methods": False
                }
            }
    
    def _parse_response(self, response_text: str, pdf_path: str) -> Dict[str, Any]:
        """解析 Claude 的响应"""
        import re
        
        # 提取JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text.strip()
        
        # 解析JSON
        try:
            data = json.loads(json_str)
        except Exception as e:
            # 尝试修复
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            try:
                data = json.loads(json_str)
            except Exception as e2:
                # 保存原始响应用于调试
                debug_file = Path("outputs/debug_response.txt")
                debug_file.parent.mkdir(exist_ok=True)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                
                return {
                    "success": False,
                    "error": f"JSON解析失败: {str(e2)}",
                    "paper_info": {
                        "title": Path(pdf_path).stem,
                        "has_measurement_methods": False,
                        "has_analysis_methods": False
                    }
                }
        
        data["success"] = True
        data["file_path"] = str(pdf_path)
        return data
    
    def process_batch(self, pdf_files: List[str], max_workers: int = 5) -> List[Dict]:
        """并行处理多个PDF文件"""
        total = len(pdf_files)
        results = []
        
        print(f"\n开始并行处理 {total} 个文件 (线程数: {max_workers})")
        print("=" * 60)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_pdf = {
                executor.submit(self.extract_from_pdf, pdf, total): pdf 
                for pdf in pdf_files
            }
            
            # 收集结果
            for future in as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"  ✗ 异常: {Path(pdf).name[:30]} - {e}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "paper_info": {
                            "title": Path(pdf).stem,
                            "has_measurement_methods": False,
                            "has_analysis_methods": False
                        }
                    })
        
        return results


def merge_methods(results: List[Dict]) -> Dict[str, Any]:
    """合并多篇论文的方法，处理同一变量的多种测量方法"""
    
    # 按变量ID收集测量方法
    methods_by_variable = defaultdict(list)
    
    # 收集统计分析方法
    analysis_methods_collection = defaultdict(list)
    
    # 收集数据字段
    data_fields_collection = defaultdict(list)
    
    success_count = 0
    
    for result in results:
        if not result.get("success"):
            continue
        
        success_count += 1
        paper_title = result.get("paper_info", {}).get("title", "Unknown")
        paper_year = result.get("paper_info", {}).get("year", "Unknown")
        
        # 收集测量方法
        for method in result.get("measurement_methods", []):
            var_id = method.get("variable_id", "")
            if not var_id:
                continue
            
            methods_by_variable[var_id].append({
                "paper": paper_title,
                "year": paper_year,
                "method": method
            })
        
        # 收集分析方法
        for analysis in result.get("analysis_methods", []):
            method_name = analysis.get("method_name", "")
            if not method_name:
                continue
            
            analysis_methods_collection[method_name].append({
                "paper": paper_title,
                "year": paper_year,
                "method": analysis
            })
        
        # 收集数据字段
        for field in result.get("data_fields", []):
            field_name = field.get("field_name", "")
            if not field_name:
                continue
            
            data_fields_collection[field_name].append({
                "paper": paper_title,
                "field": field
            })
    
    # 构建最终的变量测量方法库
    variable_methods = {}
    
    for var_id, method_list in methods_by_variable.items():
        # 统计每种方法的使用频率
        method_frequency = defaultdict(int)
        method_details = defaultdict(list)
        
        for item in method_list:
            method_name = item["method"].get("method_name", "")
            method_frequency[method_name] += 1
            method_details[method_name].append(item)
        
        # 按使用频率排序
        sorted_methods = sorted(
            method_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 构建多种测量方法
        measurement_methods = []
        for method_name, freq in sorted_methods:
            # 选择最详细的一个作为代表
            representative = max(
                method_details[method_name],
                key=lambda x: len(str(x["method"]))
            )
            
            # 确定推荐级别
            if freq >= 5:
                recommendation_level = "highly_recommended"
            elif freq >= 3:
                recommendation_level = "recommended"
            else:
                recommendation_level = "alternative"
            
            measurement_methods.append({
                "method_name": method_name,
                "usage_frequency": freq,
                "usage_papers": [item["paper"] for item in method_details[method_name]],
                "recommendation_level": recommendation_level,
                "recommendation_reason": f"在{freq}篇论文中使用",
                **representative["method"]
            })
        
        # 确定默认方法（使用频率最高的）
        default_method = measurement_methods[0]["method_name"] if measurement_methods else None
        
        variable_methods[var_id] = {
            "variable_id": var_id,
            "variable_name": measurement_methods[0]["variable_name"] if measurement_methods else "",
            "total_methods": len(measurement_methods),
            "default_method": default_method,
            "method_selection_logic": "优先使用使用频率最高的方法",
            "measurement_methods": measurement_methods,
            "method_comparison": {
                "correlation": "待补充：不同方法之间的相关性",
                "pros_cons": "待补充：各方法的优缺点对比"
            }
        }
    
    # 构建统计分析方法库
    analysis_methods = []
    for method_name, method_list in analysis_methods_collection.items():
        # 选择最详细的一个作为代表
        representative = max(
            method_list,
            key=lambda x: len(str(x["method"]))
        )
        
        analysis_methods.append({
            "method_name": method_name,
            "usage_frequency": len(method_list),
            "usage_papers": [item["paper"] for item in method_list],
            **representative["method"]
        })
    
    # 按使用频率排序
    analysis_methods.sort(key=lambda x: x["usage_frequency"], reverse=True)
    
    # 构建数据字段库
    data_fields = []
    for field_name, field_list in data_fields_collection.items():
        # 合并相关变量
        related_vars = set()
        for item in field_list:
            related_vars.update(item["field"].get("related_variables", []))
        
        # 选择最详细的一个作为代表
        representative = max(
            field_list,
            key=lambda x: len(str(x["field"]))
        )
        
        data_fields.append({
            "field_name": field_name,
            "usage_frequency": len(field_list),
            "related_variables": list(related_vars),
            **representative["field"]
        })
    
    # 按使用频率排序
    data_fields.sort(key=lambda x: x["usage_frequency"], reverse=True)
    
    # 构建最终结果
    merged_result = {
        "meta": {
            "name": "Patent Analysis Method Knowledge Base",
            "version": "1.0",
            "description": "从50篇专利分析文献中提取的变量测量方法和统计分析方法",
            "created_date": time.strftime("%Y-%m-%d"),
            "total_papers_processed": len(results),
            "successful_extractions": success_count,
            "total_variables_with_methods": len(variable_methods),
            "total_analysis_methods": len(analysis_methods),
            "total_data_fields": len(data_fields)
        },
        "variable_measurement_methods": variable_methods,
        "statistical_analysis_methods": analysis_methods,
        "data_fields": data_fields
    }
    
    return merged_result


def main():
    """主函数"""
    print("=" * 60)
    print("变量测量方法提取器")
    print("=" * 60)
    
    extractor = MethodExtractor()
    
    # 获取PDF文件列表（前50篇）
    pdf_folder = Path("downloads")
    pdf_files = sorted(pdf_folder.glob("*.pdf"))[:50]
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    
    # 并行处理
    start_time = time.time()
    results = extractor.process_batch([str(f) for f in pdf_files], max_workers=5)
    total_time = time.time() - start_time
    
    # 保存原始结果
    output_dir = Path("outputs/method_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result.get("success"):
            title = result.get("paper_info", {}).get("title", "unknown")[:80]
            # 清理文件名
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
            output_file = output_dir / f"{safe_title}_methods.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)
    print(f"成功: {success_count}/{len(results)}")
    print(f"总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
    print(f"平均每篇: {total_time/len(results):.1f}秒")
    
    # 合并方法
    print("\n" + "=" * 60)
    print("合并方法...")
    print("=" * 60)
    
    merged_result = merge_methods(results)
    
    # 保存合并结果
    merged_file = "sandbox/static/data/method_knowledge_base.json"
    with open(merged_file, 'w', encoding='utf-8') as f:
        json.dump(merged_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 方法知识库已保存到: {merged_file}")
    print(f"  - 变量测量方法: {merged_result['meta']['total_variables_with_methods']} 个变量")
    print(f"  - 统计分析方法: {merged_result['meta']['total_analysis_methods']} 种方法")
    print(f"  - 数据字段: {merged_result['meta']['total_data_fields']} 个字段")
    
    # 保存汇总
    summary = {
        "meta": {
            "total_papers": len(results),
            "success_papers": success_count,
            "total_time_seconds": total_time,
            "avg_time_per_paper": total_time / len(results),
            "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "all_results": results
    }
    
    summary_file = output_dir / "extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 汇总结果已保存到: {summary_file}")


if __name__ == "__main__":
    main()
