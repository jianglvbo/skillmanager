#!/usr/bin/env node
/*
 * ego 通道桥（2026-09-15 用户拍板：spyder 从 Chrome CDP 迁到 ego lite）。
 *
 * 为什么是这样一个文件：ego lite **不对外暴露 CDP 端口**（没有 `--remote-debugging-port`
 * 这类语义），它的 CDP 能力只经 `ego-browser nodejs` 的 Node 运行时暴露
 * （`page.cdp()` / `page.evaluate()`）。所以由 Python 侧起一个 unix socket 服务端，
 * 本脚本经 `-e` 传入、连接回来，之后两边用 **JSON Lines over socket** 通信；
 * 登录态与反爬特征全部由 ego 进程承载，本脚本不启动任何浏览器。
 *
 * 为什么不用 stdin 传协议（2026-09-15 实测，三个坑）：
 *   ① 脚本文本走 stdin → CLI 要等 EOF 才执行；
 *   ② 用 `-e` 传脚本但 stdin 是管道 → CLI 仍把管道当「脚本待从 stdin 读」而挂住；
 *   ③ stdin 给伪终端 → 脚本执行完进程立刻退出（PTY 上 events 不续命）。
 *   → 结论：stdin 一律给 /dev/null，协议另开 socket（与 Python 的父子关系无关，最稳）。
 *
 * 协议（每行一个 JSON 请求，回一行 JSON 响应）：
 *   {"id":1,"cmd":"goto","page":"p1","url":"https://xueqiu.com/"}
 *   {"id":2,"cmd":"evaluate","page":"p1","fn":"async (a) => ({...})","arg":{...}}
 *   {"id":3,"cmd":"waitForSelector","page":"p1","selector":"div","timeoutMs":8000}
 *   {"id":4,"cmd":"newPage"}                        // 新建 ego 标签页，回 {"label":"p2"}
 *   {"id":5,"cmd":"url","page":"p2"}
 *   {"id":6,"cmd":"close","page":"p2"}              // 只关该页（默认保留页签，见下）
 *   {"id":7,"cmd":"shutdown"}                       // 桥自行退出
 *   {"id":8,"cmd":"screenshot","page":"p1","path":"/abs/out.png"}   // 落图，供用户事后核对风控
 *   {"id":9,"cmd":"text","page":"p1"}               // 读页面可见文本（`document.body.innerText`）
 *   {"id":10,"cmd":"cookies"}                       // 读该会话 Cookie 串（给 requests 复用同一登录态）
 *
 *   **页签策略（2026-09-16 用户口径：随用随关，除非有必要才保留）**：
 *   ① 页面确实开在 ego 里且可见（用户要盯风控）；
 *   ② 桥在整个会话里**只维护一张工作页**：临时页用完即"放回"，下一次调用直接复用，
 *      全程不新开第二张——ego 任务空间有 8 个标签页上限（实测
 *      `Page budget reached (8/8)`），"用完就关、下次再开"在逐帖循环里必然撞顶；
 *   ③ 桥退出（shutdown / 进程被杀，含父进程异常退出时注册的 exit 钩子）时，
 *      把桥自己开的页签**全部真关**——用完不留痕，也不占用户浏览器。
 *
 *   fn 既接受函数表达式（`async (a) => {...}` / `() => {...}`），也接受裸表达式
 *   （`document.title`）；裸表达式会被包成 `async (a) => (expr)`，这样 Python 侧
 *   两种 Playwright 写法都能原样传来。
 *
 * 配置从哪来（2026-09-15 实测）：ego 的 Node 运行时**不继承父进程环境变量**
 * （`process.env.XUEQIU_EGO_SOCK` 是 undefined），所以配置由 Python 侧在启动时
 * 注入到脚本头部（见 ego_browser.py 的 `_bake_config`）：本文件第二行期望一个
 * `const __EGO_CFG = {...}`。字段：
 *   sock       必填：Python 侧 socket 路径
 *   space      复用已存在的任务空间 id（多轮采集沿用同一个，不新建）
 *   spaceName  任务空间名（仅新建时用到）
 *   url        启动时若当前页不在该域，先导航过去（默认雪球首页）
 *   （无其它可调项：会话内固定一张工作页，退出时统一关）
 */

const CFG = typeof __EGO_CFG !== "undefined" ? __EGO_CFG : {};
const SOCK = CFG.sock;
const SPACE = CFG.space;
const SPACE_NAME = CFG.spaceName || "xueqiu-spyder";
const HOME = CFG.url || "https://xueqiu.com/";

const pages = new Map();
let task = null;
let workPage = null;                    // 会话内唯一的工作页（用完放回，下次复用）

const net = require("net");

function pageOf(label) {
  const page = pages.get(label || "p1");
  if (!page) throw new Error("unknown page label: " + label);
  return page;
}

async function boot() {
  task = SPACE ? await taskSpace(Number(SPACE)) : await taskSpace(SPACE_NAME);
  // 注册表只装本会话真正在用的页签：ego 的页签编号是**整个浏览器单调递增**的
  // （本次实测跨进程递增到 p15），跨会话残留的旧条目会让 pageOf() 指到别的 space 的页。
  pages.clear();
  workPage = null;
  const first = task.page("p1");
  pages.set("p1", first);
  const current = await first.url();
  if (!/xueqiu\.com/.test(current)) {
    await first.goto(HOME);
    await first.waitForLoadState("domcontentloaded");
  }
  // 用完收尾：桥退出（正常 shutdown / 被杀）时把桥自己开的页签全关
  process.on("exit", () => { cleanupOwnPages(); });
  process.on("SIGTERM", () => { cleanupOwnPages(); process.exit(0); });
  process.on("SIGINT", () => { cleanupOwnPages(); process.exit(0); });
}

/* 关掉桥自己开的页签（主页面 p1 是用户的，不动）。
   注意：必须 **await**，因为 process.exit 不等异步——2026-09-16 实测用 exit 钩子
   调它会残留页签。 */
async function cleanupOwnPages() {
  workPage = null;
  for (const [label, p] of Array.from(pages.entries())) {
    if (label === "p1") continue;
    try {
      await p.close();
      pages.delete(label);
    } catch (e) { /* 已关或连接已断，忽略 */ }
  }
}

function forgetAndClose(page) {
  for (const [label, p] of Array.from(pages.entries())) {
    if (p === page) pages.delete(label);
  }
  try { page.close(); } catch (e) { /* 已关或连接已断，忽略 */ }
}

async function handle(req) {
  const id = req && req.id;
  try {
    switch (req.cmd) {
      case "newPage": {
        if (!workPage) {
          // 整个会话只开一张工作页：用完放回，下次直接复用（避开 8 页上限）
          workPage = await task.newPage();
          pages.set(workPage.label, workPage);
        }
        return { id, ok: true, result: { label: workPage.label, reused: true } };
      }
      case "goto": {
        const page = pageOf(req.page);
        await page.goto(req.url);
        await page.waitForLoadState("domcontentloaded");
        return { id, ok: true, result: { url: await page.url() } };
      }
      case "evaluate": {
        const page = pageOf(req.page);
        const raw = String(req.fn || "").trim().replace(/;\s*$/, "");
        const looksLikeFn = /^(async\s*)?(function\b|\()/.test(raw) || /=>/.test(raw);
        const fn = eval("(" + (looksLikeFn ? raw : "async (a) => (" + raw + ")") + ")");
        const result = await page.evaluate(fn, req.arg);
        return { id, ok: true, result: result === undefined ? null : result };
      }
      case "waitForSelector": {
        await pageOf(req.page).waitForSelector(req.selector, {
          timeout: req.timeoutMs || 8000,
        });
        return { id, ok: true, result: true };
      }
      case "url": {
        return { id, ok: true, result: await pageOf(req.page).url() };
      }
      case "close": {
        const label = req.page || "p1";
        const page = pageOf(label);
        if (label === "p1" || req.force) {
          // 主页面是用户的页面，桥不关；显式 force 才真关
          if (label === "p1") return { id, ok: true, result: { kept: true, label } };
          pages.delete(label);
          await page.close();
          return { id, ok: true, result: { closed: true, label } };
        }
        // 用完放回：页签由桥在退出时统一关（会话内复用同一张，不再新开）
        return { id, ok: true, result: { released: true, label } };
      }
      case "screenshot": {
        // 未指定页时拍**工作页**（正在被驱动的页），而不是主页面——2026-09-16 实测：
        // 主页面停在某个不动的 URL 上，进度截图拍它会拍到"上一次的样子"。
        const target = pageOf(req.page || (workPage ? workPage.label : "p1"));
        await target.screenshot({ path: req.path });
        return { id, ok: true, result: { path: req.path, page: req.page || (workPage ? workPage.label : "p1") } };
      }
      case "text": {
        // 页面可见文本：脚本侧要"看"页面内容时用（如关注列表接口页的 JSON 文本）
        const text = await pageOf(req.page).evaluate(() => document.body.innerText || "");
        return { id, ok: true, result: text };
      }
      case "cookies": {
        const jar = await pageOf(req.page).evaluate(() => document.cookie || "");
        return { id, ok: true, result: jar };
      }
      case "shutdown": {
        // 先把桥自己开的页签真关掉再退出（exit 钩子里 await 不住，会残留）
        await cleanupOwnPages();
        setTimeout(() => process.exit(0), 50);
        return { id, ok: true, result: { cleaned: true } };
      }
      default:
        return { id, ok: false, error: "unknown cmd: " + (req && req.cmd) };
    }
  } catch (e) {
    const detail = String((e && e.stack) || (e && e.message) || e).slice(0, 900);
    process.stderr.write("[bridge] " + req.cmd + " failed: " + detail + "\n");
    return { id, ok: false, error: String((e && e.message) || e).slice(0, 600) };
  }
}

async function main() {
  if (!SOCK) {
    process.stderr.write("XUEQIU_EGO_SOCK 未设置\n");
    process.exit(2);
  }
  await boot();

  const conn = net.connect(SOCK);
  conn.setEncoding("utf8");
  conn.on("connect", () => {
    conn.write(JSON.stringify({ hello: true, pid: process.pid, space: task.spaceId }) + "\n");
  });
  conn.on("error", (e) => {
    process.stderr.write("socket error: " + String(e).slice(0, 200) + "\n");
    process.exit(2);
  });

  let buffer = "";
  let queue = Promise.resolve();
  conn.on("data", (chunk) => {
    buffer += chunk;
    let idx;
    while ((idx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line) continue;
      let req = null;
      try {
        req = JSON.parse(line);
      } catch (e) {
        conn.write(JSON.stringify({ id: null, ok: false, error: "bad json" }) + "\n");
        continue;
      }
      // 串行执行，保证同一页上的动作不会互相插队
      queue = queue.then(async () => {
        const resp = await handle(req);
        if (conn.writable) conn.write(JSON.stringify(resp) + "\n");
      });
    }
  });
}

main().catch((e) => {
  process.stderr.write("bridge fatal: " + String((e && e.message) || e).slice(0, 300) + "\n");
  process.exit(1);
});
