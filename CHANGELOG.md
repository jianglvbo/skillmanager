# CHANGELOG

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
