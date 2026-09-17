#!/usr/bin/env python3
"""
微信公众号文章提取器
用法：
  python3 wechat_extract.py <URL> [--markdown] [--with-images]
"""

import sys
import re
import json
import argparse
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("错误：缺少依赖，请运行 pip3 install requests beautifulsoup4 lxml", file=sys.stderr)
    sys.exit(1)

# 微信内置浏览器 UA（如失效需更新版本号）
WECHAT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.49(0x18003137) NetType/WIFI Language/zh_CN"
)

HEADERS = {
    "User-Agent": WECHAT_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://mp.weixin.qq.com/",
}


def fetch_html(url: str) -> str:
    """获取文章 HTML"""
    resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


def extract_meta(soup: BeautifulSoup) -> dict:
    """提取文章元数据"""
    meta = {}

    # 标题
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["title"] = og_title["content"].strip()
    else:
        h1 = soup.find("h1", class_="rich_media_title") or soup.find("h1")
        meta["title"] = h1.get_text(strip=True) if h1 else "未命名文章"

    # 作者
    og_author = soup.find("meta", property="og:article:author") or soup.find("meta", {"name": "author"})
    meta["author"] = og_author["content"].strip() if og_author and og_author.get("content") else ""

    # 公众号名称
    profile_el = soup.find("a", id="js_name") or soup.find("span", class_="profile_nickname")
    meta["account"] = profile_el.get_text(strip=True) if profile_el else ""
    if not meta["account"]:
        og_account = soup.find("meta", {"property": "og:article:author"})
        if og_account:
            meta["account"] = og_account.get("content", "").strip()

    # 发布日期 — 从 script 中的 ct (create_time) unix 时间戳提取
    scripts = soup.find_all("script")
    date_str = ""
    for script in scripts:
        text = script.string or ""
        # ct = "timestamp"
        m = re.search(r'ct\s*=\s*"(\d+)"', text)
        if m:
            ts = int(m.group(1))
            dt = datetime.fromtimestamp(ts)
            date_str = f"{dt.year}年{dt.month}月{dt.day}日"
            break
        # createTime = 'timestamp'
        m = re.search(r'createTime\s*=\s*[\'"](\d+)[\'"]', text)
        if m:
            ts = int(m.group(1))
            dt = datetime.fromtimestamp(ts)
            date_str = f"{dt.year}年{dt.month}月{dt.day}日"
            break
    meta["date"] = date_str

    # 摘要
    og_desc = soup.find("meta", property="og:description")
    meta["description"] = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""

    return meta


def html_to_markdown(content_div) -> tuple[str, list[str]]:
    """将 #js_content 转为 Markdown，返回 (markdown_text, image_urls)"""
    image_urls = []
    lines = []

    def process_node(node, indent=0):
        if isinstance(node, NavigableString):
            text = str(node)
            # 清理多余空白但保留换行
            text = re.sub(r'[^\S\n]+', ' ', text)
            if text.strip():
                lines.append(text.strip())
            return

        if not hasattr(node, 'name'):
            return

        tag = node.name

        # 跳过 style/script
        if tag in ('style', 'script'):
            return

        # 图片处理
        if tag == 'img':
            src = node.get('data-src') or node.get('src', '')
            if src and 'mmbiz.qpic.cn' in src:
                image_urls.append(src)
                alt = node.get('alt', '')
                lines.append(f"![{alt}]({src})")
            return

        # 标题
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            text = node.get_text(strip=True)
            if text:
                lines.append("")
                lines.append(f"{'#' * level} {text}")
                lines.append("")
            return

        # 段落
        if tag == 'p':
            text = node.get_text(strip=True)
            if text:
                lines.append(text)
            else:
                lines.append("")
            # 处理段落内图片
            for img in node.find_all('img'):
                src = img.get('data-src') or img.get('src', '')
                if src and 'mmbiz.qpic.cn' in src:
                    if src not in image_urls:
                        image_urls.append(src)
                        alt = img.get('alt', '')
                        lines.append(f"![{alt}]({src})")
            return

        # 加粗/斜体
        if tag in ('strong', 'b'):
            text = node.get_text(strip=True)
            if text:
                lines.append(f"**{text}**")
            return
        if tag in ('em', 'i'):
            text = node.get_text(strip=True)
            if text:
                lines.append(f"*{text}*")
            return

        # 列表
        if tag == 'li':
            text = node.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
            return
        if tag in ('ul', 'ol'):
            lines.append("")
            for child in node.children:
                process_node(child, indent + 1)
            lines.append("")
            return

        # blockquote
        if tag == 'blockquote':
            text = node.get_text(strip=True)
            if text:
                for line in text.split('\n'):
                    if line.strip():
                        lines.append(f"> {line.strip()}")
                lines.append("")
            return

        # br
        if tag == 'br':
            lines.append("")
            return

        # section/div 等容器 — 递归处理子节点
        for child in node.children:
            process_node(child, indent)

    process_node(content_div)

    # 清理多余空行
    result = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        result.append(line)
        prev_empty = is_empty

    return "\n".join(result).strip(), image_urls


def extract_article(url: str) -> dict:
    """提取文章完整数据"""
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    # 检查错误页面
    error = soup.find("div", class_="weui-msg__title") or soup.find("p", class_="weui-warn-msg__title")
    if error:
        return {"error": error.get_text(strip=True)}

    # 检查正文 div
    content_div = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
    if not content_div:
        # 可能是视频文章或其他类型
        video_desc = soup.find("div", class_="video_area")
        if video_desc:
            return {"error": "该文章为视频类型，暂不支持提取"}
        return {"error": "未找到文章正文，可能已被删除或需要登录"}

    meta = extract_meta(soup)
    markdown, images = html_to_markdown(content_div)

    return {
        "title": meta["title"],
        "author": meta["author"],
        "account": meta["account"],
        "date": meta["date"],
        "url": url,
        "description": meta["description"],
        "markdown": markdown,
        "images": images,
    }


def _slug_date(raw: str) -> str:
    """把抓到的日期规整成裸 yyyy-MM-dd（2026-09-12：SKILL.md 明令禁止中文年月日与引号）。

    源站日期形态多样（2026-09-12 / 2026年9月12日 / 09月12日 / 空），判不出就留空。
    """
    t = str(raw or "").strip()
    if not t:
        return ""
    m = re.search(r"(20\d{2})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})", t)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    m = re.search(r"^(\d{1,2})\D{1,3}(\d{1,2})$", t)          # 缺年份 → 用当年
    if m:
        return "%d-%02d-%02d" % (datetime.now().year, int(m.group(1)), int(m.group(2)))
    return ""


def format_markdown(article: dict, inline_images: bool = False) -> str:
    """输出带 frontmatter 的 Markdown（字段规范见 SKILL.md 第二步）"""
    recorded = datetime.now().strftime("%Y-%m-%d")
    title = str(article.get("title", "")).strip()
    url = str(article.get("url", "")).strip()
    date = _slug_date(article.get("date", ""))
    # source 必须是**真实原文链接**的 markdown（禁止"微信公众号"这类渠道名占位）
    source = "[%s](%s)" % (title or "原文", url) if url else ""

    fm = [
        "---",
        f'title: "{title}"',
        f'source: "{source}"',
        f'author: "{article.get("author", "")}"',
        f'account: "{article.get("account", "")}"',
        f'date: {date}' if date else 'date: ',
        f'url: {url}',
        f'recorded: {recorded}',
        'type: "长文"',
        'status: "待提炼"',
        "tags: []",
        "---",
        "",
    ]

    md = article["markdown"]
    if not inline_images and article.get("images"):
        md += "\n\n---\n\n## 文章图片\n\n"
        for i, img_url in enumerate(article["images"], 1):
            md += f"- [图片{i}]({img_url})\n"

    return "\n".join(fm) + md


def main():
    parser = argparse.ArgumentParser(description="微信公众号文章提取器")
    parser.add_argument("url", help="文章链接")
    parser.add_argument("--markdown", action="store_true", help="输出 Markdown 格式（含 frontmatter）")
    parser.add_argument("--with-images", action="store_true", help="在正文中内联图片")
    args = parser.parse_args()

    try:
        article = extract_article(args.url)
    except requests.exceptions.RequestException as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)

    if "error" in article:
        print(f"提取失败：{article['error']}", file=sys.stderr)
        sys.exit(1)

    if args.markdown:
        print(format_markdown(article, inline_images=args.with_images))
    else:
        print(json.dumps(article, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
