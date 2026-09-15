# 采集编排执行细节指南

> 本文件承载 post-fetch Workflow 的完整执行细节（前置同步、工具层调用、时间窗、格式验收、风控知识）。
> SKILL.md 仅保留步骤摘要骨架，细节一律以本文件为准；采集执行由 xueqiu-spyder 承载，本层不持有页面解析规则（2026-09-09 重构，page-structure.md 已退役）。
> 权威规则：`framework-rules.md` #12（博主补登/移除例外）、#29（帖子集例外流程）、#35（原文链接必填）。
> 2026-09-09 重构：编排-工具分层（post-fetch 编排 → xueqiu-spyder 抓取）。
> 2026-09-16 收口：**全部浏览器动作统一走 ego lite**（采集走 xueqiu-spyder 的桥；同步/摘要补全走 `scripts/xq_ego.py`），**browser-act 依赖已移除**，不要再起 Chrome。

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

脚本输出（依赖 **ego lite 已打开且已登录雪球** + 看板服务 127.0.0.1:8698；脚本内部走 `xq_ego.py`）：
1. **新增**（关注中但看板未登记）→ 向用户报告，`--apply` 后走 `POST /api/bloggers` 登记（编号递增，雪球ID填入，平台=雪球，「信息截止」=半年前今天 17:50:00 ISO）
2. **取关**（看板登记但已不关注，且平台=雪球）→ 向用户报告，**须用户到看板手工删除**（涉及目录回收，脚本不自动执行，保留画像文件夹与 wiki 条目）
3. **ID 不一致**（看板 ID 与关注列表不符）→ 报告，人工核对
4. **博主层残留**（看板无登记但 `博主/<名>/` 存在文件夹）→ 报告，询问迁移/删除/保留（2026-08-10 曾遗留 APEC蓝天/douhun/james_nj/景风长赢，8/14 审查才暴露）
5. 更新看板 `updateDate` 为当天

**info_cutoff 一致性（2026-08-14 新增；2026-09-15 收口到单一权威）**：本次「信息截止」发生变更的博主，核对**看板 MySQL `blogger.info_cutoff_datetime`**（ISO 裸写无引号，规则 #36）。**画像 md 已于 2026-09-12 退役**，不再有画像侧需要同步——旧版本此处要求「画像与看板同值」，现在只认看板。

> 此步取代原规则 #12 中「Agent 不得自行新增博主」的限制——用户明确授权从雪球关注列表同步。但 Agent 仍不得凭空捏造博主（必须有雪球关注关系作为来源）。

---

## 第二步：工具层调用（委托 xueqiu-spyder 采集）

执行模板：

```bash
SPYDER=~/.agents/skills/xueqiu-spyder                       # 工具层权威位置（部署目录）
PY=${XUEQIU_PY:-$(cat ~/.config/xueqiu-spyder/python 2>/dev/null || echo python3)}
NOW=$(date "+%Y-%m-%dT%H:%M:%S")
$PY "$SPYDER/main.py" user {xq_id} \
  --from "{info_cutoff}" --to "$NOW" \
  --outfile "雪球采集-{nickname}-{YYYY年M月D日}.md" \
  --output "{输出目录}"
```

- `{xueqiu-spyder 目录}`：**`~/.agents/skills/xueqiu-spyder/`**（部署目录＝权威；`~/.workbuddy/skills/investment/xueqiu-spyder/` 是历史镜像，勿用）

- `{info_cutoff}` 取看板 `blogger.info_cutoff_datetime`（ISO `YYYY-MM-DDTHH:mm:ss`）；新增博主默认半年前 17:50:00
- spyder 内部完成：翻页拉取 → 置顶排除 + 时间窗过滤 → 截断帖详情页补全（含精确时间覆盖）→ 帖子集输出
- spyder 用户名传参：可直接传数字 ID；传昵称时自动搜索解析
- 输出文件命名与 vault 路径由本层控制（spyder `--outfile/--output`）

**环境检查**（调用前）：
- venv 依赖：`$PY -c "import requests, playwright"`
- **ego lite 通道（默认，2026-09-15 起）**：确认 ego lite 已打开且已登录雪球；`SPYDER/ego_browser.py` 的自检打印当前页 URL/标题即可
- ~~Chrome CDP：`curl -s http://localhost:9222/json/version`~~ —— 旧通道（`XUEQIU_TRANSPORT=chrome`）才需要，仅排障时用；主机名必须 `localhost`（Chrome 152 起 `127.0.0.1` 返 404），端口用 `XUEQIU_DEBUG_PORT` 覆盖
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
5. 不合格项 → 修复后落 vault；合格 → 汇报 + info_cutoff 回写（看板）

---

## 第四步：info_cutoff 更新前置条件（2026-09-09 用户硬约束：保证不漏采）

**只有该博主本次采集真正完成，才能更新其 info_cutoff**。判定依 spyder 退出码：

| 退出码 | 含义 | 更新 cutoff |
|:---|:---|:---|
| `0` | 采集成功、已产出帖子集 | ✅ |
| `2` | 采集成功、窗口内无新帖（已确认无内容） | ✅ |
| `3` | **窗口起点没翻到**（`--max-pages` 不足，最旧帖仍比窗口起点新） | ❌ **禁止**，加大页数重跑 |
| `1` | **失败**（WAF/登录失效/异常，未产出） | ❌ **禁止** |

```bash
$PY main.py user {xq_id} --from "{cutoff}" --max-pages {N} ...
code=$?
case $code in
  0|2) # 采集完成 → 回写 info_cutoff（看板）
       python3 post-fetch/scripts/xq_update_cutoff.py "{nickname}" "$(date '+%Y-%m-%dT%H:%M:%S')" ;;
  1|3) # 采集失败 / 页数不足 → 保持原 cutoff，列入待重试清单报告用户
       echo "⚠️ {nickname} 采集未完成（退出码 $code），cutoff 保持当前值，待重试" ;;
esac
```

**失败时绝不更新**：否则下次从新 cutoff 起算，本次未采到的帖子永久遗漏。原则是**宁可重复采，不可漏采**（重复内容可在提炼阶段去重）。

**批量收尾核对**：逐一核对退出码 → 仅对 0/2 回写 cutoff → 退出码 1/3 的博主列「待重试清单」报给用户，其 cutoff 原值不动。

---

## 第五步：原文落库 post_history + 入库校验 + 清理临时产物（2026-09-12 新增，强制）

采集产物 md **不再落 vault 粗制品**，它是临时文件；原文落 `post_history`，提炼也从库里读：

```bash
# ① 落库（幂等，url_hash 判重）
node ~/Project/investment-console/scripts/import-post-history.js "<采集产物.md>"
# ② 入库校验（逐帖 url_hash + content_hash 一致才算留档；缺口则禁止清理）
node ~/.agents/skills/post-fetch/scripts/check-post-history-covered.js "<采集产物.md>"
# ③ 校验通过 → 清理临时产物（--rm 一步到位，移入废纸篓可恢复）
node ~/Project/investment-console/scripts/import-post-history.js --rm "<采集产物.md>"
# ④ 保留期清理：post_history 只保留 180 天（滚动窗口；2026-09-15 用户拍板由 30 天放宽）
node ~/Project/investment-console/scripts/purge-post-history.js --dry
```
- 摘要帖与无 `[原文]` 链接的帖**按设计不入库**（列出但不计缺口）
- 「言论 post_history_id 取不到」「按 URL 查不到留档」在 180 天窗口外**都是正常现象**
- 输出目录用 vault 外临时目录（默认 `~/.cache/xueqiu-spyder/out`）

---

## 引用内容与 Emoji 处理（验收口径）

- **引用块**（`>` 前缀）：保留，区分作者原文和引用原文；`//@` 嵌套引用保留原文结构
- **Emoji**：雪球表情图片转 `[表情名]` 文本占位后，**纯文本化阶段删除占位**（2026-09-03 §采集2：不留占位）；Unicode 文字 emoji 原样保留（属正文）
- **回复形态判定**：含 "回复 @"/引用块 → 回复；原创 <300 字 → 短文；≥300 字或含分段/小标题 → 长文；专栏 → 专栏

**单帖接口 `statuses/show.json` 的限流（2026-09-11 实测新增，硬约束）**：

| 项 | 实测值 |
|:---|:---|
| 用途 | 按 URL 回采单帖正文 / 形态（历史指针行补正文、`form` 补全、按链接核验） |
| 危险区 | **≈1.1 req/s 连续约 200 次 → 405**（返回 `text/html` 验证页，非 JSON） |
| 安全速率 | **`sleep ≥1.2s` + 每 50 次停 45s（≈0.7 req/s）**；实测 `sleep 1.0s` + 每 100 次停 30s 连续 160 次无封禁 |
| 检测与退避 | 响应 `content-type` 非 json 或 HTTP 405 → **退避 300s** 后重试同一 id；**连续 3 次限流 → 中止本轮**，保留进度文件稍后续跑 |
| 进度语义 | **只有真正拿到内容的才写入进度文件**；限流/异常必须留待重跑——本轮曾把 488 条限流失败静默记为「已处理」，缺口被掩盖（2026-09-11 教训） |

> 与 timeline 端点同属阿里云 WAF 保护：**提速率是最容易踩的坑**——先按上表速率跑，别为省时间把 sleep 压到 0.5s 以下。
