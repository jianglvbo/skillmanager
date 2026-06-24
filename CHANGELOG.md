# Changelog

本文件记录 `~/Ai/` 仓库的整体版本变更历史。

## 1.15.0 — 2026-06-25

### Changed
- **wiki-refine**：新增知识萃取分析步骤，解决时间绑定内容直接作为维基条目的问题
  - 流程新增步骤3「知识萃取分析」：区分可复用知识与时间绑定信息，判断是否拆分为多条条目
  - 新增标题命名规则：以知识概念命名，不以原文标题/日期/事件命名
  - 提炼原则从6条扩充为7条：「忠于原文」升级为「忠于原文但可泛化」，新增「去时间绑定」
  - 自检清单新增4项萃取相关检查
- **knowledge-pipeline (v5.3.0)**：调用链说明补充多条目产出注释
- **五个子模板增加萃取引导**：
  - wiki-opinion：新增「适用场景与边界」section，各 section 增加泛化引导
  - wiki-market-overview：新增「结构特征」section，驱动因素增加可复用框架提取引导
  - wiki-method / wiki-case-study / wiki-data-interp：各 section 增加萃取引导语

## 1.14.0 — 2026-06-24

### Changed
- **knowledge-pipeline (v5.2.0)**：路由决策层新增作者-博主联动
  - 命中「投资知识全流程」时检查 author 是否在 BLOGGER_CONSOLE 中
  - 若匹配则并行触发「博主画像纯提炼」链路，两条链路独立并行、互不耦合

## 1.13.0 — 2026-06-24

### Changed
- **Skill 目录重新整理**：按 content/knowledge-framework/meta/office 四大分类归档
  - `content/`：douyin-video-summary、getnote、wechat-article
  - `knowledge-framework/`：保持不变（7 个子 skill）
  - `meta/`：ai-repo-manager、skill-guidelines
  - `office/`：mac-cleaner、qmd
  - `xq-post-fetch/`：独立保留（v3.0.0，Chrome Extension MCP 方案）

### Removed
- **serenity-skill/**：已废弃，清理残留目录（v1.12.0 标记删除但未实际清理）
- **xueqiu/**：旧版雪球系统目录，已被顶层 xq-post-fetch v3.0.0 替代
- **knowledge/**：空壳分类目录（v1.10.0 迁移残留，7 个子目录均无 SKILL.md）
- **investment/**：空目录
- **content/douyin-video-summary/models/ggml-small.bin**：孤立的 465MB whisper 模型（已移至废纸篓）

## 1.12.0 — 2026-06-24

### Added
- **xq-post-fetch**：雪球博主帖子采集 skill（v2.1.0）
  - CDP Proxy + user_timeline API 采集
  - 批量采集、分级超时重试、断点续采、多页分页
  - JS 模板外部化 + 防御性编程

### Removed
- **serenity-skill**：已废弃删除

## 1.11.0 — 2026-06-23

### Changed
- **skill-guidelines**：按《Agent Skill 设计纲领》全面重写（v3.1.0 → v5.0.0）
  - 新增"核心定位与认知重构"章节（Skill ≠ 脚本 ≠ 知识库 ≠ 工具）
  - 八原则扩展为完整的战略指导（新增"精准描述与语义发现""标准化输出与工程化结构"独立原则）
  - 提炼九条工程化落地规律（战术执行层）
  - 扩展最小必要结构模板（七要素 → 八要素，新增语言约定章节）
  - 新增审查清单（必查项 + 质量项 + 安全项）
  - WorkBuddy 侧目录从 `skill-design` → `guidelines`

## 1.10.0 — 2026-06-23

### Added
- **knowledge-framework/ 目录**：知识框架专用子目录，收录 10 个 pipeline skill

### Changed
- knowledge-pipeline、wiki-refine、link-analysis 移入 `skill/knowledge-framework/`
- 新增 coarse-processor、wiki-review、qa-ask、blogger-refine、link-ingest、investment-knowledge-framework、xq-blogger-analysis 到 knowledge-framework/

### Removed
- `skill/my-knowledge/`：旧版知识框架目录，内容已迁移到 knowledge-framework/

## 1.9.0 — 2026-06-23

### Added
- **knowledge-pipeline skill**：知识框架全局编排者（`skill/knowledge-pipeline/`）
  - 唯一持有路径表、模板路径表、全局规则和调用链
  - 投资知识全流程：link-ingest → coarse-processor → wiki-refine → qa-ask
  - 博主画像全流程：link-ingest → coarse-processor → blogger-refine
  - 提问模板（`assets/question-templates.md`）：板块分析/个股分析/博主观点汇总/宏观环境分析
  - 全局规则：日期格式 YYYY年M月D日、提炼前必读控制台、新增画像扫描全部原始资源

### Changed
- **skill-design → skill-guidelines**：重命名为 Agent Skill 准则（`skill/skill-guidelines/`）
  - 适用范围从「创建/重构」扩展到「全生命周期」（创建 + 修改 + 维护）
  - 触发词新增「skill修改」「修改skill」「skill规范」
  - 标题从「设计原则」改为「准则」
  - version：3.0.0 → 3.1.0
- **README.md**：目录结构和 Skill 列表更新；knowledge-pipeline 和 skill-guidelines 描述更新

## 1.8.0 — 2026-06-22

### Added
- **skill-design skill**：Skill 设计规范（`skill/skill-design/`）
  - 八条核心设计原则：职责单一与模块化、精准描述与语义发现、确定性优先与结构刚性、渐进式披露、人类主导核心知识、内置验证循环与可观测性、安全性与权限边界、标准化输出与工程化结构
  - 包含级别分类（轻量/标准/重量）和设计模式速览
  - 四层工程结构：自然语言负责判断编排、脚本负责稳定执行、模板负责规范输出、参考资料补充细节

### Changed
- **README.md**：目录结构和 Skill 列表加入 skill-design-checklist

## 1.7.0 — 2026-06-18

### Added
- **investment-knowledge-framework skill**：投资分析知识管理框架操作手册（`skill/investment-knowledge-framework/`）
  - 从 Obsidian vault 内文件迁移为独立 skill
  - 整合粗加工、提炼、问答、迭代四个流程
  - 整合三套 frontmatter 模板（原始资源、维基条目、问答看板）
  - 整合标签体系和审查规则
  - 包含核心约定：日期格式、wikilink 路径规范、多维度提炼、交叉链接

### Changed
- **README.md**：目录结构和 Skill 列表加入 investment-knowledge-framework

## 1.6.0 — 2026-06-17

### Added
- **wechat-article skill**：微信公众号文章提取工具（`skill/wechat-article/`）
  - `scripts/wechat_extract.py`：通过模拟微信客户端 UA（MicroMessenger）绕过反爬
  - 支持 JSON 和 Markdown 两种输出模式，含 frontmatter（title/source/author/date/status）
  - 提取标题、作者、公众号名称、发布日期（ct 时间戳解析）、摘要、正文
  - 图片 URL 提取（data-src），支持 `--with-images` 内联模式
  - 错误处理：文章删除/权限限制/视频类型等场景
- **README.md**：目录结构和 Skill 列表加入 wechat-article

### Changed
- **link-analysis**：公众号内容抓取策略从 `curl / autocli` 改为引用 `wechat-article` skill 的专用脚本

## 1.5.0 — 2026-06-17

### Added
- **douyin-video-summary skill**：抖音视频摘要工具（`skill/douyin-video-summary/`）
  - 来源：skills.sh 社区（liu-wei-ai/douyin-video-summary），1.5K 安装量
  - 工作流：解析抖音链接 → 浏览器拦截音频 URL → curl 下载 → ffmpeg 转 WAV → whisper.cpp 本地转录 → 结构化摘要
  - 包含辅助脚本 `scripts/download_audio.sh`、`scripts/transcribe.sh` 和一键依赖安装 `scripts/setup.sh`
  - whisper 模型文件（ggml-small.bin, 465MB）通过 hf-mirror.com 国内镜像下载到 `models/` 目录
  - 支持飞书文档同步（`references/feishu-sync.md`）
  - 依赖：whisper-cpp、ffmpeg（setup.sh 自动安装）

### Changed
- **link-analysis**：重大改写，从熊掌记（Bear）迁移到 Obsidian 投资分析框架
  - 链接收集：区分飞书/IM（存粗制品）和 WorkBuddy 对话（仅存档）两种渠道
  - 粗加工流程：从粗制品目录读取 → 补 frontmatter → 归档到 `2 原始资源仓库/`
  - 新增 Obsidian Vault 路径和目录结构说明
- **xq-registry**：增量数据刷新（2026-06-16）
  - 总帖子分析量：4643 → 4796（+153 条）
  - 18 位博主的 SKILL.md 新增当日发帖更新章节
  - 各博主 post_count 和 info_cutoff 同步更新
- **README.md**：目录结构和 Skill 列表加入 douyin-video-summary；更新 link-analysis 描述
- **.gitignore**：添加 `*.bin` 和 `skill/xueqiu/data/*.json` 规则

## 1.4.1 — 2026-06-16

### Changed
- **qmd/SKILL.md**：新增「Agent 使用模式」章节，定义四种 Agent 检索工作流（关键词定位 / 语义搜索 / URI→路径转换 / 索引检查）；新增 Obsidian Vault 路径映射表（qmd:// URI ↔ 真实文件路径）；触发条件加入 Agent 自动化触发说明

## 1.4.0 — 2026-06-16

### Added
- **qmd skill**：本地文档索引与搜索工具（`skill/qmd/`）
  - 基于 `qmd` CLI（v0.9.0），支持对本地 Markdown 文件建立全文索引和向量嵌入
  - 三种搜索模式：BM25 关键词搜索（`search`）、向量语义搜索（`vsearch`）、混合查询+LLM 重排序（`query`）
  - Collection 管理：添加/删除/重命名/浏览/更新
  - MCP Server 模式：支持 stdio 和 HTTP 两种传输方式
  - 当前已索引 Obsidian vault（45 个 Markdown 文件）

### Changed
- **README.md**：目录结构和 Skill 列表加入 qmd

## 1.3.2 — 2026-06-12

### Fixed
- **ai-repo-manager**：修正 Git 提交流程，在 commit 前增加 `git fetch` + `git pull --rebase` 步骤，防止因远程有新提交导致 push 被拒绝
- **README.md**：日常同步章节同步修正为先拉取再提交的流程

## 1.3.1 — 2026-06-12

### Added
- **ai-repo-manager skill**：Ai/ 仓库管理器（`skill/ai-repo-manager/`）
  - 六步强制流程：变更 → 更新 README.md → 更新 CHANGELOG.md → Git 提交 → 推送 → 确认同步
  - 强调 README.md 和 CHANGELOG.md 迭代为强制性步骤，不可跳过
  - 包含 CHANGELOG 格式参考（`references/changelog-format.md`）
  - 涵盖三种常见场景：新增 Skill、修改 Skill、仅文档更新

### Changed
- **README.md**：目录结构和 Skill 列表加入 ai-repo-manager

## 1.3.0 — 2026-06-12

### Added
- **mac-cleaner skill**：macOS 磁盘分析与垃圾清理（`skill/mac-cleaner/`）
  - 三段式工作流：扫描分析 → 生成建议 → 安全清理
  - 包含分析脚本 `scripts/analyze_mac_storage.sh` 和参考文档 `references/common-junk-locations.md`
  - 使用 osascript 废纸篓方式，安全可恢复

### Changed
- **纳入 GitHub 版本管理**：仓库已推送到 [github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)（main 分支）
- **README.md**：
  - 新增 GitHub 仓库链接和版本管理章节（含首次推送和日常同步命令）
  - 安装方式从 symlink 改为 `cp -r`（匹配实际规范，保持仓库与运行实例隔离）
  - 更新目录结构和 Skill 列表（加入 mac-cleaner）
  - 更新日期 2026-06-12

## 1.2.1 — 2026-06-10

### Changed
- **link-analysis/SKILL.md**：「六、保存到熊掌记」重写为决策树——纯文本 → Bear MCP，含图片 → bearcli（因 MCP 无 `add_attachment` 能力）
- **xueqiu-to-bear/SKILL.md**：「5. 存入熊掌记」同上重写，不再将 MCP 标为「推荐」而是按场景区分

## 1.2.0 — 2026-06-10

### Removed
- **xiongzhangji**：移除熊掌记 Skill（SKILL.md、create_note.py、bear.applescript 等）
  - 原因：Bear 2.x 内置 `bearcli mcp-server`，已通过 MCP 直连熊掌记，旧 Skill 不再需要
  - QoderWork 中的 xiongzhangji skill 配置已同步移除
  - 目录已移至废纸篓，如需恢复可在废纸篓中找到

### Changed
- **link-analysis/SKILL.md**：熊掌记写入方式从 `xiongzhangji/scripts/create_note.py` 改为 Bear MCP `create_note`
- **xueqiu-to-bear/SKILL.md**：前置依赖和熊掌记写入方式从 xiongzhangji 技能改为 Bear MCP Server
- **xueqiu-following-search/SKILL.md**：前置条件和熊掌记写入方式从 xiongzhangji skill 改为 Bear MCP Server
- **README.md**：移除 xiongzhangji 的目录结构和 Skill 说明

## 1.1.0 — 2026-06-09

### Added
- 新增 CONTRIBUTING.md：仓库协作规则，面向所有接入 Agent
- README.md 新增指向 CONTRIBUTING.md 的链接

## 1.0.0 — 2026-06-08

### Added
- 新增根目录 CHANGELOG.md（本文件）
- 新增根目录 .gitignore
- 为 link-analysis、xiongzhangji skill 新增 README.md 和 CHANGELOG.md
- 为 xueqiu/ 组新增 README.md 和 CHANGELOG.md

### Changed
- **重构根目录 README.md**：改为 Agent 无关的 skill 仓库手册，去除所有 WorkBuddy/QoderWork 专属引用
- 明确仓库定位：本地 skill 仓库，Agent 无关，版本管理，仅按需更新

### Fixed
- **link-analysis/SKILL.md**：去除 `#WorkBuddy` 标签和 WorkBuddy automation 引用
- **link-analysis/scripts/add_link.py**：去除硬编码 `~/.workbuddy/` 路径
- **xiongzhangji/SKILL.md**：去除硬编码 `~/.workbuddy/skills/` 路径
- **xueqiu-to-bear/SKILL.md**：去除 `#WorkBuddy` 标签
- **xueqiu-to-bear/scripts/fetch_xueqiu.py**：去除 `#QoderWork` 标签
- **xq-registry/SKILL.md**：去除 QoderWork 引用
