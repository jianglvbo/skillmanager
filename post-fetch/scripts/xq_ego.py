#!/usr/bin/env python3
"""post-fetch 脚本的 ego lite 接入层（2026-09-16 迁移，替代 browser-act）

用户口径：「以后别用 chrome 了，用 ego lite」「无论什么时候用完 ego lite 都要记得关」。

为什么单独一层：post-fetch 下的同步/补全脚本原来都直接调 browser-act（chrome 模式），
与工具层 xueqiu-spyder 的 ego 通道是两套浏览器；这里统一成 ego lite，
复用 xueqiu-spyder 的桥（ego_browser.EgoBridge），登录态与工具层完全一致。

用法（脚本里）：

    from xq_ego import ego_session, bring_to_front

    with ego_session() as page:
        page.goto("https://xueqiu.com/...")
        txt = page.text()        # 页面可见文本（JSON 接口页就是原文）
        body = page.evaluate("() => document.querySelector('.article__bd__detail')?.textContent || ''")

退出 with 时桥会关掉自己开的页签（ego 里不留痕迹）；前置条件＝ego lite 已打开且已登录雪球。
"""
import os
import sys
from contextlib import contextmanager

# 复用工具层的 ego 通道（唯一实现，别再各写一份）
_SPYDER_CANDIDATES = ["~/.agents/skills/xueqiu-spyder", "~/.zcode/skills/xueqiu-spyder"]
for _c in _SPYDER_CANDIDATES:
    _d = os.path.expanduser(_c)
    if os.path.isdir(_d):
        SPYDER_DIR = _d
        if SPYDER_DIR not in sys.path:
            sys.path.insert(0, SPYDER_DIR)
        break

from ego_browser import BridgeError, EgoBridge   # noqa: E402  （路径注入后才能导入）


@contextmanager
def ego_session():
    """开一个 ego 会话；退出时关桥（桥自己开的页签随之关闭）"""
    bridge = EgoBridge()
    try:
        bridge.start()
    except BridgeError as e:
        sys.exit(f"❌ ego 通道不可用：{e}\n"
                 f"（请先打开 ego lite 并登录雪球；用户已要求不再用 Chrome）")
    try:
        yield bridge.main_page
    finally:
        bridge.stop()


def bring_to_front(app="ego lite"):
    """把浏览器窗口拉到前台（风控时要用户盯屏/手动过滑块）"""
    import subprocess
    try:
        subprocess.run(["osascript", "-e", f'tell application "{app}" to activate'],
                       capture_output=True, timeout=5)
    except Exception:
        pass
