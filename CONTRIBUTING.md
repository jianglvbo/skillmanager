# 仓库协作规则

> 本文件面向所有接入此仓库的 Agent。在修改仓库前，请先读完。

---

## 一、仓库定位

`~/Ai/` 是一个**本地 Agent Skill 仓库**，多方 Agent 共用。它存放：

- **用户自行创建**的 Skill
- 用户要求从**网络下载**的 Skill
- Skill 配套的脚本、模板与参考文档

不存放来自 Agent 内置商店安装的 Skill。

---

## 二、入口文档

| 文件 | 读给谁看 | 内容 |
|------|---------|------|
| `README.md` | 新接入的 Agent | 仓库介绍、安装指南、Skill 列表 |
| `CONTRIBUTING.md`（本文件） | 所有 Agent | 修改规则、版本管理、协作约定 |
| `CHANGELOG.md` | 所有 Agent | 版本变更记录 |

---

## 三、修改原则

### 3.1 不随意改动

本仓库应像代码库一样管理。每一次修改都应：

1. 确认修改是否必要
2. 读取目标文件当前内容，避免覆盖他人工作
3. 只改你确认需要改的部分

### 3.2 提交与推送

- **仅在用户明确要求时**才进行 `git commit` 或 `git push`
- 用户未说"提交"或"推送"，只改文件，不做 git 操作

---

## 四、冲突处理

合并时遇到冲突：

- **能自动处理的**：由 Agent 自行合并
- **无法自动处理的**：停止操作，将冲突内容和上下文提交给用户确认

---

## 五、版本记录

所有变更必须记入仓库根目录的 `CHANGELOG.md`，格式：

```markdown
## YYYY-MM-DD

### Changed
- 修改了什么，为什么改

### Added
- 新增了什么

### Removed
- 移除了什么
```

---

## 六、内容规范

### Skill 必须是 Agent 无关的

Skill 文件（SKILL.md、README.md、脚本、模板等）**不得包含**：

| 禁止内容 | 示例 |
|---------|------|
| 特定 Agent 名称 | `WorkBuddy`、`QoderWork`、`Claude Code` |
| 特定 Agent 路径 | `~/.workbuddy/skills/`、`~/.qoderworkcn/` |
| 特定 Agent 链接或名字 | 任何绑定到单一 Agent 的 URL 或标识 |
| 个人标签 | 仅对某个 Agent 有意义的标签 |

### 允许保留的内容

- 以投资/商业分析为目的提及的 Agent 产品名称（如"WorkBuddy 投放地铁广告"属于投资分析内容，不是 Agent 配置）
- 以方法论文档为目的提及的外部研究者名称（如 Serenity、@aleabroreddit）

---

## 七、目录结构参考

以 `serenity-skill/` 作为标准 Skill 结构的模板：

```text
skill-name/
├── SKILL.md          ← 必需：Agent 加载入口
├── README.md         ← 建议：人类可读说明
├── CHANGELOG.md      ← 建议：版本变更
├── references/       ← 可选：详细规则、标准、手册
├── scripts/          ← 可选：确定性脚本
├── assets/           ← 可选：模板、schema
├── examples/         ← 可选：输入输出示例
└── evals/            ← 可选：行为测试用例
```

---

## 八、安装方式

接入此仓库的 Agent 通过符号链接安装 Skill：

```bash
ln -s ~/Ai/skill/<分类>/<skill-name> ~/.agent/skills/<skill-name>
```

不要在 Skill 文件中写死任何 Agent 的安装路径。

---

## 九、其他 Agent 的存在

记住：有**其他 Agent 和你共用此仓库**。

- 不要假设你对仓库的视角是唯一的
- 数据文件只追加不覆盖
- 操作后清理临时文件
