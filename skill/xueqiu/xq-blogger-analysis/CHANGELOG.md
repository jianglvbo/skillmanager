# Changelog — xq-blogger-analysis

## 2.2.0 (2026-06-22)

- **Skill 重命名**：`xq-registry` → `xq-blogger-analysis`，更准确反映"博主画像分析"的定位
- **Skill 解耦**：移除对其他 skill 的显式引用

## 2.1.0 (2026-06-22)

- **仪表盘上移**：仪表盘从博主分析框架内上移至 vault 根目录 `仪表盘/`
- **目录精简**：博主分析框架只保留 `原始资源仓库/`、`博主画像/`、`索引/`
- **博主画像 frontmatter 统一**：全部 45 个画像文件补全 `category`/`content_type`/`time_sensitivity`/`tags`/`sources`/`queried` 字段
- **tags 自动生成**：从 `markets` 字段自动生成 `类型/博主画像` + `市场/XXX` 标签
- **查询配方改进**：Dataview 查询改用 `contains(markets, ...)` 过滤，不再依赖 tags

## 2.0.0 (2026-06-21)

- **架构重构**：从"中控管理 40+ 独立 skill"重构为"框架级操作手册"
- **数据化转型**：40+ xq-{name}/SKILL.md 不再作为 skill，转为 vault 博主画像 .md 文件
- **流水线定义**：新增完整流水线（粗制品 → 粗加工 → 原始资源仓库 → 提炼 → 博主画像）
- **博主画像模板**：新增完整模板（身份卡/擅长与局限/核心投资模型/决策启发式/表达DNA/准确率追踪等）
- **三维分类**：博主画像支持 category + content_type + time_sensitivity 分类
- **路由层重构**：路由层改为读取 vault 博主画像文件，不再加载独立 skill
- **registry.json**：保留作运营索引，复制至 vault 博主分析框架/索引/
- **设计原则**：明确 skill 只定义做什么/怎么做，不包含调度策略

## 1.0.0 (2026-06-13)

- 初版：雪球博主注册表中控，管理 40+ 独立博主 skill
