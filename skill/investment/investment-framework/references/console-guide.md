# 投资看板（investment-console）联动指南

> 本文件描述流水线（提炼/审查/言论追踪）与投资看板的数据契约与渲染约定，只保留**执行流水线时必须知道**的部分。

## 1. 看板是什么

纯前端 + 零依赖 Node 轻服务，**本地运行**（`~/Project/investment-console`，端口 8698，launchd 托管 com.investment-console）。读本地 iCloud vault（`config.vaultRoot` 指向 Obsidian 库），派生索引与运营记录写**远程共享 MySQL**（`investment_kb`，host 见 config.json；方案 A：预测控制台等已迁库，vault 不再存控制台 Markdown）。MCP 端点 `http://127.0.0.1:8698/mcp`（Bearer token 见 `Ai/tools/investment-console-mcp/README.md`）。**看板不产生知识，只呈现流水线结果。**

## 2. 数据契约（流水线写入）

| 写入方 | 端点 | 数据 | 看板呈现 |
|:---|:---|:---|:---|
| investment-refine 第四步 | `MCP refine_record` | targets[]（含 thinking v2 思考链路/basis/relation） | 提炼时间轴 + 思考时间线（决策链路图） |
| investment-review 第四步 | `MCP review_record` | 结构化审查（checks/groups/recycle） | 审查模块（2026-08-16 起不再产出 md 审查报告） |
| 粗制品队列 | `GET /api/coarse/list` | 直接读 vault `工作区/粗制品/`；「已加工」状态由提炼记录 `refine_records.from_rel` 推导（原 `coarse_records` 表已于 2026-09-12 删除，评分字段不再展示） | 粗制品模块 |
| post-fetch 第三步之二 | `scripts/import-post-history.js`（批量）/ `MCP post_history`（单条 upsert） | 采集原文落 `post_history` 表（提炼前原文留档，**唯一用途=避免重采**） | 不呈现（后端留档；`post_history action=get/check` 供提炼与补采读取） |

失败处理：API 失败（看板未启动）不阻断主流程，汇报提示「看板数据未写入」。

## 3. refine/record 请求体（决策链路图数据源）

```json
{
  "from": "工作区/原始资源/<源文件>.md",
  "sourceType": "raw",            // raw / coarse（帖子集#29、直投#30）
  "source": "[原文](url)",
  "targets": [{
    "path": "博主/雪月霜/分析框架/xxx.md",
    "type": "wiki",               // 英文码：wiki / blogger（言论追踪）/ macro
    "layer": "blogger",           // 英文码：my/blogger/other/macro/workspace（禁中文，见 refine-schema.md 二B 字典表）
    "category": "analysis_framework", // 英文码：analysis_framework/trading_system/…（同上）
    "tags": ["分析框架/估值"],     // 挂一级前缀，禁裸标签
    "basis": "原文「关键句」",      // 依据（必填，从原文哪句提炼）
    "thinking": [                 // 标准 5 步：识别/价值/归类/关系/生成
      "识别：…", "价值：…", "归类：…", "关系：…", "生成：…"
    ],
    "relation": "new"             // 英文码：new/append/complement/conflict_check/other
  }],
  "reason": "整体拆分决策说明",
  "steps": ["读取原文", "归属层判断", "创建条目", "更新博主档案", "校验"],
  "bloggerUpdated": true,
  "bloggerName": "雪月霜",
  "verify": { "ok": true, "detail": "verify-format.py 0 问题" },
  "verificationHints": []
}
```

- 一对多：一篇拆多条，targets 全写，每条必填 basis + thinking（决策语义由 thinking 的"决策"步承载）
- thinking 每步来自第一步分析的真实判断（归属层铁律/标签体系/模板选择/同作者预检），**禁止事后编撰**
- 涉及已登记博主：targets 同时含 `type:"blogger"` 言论条目（落 DB 单轨） + `bloggerUpdated:true`
- 旧数据 `to[]` 字符串数组自动兼容归一化
- **路径书写语义（2026-09-01 用户确认，写入侧硬约束）**：自由文本（reason/thinking/basis/verify.detail）中 `.md` 完整路径 = 写入方承诺该文件真实存在（本次检索命中或本条产物/源），前端渲染为可点击《文件名》跳 Obsidian；假想/被否决/未创建条目一律写《名称》（不带 `.md`）渲染为纯文本。前端存在性校验（vault 索引 ∪ 本条产物）仅兜底质检，权威判定在写入侧（规则源：investment-refine/references/refine-schema.md 四）

## 4. 决策链路图规范（2026-08-31 v2：用户拍板旧 10 节点太死板、信息太少，改真实思考时间线）

**v2 = 思考时间线（`buildThinkingFlow(r)`，纯 DOM，替换 mermaid 固定流程图）**：

```
源文件卡 → [拆分决策] → 每条产物一条"思考轨道"：
  ▸ 产物 N · 文件名 [类型·层] [关系码]
     每一步 = kind 徽章 + 推理文本
       决策步（kind 含"决策"/"排除"）→ 红点强调（菱形语义）
       quote → 原文引用块（触发该步的原文句）
       alt → 备选/否决块（✗ 被否决的方案 + 理由）
  → 产物卡（点击在 Obsidian 打开）＝链路终点
```

> 2026-09-01 用户决定：移除 `[校验]` 收尾节点，「落为产物」即终点（verify 数据仍落库，仅不渲染）。

- **数据**：thinking v2 = 自由长度对象数组 `[{kind,text,quote?,alt?}]`（真实推理步，见 investment-refine SKILL.md）；旧 5 步字符串数组/合并字符串自动降级解析（kind=识别/价值/归类/关系/生成）
- **判断语义保留**：真实分叉数据（归属层/关系决策、备选否决）以"决策步红点 + alt 否决块"呈现；不再为无分叉数据画菱形
- **关系判断职责边界（保持）**：提炼时关系判断 = 生成决策（thinking 中 kind 含"决策"的关系步）；审查 C3/C7 = 写后质检，不重复
- **信息量要求**：每步保留完整推理文本（不截断）、原文引用、备选否决——这就是"具象化"的信息来源；禁止空话步骤（如"价值：值得提炼"）

## 5. 产物展示约定（2026-08-17 最新）

- **单产物**：`源 ⟶ 产物` 链
- **多产物**：`源 ⟶` 后产物徽章**横向并联**（flex gap 分隔、产物间无箭头、自动换行）——体现「一个源分出多个并列产物」；**不用 SVG 分叉图**（用户试用后否决，改回纯 CSS 并联）
- 产物徽章 title = 完整路径；blogger 类型粉色标记

## 6. 前端实现要点（改渲染必读）

- 思考时间线（v2，2026-08-31 起）：`buildThinkingFlow(r)` 纯 DOM 渲染（`.tk-*` 样式）；旧数据 `parseThinkingV2` 降级解析；产物卡 `.tk-product` 绑 click → `openInObsidian(path)`。~~mermaid 版 `buildFlowMermaid(r)` 已弃用~~（保留函数作历史参考，不再调用）
- 交互：全屏覆盖层 + 滚动容器；上一篇/下一篇导航
- **博主列表排序（2026-09-13 用户要求）**：**按言论数量降序，与「特别关注」无关**，**已删除的一律排最后**。原实现第一顺位是 `special`，导致特别关注的几位总霸占前几名、言论多的博主反而被压在下面。特别关注只保留名字前的 `★` 星标，**不参与排序**。排序在服务端 `/api/blogger/list`（`list.sort`：`deletedAt` → `stmtCount` → `tradeCount` → `fileCount`），前端 `renderBloggerList()` **不再二次排序**；点星标走 `updateBloggerRowStar()` 就地更新那一行，不重建列表。

## 7. 设计铁律（改任何前端必须遵守）

- 持续动画默认禁止；backdrop-filter 仅浮层（≤10，当前 5）；无粒子/Canvas 背景动画；无 setInterval UI 轮询
- **监听器模块级单例**：持久元素重渲染时重复绑定的监听器必须只绑一次（0.11.1 教训：scroll 监听器累积泄漏 → 越用越卡）
- 自检：backdrop-filter ≤10、持续动画 0、定时器 0
- 教训：粒子 + blur(80px) + 82 个 backdrop-filter → Renderer CPU 107%（v0.8-v0.9.5 五轮清干净）

## 8. 其他

- 主题：10 主题 × 深浅 2 模式，CSS 变量实现；决策链路图颜色 getComputedStyle 动态读 + hex 校验兜底
- 看板数据在 `data/`，**别手动改 JSON**，一律走 API（否则操作日志/索引不同步）
- 验证：playwright + 系统 Chrome（`executable_path` 指定）；`node --check web/app.js`；jsdom 只能看逻辑不能信布局

## 8.5 本地看板运维（2026-09-11 补充）

| 项 | 值 |
|:---|:---|
| 服务 | launchd `com.investment-console`（`~/Library/LaunchAgents/com.investment-console.plist`，KeepAlive=1，端口 8698） |
| 启动器 | **`~/Project/investment-console/scripts/run-server.sh`**（plist 的 ProgramArguments 指向它）——按「WorkBuddy `versions/current` → 任一已装版本 → PATH 里的 node」解析 node 后 exec server.js |
| 重启 | `launchctl kickstart -k gui/$(id -u)/com.investment-console`；改 plist 后用 `launchctl bootout` + `launchctl bootstrap gui/$(id -u) <plist>` |
| 日志 | `~/Library/Logs/investment-console.log`（stdout+stderr 合并） |
| 健康检查 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8698/` → 200；`launchctl list \| grep investment-console` → 第二列为退出码（非 0 即异常） |

> **踩过的坑（2026-09-11）**：plist 原先写死 `~/.workbuddy/binaries/node/versions/22.22.2-2/bin/node`，WorkBuddy 升级把该版本删掉后**服务静默起不来**——`launchctl list` 显示退出码 `78`、端口无监听，但日志里没有任何报错（因为根本没启动到 node）。**排查口诀**：退出码非 0 且日志无新增 → 先验 `ProgramArguments` 里的可执行文件是否存在。现已改为启动器脚本自愈。
**数据库注释约定（2026-09-11 补齐）**：`investment_kb` **每表每字段均带 COMMENT**（约定写在权威文件 `~/Ai/tools/investment-kb/investment_kb.sql` 文件头）。新增表/字段后跑审计：

```bash
node ~/Project/investment-console/scripts/audit-schema-comments.js           # 列清单
node ~/Project/investment-console/scripts/audit-schema-comments.js --strict  # 有缺失则退出码 1
```

审计口径：只读视图 `statements` 无列注释概念，自动排除。**当前状态：表注释 22/22、列注释 328/328**（六张帖子表与 `_sub`/`_rel` 表均已补齐；`blogger_statements_legacy`、被重启窗口期误建的空表 `statement_reviews` 均已清理，见 framework-rules #39/#44）。

**权威 schema 是生成物（2026-09-12 起）**：改库后必须重新导出 + 回放校验，否则文件与实库漂移（本轮就抓出过视图缺列、表名不一致）：

```bash
node ~/Project/investment-console/scripts/export-schema.js        # 实库 → ~/Ai/tools/investment-kb/investment_kb.sql（含 dict 内容快照）
node ~/Project/investment-console/scripts/verify-schema-replay.js # 空库回放 + 逐列类型/注释比对；一致退出码 0，漂移 1
```

> **连接 collation 坑（2026-09-12）**：服务端与脚本连 MySQL 必须用 `charset: 'utf8mb4_unicode_ci'`。沿用 `'utf8mb4'` 会落到 `utf8mb4_general_ci`，与视图里字面量派生的列（`utf8mb4_bin`）比较时直接报 `Illegal mix of collations`（`COALESCE(content_type,'view')<>'trade'` 这类写法首当其冲）。

**读缓存（2026-09-12 起，Redis）**：看板读 MySQL 的热点走 Redis 缓存——键格式 `ik:<域>:v<epoch>:<hash>`，
**写操作换一个新 epoch（`SET`）令全部旧键立即失效**（TTL 300s 兜底），Redis 不可用时静默回退直连 MySQL（缓存绝不阻断业务）。
覆盖：博主列表计数、博主详情、帖子列表、买卖列表、控制台主题列表/详情。运维：

```bash
bash ~/Project/investment-console/scripts/cache-stats.sh                  # 看板侧命中率 + 服务器 Redis 状态 + 隧道
python3 ~/Project/investment-console/scripts/redis-inspect.py keys        # 缓存里有什么（键/大小/TTL/值预览）
python3 ~/Project/investment-console/scripts/redis-inspect.py get '<key>' # 单键的值（自动解压+格式化）
curl -s http://127.0.0.1:8698/api/cache/stats                 # 进程内命中/未命中/键数
curl -s -X POST http://127.0.0.1:8698/api/cache/clear         # 手动失效（epoch+1）
```

> Redis 装在服务器 `/home/jianglb/redis`（systemd `redis-investment`），看板**直连 `106.55.14.116:6379`**
> （安全组已放行；备用通路为 SSH 隧道，`scripts/redis-endpoint.sh [check|direct|tunnel]` 可一键切换复验）。
> **缓存值 >2KB 自动 gzip+base64 压缩**（`g:` 前缀）：98KB 的主题详情压到 32KB，热读 0.14s→0.05s——缓存值同样跨公网回传，
> 不压缩等于把「查库 RTT」换成「传大 JSON 带宽」。客户端另有三个 WAN 必备健壮性：命令超时即重连（空闲连接会被 NAT 静默掐死）、
> 15s 心跳保活、`epoch` 键被 LRU 淘汰时生成随机 epoch 而**不回落固定值**（否则会读到本该失效的老键）。
> 安装/配置/安全细节与查看命令见 server-ops skill。

> **结构约定速查**：帖子一律 `post`（六张分表 `statement_trade`/`statement_predict`/`statement_research`/`statement_view`/`statement_insight`/`statement_chat` + 视图 `statements`），一条帖子只落一张表｜四维度走 `实体关联表`｜子表 `_sub`、关联表 `_rel`｜**弃用表删前备份后直接 DROP**（不留 `_del`）｜可枚举值进 `dict`、字段注释标注 `dict.type`｜vault 文件索引/标签**不落库**（服务端内存扫描 `buildIndex()`）｜`wiki_ref` 存 vault 相对路径、前端生成 `obsidian://` 本地打开链接。详见 framework-rules #44。

> 另一坑：旧实例若成为孤儿进程（PPID=1）会与新实例抢状态；`launchctl kickstart -k` 之前先 `pgrep -fl "node server.js"` 确认没有残留。

## 9. 编排者看板联动清单（自 SKILL.md 下沉）

流水线结果写入本地运行的投资看板（`http://127.0.0.1:8698`，端口 8698，launchd 托管 com.investment-console；读本地 iCloud vault、连远程 MySQL；连接与 token 见 `Ai/tools/investment-console-mcp/README.md`），看板不产生知识、只呈现结果：

- **提炼** → `MCP refine_record`（refine 第四步已实现，targets 含 thinking v2 自由对象数组/basis/relation）→ 提炼时间轴 + 决策链路图
- **审查** → `MCP review_record`（review 第四步已实现）→ 审查模块（2026-08-16 起不再产出 md 审查报告）
- **待复核**（2026-09-12 用户要求）→ `MCP pending_decision`：agent 处理不了的帖子/问题进队（带候选答案），
  用户在看板「待复核」页（菜单在「审查」**前面**，带未处理数角标）点选或作答；**下次审查把答复内化成规则/别名/案例并回写 `internalized`**，同类帖子以后不再问用户（framework-rules #49）。
  三个 tab：待你裁决（open）/ 待内化（resolved 且 internalized 空）/ 全部；卡片含原文片段、候选按钮、自由作答与「已内化→落点」。
  **用户在卡片上还能点「建议删除这条言论」**（＝帖子质量不够却被提炼了，**理由必填**）：答复落成 `verdict=delete`，
  审查时 `list status=pending_internalize verdict=delete` 就是**必须执行的删除清单**（删完 `internalize` 回写「已删除言论 #id + 规则落点」，
  页面随之显示「言论已删除」）；删除理由要追加到 `refine-schema.md` 的「用户删过的类型」判据表，让同类帖子下次不落库（framework-rules #50）。`blogger_statement` 遇到解析不出的标的名会**自动上报**一类（warnings 里带编号）。
- **原文留档**（2026-09-11 新增）→ `post_history` 表：采集验收后由 post-fetch 调 `scripts/import-post-history.js` 落库（摘要帖/无链接帖不入库）；提炼侧第 0.5 步与补采场景用 `MCP post_history`（`check` 查窗口内已留档、`get` 取原文）——**目的是避免重采**，不参与提炼判定。规则见 framework-rules #41
- **待读/已读**（2026-09-12 用户要求）→ 言论「阅读状态」：`statement_*` 六表的 `is_read`（默认 1=已读），
  看板四层徽标＝菜单角标（总待读）/ 四维度 tab 角标 / 列表卡右上角待读数 / 言论卡**左侧红条**（不写文字，用户 2026-09-12 要求）；
  用户把言论卡**向上滑出可视区**（首屏就在屏上的不算）由前端 `POST /api/statement/read` 置已读（**只写库、界面不自动刷新**——
  切菜单/换维度重读数据时标识才消失），四个维度 tab 角标与菜单角标**同款同位置**（`.nav-badge`），agent 侧维护用 `MCP statement_read`；
  **言论列表排序＝未读优先 + 时间倒序**（服务端 SQL 与前端混排同一口径）
  （stats/read/unread/all-read）。**agent 不主动标待读**（见 framework-rules #51）
- **决策链路图 v2（思考时间线，2026-08-31 起替代旧 10 节点流程图）**：源→拆分决策→每条产物一条思考轨道（kind 徽章 + 推理文本，决策步红点、quote 原文引用、alt 否决块）→产物卡即终点；判断只留给有真实分叉处（归属层/关系），关系判断落在 thinking 的「决策」步，审查 C3/C7=写后质检不重复。详见 console-guide §4
- **产物展示**：多产物**横向并联**（产物徽章并排、无箭头，不用 SVG 分叉图——用户试用后否决）
- 失败处理：API 失败不阻断主流程，汇报提示「看板数据未写入」
