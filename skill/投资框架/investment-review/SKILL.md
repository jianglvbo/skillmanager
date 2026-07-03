---
name: investment-review
description: >
  投资框架审查执行器。执行内容审查（框架一致性、知行合一、我的vs博主冲突、经验验证）
  和结构审查（归类正确性、frontmatter完整性、wikilink有效性、标签匹配）。
  触发词：「审查」「review」「健康度」「框架检查」。
  由 investment-framework 编排调用，不独立触发。
license: MIT
agent_created: true
metadata:
  version: "1.0.0"
  short-description: 投资框架审查执行器
compatibility: 通用
---

# 审查执行器

---

## Default Stance

### 核心原则

- **两层审查独立执行**：内容审查和结构审查分步进行，各自产出独立报告
- **只报告不修改**：审查只输出问题清单，不直接修改文件，由用户决定是否修正
- **参数全部由编排者传入**：审查范围、目标目录由编排者指定

### 禁止行为

- 绝不直接修改任何框架文件
- 绝不跳过"我的"层的审查（"我的"虽由用户管理，但仍需检查一致性）
- 绝不将结构问题与内容问题混在同一份报告中

---

## Workflow

### 内容审查

**第一步**：读取参数 `{ scope_dirs, blogger_console_path }`
**第二步**：扫描 scope_dirs 下所有 .md 文件
**第三步**：内部一致性检查——交易体系的规则 vs 分析框架的方法论是否矛盾
**第四步**：知行合一检查——投资心态中记录的纪律 vs 分析档案中的实际行为
**第五步**：我的 vs 博主冲突检查——"我的"层的方法论 vs "博主"层的方法论是否有冲突
**第六步**：经验验证检查——投资心得中的教训是否在后续分析档案中被验证
**第七步**：输出内容审查报告

### 结构审查

**第一步**：读取参数 `{ scope_dirs }`
**第二步**：归类正确性——文件是否在正确的归属层和分类下
**第三步**：frontmatter 完整性——必填字段是否齐全（title/createDate/updateDate/tags）
**第四步**：wikilink 有效性——所有 `[[]]` 链接目标是否存在、双向互链是否完整
**第五步**：标签匹配——行业标签是否与实际内容匹配、个股的行业标签是否一致
**第六步**：输出结构审查报告

---

## Output Format

### 内容审查报告

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| consistency_issues | list | 内部一致性问题 |
| action_alignment_issues | list | 知行合一问题 |
| framework_conflicts | list | 我的 vs 博主冲突 |
| verification_gaps | list | 未验证的经验教训 |

### 结构审查报告

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| misplaced_files | list | 归类错误的文件 |
| incomplete_frontmatter | list | frontmatter 缺失的文件 |
| broken_links | list | 失效的 wikilink |
| tag_mismatches | list | 标签不匹配的条目 |

---

## Relative Files

无。本 skill 不加载额外文件。

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数 |
| 2 | 用户约定（审查维度定义） |
| 3 | Obsidian frontmatter 规范 |

---

## 自检

- [ ] 内容审查四个维度是否都已检查？
- [ ] 结构审查四个维度是否都已检查？
- [ ] 是否只输出了报告而未修改任何文件？
- [ ] 审查范围是否覆盖了编排者指定的所有目录？
