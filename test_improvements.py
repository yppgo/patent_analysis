"""
快速测试改进效果
"""
import sys
sys.path.append('src')

print("=" * 80)
print("改进效果验证")
print("=" * 80)

# 1. 验证 Temperature 改进
print("\n1️⃣ 验证 Temperature 设置")
print("-" * 80)
try:
    from src.utils.llm_client import LLMClient
    client = LLMClient()
    print(f"✅ Temperature: {client.temperature}")
    if client.temperature >= 0.7:
        print("   ✅ 已提高到 0.7，有助于增加多样性")
    else:
        print(f"   ⚠️ 当前为 {client.temperature}，建议提高到 0.7")
except Exception as e:
    print(f"❌ 错误: {e}")

# 2. 验证 Strategist 改进
print("\n2️⃣ 验证 Strategist 配置")
print("-" * 80)
try:
    with open('src/agents/strategist.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含方法列表
    if '文本分析：LDA、NMF、BERTopic' in content:
        print("✅ 已添加方法选项提示")
    else:
        print("⚠️ 未找到方法选项提示")
    
    # 检查示例是否抽象化
    if '第一步的分析目标（根据用户需求设计）' in content:
        print("✅ 示例已抽象化")
    elif '对专利进行主题分类' in content:
        print("⚠️ 示例仍然过于具体")
    
    # 检查 format_notes
    if 'format_notes' in content and '只保存 ID 列' in content:
        print("✅ 已添加 format_notes 说明")
    else:
        print("⚠️ 未找到 format_notes")
        
except Exception as e:
    print(f"❌ 错误: {e}")

# 3. 验证 Coding Agent 改进
print("\n3️⃣ 验证 Coding Agent 提示词")
print("-" * 80)
try:
    with open('src/agents/coding_agent_v4_2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查开头强调
    if '🚨 最重要的要求' in content:
        print("✅ 已在开头强调重要要求")
    else:
        print("⚠️ 未找到开头强调")
    
    # 检查多列展开
    if 'needs_expansion' in content:
        print("✅ 已添加多列展开检测")
    else:
        print("⚠️ 未找到多列展开检测")
    
    # 检查依赖说明
    if '通过 ID 合并' in content or '通过 ID 列合并' in content:
        print("✅ 已添加依赖合并说明")
    else:
        print("⚠️ 未找到依赖合并说明")
    
    # 检查验证步骤
    if '步骤5：验证保存的文件' in content or '验证保存的文件' in content:
        print("✅ 已添加验证步骤")
    else:
        print("⚠️ 未找到验证步骤")
        
except Exception as e:
    print(f"❌ 错误: {e}")

# 4. 检查现有输出文件
print("\n4️⃣ 检查现有输出文件")
print("-" * 80)
import os
import pandas as pd

output_files = [
    'outputs/step_1_topic_results.csv',
    'outputs/step_2_outlier_results.csv',
    'outputs/step_3_keywords_results.csv'
]

for file_path in output_files:
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, nrows=1)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"\n📄 {os.path.basename(file_path)}")
            print(f"   大小: {file_size:.2f} MB")
            print(f"   列数: {len(df.columns)}")
            print(f"   列名: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")
            
            # 判断是否优化
            if file_size > 5:
                print(f"   ⚠️ 文件过大，可能包含冗余数据")
            elif file_size < 1:
                print(f"   ✅ 文件大小合理")
            
            # 检查是否包含原始数据列
            if '标题(译)(简体中文)' in df.columns or '摘要(译)(简体中文)' in df.columns:
                print(f"   ⚠️ 包含原始数据列（标题/摘要）")
            else:
                print(f"   ✅ 不包含原始数据列")
                
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    else:
        print(f"\n📄 {os.path.basename(file_path)}")
        print(f"   ⚠️ 文件不存在（需要重新运行系统）")

# 总结
print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)
print("\n💡 建议：")
print("1. 如果现有输出文件过大，请重新运行系统以应用优化")
print("2. 运行相同目标 3-5 次，观察方案多样性")
print("3. 检查生成的代码是否只保存必要的列")
print("\n📚 相关文档：")
print("- docs/OUTPUT_OPTIMIZATION.md")
print("- docs/DIVERSITY_IMPROVEMENT.md")
print("- docs/SESSION_SUMMARY.md")
