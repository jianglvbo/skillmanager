---
name: post-fetch
description: |
  雪球博主帖子采集编排层。负责：前置同步（雪球关注列表 → 看板博主控制台）、
  xq_id/时间窗解析（info_cutoff 增量）、调用 xueqiu-spyder 工具层执行采集、
  帖子集格式验收、info_cutoff 双写（画像 + 看板）、交接提炼流水线。
  触发词：「抓取雪球」「雪球帖子」「采集雪球」「xq fetch」「雪球动态」「采集帖子」
  排除条件：含「分析」「提炼」「画像」等关键词时交给 investment-refine；
  纯抓取执行（不经编排）可直接调 xueqiu-spyder。
  依赖条件：xueqiu-spyder（venv + Chrome CDP 调试端口，雪球已登录）。
  区别于 xueqiu-spyder：post-fetch 是知识框架集成编排者，spyder 是纯抓取工具层。
license: MIT
agent_created: true
metadata:
  version: "5.0.0"
  short-description: 雪球博主帖子采集编排层（编排 xueqiu-spyder + 框架集成）
compatibility: 通用
---

# 雪球帖子采集编排 v5.0

## Default Stance

### 核心原则
- **编排-工具分层（2026-09-09 重构定案）**：采集执行委托 `xueqiu-spyder`（CDP 复用已登录 Chrome）；post-fetch 只做框架集成（控制台同步 / 参数解析 / 格式验收 / info_cutoff 双写 / 提炼交接），**不直接操作浏览器**。
- **用户页方案 + 详情页补全（2026-08-15 定案，由 spyder 承载）**：完整采集走「timeline 翻页 + 详情页补全」，工具层内建 WAF/滑块检测，命中即停不硬撞。
- **全文优先**：每条帖子必须经完整性验证，未经详情页确认不得标注「全文」（spyder 已实现，验收复核）。
- **容错优先**：单帖失败不影响整批；置顶帖排除、不纳入时间窗口统计。
- **独立可用**：用户直接输入参数即可运行，不依赖 pipeline。
- **本链路产出为纯文本（2026-09-03《博主言论设计》§采集2）**：写入前逐条净化（删 `![[...]]`/`![](url)`/`<img>`/裸图 URL/表情占位）；`author` 在页脚剥离后解析，值中不得含 `发布于|来自|关注|：|:`，判不出置 `Unknown` 标待复核；每帖记 `发帖时间`（详情页绝对时间）+ `形态`（回复/短文/长文）。**不在采集阶段猜内容分类、不写观点时间**（content_type/view_date 由 investment-refine 判定）。
- **收尾必清理**：spyder 退出即释放 CDP 连接；编排层不遗留任何浏览器自动化进程。

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不直接 curl / requests 裸调雪球 API（WAF 拦截；由 spyder 内建检测兜底）
- 绝不在采集阶段分析或总结帖子内容
- 绝不将置顶帖归入采集窗口
- 绝不未经详情页验证即标注「全文」
- **绝不跳过格式验收**：spyder 输出必须对照 `references/output-format.md` 复核后才落 vault

---

## Workflow

### 输入参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|:---|:---|:---|:---|:---|
| xq_id | int | 否 | — | 雪球用户 ID（与 blogger_name 二选一；均不传则默认采集全部博主） |
| blogger_name | string | 否 | — | 博主名称，从看板博主控制台（MySQL bloggers 表 `xueqiu_id` 字段）解析（与 xq_id 二选一；均不传则默认全部） |
| max_posts | int | 否 | 50 | 最大采集条数 |
| output_dir | path | 否 | {VAULT}/工作区/粗制品 | 输出目录（vault 相对路径 `工作区/粗制品`，见 investment-framework 路径表 ROUGH_DIR） |

**时间窗口**：采集范围 = 看板博主控制台「信息截止」（MySQL bloggers 表 `info_cutoff`；API /api/bloggers/live 可读）（ISO `YYYY-MM-DDTHH:mm:ss`）→ 当前时间；精确到时间支持同日多次采集去重。新增博主默认半年前 17:50:00。

> 两参均不传 → 逐博主执行看板中所有「雪球ID」非空博主。同时传入 → 以 xq_id 为准。

### 前置步骤：同步雪球关注列表 → 更新看板博主控制台

每次采集会话开始**必须**先执行（无论单博主还是批量）。完整规则见 `references/execution-guide.md`「前置步骤」——获取用户 ID、分页拉取关注列表、与看板对比（新增→确认后登记 / 取关→报告由用户看板删除 / 无变动）、更新 `updateDate`。

**残留检测（2026-08-14）**：比对看板登记名与 `博主/` 层文件夹——看板已移除但博主层仍有文件 → 报告并询问清理或迁移（防未登记博主悬空）。

**info_cutoff 一致性（2026-08-14）**：本次「信息截止」变更的博主，核对画像 frontmatter `info_cutoff` 同值，不一致则同步（规则 #36）。

### 第零步：解析雪球 ID

- 传入 `xq_id` → 直接使用
- 传入 `blogger_name` → 从看板博主控制台（`GET /api/bloggers/live`，匹配 name/alias 取 `xueqiuId`）；匹配不到或 ID 为空 → 报错停止
- 均未传 → 「全部博主」模式：取看板所有「雪球ID」非空博主，逐博主执行

### 第一步：检查工具层环境

```bash
PY=~/.workbuddy/binaries/python/envs/xueqiu-spyder/bin/python
$PY -c "import requests, playwright"        # 依赖就绪
curl -s http://127.0.0.1:9222/json/version  # CDP 可达（端口被占用时按 spyder 约定换 XUEQIU_DEBUG_PORT）
```
- 依赖缺失 → `pip install -r {xueqiu-spyder 目录}/requirements.txt`（本地安装位置 `~/.workbuddy/skills/investment/xueqiu-spyder/`）
- CDP 不可达 → 提示按 xueqiu-spyder 启动调试 Chrome 并登录雪球
- 工具层完整流程与参数见 `xueqiu-spyder` SKILL.md（加载读取）

### 第二步：执行采集（委托 xueqiu-spyder）

```bash
$PY {xueqiu-spyder}/main.py user {xq_id} \
  --from "{info_cutoff}" --to "{now_iso}" --max-pages {N} \
  --outfile "雪球采集-{nickname}-{YYYY年M月D日}.md" --output "{输出目录}"
```
- `now_iso` 先取：`date "+%Y-%m-%dT%H:%M:%S"`
- **`{N}` 按窗口长度取**（硬约束，不得沿用默认 10）：≤24h→**3**、≤7 天→**5**、>7 天→10
- **批量节流**：每处理 10 位博主暂停 60 秒再继续
- 逐帖：截断补全（详情页）→ 形态判定 → 置顶排除 → 时间窗过滤 → 帖子集输出（spyder 内部完成）
- **端点封禁自动降级**：v4 timeline 被 WAF 405 时 spyder 自动切旧版端点，无需干预；降级后仍失败才按 WAF 报错处理（稍后重试 / 人工过验证），不硬撞

### 第三步：格式验收（强制，不可跳过）

打开 spyder 输出文件，对照 `references/output-format.md` 复核：
- frontmatter 七字段完整、type=`帖子集`、status=`待提炼`（含摘要帖则 `待提炼-含摘要`）
- 每帖三件套齐全：`## N. 标题` + 正文 + 发布行（含 `形态`、`全文/摘要` 标记、`[原文]` 链接）
- 纯文本净化已生效（无 `![[`、`![](url)`、`<img>`、`[表情]` 占位残留；Unicode emoji 正文保留）
- 不合格 → 修复后落 vault；合格 → 进入第四步

### 第三步之二：原文落库 post_history（2026-09-11 新增，强制）

**目的只有一个：避免重采。** 采集产物（帖子集 md）会随粗制品清理而消失，原文一旦没留档，日后想回顾/重新提炼就只能重抓——本轮就为此回采了 210 条、还因速率过快触发 WAF 405。故**每次采集验收通过后立即落库**：

```bash
node ~/Project/investment-console/scripts/import-post-history.js "<帖子集.md>"    # 可传多个文件
# 输出：新增 N | 更新 M | 无变化 K | 跳过（摘要 a / 无链接或空正文 b / 博主未建档 c）
```

| 规则 | 说明 |
|:---|:---|
| 幂等 | 以 `url_hash`（md5 原文链接）判重：同帖再采 → 内容没变记「无变化」（只刷新抓取时间与互动数），内容变了记「更新」并覆盖原文 |
| **摘要帖不入库** | 带「摘要」标记的帖内容残缺，**故意不存**——这样下次采集仍会重新抓取，不会被误判为"已有" |
| **无链接不入库** | 缺 `[原文]` 链接 = 来源不可回溯（规则 #35），跳过 |
| 博主未建档 | 会报错跳过；需先在博主控制台登记（规则 #12） |
| 落库时机 | 第三步验收通过后、第四步报告前；报告里带上「原文留档 N 条」 |

**采集前可先查重**（可选，用于补采/回补场景）：MCP `post_history` 的 `action=check`（传 blogger + from/to）会返回该博主窗口内已留档的帖子清单（含 `platformPostId`、`contentHash`），据此跳过已采、只补缺口。

### 第四步：向用户报告摘要

采集 N 条帖子，时间范围 X ~ Y，其中 M 条补全了全文，输出文件路径。

### 第五步：更新 info_cutoff（画像 + 看板双写）

> **前置条件（2026-09-09 用户硬约束：保证不漏采）**：**只有该博主本次采集真正完成，才能更新其 info_cutoff**。判定依 spyder 退出码：
>
> | spyder 退出码 | 含义 | 是否更新 cutoff |
> |:---|:---|:---|
> | `0` | 采集成功、已产出帖子集 | ✅ 更新 |
> | `2` | 采集成功、**窗口内无新帖**（已确认无内容） | ✅ 更新 |
> | `1` | **采集失败**（WAF 封禁 / 登录失效 / 异常中断，未产出） | ❌ **禁止更新** |
>
> **失败时绝不更新**——否则下次采集从新 cutoff 起算，会永久漏掉本次未采到的帖子。失败博主须报告用户，待重试成功后再更新；重试前其 cutoff 保持原值（宁可重复采，不可漏采）。

将「信息截止」更新为**本次采集实际完成时间**（ISO `YYYY-MM-DDTHH:mm:ss`，无精确时间默认当天 `17:50:00`）：
1. **博主画像** `博主/{nickname}/{nickname}.md`：frontmatter `info_cutoff` + `updateDate`
2. **看板 MySQL** `bloggers.info_cutoff`（经 `scripts/xq_update_cutoff.py` 回写，脚本同时更新画像）

画像文件不存在 → 仅更新看板，不自动创建画像。

**批量采集收尾核对（硬约束）**：批量结束后必须逐位核对「本次是否采集完成」，只对退出码 0/2 的博主执行双写；退出码 1 的博主列入「待重试清单」报告用户，**其 cutoff 保持原值不动**。

### 采集完成即结束

本 skill 仅负责采集编排。产出帖子集按 `framework-rules.md` #29 例外流程，由 investment-refine **直接执行**提炼（不进原始资源、不需确认、提炼后源文件移废纸篓），精华去糟粕清单见 `references/refine-checklist.md`。采集阶段不分析内容。

> **`[原文]` 链接是画像表原文链接的唯一权威来源**：每帖输出均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})`，采集阶段须确保**每帖都带、不得丢弃**——后续提炼填充博主画像三表「原文链接」列（framework-rules #35）一律取自此链接，禁止填采集批次名、禁止留空。

---

## Output Format

输出为 markdown 文件（帖子集按 #29 例外直接进提炼，不经粗加工）。**完整格式规范——frontmatter 字段表、三件套结构、摘要行字段、status 取值（待提炼/待提炼-含摘要）、铁律——一律见 `references/output-format.md`**，字段名与取值严格按该文件、不得自创。

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| **编排执行细节/前置同步/风控背景** | `references/execution-guide.md` | 关注列表同步（browser-act 脚本）、工具层调用模板、时间窗、验收规则、风控知识 | 读取 |
| 格式验收/输出规范 | `references/output-format.md` | 帖子集 frontmatter/三件套/字段表/status/原文链接铁律 | 读取 |
| 采集后提炼帖子集 | `references/refine-checklist.md` | 精华去糟粕价值流水线、灰区裁决、言论追踪落位（framework-rules #29 例外，investment-refine 加载） | 读取 |
| **关注列表同步** | `scripts/xq_sync_console.py` | 同步 + 看板对比（dry-run/--apply；依赖 browser-act + 已登录 session） | **执行** |
| **info_cutoff 双写** | `scripts/xq_update_cutoff.py` | 画像 + 看板 MySQL 双写（参数：nickname/ISO时间） | **执行** |
| 存量批次净化 | `scripts/clean_legacy_batches.py` | 旧批次帖子集清洗到纯文本基线（--dry-run/--dir） | **执行** |
| 摘要帖二次补全 | `scripts/xq_refetch_summary.py` | 标「摘要」帖导航详情页补全（依赖 browser-act；--dir/--date） | **执行** |
| **采集执行（工具层）** | xueqiu-spyder SKILL.md + main.py | 抓取 CLI、参数、输出格式（编排时加载） | 读取/执行 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数（xq_id、blogger_name、max_posts） |
| 2 | 看板博主控制台（MySQL bloggers 表，`GET /api/bloggers/live`） |
| 3 | xueqiu-spyder 工具层输出（帖子集文件） |
| 4 | `references/output-format.md`（验收规范） |
| 5 | 雪球页面/API 实际结构（由 spyder 解析，本层不持有） |

---

## 自检

- [ ] 前置同步已执行（关注列表 ↔ 看板对比，含残留/一致性检测）？
- [ ] xq_id 已解析（直接传入 / 看板按 blogger_name 查 / 全部博主模式）且为数字？
- [ ] 工具层环境就绪（venv 依赖 + Chrome CDP 可达 + 雪球已登录）？
- [ ] xueqiu-spyder SKILL.md 已加载（含其参数与自检）？
- [ ] 采集委托 spyder 执行（`main.py user --from {cutoff} --to {now}`），未绕过工具层直接操作浏览器？
- [ ] **`--max-pages` 按窗口长度取值**（≤24h→3、≤7 天→5、>7 天→10），未沿用默认 10？
- [ ] **批量采集每 10 位暂停 60 秒**（节流）？
- [ ] **采集产物已落 post_history**（`import-post-history.js`，摘要帖与无链接帖按规则跳过）？
- [ ] 时间窗口 = info_cutoff → 当前，置顶帖已排除？
- [ ] spyder 输出已对照 output-format.md 完成格式验收（frontmatter/三件套/发布行/纯文本）？
- [ ] 每帖均带 `[原文]` 链接？
- [ ] 标「摘要」的帖未混入「全文」标记？status 与摘要行一致？
- [ ] **仅对采集完成（spyder 退出码 0/2）的博主双写 info_cutoff**；失败（退出码 1）者**保持原 cutoff 不动**并列入待重试清单报用户（防漏采）？
- [ ] 无浏览器自动化进程遗留？
