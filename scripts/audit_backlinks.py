"""OPTIONAL, NON-BLOCKING audit of outbound (external) links across the site.

Not part of CI and not part of the publishing gate. It never fails a build: the exit
code is always 0. It reports which external domains the site links to, how often, and
from which pages, so an editor can review business and source links.

Usage:
  python scripts/audit_backlinks.py             # offline inventory
  python scripts/audit_backlinks.py --json
  python scripts/audit_backlinks.py --check     # also test reachability (network)
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_gate  # noqa: E402
import seo_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def inventory(root, cfg, rels=None):
    """Return {domain: {"links": n, "pages": [..], "urls": [..]}} for external links."""
    root = Path(root)
    rels = rels if rels is not None else seo_lib.discover_pages(root, cfg)
    by_domain = defaultdict(lambda: {"links": 0, "pages": set(), "urls": set()})
    for rel in rels:
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        for url in link_gate.external_urls(text):
            host = (urlsplit(url).hostname or "").lower()
            entry = by_domain[host]
            entry["links"] += 1
            entry["pages"].add(rel)
            entry["urls"].add(url)
    return {d: {"links": e["links"], "pages": sorted(e["pages"]), "urls": sorted(e["urls"])}
            for d, e in sorted(by_domain.items())}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="test reachability of each external URL (network)")
    args = ap.parse_args(argv)
    cfg = seo_lib.load_config()
    inv = inventory(args.root, cfg)
    unreachable = []
    if args.check:
        urls = [u for e in inv.values() for u in e["urls"]]
        unreachable = link_gate.check_reachable(urls)
    if args.json:
        print(json.dumps({"domains": inv, "unreachable": unreachable}, indent=2))
    else:
        total = sum(e["links"] for e in inv.values())
        print(f"external links: {total} across {len(inv)} domains (non-blocking audit)")
        for domain, e in sorted(inv.items(), key=lambda kv: -kv[1]["links"]):
            print(f"  {e['links']:4d}  {domain}  ({len(e['pages'])} pages)")
        for w in unreachable:
            print(f"  unreachable: {w['ref']}  {w['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
