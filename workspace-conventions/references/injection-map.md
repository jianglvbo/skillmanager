# 各 agent 注入点对照表

> 全部为 2026-09-26 在一台 Mac 上实测（`ls` / DB 查询 / 会话注入证据）。
> 换机器/换用户目录后必须重新核实，别把这张表当先验事实。

## 一、先确定「实际在用哪几家」

装了 skills-manager 的机器，以它的账为准（只读查询）：

```bash
DB="$HOME/.skills-manager/skills-manager.db"
sqlite3 "$DB" "select distinct tool from skill_targets union select distinct tool from folder_targets;"
sqlite3 "$DB" "select value from settings where key='disabled_tools';"
```

实测：只有 `qoder` / `qwen_work` / `zcode` 三家有部署记录，
`claude_code`、`codex`、`qwen_code` 等三十余家在 `disabled_tools` 里 →
**不要为它们建任何文件**。没装 skills-manager 就按 `ls -d $HOME/.<client>` 逐个探。

## 二、三层注入点

| 层 | Qoder | Qwen Work | ZCode |
|:---|:---|:---|:---|
| 工作区项目规则 | `AGENTS.md` ✅ 实证注入 | `AGENTS.md`（同规范） | `AGENTS.md`（同规范） |
| 工作区 skill 层 | `.agents/skills/` ✅ 实证可见 | 同 + `~/.qwenworkcn/skills` 全局 | `[待验证]` 项目级 `.zcode/skills` 为覆盖位，是否也扫 `.agents/skills` 未实测 |
| **用户级通用规则** | `$HOME/.qoder-cn/memory/MEMORY.md` ✅ 实证注入（条目 = 同目录 `<name>.md` + 索引一行） | **无落点**：`$HOME/.qwenworkcn/` 下无 AGENTS/CLAUDE 类文件（只有 `skill-convention.md`，非全局指令文件） | `$HOME/.zcode/AGENTS.md` ✅ 存在（33 行） |
| 用户级 skill 目录 | `$HOME/.qoder-cn/skills` | `$HOME/.qwenworkcn/skills` | `$HOME/.zcode/skills` |

## 三、已知坑

- **Qoder 是否支持用户级 `AGENTS.md`：未证实**。`app.asar` 与 `~/.qoder-cn/app/bundled-resources`
  里搜不到 `AGENTS.md` 常量（只搜到 `MEMORY.md`），也没有该文件存在过被读的证据。
  → 在实测出结论前，Qoder 的通用规则只往 `memory/` 写，**不要新建 `~/.qoder-cn/AGENTS.md`**。
- **悬空软链静默消失**：agent 不报错，skill 直接不见。`$HOME/.qoder-cn/skills` 里的
  `animate` / `animate-expo` 是指向 `$HOME/.agents/skills/`（现为空目录）的相对链，已实测悬空。
- 跨工具公共位置按 Agent Skills 开放规范是 `.agents/skills/`（项目）与 `~/.agents/skills/`（用户），
  Codex / Copilot / Qwen Code 等也认；但这层**谁都不保证自动填**——它不在 skills-manager CLI 的写入范围里。
