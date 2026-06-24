---
name: qmd
description: QMD 本地文档索引与搜索工具。对本地 Markdown/文本文件建立全文索引、向量嵌入和语义搜索。支持 collection 管理、BM25 关键词搜索、向量语义搜索、混合查询（LLM 重排序）以及 MCP Server 模式。触发词：「搜索我的文档」「用qmd」「qmd search」「qmd query」「索引文档」「文档搜索」「语义搜索本地文件」。
agent_created: true
---

# QMD — 本地文档索引与搜索

`qmd` 是一个本地命令行文档搜索引擎，对指定目录下的文件建立全文索引和向量嵌入，支持三种搜索模式。

**核心能力**：全文检索（BM25） → 向量语义搜索 → 混合查询 + LLM 重排序。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 在本地文档/笔记中搜索内容
- 语义搜索 Obsidian 或其他 Markdown 仓库
- 管理文档索引（添加/更新/删除 collection）
- 查看索引状态
- 启动 qmd MCP Server

**Agent 自动化触发**：当对话中需要查找用户的 Obsidian 笔记或本地文档时，Agent 应主动使用本 Skill 进行搜索，无需等待用户明确提及「qmd」。

## 工作模式（路由表）

| 用户意图 | 对应命令 | 说明 |
|---------|---------|------|
| "搜索 XX"、"找一下 XX" | `qmd query` | 混合搜索+重排序（推荐，需先 embed） |
| "搜关键词 XX"、"精确搜" | `qmd search` | BM25 全文检索，不依赖 embedding |
| "语义搜索 XX"、"意思相近的" | `qmd vsearch` | 纯向量相似度搜索 |
| "看看索引状态" | `qmd status` | 查看索引统计 |
| "更新索引"、"同步文档" | `qmd update` | 重新扫描文件 |
| "跑 embedding"、"生成向量" | `qmd embed` | 生成向量嵌入 |

## 核心命令

### 索引管理

```bash
# 查看状态
qmd status

# 添加 collection（对目录建索引）
qmd collection add /path/to/dir --name <名称> --mask "**/*.md"

# 列出所有 collection
qmd collection list

# 重命名
qmd collection rename <旧名> <新名>

# 删除
qmd collection remove <名称>

# 浏览 collection 中的文件
qmd ls <collection名>

# 更新索引（--pull 会先 git pull）
qmd update [--pull]

# 生成向量嵌入（搜索前必须执行）
qmd embed [-f]

# 清理缓存和孤儿数据
qmd cleanup
```

### 搜索

```bash
# 推荐：混合搜索 + LLM 重排序（需先 qmd embed）
qmd query "查询内容" [-n 10] [-c collection名] [--full] [--json]

# BM25 全文关键词搜索
qmd search "关键词" [-n 10] [-c collection名] [--full]

# 向量相似度搜索
qmd vsearch "语义查询" [-n 10]
```

**搜索选项**：
- `-n <N>`：返回 N 条结果（默认 5，`--files` 模式默认 20）
- `-c <名称>`：限定搜索范围到指定 collection
- `--full`：输出完整文档而非片段
- `--line-numbers`：显示行号
- `--json` / `--csv` / `--md` / `--xml`：指定输出格式
- `--min-score <0-1>`：最低相似度阈值
- `--all`：返回所有匹配项

### 文档获取

```bash
# 获取单篇文档（支持指定行范围和行数）
qmd get qmd://collection名/路径/文件.md
qmd get qmd://collection名/路径/文件.md:42       # 从第 42 行开始
qmd get qmd://collection名/路径/文件.md -l 20     # 最多 20 行

# 批量获取（glob 或逗号分隔）
qmd multi-get "qmd://obsidian/旧文件/**/*.md" -l 50
```

### MCP Server

```bash
# stdio 模式
qmd mcp

# HTTP 模式（前台）
qmd mcp --http [--port 8181]

# 后台守护进程
qmd mcp --http --daemon

# 停止后台
qmd mcp stop
```

## Agent 使用模式

Agent 在对话中检索用户的 Obsidian/本地文档时，遵循以下流程：

### 模式一：关键词快速定位

当用户提到某个具体主题、股票、公司名时：

```bash
# 先用 search 找相关文件（不依赖 embedding，立即可用）
qmd search "关键词" -c obsidian --json -n 10

# 拿到文件列表后，用 qmd get 读取内容
qmd get qmd://obsidian/旧文件/个股研究/xxx.md
```

### 模式二：语义理解搜索

当用户描述概念、场景而非精确关键词时：

```bash
# 需先 embed
qmd query "语义查询" -c obsidian -n 10 --json
```

### 模式三：URI → 真实路径转换

qmd 搜索返回的是 `qmd://` 前缀的 URI，读/写文件需转换为真实路径：

```
qmd://obsidian/旧文件/个股研究/耀才证券.md
→ /Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/旧文件/个股研究/耀才证券.md
```

转换方式：`qmd get` 直接输出内容，或用 shell 拼接真实路径。

### 模式四：检查索引是否最新

```bash
# 查看状态确认文件是否已索引
qmd status

# 如有新文件未索引
qmd update && qmd embed
```

## 当前状态

### Obsidian Vault

| 项目 | 值 |
|------|-----|
| **Vault 路径** | `/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents` |
| **qmd Collection 名** | `obsidian` |
| **URI 前缀** | `qmd://obsidian/` |
| **文件数** | 45（`**/*.md`） |

> **路径映射**：`qmd://obsidian/旧文件/xxx.md` ↔ `/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/旧文件/xxx.md`
>
> 搜索用 qmd URI，读/写文件用真实路径。

### 系统信息

| 项目 | 值 |
|------|-----|
| **索引位置** | `~/.cache/qmd/index.sqlite` |
| **已建 collection** | `obsidian`（`**/*.md`，45 文件） |
| **嵌入状态** | 待执行（`qmd embed`） |
| **模型** | embeddinggemma-300M / qwen3-reranker-0.6b / Qwen3-0.6B |

## 工作流

### 首次使用

```
qmd collection add /path/to/vault --name my-notes --mask "**/*.md"
qmd embed          # 生成向量嵌入
qmd query "测试查询"  # 验证搜索可用
```

### 日常使用

```
qmd update         # 扫描新增/变更文件
qmd embed          # 增量更新向量（仅处理新文件，除非 -f 全量重建）
qmd query "要搜的内容"
```

### 搜索 Obsidian 笔记

```bash
# 当前 collection 名是 obsidian
qmd search "个股研究" -c obsidian --full
qmd query "耀才证券的商业模式" -c obsidian -n 10
```

## 注意事项

- **搜索前必须 `qmd embed`**，否则 `query` 和 `vsearch` 不可用（`search` 不依赖 embedding）
- 模型首次运行会自动从 HuggingFace 下载（约 1-2GB），只下载一次
- `qmd get` 使用 `qmd://` 协议，获取文件用绝对路径或 qmd:// URI 均可
- `qmd --help` 查看完整命令列表
