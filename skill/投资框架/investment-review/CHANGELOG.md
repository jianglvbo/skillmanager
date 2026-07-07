# Changelog

## 2.2.0 (2026-07-07)
- 新增 `scripts/vault_review.py` 结构审查自动扫描器：覆盖归类 / frontmatter 完整性（含 updateDate）/ 引号 / wikilink（正文 + `source` 字段）/ 脚注格式 / 标签 六维 + 扩展检查（禁用 `## 来源` 段、source 为 URL、空壳 junk），输出 `vault_review_result.json`，严格只报告不修改
- SKILL.md 结构审查 Workflow 新增「辅助 · 自动预扫」步骤与 Relative Files 加载时机

## 2.1.0 (2026-07-07)
- 结构审查新增「脚注格式」维度：检查脚注定义 wikilink 是否以单 `]]` 闭合（禁止 `]]]`/多余 `]]`），格式是否为 `[[target]] — 关系：说明`
- 结构审查 wikilink 有效性扩展至 frontmatter `source` 字段（此前仅扫正文）
- 结构审查 frontmatter 完整性显式要求 `updateDate` 为必填字段
- 内容审查新增「已存在脚注关系依据复核」：逐条核对文件中已有脚注的关系声明是否有目标文件原文支撑，无依据一律记为编撰关系（建议删除或降级为 enhance）
- Output Format 新增字段：结构审查 `footnote_format_issues`、内容审查 `fabricated_footnotes`，并补充对应报告模板小节
- 自检清单扩展为六个维度 + 脚注格式 / 关系依据检查项
