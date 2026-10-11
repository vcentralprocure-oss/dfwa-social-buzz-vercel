"""Shared helpers for the DFW Social Buzz SEO tooling (standard library only).

Scope: sitemap.xml, robots.txt, canonical and Open Graph tags for NEW pages.
Existing pages are never modified by these tools.
"""

import fnmatch
import html
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

CONFIG_PATH = Path(__file__).resolve().parent / "seo_config.json"

META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*["\']([^"\']*)["\']')


def has_noindex(text):
    """True if any robots meta tag contains noindex, regardless of attribute order."""
    for tag in META_TAG_RE.findall(text):
        attrs = {k.lower(): v.lower() for k, v in ATTR_RE.findall(tag)}
        if attrs.get("name") == "robots" and "noindex" in attrs.get("content", ""):
            return True
    return False
CANONICAL_RE = re.compile(r'<link\s+[^>]*rel\s*=\s*["\']canonical["\'][^>]*>', re.IGNORECASE)
OG_TITLE_RE = re.compile(r'<meta\s+[^>]*property\s*=\s*["\']og:title["\']', re.IGNORECASE)


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["canonical_host"] = cfg["canonical_host"].rstrip("/")
    return cfg


def is_excluded(rel, exclude_globs):
    return any(fnmatch.fnmatch(rel, pat) for pat in exclude_globs)


def discover_pages(root, cfg):
    """Return sorted repo-relative paths of pages that are eligible for the sitemap.

    A page is eligible when it matches an include glob, matches no exclude glob,
    and does not declare noindex. Drafts are excluded by naming convention
    (see exclude_globs) or by a noindex robots meta tag.
    """
    root = Path(root)
    found = set()
    for pattern in cfg["include_globs"]:
        for path in root.glob(pattern):
            if path.is_file():
                found.add(path.relative_to(root).as_posix())
    eligible = []
    for rel in sorted(found):
        if is_excluded(rel, cfg["exclude_globs"]):
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        if has_noindex(text):
            continue
        eligible.append(rel)
    return eligible


def page_path(rel):
    """Public URL path served for a repo file (Vercel static, no cleanUrls)."""
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def canonical_url(cfg, rel):
    return cfg["canonical_host"] + page_path(rel)


def build_sitemap(cfg, rels):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in rels:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(canonical_url(cfg, rel))}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_robots(cfg):
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {cfg['canonical_host']}/sitemap.xml\n"
    )


def render_seo_tags(cfg, meta):
    """Return canonical and Open Graph tags for a new page.

    meta keys: rel (repo path of the page), title, description,
    image (optional repo-relative image path), published (optional ISO date),
    site_name (optional, default "Arlington Pulse").
    """
    url = canonical_url(cfg, meta["rel"])
    title = html.escape(meta["title"], quote=True)
    desc = html.escape(meta["description"], quote=True)
    site = html.escape(meta.get("site_name", "Arlington Pulse"), quote=True)
    lines = [
        f'    <link rel="canonical" href="{url}">',
        f'    <meta property="og:type" content="article">',
        f'    <meta property="og:site_name" content="{site}">',
        f'    <meta property="og:title" content="{title}">',
        f'    <meta property="og:description" content="{desc}">',
        f'    <meta property="og:url" content="{url}">',
    ]
    if meta.get("image"):
        image_url = cfg["canonical_host"] + "/" + meta["image"].lstrip("/")
        lines.append(f'    <meta property="og:image" content="{html.escape(image_url, quote=True)}">')
    if meta.get("published"):
        lines.append(f'    <meta property="article:published_time" content="{html.escape(meta["published"], quote=True)}">')
    return "\n".join(lines) + "\n"


def count_tags(text):
    return {
        "canonical": len(CANONICAL_RE.findall(text)),
        "og_title": len(OG_TITLE_RE.findall(text)),
    }
