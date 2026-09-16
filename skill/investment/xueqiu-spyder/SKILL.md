---
name: xueqiu-spyder
description: |
  雪球抓取工具层。**通过 ego lite 通道**（`ego-browser nodejs` + 本地 socket 桥，
  见 `ego_bridge.js` / `ego_browser.py`）复用本机已登录雪球会话，调用
  雪球 timeline API + 详情页补全，抓取指定博主的帖子全文，输出对齐投资框架规范的
  帖子集 markdown（frontmatter + 三件套 + 发布行，含形态/全文标记/原文链接）。
  触发词：「xueqiu-spyder」「spyder 抓取」「雪球抓取」「抓取雪球」「采集雪球」
  排除条件：博主控制台同步 / info_cutoff 回写 / 帖子集提炼等框架动作由 post-fetch
  编排调用本工具，不独立执行；含「提炼」「分析」关键词时交 post-fetch / investment-refine。
license: MIT
agent_created: true
metadata:
  version: "3.0.0"
  short-description: 雪球抓取工具层（ego lite 通道复用登录态，输出帖子集标准格式）
  layer: tool
  orchestrated_by: post-fetch
compatibility: macOS / Linux
---

# 雪球抓取工具层 v3.0

## Default Stance

### 核心原则
- **采集层单一职责**：只做抓取与帖子集输出，不做框架编排（控制台同步 / info_cutoff 回写 / 帖子集提炼均不在此层）。
- **ego lite 通道复用登录态（2026-09-15 迁移；2026-09-16 收口为唯一通道）**：经 `ego-browser nodejs` 把浏览器动作转发给**本机已打开并已登录雪球的 ego lite**；ego lite 没有对外 CDP 端口，故走本地 socket 桥（`ego_bridge.js`）。**Chrome 相关代码已于 2026-09-16 整段删除**（`_launch_chrome`/`_connect_chrome`/playwright 依赖/9222 端口常量全没了）——起因是 `auto` 模式在 ego 桥超时时**静默拉起过 Google Chrome**（用户当场抓到窗口与 `--remote-debugging-port=9222 --user-data-dir=…/xueqiu-spyder/chrome-profile` 进程）。
  - **默认值 `XUEQIU_TRANSPORT=ego`**；设成别的值会直接报错并告诉你"本工具只走 ego lite"，不再有任何自动回落。
- **全文优先**：截断帖必须经详情页验证补全，未经验证不得标「全文」。
- **现场可见 + 留证（2026-09-16 用户要求）**：用户原话「**采集博主言论的时候，我需要 ego lite 的页面在前端，我才能知道有没有触发风控**」。三条落实：
  1. 采集页开在 **ego 自己的标签页**里（不藏窗口），开始与结束时自动把 ego lite 拉到前台（macOS `osascript activate`；`XUEQIU_EGO_WAKE=0` 可关）；
  2. **页签随用随关**（用户口径「随用随关，除非有必要才保留」）：会话内最多多占**一张**工作页并逐帖复用（ego 任务空间有 8 页上限，每帖新开必撞顶），**桥退出时关掉**——跑完不留页签；
  3. 命中风控/异常时**自动截图留证**，另外详情页补全每 5 条抽一帧（`XUEQIU_EGO_SHOT_EVERY`），落到 `~/.cache/xueqiu-spyder/shots/<批次>/`。
- **风控自控**：命中滑块/安全验证（`滑动|安全验证|captcha|访问验证`）时**不硬撞**——把 ego 交给用户接管、等其过完验证再自动重试本页（超时才按 WAF 中止）；**timeline 端点级封禁自动降级**（v4 → 旧版端点，见「输入参数」段）。
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

### 第二步：确认 ego lite 已打开且已登录雪球

- 先决条件：**ego lite 正在运行**，且其中已登录雪球（用户自己的浏览器，工具不负责拉起）
- CLI 可用性：`ego-browser --help` 有输出（CLI 装在 `~/.local/bin/ego-browser`）
- 自检（Python 侧一行连通性检查，等价于「登录态是否可用」）：

```bash
$PY - <<'PY'
import sys; sys.path.insert(0, "~/.agents/skills/xueqiu-spyder")
import ego_browser
b = ego_browser.EgoBridge(); b.start()
print("ego ready:", b.main_page.url)         # 期望 https://xueqiu.com/…
print("login:", b.call("evaluate", page="p1", fn="() => document.title"))
b.stop()
PY
```

- 未登录（标题不含雪球 / fetch 命中 `滑动|安全验证|captcha`）→ 停止，提示用户**在 ego lite 里登录雪球**后重跑
- 通道细节与踩坑（脚本注入、socket、ego 不继承环境变量等）见 `ego_browser.py` 模块头注释

> **Chrome 通道已删除（2026-09-16）**：`XUEQIU_TRANSPORT` 只认 `ego`；
> 旧 `chrome`/`auto` 取值一律直接报错。历史上 `auto` 曾在 ego 桥超时时静默拉起 Chrome
> （用户当场抓到进程），所以这不是"改默认值"，是把相关代码整段删掉了。

### 第二步之二：看一眼现场（采集全程保持可见）· 2026-09-16 新增

采集时**页面就在 ego lite 里开着**（不是无头、不是别的浏览器），工具会自动：

| 行为 | 说明 | 关闭方式 |
|:---|:---|:---|
| 开始/结束时把 ego 窗口拉到前台 | macOS `osascript … activate`，非 macOS 跳过 | `XUEQIU_EGO_WAKE=0` |
| 页签随用随关 | 一次采集最多多占**一张**工作页（逐帖复用它，不每帖开新页——ego 任务空间有 8 页上限）；**桥退出时把这张关掉**，跑完不留页签 | 无需配置 |
| **命中滑块 → 交给你接管** | timeline/详情页命中滑块或安全验证时，ego 置前 + 自动 `handOff()`，等你过完验证、控制权交还后**自动重试本页**（默认最长等 15 分钟） | `XUEQIU_EGO_SLIDER_WAIT_MS` 调等待时长；`0` 可关 |
| 命中风控/异常自动截图 | timeline 命中滑块/验证、详情页 405、详情页异常、翻页失败 | `XUEQIU_EGO_SHOT_DIR=`（置空） |
| 详情页每 5 条抽一帧 | 记录补全进度与偶发风控弹窗 | `XUEQIU_EGO_SHOT_EVERY=0` |

截图落在 `~/.cache/xueqiu-spyder/shots/<批次时间戳>/`，文件名含时间与原因（如 `-waf-detail-…`、`-progress-15`）。
**采集期间请把 ego lite 留在可见位置**——风控弹窗（滑块/安全验证）只在页面上出现，截图是事后核对用的，不是替代现场盯屏。

### 第三步：执行采集

```bash
$PY main.py user {xq_id} --from "{cutoff_iso}" --outfile "雪球采集-{昵称}-{日期}.md" --output "{输出目录}"
```

- 流程：翻页拉列表 → 置顶排除 + 时间窗过滤 → 截断帖详情页补全（含精确时间覆盖）→ 帖子集输出
- 登录 Chrome 内页面自身发出的带签名请求可成功翻页；裸 API 翻页被 WAF 拦截时工具抛 `CrawlerError`，按报错提示处理

### 第四步：校验输出

- 打开输出文件，核对：frontmatter 七字段齐全、每帖带 `[原文]` 链接、发布行含 `形态/全文|摘要` 标记、无 WAF 报错残留
- 不合格 → 修复或重跑；合格 → 汇报文件路径 + 采集条数 + 时间范围

### 环境变量（工具层全量）

| 变量 | 默认 | 作用 |
|:---|:---|:---|
| `XUEQIU_TRANSPORT` | **`ego`** | 只允许 ego lite（唯一通道）；任何其它取值都会直接报错 |
| `XUEQIU_EGO_SPACE` | 空 | 复用指定 ego 任务空间 id（多轮采集沿用同一个） |
| `XUEQIU_EGO_SPACE_NAME` | `xueqiu-spyder` | 新建任务空间时的名字 |
| `XUEQIU_EGO_WAKE` | `1` | 开始/结束把 ego 窗口拉到前台 |
| （页签策略固定） | — | 会话内最多一张工作页、退出即关；不再提供"保留页签"开关 |
| `XUEQIU_EGO_SHOT_DIR` | `~/.cache/xueqiu-spyder/shots` | 截图目录（置空＝不落图） |
| `XUEQIU_EGO_SHOT_EVERY` | `5` | 详情页每 N 条抽一帧（0＝关） |
| `XUEQIU_EGO_SLIDER_WAIT_MS` | `900000`（15 分钟） | 滑块交接后等用户过验证的时长；超时按 WAF 中止本轮 |
| `XUEQIU_EGO_BOOT_TIMEOUT` | `90` | 桥启动握手超时（秒） |
| `XUEQIU_EGO_LOG` | 空 | 把桥 stderr 另存一份日志（排障用） |
| `XUEQIU_DEBUG_PORT` / `XUEQIU_DEBUG_HOST` / `XUEQIU_CHROME_PATH` | 9222 / localhost / 系统 Chrome | **仅**旧 `chrome` 通道 |

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
| 运行环境/依赖 | `requirements.txt` | requests + playwright（playwright 仅旧 chrome 通道用） | 安装 |
| **ego lite 通道（默认）** | `ego_browser.py` | 起 unix socket、`-e` 注入配置启动桥、JSON Lines 协议、playwright 同签名适配 | 执行 |
| **ego 通道的浏览器侧** | `ego_bridge.js` | 在 `ego-browser nodejs` 里执行：任务空间/标签页/`page.evaluate` 转发 | 执行（由 ego_browser.py 拉起） |
| 抓取内核 | `crawler.py` | 通道选择（ego 优先）、翻页、截断补全、WAF 检测、时间覆盖 | 执行 |
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
- [ ] **ego 通道就绪**：ego lite 已打开且已登录雪球（第二步自检打印出雪球标题）？
- [ ] 日志确认走的是 ego 通道（`已连接 ego lite`）？（Chrome 回落路径 2026-09-16 已删除，日志里不该再出现任何 Chrome 字样）
- [ ] 采集时 ego lite 窗口保持**可见**（前台）——风控弹窗只在页面上出现？
- [ ] 若本轮命中滑块：是否已交接给用户（`handOff`）并在其过完验证后自动重试本页？汇报里是否说明「哪一步被滑块拦过、谁处理的」？
- [ ] 采集跑完后，ego 里**有没有多出来的页签**（应只剩本任务空间原有的 p1/p2；多出来说明桥没关干净）？
- [ ] 若本轮出现过风控/异常：`~/.cache/xueqiu-spyder/shots/<批次>/` 下是否有对应截图？汇报里是否给了路径？
- [ ] 输出为帖子集格式（frontmatter 七字段 + 三件套 + 发布行）？
- [ ] 每帖均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})` 链接？
- [ ] 置顶帖已排除、未纳入窗口统计？
- [ ] 截断帖已补全或标记「摘要」（无未经详情页验证即标「全文」）？
- [ ] 时间窗生效（--from/--to，毫秒过滤）？
- [ ] timeline 端点被封时自动降级生效（日志含「自动降级到旧版路径」）？
- [ ] 退出码语义正确（0=有产出 / 2=窗口内无新帖 / 3=窗口起点没翻到、页数不足 / 1=失败），未把「失败」或「页数不足」误当「无新帖」？
- [ ] 无 WAF/滑块报错残留、输出未被验证页污染？
