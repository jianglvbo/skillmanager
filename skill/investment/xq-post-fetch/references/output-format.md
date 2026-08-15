# 帖子集输出格式规范

> 由 xq-post-fetch SKILL.md Output Format 引用。帖子集按 #29 例外流程直接进提炼（investment-refine 加载），不经粗加工。

## 字段表

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| title | string | 帖子标题（有 title 字段用 title；无 title 取正文首个完整句子，不硬切字数） |
| text | string | 正文全文（截断帖补全后标记） |
| created_at | string | 发布时间（YYYY年M月D日 HH:MM） |
| retweet_count | int | 转发数 |
| reply_count | int | 回复数 |
| like_count | int | 点赞数 |
| is_pinned | bool | 是否置顶 |
| completeness | string | 全文 / 摘要 |
| post_url | string | 帖子原文链接（`https://xueqiu.com/{xq_id}/{post_id}`） |

## 三件套结构

每帖为 `## N. 标题 + 正文 + 摘要行`，帖间以 `---` 分隔；摘要行标记「全文」或「摘要」：

```markdown
## 1. {帖子标题}

{正文全文}

> 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | 全文 | [原文](https://xueqiu.com/{xq_id}/{post_id})
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

## 铁律

- 每帖必须带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接（画像表原文链接唯一权威来源，framework-rules #35）
- 未经详情页验证不得标「全文」
