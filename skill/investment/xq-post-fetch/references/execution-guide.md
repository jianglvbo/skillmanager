# 采集执行细节指南

> 本文件承载 xq-post-fetch Workflow 的完整执行细节（关注列表同步、会话管理、滚动加载、API 截断判定、**风控规避**）。
> SKILL.md 仅保留「第零步~第七步」摘要骨架，细节一律以本文件 + `page-structure.md` 为准，避免双源漂移。
> 权威规则：`framework-rules.md` #12（博主补登/移除例外）、#29（帖子集例外流程）、#35（原文链接必填）。
> 2026-08-15 批量采集 40 位博主实战后修订：新增「风控规避」章节 + 用户页采集主路径，替代原「API 翻页」路径。
> 2026-08-19 批量采集 42 位博主后修订：新增「登录态隔离与 profile 导入」章节 + 「修改于」时间戳陷阱 + 脚本自动化说明（`xq_sync_console.py` / `xq_user_collect.py` v2）。

---

## 〇、风控规避（2026-08-15 实战核心经验）

雪球对采集有**两层反爬**，必须提前规避：

### 第一层：WAF URL 拦截（分页裸 URL）

- **现象**：直接 navigate `https://xueqiu.com/v4/statuses/user_timeline.json?page=2&user_id=xxx` 返回「很抱歉，由于您访问的URL有可能对网站造成安全威胁，您的访问被阻断」，页面 body 是 WAF 拦截页
- **规律**：`page=1` 裸 URL 通常可访问；`page>=2` 裸 URL 被 WAF 拦截（分页参数触发）；带签名参数（`md5__1038`、`u_atoken`）的请求是页面自身发出的，可成功
- **规避**：**放弃 API 翻页，改用用户页滚动加载**（浏览器真实滚动触发带签名请求，不触发 WAF）

### 第二层：阿里云滑块验证（连续请求触发）

- **现象**：连续 ~90 次 show.json/API 请求后触发「访问验证：请按住滑块，拖动到最右边」；页面 body 含 `aliyunCaptcha-sliding-slider`。**2026-08-19 实测：连续导航 10+ 个详情页也会触发**（get markdown 返回「滑动验证页面」）
- **限制**：`solve-captcha` 与 `remote-assist` 均需 API key（browser-act 未配置时不可用）——**不要依赖自动解决**
- **规避**：
  1. **优先用户页方案**（见下）——浏览器渲染页面，实测 40 位博主全程零滑块
  2. 若已触发：请用户人工拖滑块；或 **关闭 session 重开**（`browser-act session close xq` + 重新 `browser open`），新 session 用户页可恢复访问（API 端点仍可能被拦）
  3. **详情页补全也有风控成本**：每帖导航详情页 = 一次请求。截断帖才需要补全；非截断帖只靠用户页正文即可（v2 脚本已按此优化——「修改于」帖与截断帖才进详情页）
  4. **滑块检测**：脚本对 get markdown 返回含「滑动验证/访问验证」的页面做检测，标记为「摘要」而非「全文」，**不盲重试**（越重试越容易被封）

### 采集主路径（2026-08-15 定案）：用户页滚动加载 + 详情页补全

替代原「timeline API 翻页」路径，实测最稳：

1. `navigate https://xueqiu.com/u/{xq_id}` + 等待 4s
2. `get markdown` → 按 `page-structure.md` 解析帖子（时间戳用 `re.search` 非行首锚定）
3. 帖子数不足 → `scroll down --amount 2500` + 等待 2s + 重新 `get markdown`（滚动触发带签名请求，不触发 WAF）
4. 按 cutoff 过滤（**必须排除置顶帖**：完整日期 + 链接后「置顶」标记）
5. 截断帖（正文含「展开」）→ `navigate https://xueqiu.com/{xq_id}/{post_id}` 详情页补全（提取「来源：雪球App」与「风险提示」之间正文）
6. 生成帖子集文件（每帖带 `[原文]` 链接）；**0 帖不生成文件**

> timeline API 仍可用于**快速预扫**（page=1 判断博主是否有新帖），但完整采集走用户页方案。

### 「修改于」时间戳陷阱（2026-08-19 实战发现）

用户页时间戳有两种形态：

| 形态 | 含义 | 采集判定 |
|:---|:---|:---|
| `07-16 14:06· 来自iPhone` | **发布时间** | 直接与 cutoff 比较 |
| `修改于08-13 20:54· 来自雪球` | **最后修改时间**（原帖可能发布于更早） | **必须进详情页取「发布于」时间**再做窗口判定 |

- **风险**：把「修改于」时间当发布时间 → 旧帖被作者修改后时间 > cutoff → 误当新帖采入（重复内容）
- **处理（v2 脚本已实现）**：对「修改于」帖导航详情页，提取 `[发布于 YYYY-MM-DD HH:MM]`；详情页也只有「修改于」（无法确认发布时间）→ **跳过该帖**（疑似旧帖修改，防误采），stderr 打印 `⏭️ 跳过`
- **注意**：部分活跃博主（如重组专家）用户页全是「修改于」帖 → 可能整页 0 新帖 → 不生成文件，属正常（非漏采）

---

## 前置步骤：同步雪球关注列表 → 更新博主控制台

每次采集会话开始时**必须**先执行此步（无论单博主还是批量）。**推荐直接运行 `scripts/xq_sync_console.py`**（2026-08-19 新增，一键完成 1-7 步并输出报告）：

```bash
python3 ~/.agents/skills/xq-post-fetch/scripts/xq_sync_console.py            # dry-run：输出对比报告
python3 ~/.agents/skills/xq-post-fetch/scripts/xq_sync_console.py --apply    # 确认后落地（新增追加行/取关删行/更新 updateDate）
```

脚本自动：创建 session → 校验登录 → 分页拉取关注列表 → 解析控制台 → 对比输出【新增/取关/ID不一致/博主层残留/待采集清单】。**落地前必须向用户报告变更并确认**（新增/取关都需用户点头，脚本 dry-run 模式即为此设计）。

手工执行时的完整规则：

1. 获取当前登录用户 ID：导航 `https://xueqiu.com/user/show.json`，从 JSON 提取 `id` 字段
2. 分页获取关注列表：`https://xueqiu.com/friendships/groups/members.json?gid=0&page={n}&count=50`，逐页直到返回空
3. 读取博主控制台（`{VAULT}/工作区/博主控制台.md`），解析表格
4. 对比：
   - **新增**（在关注列表但不在控制台）→ 向用户报告，确认后追加行（编号递增，雪球ID填入，「是否雪球博主」=是，「是否特别关注」=否，「信息截止」=半年前的今天 17:50:00，ISO 格式 `YYYY-MM-DDTHH:mm:ss`）
   - **取关**（在控制台但不在关注列表，且「是否雪球博主」=是）→ 向用户报告，确认后从控制台**删除该行**（保留博主画像文件夹和已有 wiki 条目，不删除任何文件）
   - **无变动** → 报告「关注列表无变化」
5. 更新控制台 `updateDate` 为当天
6. **残留检测（2026-08-14 新增）**：比对控制台登记名与 `{VAULT}/博主/` 下文件夹——控制台无登记但 `博主/<名>/` 仍存在文件/文件夹 → 向用户报告（博主名 + 文件数），询问处理方式：迁移至其他层（#12）/ 删除画像 / 保留观察。**Agent 不自行删除**。此步防「控制台移除但博主层残留」形成未登记博主悬空（2026-08-10 同步后曾遗留 APEC蓝天/douhun/james_nj/景风长赢，8/14 审查才暴露）
7. **info_cutoff 一致性（2026-08-14 新增）**：本次「信息截止」发生变更的博主，检查画像 `博主/<名>/<名>.md` frontmatter `info_cutoff` 是否已同步为同值；不一致 → 更新画像（ISO 格式 `YYYY-MM-DDTHH:mm:ss` 裸写无引号，规则 #36）。画像不存在 → 跳过（新博主待采集后第七步创建）

> 此步取代原规则 #12 中「Agent 不得自行新增博主」的限制——用户明确授权从雪球关注列表同步。但 Agent 仍不得凭空捏造博主（必须有雪球关注关系作为来源）。

---

## 前置步骤 A：登录态隔离与 profile 导入（2026-08-19 实战发现）

**坑**：browser-act 创建的浏览器实例（如 `xueqiu-browser`）是**独立隔离的**，不自动复用本地 Chrome 的登录态——本地 Chrome 已登录雪球，但 browser-act 打开页面仍显示「用户未登录」（`user/show.json` 返回 `error_code:10022`）。

**解决**：把本地 Chrome profile 导入 browser-act 浏览器（一次性，导入后持久）：

```bash
# 1. 查看可导入的本地 profile（含邮箱标识，找到你登录雪球的那个）
browser-act browser list-profiles
#   例：local_profile_109882663793328303  您的 Chrome  local  422084591@qq.com

# 2. 导入 profile 到目标浏览器（先关闭该浏览器的活动 session）
browser-act session close xq
browser-act browser import-profile <browser_id> <profile_id> --allow-restart-chrome
#   例：browser-act browser import-profile chrome_local_103721927322894575 local_profile_109882663793328303 --allow-restart-chrome

# 3. 验证登录态
browser-act --session xq browser open <browser_id> https://xueqiu.com/
browser-act --session xq navigate https://xueqiu.com/user/show.json
#   返回 {"id":xxxxx} 而非 error_code:10022 → 成功
```

**判断是否已登录的可靠方法**：`user/show.json` 返回 `{"id":N}` 为已登录；`{"error_code":"10022","error_description":"用户未登录"}` 为未登录。**页面标题含「我的首页」也是登录标志**；纯「雪球 - 聪明的投资者都在这里」不代表已登录。

> 脚本 `xq_user_collect.py` v2 已内置登录校验（`ensure_session()`），未登录会直接报错并提示导入 profile，不再傻等。

---

## 第二步：会话管理与登录验证

**脚本自动化**：`xq_user_collect.py` v2 已内置 `ensure_session()`——自动探测浏览器 → 创建独立 session（`xq_<pid>`，避免与他人会话争用）→ 导航 user/show.json 校验登录 → 未登录报错并提示导入 profile。**单博主采集可直接跑脚本，无需手工建 session**。

手工会话管理（按顺序判断）：
1. `browser-act session list` 查看活跃会话
2. 扫描**本对话的工具调用历史**：是否已执行过 `browser open --session <name>`？
   - 是 → 该 session 是我的，直接 `navigate` 到目标 URL
   - 否 → 该 session 不是我的，**不要操作它**
3. 没有我的 session → 用 `browser-act --session xq browser open {browser_id} "https://xueqiu.com/u/{xq_id}"` 创建新 session
4. 有我的 session → 直接 `browser-act --session {name} navigate "https://xueqiu.com/u/{xq_id}"`

**chrome 模式启动失败处理（2026-08-15 实战）**：`browser open` 报 `Error 230404: Chrome did not start within 30.0s` 时，根因多为**本地 Chrome 正在运行**（profile 锁）。处理：
1. `pgrep -x "Google Chrome" | wc -l` 确认本地 Chrome 进程
2. `osascript -e 'tell application "Google Chrome" to quit'` 优雅退出 + `pkill -x "Google Chrome"` 清理残留（需用户同意让出本地 Chrome）
3. 重试 `browser open`（此前 4 次失败，关 Chrome 后一次成功）
4. 备选：`--headed` 模式打开（窗口可见，用户可操作滑块验证）

**验证登录态**：
- `browser-act --session {name} get title`
- 标题含用户昵称 → 已登录
- 标题不含昵称或含「登录」→ **停止，提示用户在 Chrome 中登录雪球**

**session 独占铁律（2026-08-15 实战教训）**：一个 session 同一时刻只允许一个采集任务操作。批量验证脚本后台运行时，**禁止并行 navigate/eval 测试**——会争用 session 导致任务中断（本次曾因此丢失验证进度）。如需并行，创建第二个 session（`--session xq2`）。

---

## 第三步：滚动加载更多

- 如果首屏帖子数 < max_posts 且最旧帖子仍在时间窗口内 → 需要滚动加载：

  ```bash
  browser-act --session {name} scroll down --amount 2000
  browser-act --session {name} wait stable
  browser-act --session {name} get markdown
  ```

- 重新解析 markdown，合并新帖子（按 post_id 去重）
- 重复直到帖子数 ≥ max_posts 或最旧帖子超出时间窗口

---

## 第四步：API 采集路径的截断判定

使用 timeline API 获取帖子列表时：

- timeline API 的 `text` 字段**不保证全文**，以下情况必须导航详情页验证：
  1. `text` 以 "……"/"..."/"....." 结尾
  2. `text` 为空但 `description` 有内容（type="3" 专栏文章）
  3. `truncated` 字段为 true
- 不满足上述条件的帖子，仍需逐帖导航详情页获取完整正文（详情页是唯一权威来源）
- **禁止仅凭 API 返回即标注「全文」**

**补全流程**：
```bash
browser-act --session {name} navigate "https://xueqiu.com/{xq_id}/{post_id}"
browser-act --session {name} wait stable
browser-act --session {name} get markdown
```
- 从详情页提取完整正文（正文在 `来源：雪球App` 和 `风险提示` 之间）
- 详情页同时提供精确发布时间（`发布于 YYYY-MM-DD HH:MM`），覆盖用户页的模糊时间
- 补全后标记：「全文」（经详情页验证）vs「摘要」（详情页也无法获取全文）

---

## 引用内容与 Emoji 处理

- **引用块**（`>` 前缀）：保留，区分作者原文和引用原文（规则见 `page-structure.md`「引用内容处理」）
- **Emoji 处理**：雪球表情图片 `![表情](url)` 替换为 `[表情]` 文本占位（规则见 `page-structure.md`「Emoji 处理」）。**保持原文原则**：采集阶段一律保留表情（转文本占位），禁止删除；Unicode 表情字符原样保留

---

## 全流程脚本自动化（2026-08-19 落地）

| 环节 | 脚本 | 说明 |
|:---|:---|:---|
| 前置步骤（关注列表同步→控制台对比） | `scripts/xq_sync_console.py` | dry-run 出报告 → 用户确认 → `--apply` 落地 |
| 单博主采集 | `scripts/xq_user_collect.py` | 自建 session + 登录校验 + 修改帖处理 + 0帖不生成文件 + 自动双写 info_cutoff |
| info_cutoff 双写 | `scripts/xq_update_cutoff.py` | 画像 + 控制台双写（被 v2 采集脚本自动调用） |

**批量采集推荐流程**（42 位约 25 分钟，全程零手工）：

```bash
# 1. 前置：同步控制台（确认新增/取关）
python3 xq_sync_console.py            # 报告
python3 xq_sync_console.py --apply    # 确认后落地

# 2. 批量采集（逐博主串行；session 独占铁律禁止并行）
python3 xq_batch_collect.py           # 调度器：读控制台 → 逐博主跑 xq_user_collect.py
```

> 批量调度器（`xq_batch_collect.py`）不在 skill 内（按场景临时生成即可）：读取控制台「雪球ID 非空」行 → 逐博主调 `xq_user_collect.py <id> <名> <cutoff> <outfile> --no-cutoff` → 最后统一跑 `xq_update_cutoff.py` 双写。
