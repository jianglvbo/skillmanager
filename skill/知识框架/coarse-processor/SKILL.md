---
name: coarse-processor
description: |
  粗加工模块。补全 frontmatter 并归档原文到原始资源仓库。
  不负责提炼——只做 metadata 补全和文件迁移。
  所有路径、模板和处理规则由 pipeline 传入。skill 不持有任何业务规则——纯执行引擎。
  触发词：「粗加工」「归档」「raw process」「coarse」
  区别：与 wiki-refine 的区别在于不做知识结构化。
version: 3.0.0
---

# 粗加工

## Default Stance

### 核心原则
- **纯执行引擎**：所有参数由 pipeline 传入，不硬编码路径或规则。
- **保真优先**：保留原文内容，只做 frontmatter 补全和清洗规则处理，不改动正文观点。
- **逐字稿特殊处理**：ASR 逐字稿需按规则断句分段，不能当作普通文本处理。

### 禁止行为
- 绝不修改原文的观点和内容（清洗规则除外）
- 绝不跳过必填 frontmatter 字段
- 绝不在 skill 内硬编码路径或模板
- 绝不自行决定待处理文件列表（由 pipeline 从 PENDING_QUEUE 传入）

---

## Workflow

**第一步**：读 {rules_path}，获取粗加工规则定义（逐字稿处理、清洗规则）
**第二步**：读 source_path，校验文件存在
**第三步**：读 {template_path}，按模板补全 frontmatter
**第四步**：按 {rules_path} 中的规则处理原文（含逐字稿断句、清洗）
**第五步**：保留图片 wikilink 引用
**第六步**：移动文件到 {target_dir}/{type}/
**第七步**：删除源文件

## 输入（全部必填）

{source_path, target_dir, type, template_path, rules_path}

## Output Format

粗加工产出为一个迁移后的文件：
- 位置：`{target_dir}/{type}/{文件名}.md`
- 内容：补全 frontmatter + 清洗后的正文
- 源文件已删除

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | {template_path} | frontmatter 模板（由 pipeline 传入） |
| 始终 | {rules_path} | 粗加工规则（逐字稿处理、清洗规则） |

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定 |
| 2 | Obsidian 规范 |
| 3 | knowledge-pipeline（路径常量、模板、规则文件） |
| 4 | 工程实践验证 |

## Pitfalls

- **逐字稿标题必须保留**：处理抖音逐字稿时，`## 逐字稿` 是正文的 section 标题，不是元数据。去时间轴的代码不能跳过以 `## ` 开头的行——只跳过时间戳行（`**MM:SS**`），保留 `## 逐字稿` 作为输出段落的标题。
- **抖音 ASR 逐字稿无标点**：抖音转录的逐字稿是纯 ASR 输出，句间没有句号/感叹号/问号。分段时不能依赖 `[。！？]` 做断点，应在口语话语标记词（那、但是、其实、所以、为什么、还有、接下来、不过、比如、如果）处寻找自然断点，每 200-400 字为一段。
- **文件名特殊字符**：粗制品文件名可能含中文引号（""）、全角括号（（））等。用 bash heredoc 传 Python 脚本会报 SyntaxError。应先将脚本写入文件（Write 工具），再用 `python3 <script.py>` 执行。

## 自检

- [ ] 是否已读 {rules_path} 获取处理规则？
- [ ] 目标文件是否存在？
- [ ] frontmatter 所有必填字段非空？
- [ ] 源文件是否已删除？
- [ ] 原文内容与源文件一致？
