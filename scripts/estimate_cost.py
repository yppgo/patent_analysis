#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估算批量处理的时间和成本
"""

# Claude Sonnet 4 定价（通过聚合AI）
INPUT_PRICE = 3 / 1_000_000  # ¥3/百万tokens
OUTPUT_PRICE = 15 / 1_000_000  # ¥15/百万tokens

# 单篇论文估算
AVG_PDF_SIZE_MB = 8  # 平均PDF大小
AVG_PDF_PAGES = 15  # 平均页数
AVG_INPUT_TOKENS = 50_000  # 输入tokens（PDF + prompt）
AVG_OUTPUT_TOKENS = 2_000  # 输出tokens（JSON结果）
AVG_TIME_SECONDS = 15  # 平均处理时间

# 批量处理
TOTAL_PAPERS = 500

print("=" * 60)
print("批量处理成本和时间估算")
print("=" * 60)

# 时间估算
print("\n【时间估算】")
print(f"单篇处理时间: {AVG_TIME_SECONDS}秒")
print(f"总论文数: {TOTAL_PAPERS}篇")

# 串行处理
serial_time = TOTAL_PAPERS * AVG_TIME_SECONDS
print(f"\n串行处理:")
print(f"  总时间: {serial_time}秒 = {serial_time/60:.1f}分钟 = {serial_time/3600:.1f}小时")

# 并行处理（5线程）
parallel_time_5 = serial_time / 5
print(f"\n并行处理 (5线程):")
print(f"  总时间: {parallel_time_5}秒 = {parallel_time_5/60:.1f}分钟 = {parallel_time_5/3600:.1f}小时")

# 并行处理（10线程）
parallel_time_10 = serial_time / 10
print(f"\n并行处理 (10线程):")
print(f"  总时间: {parallel_time_10}秒 = {parallel_time_10/60:.1f}分钟 = {parallel_time_10/3600:.1f}小时")

# 成本估算
print("\n" + "=" * 60)
print("【成本估算】")
print("=" * 60)

total_input_tokens = TOTAL_PAPERS * AVG_INPUT_TOKENS
total_output_tokens = TOTAL_PAPERS * AVG_OUTPUT_TOKENS

input_cost = total_input_tokens * INPUT_PRICE
output_cost = total_output_tokens * OUTPUT_PRICE
total_cost = input_cost + output_cost

print(f"\n输入tokens: {total_input_tokens:,} ({total_input_tokens/1_000_000:.1f}M)")
print(f"输出tokens: {total_output_tokens:,} ({total_output_tokens/1_000_000:.1f}M)")
print(f"\n输入成本: ¥{input_cost:.2f}")
print(f"输出成本: ¥{output_cost:.2f}")
print(f"总成本: ¥{total_cost:.2f}")

# 不同规模对比
print("\n" + "=" * 60)
print("【不同规模对比】")
print("=" * 60)

for n in [50, 100, 200, 500, 1000]:
    cost = n * (AVG_INPUT_TOKENS * INPUT_PRICE + AVG_OUTPUT_TOKENS * OUTPUT_PRICE)
    time_serial = n * AVG_TIME_SECONDS / 60
    time_parallel = time_serial / 5
    print(f"\n{n}篇论文:")
    print(f"  成本: ¥{cost:.2f}")
    print(f"  时间(串行): {time_serial:.1f}分钟")
    print(f"  时间(并行5线程): {time_parallel:.1f}分钟")

print("\n" + "=" * 60)
print("建议")
print("=" * 60)
print("""
1. 先处理50-100篇测试，验证质量
2. 使用并行处理（5-10线程）加速
3. 分批处理，避免一次性消耗过多
4. 设置错误重试机制
5. 定期保存中间结果
""")
