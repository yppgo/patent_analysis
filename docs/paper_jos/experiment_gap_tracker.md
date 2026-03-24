# 投稿前缺口追踪

## 已完成

- [x] 新建独立期刊稿目录，并冻结 thesis 主目录不再覆盖式修改
- [x] 固化主证据池现有 `90` 组内部重复实验及其统计、表格、图形导出脚本
- [x] 完成 `G_react_single_agent / H_execution_feedback` 的 `30` 组外部机制基线
- [x] 重新选择并写回 `H_execution_feedback` 作为 `strongest external mechanism baseline`
- [x] 完成期刊稿正文骨架、参考文献接入、英文摘要入口和可编译 PDF
- [x] 完成人工盲评材料包与评分汇总脚本，默认生成 `4` 位评审模板
- [x] 完成 `Q4/Q5`、`cross_domain_bugzilla`、`subdomain_stability_full` 等配置与脚本改造
- [x] 收紧重复实验校验逻辑，空蓝图/报错蓝图不再计为有效完成

## 进行中

- [ ] 主证据池从 `3` 问题扩展到 `5` 问题：补跑 `6 模式 × Q4/Q5 × 5 重复 = 60` 组
- [ ] 外部机制基线扩展到 `5` 问题：补跑 `G/H × Q4/Q5 × 5 重复 = 20` 组
- [ ] 运行 `cross_domain_bugzilla` 的真跨领域小验证：`D/C × 3 问题 × 3 重复 = 18` 组
- [ ] 回收至少 `3` 位真实评审者的匿名盲评结果

## 当前阻塞项

- [ ] 主问题扩展尚未形成新的 `150` 组主证据；当前正文主统计仍只能诚实引用冻结的 `90` 组
- [ ] 外部机制基线仍只有 `Q1-Q3`，尚未达到正式目标 `50` 组
- [ ] 当前 API 连接不稳定；若直接重跑，容易产出 `Connection error` 导致的空任务蓝图
- [ ] 人工盲评目前只有模板与匿名材料，尚未回收真实评分

## 新近完成

- [x] 已通过 Mozilla 官方 Bugzilla API 抓取 `Core / Firefox / Toolkit` 各 `150` 条样本，共 `450` 条原始缺陷记录
- [x] 已生成原始 CSV：`outputs/jos_artifacts/datasets/mozilla_bugzilla_recent.csv`
- [x] 已物化标准化跨领域数据集：`outputs/jos_artifacts/datasets/cross_domain_bugzilla.xlsx`

## 降级为可选

- [ ] `transfer_iot_auto` 子领域稳定性验证暂不作为当前投稿版 P0 证据
- [ ] 若后续时间允许，可将 `transfer_iot_auto` 作为补充材料中的“相邻技术子领域稳定性”附加验证

## 口径要求

- `G/H` 统一称为 `external mechanism baselines`
- `H` 统一称为 `strongest external mechanism baseline`
- `transfer_iot_auto` 统一称为“子领域稳定性验证”，不得再写成“跨领域迁移验证”
- 当前投稿主线优先级为：`external_q45 -> main_q45 -> cross_domain_bugzilla -> human review`
- 在新增证据真正落地前，本目录对应稿件仍属于“增强版投稿准备稿”，不是最终投稿版
