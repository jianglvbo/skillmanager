# 采集编排执行细节指南

> 本文件承载 post-fetch Workflow 的完整执行细节（前置同步、工具层调用、时间窗、格式验收、风控知识）。
> SKILL.md 仅保留步骤摘要骨架，细节一律以本文件为准；采集执行由 xueqiu-spyder 承载，本层不持有页面解析规则（2026-09-09 重构，page-structure.md 已退役）。
> 权威规则：`framework-rules.md` #12（博主补登/移除例外）、#29（帖子集例外流程）、#35（原文链接必填）。
> 2026-09-09 重构：编排-工具分层（post-fetch 编排 → xueqiu-spyder 抓取），替代 browser-act 直采路径。

---

## 〇、风控知识背景（spyder 已内建检测，编排层须知）

雪球对采集有**两层反爬**，xueqiu-spyder 工具层内建 WAF/滑块检测（命中即抛 `CrawlerError` 停止），编排层遇到报错时按此背景判断处置：

- **第一层 WAF URL 拦截**：分页裸 URL（`page>=2`）被拦截返回「很抱歉…访问被阻断」。规避：spyder 通过已登录 Chrome 会话请求（带签名参数），正常可翻页。
- **第二层 阿里云滑块验证**：连续请求触发「访问验证：请按住滑块」。规避：人工过验证 / 稍后重试，绝不硬撞。
- spyder 翻页若持续失败：检查 Chrome 登录态是否过期（标题含昵称=已登录），必要时用户重新登录雪球。

> timeline API 仍可用于**快速预扫**（page=1 判断博主是否有新帖），但完整采集以 spyder 工具层为准。

---

## 前置步骤：同步雪球关注列表 → 更新看板博主控制台

每次采集会话开始时**必须**先执行此步（无论单博主还是批量）。执行脚本：

```bash
python3 {post-fetch}/scripts/xq_sync_console.py            # dry-run（默认）：输出对比报告
python3 {post-fetch}/scripts/xq_sync_console.py --apply    # 确认后落地：新增登记；取关须看板手工删
```

脚本输出（依赖 browser-act CLI + 已登录雪球 session + 看板服务 127.0.0.1:8698）：
1. **新增**（关注中但看板未登记）→ 向用户报告，`--apply` 后走 `POST /api/bloggers` 登记（编号递增，雪球ID填入，平台=雪球，「信息截止」=半年前今天 17:50:00 ISO）
2. **取关**（看板登记但已不关注，且平台=雪球）→ 向用户报告，**须用户到看板手工删除**（涉及目录回收，脚本不自动执行，保留画像文件夹与 wiki 条目）
3. **ID 不一致**（看板 ID 与关注列表不符）→ 报告，人工核对
4. **博主层残留**（看板无登记但 `博主/<名>/` 存在文件夹）→ 报告，询问迁移/删除/保留（2026-08-10 曾遗留 APEC蓝天/douhun/james_nj/景风长赢，8/14 审查才暴露）
5. 更新看板 `updateDate` 为当天

**info_cutoff 一致性（2026-08-14 新增）**：本次「信息截止」发生变更的博主，检查画像 `博主/<名>/<名>.md` frontmatter `info_cutoff` 是否已同步同值；不一致 → 更新画像（ISO 裸写无引号，规则 #36）。画像不存在 → 跳过（新博主待采集后第五步创建）。

> 此步取代原规则 #12 中「Agent 不得自行新增博主」的限制——用户明确授权从雪球关注列表同步。但 Agent 仍不得凭空捏造博主（必须有雪球关注关系作为来源）。

---

## 第二步：工具层调用（委托 xueqiu-spyder 采集）

执行模板：

```bash
PY=~/.workbuddy/binaries/python/envs/xueqiu-spyder/bin/python
NOW=$(date "+%Y-%m-%dT%H:%M:%S")
$PY {xueqiu-spyder 目录}/main.py user {xq_id} \
  --from "{info_cutoff}" --to "$NOW" \
  --outfile "雪球采集-{nickname}-{YYYY年M月D日}.md" \
  --output "{输出目录}"
```

- `{xueqiu-spyder 目录}`：本地 `~/.workbuddy/skills/investment/xueqiu-spyder/`（与 post-fetch 同目录层级；以实际安装位置为准）

- `{info_cutoff}` 取看板 `bloggers.info_cutoff`（ISO `YYYY-MM-DDTHH:mm:ss`）；新增博主默认半年前 17:50:00
- spyder 内部完成：翻页拉取 → 置顶排除 + 时间窗过滤 → 截断帖详情页补全（含精确时间覆盖）→ 帖子集输出
- spyder 用户名传参：可直接传数字 ID；传昵称时自动搜索解析
- 输出文件命名与 vault 路径由本层控制（spyder `--outfile/--output`）

**环境检查**（调用前）：
- venv 依赖：`$PY -c "import requests, playwright"`
- Chrome CDP：`curl -s http://127.0.0.1:9222/json/version` 返回 JSON；端口占用时 `XUEQIU_DEBUG_PORT` 覆盖
- 登录态：用户页标题含昵称 = 已登录

**翻页数与节流（2026-09-09 实测固化，硬约束）**：

`--max-pages` **必须按窗口长度取值**，不得沿用默认 10 页——实测 405 封禁主因就是翻页过量：

| 窗口长度（info_cutoff → now） | `--max-pages` |
|:---|:---|
| ≤ 24 小时 | **3** |
| ≤ 7 天 | **5** |
| > 7 天 | 10 |

**批量节流**：连续采集时**每处理 10 位博主暂停 60 秒**（`sleep 60`），再继续下一位。

> **实测依据（2026-09-09）**：连续 17 位 × 10 页 ≈ 172 次请求 / 6.5 分钟（约 26 次/分钟）→ `v4/statuses/user_timeline.json` 被阿里云 WAF 对该 IP 临时封禁（405，页面自身带签名请求亦 405，其他端点正常）。改用 ≤3 页 + 每 10 位暂停后未再触发。经验阈值：timeline 翻页 ~150-180 次 / 详情页导航 ~100-120 次 为危险区。

**端点被封无需人工干预**：spyder 内建自动降级（v4 → 旧版 `/statuses/user_timeline.json`，数据一致），失败一次即自动切换重试，见 `xueqiu-spyder` SKILL。若降级后仍失败，才按 WAF 报错处置（稍后重试 / 人工过验证）。

---

## 第三步：格式验收（对照 output-format.md）

spyder 输出后逐项核对：

1. frontmatter 七字段：title/source/author/date/recorded/type/status（type=`帖子集`；status=`待提炼`，含摘要帖则 `待提炼-含摘要`）
2. 每帖三件套：`## N. 标题` + 正文 + 摘要行（发布行含 `形态`、`全文/摘要`、`[原文]` 链接）
3. 纯文本净化：无 `![[`、`![](url)`、`<img>`、`[表情]` 占位残留（Unicode emoji 属正文保留）
4. `author` 值合法：不含 `发布于|来自|关注|：|:`，判不出置 `Unknown` 并标待复核
5. 不合格项 → 修复后落 vault；合格 → 汇报 + info_cutoff 双写

---

## 引用内容与 Emoji 处理（验收口径）

- **引用块**（`>` 前缀）：保留，区分作者原文和引用原文；`//@` 嵌套引用保留原文结构
- **Emoji**：雪球表情图片转 `[表情名]` 文本占位后，**纯文本化阶段删除占位**（2026-09-03 §采集2：不留占位）；Unicode 文字 emoji 原样保留（属正文）
- **回复形态判定**：含 "回复 @"/引用块 → 回复；原创 <300 字 → 短文；≥300 字或含分段/小标题 → 长文；专栏 → 专栏
