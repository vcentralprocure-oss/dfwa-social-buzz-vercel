"""Tests for scripts/build_snapshot.py (raw Letterman connector output -> importer snapshot).

All data here is SYNTHETIC. It mirrors the SHAPE of get_article and list_content_blocks output, including the quirks seen
in real published articles (block-level state reading DRAFT, a '| Arlington Pulse' title suffix, a null headline subTitle).
Imports run only in temporary directories.
"""

import copy
import io
import json
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import article_lib as al  # noqa: E402
import build_snapshot as bs  # noqa: E402
import import_letterman_article as imp  # noqa: E402
import seo_lib  # noqa: E402

CFG = seo_lib.load_config()
SLUG = "synthetic-lantern-walk"
ARTICLE_ID = "6a0000000000000000000001"
BODY = "<p>SYNTHETIC body paragraph one.</p><p>&nbsp;</p><p>SYNTHETIC body paragraph two.</p>"
APPROVAL = {
    "approved_by": "Synthetic Owner", "approved_at": "2026-10-26", "site_publish_date": "2026-10-26",
    "image_alt": "Synthetic test image", "quadrant": "all", "quadrant_evidence": "", "manual_review": True,
}


def raw_article(**over):
    a = {
        "id": ARTICLE_ID, "storageId": bs.ARLINGTON_PULSE_ID, "title": "SYNTHETIC Lantern Walk | Arlington Pulse",
        "state": "PUBLISHED", "description": "A synthetic subheadline.", "urlPath": SLUG, "keywords": ["synthetic", "walk"],
        "summary": {"title": "SYNTHETIC Lantern Walk", "description": "Synthetic meta description for tests.",
                    "imageUrl": "https://example.invalid/hero.png", "content": "<p>x</p>"},
        "previewImageUrl": "https://example.invalid/card.png", "publishedAt": "2026-10-26T00:00:00.000Z",
        "noIndex": False, "publicUrl": f"https://example.invalid/a/{SLUG}",
    }
    a.update(over)
    return a


def block(btype, index, **over):
    b = {"id": "6a0000000000000000000100", "type": btype, "index": index, "title": "Text ", "subTitle": None,
         "imageUrl": None, "promptOutput": None, "state": "DRAFT", "isActive": True, "links": []}
    b.update(over)
    return b


def raw_blocks(blocks=None, **kw):
    if blocks is None:
        blocks = [block("HEADLINE_COMBO", 0, title="SYNTHETIC Lantern Walk", subTitle="A synthetic subheadline."),
                  block("TEXT", 1, promptOutput=BODY)]
    return {"contentBlocks": blocks}


def codes(exc):
    return {e["code"] for e in exc.exception.errors}


_DEFAULT = object()


def refused(article, blocks=_DEFAULT, **kw):
    try:
        bs.build_snapshot(article, raw_blocks() if blocks is _DEFAULT else blocks, **kw)
    except bs.BuildRefused as exc:
        return {e["code"] for e in exc.errors}
    raise AssertionError("build was not refused")


class EligibilityTests(unittest.TestCase):
    def test_published_article_is_eligible(self):
        self.assertEqual(bs.check_eligibility(raw_article()), [])

    def test_every_state_that_is_not_exactly_published_is_refused(self):
        for state in (None, "", "DRAFT", "draft", "Draft", "Published", "published", " PUBLISHED", "PUBLISHED ", "UNPUBLISHED",
                      "ARCHIVED", "SCHEDULED", "PENDING", True, False, 1, 0, ["PUBLISHED"], {"state": "PUBLISHED"}):
            got = refused(raw_article(state=state))
            self.assertTrue(got & {"state-missing-or-invalid", "not-published"}, repr(state))

    def test_missing_state_key_is_refused(self):
        a = raw_article()
        del a["state"]
        self.assertIn("state-missing-or-invalid", refused(a))

    def test_published_without_a_readable_publishedAt_is_ambiguous_and_refused(self):
        for value in (None, "", "   ", "yesterday", 20261026, "2026-13-45T00:00:00Z", ["2026-10-26"]):
            self.assertIn("ambiguous-published", refused(raw_article(publishedAt=value)), repr(value))
        a = raw_article()
        del a["publishedAt"]
        self.assertIn("ambiguous-published", refused(a))

    def test_draft_is_refused_even_with_publishedAt_and_published_looking_blocks(self):
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, state="PUBLISHED"), block("TEXT", 1, promptOutput=BODY, state="PUBLISHED")])
        self.assertIn("not-published", refused(raw_article(state="DRAFT", publishedAt="2026-10-26T00:00:00Z"), blocks))

    def test_block_level_state_is_never_consulted(self):
        for block_state in ("DRAFT", "PUBLISHED", None, "garbage", 7):
            blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T", subTitle="S", state=block_state),
                                 block("TEXT", 1, promptOutput=BODY, state=block_state)])
            snap, _ = bs.build_snapshot(raw_article(), blocks)
            self.assertEqual(snap["letterman"]["state"], "PUBLISHED", repr(block_state))

    def test_wrong_or_missing_publication_is_refused(self):
        self.assertIn("wrong-publication", refused(raw_article(storageId="69bf42c447872b28b4eccd74")))
        a = raw_article()
        del a["storageId"]
        self.assertIn("wrong-publication", refused(a))

    def test_non_object_articles_are_malformed(self):
        for bad in (None, [], "PUBLISHED", 5, True):
            with self.assertRaises(bs.BuildRefused) as exc:
                bs.build_snapshot(bad, raw_blocks())
            self.assertIn("malformed-article", codes(exc), repr(bad))


class MappingTests(unittest.TestCase):
    def build(self, article=None, blocks=None, **kw):
        return bs.build_snapshot(article or raw_article(), blocks or raw_blocks(), **kw)

    def test_title_suffix_is_normalized_only_at_the_end(self):
        cases = {"Weekend Guide | Arlington Pulse": "Weekend Guide", "Weekend Guide|Arlington Pulse": "Weekend Guide",
                 "  Weekend Guide  |  Arlington Pulse  ": "Weekend Guide", "Arlington Pulse | Weekend Guide": "Arlington Pulse | Weekend Guide",
                 "About Arlington Pulse readers": "About Arlington Pulse readers"}
        for raw, want in cases.items():
            a = raw_article(summary={"title": raw, "description": "m"})
            self.assertEqual(self.build(a)[0]["letterman"]["title"], want, raw)

    def test_title_falls_back_through_headline_then_article_and_never_to_just_the_suffix(self):
        a = raw_article(summary={"title": "| Arlington Pulse", "description": "m"})
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="Headline Title | Arlington Pulse"), block("TEXT", 1, promptOutput=BODY)])
        self.assertEqual(self.build(a, blocks)[0]["letterman"]["title"], "Headline Title")
        a = raw_article(summary={"description": "m"}, title="Article Title | Arlington Pulse")
        blocks = raw_blocks([block("TEXT", 1, promptOutput=BODY)])
        self.assertEqual(self.build(a, blocks)[0]["letterman"]["title"], "Article Title")
        a = raw_article(summary={"description": "m"}, title="| Arlington Pulse")
        self.assertIn("missing-title", refused(a, blocks))

    def test_subtitle_comes_from_subTitle_when_present(self):
        snap, _ = self.build()
        self.assertEqual(al.subtitle_of(snap), "A synthetic subheadline.")

    def test_subtitle_comes_from_promptOutput_when_subTitle_is_null(self):
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T", subTitle=None, promptOutput="Plain subtitle text."),
                             block("TEXT", 1, promptOutput=BODY)])
        snap, _ = self.build(blocks=blocks)
        self.assertEqual(al.subtitle_of(snap), "Plain subtitle text.")

    def test_markup_in_promptOutput_is_not_used_as_a_subtitle(self):
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T", subTitle=None, promptOutput="<p>markup</p>"),
                             block("TEXT", 1, promptOutput=BODY)])
        snap, warnings = self.build(blocks=blocks)
        self.assertEqual(al.subtitle_of(snap), "")
        self.assertIn("no-subtitle", {w["code"] for w in warnings})

    def test_meta_description_prefers_summary_description(self):
        snap, warnings = self.build()
        self.assertEqual(snap["letterman"]["description"], "Synthetic meta description for tests.")
        self.assertNotIn("description-fallback", {w["code"] for w in warnings})

    def test_meta_description_falls_back_to_article_description_with_a_warning(self):
        for summary in ({"title": "T"}, {"title": "T", "description": ""}, {"title": "T", "description": "   "},
                        {"title": "T", "description": None}, None):
            snap, warnings = self.build(raw_article(summary=summary))
            self.assertEqual(snap["letterman"]["description"], "A synthetic subheadline.", repr(summary))
            self.assertIn("description-fallback", {w["code"] for w in warnings})

    def test_missing_description_everywhere_is_refused(self):
        a = raw_article(summary={"title": "T"}, description="  ")
        self.assertIn("missing-description", refused(a))

    def test_card_excerpt_prefers_approval_then_summary_and_is_never_truncated(self):
        snap, _ = self.build(approval={**APPROVAL, "card_excerpt": "Owner approved excerpt."})
        self.assertEqual(snap["letterman"]["summary_description"], "Owner approved excerpt.")
        snap, _ = self.build()
        self.assertEqual(snap["letterman"]["summary_description"], "Synthetic meta description for tests.")
        long_text = "x" * 200
        snap, warnings = self.build(raw_article(summary={"title": "T", "description": long_text}))
        self.assertEqual(snap["letterman"]["summary_description"], long_text)
        self.assertIn("excerpt-too-long", {w["code"] for w in warnings})

    def test_body_is_the_active_text_blocks_in_index_order(self):
        blocks = raw_blocks([block("TEXT", 3, promptOutput="<p>third</p>"), block("HEADLINE_COMBO", 0, title="T"),
                             block("TEXT", 1, promptOutput="<p>first</p>"), block("TEXT", 2, promptOutput="<p>hidden</p>", isActive=False),
                             block("IMAGE", 4, isActive=False)])
        snap, _ = self.build(blocks=blocks)
        self.assertEqual(al.body_html_of(snap), "<p>first</p><p>third</p>")

    def test_image_selection_order_and_source_url(self):
        snap, _ = self.build(image={"file": f"arlington/images/articles/{SLUG}.png", "source_url": ""})
        self.assertEqual(snap["letterman"]["preview_image_url"], "https://example.invalid/hero.png")
        self.assertEqual(snap["image"]["source_url"], "https://example.invalid/hero.png")
        a = raw_article(summary={"title": "T", "description": "m"})
        self.assertEqual(self.build(a)[0]["letterman"]["preview_image_url"], "https://example.invalid/card.png")
        a = raw_article(summary={"title": "T", "description": "m"}, previewImageUrl=None)
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T", imageUrl="https://example.invalid/headline.png"), block("TEXT", 1, promptOutput=BODY)])
        self.assertEqual(self.build(a, blocks)[0]["letterman"]["preview_image_url"], "https://example.invalid/headline.png")

    def test_keywords_default_to_empty_and_noindex_passes_through(self):
        a = raw_article(noIndex=True)
        del a["keywords"]
        snap, _ = self.build(a)
        self.assertEqual(snap["letterman"]["keywords"], [])
        self.assertIs(snap["letterman"]["no_index"], True)

    def test_approval_is_filtered_and_the_draft_override_is_never_propagated(self):
        snap, warnings = self.build(approval={**APPROVAL, "surprise": 1})
        self.assertEqual(set(snap["approval"]), set(bs.APPROVAL_KEYS))
        self.assertIn("ignored-approval-key", {w["code"] for w in warnings})
        self.assertIn("unsupported-override", refused(raw_article(), approval={**APPROVAL, "allow_draft_state": True}))
        self.assertIn("unsupported-override", refused(raw_article(allow_draft_state=True)))

    def test_no_approval_builds_with_a_warning_and_the_importer_decides(self):
        snap, warnings = self.build()
        self.assertEqual(snap["approval"], {})
        self.assertIn("no-approval-record", {w["code"] for w in warnings})

    def test_malformed_approval_is_refused(self):
        for bad in ([], "approved", 5, ["x"]):
            self.assertIn("malformed-approval", refused(raw_article(), approval=bad), repr(bad))


class MalformedAndIncompleteTests(unittest.TestCase):
    def test_malformed_block_documents(self):
        for bad in (None, [], {}, {"contentBlocks": None}, {"contentBlocks": "x"}, {"contentBlocks": {"a": 1}}, "blocks", 5):
            self.assertIn("malformed-blocks", refused(raw_article(), bad), repr(bad))

    def test_malformed_block_entries(self):
        for bad in (5, None, "x", ["a"]):
            self.assertIn("malformed-block", refused(raw_article(), raw_blocks([block("TEXT", 1, promptOutput=BODY), bad])), repr(bad))

    def test_ambiguous_active_flag_is_refused(self):
        for value in (None, "true", 1, 0, "false"):
            b = block("TEXT", 1, promptOutput=BODY)
            b["isActive"] = value
            self.assertIn("ambiguous-block-active", refused(raw_article(), raw_blocks([block("HEADLINE_COMBO", 0, title="T"), b])), repr(value))
        b = block("TEXT", 1, promptOutput=BODY)
        del b["isActive"]
        self.assertIn("ambiguous-block-active", refused(raw_article(), raw_blocks([b])))

    def test_active_blocks_that_would_be_dropped_are_refused(self):
        for btype in ("IMAGE", "SPONSOR_SPOT", "AI_ARTICLE", None, "text", 5):
            blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T"), block("TEXT", 1, promptOutput=BODY), block(btype, 2)])
            self.assertIn("unsupported-block", refused(raw_article(), blocks), repr(btype))

    def test_block_index_problems(self):
        for index in ("1", 1.5, True, None):
            blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T"), block("TEXT", index, promptOutput=BODY)])
            self.assertIn("malformed-block-index", refused(raw_article(), blocks), repr(index))
        blocks = raw_blocks([block("TEXT", 1, promptOutput=BODY), block("TEXT", 1, promptOutput="<p>again</p>")])
        self.assertIn("duplicate-block-index", refused(raw_article(), blocks))

    def test_multiple_headline_blocks_are_ambiguous(self):
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="A"), block("HEADLINE_COMBO", 1, title="B"), block("TEXT", 2, promptOutput=BODY)])
        self.assertIn("multiple-headline-blocks", refused(raw_article(), blocks))

    def test_text_and_body_problems(self):
        self.assertIn("malformed-block", refused(raw_article(), raw_blocks([block("HEADLINE_COMBO", 0, title="T"), block("TEXT", 1, promptOutput=5)])))
        for body in (None, "", "   \n"):
            blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="T"), block("TEXT", 1, promptOutput=body)])
            self.assertIn("missing-body", refused(raw_article(), blocks), repr(body))
        self.assertIn("missing-body", refused(raw_article(), raw_blocks([block("HEADLINE_COMBO", 0, title="T")])))
        self.assertIn("missing-body", refused(raw_article(), raw_blocks([])))

    def test_incomplete_article_fields(self):
        for bad_id in (None, "", "abc", "6A0000000000000000000001", "6a000000000000000000000g", 5):
            self.assertIn("missing-or-invalid-id", refused(raw_article(id=bad_id)), repr(bad_id))
        for slug in (None, "", "   "):
            self.assertIn("missing-slug", refused(raw_article(urlPath=slug)), repr(slug))
        for slug in ("Has Space", "UPPER", "-lead", "trail-", "dou--ble", " padded", "padded ", "x" * (al.SLUG_MAX + 1), "under_score"):
            self.assertIn("invalid-slug", refused(raw_article(urlPath=slug)), repr(slug))
        self.assertIn("id-style-slug", refused(raw_article(urlPath=ARTICLE_ID)))
        a = raw_article()
        del a["urlPath"]
        self.assertIn("missing-slug", refused(a))

    def test_noindex_must_be_a_real_boolean(self):
        for value in (None, "false", "true", 0, 1, [], ""):
            self.assertIn("noindex-missing-or-invalid", refused(raw_article(noIndex=value)), repr(value))
        a = raw_article()
        del a["noIndex"]
        self.assertIn("noindex-missing-or-invalid", refused(a))

    def test_keywords_and_summary_shapes(self):
        for bad in ("a,b", [1, 2], {"a": 1}, ["ok", 3]):
            self.assertIn("malformed-keywords", refused(raw_article(keywords=bad)), repr(bad))
        for bad in ("text", [], 5):
            self.assertIn("malformed-summary", refused(raw_article(summary=bad)), repr(bad))

    def test_title_missing_everywhere(self):
        a = raw_article(summary={"description": "m"}, title=None)
        self.assertIn("missing-title", refused(a, raw_blocks([block("TEXT", 1, promptOutput=BODY)])))

    def test_all_reasons_are_reported_together(self):
        a = raw_article(state="DRAFT", noIndex=None, urlPath=None)
        got = refused(a, {"contentBlocks": []})
        self.assertTrue({"not-published", "noindex-missing-or-invalid", "missing-slug", "missing-body"} <= got, got)

    def test_nothing_defaults_to_eligible_for_an_empty_article(self):
        self.assertTrue(refused({}, raw_blocks()))
        self.assertIn("state-missing-or-invalid", refused({}, raw_blocks()))


# --------------------------------------------------------------------------- integration with the importer
def make_jpeg(width=1200, height=630):
    sof = b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", height, width) + b"\x03" + b"\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + sof + b"\xff\xd9"


class SiteCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "templates").mkdir()
        (self.root / al.TEMPLATE_PATH).write_bytes((REPO / al.TEMPLATE_PATH).read_bytes())
        (self.root / "arlington" / "articles").mkdir(parents=True)
        self.hub_bytes = (REPO / al.HUB_PATH).read_bytes()
        (self.root / al.HUB_PATH).write_bytes(self.hub_bytes)
        (self.root / "arlington/images/articles").mkdir(parents=True)
        self.image_rel = f"arlington/images/articles/{SLUG}.jpg"
        (self.root / self.image_rel).write_bytes(make_jpeg())
        self.inputs = self.root / "_inputs"
        self.inputs.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def save(self, name, obj):
        p = self.inputs / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        return str(p)

    def run_cli(self, article=None, blocks=None, approval=APPROVAL, image=True, extra=()):
        argv = ["--article", self.save("article.json", raw_article() if article is None else article),
                "--blocks", self.save("blocks.json", raw_blocks() if blocks is None else blocks), "--root", str(self.root)]
        if approval is not None:
            argv += ["--approval", self.save("approval.json", approval)]
        if image:
            argv += ["--image-file", self.image_rel]
        argv += list(extra)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = bs.main(argv)
        return rc, buf.getvalue()

    @property
    def snap_path(self):
        return self.root / "content/letterman" / f"{SLUG}.json"


class IntegrationTests(SiteCase):
    def import_built(self):
        return imp.import_article(self.root, self.snap_path, CFG)

    def test_wizard_style_article_goes_from_raw_output_to_a_page_without_manual_assembly(self):
        rc, out = self.run_cli()
        self.assertEqual(rc, 0, out)
        self.assertIn("importer validation: no errors", out)
        result = self.import_built()
        self.assertTrue(result["hub_card"])
        page = (self.root / al.PAGE_DIR / f"{SLUG}.html").read_text(encoding="utf-8")
        self.assertIn(f'<link rel="canonical" href="https://dfwasocialbuzz.com/arlington/articles/{SLUG}.html">', page)
        self.assertIn("<title>SYNTHETIC Lantern Walk | Arlington Pulse</title>", page)
        self.assertNotIn("Arlington Pulse | Arlington Pulse", page)
        self.assertEqual(imp.verify_all(self.root), [])

    def test_legacy_style_article_with_suffix_and_null_subtitle_imports(self):
        article = raw_article(title="Weekend Guide | Arlington Pulse",
                              summary={"title": "Weekend Guide", "description": "Same text as the description.", "imageUrl": "https://example.invalid/h.jpg"},
                              description="Same text as the description.")
        blocks = raw_blocks([block("HEADLINE_COMBO", 0, title="Weekend Guide", subTitle=None, promptOutput="Same text as the description."),
                             block("TEXT", 1, promptOutput=BODY)])
        rc, out = self.run_cli(article, blocks)
        self.assertEqual(rc, 0, out)
        self.import_built()
        self.assertEqual(imp.verify_all(self.root), [])

    def test_a_draft_never_produces_a_snapshot(self):
        for state in ("DRAFT", None, "published", "PUBLISHED "):
            rc, out = self.run_cli(raw_article(state=state))
            self.assertEqual(rc, 1, repr(state))
            self.assertIn("BUILD REFUSED. Nothing was written.", out)
            self.assertFalse(self.snap_path.exists(), repr(state))
            self.assertFalse((self.root / "content").exists(), repr(state))

    def test_missing_approval_builds_but_the_importer_refuses(self):
        rc, out = self.run_cli(approval=None)
        self.assertEqual(rc, 0, out)
        self.assertIn("importer validation: would REFUSE", out)
        with self.assertRaises(al.ImportRefused) as exc:
            self.import_built()
        self.assertIn("missing-approval", {e["code"] for e in exc.exception.errors})
        self.assertFalse((self.root / al.PAGE_DIR / f"{SLUG}.html").exists())

    def test_missing_image_builds_but_the_importer_refuses(self):
        (self.root / self.image_rel).unlink()
        rc, out = self.run_cli()
        self.assertEqual(rc, 0, out)
        with self.assertRaises(al.ImportRefused) as exc:
            self.import_built()
        self.assertIn("missing-image", {e["code"] for e in exc.exception.errors})

    def test_importer_refuses_a_built_snapshot_whose_state_is_tampered_with(self):
        self.assertEqual(self.run_cli()[0], 0)
        snap = json.loads(self.snap_path.read_text(encoding="utf-8"))
        snap["letterman"]["state"] = "DRAFT"
        snap["approval"]["allow_draft_state"] = True
        self.snap_path.write_text(json.dumps(snap), encoding="utf-8")
        with self.assertRaises(al.ImportRefused) as exc:
            self.import_built()
        self.assertTrue({"draft-not-approved", "unsupported-override"} <= {e["code"] for e in exc.exception.errors})
        self.assertEqual((self.root / al.HUB_PATH).read_bytes(), self.hub_bytes)

    def test_noindex_article_gets_a_noindex_page_and_no_hub_card(self):
        rc, out = self.run_cli(raw_article(noIndex=True))
        self.assertEqual(rc, 0, out)
        result = self.import_built()
        self.assertFalse(result["hub_card"])
        self.assertTrue(seo_lib.has_noindex((self.root / al.PAGE_DIR / f"{SLUG}.html").read_text(encoding="utf-8")))


class CliTests(SiteCase):
    def test_dry_run_writes_nothing(self):
        rc, out = self.run_cli(extra=["--dry-run"])
        self.assertEqual(rc, 0, out)
        self.assertIn("DRY RUN", out)
        self.assertFalse((self.root / "content").exists())

    def test_existing_snapshot_is_not_replaced_without_overwrite(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.snap_path.read_bytes()
        rc, out = self.run_cli(raw_article(keywords=["changed"]))
        self.assertEqual(rc, 1)
        self.assertIn("snapshot-exists", out)
        self.assertEqual(self.snap_path.read_bytes(), before)
        self.assertEqual(self.run_cli(raw_article(keywords=["changed"]), extra=["--overwrite"])[0], 0)
        self.assertIn("changed", self.snap_path.read_text(encoding="utf-8"))

    def test_only_content_letterman_is_ever_written(self):
        self.assertEqual(self.run_cli()[0], 0)
        written = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()
                         and not p.relative_to(self.root).as_posix().startswith(("_inputs", "templates", "arlington")))
        self.assertEqual(written, [f"content/letterman/{SLUG}.json"])

    def test_image_path_must_match_the_slug(self):
        (self.root / "arlington/images/articles/other.jpg").write_bytes(make_jpeg())
        rc, out = self.run_cli(image=False, extra=["--image-file", "arlington/images/articles/other.jpg"])
        self.assertEqual(rc, 1)
        self.assertIn("image-path", out)
        self.assertFalse((self.root / "content").exists())

    def test_unreadable_input_is_refused_without_echoing_its_content(self):
        bad = self.inputs / "article.json"
        bad.write_text("{ SECRET-LOOKING-TEXT not json", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = bs.main(["--article", str(bad), "--blocks", self.save("blocks.json", raw_blocks()), "--root", str(self.root)])
        self.assertEqual(rc, 1)
        self.assertIn("unreadable-input", buf.getvalue())
        self.assertNotIn("SECRET-LOOKING-TEXT", buf.getvalue())
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = bs.main(["--article", str(self.inputs / "nope.json"), "--blocks", str(self.inputs / "nope2.json"), "--root", str(self.root)])
        self.assertEqual(rc, 1)

    def test_reread_that_matches_is_accepted(self):
        extra = ["--reread-article", self.save("a2.json", raw_article()), "--reread-blocks", self.save("b2.json", raw_blocks())]
        rc, out = self.run_cli(extra=extra)
        self.assertEqual(rc, 0, out)
        self.assertTrue(self.snap_path.exists())

    def test_reread_that_disagrees_is_refused_by_field_name_only(self):
        changed = raw_blocks([block("HEADLINE_COMBO", 0, title="SYNTHETIC Lantern Walk", subTitle="A synthetic subheadline."),
                              block("TEXT", 1, promptOutput=BODY.replace("two", "TWO-EDITED-MARKER"))])
        extra = ["--reread-article", self.save("a2.json", raw_article()), "--reread-blocks", self.save("b2.json", changed)]
        rc, out = self.run_cli(extra=extra)
        self.assertEqual(rc, 1)
        self.assertIn("reread-mismatch", out)
        self.assertIn("letterman.blocks[1].html", out)
        self.assertNotIn("TWO-EDITED-MARKER", out)
        self.assertFalse(self.snap_path.exists())

    def test_reread_that_shows_the_article_was_unpublished_is_refused(self):
        extra = ["--reread-article", self.save("a2.json", raw_article(state="DRAFT")), "--reread-blocks", self.save("b2.json", raw_blocks())]
        rc, out = self.run_cli(extra=extra)
        self.assertEqual(rc, 1)
        self.assertIn("not-published", out)
        self.assertFalse(self.snap_path.exists())

    def test_reread_flags_must_come_together(self):
        rc, out = self.run_cli(extra=["--reread-article", self.save("a2.json", raw_article())])
        self.assertEqual(rc, 1)
        self.assertIn("usage", out)
        self.assertFalse(self.snap_path.exists())

    def test_compare_snapshots_names_fields_not_text(self):
        a, _ = bs.build_snapshot(raw_article(), raw_blocks())
        b = copy.deepcopy(a)
        self.assertEqual(bs.compare_snapshots(a, b), [])
        b["letterman"]["title"] = "Other"
        b["letterman"]["blocks"][1]["html"] = "<p>other</p>"
        self.assertEqual(bs.compare_snapshots(a, b), ["letterman.title", "letterman.blocks[1].html"])
        b["letterman"]["blocks"].pop()
        self.assertEqual(bs.compare_snapshots(a, b), ["letterman.title", "letterman.blocks.count"])


if __name__ == "__main__":
    unittest.main()
