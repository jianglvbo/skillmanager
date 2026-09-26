# 采集执行细节指南

> 本文件承载 xueqiu-spyder Workflow 的完整执行细节（2026-09-26 起本 skill = 原 post-fetch 编排 + 原抓取工具层合并；
> 旧引用「post-fetch/references/execution-guide.md」一律指向本文件）。SKILL.md 仅保留步骤摘要骨架，细节以本文件为准。
> 权威规则：`framework-rules.md` #12（博主补登/移除例外）、#29（帖子集例外流程）、#35（原文链接必填）。
> 2026-09-16 收口：**全部浏览器动作统一走 ego lite**（采集走本 skill 的桥；同步/摘要补全走 `scripts/xq_ego.py`）；
> browser-act 与 Chrome 通道都已从代码删除，不会再起任何别的浏览器。

---

## 〇、风控知识背景（spyder 已内建检测，编排层须知）

雪球对采集有**两层反爬**，xueqiu-spyder 工具层内建 WAF/滑块检测（命中即抛 `CrawlerError` 停止），编排层遇到报错时按此背景判断处置：

- **第一层 WAF URL 拦截**：分页裸 URL（`page>=2`）被拦截返回「很抱歉…访问被阻断」。规避：spyder 通过 **ego lite 里已登录的雪球会话**请求（带签名参数），正常可翻页。
- **第二层 阿里云滑块验证**：连续请求触发「访问验证：请按住滑块」。规避：人工过验证 / 稍后重试，绝不硬撞。
- **第三层 静默空页（最危险——会被误读成「博主没发帖」）**：被风控时页面可能**正常打开**（头像/粉丝数/认证都在），只有**帖子列表是空的**。用户口径（2026-09-24）：「**没有博主主页进去是全空的**」——**博主主页不可能零帖子**，看到空列表一律按风控拦截处理，不得判「无新帖」。
  - **判据**：`timeline__item` 类元素数为 0（或帖子区无内容）＝被拦；有任意条目＝页面正常。
  - **注意 DOM 渲染变体**：`.timeline__list` / `.timeline__item__info` 可能不匹配（换了渲染），别用它们判定空页——用**同源 API** 复核（`/statuses/user_timeline.json?user_id=&page=1`，返回 statuses 即正常）。
  - **处置**：不推进 cutoff（按失败处理），冷却后重试；本轮已把该博主列入待重试清单。
- spyder 翻页若持续失败：检查 **ego lite 里**的雪球登录态是否过期（标题含昵称=已登录），必要时用户重新登录雪球。
- **「用户接管」会中断整轮**（2026-09-21/24 各踩一次）：命中滑块时 ego 被激活并 `handOff` 给用户，用户一动手接管，任务空间即不属于 agent，后续每条都报 `任务空间已不属于 agent / hard stop`。这是正常保护，**不要重试夺回**——等用户过完验证、下一轮采集会自动换新空间继续。

> timeline API 仍可用于**快速预扫**（page=1 判断博主是否有新帖），但完整采集以 spyder 工具层为准。

---

## 前置步骤：同步雪球关注列表 → 更新看板博主控制台

每次采集会话开始时**必须**先执行此步（无论单博主还是批量）。执行脚本：

```bash
python3 {xueqiu-spyder}/scripts/xq_sync_console.py            # dry-run（默认）：输出对比报告
python3 {xueqiu-spyder}/scripts/xq_sync_console.py --apply    # 确认后落地：新增登记；取关须看板手工删
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

## 模式决策：feed（缺省）vs user（兜底）

| 场景 | 模式 | 理由 |
|:---|:---|:---|
| 日常增量（全部已关注博主，隔 ≤3 天） | **feed** | 一次会话覆盖全部博主，自然浏览形态，风控暴露最小；逐博主 cutoff 记账由**流断点书签**取代 |
| 首采 / 窗口 >3 天 / 跨周补采 | user | 关注流无限滚动有历史地板，深窗口翻不到 |
| feed 书签未翻到（退出码 3）/ 流缺帖抽查 | user | 宁可重复采，不可漏采 |

**轮转抽查（feed 模式的兜底纪律）**：feed 采集完成后，对本轮**未露面**的看板博主做小比例核对（每轮抽 1/5~1/7，用 `main.py user {xq_id} --from {其 info_cutoff} --max-pages 1` 翻一页）；抽查发现漏帖 → 说明流有渲染缺口，该博主改走 user 模式补齐并报告用户。

---

## feed 模式（缺省）：流式采集执行细节

```bash
PY=${XUEQIU_PY:-$(cat ~/.config/xueqiu-spyder/python 2>/dev/null || echo python3)}
SPYDER="$(ls -d ~/.zcode/skills/xueqiu-spyder 2>/dev/null | head -1)"
$PY "$SPYDER/main.py" feed --tab follow --limit 50 \
  --outfile "雪球采集-关注流-{YYYY年M月D日}.md" --output ~/.cache/xueqiu-spyder/out
```

- `--since` 缺省读**流断点书签**（`~/.cache/xueqiu-spyder/feed-state.json`，本 skill 私有状态，非看板字段）；无书签按 limit 采。滚动停止条件：凑满 limit 且最旧帖时间 ≤ 书签（翻到了）／滚动地板或步数上限（60 步）没翻到 → **退出码 3，禁止写书签**，走 user 兜底。
- **退出码**：0=产出（写书签=本轮起点）/ 2=窗口内无帖（写书签）/ 3=书签未翻到（**禁写**）/ 1=失败（禁写）。
- **博主过滤**：缺省（auto=关注流开）按看板 `/api/bloggers/live` 的 xueqiuId 过滤，非看板博主帖不入产物；服务不可用时不过滤，未建档帖由 import-post-history 跳过（等效兜底）。
- **时间**：流内相对时间锚定采集瞬间换算绝对时间（分钟级精度）；「修改于」＝编辑时间非首发，发布行标 `（修改于·推算）`，普通流内推算标 `（流内推算）`；例外帖走详情页拿权威时间。
- **例外 URL**（自身专栏 / 流内展开失败）：详情页补全文+权威时间，节流 2.6~3.4s，连续 3 次失败熔断、余下按「摘要」处理。
- **cutoff 回写**：feed 成功后，仅对**本轮实际采到帖**的博主回写 `info_cutoff`（`scripts/xq_update_cutoff.py`，值=本轮书签）；未露面博主不动（下次轮转抽查核对）。
- **机制要点（改代码前必读，2026-09-26 实测）**：展开控件是 `a.timeline__expand__control`（textContent 带不可见 iconfont 字符，按 textContent==='展开' 匹配永远 0 命中）；handler 进视口才惰性挂载（scrollIntoView 后停 ~1s 再点，380ms 全落空）；计数在 `.timeline__item__ft`（数字>0 显数字、=0 显标签）；引用卡 `.timeline__item__forward__content` 是正文块**兄弟节点**，回复帖同名元素装的是对话预览（回复帖不拼引用卡）。

---

## user 模式（兜底）：逐博主采集

执行模板：

```bash
# 先探活：路径已多次迁移（~/.agents → ~/.zcode/skills → 项目内 .agents），别信固定值
SPYDER="$(ls -d ~/.zcode/skills/xueqiu-spyder ~/Project/investment-dashboard/.agents/skills/xueqiu-spyder 2>/dev/null | head -1)"
[ -n "$SPYDER" ] || { echo "❌ xueqiu-spyder 未找到，先 ls 确认位置"; exit 1; }
PY=${XUEQIU_PY:-$(cat ~/.config/xueqiu-spyder/python 2>/dev/null || echo python3)}
NOW=$(date "+%Y-%m-%dT%H:%M:%S")
$PY "$SPYDER/main.py" user {xq_id} \
  --from "{info_cutoff}" --to "$NOW" \
  --outfile "雪球采集-{nickname}-{YYYY年M月D日}.md" \
  --output "{输出目录}"
```

- `{xueqiu-spyder 目录}`：**位置会迁，引用前先 `ls` 探活**。历史：`~/.agents/skills/xueqiu-spyder/`（2026-09-23 失效）→ `~/.zcode/skills/xueqiu-spyder/`（symlink → `~/.skills-manager/skills/`）／项目内 `.agents/skills/xueqiu-spyder/`；`~/.workbuddy/...` 是历史镜像，勿用。**硬编码路径已三次失效**（09-21 / 09-23 / 09-24 各踩一次），本轮 `run_fetch_batch.py` 的候选列表还留着失效项

- `{info_cutoff}` 取看板 `blogger.info_cutoff_datetime`（ISO `YYYY-MM-DDTHH:mm:ss`）；新增博主默认半年前 17:50:00

> **⚠️ 时区陷阱（2026-09-16 审计实测，踩过一次）**：库里那一列存的是**本地时间**（如 20:41），但看板 API 把它序列化成 **UTC ISO**（`12:41:00.000Z`）。所以**从 API 取值做 `--from` 时必须 +8h 还原本地**——直接截前 19 位当本地用会少算 8 小时，导致每次重复采 8 小时（重复记录 + 多余请求）。实测对照：晚舟夕照 库里 20:41 ／ API `12:41:00.000Z` ／ +8h = 20:41 ✅。批处理脚本已内置这个换算（`run_fetch_batch.cutoff_iso`）；手写命令时记得自己转。
- spyder 内部完成：翻页拉取 → 置顶排除 + 时间窗过滤 → 截断帖详情页补全（含精确时间覆盖）→ 帖子集输出
- spyder 用户名传参：可直接传数字 ID；传昵称时自动搜索解析
- 输出文件命名与 vault 路径由本层控制（spyder `--outfile/--output`）

**环境检查**（调用前）：
- venv 依赖：`$PY -c "import requests"`（playwright 已于 2026-09-16 移除）
- **ego lite 通道（默认，2026-09-15 起）**：确认 ego lite 已打开且已登录雪球；`SPYDER/ego_browser.py` 的自检打印当前页 URL/标题即可
- **无需任何 CDP 预检**：Chrome 通道（含 `XUEQIU_DEBUG_PORT` 等）已于 2026-09-16 从工具层整段删除，采集只走 ego lite。
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

## 格式验收（对照 output-format.md，两模式共用）

spyder 输出后逐项核对：

1. frontmatter 七字段：title/source/author/date/recorded/type/status（type=`帖子集`；status=`待提炼`，含摘要帖则 `待提炼-含摘要`）
2. 每帖三件套：`## N. 标题` + 正文 + 摘要行（发布行含 `形态`、`全文/摘要`、`[原文]` 链接）
3. 纯文本净化：无 `![[`、`![](url)`、`<img>`、`[表情]` 占位残留（Unicode emoji 属正文保留）
4. `author` 值合法：不含 `发布于|来自|关注|：|:`，判不出置 `Unknown` 并标待复核；**且必须等于文件名里的博主名**——`author` 取 API `user.screen_name`，若出现**所有文件同名**或出现知名大 V 名（如「大道无形我有型」）＝抓到了侧栏「用户推荐」位（DOM 竞态，2026-09-21/24 各踩一次），按文件名批量订正后再入库
5. 不合格项 → 修复后落 vault；合格 → 汇报 + info_cutoff 回写（看板）

---

## user 模式：info_cutoff 更新前置条件（防漏采硬约束）

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
       python3 "$SPYDER/scripts/xq_update_cutoff.py" "{nickname}" "$(date '+%Y-%m-%dT%H:%M:%S')" ;;
  1|3) # 采集失败 / 页数不足 → 保持原 cutoff，列入待重试清单报告用户
       echo "⚠️ {nickname} 采集未完成（退出码 $code），cutoff 保持当前值，待重试" ;;
esac
```

**失败时绝不更新**：否则下次从新 cutoff 起算，本次未采到的帖子永久遗漏。原则是**宁可重复采，不可漏采**（重复内容可在提炼阶段去重）。

**批量收尾核对**：逐一核对退出码 → 仅对 0/2 回写 cutoff → 退出码 1/3 的博主列「待重试清单」报给用户，其 cutoff 原值不动。

---

## 落库 post_history + 入库校验 + 清理临时产物（强制，两模式共用）

采集产物 md **不再落 vault 粗制品**，它是临时文件；原文落 `post_history`，提炼也从库里读：

```bash
# ① 落库（幂等，url_hash 判重）——仓库脚本 2026-09-23 起在 src/scripts/
node ~/Project/investment-dashboard/src/scripts/import-post-history.js "<采集产物.md>"
# ② 入库校验（逐帖 url_hash + content_hash 一致才算留档；缺口则禁止清理）
node <xueqiu-spyder>/scripts/check-post-history-covered.js "<采集产物.md>"
# ③ 校验通过 → 清理临时产物（--rm 一步到位，移入废纸篓可恢复）
node ~/Project/investment-dashboard/src/scripts/import-post-history.js --rm "<采集产物.md>"
# ④ 保留期清理：post_history 只保留 180 天（滚动窗口；2026-09-15 用户拍板由 30 天放宽）
node ~/Project/investment-dashboard/src/scripts/purge-post-history.js --dry
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
