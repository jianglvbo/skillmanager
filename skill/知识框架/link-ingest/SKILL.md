---
name: link-ingest
description: |
  链接收集与抓取。将 URL 转为可存档的 Markdown，存入指定目录。
  不负责后续加工——只抓原文、写 frontmatter。
  所有路径和规则由调用方传入，全部必填。skill 不持有任何业务规则——纯执行引擎。
  触发词：「链接收集」「抓取」「存链接」「ingest link」
  区别：与 coarse-processor 的区别在于不做 metadata 补全和归档。
version: 3.0.0
---

# 链接收集

## Default Stance

### 核心原则
- **纯执行引擎**：所有参数由调用方传入，不硬编码路径或规则。
- **工具匹配**：按 source_type 选择最佳抓取工具，不自行决定工具。
- **只抓正文**：不抓评论、侧边栏、广告等无关内容。

### 禁止行为
- 绝不修改原文内容
- 绝不抓取评论或无关元素
- 绝不硬编码路径或模板
- 绝不在抓取失败时生成占位内容

---

## Workflow

**第一步**：读 {rules_path}，获取链接收集规则（source_type→工具映射、frontmatter 字段定义）
**第二步**：按 rules_path 中的 source_type→工具映射选择抓取工具
**第三步**：抓取原文，不抓评论
**第四步**：按 rules_path 中的 frontmatter 字段定义写入
**第五步**：保存到 {output_dir}/{标题}.md

## 输入（全部必填）

{url, source_type, output_dir, rules_path}

## Output Format

链接收集产出为一个新文件：
- 位置：`{output_dir}/{标题}.md`
- 内容：frontmatter（按 rules_path 字段定义）+ 正文 Markdown
- 返回抓取状态（成功/失败/空内容）

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | {rules_path} | 链接收集规则（工具映射、frontmatter 字段） |

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定 |
| 2 | Obsidian 规范 |
| 3 | knowledge-pipeline（路径常量、规则文件） |
| 4 | 工程实践验证 |

## 自检

- [ ] 是否已读 {rules_path} 获取收集规则？
- [ ] 文件是否成功写入 {output_dir}？
- [ ] frontmatter 必填字段非空？
- [ ] 原文内容不为空？
