# CHANGELOG

## 2026-09-01

### Added
- 新建 CHANGELOG.md（CONTRIBUTING.md 第五节要求，仓库此前缺失）
- investment-refine v2.10.0：决策链路落库自由文本新增「路径书写硬约束」——`.md` 完整路径只允许指向本次检索确认存在的 vault 文件或本条产物/源；假想、被否决、未创建条目一律写《名称》（不带 `.md`）。看板渲染语义：`.md` = 可点击跳 Obsidian，《名称》 = 纯文本。同步修正 schema 示例中的违规写法（alt 里的假想条目路径）并新增自检项。规则源：investment-refine/references/refine-schema.md 四（2026-09-01 用户确认：前置约束优于回检兜底，起因：黄金配置思路假想条目被渲染成死链接）

### Changed
- investment-framework v2.16.0：console-guide.md §3 数据契约补充「路径书写语义」条目，明确前端存在性校验（vault 索引 ∪ 本条产物）仅兜底质检、权威判定在写入侧
