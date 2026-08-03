---
name: wechat-article
description: 提取微信公众号文章正文并转为 Markdown。当用户发送 mp.weixin.qq.com 链接，或提到"公众号文章"、"微信文章"、"提取公众号"、"抓取公众号"时使用。支持标题、作者、公众号名称、发布日期和正文的完整提取，可直接写入 Obsidian 粗制品目录。
version: 1.0.0
---

# 微信公众号文章提取

## 触发条件

- 用户发送的 URL 包含 `mp.weixin.qq.com`
- 用户提到"公众号文章"、"微信文章"、"提取公众号"等关键词

## 使用方式

运行提取脚本：

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/内容提取/wechat-article/scripts/wechat_extract.py "<URL>"
```

### 输出模式

脚本默认输出 JSON 到 stdout，包含以下字段：

```json
{
  "title": "文章标题",
  "author": "作者",
  "account": "公众号名称",
  "date": "YYYY年M月D日",
  "url": "原始链接",
  "markdown": "正文 Markdown 内容",
  "images": ["图片URL列表"]
}
```

加 `--markdown` 参数直接输出纯 Markdown（含 frontmatter），适合写入文件：

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/内容提取/wechat-article/scripts/wechat_extract.py "<URL>" --markdown
```

## 工作流

### 1. 提取文章

```bash
/opt/homebrew/bin/python3 ~/Ai/skill/内容提取/wechat-article/scripts/wechat_extract.py "<URL>" --markdown
```

### 2. 写入 Obsidian 粗制品

将输出保存到 Obsidian 粗制品目录（`工作区/粗制品/`，见 investment-framework 路径表 ROUGH_DIR），文件名不含日期前缀（日期通过 frontmatter 记录）：

```
工作区/粗制品/{标题}.md
```

frontmatter 格式：

```yaml
---
title: "文章标题"
source: "微信公众号"
author: "作者名"
account: "公众号名称"
date: "YYYY年M月D日"
url: "https://mp.weixin.qq.com/s/xxx"
recorded: "YYYY年M月D日"
type: "长文"
status: "待提炼"
---
```

### 3. 回复用户

写入后仅回复：`收到，纳入分析`

## 技术原理

微信公众号文章服务端渲染 HTML，但会对非微信客户端的 User-Agent 返回反爬页面。通过伪装微信内置浏览器 UA（MicroMessenger），可正常获取完整 HTML，再用 BeautifulSoup 从 `#js_content` div 提取正文。

## 注意事项

- 图片 URL 在 `data-src` 属性中，脚本会自动提取并列表，但默认不下载
- 如需用 `![](url)` 内联图片，加 `--with-images` 参数
- 部分文章可能因删除、封禁或权限限制返回错误，脚本会给出明确提示
- 微信反爬策略可能更新，若脚本失效需更新 UA 字符串

## 依赖

- Python 3.11+（路径：`/opt/homebrew/bin/python3`）
- requests
- beautifulsoup4
- lxml
