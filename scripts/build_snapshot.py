"""Build an importer snapshot from the Letterman connector's RAW output (standard library only).

The connector (MCP) exists only inside a Claude session, so this script never contacts Letterman. It reads the two raw
responses saved to files exactly as returned:
  get_article(articleId)          -> article.json
  list_content_blocks(articleId)  -> blocks.json   ({"contentBlocks": [...]})

Fail closed. Only an article whose OWN state is exactly "PUBLISHED" (with a readable publishedAt) is eligible; block-level
state is never consulted. Anything missing, malformed or ambiguous refuses the build and writes nothing.

Usage:
  python scripts/build_snapshot.py --article article.json --blocks blocks.json --approval approval.json \\
      --image-file arlington/images/articles/<slug>.jpg \\
      [--reread-article article2.json --reread-blocks blocks2.json] [--dry-run] [--overwrite] [--root DIR]

The snapshot contains the article text. This repository is public: do not commit or push a snapshot or its page without the
owner's explicit approval (see docs/publishing-workflow.md).
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import article_lib as al  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ARLINGTON_PULSE_ID = "69ee9d94a166af267eb5e972"
ID_RE = re.compile(r"^[0-9a-f]{24}$")
TITLE_SUFFIX_RE = re.compile(r"\s*\|\s*Arlington Pulse\s*$")
ALLOWED_BLOCK_TYPES = ("HEADLINE_COMBO", "TEXT")
APPROVAL_KEYS = ("approved_by", "approved_at", "site_publish_date", "image_alt", "quadrant", "quadrant_evidence", "manual_review")
SNAPSHOT_DIR = "content/letterman"
OVERRIDE_KEY = "allow_draft_state"


class BuildRefused(Exception):
    def __init__(self, errors, warnings=None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__("; ".join(e["code"] for e in errors))


def _e(code, message):
    return {"code": code, "message": message}


def _text(value):
    """The stripped string if it is a non-empty string, else None."""
    return value.strip() if isinstance(value, str) and value.strip() else None


def normalize_title(raw):
    """Strip a trailing '| Arlington Pulse' (the page template appends it itself)."""
    t = _text(raw)
    if t is None:
        return None
    return TITLE_SUFFIX_RE.sub("", t).strip() or None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def check_eligibility(article, publication_id=ARLINGTON_PULSE_ID):
    """Errors that make the article ineligible. Empty only when the ARTICLE'S OWN state is exactly 'PUBLISHED' with a
    readable publishedAt, in the expected publication. A missing, unknown or ambiguous state is never eligible."""
    if not isinstance(article, dict):
        return [_e("malformed-article", "get_article output must be a JSON object.")]
    errors = []
    state = article.get("state")
    if "state" not in article or not isinstance(state, str) or not state:
        errors.append(_e("state-missing-or-invalid", "The article has no usable state field. Refusing to guess."))
    elif state != "PUBLISHED":
        errors.append(_e("not-published", f"Article state is {state!r}, not exactly 'PUBLISHED'."))
    elif _parse_time(article.get("publishedAt")) is None:
        errors.append(_e("ambiguous-published", "State is PUBLISHED but publishedAt is missing or unreadable. Refusing to guess."))
    if article.get("storageId") != publication_id:
        errors.append(_e("wrong-publication", f"Article belongs to publication {article.get('storageId')!r}, not {publication_id!r}."))
    return errors


def _active_blocks(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get("contentBlocks"), list):
        return [], [_e("malformed-blocks", "list_content_blocks output must be an object with a contentBlocks list.")]
    errors, active, seen = [], [], set()
    for i, b in enumerate(doc["contentBlocks"]):
        if not isinstance(b, dict):
            errors.append(_e("malformed-block", f"Block #{i} is not an object."))
            continue
        if not isinstance(b.get("isActive"), bool):
            errors.append(_e("ambiguous-block-active", f"Block #{i} has no boolean isActive; cannot tell if it is live."))
            continue
        if not b["isActive"]:
            continue
        if b.get("type") not in ALLOWED_BLOCK_TYPES:
            errors.append(_e("unsupported-block", f"Block #{i} has type {b.get('type')!r}; only {', '.join(ALLOWED_BLOCK_TYPES)} can be imported without dropping content."))
            continue
        idx = b.get("index")
        if isinstance(idx, bool) or not isinstance(idx, int):
            errors.append(_e("malformed-block-index", f"Block #{i} has no integer index."))
            continue
        if idx in seen:
            errors.append(_e("duplicate-block-index", f"Two active blocks share index {idx}; the order is ambiguous."))
            continue
        seen.add(idx)
        active.append(b)
    return sorted(active, key=lambda b: b["index"]), errors


def build_snapshot(article, blocks_doc, approval=None, image=None, publication_id=ARLINGTON_PULSE_ID):
    """Return (snapshot, warnings) or raise BuildRefused with every reason found."""
    errors = check_eligibility(article, publication_id)
    if not isinstance(article, dict):
        raise BuildRefused(errors)
    warnings = []
    active, block_errors = _active_blocks(blocks_doc)
    errors += block_errors

    if not (isinstance(article.get("id"), str) and ID_RE.fullmatch(article["id"])):
        errors.append(_e("missing-or-invalid-id", "Article id must be a 24-character lowercase hex string."))
    slug = article.get("urlPath")
    if _text(slug) is None:
        errors.append(_e("missing-slug", "Article has no urlPath. Set a slug in Letterman first; ID-style URLs are not imported."))
        slug = None
    elif slug != slug.strip() or not al.SLUG_RE.fullmatch(slug) or len(slug) > al.SLUG_MAX:
        errors.append(_e("invalid-slug", f"urlPath {slug!r} must be lowercase letters, digits and single hyphens, up to {al.SLUG_MAX} characters."))
        slug = None
    elif slug == article.get("id"):
        errors.append(_e("id-style-slug", "urlPath is just the article id; set a real slug in Letterman."))
        slug = None
    if not isinstance(article.get("noIndex"), bool):
        errors.append(_e("noindex-missing-or-invalid", "noIndex must be true or false. Refusing to assume the article is indexable."))
    keywords = article.get("keywords")
    if keywords is None:
        keywords = []
    elif not (isinstance(keywords, list) and all(isinstance(k, str) for k in keywords)):
        errors.append(_e("malformed-keywords", "keywords must be a list of strings."))
        keywords = []
    summary = article.get("summary")
    if summary is None:
        summary = {}
    elif not isinstance(summary, dict):
        errors.append(_e("malformed-summary", "summary must be an object."))
        summary = {}

    headlines = [b for b in active if b["type"] == "HEADLINE_COMBO"]
    texts = [b for b in active if b["type"] == "TEXT"]
    if len(headlines) > 1:
        errors.append(_e("multiple-headline-blocks", "More than one active HEADLINE_COMBO block; the headline is ambiguous."))
    headline = headlines[0] if len(headlines) == 1 else {}
    for b in headlines + texts:
        for key in ("title", "subTitle", "promptOutput", "imageUrl"):
            if b.get(key) is not None and not isinstance(b.get(key), str):
                errors.append(_e("malformed-block", f"Block index {b['index']}: {key} must be text."))
    body_blocks = []
    for b in texts:
        html = b.get("promptOutput")
        if isinstance(html, str) and html.strip():
            body_blocks.append({"type": "TEXT", "index": b["index"], "title": b.get("title") if isinstance(b.get("title"), str) else "",
                                "subTitle": None, "html": html, "links": []})
    if not body_blocks:
        errors.append(_e("missing-body", "No active TEXT block with body text."))

    title = (normalize_title(summary.get("title")) or normalize_title(headline.get("title")) or normalize_title(article.get("title")))
    if not title:
        errors.append(_e("missing-title", "No usable title in summary.title, the headline block, or the article."))

    description = _text(summary.get("description"))
    if description is None:
        description = _text(article.get("description"))
        if description is None:
            errors.append(_e("missing-description", "Neither summary.description nor description is set."))
        else:
            warnings.append(_e("description-fallback", "summary.description is empty; the article description was used as the meta description."))

    subtitle = _text(headline.get("subTitle"))
    if subtitle is None:
        po = _text(headline.get("promptOutput"))
        if po and "<" not in po:
            subtitle = po
        else:
            warnings.append(_e("no-subtitle", "No subtitle found in the headline block."))

    ap_in = {} if approval is None else approval
    if not isinstance(ap_in, dict):
        errors.append(_e("malformed-approval", "The approval record must be a JSON object."))
        ap_in = {}
    if OVERRIDE_KEY in ap_in or OVERRIDE_KEY in article:
        errors.append(_e("unsupported-override", f"{OVERRIDE_KEY} is not supported and is never honored."))
    ignored = sorted(set(ap_in) - set(APPROVAL_KEYS) - {"card_excerpt"} - {OVERRIDE_KEY})
    if ignored:
        warnings.append(_e("ignored-approval-key", f"Ignored approval fields: {', '.join(ignored)}."))
    if not ap_in:
        warnings.append(_e("no-approval-record", "No approval record supplied; the importer will refuse until it is."))
    approval_out = {k: ap_in[k] for k in APPROVAL_KEYS if k in ap_in}

    excerpt = _text(ap_in.get("card_excerpt")) or description
    if excerpt and len(excerpt) > al.EXCERPT_MAX:
        warnings.append(_e("excerpt-too-long", f"Card excerpt is {len(excerpt)} characters; the importer limit is {al.EXCERPT_MAX} and never truncates. Provide approval.card_excerpt."))

    preview = _text(summary.get("imageUrl")) or _text(article.get("previewImageUrl")) or _text(headline.get("imageUrl"))
    image_out = {}
    if image:
        image_out = {"file": image.get("file", ""), "source_url": image.get("source_url") or preview or ""}

    if errors:
        raise BuildRefused(errors, warnings)

    out_blocks = []
    if headline:
        out_blocks.append({"type": "HEADLINE_COMBO", "index": headline["index"], "title": normalize_title(headline.get("title")) or title,
                           "subTitle": subtitle, "html": None, "links": []})
    out_blocks += body_blocks
    snapshot = {
        "_comment": "Built by scripts/build_snapshot.py from raw Letterman connector output. Contains article text: do not commit or push without the owner's approval.",
        "letterman": {
            "id": article["id"], "publication_id": article["storageId"], "state": "PUBLISHED", "url_path": slug,
            "public_url": article.get("publicUrl") if isinstance(article.get("publicUrl"), str) else "",
            "no_index": article["noIndex"], "title": title, "description": description, "summary_description": excerpt,
            "keywords": keywords, "published_at": article["publishedAt"].strip(), "preview_image_url": preview or "",
            "blocks": out_blocks,
        },
        "approval": approval_out,
        "image": image_out,
    }
    return snapshot, warnings


def compare_snapshots(a, b):
    """Names of the fields that differ between two builds of the same article. Never returns the text itself."""
    diffs = []
    la, lb = a["letterman"], b["letterman"]
    for k in sorted(set(la) | set(lb)):
        if k != "blocks" and la.get(k) != lb.get(k):
            diffs.append(f"letterman.{k}")
    ba, bb = la.get("blocks", []), lb.get("blocks", [])
    if len(ba) != len(bb):
        diffs.append("letterman.blocks.count")
    else:
        for x, y in zip(ba, bb):
            for k in sorted(set(x) | set(y)):
                if x.get(k) != y.get(k):
                    diffs.append(f"letterman.blocks[{x.get('index')}].{k}")
    return diffs


def _load(path, label):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise BuildRefused([_e("unreadable-input", f"{label} file not found: {path}")])
    except (OSError, ValueError):
        raise BuildRefused([_e("unreadable-input", f"{label} file is not valid JSON: {path}")])


def _image_arg(root, slug, image_file, source_url):
    if not image_file:
        return None
    rel = Path(image_file).as_posix()
    if not re.fullmatch(re.escape(al.IMAGE_DIR) + r"/" + re.escape(slug) + r"\.(jpg|jpeg|png|webp)", rel):
        raise BuildRefused([_e("image-path", f"--image-file must be {al.IMAGE_DIR}/{slug}.(jpg|jpeg|png|webp); got {rel!r}.")])
    return {"file": rel, "source_url": source_url}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--article", required=True, help="raw get_article output (JSON file)")
    ap.add_argument("--blocks", required=True, help="raw list_content_blocks output (JSON file)")
    ap.add_argument("--approval", help="owner-supplied approval record (JSON file)")
    ap.add_argument("--image-file", help="image already stored in the repo at arlington/images/articles/<slug>.<ext>")
    ap.add_argument("--image-source-url", default="", help="where the image came from (default: the article's image URL)")
    ap.add_argument("--reread-article", help="a SECOND get_article read of the same article")
    ap.add_argument("--reread-blocks", help="a SECOND list_content_blocks read of the same article")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--dry-run", action="store_true", help="check and report; write nothing")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing snapshot")
    args = ap.parse_args(argv)
    root = Path(args.root)
    try:
        if bool(args.reread_article) != bool(args.reread_blocks):
            raise BuildRefused([_e("usage", "--reread-article and --reread-blocks must be given together.")])
        article, blocks = _load(args.article, "article"), _load(args.blocks, "blocks")
        approval = _load(args.approval, "approval") if args.approval else None
        slug = article.get("urlPath") if isinstance(article, dict) else None
        image = _image_arg(root, slug, args.image_file, args.image_source_url) if args.image_file and isinstance(slug, str) else None
        if args.image_file and not isinstance(slug, str):
            raise BuildRefused([_e("missing-slug", "Cannot place an image for an article without a slug.")])
        snapshot, warnings = build_snapshot(article, blocks, approval, image)
        if args.reread_article:
            second, _ = build_snapshot(_load(args.reread_article, "re-read article"), _load(args.reread_blocks, "re-read blocks"),
                                       approval, image)
            diffs = compare_snapshots(snapshot, second)
            if diffs:
                raise BuildRefused([_e("reread-mismatch", "The two reads of the article disagree (or the article changed): " + ", ".join(diffs))], warnings)
        slug = snapshot["letterman"]["url_path"]
        out = Path(args.root, SNAPSHOT_DIR, f"{slug}.json")
        resolved_dir = (root / SNAPSHOT_DIR).resolve()
        if out.resolve().parent != resolved_dir:
            raise BuildRefused([_e("bad-output-path", "Snapshots are only written to content/letterman/<slug>.json.")], warnings)
        if out.exists() and not args.overwrite and not args.dry_run:
            raise BuildRefused([_e("snapshot-exists", f"{SNAPSHOT_DIR}/{slug}.json already exists; use --overwrite to replace it.")], warnings)
    except BuildRefused as exc:
        print("BUILD REFUSED. Nothing was written.")
        for e in exc.errors:
            print(f"  - [{e['code']}] {e['message']}")
        for w in exc.warnings:
            print(f"  warning [{w['code']}] {w['message']}")
        return 1
    for w in warnings:
        print(f"  warning [{w['code']}] {w['message']}")
    errs, warns = al.validate_snapshot(snapshot, root, check_files=True)
    if args.dry_run:
        print(f"DRY RUN: would write {SNAPSHOT_DIR}/{slug}.json")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {SNAPSHOT_DIR}/{slug}.json  (contains article text: do not commit or push without the owner's approval)")
    if errs:
        print("importer validation: would REFUSE until fixed:")
        for e in errs:
            print(f"  - [{e['code']}] {e['message']}")
    else:
        print("importer validation: no errors")
    for w in warns:
        print(f"  importer warning [{w['code']}] {w['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
