import os

# API endpoints
XUEQIU_HOME = "https://xueqiu.com/"
SEARCH_STATUS_URL = "https://xueqiu.com/query/v1/symbol/search/status.json"
# v4 路径被 WAF 405 封禁时，可经 XUEQIU_TIMELINE_URL 切到旧版路径
# （旧版数据结构一致 {"count":N,"statuses":[...]}，但 count 上限 20）
USER_TIMELINE_URL = os.environ.get(
    "XUEQIU_TIMELINE_URL", "https://xueqiu.com/v4/statuses/user_timeline.json"
)
# 自动降级目标：v4 路径 405/非 JSON 时 crawler 自动切到此端点重试（无需人工干预）
USER_TIMELINE_URL_FALLBACK = os.environ.get(
    "XUEQIU_TIMELINE_URL_FALLBACK", "https://xueqiu.com/statuses/user_timeline.json"
)
# 旧版路径每页上限 20（v4 支持 50），降级后自动下调
FALLBACK_POSTS_COUNT = 20

# Crawling parameters
MIN_REPLY_COUNT = 20
MAX_PAGES = 20
POSTS_PER_PAGE = 50
# 用户页翻页每页条数：默认 20（v4 与旧版路径都支持；旧版上限即 20）
USER_POSTS_COUNT = int(os.environ.get("XUEQIU_POSTS_COUNT", "20"))

# Rate limiting
REQUEST_DELAY = 1.0
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

# Headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Output
DEFAULT_OUTPUT_DIR = "./output"

# ── 浏览器通道（2026-09-15 用户拍板：默认走 ego lite）──────────────────────
#   ego   : 经 ego_bridge.js 把浏览器动作转发给 **ego lite**（复用其登录态，不启动 Chrome）
#   chrome: 旧路径，Chromium CDP 调试端口（仅作兼容保留；用户已要求不再用 Chrome）
#   auto  : 默认——装了 ego-browser CLI 就用 ego，否则回落 chrome 并告警
# 用户原话（2026-09-15）：「以后别用 chrome 了，用 ego lite」。
BROWSER_TRANSPORT = os.environ.get("XUEQIU_TRANSPORT", "auto").strip().lower()
# 桥接脚本：同目录的 ego_bridge.js，可用环境变量指到别处
EGO_BRIDGE_JS = os.environ.get(
    "XUEQIU_EGO_BRIDGE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ego_bridge.js"),
)
# 复用的 ego 任务空间 id（同一批采集沿用，跨进程不新建）
EGO_SPACE = os.environ.get("XUEQIU_EGO_SPACE", "")
# ego 桥启动握手超时（秒）
EGO_BOOT_TIMEOUT = float(os.environ.get("XUEQIU_EGO_BOOT_TIMEOUT", "90"))

# ── 现场可见性（2026-09-16 用户要求）──────────────────────────────────
# 用户原话：「采集博主言论的时候，我需要 ego lite 的页面在前端，我才能知道有没有触发风控」。
# EGO_WAKE：采集开始/结束时把 ego lite 窗口拉到前台（macOS 走 osascript activate）
EGO_WAKE = os.environ.get("XUEQIU_EGO_WAKE", "1") not in ("0", "false", "no")
# EGO_SHOT_DIR：命中风控/异常时自动落图留证的目录（空＝不落图）
EGO_SHOT_DIR = os.environ.get(
    "XUEQIU_EGO_SHOT_DIR",
    os.path.join(os.path.expanduser("~"), ".cache", "xueqiu-spyder", "shots"),
)
# 详情页补全过程中每隔 N 条落一张图（0＝关；默认每 5 条，便于回看进度与风控弹窗）
EGO_SHOT_EVERY = int(os.environ.get("XUEQIU_EGO_SHOT_EVERY", "5"))
