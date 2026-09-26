"""流式采集（关注/热门时间线）——feed 模式，2026-09-26 实测定型。

与 user 模式（逐博主主页翻页）的关系：feed 是**日常增量缺省路径**（一次会话覆盖全部
已关注博主，风控暴露最小），user 模式保留给首采/深窗口/补漏。断点不是逐博主
info_cutoff，而是**流位置书签**（~/.cache/xueqiu-spyder/feed-state.json）。

机制要点（2026-09-26 实测，改前先读）：
- **切 tab**：桥新开会话默认落「热门」，关注流必须显式点「关注」tab。
- **展开控件**：`a.timeline__expand__control`——textContent 带不可见 iconfont 图形字符，
  按 textContent==='展开' 匹配永远 0 命中，须按类名或 innerText 匹配。
- **展开要 dwell**：handler 进视口才惰性挂载，scrollIntoView 后停 ~1s 再点才生效；
  380-450ms 就点全部落空。点完回读正文验证，失败换候选重试一次。
- **计数在流内**：`.timeline__item__ft` 三个 a.timeline__item__control 依次
  转发/讨论/赞——数字>0 显示数字，=0 显示标签。
- **引用卡**：`.timeline__item__forward__content` 是正文块的**兄弟节点**（转帖引用），
  回复帖同名元素装的是对话预览——回复帖（正文以「回复@」开头）不得拼引用卡。
- **时间**：流内相对时间锚定采集瞬间换算绝对时间；「修改于」= 编辑时间非首发时间，
  标记（修改于·推算）。例外帖（自身专栏/展开失败）走详情页拿权威时间与全文。
- **风控**：例外 URL 节流 2.6-3.4s、连续 3 次失败熔断；流会话本身是自然浏览形态。

退出码：0=产出 / 2=窗口内无帖 / 3=书签未翻到（滚动地板/上限，禁止写断点）/ 1=失败。
"""
import json
import os
import random
import re
import time
import urllib.request
from datetime import datetime, timedelta

import ego_browser

N_TARGET_DEFAULT = 50
PACE = (2.6, 3.4)          # 例外详情页节流
BREAK_N = 3
MAX_SCROLL = 60            # 滚动步数硬上限（≈500 条），超出按「书签未翻到」处理
STATE_PATH = os.path.expanduser("~/.cache/xueqiu-spyder/feed-state.json")
DASHBOARD = "http://127.0.0.1:8698"

# ── 注入页面的 JS（均已实测）─────────────────────────────────────────
CLICK_TAB_JS = r"""
(name) => {
  for (const bar of [...document.querySelectorAll('div,nav,ul')]) {
    const f = [...bar.querySelectorAll('*')].find(c => c.textContent.trim() === name && c.children.length === 0);
    if (f && [...bar.parentElement.querySelectorAll('*')].some(c => c.textContent.trim() === '7x24' || c.textContent.trim() === '自选')) {
      f.click(); return true;
    }
  }
  return false;
}
"""
ITEM_COUNT_JS = "() => document.querySelectorAll('.timeline__item').length"
SCROLL_JS = "() => { window.scrollBy(0, 2600); return window.scrollY; }"
OLDEST_LABEL_JS = r"""
() => {
  const items = [...document.querySelectorAll('.timeline__item')];
  if (!items.length) return null;
  const t = (items[items.length - 1].querySelector('.date-and-source') || {}).innerText || '';
  return t.trim();
}
"""
EXPAND_JS = r"""
async (maxItems) => {
  let ok = 0;
  for (const it of [...document.querySelectorAll('.timeline__item')]) {
    if (ok >= maxItems) break;
    const content = it.querySelector('.timeline__item__content');
    if (!content) continue;
    if (!((content.innerText || '').includes('展开'))) continue;
    const btn = it.querySelector('a.timeline__expand__control') ||
                [...content.querySelectorAll('a,span')].find(e => {
                  const t = (e.innerText || '').trim();
                  return t === '展开' || t === '展开全文';
                });
    if (!btn) continue;
    for (let attempt = 0; attempt < 2; attempt++) {
      btn.scrollIntoView({ block: 'center' });
      await new Promise(r => setTimeout(r, attempt === 0 ? 1000 : 1300));
      btn.click();
      await new Promise(r => setTimeout(r, 450));
      if (!((content.innerText || '').includes('展开'))) { ok++; break; }
    }
  }
  return { ok };
}
"""
FEED_JS = r"""
() => {
  const num = (t) => /^\d+$/.test(t) ? parseInt(t, 10) : 0;
  const rows = [];
  for (const it of [...document.querySelectorAll('.timeline__item')]) {
    const nameA = it.querySelector('.user-name');
    const content = it.querySelector('.timeline__item__content');
    const permA = it.querySelector('a[href].date-and-source');
    const timeA = it.querySelector('.date-and-source');
    if (!permA) continue;
    const controls = [...it.querySelectorAll('.timeline__item__ft a.timeline__item__control')]
      .slice(0, 3).map(a => (a.querySelector('span:last-child') || a).innerText.trim());
    const ctext = (content ? content.innerText : '');
    let quoted = null;
    const fwd = it.querySelector('.timeline__item__forward__content');
    if (fwd) {
      const anchors = [...fwd.querySelectorAll('a[href]')];
      const qLink = anchors.map(a => a.getAttribute('href')).find(h => /^\/(\d+|[\w-]+)\/\d+$/.test(h || ''));
      const wrap = fwd.parentElement && fwd.parentElement !== it ? fwd.parentElement : fwd;
      const wrapTxt = wrap.innerText || '';
      const lines = wrapTxt.split('\n').map(s => s.trim()).filter(Boolean);
      const qAuthor = (lines.find(l => /^@.+[:：]$/.test(l)) || lines.find(l => /^@/.test(l)) || '').replace(/[:：]\s*$/, '');
      const titleA = anchors.find(a => a.getAttribute('href') === qLink && (a.innerText || '').trim().length >= 6);
      const footLine = [...lines].reverse().find(l => /·\s*转发\s*\d+/.test(l)) || '';
      const fm = /((?:昨天|今天)?\s*\d+\s*(?:分钟|小时|天)前|\d{2}-\d{2}\s*\d{2}:\d{2})\s*·\s*转发\s*(\d+)\s*·\s*讨论\s*(\d+)\s*·\s*赞\s*(\d+)/.exec(footLine) || [];
      quoted = {
        url: qLink || null,
        author: qAuthor || null,
        title: titleA ? titleA.innerText.trim() : null,
        isColumn: wrapTxt.includes('专栏'),
        time: fm[1] || '',
        counts: [parseInt(fm[2] || 0, 10), parseInt(fm[3] || 0, 10), parseInt(fm[4] || 0, 10)],
        lead: lines.filter(l => l !== footLine && l !== qAuthor && l !== (titleA ? titleA.innerText.trim() : '\u0000'))
                   .join('\n').slice(0, 1200),
      };
    }
    rows.push({
      href: permA.getAttribute('href'),
      author: nameA ? nameA.innerText.trim() : null,
      timeLabel: timeA ? timeA.innerText.trim() : null,
      column: !!it.querySelector('.timeline__item__title'),
      trunc: /展开/.test(ctext),
      counts: [num(controls[0] || ''), num(controls[1] || ''), num(controls[2] || '')],
      quoted,
      text: ctext.slice(0, 20000),
    });
  }
  return { now: Date.now(), rows };
}
"""
DETAIL_JS = r"""
() => {
  const art = document.querySelector('.article__bd');
  const bodyTxt = document.body.innerText || '';
  const blocked = /滑动|安全验证|captcha|访问验证/i.test(bodyTxt.slice(0, 3000));
  const head = (bodyTxt.match(/(发布于|修改于)\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})/) || []);
  return {
    blocked,
    timeRaw: head.length ? head[2] + ' ' + head[3] : '',
    edit: head.length ? head[1] : null,
    content: art ? (art.innerText || '').slice(0, 20000) : null,
  };
}
"""

# ── 文本清洗 ─────────────────────────────────────────────────────────

def clean_feed(t):
    t = (t or "").replace("\u00a0", " ").strip()
    for _ in range(3):
        t = re.sub(r"(收起|展开|查看对话|查看图片)\s*$", "", t).strip()
    return t


def tidy_article(t):
    t = (t or "").strip()
    t = re.sub(r"(收起|展开|查看对话|查看图片)\s*$", "", t).strip()
    t = re.sub(r"\s*·\s*转发\s*\d+\s*·\s*讨论\s*\d+\s*·\s*赞\s*\d+\s*$", "", t).strip()
    t = re.sub(r"\n([，。、；：）」！？])", r"\1", t)
    t = re.sub(r"([，、；：）」！？])\n(?!\n)", r"\1", t)
    t = re.sub(r"([（「])\n", r"\1", t)
    return t


def clean_quote(t):
    t = tidy_article(t)
    t = re.sub(r"\s*(昨天|今天)?\s*\d{1,2}:\d{2}\s*(·\s*转发\s*\d+\s*·\s*讨论\s*\d+\s*·\s*赞\s*\d+)?\s*$", "", t).strip()
    t = re.sub(r"(\d+\s*(分钟|小时|天)前)\s*$", "", t).strip()
    t = re.sub(r"^(?:专栏|：+|:+)\s*", "", t).strip()
    return t


def first_sentence(t):
    t = (t or "").strip()
    m = re.match(r"^(.*?[。！？])", t, re.S)
    return m.group(1).strip() if (m and m.group(1).strip()) else t[:30]


def derive_time(label, anchor_ms):
    """流内相对时间 → 绝对 datetime（锚定采集瞬间）。返回 (datetime, edited:bool) 或 (None, False)。"""
    if not label:
        return None, False
    edited = "修改于" in label
    label = label.replace("修改于", "").strip()
    now = datetime.fromtimestamp(anchor_ms / 1000)
    m = re.search(r"(\d+)\s*分钟前", label)
    if m:
        return now - timedelta(minutes=int(m.group(1))), edited
    m = re.search(r"(\d+)\s*小时前", label)
    if m:
        return now - timedelta(hours=int(m.group(1))), edited
    m = re.search(r"(昨天|今天)\s*(\d{1,2}):(\d{2})", label)
    if m:
        d = now.date() - timedelta(days=1 if m.group(1) == "昨天" else 0)
        return datetime(d.year, d.month, d.day, int(m.group(2)), int(m.group(3))), edited
    m = re.search(r"(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", label)
    if m:
        dt = datetime(now.year, int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        if dt > now:                      # 跨年：12-31 的帖在 1 月看到
            dt = dt.replace(year=now.year - 1)
        return dt, edited
    return None, False


def label_older_than(label, anchor_ms, since_dt):
    dt, _ = derive_time(label, anchor_ms)
    return dt is not None and dt <= since_dt


def load_tracked():
    """看板博主清单（uid → 昵称）；服务不可用返回 None（不过滤，交给入库侧跳过）"""
    try:
        with urllib.request.urlopen(DASHBOARD + "/api/bloggers/live", timeout=3) as r:
            data = json.loads(r.read().decode("utf-8"))
        bloggers = data.get("data") if isinstance(data, dict) else data
        m = {}
        for b in bloggers or []:
            xid = str(b.get("xueqiuId") or "").strip()
            if xid:
                m[xid] = b.get("name")
        return m or None
    except Exception:
        return None


def load_bookmark(tab):
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh).get(tab)
    except Exception:
        return None


def save_bookmark(tab, iso):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    state = {}
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            state = json.load(fh)
    except Exception:
        pass
    state[tab] = iso
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)


# ── 主流程 ───────────────────────────────────────────────────────────

def run_feed(tab="follow", limit=N_TARGET_DEFAULT, since=None, output_dir=None,
             outfile=None, filter_mode="auto"):
    import logging
    logger = logging.getLogger(__name__)
    if output_dir is None:
        output_dir = os.path.expanduser("~/.cache/xueqiu-spyder/out")
    since_dt = None
    if since:
        since_dt = datetime.strptime(since.replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S")
    elif tab == "follow":
        bm = load_bookmark(tab)
        if bm:
            since_dt = datetime.strptime(bm[:19], "%Y-%m-%d %H:%M:%S")
            logger.info("流断点书签: %s（上次采集起点之后的内容为本轮窗口）", bm)

    tracked = None
    if filter_mode == "on" or (filter_mode == "auto" and tab == "follow"):
        tracked = load_tracked()
        logger.info("看板博主过滤: %s", f"{len(tracked)} 位" if tracked else "不可用（不过滤，未建档帖由入库侧跳过）")

    b = ego_browser.EgoBridge()
    b.start()
    anchor_ms, raw = 0, []
    try:
        p = b.main_page
        try:
            p.wait_for_selector(".timeline__item", timeout=10000)
        except Exception:
            time.sleep(4)
        tab_name = {"follow": "关注", "hot": "热门"}.get(tab, tab)
        p.evaluate(CLICK_TAB_JS, tab_name)
        time.sleep(2.5)
        # 滚动：凑 limit 且（有书签时）翻到书签；stale×3 或步数上限 → 可能书签未翻到
        stale, steps, reached = 0, 0, since_dt is None
        while steps < MAX_SCROLL:
            n = p.evaluate(ITEM_COUNT_JS, None)
            if n >= limit and (reached or since_dt is None):
                break
            if since_dt is not None and n > 0:
                oldest = p.evaluate(OLDEST_LABEL_JS, None)
                if label_older_than(oldest, anchor_ms if anchor_ms else time.time() * 1000, since_dt):
                    reached = True
                    if n >= limit:
                        break
            before = n
            p.evaluate(SCROLL_JS, None)
            steps += 1
            time.sleep(1.2)
            if p.evaluate(ITEM_COUNT_JS, None) <= before:
                stale += 1
                if stale >= 3:
                    break
            else:
                stale = 0
        if since_dt is not None and not reached:
            oldest = p.evaluate(OLDEST_LABEL_JS, None)
            reached = label_older_than(oldest, time.time() * 1000, since_dt)

        # 流内展开（视口 dwell）
        exp = p.evaluate(EXPAND_JS, min(limit + 12, 60))
        time.sleep(1.0)
        res = p.evaluate(FEED_JS, None)
        anchor_ms, raw = res["now"], res["rows"]
        logger.info("载入 %s 条，流内展开 %s 条，滚动 %s 步，书签已翻到: %s",
                    len(raw), exp.get("ok", 0), steps, reached if since_dt else "n/a")
    finally:
        b.stop()

    # 去重 + 窗口过滤（书签 30 分钟重叠容差）+ 博主过滤
    seen, rows = set(), []
    dropped_untracked = 0
    for r in raw:
        if r["href"] in seen:
            continue
        seen.add(r["href"])
        if since_dt:
            dt, _ = derive_time(r["timeLabel"], anchor_ms)
            if dt and dt < since_dt - timedelta(minutes=30):
                continue
        if tracked is not None:
            uid = (re.match(r"^/(\d+)/", r["href"]) or [None, None])[1]
            if uid and uid not in tracked:
                dropped_untracked += 1
                continue
        rows.append(r)
    rows = rows[:limit]
    if since_dt is not None and not reached:
        print("流书签未翻到（滚动地板/步数上限）：不可写断点，须重跑或走逐博主兜底")
        return "__NO_WINDOW_REACHED__"
    if not rows:
        print("窗口内无新帖（流内未见到书签之后的帖子）")
        return "__NO_NEW_POSTS__"

    # 例外帖：自身专栏 / 展开失败 → 详情页
    todo = [r for r in rows if r["column"] or r["trunc"]]
    logger.info("例外帖 %s 条（专栏/展开失败）→ 详情页补全", len(todo))
    if todo:
        b = ego_browser.EgoBridge()
        b.start()
        p2 = b.new_page()
        fails = 0
        try:
            for r in todo:
                try:
                    p2.goto("https://xueqiu.com" + r["href"])
                    time.sleep(1.2 + random.random() * 0.5)
                    d = p2.evaluate(DETAIL_JS, None)
                    if d.get("blocked"):
                        raise RuntimeError("WAF 滑块/安全验证")
                    if not d.get("content"):
                        time.sleep(2.5)
                        d = p2.evaluate(DETAIL_JS, None)
                    if not d.get("content"):
                        raise RuntimeError("详情页无正文")
                    r["detail"] = d
                    fails = 0
                except Exception as e:
                    r["detail_err"] = str(e)[:120]
                    fails += 1
                    logger.warning("例外帖失败 %s %s", r["href"], r["detail_err"])
                    if fails >= BREAK_N:
                        logger.error("连续 %s 次失败熔断，余下按「摘要」处理", fails)
                        break
                time.sleep(random.uniform(*PACE))
        finally:
            p2.close()
            b.stop()

    # 组装帖子集（多博主格式，规范见 post-fetch→xueqiu-spyder references/output-format.md）
    now_dt = datetime.fromtimestamp(anchor_ms / 1000)
    out_rows, n_full = [], 0
    for i, r in enumerate(rows, 1):
        d = r.get("detail")
        own = clean_feed(r["text"])
        body, complete, reason = own, "全文", ""
        if r["column"]:
            if d and d.get("content"):
                body = tidy_article(d["content"])
            else:
                complete, reason = "摘要", "专栏未取到全文"
        elif r["trunc"]:
            if d and d.get("content"):
                body = tidy_article(d["content"])
            else:
                complete, reason = "摘要", "流内展开失败"
        elif r.get("quoted") and r["quoted"].get("text") and r["quoted"].get("url") \
                and not own.startswith("回复@"):
            qt = clean_quote(r["quoted"]["text"])
            if qt and not (r["quoted"].get("title") and r["quoted"]["title"][:8] in body):
                body = own + "\n\n" + qt
        # 时间：详情页权威 > 流内推算
        tm, tmark, edited = "", "", False
        if d and d.get("timeRaw"):
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}:\d{2})", d["timeRaw"])
            if m:
                tm = f"{m.group(1)}年{m.group(2)}月{m.group(3)}日 {m.group(4)}"
                edited = d.get("edit") == "修改于"
        if not tm:
            dt, ed = derive_time(r["timeLabel"], anchor_ms)
            if dt:
                tm = f"{dt.year}年{dt.month:02d}月{dt.day:02d}日 {dt.strftime('%H:%M')}"
                tmark = "（修改于·推算）" if ed else "（流内推算）"
        if not tm:
            complete, reason = "摘要", "时间不可解析"
            tm = "1970年01月01日 00:00"
        # 引用卡结构化 → 回复内容块（正文已内联则跳过）
        q = r.get("quoted")
        if q and q.get("url") and not own.startswith("回复@"):
            already = bool(q.get("title") and q["title"][:8] in body)
            if not already:
                kind = "专栏" if q.get("isColumn") else "帖子"
                head = f"> 回复内容：{q.get('author') or '被引作者'} 的{kind}"
                if q.get("title"):
                    head += f"《{q['title']}》"
                parts = ([q.get("time")] if q.get("time") else []) + \
                    [f"转发 {q['counts'][0]}", f"讨论 {q['counts'][1]}", f"赞 {q['counts'][2]}"]
                meta = " · ".join(p for p in parts if p)
                if meta:
                    head += f"（{meta}）"
                block = [head, f"> 被引原文：https://xueqiu.com{q['url']}"]
                lead = (q.get("lead") or "").strip()
                if q.get("title"):
                    lead = lead.replace(q["title"], "", 1).strip()
                lead = re.sub(r"^(?:专栏|：+|:+)\s*", "", lead).strip()
                if lead:
                    block.insert(1, f"> 导语：{lead}")
                body = (body + "\n\n" + "\n".join(block)).strip()
        title = first_sentence(body)
        if r["column"] and body:
            m = re.match(r"^([^\n，。]{4,60})", body)
            title = m.group(1) if m else title
        is_reply = ("回复@" in body or "//@" in body) or bool(q and q.get("url"))
        form = "专栏" if r["column"] else ("回复" if is_reply else ("短文" if len(body) < 200 else "长文"))
        if complete == "全文":
            n_full += 1
        c = r["counts"]
        author = r.get("author") or "Unknown"
        pub = (f"> 发布：{tm}{tmark}{'（修改于）' if edited else ''} | 形态：{form} | 作者：{author}"
               f" | 转发 {c[0]} | 回复 {c[1]} | 点赞 {c[2]}"
               f" | {complete}{' | ' + reason if reason else ''}"
               f" | [原文](https://xueqiu.com{r['href']})")
        out_rows.append((i, title, body, pub, author))

    status = "待提炼" if n_full == len(out_rows) else "待提炼-含摘要"
    n_author = len({x[4] for x in out_rows})
    tab_desc = {"follow": "关注流", "hot": "热门流"}.get(tab, tab)
    lines = [
        "---",
        f'title: "雪球帖子采集：{tab_desc}（多博主） {now_dt.year}年{now_dt.month}月{now_dt.day}日"',
        'source: "https://xueqiu.com/"',
        f'author: "{tab_desc} {n_author} 位博主"',
        f'date: "{now_dt.year}年{now_dt.month}月{now_dt.day}日"',
        f'recorded: "{now_dt.year}年{now_dt.month}月{now_dt.day}日"',
        'type: "帖子集"',
        f'status: "{status}"',
        "tags: []",
        "---",
        "",
    ]
    for i, title, body, pub, author in out_rows:
        lines += [f"## {i}. {title}", "", body, "", pub, "", "---", ""]
    os.makedirs(output_dir, exist_ok=True)
    outfile = outfile or f"雪球采集-{tab_desc}-{now_dt:%Y年%m月%d日}.md"
    path = os.path.join(output_dir, outfile)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"帖子集已生成: {path}")
    print(f"统计: {len(out_rows)} 帖（全文 {n_full} / 摘要 {len(out_rows) - n_full}），博主 {n_author} 位"
          + (f"，非看板博主过滤 {dropped_untracked} 条" if dropped_untracked else ""))
    # 成功产出 → 写流断点书签（本轮起点）
    save_bookmark(tab, datetime.fromtimestamp(anchor_ms / 1000).strftime("%Y-%m-%dT%H:%M:%S"))
    return path
