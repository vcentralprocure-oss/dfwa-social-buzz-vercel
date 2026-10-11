"""Import an approved Letterman article snapshot as a local Arlington article page.

Usage:
  python scripts/import_letterman_article.py content/letterman/<slug>.json [--dry-run]
  python scripts/import_letterman_article.py --verify-all

The importer refuses drafts and unapproved snapshots, never contacts Letterman, and
never changes a Letterman article's status. On success it writes:
  arlington/articles/<slug>.html   (new page; canonical + Open Graph tags; noindex if requested)
  one hub card at the top of arlington/index.html (not for noindex articles)
  sitemap.xml and robots.txt       (regenerated)
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import article_lib as al  # noqa: E402
import generate_seo  # noqa: E402
import link_gate  # noqa: E402
import seo_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = "content/letterman"


def import_article(root, snapshot_path, cfg=None, dry_run=False):
    root = Path(root)
    cfg = cfg or seo_lib.load_config()
    snap = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    errors, warnings = al.validate_snapshot(snap, root)
    if errors:
        raise al.ImportRefused(errors, warnings)
    slug = al.slug_of(snap)
    template = (root / al.TEMPLATE_PATH).read_text(encoding="utf-8")
    page = al.render_page(snap, template, cfg, root)
    noindex = bool(snap["letterman"].get("no_index"))
    hub_path = root / al.HUB_PATH
    hub_new = None
    if not noindex:
        hub_new = al.insert_hub_card(hub_path.read_bytes().decode("utf-8"), snap)
    result = {
        "slug": slug,
        "page": f"{al.PAGE_DIR}/{slug}.html",
        "hub_card": hub_new is not None,
        "noindex": noindex,
        "warnings": warnings,
    }
    if dry_run:
        return result
    page_path = root / al.PAGE_DIR / f"{slug}.html"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_bytes(page.encode("utf-8"))
    if hub_new is not None:
        hub_path.write_bytes(hub_new.encode("utf-8"))
    generate_seo.write_outputs(root, cfg)
    return result


ARTICLE_REGION_RE = re.compile(r'<!-- article-body-start -->(.*?)<!-- article-body-end -->', re.DOTALL)


def verify_all(root):
    """Check every committed snapshot that has a page: draft protection, tags, links, text."""
    root = Path(root)
    problems = []
    for sp in sorted((root / SNAPSHOT_DIR).glob("*.json")) if (root / SNAPSHOT_DIR).exists() else []:
        snap = json.loads(sp.read_text(encoding="utf-8"))
        slug = sp.stem
        if al.slug_of(snap) != slug:
            problems.append((slug, al._i("snapshot-name-mismatch", f"Snapshot file name '{slug}' does not match its slug '{al.slug_of(snap)}'.", "")))
            continue
        page = root / al.PAGE_DIR / f"{slug}.html"
        if not page.exists():
            continue
        errors, _ = al.validate_snapshot(snap, root, check_duplicate=False)
        for e in errors:
            problems.append((slug, e))
        text = page.read_text(encoding="utf-8", errors="replace")
        noindex = bool(snap["letterman"].get("no_index"))
        counts = seo_lib.count_tags(text)
        if noindex:
            if not seo_lib.has_noindex(text):
                problems.append((slug, al._i("noindex-missing", "Letterman noIndex is set but the page has no noindex tag.", "")))
        else:
            if counts["canonical"] != 1 or counts["og_title"] != 1:
                problems.append((slug, al._i("seo-tags", f"Page needs exactly one canonical and one og:title; found {counts}.", "")))
        m = ARTICLE_REGION_RE.search(text)
        region = m.group(1) if m else ""
        ge, _ = link_gate.check_links(region, f"{al.PAGE_DIR}/{slug}.html", root)
        for e in ge:
            problems.append((slug, e))
        if al.paragraph_texts(region) != al.paragraph_texts(al.body_html_of(snap)):
            problems.append((slug, al._i("text-drift", "Page text differs from the approved Letterman text.", "")))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot", nargs="?")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-all", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.verify_all:
        problems = verify_all(root)
        if problems:
            print("VERIFY FAILED:")
            for slug, e in problems:
                print(f"  - {slug}: [{e['code']}] {e['message']}")
            return 1
        print("verify-all: every snapshot with a page passes draft protection, tag, link and text checks")
        return 0
    if not args.snapshot:
        ap.error("a snapshot path is required (or use --verify-all)")
    try:
        result = import_article(root, args.snapshot, dry_run=args.dry_run)
    except al.ImportRefused as exc:
        print("IMPORT REFUSED. Nothing was written.")
        for e in exc.errors:
            print(f"  - [{e['code']}] {e['message']}")
        for w in exc.warnings:
            print(f"  warning [{w['code']}] {w['message']}")
        return 1
    print(("DRY RUN: would write " if args.dry_run else "wrote ") + result["page"])
    print(f"hub card: {'yes' if result['hub_card'] else 'no (noindex article)'}")
    for w in result["warnings"]:
        print(f"  warning [{w['code']}] {w['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
