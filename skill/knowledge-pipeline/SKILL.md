---
name: knowledge-pipeline
description: |
  知识框架全局编排者。定义七模块清单、调用链、路径表、全局规则、所有输出模板。
  加工 skill 不包含任何路径和模板——全部由此传入。路径变更只改这里。
  触发词：「框架」「全貌」「pipeline」「全局」「怎么用」「流程」
version: 4.0.0
---

# 知识框架 · 全局编排者

唯一持有路径、模板、调用链的地方。加工 skill 全部无默认值，缺参数就报错。

---

## 路径表

| 常量 | 值 |
|:---|:---|
| ROUGH_DRAFTS | 粗制品/ |
| WIKI_RAW | 原始资源仓库 |
| BLOGGER_RAW | 原始资源仓库 |
| WIKI_TARGET | 维基仓库/投资分析 |
| BLOGGER_PROFILE | 维基仓库/博主画像 |
| BLOGGER_CONSOLE | 仪表盘/博主控制台.md |
| QA_OUTPUT | 问答看板/历史问答 |
| REVIEW_OUTPUT | 问答看板/审查报告 |

---

## 模板路径表

| 模板 | 路径 |
|:---|:---|
| raw-frontmatter | knowledge-pipeline/assets/raw-frontmatter.md |
| wiki-entry | knowledge-pipeline/assets/wiki-entry.md |
| wiki-method | knowledge-pipeline/assets/wiki-method.md |
| wiki-case-study | knowledge-pipeline/assets/wiki-case-study.md |
| wiki-data-interp | knowledge-pipeline/assets/wiki-data-interp.md |
| wiki-opinion | knowledge-pipeline/assets/wiki-opinion.md |
| wiki-market-overview | knowledge-pipeline/assets/wiki-market-overview.md |
| blogger-frontmatter | knowledge-pipeline/assets/blogger-frontmatter.md |
| blogger-profile | knowledge-pipeline/assets/blogger-profile.md |
| qa-output | knowledge-pipeline/assets/qa-output.md |
| review-report | knowledge-pipeline/assets/review-report.md |
| question-templates | knowledge-pipeline/assets/question-templates.md |

---

## 调用链

### 投资知识全流程

1. **link-ingest**({ url, source_type, output_dir: ROUGH_DRAFTS })
2. **coarse-processor**({ source_path, target_dir: WIKI_RAW, type, template_path: raw-frontmatter })
3. **wiki-refine**({ source_path, target_dir: WIKI_TARGET, category, content_type, time_sensitivity, template_path })
   → template_path 按 content_type 选择：wiki-method / wiki-case-study / wiki-data-interp / wiki-opinion / wiki-market-overview
4. **qa-ask**({ question, search_dirs: [WIKI_TARGET, BLOGGER_PROFILE], output_dir: QA_OUTPUT, template_path: qa-output })
   → 提问模板参考：question-templates

### 博主画像全流程

1. **link-ingest**({ url, source_type, output_dir: ROUGH_DRAFTS })
2. **coarse-processor**({ source_path, target_dir: BLOGGER_RAW, type, template_path: raw-frontmatter })
3. 读 BLOGGER_CONSOLE → 提取 config_snapshot = {name, aliases, is_xueqiu, is_following, is_starred}
4. **blogger-refine**({ source_path, config_snapshot, profile_path: BLOGGER_PROFILE/{name}.md, template_path: blogger-profile })
   → 返回 {profile_content, console_delta}
5. 写 profile_content 到 BLOGGER_PROFILE/{name}.md
6. 用 console_delta 更新 BLOGGER_CONSOLE 对应行

### 博主画像纯提炼（已有原始资源）

1. 读 BLOGGER_CONSOLE → config_snapshot
2. **若画像不存在**：扫描 WIKI_RAW/{帖子,长文}/，收集该作者全部文章作为 source_paths
3. **blogger-refine**({ source_path, config_snapshot, profile_path, template_path: blogger-profile })
   → 返回 {profile_content, console_delta}
4. 写 profile_content
5. 更新控制台

### 审查

**wiki-review**({ target_dir: WIKI_TARGET, dimensions, output_dir: REVIEW_OUTPUT, template_path: review-report })

---

## 全局规则

- 日期格式：YYYY年M月D日
- 文件命名：不带日期前缀
- wikilink：完整路径，不加 emoji 前缀
- 控制台默认值：雪球博主=是，雪球关注=是，特别关注=否（空单元格=默认值）
- 提炼前必读控制台，提炼后必更新控制台
- 加工 skill 全部参数必填，不传即报错
- 原始资源仓库位于 vault 根目录「原始资源仓库/」，博主画像与维基条目均位于「维基仓库/」下，共享同一原始资源
- 新增博主画像时，须扫描全部原始资源（帖子/ + 长文/），收集该作者所有文章一并提炼
