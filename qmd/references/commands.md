# QMD 命令参考

> 完整命令清单。主文件只保留路由与使用模式；具体命令参数在此查。

## 索引管理

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

## 搜索

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

## 文档获取

```bash
# 获取单篇文档（支持指定行范围和行数）
qmd get qmd://collection名/路径/文件.md
qmd get qmd://collection名/路径/文件.md:42       # 从第 42 行开始
qmd get qmd://collection名/路径/文件.md -l 20     # 最多 20 行

# 批量获取（glob 或逗号分隔）
qmd multi-get "qmd://obsidian/旧文件/**/*.md" -l 50
```

## MCP Server

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

## 工作流速查

**首次使用**：
```
qmd collection add /path/to/vault --name my-notes --mask "**/*.md"
qmd embed          # 生成向量嵌入
qmd query "测试查询"  # 验证搜索可用
```

**日常使用**：
```
qmd update         # 扫描新增/变更文件
qmd embed          # 增量更新向量（仅处理新文件，除非 -f 全量重建）
qmd query "要搜的内容"
```

**搜索 Obsidian 笔记**（collection 名是 `obsidian`）：
```bash
qmd search "个股研究" -c obsidian --full
qmd query "耀才证券的商业模式" -c obsidian -n 10
```

## 注意事项

- **搜索前必须 `qmd embed`**，否则 `query` 和 `vsearch` 不可用（`search` 不依赖 embedding）
- 模型首次运行会自动从 HuggingFace 下载（约 1-2GB），只下载一次
- `qmd get` 使用 `qmd://` 协议，获取文件用绝对路径或 qmd:// URI 均可
- `qmd --help` 查看完整命令列表
