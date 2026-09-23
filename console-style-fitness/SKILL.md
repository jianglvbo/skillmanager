---
name: console-style-fitness
description: 「控制台风格」（console-style）健身应用的样式规范与维护执行器。风格本质：玻璃拟态 + 极光渐变 + 多主题 token 的类苹果控制台 UI。覆盖：风格 token 体系（玻璃/渐变/圆角/阴影/10 主题×日夜）、单文件应用架构与数据模型（state/登录/周计划/器械/三餐偏好/力量部位）、AI 生成链路（计划/预测/建议 + 确定性修正）、自定义组件（cxSelect/chip）、GitHub Pages 部署与结构校验。触发词：「健身塑形控制台」「fitness-console」「console-style」「一键生成计划」「计划参数」「运动库」「食物库」等修改/维护/部署该风格应用的场景。排除：健身内容创作、饮食营养建议撰写。
---

# Default stance

## 核心原则

1. **单文件权威**：应用核心是 `web/index.html`（约 3200 行），所有 UI/逻辑/样式在其中；`server.js` 只负责数据同步与 AI Key 分发。改动前先读文件确认现状，禁止凭记忆改。
2. **确定性修正优先**：AI 输出（计划/预测）不可信，生成后必须经本地修正层兜底——周计划休息日强制无训练、摄入量按目标热量校准、力量动作按部位+器械过滤。LLM 自觉不可依赖。
3. **结构变更必须机器校验**：HTML 区块交换/删除后，必须校验 ① section 开标签完整 ② div 开闭平衡 ③ JS 语法。跑 `scripts/validate.py`，禁止目测。
4. **样式走设计令牌**：颜色/圆角/阴影一律用 CSS 变量（--accent/--glass/--radius 等），禁止硬编码裸色值；自定义下拉用 cxSelectHTML，不用系统 select。

## 禁止行为

- **禁止改动内部存储 key**：`fitness-console-session`、`fitness-console-data-{user}`、迁移标记——改动即丢数据。
- **禁止凭猜写 hashPw 结果**：新增账号必须用文件内原 `hashPw` 函数计算（djb2 变体 + 盐 + 200 轮），并在本地校验通过。
- **禁止只改线上不同步**：本机 index.html 与 GitHub Pages（jianglvbo/fitness-plan）必须同步，改动后 git commit + push。
- **禁止在弹窗/表单用裸 select 破坏风格**：新下拉优先 cxSelectHTML；颜色/主题变更必须同步 10 套主题变量，避免单主题适配。

# Workflow

## 第一步：定位任务类型

| 任务 | 路径 |
|:--|:--|
| 新增/修改功能 | 第二步 → 第四步 |
| 修复结构错乱 | 第三步（校验）优先 |
| 新增账号 | 第六步 |
| 部署/同步 Pages | 第七步 |
| 样式调整 | 第四步 + references/design-tokens.md |

## 第二步：读现状

读 `web/index.html` 相关段（函数/区块），确认数据结构与现有实现，禁止以旧文件为参照做格式判断。

## 第三步：修改 + 机器校验（每次改动必做）

1. 改 HTML 结构（section 交换/增删区块）→ 校验 section 开标签 + div 平衡
2. 改 JS → `node --check` 语法
3. 全部完成 → 跑 `scripts/validate.py`（语法 + div 平衡 + 服务 200）

## 第四步：按类型实施

- **UI 组件**：新下拉用 `cxSelectHTML(id, value, options)` + `bindCustomSelects(root, onChange)`；多选用 chip 切换（`.chip.active`）。
- **数据字段**：`state` 新增字段必须同步 `defaultState()` + `migratePlanParams()`/`migrateExerciseCats()`（旧数据补齐），否则旧用户加载报错。
- **AI 链路**：prompt 加参数后，同步更新 system 说明；生成结果必经确定性修正（休息日/营养校准/部位器械过滤）。
- **动效**：进入 `pageIn`（0.5s cubic-bezier(.22,1,.36,1)）；过渡禁露白靠 html 渐变背景（单层，body 不设背景）。

## 第五步：日志与交付

变更摘要写入工作区记忆日志；交付时 present_files 打开本机 `http://127.0.0.1:8699`。

## 第六步：新增账号

用 `hashPw('密码', '<用户名>-salt-0810')`（从文件提取原函数）算哈希 → 追加进 `BUILTIN_USERS` → 本地 node 校验登录。

## 第七步：GitHub Pages 部署

`cp ~/Project/fitness-console/web/index.html "$PAGES_REPO/index.html"`（`$PAGES_REPO`＝`jianglvbo/fitness-plan` 的本地克隆；**原写的 `/tmp/fitness-plan` 不是 git 仓库**）→ commit+push（作者 jianglvbo）→ Pages 数分钟自动更新。本机直连 github.io 被墙，验证走代理 `-x http://127.0.0.1:7890`。

# Output format

| 字段 | 类型 | 说明 |
|:--|:--|:--|
| 变更点 | 数组 | 每项：文件 + 位置 + 改动说明 |
| 校验结果 | 对象 | syntax/divBalance/service 三项布尔 |
| 数据兼容 | 布尔 | 是否涉及 state 新字段（需迁移） |
| 部署同步 | 布尔 | 是否已 push Pages |

# Relative files

| 场景 | 加载文件 | 内容 | 方式 |
|:--|:--|:--|:--|
| 样式调整/新 UI | `references/design-tokens.md` | 主题 token、玻璃拟态、圆角/字体/图标规范 | 读取 |
| 数据/账号/AI 链路 | `references/data-model.md` | state 结构、登录、周计划/器械/三餐、AI 修正层 | 读取 |
| 每次改完 | `scripts/validate.py` | 语法 + div 平衡 + section 校验 | **执行** |

# Source hierarchy

| 优先级 | 来源 |
|:--|:--|
| 1 | 用户显式约定（当前需求为最高优先） |
| 2 | 本项目既有代码结构与设计令牌（以代码为准，不以旧文件为准） |
| 3 | 本 skill 的 references 规范 |
| 4 | 通用 Web 工程实践 |

# 自检

- [ ] YAML 门控：name + description 含触发词与排除条件？
- [ ] Default stance：核心原则 + 禁止行为各 ≥3 条？
- [ ] 修改后跑了 validate.py（语法/div/section/服务）？
- [ ] state 新字段同步了 defaultState + 迁移函数？
- [ ] 改动同步了 GitHub Pages？
- [ ] 执行路径自检：假设现在接到「修改健身塑形控制台 XX」任务，按本 skill 流程能否完整走通？（含校验脚本路径、部署路径）
