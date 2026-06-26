---
name: qa-ask
description: |
  知识检索与问答模块。查询维基仓库和/或博主画像，生成结构化问答产物。
  支持 source 参数控制检索范围（wiki/blogger/both），可独立使用，也可作为财报分析等链路的背景检索前置步骤。
  所有搜索目录、输出路径和查询规则由 pipeline 传入。skill 不持有任何业务规则——纯执行引擎。
  触发词：「问答」「提问」「qa」「根据框架」「怎么看」「财报分析」「结合框架分析」
  区别：与 wiki-review 的区别在于产出是一次性问答，非批量审查报告。
version: 3.0.0
---

# 知识检索与问答

## Default Stance

### 核心原则
- **纯执行引擎**：所有参数由 pipeline 传入，不硬编码路径或规则。
- **检索优先**：先搜索已有知识，再组织回答。不编造知识库中不存在的信息。
- **引用可追溯**：回答中引用的条目必须标注来源路径。

### 禁止行为
- 绝不编造知识库中不存在的观点
- 绝不跳过搜索直接生成回答
- 绝不遗漏被引用条目的 queried 计数更新
- 绝不硬编码搜索目录或输出路径

---

## Workflow

**第一步**：读 {rules_path}，获取查询规则和 source→目录映射
**第二步**：读 {template_path}，获取输出格式
**第三步**：解析 question，确定查询策略
**第四步**：按 rules_path 中的 source→目录映射确定搜索目录，在目标目录中搜索相关条目
**第五步**：按 {template_path} 格式输出
**第六步**：保存到 {output_dir}/YYYY年M月D日-主题.md
**第七步**：更新被引用条目的 queried 计数和 last_queried

## 输入（全部必填）

{question, source, output_dir, template_path, rules_path}

## Output Format

问答产出为一个结构化文件：
- 位置：`{output_dir}/YYYY年M月D日-主题.md`
- 内容：问题 + 检索到的相关条目摘要 + 综合回答 + 引用来源列表
- 被引用条目的 frontmatter 已更新 queried/last_queried

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | {template_path} | 问答输出模板 |
| 始终 | {rules_path} | 查询规则（source→目录映射） |

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定 |
| 2 | Obsidian 规范 |
| 3 | knowledge-pipeline（路径常量、规则文件） |
| 4 | 工程实践验证 |

## 自检

- [ ] 是否已读 {rules_path} 获取查询规则？
- [ ] source 值是否为 wiki / blogger / both 之一？
- [ ] 文件保存到正确路径？
- [ ] 引用条目路径存在？
- [ ] queried 计数已更新？
