# 仓库配置登记

> 本文件登记常用 git 仓库的配置（路径、远程、文档更新约定）。**本文件是配置数据，不是通用规则**——通用 git 操作规则在 SKILL.md，本文件只提供「各仓库特有的约定」。
> 使用方式：确认 target_repo 后，按仓库名加载对应小节。未登记的仓库直接按 SKILL.md 通用流程执行，无 README/CHANGELOG 强制要求。

## 1. Ai 仓库（~/Ai）

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/Ai/` |
| 远程仓库 | `git@github.com:jianglvbo/Ai.git`（SSH） |
| 默认分支 | `main` |
| 安装方式 | `cp -r`（严禁 symlink） |
| 提交邮箱 | `49331439+jianglvbo@users.noreply.github.com` |

### 文档更新约定（强制性）

每次推送前必须更新 README.md 和 CHANGELOG.md，不可跳过：

- **README.md**：变更影响目录结构/Skill 列表/仓库规范/工具/安装方式时更新对应章节，并更新底部「最后更新」日期
- **CHANGELOG.md**：文件顶部插入新版本条目，格式：

```markdown
## X.Y.Z — YYYY-MM-DD

### Added / Changed / Fixed / Removed
- 变更描述
```

版本号规则：MAJOR（结构重大变更）/ MINOR（新增 skill、功能级）/ PATCH（修正、文档更新），不跳过。

### 提交 author

`--author="<模型名> <49331439+jianglvbo@users.noreply.github.com>"`。邮箱固定为此仓库的 noreply 邮箱（本仓库约定）；模型名由执行 agent 自行获取。

### 提交信息示例

- `fix(investment-framework): 模板 tags 示例对齐 tag-taxonomy`
- `feat(ai-repo-manager): 新增自动 push 阈值规则`
- `chore(investment-review): 同步三处 skill 副本`

## 2. 投资知识库仓库

| 项目 | 值 |
|------|-----|
| 本地路径 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库` |
| 远程仓库 | `git@github.com:jianglvbo/investment-notes.git`（私有，SSH） |
| 默认分支 | `main` |
| 提交邮箱 | 同上 noreply 邮箱（若未配置则用 `git config user.email`） |

### 文档更新约定

- 无 README/CHANGELOG 强制要求（Obsidian vault，以内容文件为主）
- `.gitignore` 已排除：`.smart-env/`、`.obsidian/workspace*.json`、`.obsidian/plugins/`、`.trash/`、`__visit_history/`、`.space/*.mdb`、`.makemd/`、`.DS_Store`
- 知识库变动后提交/推送进此仓库

### 提交 author

`--author="<模型名> <邮箱>"`，邮箱用 `git config user.email` 或本仓库约定值；模型名由执行 agent 自行获取。

## 3. 新增仓库

未登记的仓库：直接按 SKILL.md 通用流程执行（无 README/CHANGELOG 强制要求），首次使用后如需长期维护，可在此追加小节。
