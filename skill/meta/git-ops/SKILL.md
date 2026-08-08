---
name: git-ops
description: >
  通用 Git 提交管理工具。检测 git 仓库变更文件、暂存并提交变更、支持自定义提交信息、查看提交历史、可选推送。
  适用于任何 git 仓库（Ai 仓库、Obsidian 投资知识库等），不绑定特定仓库——目标仓库由调用方指定或从配置层读取。
  触发词：「git 提交」「提交仓库」「commit」「提交管理」「git-ops」「同步仓库」「查看提交历史」。
  与 ai-repo-manager 并存：ai-repo-manager 描述「~/Ai 仓库」的专属管理约定；git-ops 是通用提交管理工具，两者互不依赖，由 agent 按场景自行判断使用。
agent_created: true
---

# git-ops · 通用 Git 提交管理

通用 Git 提交管理工具，管理任意 git 仓库的提交全流程。**不绑定特定仓库**——目标仓库由调用方传入 `target_repo` 或从 `references/repo-config.md` 读取。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 检测某 git 仓库的变更文件
- 暂存并提交仓库变更（含自定义提交信息）
- 查看仓库提交历史
- 提到「git 提交」「提交仓库」「commit」「git-ops」

## Default Stance

### 核心原则

- **通用仓库**：目标仓库由调用方指定或配置层读取，本 skill 不写死任何仓库路径
- **提交前必检测**：先 `git status` 展示变更清单，再决定暂存什么——不盲目 `git add -A`
- **author 必须是当前 agent 的模型名**：作者身份显式指定，不依赖 git 全局 user.name；如何获取模型名由各 agent 自行决定
- **提交信息可自定义**：用户给的信息优先；未给时按 Conventional Commits 生成
- **可追溯**：提交后自检，历史可查

### 禁止行为

- 绝不 force push / 改写已推送历史
- 绝不跳过变更检测直接提交
- 绝不把 git 规则写入其他业务 skill（如投资框架）
- 绝不用 git 全局 user.name 作为 author（无法保证是当前 agent）；无法获取模型名时停止提交并询问
- 绝不提交仓库忽略清单内的文件（.gitignore 约定的内容）

---

## Workflow

### 第一步：确认目标仓库

- 调用方传 `target_repo` → 用之
- 否则查 `references/repo-config.md` 已登记仓库，向用户确认用哪个
- 均无 → 询问用户

```bash
cd <target_repo>
git status            # 确认仓库状态与当前分支
```

### 第二步：检测变更文件

```bash
git status --short    # 展示变更清单（新增/修改/删除）
```

- 展示清单：新增（`??`）、修改（`M`）、删除（`D`）
- 分类汇总：文件数、涉及目录

### 第三步：暂存变更

- 默认：`git add -A` 暂存全部
- 按需：`git add <路径>` 只暂存指定文件
- 暂存后 `git status --short` 复核

### 第四步：提交

```bash
git commit --author="<你的模型名> <邮箱>" -m "<提交信息>"
```

**提交信息格式：Conventional Commits（完整规范）**

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**（必填，英文）：`feat`（新功能）/ `fix`（修复）/ `docs`（文档）/ `style`（格式）/ `refactor`（重构）/ `perf`（性能）/ `test`（测试）/ `build`（构建）/ `ci`（CI）/ `chore`（杂项）/ `revert`（回滚）
- **scope**（可选）：影响范围，如 `(investment-framework)`；跨模块或无法归一时可省略
- **subject**（必填）：一句话描述——中文 ≤30 字、英文 ≤50 字符，结尾不加句号
- **body**（可选）：**空行分隔**，解释「为什么改」而非「改了什么」；多行时每行 ≤72 字符。简单变更可省略
- **footer**（可选）：**空行分隔**——`BREAKING CHANGE: <描述>`（破坏性变更，触发主版本号提升）或 issue 引用（`Closes #123`）。无破坏性变更/无 issue 时省略

**git 硬性要求**：subject 与 body 之间必须空行（否则整段被当标题）；`-m` 一次只传一段，多段用多个 `-m`：

```bash
git commit -m "feat(api): 新增用户认证接口" -m "实现 OAuth2 授权码流程" -m "Closes #123"
```

**完整示例**：
```
feat(api): 新增用户认证接口

实现 OAuth2 授权码流程，支持 refresh_token 轮换，
用于移动端免密续期场景。

BREAKING CHANGE: /auth/token 响应格式变更
Closes #123
```

**落地规则**：
- **简单变更**（一行能讲清）：只写 subject——`feat(git-ops): 新增提交历史查看`
- **复杂变更**（多维度/有理由背景）：subject + body
- **破坏性变更 / 有关联 issue**：追加 footer
- 用户自定义提交信息优先于生成；生成时按上述完整规范判断 body/footer 是否需要

- **邮箱**：目标仓库配置邮箱（`git config user.email`）或 repo-config 登记值
- **author**：当前 agent 模型名；无法获取时**停止提交**并询问用户
- 提交后 `git log -1 --format="%h %an %s"` 自检

### 第五步：查看提交历史（按需）

```bash
git log --oneline -10                    # 最近 10 条
git log --format="%h %ad %an %s" --date=short -5   # 带日期作者
git show --stat HEAD                     # 最近提交变更统计
```

### 第六步：推送（可选，按约定）

- 未推送 commit 数 ≥5 → 主动推送一次（`git fetch origin` 检查落后 → `git pull --rebase` → `git push`）
- 用户明确要求立即推 / 不推 → 遵循用户指示

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| repo | string | 操作的目标仓库路径 |
| changes_detected | list[string] | 检测到的变更文件清单 |
| committed | boolean | 是否完成提交 |
| commit_hash | string | 本次提交的 hash（若提交） |
| history | list[string] | 提交历史（若查看） |
| pushed | boolean | 是否推送 |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 确认目标仓库/配置 | references/repo-config.md | 已登记仓库的路径/邮箱/忽略约定 | 读取（按目标仓库选小节） |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 调用方传入的 target_repo 参数 |
| 2 | 用户显式约定（author 用模型名、Conventional Commits、push 阈值 ≥5） |
| 3 | 仓库配置（references/repo-config.md） |
| 4 | Conventional Commits 规范 |

---

## 自检

- [ ] 目标仓库路径已确认？
- [ ] 变更清单已展示（未跳过检测）？
- [ ] 未暂存忽略清单内的文件？
- [ ] author 是否为当前 agent 模型名？
- [ ] 提交信息为用户自定义或 Conventional Commits 格式？
- [ ] 未 force push？
