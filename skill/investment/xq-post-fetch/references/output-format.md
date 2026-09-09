# 帖子集输出格式规范

> 由 xq-post-fetch SKILL.md Output Format 引用。帖子集按 #29 例外流程直接进提炼（investment-refine 加载），不经粗加工。

## 字段表

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| title | string | 帖子标题（有 title 字段用 title；无 title 取正文首个完整句子，不硬切字数） |
| text | string | 正文全文（截断帖补全后标记） |
| created_at | string | 发布时间（YYYY年M月D日 HH:MM） |
| form_type | string | **帖子形态：回复 / 短文 / 长文**（客观判定：有"回复 @"/引用块 → 回复；正文 <200 字且无引用块 → 短文；≥200 字或含小标题/分段 → 长文；2026-09-06 起落进摘要行，供提炼零解析读取） |
| retweet_count | int | 转发数 |
| reply_count | int | 回复数 |
| like_count | int | 点赞数 |
| is_pinned | bool | 是否置顶 |
| completeness | string | 全文 / 摘要 |
| post_url | string | 帖子原文链接（`https://xueqiu.com/{xq_id}/{post_id}`） |

## 三件套结构

每帖为 `## N. 标题 + 正文 + 摘要行`，帖间以 `---` 分隔；摘要行标记「全文」或「摘要」，**并携带形态（2026-09-06 起）**：

```markdown
## 1. {帖子标题}

{正文全文}

> 发布：{YYYY年M月D日 HH:MM} | 形态：{回复|短文|长文} | 转发 {n} | 回复 {n} | 点赞 {n} | 全文 | [原文](https://xueqiu.com/{xq_id}/{post_id})
```

## frontmatter

```markdown
---
title: "雪球帖子采集：{nickname} {YYYY年M月D日}"
source: "https://xueqiu.com/u/{xq_id}"
author: "{nickname}"
date: "{YYYY年M月D日}"
recorded: "{YYYY年M月D日}"
type: "帖子集"
status: "待提炼"
tags: []
---
```

**status 取值（2026-09-09 新增，摘要标记）**：

| 值 | 含义 | 提炼处理 |
|:---|:---|:---|
| `待提炼` | 全部帖子均为「全文」（经详情页验证） | 正常提炼 |
| `待提炼-含摘要` | 含「摘要」帖（详情页风控未补全全文） | **只提炼标「全文」的帖；标「摘要」的一律跳过** |

> 判定以每帖摘要行的 `全文` / `摘要` 标记为准，status 仅作文件级快速提示。采集器与补全器均自动维护该值。

## 铁律

- 每帖必须带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接（画像表原文链接唯一权威来源，framework-rules #35）
- 未经详情页验证不得标「全文」
- **标「摘要」的帖不可提炼**（内容不完整，2026-09-09 用户确认）：提炼环节只处理标「全文」的帖
- **标题不得截断 markdown 链接**（2026-08-26 教训：`body[:30]` 硬切曾把 `[$中国联通(00762)$](https://xueqiu` 切成残缺 URL）。标题提取：优先正文首个完整句子（仅全角 `。！？` 断句，URL 中半角 `?`/`!` 不作句末）；无完整句子时按链接整体安全截断
