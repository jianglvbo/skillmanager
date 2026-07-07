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
  version: "2.0.0"
  short-description: 投资框架粗加工执行器
compatibility: 通用
---

# 粗加工执行器

---

## Default Stance

### 核心原则

- **只做粗加工，不做提炼**：输出是整理后的原始资源，不创建框架条目，不生成提炼预览表
- **拆分决策留给提炼环节**：粗加工只负责整理格式和补全 metadata，不判断内容应归入哪个分类
- **博主判断依赖控制台**：只对照 博主控制台.md 判断是否为已登记博主
- **参数全部由编排者传入**：缺参即报错，不硬编码路径

### 禁止行为

- 绝不生成提炼预览表或任何提炼方案
- 绝不跳过格式整理直接移动文件
- 绝不修改"我的"层的任何文件
- 绝不给原始资源文件预填框架级标签

---

## Workflow

**第一步**：读取参数 `{ source_path, target_dir, blogger_console_path }`
**第二步**：读取 source_path 文件内容
**第三步**：整理格式——逐项修复以下问题（不修复就带入下游）：
- 去除连续 ≥3 行的多余空行（保留最多 1 行空行）
- 修复同行标题：`正文。## 标题` → 拆为两行，标题独占一行且前后空行
- 修复标题间距：`##`/`###` 标题前后必须有空行
- 清除独立空 `#` 行（仅含 `#` 无标题文字的行）
- 统一标题层级、修复编码
**第四步**：去广告——移除推广内容、社交媒体分享按钮文本、无关的页脚
**第五步**：补全 frontmatter metadata：

```yaml
---
title: "{帖子标题}"
source: "{来源链接}"
author: "{作者名}"
date: "{YYYY年M月D日}"
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

无。本 skill 不加载额外文件，所有路径和规则由编排者传入。

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数（路径、控制台） |
| 2 | 用户约定（frontmatter 字段规范） |
| 3 | Obsidian frontmatter 规范 |

---

## YAML Frontmatter 规范

### 字段范围

原始资源 frontmatter **仅 7 个字段**：title、source、author、date、type、status、tags。不添加 layer、category 或其他字段——归属层和分类由提炼环节决定。

### 引号规则

frontmatter 值中的引号必须正确处理，否则 Obsidian Properties 面板解析异常：

| 值的内容 | 包裹方式 | 示例 |
|:---|:---|:---|
| 不含引号 | 双引号 | `title: "珀莱雅深度拆解"` |
| 含双引号 | 单引号包裹 | `title: '理解泡泡玛特的四本"书"'` |
| 含单引号 | 双引号包裹 | `title: "错过'时代'是最大的风险"` |
| 含双引号+单引号 | 双引号包裹+转义 | `title: "他说\"好\"了"` |

**禁止**：双引号包裹的值内部再出现未转义的双引号（如 `title: "理解"书""`），这会导致 YAML 解析错误。

### tags 格式

多值 tags 必须使用 YAML block list 格式，每项独占一行并缩进：

```yaml
tags:
  - "投资心得/心得主题/估值经验"
  - "市场/A股"
```

**禁止**：将 block list 项写在 `tags:` 同一行（如 `tags: - item1`），这会导致解析失败。空 tags 使用 `tags: []`。

---

## 自检

- [ ] frontmatter 仅含 7 个标准字段（title/source/author/date/type/status/tags）？
- [ ] 引号嵌套是否正确处理（双引号值用单引号包裹）？
- [ ] tags 是否为空或格式正确的 block list？
- [ ] 文件是否已移动到 target_dir？
- [ ] 是否未生成提炼预览表？
- [ ] 未添加 layer/category 等非原始资源字段？
- [ ] 正文中 `##`/`###` 标题是否独占一行（前后有空行）？——同行标题不会渲染
- [ ] 是否存在独立空 `#` 行（仅含 `#` 无标题文字）？——必须清除
- [ ] 段落间是否有空行分隔？——连续 ≥5 行无空行视为过于紧凑
