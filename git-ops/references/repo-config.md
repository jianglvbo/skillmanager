# 仓库配置登记（git-ops）

> git-ops 是通用提交管理工具，本文件登记用户常用 git 仓库的配置（路径、邮箱、忽略约定）。**配置数据，非通用规则**。
> 使用方式：调用方确认 target_repo 后按仓库名加载小节；未登记的仓库按 SKILL.md 通用流程执行。

## 1. Obsidian 投资知识库

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库` |
| 远程仓库 | `git@github.com:jianglvbo/investment-notes.git`（私有，SSH） |
| 默认分支 | `main` |
| 提交邮箱 | `49331439+jianglvbo@users.noreply.github.com`（或 `git config user.email`） |

### 忽略约定（.gitignore 已配置，提交时勿入）

`.smart-env/`、`.obsidian/workspace*.json`、`.obsidian/plugins/`、`.trash/`、`__visit_history/`、`.space/*.mdb`、`.makemd/`、`.DS_Store`

## 2. Ai 仓库（~/Ai）

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/.skills-manager/skills/` |
| 远程仓库 | `git@github.com:jianglvbo/Ai.git`（SSH） |
| 默认分支 | `main` |
| 提交邮箱 | `49331439+jianglvbo@users.noreply.github.com` |

> Ai 仓库的完整版本控制流程（含 README 更新约定）由 `ai-repo-manager` skill 管理；git-ops 也可提交该仓库，但完整流程建议走 ai-repo-manager。

## 3. 新增仓库

未登记的仓库：按 SKILL.md 通用流程执行（`git status` → `git add` → `git commit` → 可选 push）。如需长期维护，在此追加小节。
