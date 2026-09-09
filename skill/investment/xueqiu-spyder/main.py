import argparse
import datetime
import logging
import re
import sys
import time

import config
from crawler import XueqiuCrawler, CrawlerError
from analyzer import filter_big_v, extract_opinions, summarize_opinions, posts_to_opinions
from report import generate_report, generate_user_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_window(s):
    """解析时间窗参数：YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS → 毫秒时间戳"""
    s = s.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        s += "T00:00:00"
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise SystemExit(f"时间格式错误: {s}（支持 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS）")
    return int(dt.timestamp() * 1000)


def run(symbol, min_reply_count=None, max_pages=None, output_dir=None):
    """主流程：爬取 -> 筛选大V -> 提取观点 -> 生成报告"""
    if min_reply_count is None:
        min_reply_count = config.MIN_REPLY_COUNT
    if max_pages is None:
        max_pages = config.MAX_PAGES
    if output_dir is None:
        output_dir = config.DEFAULT_OUTPUT_DIR

    logger.info(f"开始爬取 {symbol} 的讨论帖...")
    crawler = XueqiuCrawler()

    try:
        all_posts = []
        for page in range(1, max_pages + 1):
            logger.info(f"爬取第 {page}/{max_pages} 页...")
            try:
                posts = crawler.get_stock_posts(symbol, sort="reply", page=page)
            except CrawlerError as e:
                logger.error(f"第 {page} 页爬取失败: {e}")
                break
            if not posts:
                logger.info("没有更多帖子了")
                break
            all_posts.extend(posts)

        logger.info(f"共获取 {len(all_posts)} 条帖子")

        big_v_map = filter_big_v(all_posts, min_reply_count)
        if not big_v_map:
            logger.warning("未找到符合条件的大V")
            return None

        user_posts_map = {}
        for post in all_posts:
            uid = post.get("user_id") or (post.get("user", {}) or {}).get("id")
            if uid and uid in big_v_map:
                user_posts_map.setdefault(uid, []).append(post)

        users_opinions = []
        for uid, user_info in big_v_map.items():
            posts_for_user = user_posts_map.get(uid, [])
            opinions = extract_opinions(posts_for_user, symbol)
            opinions = summarize_opinions(opinions)
            if opinions:
                users_opinions.append((user_info, opinions))
                logger.info(f"大V [{user_info.screen_name}] 提取到 {len(opinions)} 条观点")

        if not users_opinions:
            logger.warning("所有大V均无相关观点")
            return None

        users_opinions.sort(key=lambda x: x[0].followers_count, reverse=True)
        filepath = generate_report(symbol, users_opinions, output_dir)
        logger.info(f"报告已生成: {filepath}")
        return filepath
    finally:
        crawler.close()


def run_user(user_id, max_pages=10, output_dir=None, days=None, column_only=False,
             from_time=None, to_time=None, outfile=None):
    """爬取指定用户的帖子并生成帖子集文件。user_id 可以是数字ID或用户名。
    时间窗：优先 --from/--to 精确窗口；否则 --days 相对窗口（兼容）"""
    if output_dir is None:
        output_dir = config.DEFAULT_OUTPUT_DIR

    crawler = XueqiuCrawler()

    try:
        # 如果不是纯数字，按用户名搜索解析
        if not str(user_id).isdigit():
            logger.info(f"搜索用户: {user_id}")
            user_id, resolved_name = crawler.find_user_id(user_id)
            logger.info(f"已解析: {resolved_name} -> {user_id}")

        logger.info(f"开始爬取用户 {user_id} 的帖子...")

        # 一次导航同时获取用户名和帖子
        screen_name, all_posts = crawler.get_user_all_posts_with_info(
            user_id, max_pages=max_pages
        )
        logger.info(f"用户: {screen_name}，共获取 {len(all_posts)} 条帖子")

        if not all_posts:
            logger.warning("未获取到任何帖子")
            return None

        # 时间窗过滤：置顶帖排除（时间旧且非窗口内容）+ created_at 范围
        if from_time is not None or to_time is not None or days:
            lo = _parse_window(from_time) if from_time else (
                int((time.time() - days * 86400) * 1000) if days else None
            )
            hi = _parse_window(to_time) if to_time else None
            before = len(all_posts)
            all_posts = [
                p for p in all_posts
                if not (p.get("mark") == 1 or p.get("pinned"))  # 置顶帖不纳入窗口
                and p.get("created_at", 0) >= (lo or 0)
                and (hi is None or p.get("created_at", 0) <= hi)
            ]
            window_desc = f"{from_time or ('最近%d天' % days if days else '起')} ~ {to_time or 'now'}"
            logger.info(f"时间窗过滤[{window_desc}]: {before} -> {len(all_posts)} 条（置顶帖已排除）")
            if not all_posts:
                logger.warning("过滤后无帖子")
                return None

        # 仅保留专栏文章
        if column_only:
            before = len(all_posts)
            all_posts = [p for p in all_posts if p.get("is_column")]
            logger.info(f"专栏过滤: {before} -> {len(all_posts)} 条")
            if not all_posts:
                logger.warning("过滤后无专栏文章")
                return None

        # 补全被截断的帖子全文（含详情页精确时间覆盖）
        logger.info("正在获取帖子全文...")
        crawler.enrich_posts_full_text(all_posts)

        # 转为 Opinion 并按时间倒序排列
        opinions = posts_to_opinions(all_posts)
        opinions.sort(key=lambda o: o.created_ts, reverse=True)
        logger.info(f"有效帖子: {len(opinions)} 条")

        filepath = generate_user_report(
            screen_name, user_id, opinions, output_dir, outfile=outfile
        )
        logger.info(f"帖子集已生成: {filepath}")
        return filepath
    finally:
        crawler.close()


def run_search(keyword):
    """搜索雪球用户并打印结果"""
    logger.info(f"搜索用户: {keyword}")
    crawler = XueqiuCrawler()
    try:
        users = crawler.search_user(keyword)
        if not users:
            print("未找到匹配用户")
            return
        print(f"\n找到 {len(users)} 个用户:\n")
        for i, u in enumerate(users, 1):
            uid_str = u.get("uid") or "需解析"
            desc = u.get("desc", "")
            print(f"  {i}. {u['name']}  (ID: {uid_str})  {desc}")
        print()
    finally:
        crawler.close()


def main():
    # 兼容旧用法：如果第一个参数不是 stock/user/search，自动当作 stock 子命令
    if len(sys.argv) > 1 and sys.argv[1] not in ("stock", "user", "search", "-h", "--help"):
        sys.argv.insert(1, "stock")

    parser = argparse.ArgumentParser(description="雪球爬虫工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # stock 子命令
    sp_stock = subparsers.add_parser("stock", help="爬取股票大V观点")
    sp_stock.add_argument("symbol", help="股票代码，如 SH600519、SZ002738")
    sp_stock.add_argument("--min-reply", type=int, default=config.MIN_REPLY_COUNT)
    sp_stock.add_argument("--max-pages", type=int, default=config.MAX_PAGES)
    sp_stock.add_argument("--output", default=config.DEFAULT_OUTPUT_DIR)

    # user 子命令
    sp_user = subparsers.add_parser("user", help="爬取指定用户帖子并生成帖子集")
    sp_user.add_argument("user_id", help="用户ID或用户名（用户名会自动搜索解析）")
    sp_user.add_argument("--max-pages", type=int, default=10)
    sp_user.add_argument("--days", type=int, default=None, help="只保留最近N天的帖子（与 --from 互斥，优先 --from）")
    sp_user.add_argument("--from", dest="from_time", default=None, help="起始时间 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS（对齐 info_cutoff 增量窗口）")
    sp_user.add_argument("--to", dest="to_time", default=None, help="截止时间（默认当前）")
    sp_user.add_argument("--column", action="store_true", help="仅抓取专栏文章")
    sp_user.add_argument("--output", default=config.DEFAULT_OUTPUT_DIR)
    sp_user.add_argument("--outfile", default=None, help="输出文件名（默认 雪球采集-{昵称}-{日期}.md）")

    # search 子命令
    sp_search = subparsers.add_parser("search", help="搜索雪球用户")
    sp_search.add_argument("keyword", help="搜索关键词（用户名）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "stock":
            result = run(args.symbol, args.min_reply, args.max_pages, args.output)
        elif args.command == "user":
            result = run_user(args.user_id, args.max_pages, args.output,
                              getattr(args, 'days', None), getattr(args, 'column', False),
                              getattr(args, 'from_time', None), getattr(args, 'to_time', None),
                              getattr(args, 'outfile', None))
        elif args.command == "search":
            run_search(args.keyword)
            return
        else:
            parser.print_help()
            sys.exit(1)

        if result:
            print(f"\n报告已保存到: {result}")
        else:
            print("\n未生成报告")
            sys.exit(1)
    except CrawlerError as e:
        logger.error(f"爬取失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
