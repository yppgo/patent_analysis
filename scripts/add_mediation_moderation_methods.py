#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加中介分析和调节分析的默认方法
"""

import json
from datetime import datetime

# 中介和调节分析的默认方法
DEFAULT_ANALYSIS_METHODS = [
    {
        "method_name": "Baron & Kenny三步法（中介分析）",
        "method_type": "mediation",
        "usage_frequency": 0,
        "usage_papers": [],
        "formula": "Step1: Y = c*X + e1; Step2: M = a*X + e2; Step3: Y = c'*X + b*M + e3",
        "formula_explanation": "c为总效应，a为X→M效应，b为M→Y效应，c'为直接效应，间接效应=a*b",
        "applicable_scenarios": [
            "验证中介假设（A→M→B）",
            "分解总效应为直接效应和间接效应",
            "检验中介变量的作用机制"
        ],
        "assumptions": [
            "线性关系",
            "无混淆变量",
            "中介变量在因果链中间",
            "残差正态分布"
        ],
        "interpretation_guide": {
            "完全中介": "c'不显著且a*b显著，X通过M完全影响Y",
            "部分中介": "c'显著且a*b显著，X既直接影响Y也通过M影响Y",
            "无中介": "a*b不显著，M不起中介作用",
            "显著性检验": "使用Sobel Test检验间接效应a*b的显著性"
        },
        "implementation_steps": [
            "1. 回归分析：Y ~ X，检验总效应c是否显著",
            "2. 回归分析：M ~ X，检验路径a是否显著",
            "3. 回归分析：Y ~ X + M，检验路径b和c'是否显著",
            "4. 计算间接效应：indirect_effect = a * b",
            "5. Sobel Test：检验间接效应显著性"
        ],
        "python_example": """
# Baron & Kenny 中介分析示例
import statsmodels.api as sm
import numpy as np

# Step 1: 总效应 Y ~ X
X_with_const = sm.add_constant(X)
model1 = sm.OLS(Y, X_with_const).fit()
c = model1.params[1]  # 总效应
print(f"总效应 c = {c:.4f}, p = {model1.pvalues[1]:.4f}")

# Step 2: X → M
model2 = sm.OLS(M, X_with_const).fit()
a = model2.params[1]  # X对M的效应
print(f"路径 a = {a:.4f}, p = {model2.pvalues[1]:.4f}")

# Step 3: Y ~ X + M
XM = np.column_stack([X, M])
XM_with_const = sm.add_constant(XM)
model3 = sm.OLS(Y, XM_with_const).fit()
c_prime = model3.params[1]  # 直接效应
b = model3.params[2]  # M对Y的效应
print(f"直接效应 c' = {c_prime:.4f}, p = {model3.pvalues[1]:.4f}")
print(f"路径 b = {b:.4f}, p = {model3.pvalues[2]:.4f}")

# 间接效应
indirect_effect = a * b
print(f"间接效应 = {indirect_effect:.4f}")

# Sobel Test
se_indirect = np.sqrt(b**2 * model2.bse[1]**2 + a**2 * model3.bse[2]**2)
z_score = indirect_effect / se_indirect
p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
print(f"Sobel Test: z = {z_score:.4f}, p = {p_value:.4f}")
""",
        "notes": "⚠️ 默认方案：基于Baron & Kenny (1986)的经典方法"
    },
    
    {
        "method_name": "Bootstrap中介分析",
        "method_type": "mediation",
        "usage_frequency": 0,
        "usage_papers": [],
        "formula": "Indirect_Effect = a * b, 使用Bootstrap估计置信区间",
        "formula_explanation": "通过重采样估计间接效应的置信区间，不依赖正态分布假设",
        "applicable_scenarios": [
            "样本量较小时的中介分析",
            "不满足正态分布假设",
            "需要更稳健的显著性检验"
        ],
        "assumptions": [
            "线性关系",
            "无混淆变量",
            "样本独立同分布"
        ],
        "interpretation_guide": {
            "显著性判断": "如果95%置信区间不包含0，则间接效应显著",
            "效应量": "间接效应占总效应的比例 = (a*b) / c"
        },
        "implementation_steps": [
            "1. 估计路径系数 a 和 b",
            "2. Bootstrap重采样（通常1000-5000次）",
            "3. 每次重采样计算间接效应 a*b",
            "4. 构建间接效应的95%置信区间",
            "5. 判断显著性"
        ],
        "python_example": """
# Bootstrap 中介分析示例
from scipy import stats
import numpy as np

def bootstrap_mediation(X, M, Y, n_bootstrap=5000):
    n = len(X)
    indirect_effects = []
    
    for _ in range(n_bootstrap):
        # 重采样
        indices = np.random.choice(n, n, replace=True)
        X_boot = X[indices]
        M_boot = M[indices]
        Y_boot = Y[indices]
        
        # 估计路径系数
        a = np.corrcoef(X_boot, M_boot)[0, 1] * (np.std(M_boot) / np.std(X_boot))
        b = np.corrcoef(M_boot, Y_boot)[0, 1] * (np.std(Y_boot) / np.std(M_boot))
        
        indirect_effects.append(a * b)
    
    # 计算置信区间
    ci_lower = np.percentile(indirect_effects, 2.5)
    ci_upper = np.percentile(indirect_effects, 97.5)
    
    return np.mean(indirect_effects), ci_lower, ci_upper

indirect, ci_low, ci_high = bootstrap_mediation(X, M, Y)
print(f"间接效应 = {indirect:.4f}, 95% CI = [{ci_low:.4f}, {ci_high:.4f}]")
if ci_low > 0 or ci_high < 0:
    print("间接效应显著")
""",
        "notes": "⚠️ 默认方案：基于Preacher & Hayes (2008)的Bootstrap方法"
    },
    
    {
        "method_name": "交互项回归（调节分析）",
        "method_type": "moderation",
        "usage_frequency": 0,
        "usage_papers": [],
        "formula": "Y = b0 + b1*X + b2*Z + b3*(X*Z) + e",
        "formula_explanation": "b3为交互效应系数，Z为调节变量，X*Z为交互项",
        "applicable_scenarios": [
            "验证调节假设（Z调节X→Y）",
            "检验X对Y的效应是否随Z变化",
            "分析边界条件"
        ],
        "assumptions": [
            "线性关系",
            "交互项与主效应独立",
            "残差正态分布",
            "同方差性"
        ],
        "interpretation_guide": {
            "交互效应显著": "b3显著，说明Z调节X→Y的关系",
            "正向调节": "b3>0，Z越大X对Y的正效应越强",
            "负向调节": "b3<0，Z越大X对Y的正效应越弱",
            "简单斜率分析": "在Z的不同水平（均值±1SD）下分别检验X→Y的效应"
        },
        "implementation_steps": [
            "1. 中心化：X和Z减去各自均值（避免多重共线性）",
            "2. 创建交互项：X_centered * Z_centered",
            "3. 回归分析：Y ~ X_centered + Z_centered + X*Z",
            "4. 检验交互项系数b3的显著性",
            "5. 简单斜率分析：在Z的高/中/低水平下分别检验X的效应",
            "6. 绘制交互图"
        ],
        "python_example": """
# 调节分析示例
import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt

# 中心化
X_centered = X - X.mean()
Z_centered = Z - Z.mean()

# 创建交互项
interaction = X_centered * Z_centered

# 回归分析
predictors = np.column_stack([X_centered, Z_centered, interaction])
predictors_with_const = sm.add_constant(predictors)
model = sm.OLS(Y, predictors_with_const).fit()

b1 = model.params[1]  # X的主效应
b2 = model.params[2]  # Z的主效应
b3 = model.params[3]  # 交互效应
print(f"交互效应 b3 = {b3:.4f}, p = {model.pvalues[3]:.4f}")

# 简单斜率分析
Z_low = Z.mean() - Z.std()
Z_high = Z.mean() + Z.std()

slope_low = b1 + b3 * (Z_low - Z.mean())
slope_high = b1 + b3 * (Z_high - Z.mean())

print(f"Z低水平时，X的效应 = {slope_low:.4f}")
print(f"Z高水平时，X的效应 = {slope_high:.4f}")

# 绘制交互图
X_range = np.linspace(X.min(), X.max(), 100)
Y_low = model.params[0] + slope_low * (X_range - X.mean())
Y_high = model.params[0] + slope_high * (X_range - X.mean())

plt.plot(X_range, Y_low, label=f'Z = {Z_low:.2f} (低)')
plt.plot(X_range, Y_high, label=f'Z = {Z_high:.2f} (高)')
plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.title('调节效应图')
plt.show()
""",
        "notes": "⚠️ 默认方案：基于Aiken & West (1991)的经典方法"
    },
    
    {
        "method_name": "分组回归（调节分析）",
        "method_type": "moderation",
        "usage_frequency": 0,
        "usage_papers": [],
        "formula": "分别在Z的不同水平下回归：Y = b0 + b1*X + e",
        "formula_explanation": "将样本按Z分组，分别估计X→Y的效应，比较组间差异",
        "applicable_scenarios": [
            "调节变量为类别变量",
            "需要直观比较不同条件下的效应",
            "交互项回归的补充分析"
        ],
        "assumptions": [
            "线性关系",
            "各组样本量足够",
            "组间方差齐性"
        ],
        "interpretation_guide": {
            "效应差异显著": "不同组的b1系数显著不同，说明存在调节效应",
            "Chow Test": "检验组间回归系数是否显著不同"
        },
        "implementation_steps": [
            "1. 将Z分组（如按中位数或三分位数）",
            "2. 在每组中分别回归：Y ~ X",
            "3. 比较各组的回归系数b1",
            "4. Chow Test检验组间差异显著性"
        ],
        "python_example": """
# 分组回归示例
import statsmodels.api as sm
import numpy as np

# 按Z的中位数分组
Z_median = np.median(Z)
group_low = Z <= Z_median
group_high = Z > Z_median

# 低Z组回归
X_low = sm.add_constant(X[group_low])
model_low = sm.OLS(Y[group_low], X_low).fit()
b1_low = model_low.params[1]
print(f"低Z组：b1 = {b1_low:.4f}, p = {model_low.pvalues[1]:.4f}")

# 高Z组回归
X_high = sm.add_constant(X[group_high])
model_high = sm.OLS(Y[group_high], X_high).fit()
b1_high = model_high.params[1]
print(f"高Z组：b1 = {b1_high:.4f}, p = {model_high.pvalues[1]:.4f}")

# 比较
print(f"效应差异 = {b1_high - b1_low:.4f}")

# Chow Test（简化版）
diff = abs(b1_high - b1_low)
se_diff = np.sqrt(model_low.bse[1]**2 + model_high.bse[1]**2)
z_score = diff / se_diff
print(f"组间差异检验：z = {z_score:.4f}")
""",
        "notes": "⚠️ 简化方案：适用于类别调节变量或探索性分析"
    }
]


def add_mediation_moderation_methods():
    """添加中介和调节分析方法"""
    
    print("=" * 80)
    print("添加中介和调节分析方法")
    print("=" * 80)
    
    # 加载方法知识库
    kb_file = "sandbox/static/data/method_knowledge_base.json"
    with open(kb_file, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    print(f"\n加载方法知识库: {kb_file}")
    print(f"当前分析方法数: {kb['meta']['total_analysis_methods']}")
    
    # 添加方法
    added_count = 0
    for method in DEFAULT_ANALYSIS_METHODS:
        # 检查是否已存在
        exists = any(m['method_name'] == method['method_name'] 
                    for m in kb['statistical_analysis_methods'])
        
        if not exists:
            kb['statistical_analysis_methods'].append(method)
            added_count += 1
            print(f"  ✓ 添加 {method['method_name']} ({method['method_type']})")
        else:
            print(f"  ⚠ 跳过 {method['method_name']}: 已存在")
    
    # 更新元数据
    kb['meta']['total_analysis_methods'] = len(kb['statistical_analysis_methods'])
    kb['meta']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    if 'mediation_moderation_added' not in kb['meta']:
        kb['meta']['mediation_moderation_added'] = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'methods': [m['method_name'] for m in DEFAULT_ANALYSIS_METHODS],
            'note': '这些方法未从文献提取，基于统计学标准方法补充'
        }
    
    # 保存
    with open(kb_file, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 已添加 {added_count} 个分析方法")
    print(f"✓ 更新后分析方法总数: {kb['meta']['total_analysis_methods']}")
    print(f"✓ 已保存到: {kb_file}")
    
    # 统计方法类型
    method_types = {}
    for method in kb['statistical_analysis_methods']:
        mtype = method.get('method_type', 'unknown')
        method_types[mtype] = method_types.get(mtype, 0) + 1
    
    print(f"\n方法类型分布:")
    for mtype, count in sorted(method_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {mtype}: {count}个")
    
    print("\n" + "=" * 80)
    print("添加完成！")
    print("=" * 80)
    
    return added_count


if __name__ == "__main__":
    count = add_mediation_moderation_methods()
    print(f"\n总结: 成功添加 {count} 个中介/调节分析方法")
