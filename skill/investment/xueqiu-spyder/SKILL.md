---
name: xueqiu-spyder
description: |
  雪球抓取工具层。通过 Chrome CDP（调试端口）复用本机已登录 Chrome 会话，调用
  雪球 timeline API + 详情页补全，抓取指定博主的帖子全文，输出对齐投资框架规范的
  帖子集 markdown（frontmatter + 三件套 + 发布行，含形态/全文标记/原文链接）。
  触发词：「xueqiu-spyder」「spyder 抓取」「雪球抓取」「抓取雪球」「采集雪球」
  排除条件：博主控制台同步 / info_cutoff 双写 / 帖子集归档与提炼等框架动作由
  post-fetch 编排调用本工具，不独立执行；含「提炼」「画像」「归档」关键词时交
  post-fetch / investment-refine。
license: MIT
agent_created: true
metadata:
  version: "2.0.0"
  short-description: 雪球抓取工具层（CDP 复用登录态，输出帖子集标准格式）
  layer: tool
  orchestrated_by: post-fetch
compatibility: macOS / Linux
---

# 雪球抓取工具层 v2.0

## Default Stance

### 核心原则
- **采集层单一职责**：只做抓取与帖子集输出，不做框架编排（控制台同步 / info_cutoff 双写 / 归档提炼均不在此层）。
- **CDP 复用登录态**：连接本机已登录 Chrome 的调试端口（默认 9222，主机名默认 `localhost`——Chrome 152 起不接受 `127.0.0.1`；端口用 `XUEQIU_DEBUG_PORT` 覆盖、主机名用 `XUEQIU_DEBUG_HOST` 覆盖），不重复登录、不依赖 browser-act。
- **全文优先**：截断帖必须经详情页验证补全，未经验证不得标「全文」。
- **风控自控**：WAF/滑块检测（`滑动|安全验证|captcha|访问验证`）命中即抛错停止，不硬撞；**timeline 端点级封禁自动降级**（v4 → 旧版端点，见「输入参数」段）。
- **时间窗精确**：`--from/--to` 毫秒级过滤；置顶帖识别排除，不纳入窗口统计。
- **输出对齐帖子集规范**：frontmatter 七字段 + 每帖三件套（标题/正文/发布行），供 post-fetch 直接交接提炼。

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不绕过登录态裸调 API（WAF 拦截）；绝不连续翻页硬撞滑块
- 绝不在采集阶段分析/提炼帖子内容（content_type/view_date 由 investment-refine 判定）
- 绝不未经详情页验证即标「全文」——API text 可能截断，以详情页为准
- 绝不删除原文 emoji 与引用结构（`//@` 引用保留原文嵌套；表情图转 `[表情名]` 占位文本保留）
- 绝不把置顶帖归入采集窗口

---

## Workflow

### 输入参数（user 子命令，post-fetch 编排主路径）

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | str/int | 是 | 雪球用户 ID 或用户名（用户名自动搜索解析） |
| --from | str | 否 | 起始时间 `YYYY-MM-DD` 或 `YYYY-MM-DDTHH:MM:SS`（对齐 info_cutoff 增量窗口） |
| --to | str | 否 | 截止时间（默认当前） |
| --days | int | 否 | 相对窗口（与 --from 互斥，--from 优先；兼容旧用法） |
| --max-pages | int | 否 | 最大翻页数（默认 10；**编排层须按窗口长度下调**：≤24h→3、≤7天→5，见 post-fetch execution-guide） |
| --outfile | str | 否 | 输出文件名（默认 `雪球采集-{昵称}-{日期}.md`） |
| --output | path | 否 | 输出目录（默认 ./output） |
| --column | flag | 否 | 仅抓取专栏文章 |

**单帖接口 `statuses/show.json` 限流（2026-09-11 实测，硬约束）**：按 URL 取单帖正文/形态时走此接口——

| 项 | 实测 |
|:---|:---|
| 危险区 | **≈1.1 req/s 连续约 200 次 → 405**（返回 `text/html` 验证页，非 JSON） |
| 安全速率 | **`sleep ≥1.2s` + 每 50 次停 45s（≈0.7 req/s）**；1.0s + 每 100 次停 30s 连续 160 次无封禁 |
| 退避 | 命中 405 → **暂停 300s** 重试同 id；**连续 3 次限流即中止本轮**、保留进度稍后续跑 |
| 进度语义 | **只有真正取到内容的才记进度**；限流失败必须留待重跑（曾把 488 条失败静默记为已处理，缺口被掩盖） |

> 与 timeline 端点同属阿里云 WAF 保护，完整实测依据与批量节流表见 post-fetch `references/execution-guide.md`。

**产物交接（2026-09-12 变更）**：本工具产出的「帖子集」markdown 是**临时载体**——post-fetch **第三步之二**用 `~/Project/investment-console/scripts/import-post-history.js` 把它落进 `post_history`（摘要帖与无链接帖不入库），第三步之三做入库校验后即清理（`--rm`）。**输出目录用 vault 外的临时目录**（默认 `~/.cache/xueqiu-spyder/out`），采集产物不再写进 vault 的 `工作区/粗制品/`；`post_history` 既是采集落点也是提炼前的唯一原文来源。

**timeline 端点自动降级（2026-09-09 固化）**：`v4/statuses/user_timeline.json` 被阿里云 WAF 对该 IP 临时封禁（405，页面自身带签名请求亦 405）时，crawler **自动切到旧版 `/statuses/user_timeline.json`** 重试本页（数据一致，仅每页上限由 50 降为 20），只降级一次，无需人工干预。可用环境变量覆盖：
- `XUEQIU_TIMELINE_URL`：主端点（默认 v4）
- `XUEQIU_TIMELINE_URL_FALLBACK`：降级端点（默认旧版）
- `XUEQIU_POSTS_COUNT`：每页条数（默认 20，两端点兼容值）

### 第一步：确认运行环境

```bash
# venv 解释器（依赖已装：requests + playwright）
PY=${XUEQIU_PY:-$(cat ~/.config/xueqiu-spyder/python 2>/dev/null || echo python3)}   # 本机 venv 路径存 ~/.config/xueqiu-spyder/python（0600，不进仓库）
$PY --version && $PY -c "import requests, playwright"
```

### 第二步：确认 Chrome CDP 可达且已登录

- Chrome 需带调试端口启动：`--remote-debugging-port=9222`（端口可被占用时用 `XUEQIU_DEBUG_PORT` 覆盖）；启动失败处理见 crawler.py docstring
- **主机名必须用 `localhost`（2026-09-12 实测，Chrome 152）**：DevTools HTTP 端点只接受 `Host: localhost`，用 `127.0.0.1` 直连 `/json/version` 返回 404（`connect_over_cdp` 报 "Unexpected status 404"）。crawler 默认 `localhost`，可用 `XUEQIU_DEBUG_HOST` 覆盖
- 验证：`curl -s http://localhost:{PORT}/json/version` 返回 JSON；`curl -s http://localhost:{PORT}/json/list` 里能看到「我的首页 - 雪球」页面 = 已登录
- 未登录 → 停止，提示用户先在 Chrome 登录雪球

### 第三步：执行采集

```bash
$PY main.py user {xq_id} --from "{cutoff_iso}" --outfile "雪球采集-{昵称}-{日期}.md" --output "{输出目录}"
```

- 流程：翻页拉列表 → 置顶排除 + 时间窗过滤 → 截断帖详情页补全（含精确时间覆盖）→ 帖子集输出
- 登录 Chrome 内页面自身发出的带签名请求可成功翻页；裸 API 翻页被 WAF 拦截时工具抛 `CrawlerError`，按报错提示处理

### 第四步：校验输出

- 打开输出文件，核对：frontmatter 七字段齐全、每帖带 `[原文]` 链接、发布行含 `形态/全文|摘要` 标记、无 WAF 报错残留
- 不合格 → 修复或重跑；合格 → 汇报文件路径 + 采集条数 + 时间范围

**退出码约定（2026-09-09 固化，编排层据此决定是否更新 info_cutoff）**：

| 退出码 | 含义 | 编排层动作 |
|:---|:---|:---|
| `0` | 采集成功，已产出帖子集 | 可更新 info_cutoff |
| `2` | 采集成功，**窗口内无新帖**（确认无内容） | 可更新 info_cutoff |
| `3` | **窗口起点没翻到**（页数不足，最旧帖仍比窗口起点新） | **禁止更新 cutoff**，加大 `--max-pages` 重跑 |
| `1` | **失败**（WAF 封禁 / 登录失效 / 异常，未产出） | **禁止更新 cutoff**（防漏采） |

> 退出码 2 与 1 必须严格区分：「无新帖」是正常完成，「失败」是未完成——混为一谈会导致漏采（编排层误以为已采完而推进 cutoff）。
>
> **退出码 3（2026-09-12 新增，实战教训）**：`--max-pages` 太小（如 4 页=80 条）时，高产博主的时间线根本没翻到窗口起点，过滤后 0 条会被误报成「无新帖」（退出码 2）。实测：雪月霜 09-08 窗口 4 页判定无帖，加到 15 页后抓到 19 条。判据是**本轮最旧帖的 created_at 是否 ≤ 窗口起点**——大于即页数不足。高产博主（日均 20 条以上）请按 `窗口天数 × 日均条数 ÷ 20 + 2` 估算页数。

### stock / search 子命令（独立能力，不经 post-fetch）

```bash
$PY main.py stock SZ002738 --min-reply 20 --max-pages 10   # 个股大V观点报告
$PY main.py search 治雨                                       # 搜用户 ID
```

---

## Output Format

帖子集 markdown（对齐 post-fetch `references/output-format.md`）：

```markdown
---
title: "雪球帖子采集：{nickname} {YYYY年M月D日}"
source: "https://xueqiu.com/u/{xq_id}"
author: "{nickname}"
date: "{YYYY年M月D日}"
recorded: "{YYYY年M月D日}"
type: "帖子集"
status: "待提炼"        # 含摘要帖时 "待提炼-含摘要"
tags: []
---

## 1. {帖子标题}

{正文全文}

> 发布：{YYYY年M月D日 HH:MM} | 形态：{回复|短文|长文|专栏} | 转发 {n} | 回复 {n} | 点赞 {n} | {全文|摘要} | [原文](https://xueqiu.com/{xq_id}/{post_id})
```

形态客观判定：含 "回复 @"/引用块 → 回复；原创 <300 字 → 短文；≥300 字或含分段 → 长文；专栏文章 → 专栏。

---

## Relative Files

| 场景 | 文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 运行环境/依赖 | `requirements.txt` | requests + playwright | 安装 |
| CDP 抓取内核 | `crawler.py` | Chrome CDP 连接、翻页、截断补全、WAF 检测、时间覆盖 | 执行 |
| 形态/emoji/观点分析 | `analyzer.py` | 形态判定、`//@` 保留、表情转占位、Opinion 结构 | 执行 |
| 帖子集生成 | `report.py` | frontmatter + 三件套 + 发布行输出 | 执行 |
| CLI 入口/时间窗 | `main.py` | 子命令分发、--from/--to 解析 | 执行 |
| API/参数常量 | `config.py` | 端点、延迟、翻页默认值 | 读取 |
| 框架输出规范 | post-fetch `references/output-format.md` | frontmatter/三件套/字段表/铁律（编排层持有） | 读取 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数 / post-fetch 编排传入参数（user_id、--from/--to、--outfile） |
| 2 | 环境变量 `XUEQIU_DEBUG_PORT` / `XUEQIU_DEBUG_HOST` / `XUEQIU_CHROME_PATH`（本机覆盖默认） |
| 3 | `config.py` 默认值 |
| 4 | 雪球页面/API 实际结构 |

---

## 自检

- [ ] venv 依赖可用（requests + playwright import 通过）？
- [ ] Chrome CDP 可达（`/json/version` 返回 JSON）且已登录雪球？
- [ ] 输出为帖子集格式（frontmatter 七字段 + 三件套 + 发布行）？
- [ ] 每帖均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接？
- [ ] 置顶帖已排除、未纳入窗口统计？
- [ ] 截断帖已补全或标记「摘要」（无未经详情页验证即标「全文」）？
- [ ] 时间窗生效（--from/--to，毫秒过滤）？
- [ ] timeline 端点被封时自动降级生效（日志含「自动降级到旧版路径」）？
- [ ] 退出码语义正确（0=有产出 / 2=窗口内无新帖 / 3=窗口起点没翻到、页数不足 / 1=失败），未把「失败」或「页数不足」误当「无新帖」？
- [ ] 无 WAF/滑块报错残留、输出未被验证页污染？
