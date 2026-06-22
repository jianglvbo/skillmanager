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
- **版本管理**：变更通过 Git 追踪，推送前更新 CHANGELOG.md
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
├── README.md                         ← 本文件
├── CHANGELOG.md                      ← 版本变更记录
├── .gitignore                        ← Git 忽略规则
├── skill/                            ← Skill 根目录
│   ├── ai-repo-manager/              ← Ai/ 仓库管理（Git 同步 + 文档迭代）
│   ├── douyin-video-summary/        ← 抖音视频摘要（音频提取 + whisper 转录 + 结构化总结）
│   ├── investment-knowledge-framework/ ← 投资分析知识管理框架（五层流水线操作手册）
│   ├── knowledge-pipeline/           ← 知识框架全局编排者（路径表、模板表、调用链、全局规则）
│   ├── link-analysis/               ← 链接分析工作流
│   ├── mac-cleaner/                 ← macOS 磁盘分析与垃圾清理
│   ├── qmd/                         ← 本地文档索引与搜索（CLI 工具）
│   ├── serenity-skill/              ← Serenity 式供应链瓶颈研究
│   ├── skill-guidelines/            ← Agent Skill 准则（八条核心准则）
│   ├── wechat-article/             ← 微信公众号文章提取（UA 模拟 + 正文转 Markdown）
│   └── xueqiu/                      ← 雪球投资博主系统
│       ├── README.md                ← 雪球组说明
│       ├── CHANGELOG.md             ← 雪球组变更记录
│       ├── xq-blogger-analysis/     ← 博主画像分析操作手册
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

本仓库已纳入 GitHub 版本管理：

- **远程仓库**：[github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)（主分支：`main`）
- **本地路径**：`~/Ai/`
- 使用 Git 追踪所有变更
- Skill 更新后，提交到仓库并更新 CHANGELOG.md
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

### ai-repo-manager — Ai/ 仓库管理

管理 `~/Ai/` 仓库的 GitHub 版本控制全流程。包含六步强制流程：变更 → 更新 README.md → 更新 CHANGELOG.md → Git 提交 → 推送 GitHub → 确认同步。确保每次变更文档完整、版本号正确。

### douyin-video-summary — 抖音视频摘要

从抖音链接提取视频内容并生成结构化摘要。工作流：解析链接 → 浏览器拦截音频 URL → curl 下载 → ffmpeg 转 WAV → whisper.cpp 本地转录 → AI 生成摘要。支持飞书文档同步。依赖 whisper-cpp、ffmpeg。

### investment-knowledge-framework — 投资分析知识管理框架

基于 Obsidian vault 的五层循环流水线操作手册。覆盖粗加工、提炼（多维度）、问答、迭代四个核心流程，包含 frontmatter 模板、标签体系、审查规则和交叉链接原则。当用户要求处理投资文章、提炼知识或管理知识库时使用。

### knowledge-pipeline — 知识框架全局编排者

投资知识管理系统的全局调配中心。唯一持有路径表、模板路径表和全局规则的地方。定义投资知识全流程、博主画像全流程的调用链和模块分工。加工 skill 全部无默认值，路径变更只改这里。

### link-analysis — 链接分析工作流

收集用户链接（雪球、公众号、抖音等），存入 Obsidian 投资分析框架粗制品目录，支持飞书/IM 和 WorkBuddy 对话两种收集渠道。

### mac-cleaner — macOS 磁盘分析与垃圾清理

分析 Mac 存储空间占用，扫描缓存、应用残留、Time Machine 快照等垃圾文件，安全清理释放空间。包含三段式工作流：扫描分析 → 生成建议 → 安全清理（osascript 废纸篓）。

### qmd — 本地文档索引与搜索

基于 `qmd` CLI 的本地文档索引与搜索工具。支持全文检索（BM25）、向量语义搜索、混合查询+LLM 重排序，以及 MCP Server 模式。可对 Obsidian vault 等本地 Markdown 仓库建索引。

### serenity-skill — Serenity 式供应链瓶颈研究

基于 Serenity（@aleabroreddit）方法论的投资研究工作流。从市场叙事出发，沿产业链定位稀缺层，用公开证据验证，输出研究优先级排序。

### skill-guidelines — Agent Skill 准则

适用于创建新 Skill 与修改已有 Skill 的全生命周期。八条核心准则：职责单一与模块化、精准的描述与语义发现、确定性优先与结构刚性、渐进式披露与少即是多、核心知识的人类主导、内置验证循环与可观测性、安全性与权限边界、标准化输出与工程化结构。包含级别分类（轻量/标准/重量）、设计模式和四层工程结构。

### wechat-article — 微信公众号文章提取

从微信公众号链接（mp.weixin.qq.com）提取文章正文并转为 Markdown。通过模拟微信客户端 UA 绕过反爬限制，支持标题、作者、公众号名称、发布日期和完整正文的结构化提取，可直接写入 Obsidian 粗制品目录。

### xueqiu/ — 雪球投资博主系统

雪球博主画像分析系统。包含博主画像分析操作手册（xq-blogger-analysis）、关注搜索、帖子转笔记等工具链。博主画像数据存储在 Obsidian vault 中。

---

## 许可证

MIT

---

*最后更新：2026-06-23*
