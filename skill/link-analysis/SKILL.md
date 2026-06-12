---
name: link-analysis
description: 链接分析工作流。收集用户发送的链接（雪球、公众号、抖音等），定时整理生成分析文档存入熊掌记，并通过飞书发送浓缩摘要。当用户发送链接要求纳入分析、或定时任务触发每日整理时使用。
---

# 链接分析

整理当日收集的信息链接，生成分析文档存入熊掌记，飞书发送浓缩版。

**格式参考**：熊掌记中的《欧洲风电商业模式问答》笔记。

> **注意**：定时触发由各 Agent 本地管理（如自动化/定时任务机制），本 Skill 仅定义执行逻辑。

## 一、链接收集

当用户发送链接（雪球、公众号、抖音等）时：

1. **仅回复**：`收到，纳入分析`（不要多说）
2. **保存到各 Agent 约定的链接存储路径**

JSON格式：
```json
[
  {
    "url": "https://...",
    "source": "雪球/抖音/微信公众号",
    "received_at": "ISO时间",
    "note": "用户附带的简短说明（可选）"
  }
]
```

追加到当天已有数组中，文件不存在则创建。

## 二、执行流程

### 阶段一：确认

1. 读取当日链接文件，无文件或为空 → 通过飞书通知用户"今日无待分析链接"，结束
2. **先通过飞书发送确认消息给用户**：`📋 今日已收集 N 条链接，是否生成《当日信息分析_YYYY-MM-DD》？回复「生成」确认。`
3. **等待用户回复「生成」确认后**，才进入阶段二

### 阶段二：生成文档

1. 抓取所有链接内容
2. 生成 Markdown 文档
3. 存入熊掌记
4. 飞书发送浓缩版

## 三、飞书消息发送

使用飞书（lark-im skill）发送消息给用户本人。

### 发送确认消息
```bash
lark-cli im +messages-send --as user --chat-id <chat_id> --text "📋 今日已收集 N 条链接..."
```

### 发送浓缩版
```bash
lark-cli im +messages-send --as user --chat-id <chat_id> --text "（浓缩版内容，markdown格式）"
```

## 四、内容抓取（分层策略）

按优先级尝试：

**优先级1 - WebFetch / autocli read**：
- 优先使用 Agent 自带的网页获取工具
- 可用 `autocli read <url> -f text` 提取正文

**优先级2 - curl**（WebFetch 失败时）：
```bash
curl -s -L -H "User-Agent: Mozilla/5.0 ..." "URL" | python3 提取正文
```
适合公众号、新闻网站。

**优先级3 - 浏览器自动化**（最后手段，雪球等有 WAF 的网站）：
- 使用各 Agent 自带的浏览器工具

**只抓取原文正文，不抓取评论和讨论。**

## 五、文档格式

参照《欧洲风电商业模式问答》格式，紧凑排版，段落间不空行：

```markdown
#每日分析

---

## 主题标题（根据链接内容概括）

**[作者名](作者链接)** [日期 · 来源平台](原文链接)

（原文核心内容，紧凑排列）

**核心观点**：（一段话概括核心逻辑）
**关键数据**：（关键数字和数据点紧凑列出）
**分析与思考**：（深度分析：内在逻辑、风险因素、市场机会、投资启示）

---

（每条链接一个独立区块，用 --- 分隔）

---

## 今日综合要点

（跨所有链接的综合性分析与总结，紧凑排列）
```

**要点**：
- 标签行 `#每日分析` 是正文第一行（不含 H1 标题）
- 每节以作者+链接+日期的粗体行开头
- 正文紧凑无多余空行
- 每条链接间用 `---` 分隔

## 六、保存到熊掌记

**选择 Bear MCP 还是 bearcli —— 关键决策：是否需要插入图片**

> ⚠️ Bear MCP **不支持插入图片/附件**（只有 `mcp__bear__create_note`，无 `add_attachment`）。
> bearcli 支持完整功能，包括：`bearcli attachments add <ID> --filename image.png`。

**决策树**：
- 文章为纯文本（无图片） → **Bear MCP 优先**（更便捷，标签/创建一站式）
- 文章含图片/附件 → **必须用 bearcli**（MCP 做不到）

### 方式 A：Bear MCP（纯文本专用）

```
工具: mcp__bear__create_note
参数:
  title: "当日信息分析_YYYY-MM-DD"
  content: |
    #每日分析

    ---

    ## 主题标题
    ...（完整 Markdown 正文）
  tags: ["每日分析"]
```

返回结果中包含笔记 ID（`id` 字段）。

### 方式 B：bearcli 命令行（含图片/完整功能）

```bash
# 1. 创建笔记（从 stdin 读取长内容）
cat /tmp/daily_analysis.md | bearcli create "当日信息分析_YYYY-MM-DD" \
  --tags "每日分析" --format json --fields id

# 2. 插入图片附件（MCP 不支持，只有 bearcli 能做）
cat /path/to/image.png | bearcli attachments add <笔记ID> --filename image.png

# 3. 打开笔记
bearcli open <笔记ID>
```

> bearcli 路径：`/Applications/Bear.app/Contents/MacOS/bearcli`
>  mutating 命令静默成功（exit 0），错误输出到 stderr。

## 七、飞书浓缩版

```markdown
📊 今日信息分析 (YYYY-MM-DD)

**核心要点：**
1. [主题1] — 一句话总结
2. [主题2] — 一句话总结

**综合观点：**
（2-3段浓缩分析，要点式呈现）

📝 完整文档已保存至熊掌记：《当日信息分析_YYYY-MM-DD》
```

## 注意事项

- 标签行 `#每日分析` 必须是正文第一行，不要通过 URL Scheme tags 参数传
- 正文不要包含 H1 标题（Bear 自带标题字段）
- 段落间不空行，保持紧凑
- 不抓取评论和讨论，只保留原文核心内容
- 雪球链接优先用 `autocli read` 抓取
- **必须先确认用户同意后**，才执行内容抓取和文档生成
