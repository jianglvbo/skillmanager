# 提炼落库模板（POST /api/refine/record · schema）

> 由 investment-refine SKILL.md 第四步引用。**提炼完成后按本模板规定字段，`MCP 工具 `refine_record`（REST POST /api/refine/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）` 写入投资看板**，看板完整展示产物 + 决策链路。

---

## 一、落库对象结构（单次提炼 = 一条 record）

```json
{
  "id": "ref-xxx",
  "at": 1786809179530,
  "from": "工作区/原始资源/牛奶行业点评.md",
  "sourceType": "raw",
  "source": "[原文](https://xueqiu.com/.../XXXXXX)",
  "targets": [
    {
      "path": "我的/行业/牛奶行业.md",
      "type": "wiki",
      "layer": "other",
      "category": "industry",
      "tags": ["行业", "周期"],
      "basis": "原文「原奶价格已跌至 2018 年以来低位，去产能进入中后期…」",
      "relation": "new"
    }
  ],
  "reason": "整体拆分决策说明",
  "steps": ["读取原文", "归属层判断", "创建条目", "更新博主档案", "校验"],
  "bloggerUpdated": false,
  "bloggerName": "",
  "verify": { "ok": true, "detail": "verify-format.py 0 问题" },
  "verificationHints": ["该判断可后续建分析档案做结果跟踪"]
}
```

---

## 二、字段规范（必须遵守）

| 字段 | 必填 | 类型 | 说明 |
|:---|:---|:---|:---|
| `from` | ✅ | string | 源材料相对路径（原始资源 或 粗制品） |
| `sourceType` | 建议 | string | `raw`=原始资源 / `coarse`=粗制品直提（帖子集 #29 / 直投 #30）；缺省按 from 含「粗制品」推断 |
| `source` | 建议 | string | 原文链接（markdown 格式 `[标题（博主 日期）](url)`） |
| `targets` | ✅ | array | **产物列表**，每项见下 |
| `reason` | 建议 | string | 整体拆分决策说明（为何拆成这些条目） |
| `steps` | 建议 | array | 提炼步骤时间轴（读取→分析→创建→档案→校验） |
| `bloggerUpdated` | 建议 | bool | 是否更新了博主档案（言论追踪） |
| `bloggerName` | 建议 | string | 涉及博主名 |
| `verify` | 建议 | object | 产出校验结果 `{ok, detail}`（verify-format.py） |
| `verificationHints` | 建议 | array | 可验证判断提示（建分析档案建议） |

### `targets[]` 每项

| 字段 | 必填 | 说明 |
|:---|:---|:---|
| `path` | ✅ | 产物相对路径 |
| `type` | ✅ | 英文码：`wiki`=框架条目 / `blogger`=博主言论（DB 落库，画像 md 已退役） / `macro`=宏观 |
| `layer` | 建议 | **英文码**（见下方字典表）：`my`/`blogger`/`other`/`macro`/`workspace` |
| `category` | 建议 | **英文码**（见下方字典表）：`analysis_framework`/`trading_system`/`investment_mentality`/`investment_insight`/`stock`/`industry`/`macro` |
| `tags` | 建议 | 标签（来自标签体系，一级前缀） |
| `basis` | ✅ | **依据**：原文支撑该条目的关键句引用——回答"从哪句话提炼的" |
| `thinking` | ✅ | **思考链路 v2**（2026-08-31）：自由长度对象数组 `[{kind,text,quote?,alt?}]`，按真实推理过程记录（观察/疑问/假设/查证/对比/权衡/排除/决策/结论…）；`quote`=触发该步的原文引用、`alt`=备选方案/否决理由；三个决策点（归属层/拆分/关系）必含。**禁止固定 5 步模板套话**（旧格式字符串数组仍兼容展示） |
| `relation` | 建议 | **英文码**：`new`/`append`/`complement`/`conflict_check`/`other`——判断范围按分层检索链（同作者同类分类 → 全库关键词兜底 → 新建，关键词取产物名拆分+原文实体+标签 3-5 词，检索文件名/标题/标签；见 SKILL.md 第一步第 3 步；与 C7 联动） |

---

## 二B、字典码对照表（避坑 · 2026-08-31 实测）

**`layer`/`category`/`relation`/`type`/`sourceType` 必须传数据库字典英文码，传中文会落库失败（外键约束报错）**。全量对照（源：远端 MySQL `investment_kb` 的 `dict` 单表，`type` 列区分字典域；2026-08-31 schema 整合后由多张 dict_* 合并为单表）：

| 字段 | 字典表 | 合法码（码 → 中文含义） |
|:---|:---|:---|
| `layer` | dict(type=layer) | `my`=我的 / `blogger`=博主 / `other`=其他 / `macro`=宏观 / `workspace`=工作区 / `attachment`=附件 |
| `category` | dict(type=category) | `analysis_framework`=分析框架 / `trading_system`=交易体系 / `investment_mentality`=投资心态 / `investment_insight`=投资心得 / `stock`=个股 / `industry`=行业 / `macro`=宏观 |
| `relation` | dict(type=target_relation) | `new`=新建 / `append`=追加 / `complement`=互补 / `conflict_check`=矛盾预检 / `other`=其他 |
| `type` | dict(type=target_type) | `wiki`=框架条目 / `blogger`=博主言论（DB） / `macro`=宏观条目 |
| `sourceType` | dict(type=source_type) | `raw`=原始资源 / `coarse`=粗制品 |
| 审查 `checks[].status` | dict(type=check_status) | `pass`=通过 / `warn`=警告 / `fail`=失败（`ok`=旧数据遗留，新写入不用；**无 `info`**） |

> **避坑**：落库报 `foreign key constraint fails ... dict_*` 时，用 `SHOW CREATE TABLE {refine_targets|review_checks}` + 对应字典表核对码值，不要猜中文。博主言论目标 `category` 可省略（列可空）。

---

## 三、`type` 取值与看板展示

| type | 含义 | 看板展示 |
|:---|:---|:---|
| `wiki` | 框架条目 | 分类色块 + 归属层徽章 + 产物决策卡 |
| `blogger` | 博主言论（落 DB） | **粉色「言论追踪」标记** |
| `macro` | 宏观 | 琥珀色「宏观」标记 |

`sourceType=coarse` 时看板显示「粗制品直提」徽章；`verify.ok` 显示「校验通过」；`bloggerUpdated` 显示「言论追踪」。

---

## 四、决策一致性（质量保障）

- **自由文本路径书写硬约束（2026-09-01 用户确认，前置约束优于回检兜底）**：`reason` / `thinking`(text/quote/alt) / `basis` / `verify.detail` 等自由文本中，`xxx/yyy.md` 完整路径**只允许**指向「写入时已确认存在于 vault 的文件（本次检索命中）」或「本条 `targets[].path` 产物 / `from` 源」；假想、被否决、未创建的条目一律写《名称》（**不带 `.md`、不带路径**）。看板按此语义渲染：`.md` 路径 = 可点击跳 Obsidian，《名称》 = 纯文本。前端存在性校验只是兜底质检，写入方不得依赖它补救
- `basis`（依据原文句）必须**真实来自原文**，禁止事后编撰
- `thinking` 的「决策」步（归属层/拆分/标签判断）必须来自第一步分析的真实判断：归属层铁律（博主控制台登记）、标签体系、同作者一致性预检
- `relation`（关系）与审查 C7 关联备注提案、C3 矛盾预检联动——提炼时标注的互补/矛盾，审查时据此核对
- 落库失败（看板未启动等）不阻断提炼主流程，但汇报中必须提示「看板数据未写入，需补录」

---

## 五、旧数据兼容

- 旧格式 `to[]`（字符串数组）→ 服务端自动归一化为 `targets[]`（type 按路径推断：`博主/`→blogger、`宏观/`→macro、其余→wiki；layer/category 从路径提取）
- 看板读取兼容 `r.to` / `r.targets` 两种结构

## 六、博主言论分流决策矩阵（自 SKILL.md 第 1.5 步下沉）

雪球博主帖子按语义拆成 N 条言论（一帖多条），每条**先判类型、再定去向**。采集只给发帖时间与形态，内容分类与观点时间在本步判定。

**优先级（2026-09-10 更新）**：**P1 必查必录** = `trade 买卖记录` / `research 研究` / **`predict 预测记录`**（2026-09-10 用户拍板由 P2 提升）→ P2 = `view 观点` / `insight 心得总结` → P3 `chat 闲聊`（高门槛）。

> **`predict` 提为 P1 的理由**：预测是**可验证判断**，漏录即永久丢失验证样本（无法回补准确率）；且看板预测控制台的验证闭环依赖言论库侧可查。

| content_type | 涉及个股/行业/市场 | 去向 | 另落 wiki？ |
|---|---|---|---|
| `trade` | 必是 | `blogger_trade` → `blogger_trades` 表（看板买卖记录；画像 md 已退役不回写）。**方向 `stance` 必填**（看空/看多/中性），有价必标 `price`（开盘竞价位），`note` 只记操作理由。**结构化字段**：`op`/`price`/`marketCap`/`tradeDate` | 否 |
| `research` | 是 | `blogger_statement` → `blogger_statements` 表。**结构化字段**：`dataRefs`（数据来源）/`wikiRef`（已具象化条目） | 仅当沉淀出可复用框架（言论库记事实，wiki 记方法，**不重复记录**） |
| `research` | 否 | — | 能成框架 → wiki（我的/其他/宏观）；不能 → **舍弃** |
| `predict` | 必是 | `blogger_statement` → `blogger_statements`(predict) + 预测控制台。**`stance` 必填**，`view_date` 取博主下判断的时点。**结构化字段（2026-09-10 新增）**：`refPrice`/`targetPrice`/`targetDate`/`datePrecision`/`verifyStatus`/`verifyDate`/`verifyResult` —— 预测验证闭环在言论表内可直接查询，免 JOIN `prediction_records`/`prediction_verifications` | 否 |
| `view` | 是 | `blogger_statement`（含 `stance`）→ 言论库（看板言论追踪） | 否 |
| `view` | 否 | — | 有价值 → wiki；无价值 → 舍弃 |
| `insight` | 是 | `blogger_statement` → 言论库（看板言论追踪）。**结构化字段**：`transferable`（可迁移性）/`wikiRef` | 仅当沉淀方法论 |
| `insight` | 否 | — | 有价值 → wiki；否则舍弃 |
| `chat` | — | 仅当能刻画「擅长与局限 / 投资心态」→ `blogger_statement`；否则**舍弃** | 否 |

**全类型共同字段（2026-09-10 新增）**：`form`（帖子形态：回复/短文/长文/专栏）——取自采集侧摘要行，**零解析读取**，用于分流先验与质检（专栏/长文判 `research` 概率高；回复必先做 `//@` 切分）。

**`predict` 判定三要素（2026-09-04 用户定义）**：① 明确方向（看多/看空/中性）② 未来指向（时间窗："几年后/几个月后/年内"，或事件条件："美国加息/降息""地缘冲突缓和"等）③ 可判对错（含目标位/幅度/点位最佳）。缺任一要素即回落 `view`（当下判断）或 `insight`（复盘心得）；历史复盘叙述**不得**算预测。**易错例**：`白酒处于底部（公募持仓全面退出为信号）` → `view` + `stance=bullish`（当下判断，无未来时间窗/无可验证目标位），**不得归 `predict`**（同 framework-rules #30「易错判据（观点 vs 预测记录）」）。

**标的解析须还原代称**：寒王→寒武纪、赵姨→兆易创新、兆易→兆易创新；原文代称写入 `targetAlias` 留痕，能挂上主题时带 `subjectId`。

**观点时间（双时间）判定**：默认 `view_date = post_date`（`as_posted`）；原文写明日期 → `explicit`；含"三年前/今年五月份我的预判"等相对表述 → 以 `post_date` 折算，置 `derived` 并把原句抄进 `view_date_basis`。粒度按表述给（只说"三年前"不得写成精确到日）。硬约束 `view_date ≤ post_date`；跨度 ≥2 年或表述模糊（"很早以前"）→ 同时标待复核。转述他人判断不得算博主本人观点时间。

**能成 wiki 的一刀切判据**：内容是否提供**可脱离发帖语境复用的判断逻辑／框架／数据关系**？是 → wiki；否 → 只留言论（不硬造条目）。

**铁律（2026-09-08 画像单轨化 + 言论分表）**：言论/买卖/画像一律只落 MySQL（`blogger_statement`/`blogger_trade`/`update_blogger`；言论按类型物理分表 stmt_research/stmt_predict/stmt_view/stmt_insight/stmt_chat/stmt_trade_src，工具自动路由，见 framework-rules #39）。画像 md 已退役——不再镜像回写，vault 内残留画像文件仅为待删除的比对副本。**手改画像 md 表格、为画像文件写内容均为违规**。
**两条补充（2026-09-03）**：① 涉个股/行业/市场的言论调用 `blogger_statement` 时**必须传 `subjectId`**，否则该言论不会出现在「言论追踪」控制台——行业维度主题**按需创建**（词汇权威源 = tag-taxonomy 第五节申万分级；选最精确标准名，主题不存在则按标准名即时创建，**禁止自创非标准行业名**，见 framework-rules #38 行业主题按需创建）；② **写入前先查重**——同一段文字已存在于该博主的 `blogger_statements` 行时，合并/更新那一行，**禁止新增第二份**（"言论登记在谁名下就是谁的言论"既是归因依据，也是去重依据）。

### 分类不明处置（禁止静默丢弃 · 2026-09-06 用户规则）

分流时遇到 **①不属于任何既有 content_type**、或 **②定位模糊**（多类型皆可 / 明显有价值但去向不明）的言论：

1. **禁止丢弃、禁止强行套类**——强行套类会污染准确率追踪与子表结构，静默丢弃会永久丢失高价值言论，两者都比「列出来问一句」代价高。
2. **必须在执行汇报中单列「⚠ 待确认分类」一节**，逐条给出：原文全文（不得截断改写）、不确定原因（如「既有研究成分又有交易动作」「既非当下判断也无未来指向但明显是方法论雏形」）、候选建议（最接近的 1-2 个既有类型 + 理由，或「建议新增分类」+ 建议类名中英文名，供 dict 录入）。
3. **用户裁决两种结局**：**指定归属** → 按指定 content_type 正常经 `blogger_statement` 落库；**新增分类** → 走 dict 字典流程（`INSERT INTO dict`，type=`stmt_content_type`，remark 存判据、sort_order 定序，framework-rules #30 码值权威源——**只改字典，服务端校验与前端标签/tab 自动生效**，禁止在代码里加并行定义），再落库。
4. **裁决前**：该言论不写入任何表、也**不丢弃**，保持在待确认清单中（宁挂起、不流失）。
5. 「能成 wiki 的一刀切判据」仍然适用：分类不明 ≠ 没价值；确定有价值只是去向不明的，必须走本流程而不是丢弃。
