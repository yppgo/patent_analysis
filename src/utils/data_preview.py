"""
数据预览工具
为 Strategist 和 Methodologist 提供数据结构和统计信息

增强功能（v2）：
- 跨列统计：相关系数、分组对比、时间趋势
- 摘要分层抽样：按 IPC 部分层抽样摘要
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


class DataPreview:
    """
    数据预览生成器
    在蓝图设计前为智能体提供数据洞察
    """
    
    # 高基数阈值
    HIGH_CARDINALITY_THRESHOLD = 50
    
    # 适合作为类别变量的最大唯一值数
    CATEGORY_VAR_MAX_UNIQUE = 20

    # 分隔符列检测：仅对这些关键词列更可信
    DELIMITER_COLNAME_KEYWORDS = [
        "发明人",
        "申请",
        "专利",
        "地址",
        "国家",
        "地区",
        "IPC",
    ]

    # 前缀提取建议仅对这些字段更可信（避免标题/摘要类长文本误导）
    PREFIX_COLNAME_KEYWORDS = [
        "IPC",
        "分类",
        "地区",
        "国家",
    ]

    # 关键列样例行（仅注入这些列，避免 Prompt 过长）
    KEY_SAMPLE_COLUMNS = [
        "序号",
        "公开(公告)号",
        "授权日",
        "IPC主分类号",
        "被引用专利数量",
        "引用专利数量",
        "发明人",
        "Topic_Label",
    ]
    
    @classmethod
    def from_file(cls, file_path: str, sheet_name: str = None) -> 'DataPreview':
        """从文件加载数据并生成预览"""
        path = Path(file_path)
        
        # 转换为小写进行比较，支持大小写不敏感
        suffix_lower = path.suffix.lower()
        
        if suffix_lower in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0)
        elif suffix_lower == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")
        
        return cls(df)
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._preview = None
    
    def generate(self) -> Dict[str, Any]:
        """生成完整的数据预览"""
        if self._preview is not None:
            return self._preview
        
        self._preview = {
            "basic": self._generate_basic_info(),
            "columns": self._generate_column_info(),
            "recommendations": self._generate_recommendations(),
            "sample_rows": self._generate_sample_rows(),
            "cross_column_stats": self._compute_cross_column_stats(),
            "sampled_abstracts": self._sample_abstracts_stratified(),
        }
        
        return self._preview
    
    def _generate_basic_info(self) -> Dict[str, Any]:
        """生成基础信息"""
        return {
            "shape": {
                "rows": int(self.df.shape[0]),
                "columns": int(self.df.shape[1])
            },
            "column_names": self.df.columns.tolist(),
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
    
    def _generate_column_info(self) -> Dict[str, Dict]:
        """生成每列的详细信息"""
        columns_info = {}
        
        for col in self.df.columns:
            col_data = self.df[col]
            dtype = str(col_data.dtype)
            nunique = col_data.nunique()
            null_count = int(col_data.isnull().sum())
            
            info = {
                "dtype": dtype,
                "unique_count": int(nunique),
                "null_count": null_count,
                "null_percent": round(null_count / len(self.df) * 100, 1)
            }
            
            # 判断列角色
            if nunique == len(self.df):
                info["role"] = "ID列（唯一标识）"
                info["sample"] = col_data.head(2).tolist()
            
            elif dtype in ['int64', 'float64']:
                # 数值列：统计信息
                info["role"] = "数值列"
                info["stats"] = {
                    "mean": round(float(col_data.mean()), 2),
                    "median": round(float(col_data.median()), 2),
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "std": round(float(col_data.std()), 2)
                }
            
            elif nunique <= self.CATEGORY_VAR_MAX_UNIQUE:
                # 低基数列：适合做类别变量
                info["role"] = "类别列（适合做分类变量）"
                info["categories"] = col_data.value_counts().head(10).to_dict()
            
            elif nunique <= self.HIGH_CARDINALITY_THRESHOLD:
                # 中等基数列
                info["role"] = "中等基数列"
                info["top_10"] = col_data.value_counts().head(10).to_dict()
                info["sample"] = col_data.dropna().head(3).tolist()
            
            else:
                # 高基数列：需要警告
                info["role"] = "高基数列"
                info["warning"] = f"唯一值过多({nunique})，不适合直接作为类别变量"
                info["suggestion"] = "考虑：1)提取前缀分组 2)聚合为Top-N+其他 3)转换为数值特征"
                info["sample"] = col_data.dropna().head(3).tolist()
                
                # 检查是否可以提取前缀
                if dtype == 'object' and any(k in col for k in self.PREFIX_COLNAME_KEYWORDS):
                    sample_series = col_data.dropna().astype(str)
                    if len(sample_series) > 0:
                        avg_len = sample_series.head(50).str.len().mean()
                        # 长文本列前缀无意义，跳过
                        if avg_len <= 40:
                            sample_val = str(sample_series.iloc[0])
                            if len(sample_val) >= 4:
                                prefix_nunique = sample_series.str[:4].nunique()
                                if prefix_nunique < nunique:
                                    info["prefix_suggestion"] = f"提取前4位可减少到{prefix_nunique}个类别"
            
            # 增强检测：日期列
            if dtype == 'object' and not info.get("role", "").startswith("ID"):
                date_info = self._detect_date_column(col_data, col)
                if date_info:
                    info.update(date_info)
            
            # 增强检测：分隔符列（如 "张三;李四;王五"）
            if dtype == 'object' and not info.get("role", "").startswith("ID"):
                delimiter_info = self._detect_delimiter_column(col_data, col)
                if delimiter_info:
                    info.update(delimiter_info)
            
            columns_info[col] = info
        
        return columns_info
    
    def _detect_date_column(self, col_data: pd.Series, col_name: str) -> Optional[Dict]:
        """检测日期列"""
        # 根据列名判断
        date_keywords = ['日', 'date', 'time', '时间', '年', '月']
        if any(kw in col_name.lower() for kw in date_keywords):
            sample = col_data.dropna().head(3).tolist()
            try:
                # 尝试解析日期
                parsed = pd.to_datetime(col_data.dropna().head(100), errors='coerce')
                valid_ratio = parsed.notna().sum() / min(100, len(col_data.dropna()))
                if valid_ratio > 0.8:
                    min_year = parsed.dropna().dt.year.min()
                    max_year = parsed.dropna().dt.year.max()
                    return {
                        "role": "日期列",
                        "date_range": f"{min_year}~{max_year}",
                        "derived_suggestion": f"可计算时间差（如：2026 - 年份 = 专利年龄）",
                        "sample": sample
                    }
            except:
                pass
        return None
    
    def _detect_delimiter_column(self, col_data: pd.Series, col_name: str) -> Optional[Dict]:
        """检测分隔符列（如多个发明人用分号分隔）"""
        # 仅对“看起来像列表字段”的列启用，避免对摘要/标题等长文本误报
        if not any(k in col_name for k in self.DELIMITER_COLNAME_KEYWORDS):
            return None

        # 检查是否包含分隔符（默认不检测英文逗号，中文文本太容易误报）
        delimiters = [';', '|', '；']
        sample_values = col_data.dropna().astype(str).head(50)

        # 进一步降噪：如果文本很长，往往是自然语言而不是列表
        if len(sample_values) > 0:
            avg_len = sample_values.str.len().mean()
            if avg_len > 80:
                return None
        
        for delim in delimiters:
            # 计算包含分隔符的比例
            contains_delim = sample_values.str.contains(delim, regex=False, na=False)
            if contains_delim.sum() / len(sample_values) > 0.3:
                # 计算平均元素数
                avg_count = sample_values.str.split(delim).apply(len).mean()
                if avg_count > 1.5:
                    suggestion = self._make_delimiter_suggestion(col_name, delim)
                    return {
                        "has_delimiter": True,
                        "delimiter": delim,
                        "avg_items": round(avg_count, 1),
                        "derived_suggestion": suggestion
                    }
        return None

    def _make_delimiter_suggestion(self, col_name: str, delim: str) -> str:
        """根据列名生成更贴合语义的派生建议"""
        if "发明人" in col_name:
            return f"可按'{delim}'分割后计数（发明人数量）"
        if "被引用" in col_name and "专利" in col_name:
            return f"可按'{delim}'分割后计数（被引用专利条目数/前向引文数量核验）"
        if "引用" in col_name and "专利" in col_name:
            return f"可按'{delim}'分割后计数（引用专利条目数/后向引文数量核验）"
        return f"可按'{delim}'分割后计数（列表长度特征）"
    
    def _generate_recommendations(self) -> List[Dict]:
        """生成数据使用建议"""
        recommendations = []
        
        # 识别潜在的ID列
        id_cols = [col for col in self.df.columns 
                   if self.df[col].nunique() == len(self.df)]
        if id_cols:
            recommendations.append({
                "type": "info",
                "message": f"识别到ID列: {id_cols}，这些列可用于数据关联"
            })

        # 识别日期列（用于派生特征提示，同时避免被误判为“高基数分类列风险”）
        date_cols = []
        for col in self.df.columns:
            if self.df[col].dtype == object:
                date_info = self._detect_date_column(self.df[col], col)
                if date_info:
                    date_cols.append(col)
        if date_cols:
            recommendations.append({
                "type": "info",
                "message": f"日期列: {date_cols}，可派生专利年龄/时间差等连续变量"
            })
        
        # 识别高基数列（仅针对非数值列；数值列高唯一值是正常的，不应提示“分类变量”风险）
        high_card_cols = [
            col
            for col in self.df.columns
            if (self.df[col].dtype == object)
            and (col not in date_cols)
            and (self.df[col].nunique() > self.HIGH_CARDINALITY_THRESHOLD)
            and (self.df[col].nunique() < len(self.df))
        ]
        if high_card_cols:
            recommendations.append({
                "type": "warning",
                "message": f"高基数列: {high_card_cols}，不适合直接作为分类变量，需要预处理"
            })
        
        # 识别适合做类别变量的列（仅针对非数值列）
        category_cols = [
            col
            for col in self.df.columns
            if (self.df[col].dtype == object)
            and (2 <= self.df[col].nunique() <= self.CATEGORY_VAR_MAX_UNIQUE)
        ]
        if category_cols:
            recommendations.append({
                "type": "info",
                "message": f"适合做类别变量的列: {category_cols}"
            })
        
        # 识别数值列
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if self.df[col].nunique() < len(self.df)]
        if numeric_cols:
            recommendations.append({
                "type": "info",
                "message": f"数值列（可做连续变量）: {numeric_cols}"
            })
        
        return recommendations
    
    def _generate_sample_rows(self, n: int = 5) -> List[Dict]:
        """生成样例行（简化版，避免太长）"""
        sample_df = self.df.head(n)

        # 优先使用“关键列子集”
        key_cols = [c for c in self.KEY_SAMPLE_COLUMNS if c in sample_df.columns]
        if not key_cols:
            key_cols = sample_df.columns[:5].tolist()

        records = sample_df[key_cols].to_dict(orient='records')

        # 截断长文本，避免 Prompt 过长
        truncated = []
        for row in records:
            new_row = {}
            for k, v in row.items():
                if isinstance(v, str):
                    s = v.replace("\n", " ").replace("\r", " ")
                    if len(s) > 80:
                        s = s[:80] + "..."
                    new_row[k] = s
                else:
                    new_row[k] = v
            truncated.append(new_row)

        return truncated

    # ─── 新增：跨列统计 ─────────────────────────────────────

    def _compute_cross_column_stats(self) -> Dict[str, Any]:
        """
        计算跨列统计信号：相关系数、分组对比、时间趋势。
        全部基于 pandas 内置操作，无额外依赖。
        """
        result: Dict[str, Any] = {}

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()

        # 1. 数值列两两 Pearson 相关系数（仅保留 |r| > 0.1）
        if len(numeric_cols) >= 2:
            corr_matrix = self.df[numeric_cols].corr(method='pearson')
            pairs = []
            seen = set()
            for i, ca in enumerate(numeric_cols):
                for j, cb in enumerate(numeric_cols):
                    if i >= j:
                        continue
                    key = (ca, cb)
                    if key in seen:
                        continue
                    seen.add(key)
                    r = corr_matrix.loc[ca, cb]
                    if pd.notna(r) and abs(r) > 0.1:
                        pairs.append({"col_a": ca, "col_b": cb, "r": round(float(r), 3)})
            pairs.sort(key=lambda x: abs(x["r"]), reverse=True)
            result["correlation_pairs"] = pairs[:20]  # 最多保留 20 对

        # 2. 低基数分类列按组对比核心数值列的均值
        #    阈值比列信息检测更宽松（反正只取 Top 5 分组）
        GROUP_COMPARE_MAX_UNIQUE = 50
        category_cols = [
            col for col in self.df.columns
            if self.df[col].dtype == 'object'
            and 2 <= self.df[col].nunique() <= GROUP_COMPARE_MAX_UNIQUE
        ]
        # 核心数值列：排除 ID 类（唯一值 == 行数）
        core_numeric = [c for c in numeric_cols if self.df[c].nunique() < len(self.df)]

        group_comparisons = []
        for cat_col in category_cols[:5]:  # 最多取 5 个分类列
            top_cats = self.df[cat_col].value_counts().head(5).index.tolist()
            subset = self.df[self.df[cat_col].isin(top_cats)]
            for num_col in core_numeric[:3]:  # 每个分类列最多对比 3 个数值列
                grouped = subset.groupby(cat_col)[num_col].mean()
                values = {str(k): round(float(v), 2) for k, v in grouped.items() if pd.notna(v)}
                if len(values) >= 2:
                    group_comparisons.append({
                        "group_by": f"{cat_col} (Top {len(values)})",
                        "metric": num_col,
                        "values": values
                    })
        result["group_comparisons"] = group_comparisons[:15]

        # 3. 时间趋势：检测日期列，按年统计核心数值列均值
        time_trends = []
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                date_keywords = ['日', 'date', 'time', '时间']
                if any(kw in col.lower() for kw in date_keywords):
                    dates = pd.to_datetime(self.df[col], errors='coerce')
                    if dates.notna().sum() > len(self.df) * 0.5:
                        years = dates.dt.year
                        for num_col in core_numeric[:3]:
                            yearly = self.df.assign(_year=years).groupby('_year')[num_col].mean()
                            yearly = yearly.dropna().sort_index()
                            if len(yearly) >= 2:
                                by_year = {str(int(k)): round(float(v), 2) for k, v in yearly.items()}
                                time_trends.append({
                                    "metric": f"平均{num_col}",
                                    "time_column": col,
                                    "by_year": by_year
                                })
                        break  # 只用第一个日期列
        result["time_trends"] = time_trends

        return result

    # ─── 新增：摘要分层抽样 ──────────────────────────────────

    def _sample_abstracts_stratified(
        self, n_per_section: int = 5, max_total: int = 30
    ) -> Optional[Dict[str, List[str]]]:
        """
        按 IPC 部（首字符）分层抽样摘要。
        返回 {IPC部: [摘要列表]} 或 None（如果找不到摘要列或 IPC 列）。
        """
        # 自动检测摘要列
        abstract_col = None
        for col in self.df.columns:
            if '摘要' in col:
                abstract_col = col
                break
        if abstract_col is None:
            return None

        # 自动检测 IPC 列
        ipc_col = None
        for col in self.df.columns:
            if 'IPC' in col.upper() and '数量' not in col:
                ipc_col = col
                break

        abstracts = self.df[abstract_col].dropna().astype(str)
        # 过滤掉太短的（可能是 '-' 或空白）
        abstracts = abstracts[abstracts.str.len() > 20]

        if len(abstracts) == 0:
            return None

        if ipc_col is not None:
            # 提取 IPC 部（首字符）
            ipc_sections = self.df.loc[abstracts.index, ipc_col].astype(str).str[0]
            # 过滤有效部（A-H）
            valid_mask = ipc_sections.str.match(r'^[A-H]$', na=False)
            abstracts = abstracts[valid_mask]
            ipc_sections = ipc_sections[valid_mask]

            if len(abstracts) == 0:
                return None

            result = {}
            total = 0
            for section in sorted(ipc_sections.unique()):
                section_abstracts = abstracts[ipc_sections == section]
                n_sample = min(n_per_section, len(section_abstracts))
                sampled = section_abstracts.sample(n=n_sample, random_state=42)
                result[section] = [s[:300] for s in sampled.tolist()]
                total += n_sample
                if total >= max_total:
                    break
            return result
        else:
            # 没有 IPC 列，随机抽样
            n_sample = min(max_total, len(abstracts))
            sampled = abstracts.sample(n=n_sample, random_state=42)
            return {"ALL": [s[:300] for s in sampled.tolist()]}

    def get_abstracts_prompt_string(self) -> Optional[str]:
        """
        生成摘要抽样的 Prompt 文本。
        独立于 to_prompt_string()，仅在需要时调用。
        """
        preview = self.generate()
        sampled = preview.get("sampled_abstracts")
        if not sampled:
            return None

        lines = ["**领域摘要样本（分层抽样）：**", ""]
        for section, texts in sampled.items():
            if section == "ALL":
                lines.append(f"随机抽样 {len(texts)} 条：")
            else:
                lines.append(f"IPC部 {section}（{len(texts)} 条）：")
            for i, text in enumerate(texts, 1):
                lines.append(f"  {i}. {text}")
            lines.append("")
        return "\n".join(lines)
    
    def to_prompt_string(self) -> str:
        """生成可直接嵌入Prompt的字符串"""
        preview = self.generate()
        
        lines = []
        lines.append("📊 **数据预览**")
        lines.append(f"- 数据形状: {preview['basic']['shape']['rows']} 行 × {preview['basic']['shape']['columns']} 列")
        lines.append("")
        
        lines.append("**列信息：**")
        for col, info in preview['columns'].items():
            role = info.get('role', '未知')
            line = f"- `{col}` ({info['dtype']}): {role}"
            
            # 日期列
            if info.get('role') == '日期列':
                line += f" 📅 范围:{info.get('date_range', 'N/A')}"
                if 'derived_suggestion' in info:
                    line += f" → {info['derived_suggestion']}"
            # 分隔符列
            elif info.get('has_delimiter'):
                line += f" 📋 含分隔符'{info['delimiter']}', 平均{info['avg_items']}项"
                if 'derived_suggestion' in info:
                    line += f" → {info['derived_suggestion']}"
            # 警告
            elif 'warning' in info:
                line += f" ⚠️ {info['warning']}"
                if 'prefix_suggestion' in info:
                    line += f" 💡 {info['prefix_suggestion']}"
            # 数值列
            elif 'stats' in info:
                stats = info['stats']
                line += f" [均值:{stats['mean']}, 范围:{stats['min']}~{stats['max']}]"
            # 类别列
            elif 'categories' in info:
                cats = list(info['categories'].keys())[:5]
                line += f" 类别: {cats}"
            
            lines.append(line)
        
        lines.append("")
        lines.append("**建议：**")
        for rec in preview['recommendations']:
            icon = "ℹ️" if rec['type'] == 'info' else "⚠️"
            lines.append(f"{icon} {rec['message']}")
        
        # 添加派生变量建议
        lines.append("")
        lines.append("**可派生的变量：**")
        for col, info in preview['columns'].items():
            if info.get('derived_suggestion'):
                lines.append(f"- `{col}`: {info['derived_suggestion']}")

        # 关键列样例行（前5行）
        lines.append("")
        lines.append("**关键列样例（前5行）：**")
        lines.append(json.dumps(preview.get('sample_rows', []), ensure_ascii=False, indent=2))

        # ─── 跨列统计 ───────────────────────────────────────
        cross = preview.get('cross_column_stats', {})

        corr_pairs = cross.get('correlation_pairs', [])
        if corr_pairs:
            lines.append("")
            lines.append("**跨列相关系数（|r| > 0.1）：**")
            for p in corr_pairs[:10]:
                lines.append(f"- `{p['col_a']}` ↔ `{p['col_b']}`: r = {p['r']}")

        group_comps = cross.get('group_comparisons', [])
        if group_comps:
            lines.append("")
            lines.append("**分组对比（分类列 × 数值列均值）：**")
            for g in group_comps[:8]:
                vals_str = ", ".join(f"{k}: {v}" for k, v in g['values'].items())
                lines.append(f"- {g['group_by']} → {g['metric']}: {vals_str}")

        trends = cross.get('time_trends', [])
        if trends:
            lines.append("")
            lines.append("**时间趋势（按年均值）：**")
            for t in trends:
                vals_str = ", ".join(f"{k}: {v}" for k, v in t['by_year'].items())
                lines.append(f"- {t['metric']}（{t['time_column']}）: {vals_str}")

        return "\n".join(lines)


def generate_data_preview(file_path: str, sheet_name: str = None) -> Dict[str, Any]:
    """便捷函数：生成数据预览"""
    preview = DataPreview.from_file(file_path, sheet_name)
    return preview.generate()


def generate_preview_prompt(file_path: str, sheet_name: str = None) -> str:
    """便捷函数：生成可嵌入Prompt的预览字符串"""
    preview = DataPreview.from_file(file_path, sheet_name)
    return preview.to_prompt_string()
