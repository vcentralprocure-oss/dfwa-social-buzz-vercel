"""Generate sitemap.xml and robots.txt, and add canonical/OG tags to NEW pages.

Usage:
  python scripts/generate_seo.py              # write sitemap.xml and robots.txt
  python scripts/generate_seo.py --check      # exit 1 if committed files are stale
  python scripts/generate_seo.py --tag-new-page PAGE.html --meta META.json

--tag-new-page refuses any file that git already tracks, so existing pages are
never modified by this tool.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seo_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def tracked_files(root):
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True)
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def expected_outputs(root, cfg):
    rels = seo_lib.discover_pages(root, cfg)
    return {
        "sitemap.xml": seo_lib.build_sitemap(cfg, rels),
        "robots.txt": seo_lib.build_robots(cfg),
    }


def write_outputs(root, cfg):
    for name, text in expected_outputs(root, cfg).items():
        (root / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {name}")


def check_outputs(root, cfg):
    stale = []
    for name, text in expected_outputs(root, cfg).items():
        path = root / name
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(name)
    if stale:
        print("STALE generated files (run: python scripts/generate_seo.py): " + ", ".join(stale))
        return 1
    print("generated SEO files are up to date")
    return 0


def tag_new_page(root, cfg, page_rel, meta, tracked):
    if page_rel in tracked:
        raise SystemExit(f"refusing to modify tracked (existing) page: {page_rel}")
    path = root / page_rel
    text = path.read_text(encoding="utf-8")
    if seo_lib.CANONICAL_RE.search(text) or seo_lib.OG_TITLE_RE.search(text):
        raise SystemExit(f"page already has canonical or og:title tags: {page_rel}")
    if "</head>" not in text:
        raise SystemExit(f"no </head> in {page_rel}")
    meta = dict(meta, rel=page_rel)
    tags = seo_lib.render_seo_tags(cfg, meta)
    text = text.replace("</head>", tags + "</head>", 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"tagged new page: {page_rel}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tag-new-page")
    ap.add_argument("--meta")
    args = ap.parse_args(argv)
    cfg = seo_lib.load_config()
    if args.tag_new_page:
        if not args.meta:
            raise SystemExit("--meta JSON file is required with --tag-new-page")
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
        tag_new_page(ROOT, cfg, args.tag_new_page, meta, tracked_files(ROOT))
        return 0
    if args.check:
        return check_outputs(ROOT, cfg)
    write_outputs(ROOT, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
