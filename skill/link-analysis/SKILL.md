---
name: link-analysis
description: 链接分析工作流。收集用户发送的链接（雪球、公众号、抖音等），存入 Obsidian 投资分析框架的粗制品目录，为用户提供链接来源识别、内容提取和粗加工的策略参考。
---

# 链接分析

定义链接的收集、存储和粗加工策略。供 Agent 在执行链接分析任务时参考。

**Obsidian Vault 路径**：`/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资分析框架/`
**粗制品路径**：`投资分析框架/2 原始资源仓库/粗制品/`
**附件路径**：`投资分析框架/2 原始资源仓库/附件/`

## 一、链接收集

当用户发送链接（雪球、公众号、抖音等）时，按来源渠道分别处理：

### 飞书/IM 渠道 → 存为粗制品

1. **仅回复**：`收到，纳入分析`
2. **保存为 Markdown 文件**到 Obsidian 粗制品目录：
   ```
   投资分析框架/2 原始资源仓库/粗制品/{标题}.md
   ```
3. 文件包含基本 frontmatter（author、source、url）和原始内容

### WorkBuddy 对话内 → 仅存档

1. **仅回复**：`收到，纳入分析`
2. **保存到**：`~/.workbuddy/daily-links/YYYY-MM-DD.json`
3. 不触发后续流程

JSON 格式：
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

## 二、粗加工策略

对粗制品目录中的文件进行粗加工：

### 步骤

1. 读取文件内容，判断类型：帖子 / 长文 / 链接 / 问答
2. 按原始资源模板补全 frontmatter（title、source、author、date、recorded、type）
3. 设置 `status: 待提炼`
4. 保留原文完整内容，逐字稿整理为自然段落（去掉时间轴格式）
5. 移入对应子目录（帖子/、长文/、链接/、问答/）
6. 删除粗制品原文

### 粗加工后结构

```
投资分析框架/2 原始资源仓库/
├── 帖子/{标题}.md
├── 长文/{标题}.md
├── 链接/{标题}.md
└── 问答/{标题}.md
```

## 三、内容抓取策略

按平台采用不同抓取方式：

| 平台 | 方法 | 工具 |
|:---|:---|:---|
| 抖音 | API 获取视频 URL → curl 下载 → ffmpeg 提取音频 → whisper-cli 转写 | ffmpeg + whisper-cpp |
| 公众号/网页 | curl 或 autocli read 提取正文 | curl / autocli |
| 雪球 | autocli read 提取正文 | autocli |

### 抓取优先级

1. **WebFetch / autocli read** — 优先使用 Agent 自带工具
2. **curl** — WebFetch 失败时的降级方案
3. **浏览器自动化** — 雪球等有 WAF 的网站

**只抓取原文正文，不抓取评论和讨论。**

## 注意事项

- **粗加工 ≠ 提炼**：只做分类归档 + 补 frontmatter，不深入分析
- 雪球链接优先用 `autocli read` 抓取
- 抖音视频转写只做基础分段，不去口癖、不修正 Whisper 小错误
- 粗加工完成后同步更新 Obsidian 索引和变更日志
