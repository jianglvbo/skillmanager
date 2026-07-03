---
title: "{文章标题}"
source: "{来源链接}"
author: "{作者名}"
date: "{原文日期}"
recorded: "{记录日期}"
type: "{帖子|长文|链接|问答}"
status: "待提炼"
wiki_ref: ""
tags: []
---

## frontmatter 格式约束

- **所有文本字段**：YAML 双引号值内禁止嵌套任何双引号（中文 `""` 或 ASCII `"`），必须替换为单引号 `''`。适用于 title、author、summary、sources 等所有文本型字段。例：`"'错过时代'是…"` 而非 `""错过时代"是…"` 或 `"从"皈依者"到…"`
- **tags**：始终使用 YAML block list 格式（`tags:\n  - "标签1"`）。禁止行内流序列 `tags: [...]`
- **category**：始终使用 YAML block list 格式，即使只有一个值
- **sources**：纯路径字符串，不加 `[[wikilink]]` 语法，不带 `.md` 后缀。例：`"原始资源仓库/长文/文章标题"` 而非 `"原始资源仓库/长文/文章标题.md"`
- **date**：YYYY-MM-DD 格式
- **recorded**：YYYY年M月D日 格式
