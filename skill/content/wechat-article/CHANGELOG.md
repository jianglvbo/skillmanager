# Changelog — wechat-article

## 1.0.0 — 2026-06-17

### Added
- 初始版本：微信公众号文章提取 Skill
- `scripts/wechat_extract.py`：支持 JSON 和 Markdown 两种输出模式
- 通过模拟微信客户端 UA（MicroMessenger）绕过反爬
- 提取标题、作者、公众号名称、发布日期（ct 时间戳解析）、摘要
- 正文 HTML→Markdown 转换，支持标题/段落/列表/引用/加粗/斜体
- 图片 URL 提取（data-src），支持 `--with-images` 内联模式
- 错误处理：文章删除/权限限制/视频类型等场景的明确提示
