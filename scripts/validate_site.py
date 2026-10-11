"""Validate the static site: internal links, local images, canonical/OG tags,
duplicate canonicals, and sitemap consistency.

Usage:
  python scripts/validate_site.py            # report all findings; exit 1 on errors
  python scripts/validate_site.py --json     # machine-readable output

Scope is the set of pages the SEO config marks as eligible (seo_lib.discover_pages).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seo_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REF_RE = re.compile(r'\b(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
IMG_RE = re.compile(r'<img\s[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:", "#")


def resolve_local(root, page_rel, ref):
    """Return the repo file a local reference points to, or None if it is not local."""
    if not ref or ref.startswith(SKIP_SCHEMES):
        return None
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc:
        return None
    path = unquote(parts.path)
    if not path:
        return None
    if path.startswith("/"):
        target = root / path.lstrip("/")
    else:
        target = (root / page_rel).parent / path
    target = target.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return "outside-repo"
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def check_page(root, cfg, rel, errors, warnings):
    text = (root / rel).read_text(encoding="utf-8", errors="replace")
    for ref in set(REF_RE.findall(text)):
        target = resolve_local(root, rel, ref)
        if target is None:
            continue
        if target == "outside-repo":
            errors.append({"page": rel, "type": "link-outside-repo", "ref": ref})
        elif not target.exists():
            errors.append({"page": rel, "type": "broken-internal-link", "ref": ref})
    for src in set(IMG_RE.findall(text)):
        target = resolve_local(root, rel, src)
        if target is None:
            continue
        if target.suffix.lower() not in IMAGE_EXTS:
            errors.append({"page": rel, "type": "image-bad-format", "ref": src})
        elif not target.exists():
            errors.append({"page": rel, "type": "missing-image", "ref": src})
    counts = seo_lib.count_tags(text)
    expected = seo_lib.canonical_url(cfg, rel)
    if counts["canonical"] > 1:
        errors.append({"page": rel, "type": "duplicate-canonical-tag", "ref": str(counts["canonical"])})
    if counts["og_title"] > 1:
        errors.append({"page": rel, "type": "duplicate-og-title", "ref": str(counts["og_title"])})
    if counts["canonical"] == 1 and f'href="{expected}"' not in text:
        warnings.append({"page": rel, "type": "canonical-not-expected-url", "ref": expected})
    if rel.startswith("arlington/articles/") and counts["canonical"] == 0:
        warnings.append({"page": rel, "type": "no-canonical-tag (legacy page)", "ref": ""})
    return text


def check_sitemap(root, cfg, rels, errors):
    path = root / "sitemap.xml"
    if not path.exists():
        errors.append({"page": "sitemap.xml", "type": "missing-sitemap", "ref": ""})
        return
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text for e in ET.parse(path).getroot().findall("s:url/s:loc", ns)]
    expected = {seo_lib.canonical_url(cfg, r) for r in rels}
    for loc in locs:
        if locs.count(loc) > 1:
            errors.append({"page": "sitemap.xml", "type": "duplicate-sitemap-url", "ref": loc})
            break
    for missing in sorted(expected - set(locs)):
        errors.append({"page": "sitemap.xml", "type": "eligible-page-missing-from-sitemap", "ref": missing})
    for extra in sorted(set(locs) - expected):
        errors.append({"page": "sitemap.xml", "type": "sitemap-url-not-eligible", "ref": extra})


def check_duplicate_canonicals(root, cfg, rels, errors):
    seen = {}
    for rel in rels:
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        for tag in seo_lib.CANONICAL_RE.findall(text):
            m = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag)
            if m:
                href = m.group(1)
                if href in seen and seen[href] != rel:
                    errors.append({"page": rel, "type": "duplicate-canonical-url", "ref": f"{href} also on {seen[href]}"})
                seen[href] = rel


def validate(root=ROOT, cfg=None):
    cfg = cfg or seo_lib.load_config()
    rels = seo_lib.discover_pages(root, cfg)
    errors, warnings = [], []
    for rel in rels:
        check_page(root, cfg, rel, errors, warnings)
    check_sitemap(root, cfg, rels, errors)
    check_duplicate_canonicals(root, cfg, rels, errors)
    return {"pages_checked": len(rels), "errors": errors, "warnings": warnings}


BASELINE_PATH = Path(__file__).resolve().parent / "validator_baseline.json"


def finding_key(f):
    return f"{f['type']}|{f['page']}|{f['ref']}"


def load_baseline(path=BASELINE_PATH):
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8"))["known_errors"])


def write_baseline(result, path=BASELINE_PATH):
    keys = sorted({finding_key(e) for e in result["errors"]})
    payload = {
        "_comment": "Known pre-existing errors on main. CI fails only on errors NOT listed here (ratchet). Fix these in separate, approved content changes.",
        "known_errors": keys,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--update-baseline", action="store_true",
                    help="record current errors as known pre-existing issues (maintainers only)")
    args = ap.parse_args(argv)
    result = validate()
    if args.update_baseline:
        write_baseline(result)
        print(f"baseline updated with {len(result['errors'])} known errors")
        return 0
    known = load_baseline()
    new_errors = [e for e in result["errors"] if finding_key(e) not in known]
    result["new_errors"] = new_errors
    result["known_error_count"] = len(result["errors"]) - len(new_errors)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"pages checked: {result['pages_checked']}")
        print(f"errors: {len(result['errors'])} (known: {result['known_error_count']}, NEW: {len(new_errors)})  warnings: {len(result['warnings'])}")
        for e in new_errors[:200]:
            print(f"  NEW ERROR {e['type']}: {e['page']} -> {e['ref']}")
        for w in result["warnings"][:20]:
            print(f"  warn  {w['type']}: {w['page']} -> {w['ref']}")
    return 1 if new_errors else 0


if __name__ == "__main__":
    sys.exit(main())
