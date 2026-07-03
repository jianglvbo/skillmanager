---
name: investment-refine
description: >
  投资框架提炼执行器。读取原始资源 + 提炼预览表 → 按预览表逐行处理框架条目 → 创建文件并填写内容。
  一篇帖子可拆为多条框架条目（一对多）。
  触发词：「提炼」「归档框架条目」。
  由 investment-framework 编排调用，不独立触发。
license: MIT
agent_created: true
metadata:
  version: "1.0.0"
  short-description: 投资框架提炼执行器
compatibility: 通用
---

# 提炼执行器

---

## Default Stance

### 核心原则

- **按预览表逐行执行**：每一行对应一个框架条目，不跳行、不合并
- **一对多拆分**：一篇帖子可产出多个框架文件，按分类分别创建
- **模板驱动**：每个条目必须使用对应分类的模板填写 frontmatter + 正文
- **参数全部由编排者传入**：缺参即报错

- **Tags 精简分级**：只加分类检索有用的标签（个股名/行业/板块），用 "/" 多级分级（消费/酒业/白酒），禁止加产品名/品牌名等无分类价值的标签

### 禁止行为

- 绝不跳过预览表中的任何行
- 绝不在"我的"层创建或修改文件
- 绝不遗漏博主行的处理（如涉及已登记博主，必须同时更新博主档案）
- 绝不将非投资内容放入"其他"层

---

## Workflow

**第一步**：读取参数 `{ source_path, preview_table, blogger_dir, other_dir, macro_dir, blogger_console_path, templates }`
**第二步**：读取 source_path 文件内容 + 底部提炼预览表
**第三步步**：逐行处理预览表——对每一行：
  - 确定分类（分析框架/交易体系/投资心态/投资心得/个股/行业/博主）
  - 确定归属层（我的/博主/其他）
  - 从 templates 选择对应模板
  - 创建文件，填写 frontmatter + 正文内容
  - 如涉及个股，在 frontmatter 添加行业标签
**第四步**：如涉及已登记博主，读取 `博主/{博主名}/{博主名}.md`，在信息汇总章节追加本次条目
**第五步**：如涉及宏观事件，创建/更新宏观文件并在传导路径中关联行业/个股 wikilink
**第六步**：自检——所有预览表行是否都已处理？

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| created_files | list[string] | 本次创建的框架条目路径列表 |
| blogger_updated | boolean | 是否更新了博主档案 |
| macro_created | boolean | 是否创建/更新了宏观文件 |

---

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 提炼时 | references/template-mapping.md | 分类→模板映射表 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数 |
| 2 | 用户约定（三层归属、六大分类） |
| 3 | 模板文件（frontmatter 字段规范） |
| 4 | Obsidian wikilink 规范 |

---

## 自检

- [ ] 预览表每一行是否都已处理？
- [ ] 每个条目是否使用了正确的模板？
- [ ] frontmatter 字段是否完整？
- [ ] 如涉及博主，博主档案是否已更新？
- [ ] 如涉及宏观，传导路径 wikilink 是否已添加？
- [ ] 是否在"我的"层创建了文件？（应该没有）
