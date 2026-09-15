import time
import re
import sys
import logging
import subprocess
import os
import urllib.parse
from playwright.sync_api import sync_playwright

import config
import ego_browser

logger = logging.getLogger(__name__)


def _default_chrome_path():
    """跨平台返回 Chrome/Chromium 可执行文件路径（仅 XUEQIU_TRANSPORT=chrome 时用）"""
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
# 2026-09-12：CDP profile 从 skill 目录挪到用户缓存目录——它含 Cookies/Login Data/History，
# 放在 skill 目录里会被 git add 进公共仓库（当天实测已误入 1.1 万个文件）。可用
# XUEQIU_USER_DATA_DIR 覆盖；旧位置（skill 目录内）仅作迁移前的历史遗留，不再使用。
USER_DATA_DIR = os.environ.get("XUEQIU_USER_DATA_DIR") or os.path.join(
    os.path.expanduser("~"), ".cache", "xueqiu-spyder", "chrome-profile")
# ⚠️ 以下 Chrome 相关常量**只服务旧通道**（XUEQIU_TRANSPORT=chrome，2026-09-15 起仅排障用）。
# 默认通道是 ego lite，见 ego_browser.py；这两个变量在新通道下完全不参与。
# 可用环境变量 XUEQIU_DEBUG_PORT 覆盖，避免与既有 9222 调试实例冲突
DEBUG_PORT = int(os.environ.get("XUEQIU_DEBUG_PORT", "9222"))
# 2026-09-12：Chrome 152 起 DevTools HTTP 端点只接受 Host=localhost，
# 用 127.0.0.1 直连会返回 404（/json/version 不可用）。故主机名可覆盖，默认 localhost。
DEBUG_HOST = os.environ.get("XUEQIU_DEBUG_HOST", "localhost")
# ── 浏览器通道（2026-09-15 用户拍板：「以后别用 chrome 了，用 ego lite」）────
# 默认 auto：有 ego-browser CLI 就走 ego lite（ego_browser.EgoBridge），
# 没有才回落 Chrome CDP；显式设 XUEQIU_TRANSPORT=ego 则**禁止**回落 Chrome。


class CrawlerError(Exception):
    pass


class TaskSpaceLost(CrawlerError):
    """ego 任务空间已不属于 agent（用户接管 / 空间结束）。

    2026-09-16 实测：用户碰了一下浏览器，ego 就把空间交还给用户，之后每条请求都返回
    "The user has taken control of this task space…"。这种错误**重试没有意义**，
    必须立刻停手、如实汇报，等用户明确说继续再 claim 空间（ego 的硬约束）。
    """


class XueqiuCrawler:
    """复用真实浏览器环境绕过 WAF：默认走 ego lite（2026-09-15），可回落 Chrome CDP"""

    # 详情页补全连续失败多少条就停（多半是任务空间被接管/结束，继续硬撞只是刷日志）
    _ENRICH_FAIL_LIMIT = 3

    def __init__(self):
        self._pw = None
        self._browser = None
        self._ego = None
        self._page = None
        self._page_override = None
        # timeline 端点状态：v4 被 WAF 405 时自动降级到旧版路径（2026-09-09 固化）
        self._timeline_url = config.USER_TIMELINE_URL
        self._timeline_count = config.USER_POSTS_COUNT
        self._degraded = False
        self._shot_tag = time.strftime("%Y%m%d-%H%M%S")   # 本次采集的截图批次号
        self._detail_seen = 0
        self._connect_browser()

    @property
    def _main_page(self):
        """主页面句柄：ego 通道是桥的主页，chrome 通道是 playwright 的页；
        万一某段流程要临时换页，设 _page_override 即可，其余流程一律读这里"""
        return self._page_override or self._page

    def _connect_browser(self):
        """按 XUEQIU_TRANSPORT 选通道：auto 优先 ego lite，只有没有 ego CLI 时才回落 Chrome"""
        mode = config.BROWSER_TRANSPORT
        if mode in ("auto", "ego"):
            try:
                self._connect_ego()
                self._wake_ego()      # 让用户能盯着采集现场（风控是否触发）
                return
            except Exception as e:
                if mode == "ego":
                    raise CrawlerError(
                        f"ego lite 通道不可用：{e}\n"
                        f"（用户 2026-09-15 已要求只用 ego lite；请先打开 ego lite 并登录雪球，"
                        f"并确认 `ego-browser --help` 可用）"
                    )
                logger.warning(f"ego lite 通道不可用（{e}）—— 回落 Chrome CDP")
        self._connect_chrome()

    def _connect_ego(self):
        """连接 ego lite：不启动任何浏览器，只把动作转发给它（见 ego_browser.py）

        2026-09-15 迁移：原来这里连 Chrome 的 CDP 调试端口（并在没有调试端口时自己
        拉起一个带调试端口的 Chrome）。ego lite 不对外暴露 CDP 端口，故改走
        ego-browser 的 Node 运行时；登录态直接复用 ego 里已登录的雪球会话，
        不再需要单独的采集 profile（~/.cache/xueqiu-spyder/chrome-profile 随之退役）。
        """
        bridge = ego_browser.EgoBridge()
        hello = bridge.start()
        self._ego = bridge
        self._browser = ego_browser.Browser(bridge)
        self._page = bridge.main_page
        logger.info("已连接 ego lite（桥进程 pid=%s）", hello.get("pid"))

    # ── 现场可见性（2026-09-16 用户要求）──────────────────────────────
    def _wake_ego(self):
        """把 ego lite 窗口拉到前台——用户要能看着采集跑，才能第一时间发现风控。

        用户原话：「采集博主言论的时候，我需要 ego lite 的页面在前端，我才能知道有没有
        触发风控」。页面本来就开在 ego 里（可见），这里只是保证它不在别的窗口后面。
        关掉：`XUEQIU_EGO_WAKE=0`。
        """
        if not config.EGO_WAKE or sys.platform != "darwin":
            return
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "ego lite" to activate'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
            )
            logger.info("已把 ego lite 窗口拉到前台（采集过程可直接观察；禁用：XUEQIU_EGO_WAKE=0）")
        except Exception as e:
            logger.debug("激活 ego 窗口失败（不影响采集）：%s", e)

    def _shot(self, tag, page=None, force=False):
        """落一张现场截图留证（风控/异常时自动调用，也可按间隔抽帧）。

        ego 里页面是可见的，但风控提示往往一闪而过；截图让用户事后能核对
        「当时页面上到底是什么」。落图目录 `XUEQIU_EGO_SHOT_DIR`
        （默认 `~/.cache/xueqiu-spyder/shots`），失败只记日志、不影响采集。
        """
        if not config.EGO_SHOT_DIR:
            return None
        target = page if page is not None else self._main_page
        if target is None:
            return None
        try:
            os.makedirs(config.EGO_SHOT_DIR, exist_ok=True)
            stamp = time.strftime("%H%M%S")
            path = os.path.join(config.EGO_SHOT_DIR, self._shot_tag, f"{stamp}-{tag}.png")
            target.screenshot(path)
            logger.warning("现场截图已保存：%s", path)
            return path
        except Exception as e:
            if force:
                logger.warning("现场截图失败（不影响采集）：%s", e)
            return None

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
                f"http://{DEBUG_HOST}:{DEBUG_PORT}"
            )
            logger.info("已连接到运行中的 Chrome")
        except Exception:
            logger.info("未检测到调试端口，正在启动 Chrome...")
            self._launch_chrome()
            time.sleep(3)
            self._browser = self._pw.chromium.connect_over_cdp(
                f"http://{DEBUG_HOST}:{DEBUG_PORT}"
            )
            logger.info("Chrome 启动并连接成功")

        # 获取或创建页面
        contexts = self._browser.contexts
        if contexts and contexts[0].pages:
            self._page = contexts[0].pages[0]
        else:
            self._page = self._browser.contexts[0].new_page()

        # 确保在雪球域名下
        if "xueqiu.com" not in self._main_page.url:
            self._main_page.goto(config.XUEQIU_HOME, wait_until="domcontentloaded", timeout=15000)

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
                result = self._main_page.evaluate(
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

                # 任务空间被接管/结束：立刻停手，不重试（重试只会刷屏）
                blob_early = f"{result.get('error') or ''} {result.get('snippet') or ''}"
                if re.search(r"taken control|not assigned to the agent|Task space not found|commands are paused",
                             blob_early, re.I):
                    self._shot("space-lost", force=False)
                    raise TaskSpaceLost(
                        "ego 任务空间已被接管或结束——采集停止。"
                        "（要接着跑：在 ego 里把任务空间交回 agent，或让用户明确说「继续」后重新 claim）"
                    )

                # WAF / 滑块 / 安全验证检测（雪球阿里云防护特征）
                snippet = (result.get("snippet") or "") + (result.get("error") or "")
                if re.search(r"滑动|安全验证|captcha|无感验证|请完成验证|访问验证", snippet, re.I):
                    self._shot("waf-timeline")
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
                    self._shot(f"timeline-fail-page{page_num}", page=user_page)
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
                return {text: text, published: published,
                        title: document.title || '',
                        snippet: (document.body?.innerText || '').slice(0, 300)};
            }""")
            # 2026-09-12：详情页可能被 WAF 拦成 405/验证页——此前静默返回空正文，
            # 整批继续硬撞直到封禁加重（09-08 批 69 条摘要帖就是这么来的）。
            # 这里改为显式抛错中止本轮，交由编排层等待冷却后重跑。
            blob = f"{result.get('title', '')} {result.get('snippet', '')}"
            if re.search(r"(?<!\d)405(?!\d)|滑动|安全验证|访问验证|请完成验证|captcha", blob, re.I):
                self._shot(f"waf-detail-{target.strip('/').replace('/', '_')}", page=detail_page)
                raise CrawlerError(
                    f"详情页命中 WAF/405（{target}）—— 中止本轮采集，等待冷却后重跑；"
                    f"页面特征: {blob.strip()[:80]}"
                )
            return result.get("text", ""), result.get("published") or None
        except CrawlerError:
            raise
        except Exception as e:
            if "任务空间已不属于 agent" in str(e):
                logger.error(
                    "获取帖子详情失败 %s：ego 任务空间已被接管/结束——停止补全，"
                    "剩余帖子按 API 摘要处理", target,
                )
            else:
                logger.warning(f"获取帖子详情失败 {target}: {e}")
            self._shot(f"detail-error-{target.strip('/').replace('/', '_')}", page=detail_page)
            return "", None
        finally:
            detail_page.close()

    def enrich_posts_full_text(self, posts):
        """对 description 被截断的帖子，访问详情页补全内容；并用详情页精确时间覆盖 API created_at"""
        import datetime as _dt
        failed = 0
        for post in posts:
            desc = post.get("description", "") or ""
            text = post.get("text", "") or ""
            target = post.get("target", "")
            # text 为空，或 description 以 ... 结尾（摘要截断），说明正文可能被截断 → 详情页补全
            # 需要补全的判据：详情页目标存在，且正文缺失/明显是 API 摘要
            #   ① 没有正文；② 描述被截断（...）；③ 正文短于截断描述（半截内容）
            # 只按 desc.endswith("...") 判断会漏掉"text 本身就不完整但不带省略号"的帖
            # （2026-09-16 实测：description 截断、text 半截，两者都不长 → 旧判据直接跳过）
            looks_truncated = not text or desc.endswith("...") or len(text) < len(desc)
            if target and looks_truncated:
                time.sleep(config.REQUEST_DELAY)
                self._detail_seen += 1
                # 抽帧留证：详情页是风控最常出现的地方，按间隔落图便于回看
                if config.EGO_SHOT_EVERY and self._detail_seen % config.EGO_SHOT_EVERY == 0:
                    self._shot(f"progress-{self._detail_seen}")
                post["needs_full"] = True     # 待补全：失败时据此标「摘要」而不是「全文」
                full, published = self.get_post_full_text(target)
                if full:
                    # 详情页是权威来源：**只要抓到就采用**，不再要求"比 API 的 text 长"
                    # （2026-09-16 修：此前把"长度相当但内容更全"的帖误判为失败，
                    #   连撞三次触发熔断，导致后面几十条全部跳过）
                    changed = len(full) != len(text or "")
                    post["text"] = full
                    post["needs_full"] = False
                    logger.info(
                        f"  详情页正文{'覆盖' if changed else '确认'} {target} ({len(full)} 字)"
                    )
                else:
                    failed += 1
                    if failed >= self._ENRICH_FAIL_LIMIT:
                        logger.error(
                            "详情页补全连续失败 %d 条（常见原因：用户接管了任务空间 / 任务空间已结束）"
                            "——停止补全；剩余帖子按 API 摘要处理并标「摘要」，不会误标「全文」",
                            failed,
                        )
                        break
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
                    self._shot(f"timeline-fail-page{page_num}", page=user_page)
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
        """断开浏览器连接

        2026-09-15：ego 通道下 **只关桥进程，不关 ego 本身**——ego 是用户自己的浏览器，
        它的标签页与登录态要留给用户（桥进程退出时会把写入流关掉，ego 里的标签页保留）。
        """
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        finally:
            self._ego = None
            # 采集结束再把 ego 拉回前台：页签停在最后一个现场，用户可以直接看结果/风控
            self._wake_ego()
