"""ego lite 通道（2026-09-15 用户拍板：spyder 从 Chrome CDP 迁到 ego lite）。

为什么长这样：ego lite **不对外暴露 CDP 端口**（没有 `--remote-debugging-port` 这类语义），
它的 CDP 能力只经 `ego-browser nodejs` 的 Node 运行时暴露（`page.cdp()` / `page.evaluate()`）。
所以这里起一个 unix socket 服务端、把 `ego_bridge.js` 用 `-e` 交给 `ego-browser nodejs`
执行，桥连回来，双方用 JSON Lines 通信；登录态与反爬特征全部由 ego 进程承载，
本模块不启动任何浏览器。

**通道为什么是 socket（2026-09-15 实测，三个坑都踩过）**：`ego-browser nodejs` 对
stdin 的三种形态都不好用——① 脚本文本走 stdin：CLI 要等 EOF 才执行；
② `-e` 传脚本但 stdin 是管道：CLI 仍把管道当「脚本待读」而挂住；
③ stdin 给伪终端：脚本执行完进程立即退出。只有 stdin=/dev/null 时脚本立刻执行，
但那也意味着不能用 stdin 传协议 —— 所以协议另开 socket。

对外暴露的接口与 crawl 代码原来的 playwright 用法一一对应：
    Browser.contexts[0].new_page() -> Page
    Page.goto(url, wait_until=..., timeout=...)
    Page.evaluate(fn_or_expr, arg=None)
    Page.wait_for_selector(selector, timeout=...)
    Page.wait_for_timeout(ms) / Page.url / Page.close()
"""

import json
import os
import select
import shutil
import socket
import subprocess
import tempfile
import time

import config


class BridgeError(RuntimeError):
    pass


def _readline_sock(sock, buf, timeout):
    """从 socket 读一行（带超时，自己按 \\n 切）；返回 (line, 新缓冲)"""
    end = time.time() + timeout
    while "\n" not in buf:
        remaining = end - time.time()
        if remaining <= 0:
            return None, buf
        ready, _, _ = select.select([sock], [], [], min(0.5, remaining))
        if not ready:
            continue
        chunk = sock.recv(65536)
        if not chunk:
            raise BridgeError("ego 桥连接已断开")
        buf += chunk.decode("utf-8", "replace")
    line, _, rest = buf.partition("\n")
    return line, rest


class EgoBridge:
    """一个进程 = 一个 ego 任务空间 = 一次采集会话"""

    def __init__(self, cli=None, space=None, boot_timeout=None):
        self.cli = cli or shutil.which("ego-browser") or ""
        self.space = space if space is not None else config.EGO_SPACE
        self.boot_timeout = boot_timeout or config.EGO_BOOT_TIMEOUT
        self._seq = 0
        self._srv = None
        self._conn = None
        self._buf = ""
        self._log_fh = None
        self._sock_path = None
        self.proc = None
        self.main_page = None

    # ── 生命周期 ──────────────────────────────────────────────
    def start(self):
        if not self.cli:
            raise BridgeError(
                "未找到 ego-browser CLI —— 请先装好 ego lite 的命令行工具"
                "（用户 2026-09-15 已要求不再用 Chrome）"
            )
        if not os.path.exists(config.EGO_BRIDGE_JS):
            raise BridgeError(f"桥接脚本不存在: {config.EGO_BRIDGE_JS}")

        with open(config.EGO_BRIDGE_JS, "r", encoding="utf-8") as fh:
            script = fh.read()

        self._sock_path = os.path.join(
            tempfile.mkdtemp(prefix="xueqiu-ego-"), "bridge.sock")
        self._srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._srv.bind(self._sock_path)
        self._srv.listen(1)
        self._srv.settimeout(self.boot_timeout)

        # 注意顺序：先定 socket 路径，再注入配置（配置里带 socket 路径）
        script = self._bake_config(script)

        env = dict(os.environ)

        # stdin=/dev/null 是唯一能让 `-e` 脚本立刻执行的形态（见模块头注释）
        self.proc = subprocess.Popen(
            [self.cli, "nodejs", "-e", script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self._spawn_stderr_drain()

        try:
            conn, _ = self._srv.accept()
        except socket.timeout:
            self.stop()
            raise BridgeError(
                f"ego 桥启动超时（{self.boot_timeout:g}s）—— "
                f"确认 ego lite 已打开并已登录雪球")
        conn.settimeout(None)
        self._conn = conn
        self._buf = ""

        line, self._buf = _readline_sock(self._conn, self._buf, min(30, self.boot_timeout))
        if line is None:
            self.stop()
            raise BridgeError("ego 桥握手超时（连上了但没发 hello）")
        try:
            hello = json.loads(line)
        except ValueError:
            self.stop()
            raise BridgeError(f"ego 桥握手失败，首行不是 JSON: {line[:120]}")
        if not hello.get("hello"):
            self.stop()
            raise BridgeError(f"ego 桥启动失败: {hello.get('error', 'unknown')}")

        self.main_page = Page(self, "p1")
        return hello

    def _bake_config(self, script):
        """配置注入：ego 的 Node 运行时拿不到父进程环境变量（实测），
        所以把 socket 路径等直接拼进脚本头部，由桥读 `__EGO_CFG`。
        注意：shebang 必须留在**第 1 行**（否则 VM 报 SyntaxError），故先摘后拼。"""
        cfg = {
            "sock": self._sock_path,
            "space": self.space or None,
            "spaceName": os.environ.get("XUEQIU_EGO_SPACE_NAME", "xueqiu-spyder"),
            "url": os.environ.get("XUEQIU_EGO_URL", "https://xueqiu.com/"),
            # 页签保留：采集现场就是风控证据，采完不自动关（用户要盯着看）
            "keepPages": os.environ.get("XUEQIU_EGO_KEEP_PAGES", "1") not in ("0", "false", "no"),
        }
        shebang = ""
        if script.startswith("#!"):
            first_nl = script.find("\n")
            if first_nl > 0:
                shebang = script[:first_nl + 1]
                script = script[first_nl + 1:]
        header = "const __EGO_CFG = " + json.dumps(cfg, ensure_ascii=False) + ";\n"
        return shebang + header + script

    def _spawn_stderr_drain(self):
        """把桥的 stderr（致命错误/杂音）排到日志文件或 devnull，避免管道塞满卡死"""
        import threading

        def drain():
            try:
                for line in self.proc.stderr:
                    if self._log_fh:
                        self._log_fh.write(line)
                        self._log_fh.flush()
            except Exception:
                pass

        log_path = os.environ.get("XUEQIU_EGO_LOG", "")
        if log_path:
            try:
                self._log_fh = open(log_path, "a", encoding="utf-8")
            except OSError:
                self._log_fh = None
        threading.Thread(target=drain, daemon=True).start()

    def stop(self):
        """退出桥：请它自己关（保住 ego 的标签页），超时再杀"""
        try:
            if self._conn:
                self._conn.sendall((json.dumps({"id": -1, "cmd": "shutdown"}) + "\n").encode("utf-8"))
        except Exception:
            pass
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        self.proc = None
        for closeable in (self._conn, self._srv):
            try:
                if closeable:
                    closeable.close()
            except Exception:
                pass
        self._conn = self._srv = None
        self._buf = ""
        if self._log_fh:
            try:
                self._log_fh.close()
            except Exception:
                pass
            self._log_fh = None

    # ── 请求 ──────────────────────────────────────────────────
    def call(self, cmd, timeout=90, **payload):
        if not self._conn:
            raise BridgeError("ego 桥未运行")
        self._seq += 1
        req = {"id": self._seq, "cmd": cmd}
        req.update({k: v for k, v in payload.items() if v is not None})
        if cmd == "evaluate":
            # 显式带回 arg（None → null）：ego 的 page.evaluate 对「没有第二个参数」
            # 会报 must be JSON-serializable，必须传 null（2026-09-15 实测）
            req["arg"] = payload.get("arg")
        self._conn.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))

        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise BridgeError(f"ego 请求超时（{cmd}，{timeout:g}s）")
            line, self._buf = _readline_sock(self._conn, self._buf, remaining)
            if line is None:
                raise BridgeError(f"ego 请求超时（{cmd}，{timeout:g}s）")
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
            except ValueError:
                continue
            if resp.get("id") != self._seq:
                continue  # 迟到的旧响应：丢弃
            if resp.get("ok"):
                return resp.get("result")
            raise BridgeError(resp.get("error") or f"{cmd} 失败")


class Page:
    """一张 ego 标签页；label 由桥分配（p1 = 主页面，p2+ = 临时页）"""

    def __init__(self, bridge, label):
        self._bridge = bridge
        self.label = label

    def goto(self, url, wait_until=None, timeout=None):
        budget = max(30, int((timeout or 15000) / 1000) + 20)
        return self._bridge.call("goto", timeout=budget, page=self.label, url=url)

    def evaluate(self, fn_or_expr, arg=None):
        # arg 必须显式给（不能是「缺字段」）：ego 的 page.evaluate 对「没有第二个
        # 参数」和「第二个参数为 null」处理不同，缺字段会报
        # "page.evaluate argument must be JSON-serializable"（2026-09-15 实测）
        return self._bridge.call("evaluate", timeout=90, page=self.label,
                                 fn=fn_or_expr, arg=arg if arg is not None else None)

    def wait_for_selector(self, selector, timeout=8000):
        return self._bridge.call("waitForSelector", timeout=timeout / 1000 + 20,
                                 page=self.label, selector=selector, timeoutMs=timeout)

    def wait_for_timeout(self, ms):
        time.sleep(ms / 1000.0)

    def screenshot(self, path, timeout=60):
        """把该页当前画面存成 PNG（风控留证用；ego 页面本来就是可见的）"""
        return self._bridge.call("screenshot", timeout=timeout, page=self.label, path=path)

    @property
    def url(self):
        return self._bridge.call("url", timeout=30, page=self.label) or ""

    def close(self):
        try:
            self._bridge.call("close", timeout=30, page=self.label)
        except BridgeError:
            pass


class Context:
    """模仿 playwright 的 context（crawl 代码用 contexts[0].new_page()）"""

    def __init__(self, bridge):
        self._bridge = bridge

    def new_page(self):
        res = self._bridge.call("newPage", timeout=60)
        return Page(self._bridge, (res or {}).get("label") or "p1")

    @property
    def pages(self):
        return [self._bridge.main_page] if self._bridge.main_page else []


class Browser:
    """模仿 playwright 的 browser：只暴露 contexts / close"""

    def __init__(self, bridge):
        self._bridge = bridge
        self._ctx = Context(bridge)

    @property
    def contexts(self):
        return [self._ctx]

    def close(self):
        self._bridge.stop()
