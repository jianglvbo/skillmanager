---
name: xq-post-fetch
description: |
  雪球帖子采集。通过 browser-act CLI（chrome 模式）采集指定博主的帖子全文，
  自动检测截断并补全长文，输出结构化 markdown 文件。
  触发词：「抓取雪球」「雪球帖子」「采集雪球」「xq fetch」「雪球动态」
  排除条件：含「分析」「提炼」「画像」等关键词时交给 blogger-refine / wiki-refine。
  依赖条件：browser-act CLI 已安装 + Chrome 浏览器运行中 + 雪球已登录。
  区别于 browser-act：xq-post-fetch 是雪球专用采集引擎，browser-act 是通用浏览器自动化。
license: MIT
agent_created: true
metadata:
  version: "4.6.0"
  short-description: 通过 browser-act chrome 模式采集雪球博主帖子全文
compatibility: 通用
---

# 雪球帖子采集 v4.4

## Default Stance

### 核心原则
- **浏览器通道唯一**：通过 browser-act CLI（chrome 模式）或 builtin_browser MCP（javascript_tool）采集，复用 Chrome 登录态绕过阿里云 WAF。browser-act 优先；WebSocket 连接失败时降级到 builtin_browser MCP。
- **全文优先**：每条帖子必须经过完整性验证，未经详情页确认的不得标注「全文」。
- **容错优先**：单帖失败不影响整批；置顶帖标注原始日期，不纳入时间窗口统计。
- **独立可用**：用户直接输入参数即可运行，不依赖 pipeline。
- **确定性优先**：帖子解析按 `references/page-structure.md` 的 pattern 执行，不靠自由发挥。

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不直接 curl / requests 调 API（阿里云 WAF 拦截）
- 绝不在采集阶段分析或总结帖子内容
- 绝不跳过截断检测（长文必须补全全文）
- 绝不将置顶帖归入「今日」时间范围
- 绝不未经详情页验证即标注「全文」——timeline API 的 text 字段可能截断，必须以详情页为准

---

## Workflow

### 输入参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|:---|:---|:---|:---|:---|
| xq_id | int | 否 | — | 雪球用户 ID（与 blogger_name 二选一；均不传则默认采集全部博主） |
| blogger_name | string | 否 | — | 博主名称，从博主控制台「雪球ID」列解析（与 xq_id 二选一；均不传则默认全部） |
| max_posts | int | 否 | 50 | 最大采集条数 |
| output_dir | path | 否 | {VAULT}/工作区/粗制品 | 输出目录（vault 相对路径 `工作区/粗制品`，见 investment-framework 路径表 ROUGH_DIR） |

**时间窗口**：不再使用固定 hours 参数。采集范围 = 博主控制台「信息截止」列（ISO 时间格式 `YYYY-MM-DDTHH:mm:ss`）→ 当前时间；精确到时间可支持同日多次采集去重（只取 info_cutoff 之后的帖子）。新增博主「信息截止」默认为半年前 17:50:00（首次采集拉半年言论）。

> 两个参数都不传 → 默认采集博主控制台中所有「雪球ID」非空的博主（逐博主执行第零步→第七步）。同时传入 → 以 xq_id 为准。

### 前置步骤：同步雪球关注列表 → 更新博主控制台

每次采集会话开始时**必须**先执行（无论单博主还是批量）。完整规则见 `references/execution-guide.md`「前置步骤」——获取用户 ID、分页拉取关注列表、与控制台对比（新增→确认后追加行 / 取关→确认后删行 / 无变动）、更新控制台 `updateDate`。此步取代规则 #12 的自动补登限制（用户明确授权从雪球关注列表同步；但 Agent 仍不得凭空捏造博主）。

### 第零步：解析雪球 ID

- 传入 `xq_id` → 直接使用
- 传入 `blogger_name` → 从博主控制台（`{VAULT_ROOT}/工作区/博主控制台.md`）匹配「博主/别名」列取「雪球ID」列；匹配不到或 ID 为空 → 报错停止
- 均未传 → 「全部博主」模式：取控制台所有「雪球ID」非空的博主，逐博主执行

### 第一步：检查 browser-act CLI 并加载运行指令

```bash
browser-act --version
browser-act get-skills core --skill-version 2.0.2
```
- CLI 不可用 → 报错停止，提示 `uv tool install browser-act-cli --python 3.12`
- **get-skills 禁止跳过**——解析输出，确认可用浏览器 ID 和已有 session

### 第三步：打开浏览器，导航到雪球用户页

会话管理（session 归属判定、创建/复用、登录验证）完整流程见 `references/execution-guide.md`「第三步」。要点：
- 按「本对话历史中是否已有我的 session」判断复用或新建（他人 session 不操作）
- 创建：`browser-act --session xq browser open {browser_id} "https://xueqiu.com/u/{xq_id}"`
- **验证登录态**：`get title` 含用户昵称 → 已登录；含「登录」→ **停止，提示用户在 Chrome 中登录雪球**

### 第四步：获取当前时间 + 提取帖子列表

1. 获取基准时间：`date "+%Y-%m-%d %H:%M"`
2. `browser-act --session {name} wait stable` + `get markdown`
3. **加载 `references/page-structure.md`** 解析：识别帖子区域、提取 post_id/时间/正文/互动、时间格式转换、置顶帖标注
4. 按时间过滤（仅保留「信息截止」之后）+ max_posts 数量限制
5. 帖子不足时滚动加载（见 `references/execution-guide.md`「第四步」）

### 第五步：截断内容补全（强制，不可跳过）

截断检测与补全的完整规则见两处权威源：
- 用户页 markdown 侧：`references/page-structure.md`「截断检测」（`[展开]()` 标记判定）
- API 采集路径侧：`references/execution-guide.md`「第五步」（timeline API text 截断判定 + 详情页补全流程）

**铁律**：详情页是全文的唯一权威来源——**禁止仅凭 API 返回即标注「全文」**，每条帖子必须经详情页验证后标记「全文」/「摘要」。引用块保留（`>` 前缀区分作者原文），Emoji 图片按 page-structure.md 规则清洗。

### 第六步：关闭浏览器

```bash
browser-act session close {name}
```
- 采集完成后关闭 session 释放资源
- 若后续还需复用（如连续采集多个博主）→ 不关闭，提示用户

### 第七步：写入输出文件

- 位置：`{output_dir}/雪球采集-{nickname}-{YYYY年M月D日}.md`
- 格式：见 Output Format
- 向用户报告摘要：采集 N 条帖子，时间范围 X ~ Y，其中 M 条补全了全文

### 第八步：更新 info_cutoff（画像 + 控制台双写）

采集完成后，将「信息截止」更新为**本次采集实际完成时间**（ISO 格式 `YYYY-MM-DDTHH:mm:ss`，如 `2026-08-04T17:50:00`；无精确时间时默认当天 `17:50:00`），双写两处：
1. **博主画像** `博主/{nickname}/{nickname}.md`：frontmatter `info_cutoff` + `updateDate`
2. **博主控制台** `工作区/博主控制台.md`：该博主行「信息截止」列 + 控制台 frontmatter `updateDate`

画像文件不存在 → 仅更新控制台，不自动创建画像。

### 采集完成即结束

本 skill 仅负责采集。产出帖子集按 `framework-rules.md` #29 例外流程，由 investment-refine **直接执行**提炼（不进原始资源、不需确认、提炼后源文件移废纸篓），精华去糟粕清单见 `references/refine-checklist.md`。采集阶段不分析内容。

> **`[原文]` 链接是画像表原文链接的唯一权威来源**：每帖输出均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})`（见 Output Format），采集阶段须确保**每帖都带 `[原文]` 链接、不得丢弃**——后续提炼填充博主画像三表「原文链接」列（言论追踪/个股买卖/预测，见 framework-rules #35）一律取自此链接，禁止填采集批次名、禁止留空。

---

## Output Format

输出为 markdown 文件（帖子集按 #29 例外流程直接进提炼，不经粗加工）。每帖为 `## N. 标题 + 正文 + 摘要行` 三件套，帖间以 `---` 分隔；摘要行标记「全文」或「摘要」：

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

## 1. {帖子标题}

{正文全文}

> 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | 全文 | [原文](https://xueqiu.com/{xq_id}/{post_id})
```

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

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 前置步骤/会话管理/滚动加载/API截断判定 | `references/execution-guide.md` | 关注列表同步、会话管理、滚动加载、API 截断判定、引用与 emoji 处理细节 | 读取 |
| 第四步解析帖子 | `references/page-structure.md` | 帖子 markdown 结构、post_id 提取、时间格式转换、互动数据解析、截断检测、引用内容处理、emoji 清洗 | 读取 |
| 采集后提炼帖子集 | `references/refine-checklist.md` | 精华去糟粕价值流水线、灰区裁决、言论追踪 4 类落位、丢弃确认清单（framework-rules #29 例外，由 investment-refine 加载） | 读取 |
| 始终 | browser-act SKILL.md + `get-skills core` 输出 | browser-act 命令参考、运行时环境状态和操作指令 | 读取 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数（xq_id、blogger_name、max_posts） |
| 2 | 博主控制台（`工作区/博主控制台.md`「雪球ID」列，blogger_name → xq_id 解析） |
| 3 | browser-act CLI（chrome 模式页面数据） |
| 4 | 雪球页面结构（`references/page-structure.md` 中的解析规则） |
| 5 | browser-act 通用文档 |

---

## 自检

- [ ] xq_id 已解析（直接传入、从博主控制台按 blogger_name 查到、或默认全部博主模式逐博主解析）且为数字？
- [ ] 浏览器通道已确认可用（browser-act 或 builtin_browser MCP）？
- [ ] 雪球已登录（页面标题含用户昵称）？
- [ ] `references/page-structure.md` + `references/execution-guide.md` 已加载用于帖子解析与执行细节？
- [ ] 当前时间已获取（`date` 命令），用于时间窗口计算？
- [ ] 置顶帖已标注原始日期，未纳入时间窗口统计？
- [ ] **每条帖子都经过详情页验证**（不存在未经详情页确认即标「全文」的情况）？
- [ ] 以"……"/"..."结尾的帖子已导航详情页确认完整性？
- [ ] type="3"（专栏文章）的帖子已通过详情页获取正文（API text 为空）？
- [ ] 每帖均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接？
- [ ] 标题使用完整首句（非硬切 20 字）？
- [ ] 输出文件 frontmatter 完整（title/source/author/date/recorded/type/status）？
- [ ] 博主画像 info_cutoff 已更新（如画像文件存在）？
