#!/usr/bin/env node
/* 采集产物「已入库」校验器（清理临时产物前的操作门 · 2026-09-12 新增）
 *
 * 用途（2026-09-12 用户拍板定位）：采集直接落 post_history、**帖子集不再存 vault 粗制品**，
 *      采集产物 md 只是临时文件——**清理它之前**逐帖确认原文已进 post_history
 *      （url_hash 存在 + content_hash 一致），杜绝「原文没留档就被清」——
 *      这正是 post_history 存在的意义（规则 #41：提炼原文来源 + 避免重采）。
 *
 * 判据：
 *   - 每帖的 url_hash 必须命中 post_history，且 content_hash 与正文 md5 一致
 *   - 标「摘要」的帖按设计不入库（正文残缺，留着下次重采），不计入缺口但会列出
 *   - 博主未建档 / 无 [原文] 链接 的帖列入缺口
 *
 * 用法：
 *   node check-post-history-covered.js <采集产物.md> [...]   # 校验指定文件
 *   node check-post-history-covered.js --dir <临时目录>       # 校验目录下全部采集产物
 * 退出码：0=全部已入库（可安全清理临时产物）/ 1=存在缺口（禁止清理，先补入库）/ 2=用法错误
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const CONSOLE = '/Users/jianglb/Project/investment-console';
const mysql = require(path.join(CONSOLE, 'node_modules', 'mysql2', 'promise'));
const cfg = require(path.join(CONSOLE, 'src', 'config.json'));   // 2026-09-23 仓库归置：config 移入 src/

const md5 = s => crypto.createHash('md5').update(s).digest('hex');

function parsePosts(text, file) {
  const fm = text.match(/^---\n([\s\S]*?)\n---/);
  const author = (fm && (fm[1].match(/^author:\s*"?([^"\n]+)"?/m) || [])[1] || path.basename(file)
    .replace(/^雪球采集-/, '').replace(/-20\d\d年.*$/, '')).trim();
  const out = [];
  for (const b of text.split(/\n(?=## \d+\.\s)/).filter(x => /^## \d+\.\s/.test(x))) {
    const lines = b.split('\n');
    const pubIdx = lines.findIndex(l => /^>\s*发布：/.test(l));
    if (pubIdx < 0) continue;
    const pub = lines[pubIdx];
    const body = lines.slice(1, pubIdx).join('\n').trim();
    const url = (pub.match(/\[原文\]\((https?:\/\/[^)]+)\)/) || [])[1] || '';
    out.push({ url, body, author, isSummary: /\|\s*摘要\s*\|/.test(pub) });
  }
  return out;
}

(async () => {
  const args = process.argv.slice(2);
  let files = args.filter(a => !a.startsWith('--'));
  const dirIdx = args.indexOf('--dir');
  if (dirIdx >= 0) {
    const dir = args[dirIdx + 1];
    files = fs.readdirSync(dir).filter(f => f.endsWith('.md') && !f.startsWith('.')).map(f => path.join(dir, f));
  }
  if (!files.length) { console.error('用法: node check-post-history-covered.js <帖子集.md> [...] | --dir <目录>'); process.exit(2); }

  const conn = await mysql.createConnection({ host: cfg.mysql.host, port: cfg.mysql.port, user: cfg.mysql.user, password: cfg.mysql.password, database: cfg.mysql.database });
  const posts = [];
  const perFile = new Map();
  for (const f of files) {
    if (!fs.existsSync(f)) { console.error('  跳过（不存在）', f); continue; }
    const list = parsePosts(fs.readFileSync(f, 'utf8'), f);
    perFile.set(f, list);
    list.forEach(p => posts.push(p));
  }
  const hashes = [...new Set(posts.filter(p => p.url).map(p => md5(p.url)))];
  const db = new Map();
  for (let i = 0; i < hashes.length; i += 500) {
    const [rows] = await conn.query(
      `SELECT url_hash, content_hash FROM post_history WHERE url_hash IN (${hashes.slice(i, i + 500).map(() => '?').join(',')})`,
      hashes.slice(i, i + 500));
    rows.forEach(r => db.set(r.url_hash, r.content_hash));
  }

  let badFiles = 0, coveredPosts = 0, missing = 0, mismatch = 0, summaries = 0, noUrl = 0;
  for (const [f, list] of perFile) {
    const gaps = [];
    let sum = 0;
    for (const p of list) {
      if (!p.url) { noUrl++; gaps.push('（无 [原文] 链接）'); continue; }
      if (p.isSummary) { summaries++; sum++; continue; }   // 摘要帖按设计不入库
      const h = md5(p.url);
      if (!db.has(h)) { missing++; gaps.push('未入库 ' + p.url); continue; }
      if (db.get(h) !== md5(p.body.replace(/\s+$/, ''))) { mismatch++; gaps.push('正文与库内不一致 ' + p.url); continue; }
      coveredPosts++;
    }
    const ok = gaps.filter(g => !g.startsWith('（无 [原文]')).length === 0;
    if (!ok) badFiles++;
    console.log(`${ok ? '✅' : '❌'} ${path.basename(f)}  帖${list.length} 已留档${list.length - gaps.length}${sum ? ` 摘要帖${sum}` : ''}${ok ? '' : ' 缺口' + gaps.length}`);
    gaps.slice(0, 5).forEach(g => console.log('     ↳', g));
  }
  console.log(`\n合计：文件 ${perFile.size}（缺口文件 ${badFiles}）| 已留档 ${coveredPosts} 帖 | 摘要帖跳过 ${summaries} | 未入库 ${missing} | 正文不一致 ${mismatch} | 无链接 ${noUrl}`);
  await conn.end();
  process.exit(badFiles ? 1 : 0);
})();
