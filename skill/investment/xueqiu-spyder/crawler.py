import time
import re
import sys
import logging
import subprocess
import os
import urllib.parse
from playwright.sync_api import sync_playwright

import config

logger = logging.getLogger(__name__)


def _default_chrome_path():
    """跨平台返回 Chrome/Chromium 可执行文件路径"""
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if sys.platform.startswith("win"):
        return os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    for candidate in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if os.path.exists(candidate):
            return candidate
    return "google-chrome"


CHROME_PATH = os.environ.get("XUEQIU_CHROME_PATH") or _default_chrome_path()
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".chrome-debug-profile")
# 可用环境变量 XUEQIU_DEBUG_PORT 覆盖，避免与既有 9222 调试实例冲突
DEBUG_PORT = int(os.environ.get("XUEQIU_DEBUG_PORT", "9222"))


class CrawlerError(Exception):
    pass


class XueqiuCrawler:
    """通过连接本地 Chrome 调试端口来复用真实浏览器环境，绕过 WAF"""

    def __init__(self):
        self._pw = None
        self._browser = None
        self._page = None
        # timeline 端点状态：v4 被 WAF 405 时自动降级到旧版路径（2026-09-09 固化）
        self._timeline_url = config.USER_TIMELINE_URL
        self._timeline_count = config.USER_POSTS_COUNT
        self._degraded = False
        self._connect_chrome()

    def _degrade_timeline(self):
        """v4 timeline 端点被 WAF 拦截时，自动切到旧版路径并下调每页条数

        2026-09-09 实测：v4/statuses/user_timeline.json 会被阿里云 WAF 对该 IP
        临时封禁（405，页面自身带签名请求亦 405），而旧版 /statuses/user_timeline.json
        仍可用且数据结构一致。降级只做一次，避免无限重试。
        """
        if self._degraded:
            return False
        self._timeline_url = config.USER_TIMELINE_URL_FALLBACK
        self._timeline_count = config.FALLBACK_POSTS_COUNT
        self._degraded = True
        logger.warning(
            "timeline 端点失败，自动降级到旧版路径重试: %s (count=%d)",
            self._timeline_url, self._timeline_count,
        )
        return True

    def _connect_chrome(self):
        """启动带调试端口的 Chrome 并连接"""
        # 先尝试连接已有的调试端口
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.connect_over_cdp(
                f"http://127.0.0.1:{DEBUG_PORT}"
            )
            logger.info("已连接到运行中的 Chrome")
        except Exception:
            logger.info("未检测到调试端口，正在启动 Chrome...")
            self._launch_chrome()
            time.sleep(3)
            self._browser = self._pw.chromium.connect_over_cdp(
                f"http://127.0.0.1:{DEBUG_PORT}"
            )
            logger.info("Chrome 启动并连接成功")

        # 获取或创建页面
        contexts = self._browser.contexts
        if contexts and contexts[0].pages:
            self._page = contexts[0].pages[0]
        else:
            self._page = self._browser.contexts[0].new_page()

        # 确保在雪球域名下
        if "xueqiu.com" not in self._page.url:
            self._page.goto(config.XUEQIU_HOME, wait_until="domcontentloaded", timeout=15000)

    def _launch_chrome(self):
        """以调试模式启动 Chrome"""
        cmd = [
            CHROME_PATH,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={USER_DATA_DIR}",
            "--no-first-run",
            "https://xueqiu.com/",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _fetch_json(self, url, params=None):
        """在浏览器内 fetch API，返回 JSON；检测 WAF/滑块验证页"""
        query = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        full_url = f"{url}?{query}" if query else url

        for attempt in range(config.MAX_RETRIES):
            time.sleep(config.REQUEST_DELAY)
            try:
                result = self._page.evaluate(
                    """async (url) => {
                        try {
                            const resp = await fetch(url);
                            const ct = resp.headers.get('content-type') || '';
                            if (!ct.includes('json')) {
                                const snippet = (await resp.text()).slice(0, 300);
                                return {ok: false, error: 'not json', snippet: snippet};
                            }
                            return {ok: true, data: await resp.json()};
                        } catch(e) {
                            return {ok: false, error: e.message};
                        }
                    }""",
                    full_url,
                )

                if result.get("ok"):
                    return result["data"]

                # WAF / 滑块 / 安全验证检测（雪球阿里云防护特征）
                snippet = (result.get("snippet") or "") + (result.get("error") or "")
                if re.search(r"滑动|安全验证|captcha|无感验证|请完成验证|访问验证", snippet, re.I):
                    raise CrawlerError(
                        f"疑似触发 WAF/滑块验证 ({full_url}) —— 停止采集，等待数分钟或人工在浏览器完成验证后重试"
                    )
                logger.warning(f"API 请求失败: {result.get('error')} (attempt {attempt + 1})")
            except CrawlerError:
                raise
            except Exception as e:
                if attempt == config.MAX_RETRIES - 1:
                    raise CrawlerError(f"请求失败 ({full_url}): {e}")
                time.sleep(2 ** attempt)

        raise CrawlerError(f"超过最大重试次数: {full_url}")

    def get_stock_posts(self, symbol, sort="reply", page=1, count=None):
        """获取某只股票的讨论帖"""
        if count is None:
            count = config.POSTS_PER_PAGE
        params = {
            "symbol": symbol,
            "sort": sort,
            "source": "all",
            "count": count,
            "page": page,
        }
        data = self._fetch_json(config.SEARCH_STATUS_URL, params)
        return data.get("list", [])

    def get_user_posts(self, user_id, page=1, count=None):
        """获取用户的动态帖子"""
        if count is None:
            count = config.USER_POSTS_COUNT
        params = {
            "user_id": user_id,
            "page": page,
            "count": count,
        }
        data = self._fetch_json(config.USER_TIMELINE_URL, params)
        if data.get("error_code"):
            logger.warning(f"用户 {user_id} API 错误: {data.get('error_description', data.get('error_code'))}")
            return []
        statuses = data.get("statuses", [])
        return statuses if statuses else data.get("list", [])

    def get_user_all_posts(self, user_id, max_pages=10):
        """通过导航到用户主页来获取其帖子（绕过登录限制）"""
        user_page = self._browser.contexts[0].new_page()
        all_statuses = []
        try:
            user_page.goto(
                f"https://xueqiu.com/u/{user_id}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            try:
                user_page.wait_for_selector(".user-name", timeout=5000)
            except Exception:
                user_page.wait_for_timeout(1000)

            for page_num in range(1, max_pages + 1):
                time.sleep(config.REQUEST_DELAY)
                result = user_page.evaluate(
                    """async (args) => {
                        try {
                            const resp = await fetch(
                                `${args.url}?user_id=${args.uid}&page=${args.page}&count=${args.count}`
                            );
                            const ct = resp.headers.get('content-type') || '';
                            if (!ct.includes('json')) return {ok: false, error: 'not json'};
                            const data = await resp.json();
                            if (data.error_code) return {ok: false, error: data.error_description};
                            return {ok: true, statuses: data.statuses || [], count: data.count};
                        } catch(e) { return {ok: false, error: e.message}; }
                    }""",
                    {"uid": user_id, "page": page_num,
                     "url": self._timeline_url, "count": self._timeline_count},
                )
                if not result.get("ok"):
                    # 首次失败 → 尝试自动降级端点后重试本页（只降级一次）
                    if self._degrade_timeline():
                        continue
                    logger.warning(f"用户 {user_id} 第 {page_num} 页失败: {result.get('error')}")
                    break
                statuses = result.get("statuses", [])
                if not statuses:
                    break
                all_statuses.extend(statuses)
                logger.info(f"  第 {page_num} 页获取 {len(statuses)} 条 (共 {len(all_statuses)})")
        finally:
            user_page.close()
        return all_statuses

    def get_post_full_text(self, target):
        """访问帖子详情页获取完整内容 + 精确发布时间（优先 article:published_time，次选页面文本）
        返回 (full_text, published_ms or None)；target 如 /5243796549/376934652"""
        detail_page = self._browser.contexts[0].new_page()
        try:
            detail_page.goto(
                f"https://xueqiu.com{target}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            try:
                detail_page.wait_for_selector(".article__bd__detail", timeout=5000)
            except Exception:
                pass
            result = detail_page.evaluate("""() => {
                const el = document.querySelector('.article__bd__detail');
                const text = el ? el.textContent.trim() : '';
                let published = '';
                const meta = document.querySelector('meta[property="article:published_time"]');
                if (meta && meta.content) {
                    published = meta.content;
                } else {
                    const m = document.body?.innerText?.match(/发布于\\s*(\\d{4}-\\d{2}-\\d{2}\\s*\\d{2}:\\d{2})/);
                    if (m) published = m[1];
                }
                return {text: text, published: published};
            }""")
            return result.get("text", ""), result.get("published") or None
        except Exception as e:
            logger.warning(f"获取帖子详情失败 {target}: {e}")
            return "", None
        finally:
            detail_page.close()

    def enrich_posts_full_text(self, posts):
        """对 description 被截断的帖子，访问详情页补全内容；并用详情页精确时间覆盖 API created_at"""
        import datetime as _dt
        for post in posts:
            desc = post.get("description", "") or ""
            text = post.get("text", "") or ""
            target = post.get("target", "")
            # text 为空，或 description 以 ... 结尾（摘要截断），说明正文可能被截断 → 详情页补全
            if target and (not text or desc.endswith("...")):
                time.sleep(config.REQUEST_DELAY)
                full, published = self.get_post_full_text(target)
                if full and len(full) > len(text or ""):
                    post["text"] = full
                    logger.info(f"  补全帖子 {target} ({len(full)} 字)")
                # 详情页精确时间覆盖 API 时间（详情页为权威来源）
                if published:
                    try:
                        pub = published.strip().replace("T", " ")[:16]
                        dt = _dt.datetime.strptime(pub, "%Y-%m-%d %H:%M")
                        new_ms = int(dt.timestamp() * 1000)
                        old_ms = post.get("created_at") or 0
                        if new_ms != old_ms:
                            post["created_at"] = new_ms
                            logger.info(f"  详情页时间覆盖 {target}: {published}")
                    except ValueError:
                        pass
        return posts

    def get_user_info(self, user_id):
        """获取用户基本信息"""
        user_page = self._browser.contexts[0].new_page()
        try:
            user_page.goto(
                f"https://xueqiu.com/u/{user_id}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            try:
                user_page.wait_for_selector(".user-name", timeout=5000)
            except Exception:
                pass
            info = user_page.evaluate("""() => {
                let name = document.querySelector('.user-name')?.textContent?.trim() || '';
                if (!name) {
                    const title = document.title || '';
                    if (title.includes(' - 雪球')) name = title.replace(' - 雪球', '').trim();
                }
                return {screen_name: name};
            }""")
            return info
        finally:
            user_page.close()

    def search_user(self, keyword):
        """搜索用户，返回 [{name, href, uid}] 列表"""
        encoded = urllib.parse.quote(keyword)
        url = f"https://xueqiu.com/k?q={encoded}&forceRedirect=1&page=1&type=user"
        search_page = self._browser.contexts[0].new_page()
        try:
            search_page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                search_page.wait_for_selector(
                    ".search__user__card__content, a.user-name", timeout=5000
                )
            except Exception:
                pass
            users = search_page.evaluate("""() => {
                const cards = document.querySelectorAll('.search__user__card__content');
                const result = [];
                for (const card of cards) {
                    const nameEl = card.querySelector('.user-name');
                    const descEl = card.querySelector('p');
                    result.push({
                        name: nameEl ? nameEl.textContent.trim() : '',
                        href: nameEl ? nameEl.getAttribute('href') : '',
                        desc: descEl ? descEl.textContent.trim().substring(0, 80) : ''
                    });
                }
                if (!result.length) {
                    const anchors = document.querySelectorAll('a.user-name');
                    for (const a of anchors) {
                        result.push({
                            name: a.textContent.trim(),
                            href: a.getAttribute('href') || ''
                        });
                    }
                }
                return result;
            }""")
            # 解析 href 中的 uid
            for u in users:
                u["uid"] = self._extract_uid_from_href(u.get("href", ""))
            return users
        finally:
            search_page.close()

    def _extract_uid_from_href(self, href):
        """从 href 中提取数字 uid，如 /u/1234 -> '1234'"""
        if not href:
            return ""
        m = re.match(r"/u/(\d+)", href)
        if m:
            return m.group(1)
        # 虚荣路径如 /zzyandsnow，需要 resolve
        return ""

    def resolve_user_id(self, vanity_path):
        """将虚荣路径（如 /zzyandsnow）解析为数字 user_id"""
        resolve_page = self._browser.contexts[0].new_page()
        try:
            resolve_page.goto(
                f"https://xueqiu.com{vanity_path}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            try:
                resolve_page.wait_for_selector(".user-name", timeout=5000)
            except Exception:
                pass
            # 从跳转后的 URL 或页面内容提取数字 ID
            final_url = resolve_page.url
            m = re.search(r"/u/(\d+)", final_url)
            if m:
                return m.group(1)
            # 从页面 JS 变量中提取
            uid = resolve_page.evaluate("""() => {
                const m = document.body?.innerHTML?.match(/"id":(\\d{5,})/);
                return m ? m[1] : '';
            }""")
            return uid or ""
        finally:
            resolve_page.close()

    def find_user_id(self, keyword):
        """搜索用户名并返回第一个精确匹配的数字 uid"""
        users = self.search_user(keyword)
        if not users:
            raise CrawlerError(f"未找到用户: {keyword}")
        # 优先精确匹配
        target = None
        for u in users:
            if u["name"] == keyword:
                target = u
                break
        if not target:
            target = users[0]
            logger.info(f"未精确匹配，使用第一个结果: {target['name']}")
        # 如果已有数字 uid 直接返回
        if target.get("uid"):
            return target["uid"], target["name"]
        # 否则解析虚荣路径
        href = target.get("href", "")
        if href:
            uid = self.resolve_user_id(href)
            if uid:
                return uid, target["name"]
        raise CrawlerError(f"无法解析用户ID: {target}")

    def get_user_all_posts_with_info(self, user_id, max_pages=10):
        """在同一个页面中获取用户信息和所有帖子，避免重复导航"""
        user_page = self._browser.contexts[0].new_page()
        all_statuses = []
        screen_name = str(user_id)
        try:
            user_page.goto(
                f"https://xueqiu.com/u/{user_id}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            try:
                user_page.wait_for_selector(".user-name", timeout=5000)
            except Exception:
                pass

            # 在同一页面获取用户名
            screen_name = user_page.evaluate("""() => {
                let name = document.querySelector('.user-name')?.textContent?.trim() || '';
                if (!name) {
                    const title = document.title || '';
                    if (title.includes(' - 雪球')) name = title.replace(' - 雪球', '').trim();
                }
                return name;
            }""") or str(user_id)

            # 在同一页面分页获取帖子
            for page_num in range(1, max_pages + 1):
                time.sleep(config.REQUEST_DELAY)
                result = user_page.evaluate(
                    """async (args) => {
                        try {
                            const resp = await fetch(
                                `${args.url}?user_id=${args.uid}&page=${args.page}&count=${args.count}`
                            );
                            const ct = resp.headers.get('content-type') || '';
                            if (!ct.includes('json')) return {ok: false, error: 'not json'};
                            const data = await resp.json();
                            if (data.error_code) return {ok: false, error: data.error_description};
                            return {ok: true, statuses: data.statuses || [], count: data.count};
                        } catch(e) { return {ok: false, error: e.message}; }
                    }""",
                    {"uid": user_id, "page": page_num,
                     "url": self._timeline_url, "count": self._timeline_count},
                )
                if not result.get("ok"):
                    # 首次失败 → 尝试自动降级端点后重试本页（只降级一次）
                    if self._degrade_timeline():
                        continue
                    logger.warning(f"用户 {user_id} 第 {page_num} 页失败: {result.get('error')}")
                    break
                statuses = result.get("statuses", [])
                if not statuses:
                    break
                all_statuses.extend(statuses)
                logger.info(f"  第 {page_num} 页获取 {len(statuses)} 条 (共 {len(all_statuses)})")
        finally:
            user_page.close()
        return screen_name, all_statuses

    def close(self):
        """断开浏览器连接"""
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
