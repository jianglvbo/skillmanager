# qmd — 本地文档索引与搜索 Skill

基于 `qmd` CLI 的本地文档搜索工具，支持全文检索、向量语义搜索和混合查询。

## 依赖

- [qmd](https://github.com/qmd/qmd) CLI（v0.9.0+）
- 首次运行会自动下载嵌入/重排序/生成模型（~1-2GB，HuggingFace）

## 安装

```bash
# 安装到当前 Agent
cp -r ~/.skills-manager/skills/qmd ~/.workbuddy/skills/qmd
```

## 使用

在对话中触发关键词即可：
- "搜索我的文档 xxx"
- "qmd search 关键词"
- "语义搜索本地文件"
