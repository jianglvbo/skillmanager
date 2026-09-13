---
name: prediction-console
description: 维护投资看板预测控制台（MySQL 存储，方案 A：vault 不再存控制台 Markdown）。三控制台（个股/行业/市场）的预测录入、状态验证、言论跟踪全部走 MCP console_* 工具落库投资看板。触发词：「预测控制台」「录入预测」「更新预测」「预测跟踪」「预测验证」。排除条件：纯聊天、非投资预测类内容。
version: 2.1.0
---

# 预测控制台维护（MySQL 版）

> **2026-08-31 方案 A 落地**：预测控制台由 vault Markdown 迁移至 MySQL（investment_kb 预测域 4 表 + 4 字典），vault 不再存控制台文件。所有读写走 MCP 工具（`mcp__investment-console__console_*`）。博主控制台仍由 `blogger` 表 + `*_blogger` MCP 工具管理。

## Default Stance

### 核心原则
- **组合与代号不入主题（2026-09-12）**：雪球组合（`$名称(ZH123456)$`）不是个股/行业/市场主题，**不建 subject**（组合信息留在帖子 `target` 文本里）；纯小写拉丁短名（如 `cww`）是未识别代号，须先还原真名再建主题。建主题接口已内置门禁拦截，报错即按提示改写。

- **三控制台分工**：`consoleType=stock`（个股，标题含代码）/ `industry`（行业，申万最下级标签）/ `market`（市场，**封闭清单 9 个**：A股/港股/美股/韩股/汇率/虚拟货币/美债/国债/日债）
- **一主题一段**：每只股票/行业/市场在实体三表（`stock`/`industry`/`market`）各占一行，个股含 `code`+`market_code` 字段，禁止合并（如"神火/云铝"合成一段）
- **去重由 DB 兜底**：`console_add_prediction` 按（主题+预测日期+预测人+内容）唯一键幂等，重复自动跳过并返回 `duplicate: true`
- **验证留痕由服务端强制**：状态改为 `verified_correct/verified_wrong/revoked` 时 `verify`（result+basis）必填，缺了直接报错——状态枚举里禁止夹带证据
- **言论单轨（2026-09-11 收敛：预测即言论行）**：预测**就是** `statement_predict` 表里的一行 `predict` 言论——与博主言论同表同 id，结构化预测字段（参考价/目标价/目标时间/状态/验证结果）就在该行本体，**没有第二张预测表**；画像 md 已退役（2026-09-08），不再写任何 vault 画像文件
- **预测一条链路、一处展示**：博主帖子里的预测先由 `blogger_statement`（`contentType=predict`）落库；要纳入验证体系时调 `console_add_prediction` 并**传 `statementId` 复用同一行**补上目标价/参考价/状态（不传则新建一条预测言论）。同一判断**只有一行**，不存在两侧重复，也不需要任何关联表
- **码值权威源**：`content_type`(post_content_type)/`stance`/`status`(prediction_status) 等枚举以 MySQL `dict` 表为准，`remark` 里写判据；新增分类改字典不改代码
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
- 大盘走势/指数（A股牛熊、港股、美股）→ `market`，但要**落到具体市场**（A股大盘→`A股`、美股大盘→`美股`）——`大盘` 本身不是市场主题，服务端会拒（2026-09-12 用户拍板：市场只有 A股/港股/美股/汇率/虚拟货币/美债/国债/日债这种）

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
| `statementId` | 该预测源自哪条博主言论（`statement.id`）；**同一条判断已由言论链路落库时必传**——预测即言论行，传了就在该行上补预测字段与维度关联（漏传而带 `sourceUrl` 时，服务端按同链接复用已有 `statement_predict` 行；仍无则新建） |
| `status` | pending/verifying/verified_correct/verified_wrong/revoked（缺省 pending） |

### 第五步：状态变更（强制验证留痕）
调 MCP `console_update_status`：`{predictionId, status, verify:{verifyDate, verifier, basis, result, note}}`
- 状态改 `verified_correct/verified_wrong/revoked` 时 `verify.result`（correct/wrong/revoked）+ `verify.basis`（量化证据）**必填**，服务端强制
- 判定口径：方向正确即记 correct，数值偏差进 note（如"预测-35%实际-50%→correct，备注跌幅大于预期"）；方向相反/关键数值未兑现记 wrong

### 第六步：言论跟踪
- **用途边界（2026-09-03）**：本工具只记"对某条已有预测的后续跟踪"（该判断被加强还是被推翻）。**博主言论/观点/预测/研究/心得的归档不走这里**，一律走 `blogger_statement`（涉个股/行业/市场时传 `subjectId`；预测类言论用 `contentType=predict`）。
- **`source` 必须写发言者本人**（博主名或"自己"），**禁止写「雪球采集-2026年8月11日」这类批次名**。

### 第七步：（已退役）同步博主画像
2026-09-08 画像单轨化：本步取消。来源言论已由 `blogger_statement` 落库（**预测即言论行，本就是同一行，无 origin_id 关联**），画像字段存 `blogger` 表；**禁止再读写 vault 画像文件**。

---

## Output Format

### 主题命名
- 个股：`{名称}` + `subjectCode`（贵州茅台 / 600519）
- 行业：最下级名称（白酒、AI与算力、锂）
- 市场：A股/港股/美股/韩股/汇率/虚拟货币/美债/国债/日债（封闭清单；A股市场/沪深、加密货币、人民币汇率、美国国债、日本国债 等写法服务端会自动归一到标准名，`A股市场` 是 `A股` 的旧名/别名）

### 状态枚举（dict_prediction_status）
`pending`(待验证) / `verifying`(验证中) / `verified_correct`(已验证正确) / `verified_wrong`(已验证错误) / `revoked`(已撤销)

---

## Relative Files

| 场景 | 加载文件 | 方式 |
|:---|:---|:---|
| MCP 工具调用 | Ai/tools/investment-console-mcp/README.md | 读取 |
| 行业分类标准 | investment-framework/references/tag-taxonomy.md | 读取 |
| 个股/指数价格 | 腾讯 kline API（web.ifzq.gtimg.cn，不复权） | 执行 |
| 博主画像 | MySQL `blogger` 表（唯一权威） | 经 add/update_blogger 读写；**画像 md 已彻底废弃**（2026-09-12：服务端删除全部回写代码与 `/api/blogger/resync`，存量文件已于 2026-09-14 按用户指示清空（49 个画像文件先清 inbound 引用、再移入废纸篓，备份在 ~/Project/investment-console/backups/blogger_profile_20260914000617/）） |

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
- [ ] 来源言论是否已落 `statement`？（预测即言论行——`console_add_prediction` 是否传了 `statementId` 复用那一行，而非又新造一行；画像 md 已退役，禁写）
- [ ] 是否未写 vault 预测控制台文件？

> **2026-09-11 二次收敛（预测即言论行；用户问「predictions 和 statement_predict 不是重复吗？」后拍板）**：独立预测表 `predictions` 整体退役（改名 `predictions_del` 留档，101 条已全量并入 `statement_predict`：URL 命中 37 / 新建言论 14 / 跨表改类型 26 / 内容匹配 24，按 URL 100% 可回溯），`prediction_records`→`prediction_records_del`，旧 `prediction_tracks`→`prediction_tracks_del`。
> - **唯一预测表 = `statement_predict`**：一条预测＝一条 `predict` 言论，同表同 id；结构化字段在该行本体，读取经视图单表直取（无 JOIN），前端字段名零变更。
> - **`prediction_stmt_rel` 随之删除**（预测↔言论本来就是同一行，无需关联）；**跟踪表 `statement_rel` 也已退役**（2026-09-12 用户选 A：长期 0 行、看板无读路径），`console_add_track` 工具下架——预测的后续演进看后续言论自身的时间线即可。
> - `console_add_prediction`：`statementId` **传了就复用该行**（补预测字段+维度关联），不传则新建预测言论并返回其 id。
> - `console_update_status`：写 `statement_predict.status_code`（pending/verifying/verified_correct/verified_wrong/revoked），同步最近 `verify_date`/`verify_result`；另留痕子表 `statement_verify_sub.statement_id`（同预测重复验证为覆盖式 upsert，保留最近一次；该表**不设外键**）。
> - 言论侧写入 `contentType=predict` 即自动成为预测，无需再调 `console_add_prediction`；要加目标价/验证状态时再补调一次（传 `statementId`）。
