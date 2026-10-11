"""Hyperlink validation gate for new article pages (standard library only).

Blocking errors: broken internal links, malformed or unsafe URLs, links to hosts or
paths that must never be published (the arlington. subdomain, Letterman article URLs,
apex absolute self-links), and target=_blank links without rel="noopener".
Warnings: plain http, tracking parameters, duplicate external links, generic link text.
Live reachability is OPTIONAL (check_reachable) and never blocks.
"""

import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_site  # noqa: E402

FORBIDDEN_HOSTS = {"arlington.dfwasocialbuzz.com"}
LETTERMAN_HOSTS = {"m.letterman.ai"}
UNSAFE_SCHEMES = {"javascript", "data", "vbscript", "file", "ftp"}
SELF_HOSTS = {"dfwasocialbuzz.com", "www.dfwasocialbuzz.com"}
CANONICAL_SELF_HOST = "www.dfwasocialbuzz.com"
TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
GENERIC_TEXT = {"click here", "here", "link", "this link", "read more", "more"}


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._cur = {"attrs": {k.lower(): (v or "") for k, v in attrs}, "text": ""}
            self.links.append(self._cur)

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data

    def handle_endtag(self, tag):
        if tag == "a":
            self._cur = None


def extract_links(html_text):
    p = _LinkParser()
    p.feed(html_text)
    return p.links


def _issue(code, message, ref=""):
    return {"code": code, "message": message, "ref": ref}


def check_links(html_text, page_rel, root, scope="body"):
    """Return (errors, warnings) for every <a> in html_text.

    scope="body" checks only the links inside article content; "page" is the same
    check applied to a whole page. Internal links resolve against `root`.
    """
    root = Path(root)
    errors, warnings = [], []
    seen_external = set()
    for link in extract_links(html_text):
        attrs = link["attrs"]
        href = attrs.get("href", "").strip()
        text = " ".join(link["text"].split()).lower()
        if not href:
            errors.append(_issue("empty-href", "A link has no href.", text))
            continue
        if re.search(r"\s", href):
            errors.append(_issue("malformed-url", f"URL contains whitespace: {href!r}", href))
            continue
        parts = urlsplit(href)
        scheme = parts.scheme.lower()
        if scheme in UNSAFE_SCHEMES:
            errors.append(_issue("unsafe-scheme", f"Unsafe link scheme '{scheme}:'.", href))
            continue
        if scheme in ("mailto", "tel"):
            continue
        if scheme in ("http", "https"):
            host = (parts.hostname or "").lower()
            if not host or "." not in host:
                errors.append(_issue("malformed-url", f"External URL has no valid host: {href}", href))
                continue
            if host in FORBIDDEN_HOSTS:
                errors.append(_issue("forbidden-host",
                                     "Never link to the arlington. subdomain. Use a relative link or the www host.", href))
                continue
            if host in LETTERMAN_HOSTS or (host in SELF_HOSTS and parts.path.startswith("/a/")):
                errors.append(_issue("letterman-article-url",
                                     "Do not link to Letterman article URLs (/a/...). Link to the local page instead.", href))
                continue
            if host in SELF_HOSTS:
                if host != CANONICAL_SELF_HOST:
                    errors.append(_issue("apex-self-link",
                                         "Use https://www.dfwasocialbuzz.com or a relative link, not the apex host.", href))
                    continue
                # absolute link to our own canonical host: check the local target
                target = validate_site.resolve_local(root, page_rel, parts.path or "/")
                if target not in (None, "outside-repo") and not target.exists():
                    errors.append(_issue("broken-internal-link", f"Internal link target not found: {href}", href))
                continue
            # genuine external link
            if scheme == "http":
                warnings.append(_issue("insecure-http", "External link uses http, not https.", href))
            for k, _ in parse_qsl(parts.query, keep_blank_values=True):
                if k.lower().startswith(TRACKING_PREFIXES) or k.lower() in TRACKING_KEYS:
                    warnings.append(_issue("tracking-params", f"External link carries tracking parameter '{k}'.", href))
                    break
            key = href.rstrip("/").lower()
            if key in seen_external:
                warnings.append(_issue("duplicate-external-link", "The same external link appears more than once.", href))
            seen_external.add(key)
            if text in GENERIC_TEXT:
                warnings.append(_issue("generic-link-text", f"Link text '{text}' is not descriptive.", href))
            if attrs.get("target", "").lower() == "_blank":
                rel = attrs.get("rel", "").lower().split()
                if "noopener" not in rel:
                    errors.append(_issue("target-blank-no-rel", 'target="_blank" needs rel="noopener noreferrer".', href))
            continue
        if scheme:
            errors.append(_issue("unsupported-scheme", f"Unsupported link scheme '{scheme}:'.", href))
            continue
        # relative or root-relative internal link
        if href.startswith("#"):
            continue
        target = validate_site.resolve_local(root, page_rel, href)
        if target is None:
            continue
        if target == "outside-repo":
            errors.append(_issue("link-outside-repo", f"Link leaves the repository: {href}", href))
        elif not target.exists():
            errors.append(_issue("broken-internal-link", f"Internal link target not found: {href}", href))
    return errors, warnings


def external_urls(html_text):
    urls = []
    for link in extract_links(html_text):
        href = link["attrs"].get("href", "").strip()
        parts = urlsplit(href)
        if parts.scheme in ("http", "https") and (parts.hostname or "").lower() not in SELF_HOSTS:
            urls.append(href)
    return urls


def check_reachable(urls, opener=None, timeout=10):
    """OPTIONAL live check. Returns warnings only; it never blocks a release.

    `opener(url, timeout)` returns an HTTP status int; injected in tests so no network is used.
    """
    def default_opener(url, timeout):
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DFWASocialBuzz-linkcheck/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except Exception:
            return 0

    opener = opener or default_opener
    warnings = []
    for url in sorted(set(urls)):
        status = opener(url, timeout)
        if status == 0 or status >= 400:
            warnings.append(_issue("unreachable-external-link",
                                   f"External link returned {status or 'no response'}; verify manually.", url))
    return warnings
