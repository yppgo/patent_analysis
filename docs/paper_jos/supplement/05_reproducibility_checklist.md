# 可复验性检查清单

## 配置与代码

- [x] 已固定主证据池配置：`main_data_security`
- [x] 已固定外部机制基线配置：`G_react_single_agent / H_execution_feedback`
- [x] 已固定子领域稳定性配置：`transfer_iot_auto` 对应 `D / B / C / H`
- [x] 已新增真跨领域配置：`cross_domain_bugzilla`
- [x] 已给出 `Q1-Q5` 主问题模板与跨领域 `Q1-Q3` 适配模板
- [x] 已提供统一的数据集注册表、模式注册表与 bundle 定义
- [x] 已提供重复实验脚本、分批续跑脚本、统计脚本、表图导出脚本和补充材料打包脚本
- [x] 已提供人工盲评材料生成脚本与评分汇总脚本
- [x] 已收紧实验结果合法性校验，空蓝图/报错蓝图不会被计入有效证据

## 当前已物化的证据

- [x] 主证据池现有 `90` 组重复实验结果已落盘并可追溯
- [x] 外部机制基线现有 `30` 组结果已落盘并完成 strongest 选择
- [x] strongest 选择结果已写入 `outputs/jos_artifacts/stats/strongest_external_mechanism_baseline.json`
- [x] 盲评匿名材料包、匿名标签映射和评审模板已生成
- [x] `cross_domain_bugzilla` 数据集已通过官方 Mozilla Bugzilla API 抓取并物化

## 尚待补齐的真实证据

- [ ] `Q4/Q5` 尚未补跑，主证据池尚未扩展到正式目标 `150` 组
- [ ] `G/H` 的 `Q4/Q5` 尚未补跑，外部机制基线尚未扩展到正式目标 `50` 组
- [ ] `transfer_iot_auto` 子领域稳定性验证尚未形成可用正式结果
- [ ] `cross_domain_bugzilla` 尚未完成 `18` 组真跨领域实验
- [ ] 人工盲评真实评分尚未回收，当前只有模板和匿名材料

## 复现实验前的注意事项

- [x] thesis 主目录已冻结，新增实验和稿件产物仅写入期刊稿工作区与独立输出目录
- [x] `G/H` 在论文中按 `literature-inspired implementation` 描述，不宣称 strict reproduction
- [x] `transfer_iot_auto` 仅作为“子领域稳定性验证”配置保留，不再写成“跨领域迁移验证”
- [ ] 若 LLM API 连接仍不稳定，禁止直接将新批次结果并入正式证据池
- [x] 真跨领域数据源已到位并完成物化，可直接启动 `cross_domain_minimal` 批次
