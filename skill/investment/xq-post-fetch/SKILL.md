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
  version: "4.5.0"
  short-description: 通过 browser-act chrome 模式采集雪球博主帖子全文
compatibility: 通用
---

# 雪球帖子采集 v4.5

## Default Stance

### 核心原则
- **浏览器通道唯一**：通过 browser-act CLI（chrome 模式）采集，复用 Chrome 登录态。browser-act 优先；WebSocket 连接失败时降级到 builtin_browser MCP。
- **用户页方案优先（2026-08-15 定案）**：完整采集走「用户页滚动加载 + 详情页补全」，**不用 timeline API 翻页**——API 分页裸 URL 被 WAF 拦截、连续请求触发滑块（详见 execution-guide 第〇章「风控规避」）。
- **全文优先**：每条帖子必须经过完整性验证，未经详情页确认的不得标注「全文」。
- **容错优先**：单帖失败不影响整批；置顶帖标注原始日期，不纳入时间窗口统计。
- **独立可用**：用户直接输入参数即可运行，不依赖 pipeline。
- **确定性优先**：帖子解析按 `references/page-structure.md` 的 pattern 执行，不靠自由发挥。
- **收尾必清理（2026-08-27 新增，硬约束）**：采集全部结束（session 关闭）后，**必须清理采集产生的 headless Chrome 进程**（`--headless=new`，browser-act chrome 模式启动的自动化实例），禁止遗留——教训：遗留 headless 进程曾阻塞用户图形界面 Chrome 启动（详见第六步清理命令）。

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不直接 curl / requests 调 API（阿里云 WAF 拦截）
- **绝不用裸 URL 翻页调 timeline API**（`page>=2` 被 WAF 拦截，走用户页滚动）
- **绝不在采集任务运行时并行操作同一 session**（争用会中断任务；并行需开第二个 session）
- 绝不在采集阶段分析或总结帖子内容
- 绝不跳过截断检测（长文必须补全全文）
- 绝不将置顶帖归入「今日」时间范围（置顶帖 pinned 字段不可靠，按完整日期 + 「置顶」标记识别）
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

**残留检测（2026-08-14 新增）**：同步完成后比对控制台登记名与 `博主/` 层文件夹——发现「控制台已移除但博主层仍有文件/文件夹」的博主，向用户报告并询问清理或迁移（2026-08-10 同步后曾遗留 APEC蓝天/douhun/james_nj/景风长赢 4 人，直至 8/14 审查才暴露）。

**info_cutoff 一致性（2026-08-14 新增）**：本次控制台「信息截止」变更的博主，核对对应画像 `博主/<名>/<名>.md` frontmatter `info_cutoff` 是否同值，不一致则同步（规则 #36，防画像-控制台失同步；2026-08-14 曾批量失同步 29 处）。

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

### 第四步：获取当前时间 + 提取帖子列表（用户页方案）

1. 获取基准时间：`date "+%Y-%m-%d %H:%M"`
2. `browser-act --session {name} navigate "https://xueqiu.com/u/{xq_id}"` + 等待 4s + `get markdown`
3. **加载 `references/page-structure.md`** 解析：识别帖子区域、提取 post_id/时间/正文/互动、时间格式转换（含完整日期格式）、置顶帖识别。**时间戳用 `re.search` 全局搜索，禁止行首锚定**
4. 按时间过滤（仅保留「信息截止」之后，排除置顶帖）+ max_posts 数量限制
5. 帖子不足时**滚动加载**：`scroll down --amount 2500` + 等待 2s + 重新 `get markdown`（滚动触发带签名请求，不触发 WAF；详见 execution-guide 第〇章）

### 第五步：截断内容补全（强制，不可跳过）

截断检测与补全规则见 `references/page-structure.md`「截断检测」（`[展开]()` 标记判定）+ `references/execution-guide.md`「第五步」：

**补全流程（详情页 HTML，非 API）**：
```bash
browser-act --session {name} navigate "https://xueqiu.com/{xq_id}/{post_id}"
browser-act --session {name} wait stable
browser-act --session {name} get markdown
```
- 提取「来源：雪球App」与「风险提示」之间正文（完整全文）
- 详情页同时提供精确发布时间（`发布于 YYYY-MM-DD HH:MM`），覆盖用户页的模糊时间
- 补全后标记：「全文」（经详情页验证）vs「摘要」（详情页也无法获取全文）
- **禁止用 `statuses/show.json` API 补全**（连续请求触发滑块；详情页 HTML 实测零风控）

**铁律**：详情页是全文的唯一权威来源——**禁止仅凭 API 返回即标注「全文」**，每条帖子必须经详情页验证后标记「全文」/「摘要」。引用块保留（`>` 前缀区分作者原文），Emoji 图片按 page-structure.md 规则清洗。

### 第六步：关闭浏览器

```bash
browser-act session close {name}
```
- 采集完成后关闭 session 释放资源
- 若后续还需复用（如连续采集多个博主）→ 不关闭，提示用户

**headless 进程清理（2026-08-27 新增，硬约束）**：**全部采集任务结束后**（单博主完成或批量最后一个博主完成后），必须执行以下清理，确认 headless 进程已清空：

```bash
# 仅清理采集用的 headless 自动化实例（精确匹配 headless=new，绝不误杀用户 GUI Chrome）
pkill -f "headless=new" 2>/dev/null; sleep 1; pgrep -f "headless" | wc -l   # 输出必须为 0
```
- 输出非 0 → 继续 `pkill -9 -f "headless=new"` 后再验证
- **禁止遗留**：采集结束但 headless 进程残留 = 违规（2026-08-27 曾因遗留 14 个 headless 进程阻塞用户 GUI Chrome 启动）

### 第七步：写入输出文件

- 位置：`{output_dir}/雪球采集-{nickname}-{YYYY年M月D日}.md`
- 格式：见 Output Format
- 向用户报告摘要：采集 N 条帖子，时间范围 X ~ Y，其中 M 条补全了全文

**本链路产出为纯文本（2026-09-03《博主言论设计》§采集2 + 方案 v2 §3）**：

- 写入前逐条净化：删除 `![[...]]`、`![](url)`、`<img>`、裸图片 URL，以及表情（含 `[表情名]` 占位——**不留占位**）；Unicode 文字 emoji 属正文，保留
- 剥离雪球页脚噪声：`发布于…／来自…／关注`、积分余额、风险提示
- `author` 解析必须在页脚剥离**之后**；值中不得含 `发布于|来自|关注|：|:`，命中即截断，判不出置 `Unknown` 并标待复核（历史脏值会让博主头像与归属失效）
- 每条帖子记两个字段供提炼使用：`发帖时间`（详情页绝对时间，相对表述按现有折算表换算）、`形态`（回复 / 短文 / 长文，按"回复 @／引用块"与长度客观判定）
- **不在采集阶段猜内容分类，也不写观点时间**——`content_type`（六分法）与 `view_date`（观点时间）由 `investment-refine` 依语义判定；采集只做纯文本化与时间/形态记录

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

输出为 markdown 文件（帖子集按 #29 例外流程直接进提炼，不经粗加工）。完整格式规范（frontmatter/三件套/字段表/铁律）见 `references/output-format.md`，核心模板：

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

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| **风控规避/主路径/会话管理/滚动加载** | `references/execution-guide.md` | **WAF 与滑块规避（第〇章）、用户页采集主路径、chrome 启动失败处理、session 独占铁律**、关注列表同步、API 截断判定、引用与 emoji 处理 | 读取 |
| 第四步解析帖子 | `references/page-structure.md` | 帖子 markdown 结构、post_id 提取、**时间戳前缀陷阱、完整日期格式、置顶帖识别**、截断检测、引用内容处理、emoji 清洗 | 读取 |
| 采集后提炼帖子集 | `references/refine-checklist.md` | 精华去糟粕价值流水线、灰区裁决、言论追踪 4 类落位、丢弃确认清单（framework-rules #29 例外，由 investment-refine 加载） | 读取 |
| **逐博主完整采集** | `scripts/xq_user_collect.py` | 用户页滚动 + 详情页补全采集器（参数：xq_id/nickname/cutoff/outfile），实战验证零风控 | **执行** |
| **info_cutoff 双写** | `scripts/xq_update_cutoff.py` | 画像 + 控制台双写更新（参数：nickname/ISO时间） | **执行** |
| 输出格式规范 | `references/output-format.md` | 帖子集 frontmatter/三件套/字段表/原文链接铁律 | 读取 |
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
- [ ] 浏览器通道已确认可用（browser-act 或 builtin_browser MCP）？chrome 模式启动失败时是否已处理本地 Chrome 占用（关闭后重试）？
- [ ] 雪球已登录（页面标题含用户昵称）？
- [ ] `references/page-structure.md` + `references/execution-guide.md` 已加载（含第〇章风控规避）？
- [ ] 采集路径是否为**用户页滚动 + 详情页补全**（未用裸 URL 翻页调 API）？
- [ ] 采集任务运行时是否**未并行操作同一 session**（需并行时开了第二个 session）？
- [ ] 当前时间已获取（`date` 命令），用于时间窗口计算？
- [ ] 置顶帖已识别排除（按完整日期 + 「置顶」标记，**不依赖 pinned 字段**）？未纳入时间窗口统计？
- [ ] 时间戳解析是否用 `re.search` 全局搜索（未用行首锚定导致漏采）？
- [ ] **每条帖子都经过详情页验证**（不存在未经详情页确认即标「全文」的情况）？
- [ ] 以"……"/"..."结尾的帖子已导航详情页确认完整性？
- [ ] type="3"（专栏文章）的帖子已通过详情页获取正文（API text 为空）？
- [ ] 每帖均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接？
- [ ] 标题使用完整首句（非硬切 20 字）？
- [ ] 输出文件 frontmatter 完整（title/source/author/date/recorded/type/status）？
- [ ] 博主画像 info_cutoff 已更新（如画像文件存在）？
- [ ] **headless Chrome 进程已清理**（`pgrep -f "headless"` 无输出；采集结束禁止遗留，防阻塞 GUI Chrome）？
