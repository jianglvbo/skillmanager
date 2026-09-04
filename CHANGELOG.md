# CHANGELOG

## 2026-09-04

### Changed（博主言论五分法 → 六分法，新增 `predict` 预测记录）
- 动因（用户指出方案漏项）：帖子里的预测此前只能落 `view`，看板「观点」分类混入预测表述；且同一判断经预测控制台另录一份，两处显示、彼此无关联
- investment-framework：`framework-rules` #30 言论追踪子表 4 → **5**（研究 / **预测记录** / 观点 / 心得总结 / 闲聊），补 predict 三要素判定（**① 明确方向 ② 未来指向（时间窗或事件条件）③ 可判对错**）、历史复盘不得算预测；#35 同步「5 子表」，并把画像里同名的表写作「预测记录（准确率追踪）」消歧
- investment-refine：第 1.5 步分流矩阵新增 `predict` 行（必涉标的，`stance` 必填、`signal` 写目标位/时间窗），优先级 P2 纳入 predict
- xq-post-fetch：`content_type`（五分法）→（六分法）
- 看板（`~/Project/investment-console`）：`CONTENT_TYPES`/`CONTENT_CN`/`STMT_ORDER` 加 predict；MCP `blogger_statement` enum + 描述补 predict 定义；前端博主详情与言论追踪详情新增「全部」tab（时间倒序混排），结构化预测并入「预测记录」tab、取消底部常显；修 `consoleGetSubject` 直切 `toISOString` 使预测日期少一天的时区 bug；`blogger_statements.content_type` 列注释改六分；存量 id 783 改判 predict（看多 + 目标位进信号列）

## 2026-09-03

### Changed（博主言论体系重构 Phase A · 依据用户规则《博主言论设计》+ 方案 v2）
- investment-framework：`framework-rules` #30 由四类 kind（具象化/观点/信号/互动）改为**内容五分**（研究/观点/心得总结/闲聊，买卖走 #31），统一列扩为「观点时间｜发帖时间｜内容｜标的/行业｜方向｜…」并新增**双时间硬约束**（观点时间 ≤ 发帖时间、推算跨度≥2年标待复核、粒度不得假精确）与「落库唯一路径 = MCP `blogger_statement`，禁止手改画像表格」；#31 补方向必填、代称还原、**默认不自动生成预测**；`assets/博主.md` 两张表换新列并预埋 `<!-- statements/trades:begin/end -->` 锚点
- investment-coarse-processor：「正文原封不动保留（含图片引用）」硬约束**加作用域**——雪球博主言论采集链路必须纯文本（去图片/图片链接/表情含 `[表情名]` 占位）+ 剥离页脚噪声；非言论链路（转录、长文研究、其他来源）该约束继续全额生效
- xq-post-fetch：第七步新增采集期契约——纯文本化清单、`author` 必须在页脚剥离后解析且不得含 `发布于|来自|关注`（历史脏值会让博主头像与归属失效）、每条记 `发帖时间` + `形态`；**明确不在采集期猜内容分类或写观点时间**（归提炼）
- investment-refine：新增第 1.5 步**博主言论分流决策矩阵**——P1/P2/P3 优先级、`content_type` × 是否涉标的 → 去向表（trade→`blogger_trade`；涉标的→`blogger_statement`+画像+看板；不涉标的→能成 wiki 否则舍弃；闲聊→门槛内才留）、代称还原、双时间判定、"能成 wiki" 一刀切判据、"落画像必落看板"铁律
- 看板侧配套（同日常提交于 `~/Project/investment-console`）：`blogger_statements` 加 12 列（五分/双时间/方向/subject_id/blogger_id/src_rel/幂等键）、新建 `blogger_trades`、`prediction_records.origin_*`；REST+MCP `blogger_trade`；画像同步改锚点化 + 写后行数断言（修末段重复插段与静默丢写）；前端五分分节/双时间/方向徽标/买卖节/仅待复核/单轨言论追踪。smoke 26 项断言通过，历史 943 条零丢失
- framework-rules #38 补「旧主题维过渡语义」：`prediction_tracks` 定为迁移中的遗留表，新增言论一律走 `blogger_statement`；B3 只标记不删行（`migrated_to_statement_id`），未归因行保留旧表标待复核并以「待清理 N」角标显示，**残余为零才自动下架**（禁止为图干净删/藏仍承载待复核数据的主题）
- Phase B 进度：B0 collation 全库统一 ✅、B1 943 条五分/双时间回填 ✅、B3 旧主题维迁回 ✅（843 中 192 可归因迁回、651 无 wikilink 待人工；交易体系 已停用，投资认知 470/心态 5/理念 3/市赚率 3 保留可见）
- 待办 Phase B 余项：B2 抽取 66 条 trade→`blogger_trades`（等用户定，60 条无操作动词不猜写）、B4 dict 枚举真源化、651 条 legacy 人工归因

## 2026-09-02

### Changed
- prediction-console v2.1.0：第四步 `console_add_prediction` 参数表补 `subjectMarket`（sh/sz/hk/kr/us，个股必填、A+H 默认 A 股）与 `subjectHkConnect`（仅港股适用），并加对应自检项。看板 `prediction_subjects.market/hk_connect` 列 + 前端市场徽/港股通徽依赖这两字段，此前 skill 未教送导致新预测缺市场标识（补 2026-09-01 挂账）
- investment-refine v2.11.0：落库契约移除 `why` 字段（`refine_targets` 表无该列、前端不渲染，收集即丢；决策语义由 thinking v2 的「决策」步承载）；第四步大 JSON 示例与 thinking 细则下沉到 `references/refine-schema.md`，主文件 214→173 行（≤200 规范）
- investment-framework v2.16.2：`console-guide.md` 修正过期内容——§1 路径 `~/WorkBuddy/...`→真实双部署（线上 `/home/jianglb/investment-console` 唯一权威 / 本地 `~/Project/investment-console` disableDbSync 只读）+ 存储模型 `data/*.json`→MySQL（方案 A）+ 补 MCP 端点；§2 数据契约表补言论追踪 `console_*` 工具行；删除「用户桌面交接文档」私有路径；同步移除 `why`


### Changed（端到端流程审计修复 · 续）
- investment-framework v2.16.3：**P0** 看板联动/操作门/自检补「派生索引同步」——流水线写本地 iCloud vault，线上看板派生索引(files/tags/bloggers)与审查链接存在性读线上 vault 副本，新建/改名文件须经 `server-ops vault_sync.sh` 推送（记录类走共享 MySQL 不受影响）；**P1** 修正自相矛盾：端点「本地 127.0.0.1/launchd」→「线上唯一权威/systemd、本地只读」，删残留「thinking 5 步/why」「决策链路图 10 节点」旧规范（改 v2 思考时间线）
- investment-refine v2.11.1：**P2** 前置条件加「目录硬判定(#22)」——可否提炼以文件在 `工作区/原始资源/` 为准、不以 status 值为准，闭合粗制品误判
- wechat-article v1.1.1：**P2** 采集 frontmatter 对齐规范：`source` 由渠道名占位改真实链接 markdown、`date/recorded` 改 `yyyy-MM-dd` 裸写、补 `tags: []`
- **P3 结论**：粗加工不落看板成立——看板 `listCoarse()` 直接扫 vault 逐文件解析要素（title/author/source/url/摘要/雪球博主/日期），状态/评分读共享 MySQL `coarse_records`，均无需 skill POST；顺带修复 server.js `listCoarse` 变量遮蔽 bug（内层 meta 覆盖外层，致 coarse_records 状态/评分永不合并进列表）
## 2026-09-01

### Added
- 新建 CHANGELOG.md（CONTRIBUTING.md 第五节要求，仓库此前缺失）
- investment-refine v2.10.0：决策链路落库自由文本新增「路径书写硬约束」——`.md` 完整路径只允许指向本次检索确认存在的 vault 文件或本条产物/源；假想、被否决、未创建条目一律写《名称》（不带 `.md`）。看板渲染语义：`.md` = 可点击跳 Obsidian，《名称》 = 纯文本。同步修正 schema 示例中的违规写法（alt 里的假想条目路径）并新增自检项。规则源：investment-refine/references/refine-schema.md 四（2026-09-01 用户确认：前置约束优于回检兜底，起因：黄金配置思路假想条目被渲染成死链接）

### Changed
- investment-framework v2.16.0：console-guide.md §3 数据契约补充「路径书写语义」条目，明确前端存在性校验（vault 索引 ∪ 本条产物）仅兜底质检、权威判定在写入侧
- investment-framework v2.16.1：console-guide.md §4 链路图更新——移除 `[校验]` 收尾节点，「落为产物」即终点（2026-09-01 用户决定；看板渲染层已同步删除，verify 数据仍落库仅不渲染）
