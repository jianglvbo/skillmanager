---
name: ebook-download
description: 从互联网下载免费电子书（PDF/EPUB）。当用户需要查找和下载电子书、文档或出版物时使用。优先使用 GitHub 仓库、CDN 链接和其他免费直接来源。
description_zh: 从互联网下载免费电子书（PDF/EPUB）。当用户需要查找和下载电子书、文档或出版物时使用。优先使用 GitHub 仓库、CDN 链接和其他免费直接来源。
---

# 电子书下载

从互联网搜索并下载免费电子书（PDF/EPUB），优先使用可直接下载的免费来源。

## 来源优先级

按成功率从高到低排列：

### 1. GitHub 仓库（首选）

GitHub 上有大量中文电子书仓库，是最可靠的免费来源。

**搜索策略：**
- 使用 WebSearch 搜索：`github.com {书名} pdf` 或 `github.com {书名} epub`
- 常见电子书仓库：
  - `codeman008/Financial_freedom` - 投资理财类
  - `0voice/expert_readed_books` - 创业/经济/技术类
  - `liuhengheng/book_money` - 投资类
  - `fenwii/WarrenBuffettLetter` - 巴菲特相关
  - `KnowNo/books-7` - 经济学类

**下载 URL 格式：**
```
https://github.com/{user}/{repo}/raw/{branch}/{url-encoded-filename}
```

**关键技巧：**
- **必须先浏览仓库内容**：用 WebFetch 访问仓库页面，获取准确的文件名和路径
- **不要猜测文件名**：中文标点符号容易出错（如 `·` vs `•`，`《》` vs `〈〉`）
- **URL 编码**：中文文件名需要正确 URL 编码
- **分支名称**：可能是 `main` 或 `master`，需要确认

**curl 命令：**
```bash
curl -L -o "output.pdf" "https://github.com/{user}/{repo}/raw/{branch}/{encoded-filename}" \
  -s --connect-timeout 30 --max-time 300 \
  -w "status: %{http_code} size: %{size_download}bytes\n"
```

### 2. 平台 CDN 直链

某些平台的文档/附件 CDN 可以直接下载：

**雪球文档（xqdoc.imedao.com）：**
```bash
curl -L -o "output.pdf" "http://xqdoc.imedao.com/{doc-id}.pdf"
```
- 雪球用户分享的 PDF 文档常托管在此 CDN
- 无需认证，直接下载

**学术/机构网站（.edu 域名）：**
```bash
curl -L -o "output.pdf" "https://{university}.edu/path/to/file.pdf" \
  -s --connect-timeout 30 --max-time 120
```
- 学术论文、会议资料有时可公开访问
- 成功率取决于具体链接

### 3. 在线书城（仅在线阅读）

无法直接下载 PDF，但可免费在线阅读：

**微信读书（weread.qq.com）：**
- 大量中文书籍免费在线阅读
- 无法用 curl 下载，需要浏览器访问
- 适合作为"找不到下载"时的备选方案

**得到 App（dedao.cn）：**
- 部分电子书需付费
- 付费书籍无法免费下载

## 核心工作流

### 第1步：搜索电子书

对每本书，按以下顺序搜索：

1. **WebSearch**：`{书名} {作者} github pdf`
2. **WebSearch**：`{书名} {作者} pdf 下载`
3. **WebSearch**：`{书名英文} pdf free download`（英文书或中文翻译）
4. **WebSearch**：`{书名} epub 下载`

### 第2步：验证来源

找到候选链接后：

1. **GitHub 仓库**：用 WebFetch 浏览仓库，确认文件存在且路径正确
2. **直链**：先用 curl HEAD 请求检查：
   ```bash
   curl -I -L "URL" --connect-timeout 10 --max-time 15
   ```
   检查 HTTP 状态码和 Content-Length
3. **网盘链接**（ctfile、百度网盘等）：通常需要浏览器交互，标记为"需手动下载"

### 第3步：下载

```bash
# 创建输出目录
mkdir -p "/path/to/output"

# 单文件下载
curl -L -o "output.pdf" "URL" \
  -s --connect-timeout 30 --max-time 300 \
  -w "%{http_code} %{size_download}bytes\n"

# 并行下载多本书（同一来源）
curl -L -o "book1.pdf" "URL1" -s --connect-timeout 30 --max-time 300 &
curl -L -o "book2.pdf" "URL2" -s --connect-timeout 30 --max-time 300 &
wait
echo "All downloads complete"
```

### 第4步：验证下载

```bash
# 检查文件类型
file downloaded.pdf

# 期望输出：PDF document 或 EPUB document
# 如果是 HTML document，说明下载失败（404 页面或被重定向到网页）

# 检查文件大小
ls -lh downloaded.pdf

# 合理范围：
# - PDF 书籍：通常 > 500KB，常见 2MB-30MB
# - EPUB 书籍：通常 > 100KB，常见 300KB-5MB
# - 小于 50KB 的文件通常是错误页面，不是真正的电子书
```

### 第5步：清理与报告

- 删除无效文件（HTML 页面、过小的文件）
- 向用户汇报：
  - 成功下载的书籍列表（含文件大小）
  - 未找到的书籍列表（附建议的付费/手动下载渠道）

## 文件命名规范

```
{序号}-{书名}-{作者}.{扩展名}
```

示例：
- `01-证券分析-格雷厄姆.pdf`
- `04-聪明的投资者-格雷厄姆.pdf`
- `11-基业长青-吉姆柯林斯.epub`

## 常见陷阱

### 1. 文件名编码问题
**问题**：猜测的中文文件名 404  
**原因**：中文标点符号变体（`·` vs `•`）、全角/半角括号、特殊字符  
**解决**：先用 WebFetch 浏览目录，获取精确文件名

### 2. dokumen.pub 连接失败
**问题**：curl 返回 status 000（连接被拒）  
**原因**：该站点可能屏蔽自动化请求或已下线  
**解决**：跳过此来源，尝试其他渠道

### 3. 网盘需要浏览器交互
**问题**：ctfile、百度网盘等链接无法用 curl 下载  
**原因**：需要 JavaScript 执行或验证码  
**解决**：标记为"需手动下载"，提供链接和提取码

### 4. 付费内容无法免费下载
**问题**：得到 App、豆瓣阅读等平台的付费书籍  
**解决**：如实告知用户，建议通过正规渠道购买

### 5. 文件实际内容与标题不符
**问题**：下载的 PDF 实际是另一本书  
**原因**：仓库中文件名标注错误  
**解决**：下载后用 `file` 命令验证，必要时检查 PDF 元数据

## 输出模板

向用户汇报时使用以下格式：

```markdown
## 下载结果

### 成功下载（N本）
1. 《书名》作者 — 文件大小 PDF/EPUB
2. ...

### 未找到免费电子版（N本）
1. 《书名》— 建议渠道：微信读书/得到 App/购买纸质书
2. ...

### 文件保存位置
/path/to/output/
```

## 注意事项

- 大文件（> 50MB）下载时设置更长的 `--max-time`（如 600 秒）
- 并行下载时注意带宽，建议同时不超过 3 个
- 优先下载中文版，除非用户明确要求英文版
- 英文原版通常比中文翻译版更容易找到免费资源
- 对于绝版或小众书籍，资源可能极为稀缺，如实告知用户
