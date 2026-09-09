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
- **同步必须识别合并，禁止硬性覆盖（2026-09-09 用户硬约束）**：本地 `~/.agents/skills/<name>` 与仓库 `~/Ai/skill/<分类>/<name>` 双向同步时，**必须先逐文件识别差异并语义合并**；**绝不允许**用 `cp -r` / `rsync -a` 无条件覆盖任一侧。两边都有独有改动（真冲突）→ **停下来让用户决策**，不得自行取舍。

### 同步规则（识别合并流程）

`cp -r` 只用于**首次安装**（目标侧不存在该 skill）。目标侧已存在时，一律走识别合并：

1. **逐文件内容级对比**（排除 `.DS_Store` / `__pycache__` / `*.pyc` 噪音）：
   ```bash
   diff -rq -x '.DS_Store' -x '__pycache__' -x '*.pyc' \
     ~/.agents/skills/<name> ~/Ai/skill/<分类>/<name>
   ```
2. **对每个差异文件判定归属**（`diff` 逐行看，不看 mtime）：
   - **单边独有**（一侧是另一侧的超集）→ 取超集版本，属无冲突合并
   - **双方各有独有行** → 真冲突
3. **真冲突处理**：**停止同步该文件，向用户报告**（差异摘要 + 双方改动性质 + 建议），由用户决策；不得擅自取一侧
4. 合并后**再次全量校验**，确保双向零差异（排除噪音）
5. 合并结果提交并推送仓库

> **为什么禁止硬覆盖**：2026-08-31 一次 `cp` 式「收尾同步」把仓库 v2 采集脚本回退成旧版，导致已修复的标题截断 bug 回归、登录校验/修改帖处理/滑块检测全部丢失（2026-09-08 才被发现并恢复）；同日另一侧也因 rsync 覆盖丢失过内容。识别合并是唯一安全路径。

### 禁止行为

- 绝不定义通用 git 提交规则（author/格式/push 阈值）——执行层由 agent 判断，不固化在本 skill
- 绝不 symlink 安装 skill——必须 `cp -r`（仅首次安装）
- **绝不硬性覆盖已存在的 skill**（`cp -r` / `rsync -a` 无条件覆盖）——必须识别合并
- **绝不在真冲突时自行取舍**——必须上报用户决策
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
| 1 | Ai 仓库专属约定（README 更新、识别合并同步、cp -r 首次安装） |
| 2 | 用户显式约定（author 用模型名、Conventional Commits、push 节奏） |

---

## 自检

- [ ] 变更是否需更新 README（已更新）？
- [ ] **同步是否走识别合并**（逐文件 diff 判定归属，未硬性覆盖任一侧）？
- [ ] **真冲突是否已上报用户决策**（未自行取舍）？
- [ ] 是否用 `cp -r` 首次安装 skill（非 symlink）？
- [ ] 合并后是否已全量校验双向零差异（排除 .DS_Store/__pycache__）？
- [ ] 本 skill 是否未混入通用 git 提交规则（执行方式由 agent 判断）？
- [ ] 提交/推送是否已实际完成（无论走哪个工具）？
