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
 *   {"id":11,"cmd":"handoff","waitMs":900000}       // 把任务空间交给用户（过滑块），等用户交还后回执
 *
 *   **页签策略（2026-09-16 用户口径：随用随关）**：
 *   ① 页面确实开在 ego 里且可见（用户要盯风控），但**不抢焦点**；
 *   ② **工作页一进一出**：临时页用完立刻真关（`close` 直接 `page.close()`），
 *      下一次 `newPage` 再开一张——ego 任务空间有 8 个标签页上限（实测
 *      `Page budget reached (8/8)`），同一时刻只留一张工作页就不会撞顶；
 *   ③ 桥退出（shutdown / SIGTERM / SIGINT）时调 **`task.finish({keep: []})`**：
 *      agent 页签全关、**空间被释放**（回执 `closedSpace: true`）——"用完回收"的正解；
 *      只关页签会留下空空间，越攒越多（2026-09-16 用户指出）。
 *      例外：因「交给用户接管」而中断时不 finish（ego 要求：用户控制中不要 finish）。
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
let handedOff = false;      // 是否正处于「交给用户接管」状态（决定退出时要不要回收）
let task = null;
let workPage = null;                    // 会话内唯一的工作页（用完放回，下次复用）

const net = require("net");

function pageOf(label) {
  const page = pages.get(label || "p1");
  if (!page) throw new Error("unknown page label: " + label);
  return page;
}

async function boot() {
  // SPACE 既可能是数字 id（复用某空间），也可能是名字（新建/按名找）。
  // 2026-09-16 踩坑：一律 Number() 会把名字转成 NaN → "task space not found: NaN"。
  const spaceArg = SPACE == null || SPACE === ""
    ? SPACE_NAME
    : (String(SPACE).trim() !== "" && !isNaN(Number(SPACE)) ? Number(SPACE) : String(SPACE));
  task = await taskSpace(spaceArg);
  // 注册表只装本会话真正在用的页签：ego 的页签编号是**整个浏览器单调递增**的
  // （本次实测跨进程递增到 p15），跨会话残留的旧条目会让 pageOf() 指到别的 space 的页。
  pages.clear();
  workPage = null;
  // 取主页面：**不能假定 p1 一定存在或可用**——2026-09-16 踩坑：`task.page("p1")` 对
  // 一个已被关掉的页**不抛错**，只返回死引用，直到后面 `.url()` 才炸
  //（现象：桥崩在 "page p1 was closed"，Python 侧只看到"启动超时"）。
  // 所以这里用一次轻量探针验活，坏了就新开一张。
  let first = null;
  try {
    const candidate = task.page("p1");
    await candidate.url();            // 探针：死引用在这里就会抛
    first = candidate;
  } catch (e) {
    first = await task.newPage();     // 没有可用 p1 → 自己开一张
    process.stderr.write("[bridge] 空间内没有可用 p1，已新建标签页 " + first.label + "\n");
  }
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

/* 用完回收：**关页签 + 释放空间**。
   用户口径（2026-09-16）：「标签、空间都是的，用完要回收」。
   正确姿势是 ego 的 `task.finish({ keep: [] })`——实测回执
   `{closedSpace: true, closedManagedLabels: [...]}`：agent 页签全关、空间被释放。
   只逐个 close 页签会留下空空间，越攒越多（这正是用户指出来的问题）。
   注意：必须 await（process.exit 不等异步）；交接给用户的途中不回收。 */
async function cleanupOwnPages() {
  if (handedOff) {
    process.stderr.write("[bridge] 处于用户接管中，跳过回收（空间留给用户收尾）\n");
    return;
  }
  try {
    const receipt = await task.finish({ keep: [] });
    process.stderr.write("[bridge] 回收完成: " + JSON.stringify(receipt) + "\n");
  } catch (e) {
    process.stderr.write("[bridge] finish 失败（" + String(e).slice(0, 80) + "），退回逐个关页签\n");
    for (const [label, p] of Array.from(pages.entries())) {
      try { await p.close(); pages.delete(label); } catch (e2) {}
    }
  }
  workPage = null;
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
        // 工作页可能已被上一轮 close 关掉（workPage 仍指向它）——探针验活，死了就重开。
        // 2026-09-16 踩坑：close 后没清 workPage，下一次复用了已关闭的 p2 →
        // 运行时报 "unknown page label: p2"，整批详情页补全失败。
        if (workPage) {
          try {
            await workPage.url();          // 死引用在这里会抛
          } catch (e) {
            pages.delete(workPage.label);
            workPage = null;
          }
        }
        if (!workPage) {
          // 随用随关：这里只负责"要用时开一张"，用完由 close 立刻关（避开 8 页上限）
          workPage = await task.newPage();
          pages.set(workPage.label, workPage);
        }
        return { id, ok: true, result: { label: workPage.label, reused: true } };
      }
      case "goto": {
        const page = pageOf(req.page);
        // 主页面被驱动时也置前（例如同步脚本让主页面跑接口页）
        if (req.page && req.page !== "p1") { try { await page.bringToFront(); } catch (e) {} }
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
        // 2026-09-16 用户口径：「标签最好是随用随关」——所以放回时**立刻真关**，
        // 下次要用再开一张（工作页一进一出，ego 里不留悬挂标签）。
        if (label !== "p1") {
          try { await page.close(); } catch (e) {}
          pages.delete(label);
          if (workPage && workPage.label === label) workPage = null;   // 关掉的是工作页 → 清引用
          return { id, ok: true, result: { closed: true, label } };
        }
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
      case "handoff": {
        // 把任务空间交给用户（滑块/验证要人工过），然后**盯着控制权**：
        // 用户过完验证、控制权回到 agent → 回执 ok，采集方据此重试本页。
        const waitMs = Number(req.waitMs || 900000);
        handedOff = true;
        await task.handOff();
        const deadline = Date.now() + waitMs;
        while (Date.now() < deadline) {
          try {
            await task.waitForControl({ timeout: 5000, interval: 1000 });
            // 控制权回来了：显式认领一次，避免"控制权已回但 space 仍标记为用户所有"
            let reclaimed = false;
            try {
              const again = await claimTaskSpace(task.spaceId);
              reclaimed = true;
              task = again;
            } catch (e) { /* 已经在 agent 名下时 claim 会失败，属正常 */ }
            handedOff = false;      // 控制权已收回，恢复正常回收行为
            return {
              id, ok: true,
              result: { regained: true, reclaimed,
                        waitedMs: waitMs - (deadline - Date.now()) },
            };
          } catch (e) {
            // waitForControl 超时（用户还没好，或**仍由用户持有**）：继续等
          }
        }
        return { id, ok: false,
                 error: "handoff 超时：用户未在 " + Math.round(waitMs / 1000) + " 秒内交还控制权" };
      }
      case "shutdown": {
        // 用完回收：关页签 + 释放空间（用户 2026-09-16 要求）
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
