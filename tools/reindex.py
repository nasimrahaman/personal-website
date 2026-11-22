#!/usr/bin/env python3
"""Rebuild the lists of posts, the feed and the sitemap from the pages themselves.

    python3 tools/reindex.py

Every folder in docs/writing/ that holds an index.html is a post. Its title,
date, kind and description are read from the <meta> tags in its <head>, so a
post is published by adding the folder and running this, and nothing else needs
to be edited by hand. A post marked <meta name="robots" content="noindex"> is a
draft and is left out. The date is YYYY-MM-DD, or YYYY-MM when only the month
is known.

The script rewrites five things: the rows between the "posts" comments in
docs/index.html (the newest few) and in docs/writing/index.html (all of them),
docs/feed.xml, the data between the "data" comments in the <head> of each post
(its title, date and author in the form search engines read), and
docs/sitemap.xml, which lists every page in docs/ that is not marked noindex.
"""
import datetime
import html
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = "https://nasimrahaman.com"
AUTHOR = "Nasim Rahaman"
ON_HOME = 5

DATE = re.compile(r"\d{4}-\d{2}(-\d{2})?")
LISTS = re.compile(r"^(?P<indent>[ \t]*)(?P<open><!-- posts\b.*?-->)\n.*?^[ \t]*<!-- /posts -->\n", re.S | re.M)
DATA = re.compile(r"^(?P<indent>[ \t]*)(?P<open><!-- data\b.*?-->)\n.*?^[ \t]*<!-- /data -->\n", re.S | re.M)


class Head(HTMLParser):
    """Collects the name (or property) and content of every <meta> tag."""

    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = attrs.get("name") or attrs.get("property")
        if tag == "meta" and key:
            self.meta[key] = attrs.get("content", "")


def read(folder):
    """The facts about one post, or None if it is a draft."""
    head = Head()
    head.feed((folder / "index.html").read_text(encoding="utf-8"))
    meta = head.meta
    if "noindex" in meta.get("robots", ""):
        return None
    missing = [key for key in ("og:title", "description", "date", "kind") if not meta.get(key)]
    if missing:
        sys.exit(f"{folder.name}: missing <meta> for {', '.join(missing)}")
    # The lists show the date as the post gives it. The feed and the order of the
    # lists need a full date, so a month stands for its first day there.
    date = meta["date"]
    day = date if len(date) == 10 else f"{date}-01"
    try:
        if not DATE.fullmatch(date):
            raise ValueError
        datetime.date.fromisoformat(day)
    except ValueError:
        sys.exit(f"{folder.name}: the date {date!r} is not YYYY-MM-DD or YYYY-MM")
    return {
        "path": folder / "index.html",
        "url": f"/writing/{folder.name}/",
        "title": meta["og:title"],
        "summary": meta["description"],
        "date": date,
        "day": day,
        "kind": meta["kind"],
    }


def row(post, indent):
    lines = [
        "<li>",
        f'  <a href="{post["url"]}">',
        f'    <span class="key"><time datetime="{post["date"]}">{post["date"]}</time></span>',
        f'    <span class="value">{html.escape(post["title"])}</span>',
        f'    <span class="note">{html.escape(post["kind"])}</span>',
        "  </a>",
        "</li>",
    ]
    return "".join(f"{indent}{line}\n" for line in lines)


def relist(path, posts):
    text = path.read_text(encoding="utf-8")
    if not LISTS.search(text):
        sys.exit(f"{path.relative_to(ROOT)}: no <!-- posts --> … <!-- /posts --> to fill")

    def fill(match):
        indent = match["indent"]
        rows = "".join(row(post, indent) for post in posts)
        return f"{indent}{match['open']}\n{rows}{indent}<!-- /posts -->\n"

    path.write_text(LISTS.sub(fill, text), encoding="utf-8")


def feed(posts):
    updated = posts[0]["day"] if posts else datetime.date.today().isoformat()
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{AUTHOR}</title>",
        f"  <id>{SITE}/</id>",
        f'  <link href="{SITE}/" />',
        f'  <link rel="self" href="{SITE}/feed.xml" />',
        f"  <updated>{updated}T00:00:00Z</updated>",
        f"  <author><name>{AUTHOR}</name></author>",
    ]
    for post in posts:
        lines += [
            "  <entry>",
            f"    <title>{html.escape(post['title'])}</title>",
            f"    <id>{SITE}{post['url']}</id>",
            f'    <link href="{SITE}{post["url"]}" />',
            f"    <published>{post['day']}T00:00:00Z</published>",
            f"    <updated>{post['day']}T00:00:00Z</updated>",
            f"    <summary>{html.escape(post['summary'])}</summary>",
            "  </entry>",
        ]
    lines += ["</feed>", ""]
    (DOCS / "feed.xml").write_text("\n".join(lines), encoding="utf-8")


def describe(post):
    """Write into a post's <head> what it is, when it is from and who wrote it."""
    path = post["path"]
    text = path.read_text(encoding="utf-8")
    if not DATA.search(text):
        sys.exit(f"{path.relative_to(ROOT)}: no <!-- data --> … <!-- /data --> in its <head> to fill")
    facts = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post["summary"],
        "datePublished": post["date"],
        "url": SITE + post["url"],
        "mainEntityOfPage": SITE + post["url"],
        "inLanguage": "en",
        "author": {"@type": "Person", "@id": f"{SITE}/#me", "name": AUTHOR, "url": f"{SITE}/"},
    }
    # "<" is written as an escape so that nothing in a title can end the script.
    written = json.dumps(facts, indent=2, ensure_ascii=False).replace("<", "\\u003c")

    def fill(match):
        indent = match["indent"]
        lines = ['<script type="application/ld+json">', *(f"  {line}" for line in written.split("\n")), "</script>"]
        body = "".join(f"{indent}{line}\n" for line in lines)
        return f"{indent}{match['open']}\n{body}{indent}<!-- /data -->\n"

    path.write_text(DATA.sub(fill, text), encoding="utf-8")


def sitemap():
    """List every page of the site that search engines may show."""
    urls = []
    for path in sorted(DOCS.rglob("index.html")):
        head = Head()
        head.feed(path.read_text(encoding="utf-8"))
        if "noindex" in head.meta.get("robots", ""):
            continue
        folder = path.parent.relative_to(DOCS).as_posix()
        urls.append(f"{SITE}/" if folder == "." else f"{SITE}/{folder}/")
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"  <url><loc>{html.escape(url)}</loc></url>" for url in sorted(urls)]
    lines += ["</urlset>", ""]
    (DOCS / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    return len(urls)


if __name__ == "__main__":
    folders = sorted(path.parent for path in (DOCS / "writing").glob("*/index.html"))
    posts = [post for post in map(read, folders) if post]
    posts.sort(key=lambda post: (post["day"], post["title"]), reverse=True)

    relist(DOCS / "index.html", posts[:ON_HOME])
    relist(DOCS / "writing" / "index.html", posts)
    feed(posts)
    for post in posts:
        describe(post)
    pages = sitemap()
    print(f"{len(posts)} post{'' if len(posts) == 1 else 's'} listed; newest: {posts[0]['title'] if posts else 'none'}")
    print(f"{pages} page{'' if pages == 1 else 's'} in the sitemap")
