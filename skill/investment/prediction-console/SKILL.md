---
name: prediction-console
description: 维护投资看板预测控制台（MySQL 存储，方案 A：vault 不再存控制台 Markdown）。三控制台（个股/行业/市场）的预测录入、状态验证、言论跟踪全部走 MCP console_* 工具落库投资看板。触发词：「预测控制台」「录入预测」「更新预测」「预测跟踪」「预测验证」。排除条件：纯聊天、非投资预测类内容。
version: 2.1.0
---

# 预测控制台维护（MySQL 版）

> **2026-08-31 方案 A 落地**：预测控制台由 vault Markdown 迁移至 MySQL（investment_kb 预测域 4 表 + 4 字典），vault 不再存控制台文件。所有读写走 MCP 工具（`mcp__investment-console__console_*`）。博主控制台仍由 `bloggers` 表 + `*_blogger` MCP 工具管理。

## Default Stance

### 核心原则
- **三控制台分工**：`consoleType=stock`（个股，标题含代码）/ `industry`（行业，申万最下级标签）/ `market`（市场，A股/港股/美股大盘）
- **一主题一段**：每只股票/行业/市场独立 `prediction_subjects` 记录（含代码字段），禁止合并（如"神火/云铝"合成一段）
- **去重由 DB 兜底**：`console_add_prediction` 按（主题+预测日期+预测人+内容）唯一键幂等，重复自动跳过并返回 `duplicate: true`
- **验证留痕由服务端强制**：状态改为 `verified_correct/verified_wrong/revoked` 时 `verify`（result+basis）必填，缺了直接报错——状态枚举里禁止夹带证据
- **言论单轨**：预测落 `prediction_records` 的同时，来源博主言论记 `blogger_statements`（origin 关联）；画像 md 已退役（2026-09-08），不再写任何 vault 画像文件
- **预测两条链路、一处展示**：博主帖子里的预测先作为言论归档（`blogger_statement` `contentType=predict`，言论库按人追责）；纳入验证体系的另走 `console_add_prediction`（带目标价/参考价/验证留痕）。同一判断两侧都有时**必须靠 `origin_id` 关联**（传 `statementId` 或靠服务端相似度自动回填），看板合并成一张卡；未关联即视为重复数据
- **码值权威源**：`content_type`(stmt_content_type)/`stance`/`status`(prediction_status) 等枚举以 MySQL `dict` 表为准，`remark` 里写判据；新增分类改字典不改代码
- **倒序展示**：看板按预测日期倒序（月级精度排当月 1 日、展示还原为 yyyy-MM）

### 禁止行为
- 绝不重复录入已有预测（依赖 DB 幂等，但录入前仍应查重避免噪音）
- 绝不在行业主题写完整路径（只写最下级，如"白酒"非"行业/食品饮料/白酒"）
- 绝不在个股主题省略股票代码
- 绝不用回复日期代替原始判断日期
- 绝不为月级日期编造收盘价；拿不到精确日收盘价就留空
- 绝不录入不可证伪/纯叙事言论进预测记录（宏观叙事、情绪判断归言论跟踪或跳过）
- **绝不写 vault 预测控制台文件**（已迁移 MySQL；存量 md 已移废纸篓）

---

## Workflow

### 第一步：识别预测内容
从用户输入（截图/链接/文字）提取：预测人、个股/行业/市场、预测内容、目标价、时间框架

### 第二步：判断 consoleType
- 有具体股票代码 → `stock`（个股）
- 行业/板块/商品（白酒、AI、碳酸锂等）→ `industry`
- 大盘走势（A股牛熊、港股、美股）→ `market`

### 第三步：查重
`console_list_subjects(consoleType)` 找主题 → `console_get_subject` 看已有预测；已有相同（主题+日期+预测人+内容）则跳过。DB 唯一键为最终兜底。

### 第四步：录入预测
调 MCP `console_add_prediction`：

| 参数 | 规则 |
|:---|:---|
| `consoleType` | stock/industry/market（必填） |
| `subjectName` | 主题名：个股=名称（如 贵州茅台）、行业=最下级（白酒）、市场=A股 |
| `subjectCode` | 个股代码（600519/MU/01104），行业市场可省；**个股必填** |
| `subjectMarket` | 个股市场：`sh`沪/`sz`深/`hk`港/`kr`韩/`us`美（**个股必填**，看板据此渲染市场徽；A+H 双上市默认 A 股即 `sh`/`sz`，除非文章明确讨论港股） |
| `subjectHkConnect` | 是否港股通（布尔，**仅 `subjectMarket=hk` 时适用**，看板加绿「通」徽；非港股省略不填） |
| `predictDate` | 原始判断日期，精确到日 `yyyy-MM-dd`；仅知月份用 `yyyy-MM`（datePrecision=month） |
| `predictor` | 博主名或"自己" |
| `content` | 核心判断，保留原文关键表述 |
| `refPrice` | 当前价/参考价：个股=预测日收盘价（不复权，腾讯 kline API），行业/市场=商品价/指数点位；月级日期留空 |
| `targetPrice` / `targetDate` | 有明确数字/区间才填（如 2023~2027+），否则省略 |
| `sourceUrl` | 原文链接 |
| `statementId` | 该预测源自哪条博主言论（`blogger_statements.id`）；**同一条判断已由言论链路落库时必传**，漏传则服务端按「同主题+同链接+相似度≥0.5」自动回填关联 |
| `status` | pending/verifying/verified_correct/verified_wrong/revoked（缺省 pending） |

### 第五步：状态变更（强制验证留痕）
调 MCP `console_update_status`：`{predictionId, status, verify:{verifyDate, verifier, basis, result, note}}`
- 状态改 `verified_correct/verified_wrong/revoked` 时 `verify.result`（correct/wrong/revoked）+ `verify.basis`（量化证据）**必填**，服务端强制
- 判定口径：方向正确即记 correct，数值偏差进 note（如"预测-35%实际-50%→correct，备注跌幅大于预期"）；方向相反/关键数值未兑现记 wrong

### 第六步：言论跟踪
同来源后续增强/反驳言论 → MCP `console_add_track`：`{subjectId, trackDate, source, content, direction=enhance/refute/neutral, sourceUrl}`
- **用途边界（2026-09-03）**：本工具只记"对某条已有预测的后续跟踪"（该判断被加强还是被推翻）。**博主言论/观点/预测/研究/心得的归档不走这里**，一律走 `blogger_statement`（涉个股/行业/市场时传 `subjectId`；预测类言论用 `contentType=predict`）。
- **`source` 必须写发言者本人**（博主名或"自己"），**禁止写「雪球采集-2026年8月11日」这类批次名**。

### 第七步：（已退役）同步博主画像
2026-09-08 画像单轨化：本步取消。来源言论已由 `blogger_statement` 落库（与预测经 `origin_id` 关联），画像字段存 `bloggers` 表；**禁止再读写 vault 画像文件**。

---

## Output Format

### 主题命名
- 个股：`{名称}` + `subjectCode`（贵州茅台 / 600519）
- 行业：最下级名称（白酒、AI与算力、锂）
- 市场：A股/港股/美股

### 状态枚举（dict_prediction_status）
`pending`(待验证) / `verifying`(验证中) / `verified_correct`(已验证正确) / `verified_wrong`(已验证错误) / `revoked`(已撤销)

---

## Relative Files

| 场景 | 加载文件 | 方式 |
|:---|:---|:---|
| MCP 工具调用 | Ai/tools/investment-console-mcp/README.md | 读取 |
| 行业分类标准 | investment-framework/references/tag-taxonomy.md | 读取 |
| 个股/指数价格 | 腾讯 kline API（web.ifzq.gtimg.cn，不复权） | 执行 |
| 博主画像 | MySQL `bloggers` 表（单轨） | 经 add/update_blogger 读写；画像 md 已退役（仅存待删比对副本） |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（三控制台分工、验证留痕、方案 A MySQL 唯一存储） |
| 2 | tag-taxonomy 申万行业分类标准 |
| 3 | 腾讯 kline API 不复权收盘价 |
| 4 | MySQL dict_* 字典码（服务端强制校验） |

---

## 自检

- [ ] consoleType/主题/日期/预测人/内容是否齐全？
- [ ] 个股是否带 subjectCode？行业是否最下级？
- [ ] 个股是否填了 subjectMarket（sh/sz/hk/kr/us）？港股是否判定 subjectHkConnect（非港股不填）？
- [ ] 是否已查重（console_get_subject）？DB 幂等是否返回 duplicate？
- [ ] 预测日期是否为原始判断日期？月级是否走 yyyy-MM？
- [ ] 状态变更是否带 verify（result+basis）？
- [ ] 源自已有言论的预测是否带了 `statementId`（或确认自动关联命中，返回 `linkedStatementId`）？
- [ ] 来源言论是否已落 `blogger_statements` 并与预测 `origin_id` 关联？（画像 md 已退役，禁写）
- [ ] 是否未写 vault 预测控制台文件？
