"""测试 Step 3 修复后的配置"""
import sys
sys.path.append('src')

from agents.strategist import Strategist

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

# 查看 Step 3 的配置
step_3 = blueprint['steps'][2]  # Step 3 是第3个步骤（索引2）
print("=" * 60)
print("Step 3 配置：")
print("=" * 60)
import json
print(json.dumps(step_3, indent=2, ensure_ascii=False))

# 重点检查
print("\n" + "=" * 60)
print("重点检查：")
print("=" * 60)
config = step_3['implementation_config']
print(f"✓ results_columns: {config['output_files']['results_columns']}")
print(f"✓ parameters: {config['parameters']}")
print(f"✓ notes: {step_3['notes']}")
