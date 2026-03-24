# 当前可安全发表的主张

## 证据边界

- 唯一主证据源：`outputs/repeated_experiments_full/`
- 当前已完成：`6 模式 × 3 问题 × 5 重复 = 90` 组实验
- 当前可直接引用的统计文件：
  - `outputs/repeated_experiments_full/repeated_summary_report.md`
  - `outputs/repeated_experiments_full/repeated_llm_scores_summary_by_mode.csv`
  - `outputs/repeated_experiments_full/repeated_auto_metrics_summary_by_mode.csv`
  - `outputs/repeated_experiments_full/repeated_llm_scores_summary_by_question_mode.csv`
  - `outputs/repeated_experiments_full/repeated_auto_metrics_summary_by_question_mode.csv`

## 可保留主张

- `C_iterative` 在当前六模式重复实验中总体最优且更稳定，平均总分为 `23.87 ± 1.77`。
- `B_data_aware` 稳定优于 `A_template` 与 `D_baseline0`，说明数据感知是从“问题语义驱动”走向“数据证据驱动”的关键环节。
- `C_iterative` 相比 `B_data_aware` 在方法多样性、参数丰富度、任务总数和五维语义评分上均显著更强，说明两轮迭代决定性能上限。
- 在消融比较中，移除数据感知会明显降低针对性引用数和总分，说明数据感知的直接贡献最稳定。
- 知识图谱在平均意义上提供正向贡献，但收益具有任务依赖性：`Q1` 中 `F_ablate_kg > C_iterative`，而 `Q2/Q3` 中 `C_iterative > F_ablate_kg`。

## 禁止写法

- 不允许写成 `A_template` 稳定优于 `D_baseline0`。
- 不允许写成 `F_ablate_kg` 总体优于 `C_iterative`。
- 不允许写成“移除知识图谱更好”或“知识图谱约束悖论”作为主结论。
- 不允许再使用单次实验时期的“以广度换深度”或“知识图谱单独使用反而下降 27%”一类表述。

## 投稿前必补项

- 外部强基线
- 迁移数据集验证
- 正式统计推断
- 人工盲评
