#!/usr/bin/env python3
"""
Fetch Xueqiu post and comments, format as Q&A article Markdown.

Usage:
    python3 fetch_xueqiu.py <post_url> <output_file> [min_likes]

Example:
    python3 fetch_xueqiu.py "https://xueqiu.com/2292705444/358275118" /tmp/article.md 3
"""

import sys
import json
import re
import html
import subprocess
import os

def get_cookie():
    """Fetch Xueqiu cookie by visiting homepage."""
    subprocess.run(
        ["curl", "-s", "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         "-c", "/tmp/xq_cookies.txt", "https://xueqiu.com/"],
        capture_output=True
    )

def fetch_json(url):
    """Fetch JSON from Xueqiu API."""
    result = subprocess.run(
        ["curl", "-s", "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         "-b", "/tmp/xq_cookies.txt", url],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def clean_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text)

def parse_url(url):
    """Extract user_id and post_id from Xueqiu URL."""
    m = re.search(r'xueqiu\.com/(\d+)/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid Xueqiu URL: {url}")
    return m.group(1), m.group(2)

def fetch_all_comments(post_id):
    """Fetch all comments with pagination."""
    all_comments = {}
    page = 1
    while True:
        data = fetch_json(f"https://xueqiu.com/statuses/comments.json?id={post_id}&count=100&page={page}")
        comments = data.get('comments', [])
        if not comments:
            break
        for c in comments:
            cid = c['id']
            all_comments[cid] = {
                'id': cid,
                'name': c['user']['screen_name'],
                'text': clean_html(c.get('text', '')),
                'likes': c.get('like_count', 0),
                'reply_to_cid': c.get('in_reply_to_comment_id'),
                'reply_screen': c.get('reply_screenName', ''),
                'time': c.get('timeBefore', ''),
                'ip': c.get('ip_location', '') or c['user'].get('province', ''),
                'user_id': c['user']['id']
            }
        if len(comments) < 100:
            break
        page += 1
    return all_comments

def build_reply_chains(comments, author_id, min_likes=3):
    """Build reply chains: find which comments are replies to which."""
    # Build reply target lookup
    reply_targets = {}  # cid -> list of replies
    for c in comments.values():
        if c['reply_to_cid']:
            tid = c['reply_to_cid']
            if tid not in reply_targets:
                reply_targets[tid] = []
            reply_targets[tid].append(c)

    # Sort replies by likes for each target
    for tid in reply_targets:
        reply_targets[tid].sort(key=lambda x: -x['likes'])

    return reply_targets

def format_article(title, tags, main_post, comments, reply_targets, author_id, author_name, min_likes=3):
    """Format the complete article as Markdown."""
    user_id = main_post['user_id']
    post_url = f"https://xueqiu.com/{user_id}/{main_post['post_id']}"
    user_url = f"https://xueqiu.com/{user_id}"

    lines = []
    lines.append(f"# {title}")
    lines.append(f"#雪球分析 {tags}")
    lines.append("")

    # Main post with direct replies
    lines.append(f"**[{author_name}]({user_url})** [{main_post['time']}· {main_post['source']}]({post_url})")
    lines.append(main_post['text'])

    # Find top-level comments (not replies to other comments)
    top_level = []
    replied_cids = set()
    for c in comments.values():
        if c['reply_to_cid'] is None or c['reply_to_cid'] == -1:
            top_level.append(c)

    # Also find replies that target the main post directly
    # (these have reply_to_cid but the target is the main post, not another comment)
    top_level.sort(key=lambda x: -x['likes'])

    # Direct replies to main post (attached with >)
    direct_replies = [c for c in top_level if c['likes'] >= min_likes]

    # First segment: main post + its first high-liked reply
    if direct_replies:
        first = direct_replies[0]
        lines.append(f"> [{first['name']}]({user_url}/{first['user_id']}) {first['time']}· {first['ip']}· {first['likes']}赞")
        for text_line in first['text'].split('\n'):
            lines.append(f"> {text_line}")
        # Add replies to this first comment
        if first['id'] in reply_targets:
            for r in reply_targets[first['id']]:
                if r['likes'] >= min_likes:
                    is_author = r['user_id'] == int(author_id)
                    prefix = f"> **[{r['name']}]({user_url})**" if is_author else f"> [{r['name']}]({user_url}/n/{r['name']})"
                    lines.append(f"{prefix} {r['time']}· {r['likes']}赞")
                    for text_line in r['text'].split('\n'):
                        lines.append(f"> {text_line}")

    lines.append("---")

    # Remaining top-level comments (standalone or with their replies)
    for c in direct_replies[1:]:
        # The comment itself (被回复内容 - no >)
        lines.append(f"[{c['name']}]({user_url}/n/{c['name']}) {c['time']}· {c['likes']}赞")
        lines.append(c['text'])

        # Replies to this comment
        if c['id'] in reply_targets:
            for r in reply_targets[c['id']]:
                if r['likes'] >= min_likes:
                    is_author = r['user_id'] == int(author_id)
                    prefix = f"> **[{r['name']}]({user_url})**" if is_author else f"> [{r['name']}]({user_url}/n/{r['name']})"
                    reply_to = f"回复{c['name']}" if not r['text'].startswith('回复') else ''
                    likes_str = f"· {r['likes']}赞" if r['likes'] > 0 else ''
                    lines.append(f"{prefix} {reply_to}{likes_str}")
                    for text_line in r['text'].split('\n'):
                        lines.append(f"> {text_line}")

        lines.append("---")

    # Author standalone replies (high-liked author replies to low-liked comments)
    author_replies = []
    for c in comments.values():
        if c['user_id'] == int(author_id) and c['reply_to_cid'] and c['likes'] >= min_likes:
            target_cid = c['reply_to_cid']
            if target_cid in comments:
                target = comments[target_cid]
                if target['likes'] < min_likes:  # Target not already shown
                    author_replies.append((target, c))

    for target, reply in sorted(author_replies, key=lambda x: -x[1]['likes']):
        lines.append(f"[{target['name']}]({user_url}/n/{target['name']}) {target['time']}")
        lines.append(target['text'])
        lines.append(f"> **[{author_name}]({user_url})** 回复{target['name']}· {reply['likes']}赞")
        reply_text = reply['text']
        # Clean up "回复@xxx: " prefix if present
        reply_text = re.sub(r'^回复@\w+:\s*', '', reply_text)
        for text_line in reply_text.split('\n'):
            lines.append(f"> {text_line}")
        lines.append("---")

    # Remove trailing ---
    if lines and lines[-1] == "---":
        lines.pop()

    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 fetch_xueqiu.py <post_url> <output_file> [min_likes]")
        sys.exit(1)

    post_url = sys.argv[1]
    output_file = sys.argv[2]
    min_likes = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    user_id, post_id = parse_url(post_url)

    print(f"Fetching cookie...")
    get_cookie()

    print(f"Fetching main post {post_id}...")
    post_data = fetch_json(f"https://xueqiu.com/statuses/show.json?id={post_id}")
    main_post = {
        'text': clean_html(post_data.get('text', '')),
        'time': post_data.get('timeBefore', ''),
        'source': post_data.get('source', ''),
        'user_id': user_id,
        'post_id': post_id
    }
    author_name = post_data.get('user', {}).get('screen_name', 'Unknown')

    print(f"Fetching comments...")
    comments = fetch_all_comments(post_id)
    print(f"Found {len(comments)} comments")

    reply_targets = build_reply_chains(comments, user_id, min_likes)

    # Generate title from author name + topic
    title = f"{author_name}问答"

    print(f"Formatting article (min likes: {min_likes})...")
    article = format_article(
        title=title,
        tags="",
        main_post=main_post,
        comments=comments,
        reply_targets=reply_targets,
        author_id=user_id,
        author_name=author_name,
        min_likes=min_likes
    )

    with open(output_file, 'w') as f:
        f.write(article)

    print(f"Article saved to {output_file} ({len(article)} chars)")

if __name__ == "__main__":
    main()
