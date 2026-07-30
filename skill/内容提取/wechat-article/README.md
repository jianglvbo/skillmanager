# wechat-article

### 微信公众号文章提取

从微信公众号链接提取文章正文，转为带 frontmatter 的 Markdown，可直接写入 Obsidian 投资分析框架粗制品目录。

## 它能做什么

- **正文提取**：通过模拟微信客户端 UA 绕过反爬，提取 `#js_content` 正文
- **元数据提取**：标题、作者、公众号名称、发布日期、摘要
- **图片处理**：提取文章中所有图片 URL，支持内联或列表两种输出
- **Markdown 输出**：带 Obsidian frontmatter（title/source/author/date/status）

## 安装

```bash
cp -r ~/Ai/skill/内容提取/wechat-article ~/.qoderwork/skills/wechat-article
```

## 依赖

- Python 3.11+（`/opt/homebrew/bin/python3`）
- requests、beautifulsoup4、lxml

```bash
/opt/homebrew/bin/pip3 install requests beautifulsoup4 lxml
```

## 使用

### JSON 模式

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/wechat-article/scripts/wechat_extract.py "https://mp.weixin.qq.com/s/xxx"
```

### Markdown 模式（写入 Obsidian）

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/wechat-article/scripts/wechat_extract.py "https://mp.weixin.qq.com/s/xxx" --markdown
```

### 内联图片

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/wechat-article/scripts/wechat_extract.py "https://mp.weixin.qq.com/s/xxx" --markdown --with-images
```

## 目录结构

```text
wechat-article/
├── SKILL.md          ← Agent 加载入口
├── README.md         ← 本文件
├── CHANGELOG.md      ← 版本记录
└── scripts/
    └── wechat_extract.py  ← 提取脚本
```

## License

MIT
