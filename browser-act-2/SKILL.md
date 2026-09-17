---
name: browser-act
description: >
  BrowserAct 浏览器自动化 CLI，专为 AI Agent 设计。支持隐身浏览器绕过反爬、
  结构化数据提取、Stealth 提取（stealth-extract）、多浏览器并行操作、
  表单填写、截图、CAPTCHA 处理、人机协作（远程协助）。
  触发词：「browser-act」「BrowserAct」「浏览器自动化」「隐身提取」「stealth-extract」
  「绕过反爬」「网页抓取」「浏览器操作」「stealth 浏览器」。
  区别于 agent-browser / web-access：BrowserAct 提供 stealth 反检测、
  指纹伪装、代理切换、结构化提取等专业能力。
  前提：需要 `browser-act` CLI 已安装（uv tool install browser-act-cli --python 3.12）。
allowed-tools: Bash
metadata:
  agent_created: true
  version: "1.1.0"
  cli_version: "1.0.1"
  skill_source: "https://github.com/browser-act/skills/tree/main/browser-act"
  install_cmd: "uv tool install browser-act-cli --python 3.12"
  requires:
    runtime: "Python 3.12+"
    browser: "Chrome/Chromium"
    packages: "browser-act-cli (via uv)"
---

# BrowserAct — 浏览器自动化 Skill for WorkBuddy

BrowserAct 是一个专为 AI Agent 设计的浏览器自动化 CLI 工具。
它在普通浏览器自动化的基础上，提供了 **隐身反检测**、**结构化数据提取**、
**人机协作** 等企业级能力。

## Default Stance

- **默认行为**：收到网页抓取/浏览器操作请求时，优先评估是否需要用 BrowserAct
  （涉及反爬、需要 JS 渲染、需要登录态、需要复杂交互时使用）
- **禁止行为**：不要直接用 Bash 执行裸的 `browser-act` 命令而不加载本 Skill；
  不要跳过 `get-skills core` 步骤；不要在未获用户确认的情况下创建/删除浏览器

## 核心能力

| 能力 | 说明 |
|:---|:---|
| **stealth-extract** | 零配置提取受保护页面内容（隐身浏览器 + 反检测） |
| **stealth 浏览器** | 指纹伪装、动态代理、TLS 轮换，绕过反爬 |
| **chrome 模式** | 复用本地 Chrome 登录态，免重复登录 |
| **结构化提取** | 返回结构化数据而非原始 HTML，Token 消耗降低 90%+ |
| **人机协作** | Agent 卡住时生成远程链接，用户接管后 Agent 继续 |
| **多浏览器并发** | 独立 Cookie/指纹/代理，互不干扰 |
| **CAPTCHA 解决** | 自动处理验证码（需 API key） |

## Workflow

### 1. 启动前：加载运行指令
```bash
browser-act get-skills core --skill-version 2.0.2
```
**禁止跳过此步骤** — 它返回环境状态、可用浏览器列表、操作指令。

### 2. 简单提取（无需浏览器会话）
```bash
browser-act stealth-extract <URL>
```
适用于：抓取受保护页面内容、获取 JS 渲染后的数据。

### 3. 完整浏览器会话
```bash
# 打开浏览器
browser-act --session <name> browser open <id> <URL>

# 查看页面可交互元素
browser-act --session <name> state

# 交互操作
browser-act --session <name> click <index>
browser-act --session <name> input <index> "<text>"
browser-act --session <name> screenshot
```

### 4. 浏览器管理
```bash
browser-act browser list          # 列出所有浏览器
browser-act browser create ...    # 创建新浏览器（需用户确认）
browser-act browser delete <id>   # 删除浏览器（需用户确认）
```

## 安全规则

以下操作 **必须获得用户显式确认**：
- 创建新浏览器
- 删除浏览器
- 导入浏览器 Profile
- 代理变更
- 隐私开关
- 登录、表单提交、文件上传

数据隐私：所有 Cookie、登录态、页面内容均存储在本地，不上传。

## 内容抓取规则

### 规则 1：置顶帖时间处理

当抓取用户首页帖子列表时，**置顶帖可能发布于多天前**，其时间不应被纳入"今日帖子"范围。
- 展示置顶帖时，**必须标注原始发布日期**，不要将其归类为"今天"
- 时间范围统计（如"1~4小时前"）应排除置顶帖
- 在输出中明确区分：置顶帖 vs 今日帖

### 规则 2：截断内容自动补全

雪球等平台的主页列表会对长文进行截断（显示「展开」按钮），`get markdown` 只能拿到截断版本。
- 检查 `get markdown` 输出中是否出现 `展开`、`...` 等截断标记
- 如发现截断，**必须用 `navigate` 导航到文章详情页**获取全文：

```bash
# 主页截断版 → 仅摘要
browser-act --session <name> browser open <id> "https://xueqiu.com/u/<xq_id>"

# 文章详情页 → 完整全文 ✅
browser-act --session <name> navigate "https://xueqiu.com/<xq_id>/<statement_id>"
```

- 优先补全有实质性内容的长文（专栏、分析文章），回复类短帖可不补全
- 补全后更新输出文件，标记「✅ 全文」vs「⚠️ 摘要」

## 浏览器模式

| 模式 | 命令 | 适用场景 |
|:---|:---|:---|
| **Chrome** | `browser-act browser create --type chrome` | 复用本地登录态 |
| **Stealth 隐私** | `browser-act browser create --type stealth` | 每次新指纹+新IP，批量抓取 |
| **Stealth 固定身份** | `browser-act browser create --type stealth --fixed` | 稳定身份，多账号运营 |

## 安装与更新

```bash
# 安装（需 uv + Python 3.12+）
uv tool install browser-act-cli --python 3.12

# 更新
uv tool upgrade browser-act-cli

# 验证
browser-act --version
```

可选：注册免费账号获取 API key（解锁 stealth 浏览器、stealth-extract、动态代理等功能）
```bash
browser-act auth login
```

## 与已有 Skill 的关系

| 场景 | 用哪个 |
|:---|:---|
| 普通网页抓取、无反爬 | `web-access` / `agent-browser` |
| 反爬严格（亚马逊、淘宝等）、需隐身 | **BrowserAct** |
| 需登录态、复杂表单交互 | **BrowserAct** (chrome 模式) |
| 批量数据提取、结构化输出 | **BrowserAct** (stealth-extract) |

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| extracted_content | string/markdown | 抓取/提取的内容（含「✅ 全文」/「⚠️ 摘要」标记） |
| structured_data | object | stealth-extract 的结构化输出（JSON） |
| session_name | string | 使用的浏览器会话名 |
| truncated | boolean | 内容是否截断（需 navigate 补全） |
| pinned_post_dates | list[string] | 置顶帖原始发布日期（不纳入"今日"统计） |
| user_confirm_required | boolean | 是否触发需用户确认的操作（建/删浏览器等） |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 启动前 | browser-act CLI（uv 安装） | `get-skills core` 返回环境状态与操作指令 | **执行** |
| 抓取/交互 | browser-act CLI | stealth-extract / session 操作 | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户请求（URL / 抓取目标 / 交互意图） |
| 2 | browser-act CLI 输出（真实页面数据） |
| 3 | 本文件内容抓取规则（置顶帖/截断补全） |

---

## 自检

- [ ] 启动前是否执行 `browser-act get-skills core`（未跳过）？
- [ ] 涉及建/删浏览器、登录、表单提交是否已获用户确认？
- [ ] 置顶帖是否标注原始发布日期（未误归"今日"）？
- [ ] 内容截断时是否 navigate 详情页补全并标记「✅ 全文」/「⚠️ 摘要」？
- [ ] Cookie/登录态是否仅存本地（未上传）？
