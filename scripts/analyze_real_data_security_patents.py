"""
使用真实数据进行技术空白识别分析
数据来源: data/clean_patents1_with_topics_filled.xlsx (clear sheet)
方法: Angle-Based Outlier Detection (ABOD)
"""

import pandas as pd
import numpy as np
from pyod.models.abod import ABOD
from sentence_transformers import SentenceTransformer
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

def load_real_patent_data(file_path: str = 'data/clean_patents1_with_topics_filled.xlsx', 
                          sheet_name: str = 'clear',
                          sample_size: int = 500) -> pd.DataFrame:
    """
    加载真实的专利数据
    
    参数:
        file_path: Excel 文件路径
        sheet_name: Sheet 名称
        sample_size: 采样数量（为了加快处理速度）
    """
    print(f"\n📥 加载真实专利数据...")
    print(f"  文件: {file_path}")
    print(f"  Sheet: {sheet_name}")
    
    # 读取数据
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f"  ✓ 原始数据: {len(df)} 条专利")
    
    # 选择需要的列
    columns_needed = ['标题(译)(简体中文)', '摘要(译)(简体中文)', 'IPC主分类号', 'Topic_Label']
    df = df[columns_needed].copy()
    
    # 重命名列以便处理
    df.columns = ['标题', '摘要', 'IPC', '主题标签']
    
    # 删除缺失值
    df = df.dropna(subset=['标题', '摘要'])
    print(f"  ✓ 清洗后: {len(df)} 条专利")
    
    # 如果数据太多，随机采样
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        print(f"  ✓ 随机采样: {sample_size} 条专利")
    
    return df


def detect_technology_gaps_real(patents_df: pd.DataFrame, 
                                 contamination: float = 0.1) -> Dict:
    """
    使用 ABOD 检测技术空白
    
    参数:
        patents_df: 专利数据
        contamination: 离群值比例
    """
    print("\n" + "="*70)
    print("🔍 开始技术空白识别分析")
    print("="*70)
    
    try:
        # 步骤 1: 加载模型
        print("\n📥 步骤 1/4: 加载 Sentence Transformer 模型...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("  ✓ 模型加载成功: all-MiniLM-L6-v2")
        
        # 步骤 2: 文本编码
        print("\n🔤 步骤 2/4: 将专利文本编码为向量...")
        # 合并标题和摘要
        patents_df['combined_text'] = patents_df['标题'] + ' ' + patents_df['摘要']
        
        # 编码
        embeddings = model.encode(
            list(patents_df['combined_text']), 
            show_progress_bar=True,
            batch_size=32
        )
        print(f"  ✓ 编码完成: {embeddings.shape[0]} 个专利 -> {embeddings.shape[1]} 维向量")
        
        # 步骤 3: 离群值检测
        print("\n🎯 步骤 3/4: 执行 Angle-Based Outlier Detection...")
        print(f"  参数: contamination={contamination}, n_neighbors=5, method='fast'")
        
        detector = ABOD(contamination=contamination, n_neighbors=5, method='fast')
        outlier_labels = detector.fit_predict(embeddings)
        outlier_scores = detector.decision_scores_
        
        n_outliers = sum(outlier_labels == 1)
        print(f"  ✓ 检测完成: 发现 {n_outliers} 个潜在技术空白 (占比 {n_outliers/len(patents_df)*100:.1f}%)")
        
        # 步骤 4: 整理结果
        print("\n📊 步骤 4/4: 整理分析结果...")
        patents_df['is_outlier'] = outlier_labels
        patents_df['outlier_score'] = outlier_scores
        
        # 提取离群专利
        gap_patents = patents_df[patents_df['is_outlier'] == 1].copy()
        gap_patents = gap_patents.sort_values('outlier_score', ascending=False)
        
        # 提取主流专利
        mainstream_patents = patents_df[patents_df['is_outlier'] == 0].copy()
        
        print(f"  ✓ 识别出 {len(gap_patents)} 个潜在技术空白")
        print(f"  ✓ 识别出 {len(mainstream_patents)} 个主流技术")
        
        return {
            'gap_patents': gap_patents,
            'mainstream_patents': mainstream_patents,
            'statistics': {
                'total_patents': len(patents_df),
                'gap_count': len(gap_patents),
                'mainstream_count': len(mainstream_patents),
                'gap_ratio': len(gap_patents) / len(patents_df)
            }
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def display_results(results: Dict):
    """展示分析结果"""
    if 'error' in results:
        print(f"\n❌ 分析失败: {results['error']}")
        return
    
    print("\n" + "="*70)
    print("📈 分析结果汇总")
    print("="*70)
    
    stats = results['statistics']
    print(f"\n总专利数: {stats['total_patents']}")
    print(f"主流技术: {stats['mainstream_count']} ({stats['mainstream_count']/stats['total_patents']*100:.1f}%)")
    print(f"技术空白: {stats['gap_count']} ({stats['gap_ratio']*100:.1f}%)")
    
    # 显示技术空白
    print("\n" + "="*70)
    print("🌟 潜在技术空白（创新机会）- Top 10")
    print("="*70)
    
    gap_patents = results['gap_patents']
    for i, (idx, patent) in enumerate(gap_patents.head(10).iterrows(), 1):
        print(f"\n【空白 {i}】离群分数: {patent['outlier_score']:.4f}")
        print(f"  标题: {patent['标题']}")
        print(f"  IPC: {patent['IPC']}")
        if pd.notna(patent.get('主题标签')):
            print(f"  主题: {patent['主题标签']}")
        print(f"  摘要: {patent['摘要'][:100]}...")
    
    # 显示主流技术
    print("\n" + "="*70)
    print("📚 主流技术示例（前5个）")
    print("="*70)
    
    mainstream_patents = results['mainstream_patents']
    for i, (idx, patent) in enumerate(mainstream_patents.head(5).iterrows(), 1):
        print(f"\n【主流 {i}】")
        print(f"  标题: {patent['标题']}")
        print(f"  IPC: {patent['IPC']}")
        if pd.notna(patent.get('主题标签')):
            print(f"  主题: {patent['主题标签']}")
    
    # 按主题统计
    if '主题标签' in gap_patents.columns:
        print("\n" + "="*70)
        print("📊 技术空白的主题分布")
        print("="*70)
        topic_dist = gap_patents['主题标签'].value_counts()
        for topic, count in topic_dist.head(10).items():
            if pd.notna(topic):
                print(f"  {topic}: {count} 个")
    
    # 保存结果
    print("\n" + "="*70)
    print("💾 保存结果...")
    print("="*70)
    
    # 保存技术空白到 Excel
    output_file = 'data/technology_gaps_analysis_result.xlsx'
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        gap_patents[['标题', '摘要', 'IPC', '主题标签', 'outlier_score']].to_excel(
            writer, sheet_name='技术空白', index=False
        )
        mainstream_patents[['标题', '摘要', 'IPC', '主题标签']].head(100).to_excel(
            writer, sheet_name='主流技术示例', index=False
        )
    
    print(f"  ✓ 结果已保存到: {output_file}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Patent-DeepScientist - 真实数据技术空白识别")
    print("   方法: Angle-Based Outlier Detection (ABOD)")
    print("   数据: 数据安全领域专利 (clear sheet)")
    print("="*70)
    
    # 加载真实数据
    data = load_real_patent_data(sample_size=500)
    
    print(f"\n📊 数据概览:")
    print(f"  专利数量: {len(data)}")
    print(f"  IPC 分类数: {data['IPC'].nunique()}")
    if '主题标签' in data.columns:
        print(f"  主题数量: {data['主题标签'].nunique()}")
    
    # 执行分析
    results = detect_technology_gaps_real(data, contamination=0.1)
    
    # 展示结果
    display_results(results)
    
    print("\n" + "="*70)
    print("✅ 分析完成")
    print("="*70)
    print("\n💡 解读:")
    print("  - 离群分数越高，表示该专利在语义空间中越偏离主流")
    print("  - 这些离群专利可能代表新兴的技术方向或未被充分探索的领域")
    print("  - 建议进一步调研这些技术空白，评估其商业价值和可行性")
    print()
