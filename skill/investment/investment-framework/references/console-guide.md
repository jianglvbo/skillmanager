# 投资看板（investment-console）联动指南

> 本文件描述流水线（提炼/审查/言论追踪）与投资看板的数据契约与渲染约定，只保留**执行流水线时必须知道**的部分。

## 1. 看板是什么

纯前端 + 零依赖 Node 轻服务，**本地运行**（`~/Project/investment-console`，端口 8698，launchd 托管 com.investment-console）。读本地 iCloud vault（`config.vaultRoot` 指向 Obsidian 库），派生索引与运营记录写**远程共享 MySQL**（`investment_kb`，host 见 config.json；方案 A：预测控制台等已迁库，vault 不再存控制台 Markdown）。MCP 端点 `http://127.0.0.1:8698/mcp`（Bearer token 见 `Ai/tools/investment-console-mcp/README.md`）。**看板不产生知识，只呈现流水线结果。**

## 2. 数据契约（流水线写入）

| 写入方 | 端点 | 数据 | 看板呈现 |
|:---|:---|:---|:---|
| investment-refine 第四步 | `MCP refine_record` | targets[]（含 thinking v2 思考链路/basis/relation） | 提炼时间轴 + 思考时间线（决策链路图） |
| investment-review 第四步 | `MCP review_record` | 结构化审查（checks/groups/recycle） | 审查模块（2026-08-16 起不再产出 md 审查报告） |
| 粗制品评分/加工 | `POST /api/coarse/score` `/process` | 调本地 dsh | 粗制品模块 |
| post-fetch 第三步之二 | `scripts/import-post-history.js`（批量）/ `MCP post_history`（单条 upsert） | 采集原文落 `post_history` 表（提炼前原文留档，**唯一用途=避免重采**） | 不呈现（后端留档；`post_history action=get/check` 供提炼与补采读取） |
| prediction-console（言论追踪·2026-09-11 收敛：预测即言论行，唯一预测表 `stmt_predict`；`predictions_del` 留档） | `MCP console_add_prediction` / `console_update_status` / `console_add_track` | 预测/验证留痕/言论跟踪（个股/行业/市场三控制台，含 subjectMarket/subjectHkConnect） | 言论追踪模块（市场徽+港股通徽、验证留痕） |

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

审计口径：只读视图 `blogger_statements` 无列注释概念，自动排除。**当前状态：表注释 28/28、列注释 406/406**（六张 `stmt_*` 分表此前整表无注释，2026-09-11 补 135 列 + 8 张表注释；权威文件同步实库，并补齐此前遗漏的 `blogger_trades`/`statement_reviews`/`stmt_id_seq` 三表定义；`blogger_statements_legacy` 已于同日校验后删除，见 framework-rules #39）。

> 另一坑：旧实例若成为孤儿进程（PPID=1）会与新实例抢状态；`launchctl kickstart -k` 之前先 `pgrep -fl "node server.js"` 确认没有残留。

## 9. 编排者看板联动清单（自 SKILL.md 下沉）

流水线结果写入本地运行的投资看板（`http://127.0.0.1:8698`，端口 8698，launchd 托管 com.investment-console；读本地 iCloud vault、连远程 MySQL；连接与 token 见 `Ai/tools/investment-console-mcp/README.md`），看板不产生知识、只呈现结果：

- **提炼** → `MCP refine_record`（refine 第四步已实现，targets 含 thinking v2 自由对象数组/basis/relation）→ 提炼时间轴 + 决策链路图
- **审查** → `MCP review_record`（review 第四步已实现）→ 审查模块（2026-08-16 起不再产出 md 审查报告）
- **预测控制台**（2026-08-31 方案 A：MySQL 唯一存储，vault 不再存控制台 Markdown）→ `MCP console_list_subjects / console_get_subject / console_add_prediction / console_update_status / console_add_track`（见 prediction-console skill v2.0）→ 看板预测控制台模块（个股/行业/市场三页签）
- **原文留档**（2026-09-11 新增）→ `post_history` 表：采集验收后由 post-fetch 调 `scripts/import-post-history.js` 落库（摘要帖/无链接帖不入库）；提炼侧第 0.5 步与补采场景用 `MCP post_history`（`check` 查窗口内已留档、`get` 取原文）——**目的是避免重采**，不参与提炼判定。规则见 framework-rules #41
- **决策链路图 v2（思考时间线，2026-08-31 起替代旧 10 节点流程图）**：源→拆分决策→每条产物一条思考轨道（kind 徽章 + 推理文本，决策步红点、quote 原文引用、alt 否决块）→产物卡即终点；判断只留给有真实分叉处（归属层/关系），关系判断落在 thinking 的「决策」步，审查 C3/C7=写后质检不重复。详见 console-guide §4
- **产物展示**：多产物**横向并联**（产物徽章并排、无箭头，不用 SVG 分叉图——用户试用后否决）
- 失败处理：API 失败不阻断主流程，汇报提示「看板数据未写入」
