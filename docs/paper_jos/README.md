# 《软件学报》独立期刊稿工作区

这个目录专门用于维护《软件学报》常规稿，不覆盖学位论文。

## 目录说明

- `main.tex`：期刊稿主文件
- `sections/`：正文分节
- `generated/`：脚本生成的表格和证据快照
- `figures/`：期刊稿专用图
- `supplement/`：投稿前需要补齐的附属材料模板
- `FROZEN_CLAIMS.md`：当前 90 组重复实验可安全使用的主张
- `experiment_gap_tracker.md`：投稿前必须补完的缺口

## 推荐工作流

```powershell
py -3 scripts/jos/run_significance_tests.py
py -3 scripts/jos/export_jos_tables.py
py -3 scripts/jos/plot_jos_figures.py
py -3 scripts/jos/package_supplement.py
```

如本机已安装 XeLaTeX，可在本目录下执行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

说明：
- 如果本地还没有 `jos.cls`，当前主文件会自动回退到 `ctexart` 骨架继续编译。
- 一旦将《软件学报》官方类文件放入本目录，`main.tex` 会优先切换到该模板。

## 外部机制基线、子领域稳定性与跨领域验证

先物化子领域稳定性数据集：

```powershell
py -3 scripts/jos/materialize_transfer_dataset.py --dataset transfer_iot_auto --force
```

如已获得 Bugzilla 原始导出，可物化跨领域数据集：

```powershell
py -3 scripts/jos/materialize_bugzilla_dataset.py `
  --source-file path/to/bugzilla_export.csv `
  --force
```

查看当前实验配置：

```powershell
py -3 tests/repeat_pipeline_experiments.py --list-configs
```

运行主数据集上的外部基线组：

```powershell
py -3 tests/repeat_pipeline_experiments.py `
  --dataset main_data_security `
  --modes G_react_single_agent,H_execution_feedback `
  --repeats 5 `
  --output-dir outputs/repeated_experiments_external_main
```

完成后汇总外部基线：

```powershell
py -3 tests/summarize_repeated_experiments.py `
  --output-dir outputs/repeated_experiments_external_main `
  --expected-repeats 5 `
  --question-indexes 1,2,3,4,5 `
  --modes G_react_single_agent,H_execution_feedback `
  --with-llm
py -3 scripts/jos/run_significance_tests.py `
  --input-dir outputs/repeated_experiments_external_main `
  --supplemental-dir outputs/repeated_experiments_full `
  --mode-order C_iterative,G_react_single_agent,H_execution_feedback `
  --pairwise C_iterative:G_react_single_agent,C_iterative:H_execution_feedback `
  --output-prefix external_main
py -3 scripts/jos/select_strongest_external.py
```

如果希望在外部机制基线跑完后自动继续子领域稳定性验证、导出表图并生成盲评包，可直接启动：

```powershell
py -3 scripts/jos/auto_continue_submission.py
```

如果希望按当前增强版投稿路线顺序后台执行 `external_q45 -> main_q45` 两段长批次，可直接启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/jos/run_enhanced_submission_batches.ps1
```

日志默认写入：
- `outputs/jos_artifacts/run_logs/*.out.log`
- `outputs/jos_artifacts/run_logs/*.err.log`

子领域稳定性验证建议使用分批短任务入口，以便自动重跑失败样本：

```powershell
py -3 scripts/jos/run_repeated_batches.py `
  --dataset transfer_iot_auto `
  --modes D_baseline0,B_data_aware,C_iterative,H_execution_feedback `
  --question-indexes 1,2,3,4,5 `
  --repeats 3 `
  --output-dir outputs/repeated_experiments_transfer_iot_auto
```

跨领域 Bugzilla 小验证入口：

```powershell
py -3 scripts/jos/run_repeated_batches.py `
  --dataset cross_domain_bugzilla `
  --modes D_baseline0,C_iterative `
  --question-indexes 1,2,3 `
  --repeats 3 `
  --output-dir outputs/repeated_experiments_cross_domain_bugzilla
```

完成人工盲评材料导出：

```powershell
py -3 scripts/jos/prepare_human_review.py --run-index 1 --reviewer-count 4
py -3 scripts/jos/summarize_human_review.py
```

## 当前状态

- 已冻结主证据源：`outputs/repeated_experiments_full/`
- 已搭建独立期刊稿目录
- 已接入本地参考文献库与英文摘要骨架
- 已生成统计、表格、图形脚本
- 已建立投稿材料模板
- 外部机制基线、子领域稳定性与跨领域验证配置已接入
- 已补充人工盲评材料包与汇总脚本
- 已支持跨证据池统计：可用主证据中的 `C_iterative` 与外部证据中的 `G/H` 做联合统计与表图导出
- 已收紧重复实验合法性校验，空蓝图或报错蓝图不会再混入有效证据
- 当前已完成的外部机制基线为 30 组，`H_execution_feedback` 已锁定为当前 strongest external mechanism baseline
- 当前优先级为：主证据池 5 问题扩展、外部机制基线 5 问题扩展、跨领域 Bugzilla 18 组验证、人工盲评真实评分
- `transfer_iot_auto` 当前降级为可选补充验证，不再作为投稿版主线证据
