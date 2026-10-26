"""Letterman snapshot validation, page rendering and hub-card insertion.

A snapshot (content/letterman/<slug>.json) is a committed copy of an approved
Letterman article plus a site approval record. Nothing here talks to Letterman, and
nothing here can change a Letterman article's status.
"""

import html
import json
import re
import struct
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_gate  # noqa: E402
import seo_lib  # noqa: E402

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MAX = 100
ALLOWED_BODY_TAGS = {"p", "strong", "em", "u", "a"}
QUADRANTS = {"north", "south", "central", "east", "all"}
EXCERPT_MAX = 150
META_DESC_WARN = 160
ALT_MAX = 200
IMAGE_MAX_BYTES = 2 * 1024 * 1024
OG_MIN_WIDTH = 1200
IMAGE_DIR = "arlington/images/articles"
PAGE_DIR = "arlington/articles"
TEMPLATE_PATH = "templates/arlington-article-page.html"
HUB_PATH = "arlington/index.html"
SPACER_RE = re.compile(r"<p>(?:\s|&nbsp;|&#160;|\xa0)*</p>", re.IGNORECASE)
PARA_RE = re.compile(r"<p>.*?</p>", re.IGNORECASE | re.DOTALL)
SOURCE_HINT_RE = re.compile(r"\b(visit|see|check)\b[^.]{0,40}\b(official|website|page|site)\b", re.IGNORECASE)


class ImportRefused(Exception):
    def __init__(self, errors, warnings=None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__("; ".join(e["message"] for e in errors))


def _i(code, message, ref=""):
    return {"code": code, "message": message, "ref": ref}


# ---------------------------------------------------------------- body handling

class _TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.issues = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_BODY_TAGS:
            self.issues.append(_i("disallowed-tag", f"Tag <{tag}> is not allowed in article body (allowed: p, strong, em, u, a).", tag))
            return
        names = {k.lower() for k, _ in attrs}
        if tag == "a":
            extra = names - {"href"}
            if extra:
                self.issues.append(_i("disallowed-attribute", f"<a> may only have href; found {sorted(extra)}.", tag))
        elif names:
            self.issues.append(_i("disallowed-attribute", f"<{tag}> may not have attributes; found {sorted(names)}.", tag))


class _TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def text_of(fragment):
    c = _TextCollector()
    c.feed(fragment)
    return " ".join(html.unescape("".join(c.parts)).replace("\xa0", " ").split())


def paragraph_texts(body_html):
    """Non-empty paragraph texts, in order. Spacer paragraphs are ignored."""
    out = []
    for p in PARA_RE.findall(body_html):
        t = text_of(p)
        if t:
            out.append(t)
    return out


def check_body(body_html):
    issues = []
    tc = _TagChecker()
    tc.feed(body_html)
    issues.extend(tc.issues)
    leftover = PARA_RE.sub("", body_html)
    if text_of(leftover):
        issues.append(_i("text-outside-paragraph", "Article body has text outside <p> elements.", text_of(leftover)[:60]))
    if not paragraph_texts(body_html):
        issues.append(_i("empty-body", "Article body has no text."))
    return issues


def clean_body(body_html):
    """Drop empty spacer paragraphs; mark external links to open safely."""
    paras = [p for p in PARA_RE.findall(body_html) if not SPACER_RE.fullmatch(p.strip())]

    def fix_anchor(m):
        href = m.group(1)
        parts = urlsplit(href)
        host = (parts.hostname or "").lower()
        if parts.scheme in ("http", "https") and host not in link_gate.SELF_HOSTS:
            return f'<a href="{href}" target="_blank" rel="noopener noreferrer">'
        return m.group(0)

    return [re.sub(r'<a href="([^"]+)">', fix_anchor, p) for p in paras]


# ---------------------------------------------------------------- image handling

_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def image_info(path):
    """Return (kind, width, height). kind is None when the bytes are not a supported image."""
    b = Path(path).read_bytes()
    if b[:3] == b"\xff\xd8\xff":
        i = 2
        while i + 9 <= len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m == 0xFF:
                i += 1
                continue
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            if m == 0xD9:
                break
            length = struct.unpack(">H", b[i + 2:i + 4])[0]
            if m in _SOF:
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return "jpeg", w, h
            i += 2 + length
        return "jpeg", None, None
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return "png", w, h
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp", None, None
    return None, None, None


_EXT_KIND = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}


def check_image(snap, slug, root):
    errors, warnings = [], []
    img = snap.get("image") or {}
    rel = img.get("file", "")
    m = re.fullmatch(re.escape(IMAGE_DIR) + r"/" + re.escape(slug) + r"\.(jpg|jpeg|png|webp)", rel)
    if not m:
        errors.append(_i("image-path", f"Image must be stored at {IMAGE_DIR}/{slug}.(jpg|jpeg|png|webp); got '{rel}'.", rel))
        return errors, warnings
    path = Path(root) / rel
    if not path.is_file():
        errors.append(_i("missing-image", f"Image file does not exist: {rel}. Download it into the repo first.", rel))
        return errors, warnings
    size = path.stat().st_size
    if size == 0:
        errors.append(_i("empty-image", f"Image file is empty: {rel}", rel))
        return errors, warnings
    if size > IMAGE_MAX_BYTES:
        errors.append(_i("image-too-large", f"Image is {size} bytes; limit is {IMAGE_MAX_BYTES}.", rel))
    kind, w, h = image_info(path)
    if kind is None:
        errors.append(_i("image-bad-format", f"File is not a JPEG, PNG or WebP image: {rel}", rel))
    elif _EXT_KIND[path.suffix.lower()] != kind:
        errors.append(_i("image-extension-mismatch", f"Extension {path.suffix} does not match the {kind} data in {rel}.", rel))
    elif w is not None and w < OG_MIN_WIDTH:
        warnings.append(_i("image-narrow", f"Image is {w}px wide; {OG_MIN_WIDTH}px or more is recommended for social previews.", rel))
    elif w is None:
        warnings.append(_i("image-dimensions-unknown", "Could not read image dimensions.", rel))
    return errors, warnings


# ---------------------------------------------------------------- snapshot validation

def slug_of(snap):
    return (snap.get("letterman") or {}).get("url_path") or ""


def blocks_of(snap):
    return sorted((snap.get("letterman") or {}).get("blocks") or [], key=lambda b: b.get("index", 0))


def body_html_of(snap):
    return "".join(b.get("html") or "" for b in blocks_of(snap) if b.get("type") == "TEXT")


def subtitle_of(snap):
    for b in blocks_of(snap):
        if b.get("type") == "HEADLINE_COMBO" and b.get("subTitle"):
            return b["subTitle"]
    return ""


def excerpt_of(snap):
    lm = snap.get("letterman") or {}
    return lm.get("summary_description") or lm.get("description") or ""


def display_date(iso):
    dt = datetime.strptime(iso, "%Y-%m-%d")
    return f"{dt:%B} {dt.day}, {dt.year}"


def validate_snapshot(snap, root, *, check_duplicate=True, check_files=True):
    """Return (errors, warnings). Errors block the import."""
    errors, warnings = [], []
    lm = snap.get("letterman") or {}
    ap = snap.get("approval") or {}
    slug = slug_of(snap)

    for key in ("id", "state", "title", "description"):
        if not lm.get(key):
            errors.append(_i("missing-field", f"letterman.{key} is required.", key))

    if not slug:
        errors.append(_i("missing-slug", "Letterman article has no urlPath. Set a slug in Letterman first; ID-style URLs are not imported.", ""))
    elif not SLUG_RE.fullmatch(slug) or len(slug) > SLUG_MAX:
        errors.append(_i("invalid-slug", f"Slug '{slug}' must be lowercase letters, digits and single hyphens, up to {SLUG_MAX} characters.", slug))

    # draft protection: only a Letterman state of exactly "PUBLISHED" can be imported. There is no override.
    state = lm.get("state")
    if state != "PUBLISHED":
        errors.append(_i("draft-not-approved",
                         f"Letterman article state is {state!r}, not PUBLISHED. Refusing to create a site page. "
                         "Publish it in Letterman first; no approval record or flag can override this.", str(state)))
    if any("allow_draft_state" in section for section in (snap, lm, ap)):
        errors.append(_i("unsupported-override",
                         "allow_draft_state is not supported and is never honored. Remove it from the snapshot.",
                         "allow_draft_state"))
    for key in ("approved_by", "approved_at", "site_publish_date", "image_alt", "quadrant"):
        if not ap.get(key):
            errors.append(_i("missing-approval", f"approval.{key} is required. The article is not approved for the site.", key))
    if ap.get("site_publish_date"):
        try:
            datetime.strptime(ap["site_publish_date"], "%Y-%m-%d")
        except ValueError:
            errors.append(_i("invalid-date", "approval.site_publish_date must be YYYY-MM-DD.", ap["site_publish_date"]))
    if ap.get("quadrant") and ap["quadrant"] not in QUADRANTS:
        errors.append(_i("invalid-quadrant", f"quadrant must be one of {sorted(QUADRANTS)}; got '{ap['quadrant']}'.", ap["quadrant"]))
    if ap.get("quadrant") and ap["quadrant"] != "all" and not ap.get("quadrant_evidence"):
        errors.append(_i("missing-quadrant-evidence", "A non-'all' quadrant needs approval.quadrant_evidence.", ""))
    alt = ap.get("image_alt", "")
    if alt and len(alt) > ALT_MAX:
        errors.append(_i("alt-too-long", f"image_alt is {len(alt)} characters; limit is {ALT_MAX}.", ""))

    # content
    excerpt = excerpt_of(snap)
    if excerpt and len(excerpt) > EXCERPT_MAX:
        errors.append(_i("excerpt-too-long", f"Hub excerpt is {len(excerpt)} characters; limit is {EXCERPT_MAX}. Shorten summary_description in Letterman.", ""))
    if lm.get("description") and len(lm["description"]) > META_DESC_WARN:
        warnings.append(_i("meta-description-long", f"Meta description is {len(lm['description'])} characters; search engines may truncate above {META_DESC_WARN}.", ""))
    body = body_html_of(snap)
    errors.extend(check_body(body))
    gate_errors, gate_warnings = link_gate.check_links(body, f"{PAGE_DIR}/{slug or 'new'}.html", root)
    errors.extend(gate_errors)
    warnings.extend(gate_warnings)
    ext_links = link_gate.external_urls(body)
    if SOURCE_HINT_RE.search(text_of(body)) and not ext_links and not any(b.get("links") for b in blocks_of(snap)):
        warnings.append(_i("missing-source-links",
                           "The text tells readers to visit an official page or site, but no link URLs were provided. "
                           "Supply the source URLs before publishing.", ""))
    head_titles = [b.get("title") for b in blocks_of(snap) if b.get("type") == "HEADLINE_COMBO" and b.get("title")]
    if head_titles and lm.get("title") and head_titles[0].strip() != lm["title"].strip():
        warnings.append(_i("title-mismatch", "Headline block title differs from the article title; the article title is used.", head_titles[0]))

    if check_files:
        ie, iw = check_image(snap, slug, root) if slug and SLUG_RE.fullmatch(slug) else ([], [])
        errors.extend(ie)
        warnings.extend(iw)
    if check_duplicate and slug:
        if (Path(root) / PAGE_DIR / f"{slug}.html").exists():
            errors.append(_i("duplicate-slug", f"{PAGE_DIR}/{slug}.html already exists. Refusing to overwrite an existing page.", slug))
    if lm.get("no_index"):
        warnings.append(_i("noindex", "Letterman noIndex is set: the page will carry noindex, be excluded from the sitemap, and get no hub card.", ""))
    return errors, warnings


# ---------------------------------------------------------------- rendering

def render_page(snap, template_text, cfg, root):
    lm, ap = snap["letterman"], snap["approval"]
    slug = slug_of(snap)
    rel = f"{PAGE_DIR}/{slug}.html"
    paras = clean_body(body_html_of(snap))
    body = "\n".join("            " + p for p in paras)
    img = snap["image"]
    _, w, h = image_info(Path(root) / img["file"])
    dims = f' width="{w}" height="{h}"' if w and h else ""
    image_block = (
        '        <div class="featured-image">\n'
        f'            <img src="/{img["file"]}" alt="{html.escape(ap["image_alt"], quote=True)}"{dims}>\n'
        "        </div>\n"
    )
    noindex = bool(lm.get("no_index"))
    if noindex:
        robots = '\n    <meta name="robots" content="noindex, nofollow">'
        seo = ""
    else:
        robots = ""
        seo = seo_lib.render_seo_tags(cfg, {
            "rel": rel, "title": lm["title"], "description": lm["description"],
            "image": img["file"], "published": ap["site_publish_date"],
        })
    values = {
        "{{TITLE}}": html.escape(lm["title"], quote=False),
        "{{DESCRIPTION}}": html.escape(lm["description"], quote=True),
        "{{ROBOTS_META}}": robots,
        "{{SEO_TAGS}}": seo,
        "{{DATE_DISPLAY}}": display_date(ap["site_publish_date"]),
        "{{SUBTITLE}}": html.escape(subtitle_of(snap), quote=False),
        "{{IMAGE_BLOCK}}": image_block,
        "{{BODY}}": body,
    }
    out = template_text.replace("\r\n", "\n")
    for key, val in values.items():
        out = out.replace(key, val)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover:
        raise ImportRefused([_i("template-placeholder", f"Unfilled template placeholders: {sorted(set(leftover))}", "")])
    return out.replace("\n", "\r\n")


# ---------------------------------------------------------------- hub card

def build_hub_card(snap):
    lm, ap = snap["letterman"], snap["approval"]
    slug = slug_of(snap)
    q = ap["quadrant"]
    lines = [
        f'            <div class="issue-card" data-quadrant="{q}">',
        f'             <span class="quadrant-badge {q}">{q.upper()}</span>',
        f'             <h4>{html.escape(lm["title"], quote=False)}</h4>',
        f'             <div class="date">{display_date(ap["site_publish_date"])}</div>',
        f'             <p>{html.escape(excerpt_of(snap), quote=False)}</p>',
        f'             <a href="/{PAGE_DIR}/{slug}.html">Read Issue →</a>',
        "            </div>",
    ]
    return lines


def insert_hub_card(hub_text, snap):
    """Insert exactly one card at the top of .archive-grid, preserving line endings."""
    slug = slug_of(snap)
    eol = "\r\n" if "\r\n" in hub_text else "\n"
    text = hub_text.replace("\r\n", "\n")
    anchor = '        <div class="archive-grid">\n'
    if text.count(anchor) != 1:
        raise ImportRefused([_i("hub-anchor", f"Expected exactly one archive-grid anchor in the hub; found {text.count(anchor)}.", "")])
    if f'href="/{PAGE_DIR}/{slug}.html"' in text:
        raise ImportRefused([_i("hub-card-exists", f"The hub already links to {slug}. Refusing to add a duplicate card.", slug)])
    card = "\n".join(build_hub_card(snap)) + "\n"
    return text.replace(anchor, anchor + card, 1).replace("\n", eol)
