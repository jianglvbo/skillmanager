---
name: investment-coarse-processor
description: >
  投资框架粗加工执行器。读取粗制品 → 整理格式、去广告 → 补全 metadata → 移入原始资源。
  不生成提炼预览表，拆分决策由提炼环节负责。
  触发词：「粗加工」「归档」「整理帖子」。
  由 investment-framework 编排调用，不独立触发。
license: MIT
agent_created: true
metadata:
  version: "2.3.0"
  short-description: 投资框架粗加工执行器
compatibility: 通用
---

# 粗加工执行器

---

## Default Stance

### 核心原则

- **只做粗加工，不做提炼**：输出是整理后的原始资源，不创建框架条目，不生成提炼预览表
- **拆分决策留给提炼环节**：粗加工只负责整理格式和补全 metadata，不判断内容应归入哪个分类
- **繁体转简体**：粗制品正文若为繁体中文，整理时必须转为简体中文入库；仅做繁简字形转换，保留原文用词、语气、比喻、案例，不改写内容
- **博主判断依赖控制台**：只对照 博主控制台.md 判断是否为已登记博主
- **参数全部由编排者传入**：缺参即报错，不硬编码路径

### 禁止行为

- **绝不修改、精简、重组、删节正文内容**：正文必须原封不动保留，包括图片/附件引用（`![[...]]`）、全文整理/转录稿段落、看似重复的内容、口语化表达。粗加工只做两件事：① 替换/补全 frontmatter；② 去掉文件末尾明显的工具广告（如"AI整理设置点此调整"、积分余额、反馈链接）
- 绝不生成提炼预览表或任何提炼方案
- 绝不跳过格式整理直接移动文件
- 绝不修改"我的"层的任何文件
- 绝不给原始资源文件预填框架级标签

---

## Workflow

**第一步**：读取参数 `{ source_path, target_dir, blogger_console_path }`
**第二步**：读取 source_path 文件内容
**第三步**：整理格式——去除多余空行、统一标题层级、修复编码；**若正文为繁体中文，转为简体中文**（仅字形转换，不改用词、语气、比喻、案例）
**第四步**：去广告——移除推广内容、社交媒体分享按钮文本、无关的页脚。特别注意 AI 整理工具（笔记同步助手等）产出的固定模式：
- **尾部广告**：`视频时长 X分X秒 · 消耗 N 积分 · 积分余额 N`、`AI整理设置可以[点此调整](...)`、`内容效果不满意？[点此反馈](...)` 等固定尾部，整段删除
**第五步**：补全 frontmatter metadata：

```yaml
---
title: "{帖子标题}"
source: "{描述性来源，如：AI整理 - 小红书 / 雪球长文}"
author: "{作者名}"
date: {YYYY-MM-DD}
type: "帖子/长文/链接/视频整理"
status: "待提炼"
tags: []
---
```

**第六步**：对照 blogger_console_path，判断 author 是否为已登记博主
**第七步**：将文件从 source_path 移动到 target_dir
**第八步**：自检

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| output_path | string | 移动后的文件路径 |
| has_blogger | boolean | 是否涉及已登记博主 |
| blogger_name | string/null | 涉及的博主名 |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 补全 frontmatter 时 | references/frontmatter-rules.md | 7 字段规范、引号嵌套规则、tags block list 格式 | 读取 |

其余路径和规则由编排者传入。

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数（路径、控制台） |
| 2 | 用户约定（frontmatter 字段规范） |
| 3 | Obsidian frontmatter 规范 |

---

## YAML Frontmatter 规范

原始资源 frontmatter **仅 7 个字段**：title、source、author、date、type、status、tags（字段顺序 `title → source → author → date → type → status → tags`），不添加 layer/category 等字段。**`id` 字段豁免**：若粗制品/原始资源 frontmatter 含 `id`（如 `id: docid_xxx_e`，Visit History 等 Obsidian 插件写入的追踪 ID），**保留不动、不删除、不移动、不报错**——它不属于框架字段集（见 framework-rules #27「id 字段豁免」）。引号嵌套规则（含双引号用单引号包裹等）、tags block list 格式等完整规范见 `references/frontmatter-rules.md`（权威源 framework-rules #27/#21）——执行时**必须加载**，不自造格式。

---

## 自检

- [ ] 若源文为繁体中文，正文是否已转为简体中文？
- [ ] frontmatter 仅含 7 个标准字段（title/source/author/date/type/status/tags）？
- [ ] 引号嵌套是否正确处理（双引号值用单引号包裹）？
- [ ] tags 是否为空或格式正确的 block list？
- [ ] 文件是否已移动到 target_dir？
- [ ] 是否未生成提炼预览表？
- [ ] 未添加 layer/category 等非原始资源字段？
- [ ] 是否未将未登记作者「补登」进博主控制台（仅对照判断，绝不自动新增；未登记作者其条目归「其他」层，见 framework-rules #12）？
- [ ] date 是否为 `yyyy-MM-dd` 裸写无引号（见全局规则 #1）？若带引号或中文格式（如 YYYY年M月D日）即违规
- [ ] source 是否为描述性来源（如"AI整理 - 小红书"），而非 URL？
