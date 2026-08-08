---
name: ai-repo-manager
description: >
  ~/Ai/ 本地 Skill 仓库管理器。管理 Ai 仓库的 GitHub 版本控制流程与文档约定：README 更新、Skill 安装方式（cp -r）、
  变更提交与推送触发。触发词：「存到仓库」「更新仓库」「推送到GitHub」「仓库管理」「同步仓库」「Ai仓库」。
  通用 git 提交/推送操作（author 模型名、Conventional Commits、push 阈值）由 git-ops skill 承担，
  本 skill 只承载 Ai 仓库专属管理规则。
agent_created: true
---

# Ai/ 仓库管理 Skill

管理 `~/Ai/` 本地 Skill 仓库的版本控制与文档约定。**本 skill 只承载 Ai 仓库专属规则**；通用 git 提交/推送操作统一由 `git-ops` skill 承担。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 要求将 Skill/工具存入 Ai 仓库
- 要求推送到 GitHub（Ai 仓库）
- 对 Ai 仓库内容做了变更需要同步
- 提到「更新 README」「存到仓库」「仓库管理」

## 仓库信息

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/Ai/` |
| 远程仓库 | `git@github.com:jianglvbo/Ai.git`（SSH） |
| 默认分支 | `main` |
| 安装方式 | `cp -r`（严禁 symlink） |
| 提交邮箱 | `49331439+jianglvbo@users.noreply.github.com` |

## Default Stance

### 核心原则

- **单一职责**：只管理 Ai 仓库的专属约定（README、安装方式、触发）；通用 git 规则（author/格式/推送阈值）归 git-ops
- **README 是强制产物**：变更影响目录结构/Skill 列表/仓库规范/工具/安装方式时，必须更新 README 对应章节
- **变更历史由 git log 承担**：commit 用 Conventional Commits（由 git-ops 执行），无 CHANGELOG.md
- **提交走 git-ops**：本 skill 不重复定义提交规则，直接调用 git-ops 执行

### 禁止行为

- 绝不把通用 git 规则（author/push 阈值/Conventional Commits 详规）写进本 skill——那是 git-ops 的职责
- 绝不 symlink 安装 skill——必须 `cp -r`
- 绝不跳过 README 更新（若变更影响文档结构）
- 绝不把 git 规则写入投资框架等其他业务 skill

---

## Workflow

### 第一步：确认变更

```bash
cd ~/Ai
git status        # 确认变更类型
```

判断变更类型：新增 Skill / 修改 Skill / 移除 Skill / 仓库规范变更 / 文档更新。

### 第二步：更新 README.md（强制性）

变更影响以下任一内容时必须更新对应章节，并更新底部「最后更新」日期：

| 变更类型 | README 更新内容 |
|:---|:---|
| 新增 Skill | 目录结构 + Skill 说明列表 |
| 移除 Skill | 从目录结构和列表删除 |
| 变更仓库规范 | 更新对应章节 |
| 新增工具 | 更新 tools/ 目录结构 |
| 修改安装方式 | 更新安装章节 |

> 变更历史统一由 git log 承担（Conventional Commits），本仓库**无 CHANGELOG.md**（2026-08-08 删除）。

### 第三步：提交与推送（调用 git-ops）

调用 `git-ops` skill 执行提交与推送（`target_repo = ~/Ai`）：

- 提交信息按 Conventional Commits（git-ops 第四步规则）
- author 用当前 agent 模型名（git-ops 第四步规则）
- 未推送 commit ≥5 自动推送（git-ops 第六步规则）
- fetch/rebase/推送/确认流程见 git-ops

### 第四步：确认

推送完成后确认本地与远程 HEAD 一致（git-ops 流程含此步骤）。

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| repo | string | 本仓库路径（~/Ai） |
| readme_updated | boolean | 是否更新了 README |
| commit_hash | string | 本次提交 hash（由 git-ops 返回） |
| pushed | boolean | 是否推送（由 git-ops 返回） |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 提交/推送 | git-ops skill | 通用 git 提交规则（author/格式/阈值） | 调用 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | Ai 仓库专属约定（README 更新、cp -r 安装） |
| 2 | git-ops skill（通用提交/推送规则） |

---

## 自检

- [ ] 变更是否需更新 README（已更新）？
- [ ] 是否用 `cp -r` 安装 skill（非 symlink）？
- [ ] 提交是否由 git-ops 执行（author 模型名 + Conventional Commits）？
- [ ] 本 skill 是否未混入通用 git 规则？
- [ ] 是否未 force push？
