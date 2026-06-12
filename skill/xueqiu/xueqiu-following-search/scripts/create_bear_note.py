#!/usr/bin/env python3
"""
create_bear_note.py - Create a Bear note with title, content, and tags.

Usage:
    python3 create_bear_note.py --title "标题" --text "内容" --tags "标签1,标签2"
    python3 create_bear_note.py --title "标题" --file content.md --tags "标签"
"""

import argparse
import subprocess
import sys
import urllib.parse


def create_note_url(title: str, text: str, tags: str = "", pin: bool = False) -> str:
    params = {
        "title": title,
        "text": text,
        "open_note": "yes",
    }
    if tags:
        params["tags"] = tags
    if pin:
        params["pin"] = "yes"

    query = urllib.parse.urlencode(params)
    return f"bear://x-callback-url/create?{query}"


def main():
    parser = argparse.ArgumentParser(description="Create Bear note")
    parser.add_argument("--title", required=True, help="Note title")
    parser.add_argument("--text", help="Note content (Markdown)")
    parser.add_argument("--file", help="Read content from file instead")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--pin", action="store_true", help="Pin the note")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Error: provide --text or --file", file=sys.stderr)
        sys.exit(1)

    url = create_note_url(args.title, text, args.tags, args.pin)

    if len(url) > 8000:
        print(f"Warning: URL length is {len(url)}, may exceed limit.", file=sys.stderr)
        print("Consider using sqlite3 for long content (see xiongzhangji skill).", file=sys.stderr)

    result = subprocess.run(["open", url], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"OK: Bear note '{args.title}' created.")
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
