---
name: skill-guidelines
description: >
  Agent Skill 设计准则。定义 6 段标准模板、核心原则、工程规律。创建或修改 Skill 时按本规范执行。
  触发词：「skill准则」「skill设计」「skill修改」「skill规范」「skill审查」。
---

# Default stance

## 核心原则
- 用模板写 Skill：6 段结构不可缺，缺了就补
- 主文件 ≤ 200 行：细节下沉 references/，不堆在主文件
- 确定性优先：编号清单 > 自然语言，决策树 > if-else 描述
- 规则有来源：不确定的标记 `[待验证]`

## 禁止行为
- 绝不把 Skill 写成百科文档（塞教科书常识）
- 绝不依赖模型自由发挥不确定步骤
- 绝不遗漏自检步骤

---

# Workflow

## 创建新 Skill

1. 第一步：确定级别（轻量/标准/重量），见 `references/levels.md`
2. 第二步：填 YAML 门控——name、description 含触发词
3. 第三步：写 Default stance——最少 3 条核心原则 + 3 条禁止
4. 第四步：写 Workflow——第一步/第二步…编号，含决策点
5. 第五步：定 Output format——固定字段和类型
6. 第六步：列 Relative files——每个 references/ 写清何时加载
7. 第七步：填 Source hierarchy——优先级从用户约定到最佳实践
8. 第八步：加自检清单——最少 3 条

## 审查已有 Skill

1. 第一步：逐项对照 6 段结构，缺了哪段补哪段
2. 第二步：检查主文件行数 > 200 → 下沉到 references/
3. 第三步：检查 Default stance 有核心原则 + 禁止行为
4. 第四步：检查 Workflow 是否用第一步/第二步…编号
5. 第五步：检查 Relative files 加载时机是否明确
6. 第六步：报告缺失项，询问用户是否修复

---

# Output format

| 段 | 必填 | 格式 |
|:---|:---|:---|
| YAML 门控 | 是 | name + description（含触发词和排除条件） |
| Default stance | 是 | 核心原则 + 禁止行为（各 ≥3 条） |
| Workflow | 是 | 第一步/第二步…编号，含决策点 |
| Output format | 是 | 字段名 + 类型 + 说明 |
| Relative files | 否 | 场景 → 文件映射表 |
| Source hierarchy | 否 | 优先级 1-4 列表 |
| 自检 | 是 | ≥3 条 checklist |

> 完整模板 → 见 `references/template.md`

---

# Relative files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 查阅设计原则 | `references/principles.md` | 八大原则详解 |
| 查阅工程规律 | `references/rules.md` | 九条落地规律 |
| 需要完整模板 | `references/template.md` | 6 段模板带注释 |
| 判断 Skill 级别 | `references/levels.md` | 轻量/标准/重量 |
| 需要示例 | `references/examples.md` | 正反例对比 |

---

# Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | [Nature Skills](https://github.com/nicepkg/nature-skills) 设计模式 |
| 2 | 软件工程原则（单一职责、渐进式披露、确定性优先） |
| 3 | 用户显式约定（模板格式、中文命名、主文件 200 行限制） |
| 4 | 工程实践验证（编号清单提升确定性、决策树代替自然语言） |

---

# 自检

- [ ] YAML 门控：name + description（含触发词）？
- [ ] Default stance：核心原则 + 禁止行为各 ≥3 条？
- [ ] Workflow：第一步/第二步…编号？
- [ ] Output format：字段固定有类型？
- [ ] 主文件 ≤ 200 行？
- [ ] Relative files 加载时机明确？
