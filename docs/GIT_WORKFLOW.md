# Git 工作流指南

## 📋 分支策略

### 分支说明

- **main** - 主分支，稳定版本，只接受来自dev的合并
- **dev** - 开发分支，日常开发在这里进行
- **feature/** - 功能分支（可选），用于开发新功能

## 🔄 日常开发流程

### 1. 开始开发（确保在dev分支）

```bash
# 查看当前分支
git branch

# 如果不在dev分支，切换到dev
git checkout dev

# 拉取最新代码
git pull origin dev
```

### 2. 进行开发和提交

```bash
# 查看修改的文件
git status

# 添加修改的文件
git add .
# 或者添加特定文件
git add src/agents/coding_agent_v4_2.py

# 提交修改
git commit -m "feat: 添加新功能描述"

# 推送到远程dev分支
git push origin dev
```

### 3. 合并到主分支（功能完成且测试通过后）

```bash
# 切换到main分支
git checkout main

# 拉取最新的main分支
git pull origin main

# 合并dev分支
git merge dev

# 推送到远程main分支
git push origin main

# 切换回dev继续开发
git checkout dev
```

## 📝 提交信息规范

使用语义化提交信息：

```bash
# 新功能
git commit -m "feat: 添加Coding Agent的错误重试机制"

# 修复bug
git commit -m "fix: 修复递归限制错误"

# 文档更新
git commit -m "docs: 更新README安装说明"

# 代码重构
git commit -m "refactor: 重构Strategist的提示词生成逻辑"

# 性能优化
git commit -m "perf: 优化输出文件大小，减少95%存储"

# 测试
git commit -m "test: 添加Coding Agent单元测试"

# 构建/配置
git commit -m "chore: 更新依赖版本"
```

## 🌿 功能分支工作流（可选）

如果要开发大型功能，可以创建功能分支：

```bash
# 从dev创建功能分支
git checkout dev
git checkout -b feature/multi-agent-dialogue

# 开发完成后，合并回dev
git checkout dev
git merge feature/multi-agent-dialogue

# 删除功能分支
git branch -d feature/multi-agent-dialogue

# 推送到远程
git push origin dev
```

## 🔍 常用命令

### 查看状态和历史

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline --graph --all

# 查看某个文件的修改历史
git log --follow src/agents/coding_agent_v4_2.py

# 查看分支
git branch -a
```

### 撤销操作

```bash
# 撤销工作区的修改（未add）
git checkout -- 文件名

# 撤销暂存区的修改（已add未commit）
git reset HEAD 文件名

# 撤销最后一次提交（保留修改）
git reset --soft HEAD^

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD^
```

### 查看差异

```bash
# 查看工作区和暂存区的差异
git diff

# 查看暂存区和最后一次提交的差异
git diff --cached

# 查看两个分支的差异
git diff main dev
```

## 🚀 快速命令

### 日常开发（在dev分支）

```bash
# 一键提交并推送
git add . && git commit -m "feat: 你的提交信息" && git push origin dev
```

### 合并到主分支

```bash
# 快速合并dev到main
git checkout main && git pull origin main && git merge dev && git push origin main && git checkout dev
```

## ⚠️ 注意事项

1. **永远不要直接在main分支开发**
2. **合并到main前确保代码已测试**
3. **定期从main同步到dev**（如果有其他人也在开发）
4. **提交前检查.gitignore**，确保不提交敏感信息
5. **大文件不要提交到Git**（使用Git LFS或排除）

## 🔐 保护敏感信息

确保以下文件在 `.gitignore` 中：

```
.env
*.key
*.pem
data/
outputs/
```

## 📊 分支保护（GitHub设置）

建议在GitHub上设置分支保护规则：

1. 进入仓库 Settings → Branches
2. 添加规则保护 `main` 分支：
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Include administrators

这样可以防止直接推送到main分支，必须通过Pull Request。

## 🎯 当前状态

```bash
# 查看当前分支
$ git branch
  main
* dev

# 你现在在dev分支，可以开始开发了！
```

## 📚 更多资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [语义化版本](https://semver.org/lang/zh-CN/)
