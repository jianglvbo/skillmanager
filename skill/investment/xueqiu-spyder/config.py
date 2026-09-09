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
