---
name: xueqiu-to-bear
description: 抓取雪球（Xueqiu）帖子和评论，格式化为熊掌记中的问答文章。当用户提供雪球链接并希望将帖子转为熊掌记问答格式文章（含高赞评论和楼主回复）时使用。支持 Bear MCP 和 bearcli 两种方式。
---

# 雪球帖子转熊掌记问答文章

将雪球帖子（主帖 + 高赞评论 + 楼主回复）抓取整理为问答格式文章，存入熊掌记。

## 前置依赖

- **Bear 访问能力**（二选一）：
  - Bear MCP Server（推荐，需 Agent 已连接）
  - bearcli 命令行（`/Applications/Bear.app/Contents/MacOS/bearcli`）
- **macOS 环境**: curl、python3

## 工作流程

### 1. 获取雪球 Cookie

```bash
curl -s -H "User-Agent: Mozilla/5.0 ..." -c /tmp/xq_cookies.txt "https://xueqiu.com/" > /dev/null 2>&1
```

### 2. 抓取主帖

从 URL 提取帖子 ID（如 `https://xueqiu.com/2292705444/358275118` → ID=`358275118`），用户 ID=`2292705444`。

```bash
# 主帖内容
curl -s -b /tmp/xq_cookies.txt "https://xueqiu.com/statuses/show.json?id={POST_ID}"

# 全部评论（分页，每页最多100条）
curl -s -b /tmp/xq_cookies.txt "https://xueqiu.com/statuses/comments.json?id={POST_ID}&count=100&page=1"
curl -s -b /tmp/xq_cookies.txt "https://xueqiu.com/statuses/comments.json?id={POST_ID}&count=100&page=2"
# ... 直到 total count 覆盖
```

### 3. 数据处理

用 Python 处理 JSON 数据:

- **HTML 清理**: `re.sub(r'<[^>]+>', '', text)` + `html.unescape(text)`
- **按点赞排序**: `sorted(comments, key=lambda x: x['like_count'], reverse=True)`
- **构建回复链**: 通过 `in_reply_to_comment_id` 匹配被回复的原文
- **筛选高赞**: 通常保留赞数 ≥ 3 的评论和楼主（帖主）回复

### 4. 文章格式

```
# {文章标题}
#雪球分析 {其他标签}

**[帖主名](https://xueqiu.com/{user_id})** [{date}· {source}](https://xueqiu.com/{user_id}/{post_id})
{主帖正文}
> [评论者](https://xueqiu.com/{user_id}) {date}· {location}· {likes}赞
> {评论内容}
---
[评论者](https://xueqiu.com/n/{name}) {date}· {likes}赞
{评论内容}
> [回复者](url) {date}· {likes}赞
> {回复内容}
---
```

**格式规则:**

- **帖主原文**: `**[name](url)** [date· source](post_url)` — 加粗，独占顶部
- **独立评论**: `[name](url) date· likes赞` — 不加粗
- **回复（含楼主回复）**: `> **[name](url)** 回复xxx· likes赞` 或 `> [name](url) date· likes赞`
- **被回复的原文**: 放在回复上方，**不用** `>` 前缀
- **分隔符**: 每段内容之间用 `---` 分隔
- **排序**: 按点赞数从高到低排列

### 5. 存入熊掌记

**选择 Bear MCP 还是 bearcli —— 关键决策：是否需要插入图片**

> ⚠️ Bear MCP **不支持插入图片/附件**（只有 `mcp__bear__create_note`，无 `add_attachment`）。
> bearcli 支持完整功能，包括：`bearcli attachments add <ID> --filename image.png`。

**决策树**：
- 文章为纯文本（无图片） → **Bear MCP 优先**（更便捷，标签/创建一站式）
- 文章含图片/附件 → **必须用 bearcli**（MCP 做不到）

**方式 A：Bear MCP（纯文本专用）**

```
工具: mcp__bear__create_note
参数:
  title: "{文章标题}"
  content: |
    # {文章标题}
    #雪球分析 {其他标签}

    **[帖主名](url)** [date· source](post_url)
    {主帖正文}
    > [评论者](url) date· likes赞
    > {评论内容}
    ---
    ...（完整格式化内容）
  tags: ["雪球分析", "{其他标签}"]
```

如需在创建后打开笔记：
```
工具: mcp__bear__open_note
参数:
  id: "返回的笔记ID"
```

**方式 B：bearcli 命令行（含图片/完整功能）**

```bash
# 1. 创建笔记（从 stdin 读取长内容）
cat /tmp/article.md | /Applications/Bear.app/Contents/MacOS/bearcli create "{文章标题}" --tags "雪球分析" --format json --fields id

# 2. 插入图片附件（MCP 不支持，只有 bearcli 能做）
cat /path/to/image.png | /Applications/Bear.app/Contents/MacOS/bearcli attachments add <笔记ID> --filename image.png

# 3. 打开笔记
/Applications/Bear.app/Contents/MacOS/bearcli open <笔记ID>
```

## 辅助脚本

`scripts/fetch_xueqiu.py`: 自动化抓取和格式化。

```bash
# 用法: python3 scripts/fetch_xueqiu.py <帖子URL> <输出文件> [最少赞数]
python3 scripts/fetch_xueqiu.py "https://xueqiu.com/2292705444/358275118" /tmp/article.md 3
```

脚本输出格式化的 Markdown 文件，可直接通过 SQLite 写入熊掌记。

## 注意事项

- 雪球 API 需要先访问首页获取 Cookie，Cookie 有效期较短
- 评论内容含 HTML 标签，需清理
- `in_reply_to_comment_id` 可能指向不在当前结果集中的评论（被删除或分页）
- 长评论（如 AI 总结）可能超过 2000 字，酌情保留或截断
- 帖主 ID 从 URL 中提取（如 `xueqiu.com/2292705444/...` 中 `2292705444` 为用户 ID）
- 标签默认包含 `#雪球分析`，用户可指定额外标签
