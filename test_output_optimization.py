"""测试输出优化后的配置"""
import sys
sys.path.append('src')

from agents.strategist import Strategist
import json

# 创建 Strategist
strategist = Strategist()

# 生成 blueprint
blueprint = strategist.create_blueprint(
    user_request="分析专利数据的主题、异常和关键词",
    data_info={
        'main_data_path': 'data/clean_patents1_with_topics_filled.xlsx',
        'columns': ['序号', '公开(公告)号', '标题(译)(简体中文)', '摘要(译)(简体中文)']
    }
)

print("=" * 80)
print("输出优化验证")
print("=" * 80)

for step in blueprint['steps']:
    step_id = step['step_id']
    config = step['implementation_config']
    output_files = config.get('output_files', {})
    
    print(f"\n{'='*80}")
    print(f"Step {step_id}: {step['objective']}")
    print(f"{'='*80}")
    
    # 输出文件配置
    print(f"\n📁 输出配置:")
    print(f"  - 文件: {output_files.get('results_csv')}")
    print(f"  - 列名: {output_files.get('results_columns')}")
    
    # 计算预期列数
    results_cols = output_files.get('results_columns', [])
    expected_cols = 2 + len(results_cols)  # ID列(2) + 结果列
    print(f"  - 预期列数: {expected_cols} (2个ID列 + {len(results_cols)}个结果列)")
    
    # 输入数据配置
    input_source = config.get('input_data_source', {})
    print(f"\n📥 输入配置:")
    print(f"  - 主数据: {input_source.get('main_data')}")
    
    dependencies = input_source.get('dependencies', [])
    if dependencies:
        print(f"  - 依赖步骤: {len(dependencies)} 个")
        for dep in dependencies:
            print(f"    * {dep.get('file')}")
            print(f"      需要列: {dep.get('columns')}")
    else:
        print(f"  - 依赖步骤: 无（独立步骤）")

print("\n" + "=" * 80)
print("预期文件大小对比")
print("=" * 80)

# 估算文件大小
rows = 9275
print(f"\n数据行数: {rows}")

for step in blueprint['steps']:
    step_id = step['step_id']
    config = step['implementation_config']
    output_files = config.get('output_files', {})
    results_cols = output_files.get('results_columns', [])
    
    # 估算大小
    cols = 2 + len(results_cols)  # ID + 结果列
    avg_cell_size = 20  # 平均每个单元格字节数
    estimated_size_kb = (rows * cols * avg_cell_size) / 1024
    
    print(f"\nStep {step_id}:")
    print(f"  列数: {cols}")
    print(f"  预计大小: ~{estimated_size_kb:.1f} KB")

print("\n" + "=" * 80)
print("✅ 配置验证完成！")
print("=" * 80)
