---
name: ai-repo-manager
description: ~/Ai/ 本地 Skill 仓库管理器。管理仓库的 GitHub 版本控制流程，包括变更后自动更新 README.md 和 CHANGELOG.md、Git 提交推送、版本号升级。触发词：「存到仓库」「更新仓库」「推送到GitHub」「仓库管理」「同步仓库」「commit」「push to repo」。
agent_created: true
---

# Ai/ 仓库管理 Skill

管理 `~/Ai/` 本地 Skill 仓库的 GitHub 版本控制全流程。确保每次变更都正确更新文档并同步到远程。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 要求将 Skill/工具存入仓库
- 要求推送到 GitHub
- 对仓库内容做了变更需要同步
- 提到「更新 README」「更新 CHANGELOG」

## 仓库信息

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/Ai/` |
| 远程仓库 | `https://github.com/jianglvbo/Ai` |
| 默认分支 | `main` |
| 安装方式 | `cp -r`（严禁 symlink） |

## 工作流程

每次仓库变更都必须严格遵循以下流程，**READMEME.md 和 CHANGELOG.md 的迭代是强制性步骤，不可跳过**：

### 步骤 1：变更文件

完成实际的代码/文档变更（新增 skill、修改 SKILL.md、更新脚本等）。

### 步骤 2：更新 README.md（强制性）

检查本次变更是否需要更新 README.md，以下情况必须更新：

| 变更类型 | README 更新内容 |
|---------|----------------|
| 新增 Skill | 更新目录结构和 Skill 说明列表 |
| 移除 Skill | 从目录结构和列表删除 |
| 变更仓库规范 | 更新对应章节 |
| 新增工具 | 更新 tools/ 目录结构 |
| 修改安装方式 | 更新安装章节 |

同时更新底部的「最后更新」日期。

### 步骤 3：更新 CHANGELOG.md（强制性）

在文件顶部插入新版本条目。格式参考 `references/changelog-format.md`：

1. **判断版本号**：按 MAJOR.MINOR.PATCH 规则升级
2. **写条目**：用 Added / Changed / Fixed / Removed 分类
3. **标注日期**：当前日期 YYYY-MM-DD

### 步骤 4：Git 提交

```bash
cd ~/Ai
git add -A
git commit -m "<简洁的提交信息>"
```

提交信息要求：中文、一句话概括、无需前缀。

### 步骤 5：同步远程（推送前）

**先本地提交，再检查远程是否有新变动。**

```bash
git fetch origin
```

检查本地是否落后于远程：

```bash
git rev-list --count HEAD..origin/main
```

- 结果为 0：远程无新提交，直接推送
- 结果为 > 0：远程有新提交，必须先合并：

```bash
git pull --rebase origin main
```

> ⚠️ rebase 前必须先完成本地 commit（无 unstaged changes）。如遇冲突，解决后 `git add` + `git rebase --continue`，无法解决则报告用户。

### 步骤 6：推送到 GitHub

```bash
git push origin main
```

如遇 RPC 错误（大文件），使用：
```bash
git -c http.postBuffer=2147483648 push origin main
```

### 步骤 7：确认

推送完成后确认远程已同步：
```bash
git log --oneline -1
git ls-remote origin refs/heads/main | awk '{print $1}'
```

两个哈希值应一致。

## 常见场景

### 场景 A：新增 Skill 到仓库

```text
1. cp -r ~/.workbuddy/skills/skill-name ~/Ai/skill/skill-name
2. 更新 README.md：目录结构 + Skill 说明列表
3. 更新 CHANGELOG.md：版本号 +1 MINOR，Added 条目
4. git fetch origin && git pull --rebase origin main（如有远程更新）
5. git add -A && git commit && git push
```

### 场景 B：修改已有 Skill

```text
1. 编辑 Skill 文件
2. 更新 CHANGELOG.md：版本号 +1 PATCH，Changed 条目
3. git fetch origin && git pull --rebase origin main（如有远程更新）
4. git add -A && git commit && git push
```

### 场景 C：仅文档更新

```text
1. 编辑 README.md / CHANGELOG.md
2. 更新 CHANGELOG.md：记录本次文档更新
3. git fetch origin && git pull --rebase origin main（如有远程更新）
4. git add -A && git commit && git push
```

## 注意事项

- **READMEME.md 和 CHANGELOG.md 是每次推送的必备产物**，不可遗漏
- 不要跳过版本号（从 1.3.0 直接跳 1.5.0 不可取）
- Skill 安装到仓库用 `cp -r`，不要用 symlink
- 推送前确认没有遗漏文件（`git status`）
