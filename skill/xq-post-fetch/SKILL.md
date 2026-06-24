---
name: xq-post-fetch
description: |
  雪球博主帖子采集。通过 Chrome Extension MCP 在浏览器中调用雪球 user_timeline API，
  获取指定用户的帖子时间线，输出结构化 JSON。
  触发词：「抓取雪球」「雪球帖子」「采集雪球」「xq fetch」「雪球动态」
  排除条件：含「分析」「提炼」「画像」等关键词时交给 blogger-refine / wiki-refine。
  依赖条件：Chrome 浏览器运行中 + QoderWork Chrome Extension 已安装 + 雪球已登录。
license: MIT
agent_created: true
metadata:
  version: "3.0.0"
  short-description: 按 xq_id 通过浏览器 MCP 采集雪球帖子（多页+置顶帖跳过+双格式兼容）
compatibility: 通用
---

# 雪球博主帖子采集 v3.0

## Default stance

### 核心原则
- **ID 驱动**：输入 xq_id，由调用方决定采集谁，不内置博主列表
- **浏览器 MCP 直达**：通过 Chrome Extension MCP 执行 JS，复用浏览器登录态绕过阿里云 WAF
- **只采不评**：不分析、不提炼，原始数据原样输出
- **容错优先**：逐条目 try-catch，单条异常不影响整批；翻页跳过置顶帖再判断时间边界

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不在采集阶段分析或总结帖子内容
- 绝不直接 curl / requests 调 API（阿里云 WAF 拦截，返回 JS 挑战页）
- 绝不用 autocli feed（不登录返回空、无分页、无用户过滤）
- 绝不用 screen_name 作主键（user_id 唯一不变）

---

## Workflow

### 输入参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|:---|:---|:---|:---|:---|
| xq_id | int | 是 | — | 雪球用户 ID |
| hours | int | 否 | 48 | 时间窗口（小时） |
| max_pages | int | 否 | 5 | 最大翻页数 |

### 第一步：获取浏览器 Tab

1. 调用 `mcp__builtin_browser__tabs_context` 获取当前可用 tabId
2. 若无可用 tab → 调用 `tabs_create` 创建新 tab

### 第二步：导航到雪球

1. 调用 `navigate` 打开 `https://xueqiu.com/u/{xq_id}`
2. 等待页面加载完成（导航返回 duration 即可）

### 第三步：验证登录态

1. 调用 `javascript_tool` 执行 `document.title`
2. 已登录：标题含用户昵称或「我的首页」
3. 未登录：标题为「雪球 - 聪明的投资者都在这里」→ **停止，提示用户在 Chrome 中登录雪球**

### 第四步：调用 user_timeline API

1. 加载 JS 模板：读取 `references/fetch-template.js`
2. 替换占位符：`__XQ_ID__` → xq_id，`__HOURS__` → hours，`__MAX_PAGES__` → max_pages
3. 调用 `javascript_tool` 执行替换后的 JS
4. JS 内部逻辑（详见 `references/fetch-template.js`）：
   - 逐页 fetch `/v4/statuses/user_timeline.json?user_id={xq_id}&page={n}&type=0`
   - **跳过置顶帖**（`isTop === true`）和**远古帖**（比 cutoff 早 >1 年）再判断时间边界
   - 非置顶/非远古帖最旧时间 < cutoff → 停止翻页
   - 兼容双格式响应（直接字段 / `data` JSON 字符串）
   - 返回 JSON 数组

> ⚠️ **已知限制**：`user_timeline` API 对回复帖（「回复@…」）的返回不一致，可能遗漏部分回复。如需完整回复帖，需补充调用回复专用端点 [待验证]。

### 第五步：输出结果

1. 解析 JS 返回的 JSON 字符串
2. 如有错误字段 → 报告错误并停止
3. 正常 → 按 Output format 输出结构化数据
4. 报告摘要：采集 N 条帖子，时间范围 X ~ Y

### 错误处理

| 情况 | 处理 |
|:---|:---|
| HTTP 非 200 | 记录错误，停止采集 |
| 返回空 statuses | 当前页无更多数据，停止翻页 |
| 登录态失效 | 停止，提示用户登录 |
| 单页 fetch 超时 | 重试 1 次，仍失败则停止 |

---

## Output format

```json
[
  {
    "user_id": 9650668145,
    "status_id": 396224484,
    "screen_name": "管我财",
    "title": "",
    "text": "正文纯文本，去 HTML，≤500 字",
    "created_at": 1782228786000,
    "created_at_local": "2026/6/23 18:33:06",
    "retweet_count": 13,
    "reply_count": 136,
    "like_count": 490,
    "is_retweet": false,
    "source": "iPhone"
  }
]
```

| 字段 | 类型 | 来源 | 说明 |
|:---|:---|:---|:---|
| user_id | int | `d.user_id` | 雪球用户 ID |
| status_id | int | `d.id` | 帖子 ID |
| screen_name | string | `d.user.screen_name` | 博主昵称 |
| title | string | `d.title` | 帖子标题 |
| text | string | `d.description` 或 `d.text` | 正文（去 HTML，≤500 字） |
| created_at | int | `d.created_at` | Unix 毫秒时间戳 |
| created_at_local | string | 转换 | 北京时间字符串 |
| retweet_count | int | `d.retweet_count` | 转发数 |
| reply_count | int | `d.reply_count` | 回复数 |
| like_count | int | `d.like_count` | 点赞数 |
| is_retweet | bool | `d.retweeted_status != null` | 是否转发 |
| source | string | `d.source` | 发帖设备 |

---

## Relative files

| 场景 | 文件 | 内容 |
|:---|:---|:---|
| 执行采集 | `references/fetch-template.js` | 浏览器内执行的 JS 模板，含占位符和双格式兼容 |
| 查阅 API 细节 | `references/api-reference.md` | API 端点、响应结构、字段映射、登录验证 |

---

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数（xq_id、hours、max_pages） |
| 2 | 雪球 Web API（user_timeline.json 响应结构） |
| 3 | Chrome Extension MCP（tabs_context / navigate / javascript_tool） |
| 4 | 知识框架 pipeline（采集 → 粗加工 → 画像更新） |

---

## 自检

- [ ] xq_id 已传入且为数字？
- [ ] 浏览器 tab 可用（tabs_context 返回有效 tabId）？
- [ ] 雪球登录态已验证（document.title 非默认标题）？
- [ ] 置顶帖和远古帖都已跳过（不参与时间边界判断）？
- [ ] JS 模板兼容双格式响应（直接字段 + data JSON 字符串）？
- [ ] 输出字段完整且类型匹配？
- [ ] 已知回复帖可能不完整，是否已告知调用方？
