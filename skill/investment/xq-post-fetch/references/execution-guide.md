# 采集执行细节指南

> 本文件承载 xq-post-fetch Workflow 的完整执行细节（关注列表同步、会话管理、滚动加载、API 截断判定）。
> SKILL.md 仅保留「第零步~第八步」摘要骨架，细节一律以本文件 + `page-structure.md` 为准，避免双源漂移。
> 权威规则：`framework-rules.md` #12（博主补登/移除例外）、#29（帖子集例外流程）、#35（原文链接必填）。

---

## 前置步骤：同步雪球关注列表 → 更新博主控制台

每次采集会话开始时**必须**先执行此步（无论单博主还是批量）：

1. 获取当前登录用户 ID：导航 `https://xueqiu.com/user/show.json`，从 JSON 提取 `id` 字段
2. 分页获取关注列表：`https://xueqiu.com/friendships/groups/members.json?gid=0&page={n}&count=50`，逐页直到返回空
3. 读取博主控制台（`{VAULT}/工作区/博主控制台.md`），解析表格
4. 对比：
   - **新增**（在关注列表但不在控制台）→ 向用户报告，确认后追加行（编号递增，雪球ID填入，「是否雪球博主」=是，「是否特别关注」=否，「信息截止」=半年前的今天 17:50:00，ISO 格式 `YYYY-MM-DDTHH:mm:ss`）
   - **取关**（在控制台但不在关注列表，且「是否雪球博主」=是）→ 向用户报告，确认后从控制台**删除该行**（保留博主画像文件夹和已有 wiki 条目，不删除任何文件）
   - **无变动** → 报告「关注列表无变化」
5. 更新控制台 `updateDate` 为当天

> 此步取代原规则 #12 中「Agent 不得自行新增博主」的限制——用户明确授权从雪球关注列表同步。但 Agent 仍不得凭空捏造博主（必须有雪球关注关系作为来源）。

---

## 第三步：会话管理与登录验证

**会话管理**（按顺序判断）：
1. `browser-act session list` 查看活跃会话
2. 扫描**本对话的工具调用历史**：是否已执行过 `browser open --session <name>`？
   - 是 → 该 session 是我的，直接 `navigate` 到目标 URL
   - 否 → 该 session 不是我的，**不要操作它**
3. 没有我的 session → 用 `browser-act --session xq browser open {browser_id} "https://xueqiu.com/u/{xq_id}"` 创建新 session
4. 有我的 session → 直接 `browser-act --session {name} navigate "https://xueqiu.com/u/{xq_id}"`

**验证登录态**：
- `browser-act --session {name} get title`
- 标题含用户昵称 → 已登录
- 标题不含昵称或含「登录」→ **停止，提示用户在 Chrome 中登录雪球**

---

## 第四步：滚动加载更多

- 如果首屏帖子数 < max_posts 且最旧帖子仍在时间窗口内 → 需要滚动加载：

  ```bash
  browser-act --session {name} scroll down --amount 2000
  browser-act --session {name} wait stable
  browser-act --session {name} get markdown
  ```

- 重新解析 markdown，合并新帖子（按 post_id 去重）
- 重复直到帖子数 ≥ max_posts 或最旧帖子超出时间窗口

---

## 第五步：API 采集路径的截断判定

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
- **Emoji 清洗**：雪球表情图片 `![表情](url)` 替换为 `[表情]` 或删除（规则见 `page-structure.md`「Emoji 清洗」）
