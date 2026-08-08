# 6 段标准模板

> 创建新 Skill 的完整模板。复制后替换占位符即可。

---

```yaml
---
name: skill-name
description: 
  简要描述该技能的功能以及何时该使用它。
  包含触发关键词，并明确非触发条件。
---

# Default stance

## 核心原则
- ...
- ...

## 禁止行为
- 绝不...
- 绝不...

---

# Workflow

1. 第一步：...
2. 第二步：...
3. 第三步：...

---

# Output format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| ... | ... | ... |

---

# Relative files

| 场景 | 文件 | 内容 |
|:---|:---|:---|
| 始终 | SKILL.md | 核心流程 |
| 场景X | references/x.md | ... |

---

# Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | ... |
| 2 | ... |

---

# 自检

- [ ] 字段完整？
- [ ] 格式匹配？
```

## 每段说明

| 段 | 作用 | 不能少 |
|:---|:---|:---|
| YAML | Agent 发现和选择 Skill 的唯一依据 | description 含触发词 + 排除条件 |
| Default stance | 防止 Agent 乱来 | 核心原则 + 禁止行为各 ≥3 条 |
| Workflow | 确定执行顺序 | 第一步/第二步…编号，不用 1. 2. |
| Output format | 固定输出结构 | 字段名 + 类型 |
| Relative files | 上下文管理 | 每个文件写清何时加载 |
| Source hierarchy | 规则可追溯 | 从用户约定到最佳实践 |
| 自检 | 验证完整性 | ≥3 条 |
