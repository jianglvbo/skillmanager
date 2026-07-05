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
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .gitignore
├── skill/
│   ├── 内容提取/                  ← 内容提取
│   │   ├── 抖音视频摘要/           ←   抖音视频摘要
│   │   ├── 得到笔记/                 ←   得到大脑（Get笔记）
│   │   └── 微信文章/                 ←   公众号文章提取
│   ├── 知识框架/                  ← 投资知识框架
│   │   ├── 知识框架编排/             ←   全局编排
│   │   ├── 粗加工/                   ←   粗加工
│   │   ├── 维基提炼/                 ←   知识提炼
│   │   ├── 维基审查/                 ←   维基审查
│   │   ├── 知识问答/                 ←   知识问答
│   │   ├── 博主提炼/                 ←   博主画像提炼
│   │   └── 链接收集/                 ←   链接抓取
│   ├── 投资框架/                  ← 投资知识框架（新）
│   │   ├── investment-framework/   ←   全局编排者
│   │   ├── investment-coarse-processor/ ← 粗加工
│   │   ├── investment-refine/      ←   提炼执行器
│   │   └── investment-review/      ←   审查执行器
│   ├── 元工具/                    ← 元工具
│   │   ├── 仓库管理/                 ←   Ai/ 仓库管理
│   │   └── 技能准则/                 ←   Skill 设计准则
│   ├── 办公工具/                  ← 办公工具
│   │   ├── 磁盘清理/                 ←   macOS 磁盘清理
│   │   ├── 文档索引/                 ←   本地文档索引
│   │   └── browser-act/           ←   BrowserAct 浏览器自动化
│   ├── 投研分析/                    ← 券商投研技能集
│   │   ├── 深度报告/               ←   公司深度研究报告
│   │   ├── 行业研究/               ←   行业全景研究
│   │   ├── 读年报/                 ←   年报解读
│   │   ├── 业绩快评/               ←   业绩点评
│   │   ├── 调研纪要/               ←   调研笔记整理
│   │   ├── 晨会纪要/               ←   晨会汇报材料
│   │   ├── 研报摘要/               ←   卖方研报提取
│   │   └── 可比公司分析/           ←   估值对比矩阵
│   ├── 股权投资/                    ← PE/VC 投资技能集
│   │   ├── 筛项目/                 ←   BP/CIM 项目初筛
│   │   ├── 尽调清单/               ←   DD 清单生成
│   │   ├── 审条款/                 ←   TS/SPA 条款审查
│   │   ├── 投决备忘录/             ←   IC Memo 撰写
│   │   ├── 测收益/                 ←   IRR/MOIC 测算
│   │   └── 退出分析/               ←   退出路径对比
│   └── 雪球帖子采集/              ← 雪球博主帖子采集
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
├── CHANGELOG.md      ← 建议：版本变更记录
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

### 内容提取/ — 内容提取

| Skill | 说明 |
|:---|:---|
| `抖音视频摘要` | 抖音视频摘要（whisper 转录 + AI 总结） |
| `得到笔记` | 得到大脑（Get笔记）保存/搜索/管理 |
| `微信文章` | 微信公众号文章提取与转 Markdown |

### 知识框架/ — 投资知识框架

| Skill | 说明 |
|:---|:---|
| `知识框架编排` | 全局编排者：路径表、模板表、调用链、全局规则 |
| `粗加工` | 粗加工：补全 frontmatter 并归档 |
| `维基提炼` | 知识提炼：原始资源 → 维基条目 |
| `维基审查` | 维基审查：批量扫描健康度 |
| `知识问答` | 知识问答：基于维基仓库生成分析 |
| `博主提炼` | 博主画像提炼（雪球数据管道见 references/） |
| `链接收集` | 链接收集与抓取 |

### 投资框架/ — 投资知识框架（新）

| Skill | 说明 |
|:---|:---|
| `investment-framework` | 全局编排者：三大归属层 + 六大分类 + 标签体系 + 流水线 |
| `investment-coarse-processor` | 粗加工：格式整理 + 去广告 + metadata 补全 |
| `investment-refine` | 提炼执行器：原始资源 → 框架条目（一对多，可读性优先） |
| `investment-review` | 审查执行器：内容审查 + 结构审查 + 关联备注发现 |

### 元工具/ — 元工具

| Skill | 说明 |
|:---|:---|
| `仓库管理` | Ai/ 仓库 GitHub 版本管理 |
| `技能准则` | Agent Skill 设计准则（五层认知架构 + 分层执行 + 认知卸载 + 六段模板） |

### 办公工具/ — 办公工具

| Skill | 说明 |
|:---|:---|
| `磁盘清理` | macOS 磁盘分析与清理 |
| `文档索引` | 本地文档索引与搜索（BM25 + 向量） |
| `browser-act` | BrowserAct 浏览器自动化（隐身反检测 + 结构化提取） |

### 投研分析/ — 券商投研技能集

| Skill | 说明 |
|:---|:---|
| `深度报告` | 券商体例公司深度研究（行业+商业模式+财务+估值） |
| `行业研究` | 行业全景研究（市场空间+产业链+竞争格局） |
| `读年报` | A股年报 PDF 解读，含行业适配和风险扫描 |
| `业绩快评` | 业绩公告快速点评（超预期判断+单季趋势） |
| `调研纪要` | 调研笔记/电话会转录标准化整理 |
| `晨会纪要` | 晨会汇报材料生成 |
| `研报摘要` | 卖方研报提取与观点分歧矩阵 |
| `可比公司分析` | 可比公司筛选与估值指标矩阵 |

### 股权投资/ — PE/VC 投资技能集

| Skill | 说明 |
|:---|:---|
| `筛项目` | BP/CIM 项目初筛（六维评分+红线快筛） |
| `尽调清单` | 结构化 DD 清单（财务/法律/业务/技术） |
| `审条款` | TS/SPA/SHA 条款审查（含九民纪要合规） |
| `投决备忘录` | 投委会 IC Memo 撰写 |
| `测收益` | IRR/MOIC/DPI 测算（含瀑布分配） |
| `退出分析` | 退出路径对比（IPO/并购/S基金/回购） |

### 独立 Skill

| Skill | 说明 |
|:---|:---|
| `雪球帖子采集` | 雪球博主帖子采集（Chrome Extension MCP） |

---

## 许可证

MIT

---

*最后更新：2026-07-05*
