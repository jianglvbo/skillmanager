---
name: ai-repo-manager
description: >
  ~/Ai/ 本地 Skill 仓库管理器。管理 Ai 仓库的 GitHub 版本控制流程与文档约定：README 更新、Skill 安装方式（cp -r）、
  变更提交与推送触发。触发词：「存到仓库」「更新仓库」「推送到GitHub」「仓库管理」「同步仓库」「Ai仓库」。
  本 skill 只描述 Ai 仓库的专属管理规则；提交/推送的具体执行方式由 agent 根据场景自行判断选择（如 git-ops skill 或直接 git 命令）。
agent_created: true
---

# Ai/ 仓库管理 Skill

管理 `~/Ai/` 本地 Skill 仓库的版本控制与文档约定。**本 skill 只描述 Ai 仓库专属规则**；具体如何执行提交/推送，由当前 agent 按场景自行判断选择合适工具。

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

- **单一职责**：只描述 Ai 仓库的专属约定（README、安装方式、触发）；提交/推送执行方式不在本 skill 内定义
- **README 是强制产物**：变更影响目录结构/Skill 列表/仓库规范/工具/安装方式时，必须更新 README 对应章节
- **变更历史由 git log 承担**：commit 用 Conventional Commits，无 CHANGELOG.md
- **执行方式由 agent 判断**：提交/推送怎么做，由当前 agent 按场景选择合适工具（如 git-ops skill 或直接 git 命令），本 skill 不指定、不绑定

### 禁止行为

- 绝不定义通用 git 提交规则（author/格式/push 阈值）——执行层由 agent 判断，不固化在本 skill
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

### 第三步：提交与推送（执行方式由 agent 判断）

完成 README 更新后，**提交与推送的执行方式由当前 agent 按场景自行判断选择**——可以调用 git-ops skill（通用提交管理），也可以用直接 git 命令。判断依据：当前环境是否有 git-ops 可用、任务复杂度、用户偏好。

本 skill 不指定、不绑定具体执行工具。

### 第四步：确认

推送完成后确认本地与远程 HEAD 一致。

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| repo | string | 本仓库路径（~/Ai） |
| readme_updated | boolean | 是否更新了 README |
| changes | list[string] | 本次变更清单 |

---

## Relative Files

无（本 skill 只描述 Ai 仓库专属规则，无外部依赖文件）。

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | Ai 仓库专属约定（README 更新、cp -r 安装） |
| 2 | 用户显式约定（author 用模型名、Conventional Commits、push 节奏） |

---

## 自检

- [ ] 变更是否需更新 README（已更新）？
- [ ] 是否用 `cp -r` 安装 skill（非 symlink）？
- [ ] 本 skill 是否未混入通用 git 提交规则（执行方式由 agent 判断）？
- [ ] 提交/推送是否已实际完成（无论走哪个工具）？
