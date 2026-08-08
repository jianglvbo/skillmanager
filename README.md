<div align="center">

# ~/Ai — Agent Skill 本地仓库

### 自建 Agent Skill 的统一存储、分发与版本管理中心

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

本仓库是一个**本地 Skill 仓库**，存放用户自行创建或从网络获取的 Agent Skill。多个 Agent 共享此仓库，通过复制安装到各自的 skills 目录。

> 📦 已纳入 GitHub 版本管理：**[github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)**

它的核心目标：让任何接入的 Agent 都能以统一的方式发现、安装、使用和更新 Skill。

> **🔗 操作本仓库前，必须先读：[CONTRIBUTING.md](CONTRIBUTING.md)**

---

## 仓库定位

- **本地 Skill 仓库**：所有自建 skill 的单一真相来源（single source of truth）
- **GitHub 远程托管**：推送到 [github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)，支持版本管理和多设备同步
- **Agent 无关**：不绑定任何特定 Agent 框架，任何支持 Agent Skills 协议的客户端都可以使用
- **版本管理**：变更通过 Git 追踪（Conventional Commits），历史见 `git log --oneline`
- **只按需更新**：仓库内的 skill 仅在用户明确要求时更新或推送

---

## 安装

### 通用安装

将本仓库 clone 到本地后，通过**复制**将需要的 skill 安装到你的 Agent 的 skills 目录（**严禁 symlink**，保持仓库与运行实例隔离）：

```bash
cp -r ~/Ai/skill/分类目录/skill名称 ~/.agent/skills/skill名称
```

### 批量安装所有 Skill

```bash
for skill_dir in ~/Ai/skill/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  name=$(basename "$skill_dir")
  cp -r "$skill_dir" ~/.agent/skills/"$name"
done

# 也安装子分类中的 skill（如 xueqiu/ 下的具体 skill）
for skill_dir in ~/Ai/skill/*/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  name=$(basename "$skill_dir")
  cp -r "$skill_dir" ~/.agent/skills/"$name"
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
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── skill/
│   ├── meta/                      ← 元工具（skill 管理类）
│   │   ├── ai-repo-manager/       ←   Ai/ 仓库管理
│   │   ├── git-ops/               ←   通用 git 提交管理
│   │   └── guidelines/            ←   Skill 设计准则（skill-guidelines）
│   ├── content/                   ← 内容提取
│   │   ├── browser-act/           ←   BrowserAct 浏览器自动化
│   │   ├── douyin-video-summary/  ←   抖音视频摘要
│   │   ├── wechat-article/        ←   公众号文章提取
│   │   └── full-text-organizer/   ←   语音转录稿→书面文章
│   ├── office/                    ← 办公工具
│   │   ├── mac-cleaner/           ←   macOS 磁盘清理
│   │   └── qmd/                   ←   本地文档索引
│   └── investment/                ← 投资知识框架
│       ├── investment-framework/  ←   全局编排者
│       ├── investment-coarse-processor/ ← 粗加工
│       ├── investment-refine/     ←   提炼执行器
│       ├── investment-review/     ←   审查执行器
│       └── xq-post-fetch/         ←   雪球帖子采集
└── tools/
    ├── autocli/
    └── browser-act-cli/
```

---

## Skill 标准结构

每个 Skill 目录应包含：

```text
skill-name/
├── SKILL.md          ← 必需：技能定义（Agent 加载入口）
├── README.md         ← 建议：人类可读的说明文档
├── scripts/          ← 可选：辅助脚本
├── references/       ← 可选：参考资料
├── assets/           ← 可选：模板、数据文件
├── examples/         ← 可选：使用示例
└── LICENSE           ← 可选：许可证
```

参考 `知识框架/知识框架编排/` 目录作为标准结构的示例。

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

本仓库已纳入 GitHub 版本管理：

- **远程仓库**：[github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)（主分支：`main`）
- **本地路径**：`~/Ai/`
- 使用 Git 追踪所有变更（Conventional Commits，历史见 `git log --oneline`）
- Skill 更新后，提交到仓库（满 5 次 commit 自动 push 一次）
- 合并时如遇冲突，自行处理的由 Agent 解决；无法自动处理的需提交给用户确认
- **仅在用户明确要求时更新或推送仓库内容**

### 首次推送到 GitHub

```bash
cd ~/Ai
git init
git branch -m main
git remote add origin https://github.com/jianglvbo/Ai.git
git add -A
git commit -m "初始提交"
# 大仓库（含二进制文件）推送时可能需要增大 buffer：
git -c http.postBuffer=2147483648 push -u origin main
```

### 日常同步

先本地提交，再拉取远程，最后推送：

```bash
cd ~/Ai
# 1. 提交本地变更
git add -A
git commit -m "变更说明"

# 2. 检查远程是否有新提交，如有则合并
git fetch origin
git pull --rebase origin main

# 3. 推送到远程
git push origin main
```

---

## 协作规则

- **只读优先**：操作前先读目标文件，避免覆盖他人工作
- **追加优先**：数据文件只追加不覆盖
- **不留垃圾**：操作后清理临时文件
- **不写个人信息**：Skill 内容不应包含特定 Agent 的名称、路径、链接等个人信息
- **多 Agent 共用**：记住有其他 Agent 和你共享这个仓库

---

## 各 Skill 说明

### meta/ — 元工具（skill 管理类）

| Skill | 说明 |
|:---|:---|
| `ai-repo-manager` | Ai/ 仓库 GitHub 版本管理（README 更新约定、cp -r 安装） |
| `git-ops` | 通用 git 提交管理（检测变更/提交/自定义信息/历史/推送） |
| `guidelines` | Agent Skill 设计准则（skill-guidelines，五层认知架构 + 六段模板） |

### content/ — 内容提取

| Skill | 说明 |
|:---|:---|
| `browser-act` | BrowserAct 浏览器自动化（隐身反检测 + 结构化提取） |
| `douyin-video-summary` | 抖音视频摘要（whisper 转录 + AI 总结） |
| `wechat-article` | 微信公众号文章提取与转 Markdown |
| `full-text-organizer` | 语音转录稿（视频/播客/口述）→ 结构化书面文章 |

### office/ — 办公工具

| Skill | 说明 |
|:---|:---|
| `mac-cleaner` | macOS 磁盘分析与清理 |
| `qmd` | 本地文档索引与搜索（BM25 + 向量） |

### investment/ — 投资知识框架

| Skill | 说明 |
|:---|:---|
| `investment-framework` | 全局编排者：三大归属层 + 六大分类 + 标签体系 + 流水线 |
| `investment-coarse-processor` | 粗加工：格式整理 + 去广告 + metadata 补全 |
| `investment-refine` | 提炼执行器：直接执行，原始资源/帖子集 → 框架条目（一对多，可读性优先） |
| `investment-review` | 审查执行器：内容审查 + 结构审查 + 关联备注发现 |
| `xq-post-fetch` | 雪球帖子采集：browser-act 抓全文 + 截断补全 + 结构化 markdown 输出 |

---

## 许可证

MIT

---

*最后更新：2026-08-08*
