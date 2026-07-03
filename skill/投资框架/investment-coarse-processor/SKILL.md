---
name: investment-coarse-processor
description: >
  投资框架粗加工执行器。读取粗制品 → 整理格式、去广告 → 补全 metadata → 生成提炼预览表 → 移入原始资源。
  触发词：「粗加工」「归档」「整理帖子」。
  由 investment-framework 编排调用，不独立触发。
license: MIT
agent_created: true
metadata:
  version: "1.0.0"
  short-description: 投资框架粗加工执行器
compatibility: 通用
---

# 粗加工执行器

---

## Default Stance

### 核心原则

- **只做粗加工，不做提炼**：输出是整理后的原始资源 + 提炼预览表，不创建框架条目
- **预览表是核心产出**：必须覆盖帖子中所有有价值内容，分类准确
- **博主判断依赖控制台**：只对照 博主控制台.md 判断是否为已登记博主
- **参数全部由编排者传入**：缺参即报错，不硬编码路径

### 禁止行为

- 绝不跳过提炼预览表直接创建框架条目
- 绝不将无内容的行保留在预览表中
- 绝不将不在控制台的博主写入预览表的博主行
- 绝不修改"我的"层的任何文件

---

## Workflow

**第一步**：读取参数 `{ source_path, target_dir, blogger_console_path }`
**第二步**：读取 source_path 文件内容
**第三步**：整理格式——去除多余空行、统一标题层级、修复编码
**第四步**：去广告——移除推广内容、社交媒体分享按钮文本、无关的页脚
**第五步**：补全 frontmatter metadata：

```yaml
---
title: "{帖子标题}"
source: "{来源链接}"
author: "{作者名}"
date: "{YYYY年M月D日}"
type: "帖子/长文/链接"
status: "待提炼"
---
```

**第六步**：对照 blogger_console_path，判断 author 是否为已登记博主
**第七步**：分析帖子内容，按六大分类（分析框架/交易体系/投资心态/投资心得/个股/行业）逐项判断是否有有价值内容
**第八步**：生成提炼预览表（只保留有内容的行）：

```markdown
## 提炼预览

| 分类 | 内容摘要 | 预计归类文件 |
|:---|:---|:---|
```

**第九步**：将文件从 source_path 移动到 target_dir
**第十步**：自检

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| output_path | string | 移动后的文件路径 |
| preview_table | markdown | 提炼预览表内容 |
| has_blogger | boolean | 是否涉及已登记博主 |
| blogger_name | string/null | 涉及的博主名 |

---

## Relative Files

无。本 skill 不加载额外文件，所有路径和规则由编排者传入。

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数（路径、控制台） |
| 2 | 用户约定（预览表格式、六大分类） |
| 3 | Obsidian frontmatter 规范 |

---

## 自检

- [ ] frontmatter 字段是否完整（title/source/author/date/type/status）？
- [ ] 预览表是否覆盖帖子中所有有价值内容？
- [ ] 预览表是否只保留有内容的行？
- [ ] 博主行是否仅在 author 在控制台中时出现？
- [ ] 文件是否已移动到 target_dir？
