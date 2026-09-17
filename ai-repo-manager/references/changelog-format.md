# CHANGELOG.md 格式规范

## 版本号规则

- 格式：`MAJOR.MINOR.PATCH`
- **MAJOR**：仓库结构重大变更（如大量 skill 重组、规范变更）
- **MINOR**：新增 skill、新增章节、功能级变更
- **PATCH**：修正、文档更新、小改

## 条目格式

```markdown
## X.Y.Z — YYYY-MM-DD

### Added
- 新增内容的描述

### Changed
- 修改内容的描述

### Fixed
- 修复内容的描述

### Removed
- 移除内容的描述
```

## 原则

- 每次推送到 GitHub 的变更都应在 CHANGELOG 中记录
- 条目简洁明了，一句话说清变更
- 新增 Skill 标注路径
- 版本号按变更性质升级，不跳过
