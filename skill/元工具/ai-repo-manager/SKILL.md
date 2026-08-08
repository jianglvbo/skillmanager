---
name: ai-repo-manager
description: >
  通用 Git 仓库管理器。管理任意本地 git 仓库的版本控制流程：提交（Conventional Commits 格式 + author 标识当前 agent 模型名）、
  推送（未推送 commit 超阈值自动 push）、远程同步（fetch/rebase 冲突处理）、推送后确认。
  适用于任何 git 仓库（如 Skill 仓库、知识库仓库），不绑定特定 agent 或特定仓库。
  触发词：「存到仓库」「更新仓库」「推送到GitHub」「仓库管理」「同步仓库」「commit」「push to repo」「提交」「推送」。
agent_created: true
---

# 通用 Git 仓库管理 Skill

管理任意本地 git 仓库的提交与推送全流程。**不绑定特定 agent、不绑定特定仓库**——目标仓库由调用方指定（路径或通过 `target_repo` 参数），本 skill 只承载通用 git 操作规则。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 要求将文件/Skill 存入某个仓库
- 要求推送到 GitHub 或其他远程
- 对某仓库内容做了变更需要同步
- 提到「更新 README」「提交」「推送」

## 目标仓库

本 skill 是通用的，目标仓库由调用方通过 `target_repo` 参数传入（本地路径）。**本 skill 内不写死任何仓库路径**。

常见仓库的路径/远程/文档更新约定见 `references/repo-config.md`（按需加载对应仓库小节）。

## Default Stance

### 核心原则

- **author 必须是当前 agent 的模型名**：提交 author 显式指定为**当前执行 agent 的模型名**（"修改人是谁"），**这是唯一合法值**——不依赖 git 全局/仓库级 user.name（那可能是人类用户或另一 agent 的身份），**无法获取模型名时不提交**（停止并询问用户）。如何获取自己的模型名由各 agent 自行决定（如查询本平台会话记录、环境变量），本 skill 不预设获取方式
- **Conventional Commits**：提交信息用 `<type>(<scope>): <描述>` 标准格式
- **防积压**：未推送 commit 数超过阈值必须立即 push，不积压、不等待
- **先本地后远程**：任何推送前先 fetch 检查远端变动，落后则 rebase 合并，绝不 force push

### 禁止行为

- 绝不依赖 git 全局/仓库级 user.name 作为提交 author（无法保证是当前 agent）；**无法获取模型名时绝不提交**，停止并询问用户
- 绝不 force push（`--force`/`--force-with-lease`）——除非用户明确要求
- 绝不跳过文档更新（README，若目标仓库约定要求）
- 绝不跳过推送后确认（本地 HEAD 与远程 HEAD 必须一致）
- 绝不把 commit 信息写入其他 skill（如投资框架）——git 操作规则只属于本 skill

---

## Workflow

### 第一步：确认目标仓库

```bash
cd <target_repo 路径>
git status
git branch --show-current   # 确认当前分支
```

- 若调用方未给路径，询问用户目标仓库
- 确认当前分支（通常 `main`/`master`，以仓库实际为准）

### 第二步：变更文件

完成实际的代码/文档变更。变更前先 `git status` 确认工作区基线。

### 第三步：更新文档（若仓库约定要求）

部分仓库约定每次变更须更新 README.md（是否必须、更新规则见 `references/repo-config.md` 对应仓库小节）。**变更历史统一由 git log 承担（Conventional Commits 已结构化），不维护 CHANGELOG.md**。本 skill 不预设——**以目标仓库约定为准**。

### 第四步：Git 提交

```bash
git add -A
git commit --author="<你的模型名> <邮箱>" -m "<Conventional Commits 信息>"
```

**author 规则（通用）**：
- 邮箱：用目标仓库的 git 配置邮箱（`git config user.email`）或用户指定邮箱
- 模型名：**必须显式填当前 agent 的模型名**——author 标识的唯一合法值就是模型名。如何获取自己的模型名由各 agent 自行决定（如查询本平台会话记录、环境变量），本 skill 不预设获取方式
- **禁止兜底**：无法获取模型名时**不得**用 git 全局/仓库级 user.name 顶替提交（那会让 author 变成人类用户或其他 agent 身份）。此时**停止提交**，向用户报告「无法确认当前模型名」，请用户提供后再提交
- 自检：`git log -1 --format="%an"` 确认 author 是模型名

**Conventional Commits 格式**：

```
<type>(<scope>): <描述>
```

- **type**（必填，英文）：`feat` / `fix` / `docs` / `refactor` / `chore` / `style` / `test`
- **scope**（可选）：改动所属模块名
- **描述**：中文，一句话概括，不堆砌、不用 `+` 串联多个点
- 示例：`fix(investment-framework): 模板 tags 示例对齐 tag-taxonomy`

### 第五步：自动 push 阈值检查

**默认节奏（无特殊要求时）**：累计 **5 次 commit 后主动 push 一次**——每次提交后检查本地未推送 commit 数：

```bash
git rev-list --count origin/<分支>..HEAD
```

- 未推送数 **≥ 5**：主动发起一次推送（执行「第六步→第七步」），不询问、不等待——即「满 5 个 commit 推一次」的固定节奏
- 未推送数 < 5：暂不 push，继续攒 commit，下次提交时复查

**例外（用户特殊要求优先）**：
- 用户明确说「立即 push / 先推一下」：即使未推送数 <5 也立即推送
- 用户明确说「先不 push / 攒着」：即使 ≥5 也暂缓，等用户指示

> 目的：形成「满 5 推一次」的稳定节奏，既避免 commit 积压过多（本地远端漂移大、合并冲突升级），又避免每次提交都推送的频繁网络操作。

### 第六步：同步远程（推送前）

**先本地提交，再检查远程是否有新变动。**

```bash
git fetch origin
git rev-list --count HEAD..origin/<分支>
```

- 结果为 0：远程无新提交，直接推送
- 结果为 > 0：远程有新提交，必须先合并：

```bash
git pull --rebase origin <分支>
```

> ⚠️ rebase 前必须先完成本地 commit（无 unstaged changes）。如遇冲突，解决后 `git add` + `git rebase --continue`，无法解决则报告用户。

### 第七步：推送

```bash
git push origin <分支>
```

如遇 RPC 错误（大文件），使用：
```bash
git -c http.postBuffer=2147483648 push origin <分支>
```

### 第八步：确认

推送完成后确认远程已同步：

```bash
git log --oneline -1
git ls-remote origin refs/heads/<分支> | awk '{print $1}'
```

两个哈希值应一致。

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| repo | string | 目标仓库路径 |
| branch | string | 推送分支 |
| commits_pushed | int | 本次推送的 commit 数 |
| remote_synced | boolean | 本地与远程 HEAD 是否一致 |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 确认目标仓库约定 | references/repo-config.md | 各仓库路径/远程/文档更新约定 | 读取（按目标仓库选小节） |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 调用方传入的 target_repo 参数（目标仓库路径） |
| 2 | 用户显式约定（author 用模型名、Conventional Commits、push 阈值 >5） |
| 3 | Conventional Commits 规范（业界标准） |
| 4 | 目标仓库自身约定（README 规则，见 repo-config） |

---

## 自检

- [ ] 目标仓库路径已确认？
- [ ] author 是否为当前 agent 模型名（非 git 全局 user.name）？
- [ ] 提交信息是否为 Conventional Commits 格式（type(scope): 描述）？
- [ ] 未推送 commit 数是否 ≤5（超了是否已 push）？
- [ ] 推送前是否 fetch + 落后检查？
- [ ] 本地 HEAD 与远程 HEAD 是否一致？
- [ ] 是否未 force push？
- [ ] 是否有 commit 信息误写入其他 skill（如投资框架）？
