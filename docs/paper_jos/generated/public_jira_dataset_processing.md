# The Public Jira Dataset 处理说明

## 当前可做的事

当前工作区已新增独立脚本：

- `scripts/materialize_public_jira_dataset.py`
- `scripts/export_public_jira_project_sample.py`

它负责把 Jira issue 导出整理成和当前跨领域实验兼容的标准化 `xlsx`，输出字段为：

- `title`
- `description`
- `severity`
- `component`
- `product/project`
- `created_at`
- `resolved_at`
- `reporter`
- `assignee`
- `status`
- `priority`
- `comments_count`

## 重要限制

`The Public Jira Dataset` 的官方包是 MongoDB archive，这台机器当前没有：

- `mongorestore`
- `mongoexport`
- `mongosh`

所以这里的脚本目前吃的是“已经导出的 issue 级数据”，支持：

- `json`
- `jsonl`
- `ndjson`
- `csv`
- `xlsx`

## 推荐处理流程

1. 先把 TPJD 原始包导出成 issue 级 `json/jsonl/csv`
2. 再运行下面的标准化脚本

如果你已经把官方 MongoDB archive restore 到本地库，也可以直接跳过“手工导出 issue”这一步，使用：

- `scripts/export_public_jira_project_sample.py`

## 最小命令

```powershell
py -3 scripts/materialize_public_jira_dataset.py `
  --source-file path\to\jira_issues.jsonl `
  --output-file generated\cross_domain_public_jira.xlsx `
  --metadata-file generated\cross_domain_public_jira_metadata.json `
  --force
```

## 从本地 MongoDB 直接导出一个论文可用的小样本

下面这条命令会从本地恢复好的 TPJD 中，按 6 个项目各抽 500 条最近 issue，输出 `3000` 条 JSONL：

```powershell
py -3 scripts/export_public_jira_project_sample.py `
  --db-name JiraReposAnon20250623 `
  --per-project 500 `
  --raw-output generated\public_jira_project_sample.jsonl `
  --metadata-file generated\public_jira_project_sample_metadata.json `
  --force
```

然后再标准化成 `xlsx`：

```powershell
py -3 scripts/materialize_public_jira_dataset.py `
  --source-file generated\public_jira_project_sample.jsonl `
  --output-file generated\cross_domain_public_jira.xlsx `
  --metadata-file generated\cross_domain_public_jira_metadata.json `
  --force
```

## 贴近当前论文口径的采样

如果你想做一个和当前 Bugzilla 跨领域实验规模接近的 Jira 版本，可以先做按项目均衡采样：

```powershell
py -3 scripts/materialize_public_jira_dataset.py `
  --source-file path\to\jira_issues.jsonl `
  --top-projects 6 `
  --sample-per-project 500 `
  --output-file generated\cross_domain_public_jira.xlsx `
  --metadata-file generated\cross_domain_public_jira_metadata.json `
  --force
```

## 字段映射说明

- `severity` 优先取 Jira 原生或自定义 severity；若不存在，则回退到 `priority`
- `product/project` 优先取项目名，不存在时回退到项目 key
- `component` 会自动把组件列表拼成分号分隔文本
- `description` 支持普通字符串和 Jira 富文本 JSON 结构
- `comments_count` 支持从 comment 列表、`comment.total` 或显式计数字段解析

## 下一步

如果你把 TPJD 的原始文件或导出的 issue 文件放到本机路径，我可以继续帮你：

- 确认 `json-root`
- 跑标准化
- 检查项目分布和时间跨度
- 再决定是否把它裁成适合论文跨领域验证的小样本
