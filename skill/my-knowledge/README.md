# my-knowledge — 投资知识框架

个人投资知识体系的 AI 技能组，覆盖从链接收集到知识沉淀的完整流水线。

## 架构

```
用户链接/内容
    ↓
link-analysis（链接收集 + 存入粗制品）
    ↓
粗制品/（按 _route 分流）
    ├──→ investment-knowledge-framework（投资知识加工）
    │    粗加工 → 原始资源 → 提炼 → 维基仓库 → 问答 → 回流
    └──→ xq-blogger-analysis（博主画像加工）
         粗加工 → 原始资源 → 提炼 → 博主画像 → 问答 → 回流
```

**共享层**：`knowledge-pipeline` — 目录约定和 frontmatter 通信协议

## 技能列表

| Skill | 角色 | 管辖目录 |
|-------|------|----------|
| `knowledge-pipeline` | 全局约定：目录 + 数据流 | vault 全局 |
| `link-analysis` | 入口：链接收集与存储 | `粗制品/` |
| `investment-knowledge-framework` | 投资知识加工流水线 | `投资分析框架/` |
| `xq-blogger-analysis` | 博主画像加工流水线 | `博主分析框架/` |

## 模块化原则

- 各 skill 互不知晓对方存在
- 交接只通过目录和 frontmatter 字段
- 常变数据存 Obsidian vault，不硬编码在 skill 中

## 安装

```bash
# 从仓库复制到 Agent 本地 skills 目录
cp -r ~/Ai/skill/my-knowledge/{skill-name} ~/.workbuddy/skills/
```

## Obsidian Vault

路径：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的知识库/`
