<div align="center">

# ~/Ai — Agent Skill 本地仓库

### 自建 Agent Skill 的统一存储、分发与版本管理中心

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

本仓库是一个**本地 Skill 仓库**，存放用户自行创建或从网络获取的 Agent Skill。多个 Agent 共享此仓库，通过符号链接安装到各自的 skills 目录。

它的核心目标：让任何接入的 Agent 都能以统一的方式发现、安装、使用和更新 Skill。

> **🔗 操作本仓库前，必须先读：[CONTRIBUTING.md](CONTRIBUTING.md)**

---

## 仓库定位

- **本地 Skill 仓库**：所有自建 skill 的单一真相来源（single source of truth）
- **Agent 无关**：不绑定任何特定 Agent 框架，任何支持 Agent Skills 协议的客户端都可以使用
- **版本管理**：变更通过 Git 追踪，版本记录在 CHANGELOG.md
- **只按需更新**：仓库内的 skill 仅在用户明确要求时更新或推送

---

## 安装

### 通用安装

将本仓库 clone 到本地后，通过符号链接将需要的 skill 安装到你的 Agent 的 skills 目录：

```bash
# 假设 Agent skills 目录为 ~/.agent/skills/
ln -s ~/Ai/skill/分类目录/skill名称 ~/.agent/skills/skill名称
```

### 批量安装所有 Skill

```bash
for skill_dir in ~/Ai/skill/*/; do
  name=$(basename "$skill_dir")
  [ ! -L ~/.agent/skills/"$name" ] && ln -s "$(realpath "$skill_dir")" ~/.agent/skills/"$name"
done

# 也安装子分类中的 skill（如 xueqiu/ 下的具体 skill）
for skill_dir in ~/Ai/skill/*/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  name=$(basename "$skill_dir")
  [ ! -L ~/.agent/skills/"$name" ] && ln -s "$(realpath "$skill_dir")" ~/.agent/skills/"$name"
done
```

### 安装后的验证

```bash
# 确认 skill 可被 Agent 发现
ls ~/.agent/skills/
# 读取 skill 定义
cat ~/.agent/skills/skill名称/SKILL.md
```

---

## 仓库结构

```text
~/Ai/
├── README.md                         ← 本文件
├── CHANGELOG.md                      ← 版本变更记录
├── .gitignore                        ← Git 忽略规则
├── skill/                            ← Skill 根目录
│   ├── link-analysis/               ← 链接分析工作流
│   ├── serenity-skill/              ← Serenity 式供应链瓶颈研究
│   └── xueqiu/                      ← 雪球投资博主系统
│       ├── README.md                ← 雪球组说明
│       ├── CHANGELOG.md             ← 雪球组变更记录
│       ├── xq-registry/             ← 中控（注册表 + 调度）
│       ├── xq-{数字ID}/             ← 博主画像（40位）
│       ├── xueqiu-following-search/  ← 关注搜索
│       ├── xueqiu-to-bear/          ← 帖子转笔记
│       └── data/                    ← 共享数据
└── tools/                           ← CLI 工具
    └── autocli/
```

---

## Skill 标准结构

每个 Skill 目录应包含：

```text
skill-name/
├── SKILL.md          ← 必需：技能定义（Agent 加载入口）
├── README.md         ← 建议：人类可读的说明文档
├── CHANGELOG.md      ← 建议：版本变更记录
├── scripts/          ← 可选：辅助脚本
├── references/       ← 可选：参考资料
├── assets/           ← 可选：模板、数据文件
├── examples/         ← 可选：使用示例
└── LICENSE           ← 可选：许可证
```

参考 `serenity-skill/` 目录作为标准结构的示例。

---

## 准入规则

### ✅ 应该放在这里的

- 用户**自行创建**的 Skill
- 用户要求从**网络下载**的 Skill
- Skill 附带的脚本、模板、参考文件
- 跨 Agent 共享的数据文件

### ❌ 不应该放在这里的

- 从 Agent 内置商店安装的 Skill → 放 Agent 本地目录
- 包含敏感信息（密钥、token、密码）→ 永远不能放
- 仅单个 Agent 使用的私有状态/缓存 → Agent 本地工作目录
- 临时文件、调试产物 → 删除或放工作目录

---

## 版本管理

本仓库应作为代码库进行版本管理：

- 使用 Git 追踪所有变更
- Skill 更新后，提交到仓库并更新 CHANGELOG.md
- 合并时如遇冲突，自行处理的由 Agent 解决；无法自动处理的需提交给用户确认
- **仅在用户明确要求时更新或推送仓库内容**

---

## 协作规则

- **只读优先**：操作前先读目标文件，避免覆盖他人工作
- **追加优先**：数据文件只追加不覆盖
- **不留垃圾**：操作后清理临时文件
- **不写个人信息**：Skill 内容不应包含特定 Agent 的名称、路径、链接等个人信息
- **多 Agent 共用**：记住有其他 Agent 和你共享这个仓库

---

## 各 Skill 说明

### link-analysis — 链接分析工作流

收集用户链接（雪球、公众号、抖音等），定时整理生成分析文档存入熊掌记，并通过飞书发送浓缩摘要。

### serenity-skill — Serenity 式供应链瓶颈研究

基于 Serenity（@aleabroreddit）方法论的投资研究工作流。从市场叙事出发，沿产业链定位稀缺层，用公开证据验证，输出研究优先级排序。

### xueqiu/ — 雪球投资博主系统

40 位雪球博主的投资思维画像系统。包含中控注册表（xq-registry）、博主画像（xq-*）、关注搜索、帖子转笔记等完整工具链。

---

## 许可证

MIT

---

*最后更新：2026-06-10*
