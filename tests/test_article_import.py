"""Tests for the Letterman -> local Arlington article pipeline.

The snapshot in tests/fixtures/sample_festival/ is a SYNTHETIC TEST FIXTURE. It mirrors the
structure of a real unpublished Letterman draft (DRAFT state, no approval, a 151-character
description, no link URLs) with invented text. It is imported only into temporary
directories; nothing here writes into the real arlington/articles/ and nothing touches Letterman.
"""

import copy
import json
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import article_lib as al  # noqa: E402
import import_letterman_article as imp  # noqa: E402
import link_gate  # noqa: E402
import seo_lib  # noqa: E402

FIXTURE = json.loads((REPO / "tests/fixtures/sample_festival/snapshot.json").read_text(encoding="utf-8"))
SLUG = FIXTURE["letterman"]["url_path"]
IMG_REL = f"arlington/images/articles/{SLUG}.jpg"
CFG = seo_lib.load_config()


def make_jpeg(width=1200, height=630):
    sof = b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", height, width) + b"\x03" + b"\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + sof + b"\xff\xd9"


def approved(**over):
    snap = copy.deepcopy(FIXTURE)
    snap["letterman"]["state"] = "PUBLISHED"
    snap["approval"] = {
        "approved_by": "Test Owner",
        "approved_at": "2026-10-12",
        "site_publish_date": "2026-10-12",
        "image_alt": "Lanterns at a sample festival (test alt text)",
        "quadrant": "central",
        "quadrant_evidence": "Test fixture: venue address stated in the article body.",
        "manual_review": False,
    }
    for k, v in over.items():
        snap[k] = v
    return snap


class SiteCase(unittest.TestCase):
    """A temporary site built from the real template and the real hub page."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "templates").mkdir()
        (self.root / al.TEMPLATE_PATH).write_bytes((REPO / al.TEMPLATE_PATH).read_bytes())
        (self.root / "arlington" / "articles").mkdir(parents=True)
        self.hub_bytes = (REPO / al.HUB_PATH).read_bytes()
        (self.root / al.HUB_PATH).write_bytes(self.hub_bytes)
        (self.root / "arlington/images/articles").mkdir(parents=True)
        (self.root / IMG_REL).write_bytes(make_jpeg())
        self.snap_path = self.root / "content/letterman" / f"{SLUG}.json"
        self.snap_path.parent.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write_snap(self, snap):
        self.snap_path.write_text(json.dumps(snap), encoding="utf-8")
        return self.snap_path

    def page_text(self):
        return (self.root / al.PAGE_DIR / f"{SLUG}.html").read_text(encoding="utf-8")

    def hub_now(self):
        return (self.root / al.HUB_PATH).read_bytes()

    def run_import(self, snap, **kw):
        return imp.import_article(self.root, self.write_snap(snap), CFG, **kw)

    def refused_codes(self, snap):
        try:
            self.run_import(snap)
        except al.ImportRefused as exc:
            return {e["code"] for e in exc.errors}
        self.fail("import was not refused")


class DraftProtectionTests(SiteCase):
    def test_sample_fixture_as_is_is_refused_and_nothing_is_written(self):
        codes = self.refused_codes(copy.deepcopy(FIXTURE))
        self.assertIn("draft-not-approved", codes)
        self.assertIn("missing-approval", codes)
        self.assertFalse((self.root / al.PAGE_DIR / f"{SLUG}.html").exists())
        self.assertEqual(self.hub_now(), self.hub_bytes)
        self.assertFalse((self.root / "sitemap.xml").exists())

    def test_complete_approval_record_does_not_override_a_draft_state(self):
        snap = approved()
        snap["letterman"]["state"] = "DRAFT"
        self.assertIn("draft-not-approved", self.refused_codes(snap))

    def test_unapproved_published_article_is_refused(self):
        snap = copy.deepcopy(FIXTURE)
        snap["letterman"]["state"] = "PUBLISHED"
        self.assertIn("missing-approval", self.refused_codes(snap))

    def test_explicit_draft_override_is_the_only_way_through(self):
        snap = approved()
        snap["letterman"]["state"] = "DRAFT"
        snap["approval"]["allow_draft_state"] = True
        errors, _ = al.validate_snapshot(snap, self.root)
        self.assertNotIn("draft-not-approved", {e["code"] for e in errors})

    def test_importer_does_not_touch_the_snapshot_status(self):
        snap = approved()
        self.run_import(snap)
        on_disk = json.loads(self.snap_path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["letterman"]["state"], "PUBLISHED")  # unchanged from what we wrote


class ValidationTests(SiteCase):
    def codes(self, snap):
        errors, _ = al.validate_snapshot(snap, self.root)
        return {e["code"] for e in errors}

    def test_good_snapshot_has_no_errors(self):
        errors, _ = al.validate_snapshot(approved(), self.root)
        self.assertEqual(errors, [])

    def test_slug_rules(self):
        for bad in ("Has-Upper", "has_underscore", "double--hyphen", "-leading", "trailing-", "x" * 101, ""):
            snap = approved()
            snap["letterman"]["url_path"] = bad
            self.assertTrue(self.codes(snap) & {"invalid-slug", "missing-slug"}, repr(bad))
        snap = approved()
        snap["letterman"]["url_path"] = None
        self.assertIn("missing-slug", self.codes(snap))

    def test_approval_field_rules(self):
        snap = approved()
        snap["approval"]["image_alt"] = ""
        self.assertIn("missing-approval", self.codes(snap))
        snap = approved()
        snap["approval"]["quadrant"] = "west"
        self.assertIn("invalid-quadrant", self.codes(snap))
        snap = approved()
        snap["approval"]["quadrant_evidence"] = ""
        self.assertIn("missing-quadrant-evidence", self.codes(snap))
        snap = approved()
        snap["approval"]["quadrant"] = "all"
        snap["approval"]["quadrant_evidence"] = ""
        self.assertNotIn("missing-quadrant-evidence", self.codes(snap))
        snap = approved()
        snap["approval"]["site_publish_date"] = "10/12/2026"
        self.assertIn("invalid-date", self.codes(snap))

    def test_all_five_quadrant_values_are_accepted(self):
        for q in ("north", "south", "central", "east", "all"):
            snap = approved()
            snap["approval"]["quadrant"] = q
            self.assertNotIn("invalid-quadrant", self.codes(snap), q)

    def test_excerpt_limit_is_enforced_without_truncation(self):
        snap = approved()
        snap["letterman"]["summary_description"] = "x" * 151
        self.assertIn("excerpt-too-long", self.codes(snap))

    def test_sample_description_over_limit_uses_summary_description(self):
        self.assertEqual(len(FIXTURE["letterman"]["description"]), 151)
        self.assertLessEqual(len(al.excerpt_of(approved())), 150)

    def test_body_rules(self):
        for bad in ('<p>ok</p><script>x</script>', '<h2>Head</h2><p>ok</p>', '<p>ok<br></p>',
                    '<p class="x">ok</p>', 'stray text<p>ok</p>', '<p>&nbsp;</p>'):
            snap = approved()
            snap["letterman"]["blocks"][1]["html"] = bad
            self.assertTrue(self.codes(snap) & {"disallowed-tag", "disallowed-attribute", "text-outside-paragraph", "empty-body"}, bad)

    def test_forbidden_links_in_body_are_blocking(self):
        for href, code in (("https://arlington.dfwasocialbuzz.com/x", "forbidden-host"),
                           ("https://m.letterman.ai/a/x", "letterman-article-url"),
                           ("https://dfwasocialbuzz.com/arlington/", "apex-self-link"),
                           ("/arlington/articles/missing.html", "broken-internal-link"),
                           ("javascript:alert(1)", "unsafe-scheme")):
            snap = approved()
            snap["letterman"]["blocks"][1]["html"] = f'<p>See <a href="{href}">this</a></p>'
            self.assertIn(code, self.codes(snap), href)

    def test_image_rules(self):
        path = self.root / IMG_REL
        path.unlink()
        self.assertIn("missing-image", self.codes(approved()))
        path.write_bytes(b"not an image")
        self.assertIn("image-bad-format", self.codes(approved()))
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 30)
        self.assertIn("image-extension-mismatch", self.codes(approved()))
        path.write_bytes(make_jpeg() + b"\x00" * al.IMAGE_MAX_BYTES)
        self.assertIn("image-too-large", self.codes(approved()))
        path.write_bytes(b"")
        self.assertIn("empty-image", self.codes(approved()))
        snap = approved()
        snap["image"]["file"] = "arlington/images/sponsored/coffee-culture.jpg"
        path.write_bytes(make_jpeg())
        self.assertIn("image-path", self.codes(snap))

    def test_narrow_image_is_a_warning(self):
        (self.root / IMG_REL).write_bytes(make_jpeg(800, 400))
        errors, warnings = al.validate_snapshot(approved(), self.root)
        self.assertEqual(errors, [])
        self.assertIn("image-narrow", {w["code"] for w in warnings})

    def test_duplicate_slug_is_refused(self):
        (self.root / al.PAGE_DIR / f"{SLUG}.html").write_text("existing page", encoding="utf-8")
        self.assertIn("duplicate-slug", self.codes(approved()))

    def test_sample_missing_source_links_is_a_warning_not_an_error(self):
        errors, warnings = al.validate_snapshot(approved(), self.root)
        self.assertEqual(errors, [])
        self.assertIn("missing-source-links", {w["code"] for w in warnings})


class ImportSuccessTests(SiteCase):
    def setUp(self):
        super().setUp()
        self.result = self.run_import(approved())
        self.text = self.page_text()

    def test_page_basics(self):
        lm = FIXTURE["letterman"]
        self.assertIn(f"<title>{lm['title']} | Arlington Pulse</title>", self.text)
        self.assertEqual(self.text.count('<h1 class="article-headline">'), 1)
        self.assertIn(f'<h1 class="article-headline">{lm["title"]}</h1>', self.text)
        self.assertIn('<div class="article-date">October 12, 2026</div>', self.text)
        self.assertIn(f'<p class="article-subheadline">{al.subtitle_of(FIXTURE)}</p>', self.text)
        self.assertIn(f'<meta name="description" content="{lm["description"]}">', self.text)

    def test_page_matches_live_layout(self):
        live = (REPO / "arlington/articles/arlington-coffee-renaissance-5-local-cafes-september-2026.html").read_text(encoding="utf-8")
        css = lambda t: re.search(r"<style>.*?</style>", t, re.S).group(0)  # noqa: E731
        self.assertEqual(css(self.text), css(live))
        for marker in ('class="top-header"', 'class="article-container"', 'class="main-footer"', 'class="cta-box"'):
            self.assertIn(marker, self.text)

    def test_approved_text_is_preserved_and_spacers_removed(self):
        m = imp.ARTICLE_REGION_RE.search(self.text)
        self.assertEqual(al.paragraph_texts(m.group(1)), al.paragraph_texts(al.body_html_of(FIXTURE)))
        self.assertNotIn("&nbsp;", m.group(1))

    def test_image_is_local_present_and_in_og(self):
        self.assertIn(f'src="/{IMG_REL}"', self.text)
        self.assertIn('width="1200" height="630"', self.text)
        self.assertIn("alt=\"Lanterns at a sample festival (test alt text)\"", self.text)
        self.assertTrue((self.root / IMG_REL).is_file())
        self.assertIn(f'property="og:image" content="https://www.dfwasocialbuzz.com/{IMG_REL}"', self.text)

    def test_exactly_one_canonical_and_og_set_on_canonical_host(self):
        self.assertEqual(seo_lib.count_tags(self.text), {"canonical": 1, "og_title": 1})
        url = f"https://www.dfwasocialbuzz.com/arlington/articles/{SLUG}.html"
        self.assertIn(f'<link rel="canonical" href="{url}">', self.text)
        self.assertIn(f'property="og:url" content="{url}"', self.text)
        for prop in ("og:type", "og:site_name", "og:description", "article:published_time"):
            self.assertEqual(self.text.count(f'property="{prop}"'), 1, prop)
        self.assertFalse(seo_lib.has_noindex(self.text))

    def test_no_forbidden_hosts_or_apex_links_on_page(self):
        self.assertNotIn("arlington.dfwasocialbuzz.com", self.text)
        self.assertNotIn("https://dfwasocialbuzz.com", self.text)
        self.assertNotIn("m.letterman.ai", self.text)

    def test_page_uses_crlf_like_existing_articles(self):
        raw = (self.root / al.PAGE_DIR / f"{SLUG}.html").read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))

    def test_hub_gets_exactly_one_card_at_the_top_and_nothing_else(self):
        old = self.hub_bytes.decode("utf-8").replace("\r\n", "\n").split("\n")
        new = self.hub_now().decode("utf-8").replace("\r\n", "\n").split("\n")
        self.assertEqual(len(new) - len(old), 7)
        anchor = old.index('        <div class="archive-grid">')
        self.assertEqual(new[:anchor + 1], old[:anchor + 1])
        self.assertEqual(new[anchor + 8:], old[anchor + 1:])
        card = "\n".join(new[anchor + 1:anchor + 8])
        self.assertIn('data-quadrant="central"', card)
        self.assertIn('<span class="quadrant-badge central">CENTRAL</span>', card)
        self.assertIn(f'<a href="/arlington/articles/{SLUG}.html">Read Issue', card)
        self.assertIn(al.excerpt_of(FIXTURE), card)

    def test_hub_line_endings_preserved(self):
        raw = self.hub_now()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        self.assertEqual(self.hub_bytes.count(b"\n"), self.hub_bytes.count(b"\r\n"))

    def test_hub_card_target_exists_and_links_resolve(self):
        errors, _ = link_gate.check_links('<a href="/arlington/articles/%s.html">x</a>' % SLUG, "arlington/index.html", self.root)
        self.assertEqual(errors, [])

    def test_sitemap_includes_new_page_and_robots_is_unchanged(self):
        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"<loc>https://www.dfwasocialbuzz.com/arlington/articles/{SLUG}.html</loc>", sitemap)
        self.assertEqual((self.root / "robots.txt").read_text(encoding="utf-8"), seo_lib.build_robots(CFG))

    def test_second_import_is_refused_and_changes_nothing(self):
        before = self.hub_now()
        with self.assertRaises(al.ImportRefused) as ctx:
            self.run_import(approved())
        self.assertIn("duplicate-slug", {e["code"] for e in ctx.exception.errors})
        self.assertEqual(self.hub_now(), before)

    def test_verify_all_passes_after_a_good_import(self):
        self.assertEqual(imp.verify_all(self.root), [])


class NoindexTests(SiteCase):
    def test_noindex_article_gets_noindex_no_hub_card_and_no_sitemap_entry(self):
        snap = approved()
        snap["letterman"]["no_index"] = True
        result = self.run_import(snap)
        text = self.page_text()
        self.assertTrue(result["noindex"])
        self.assertTrue(seo_lib.has_noindex(text))
        self.assertEqual(seo_lib.count_tags(text), {"canonical": 0, "og_title": 0})
        self.assertEqual(self.hub_now(), self.hub_bytes)
        self.assertNotIn(SLUG, (self.root / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertEqual(imp.verify_all(self.root), [])


class VerifyAllTests(SiteCase):
    def test_draft_snapshot_with_a_page_fails_verification(self):
        self.write_snap(copy.deepcopy(FIXTURE))
        (self.root / al.PAGE_DIR / f"{SLUG}.html").write_text("<html><body>published page</body></html>", encoding="utf-8")
        codes = {e["code"] for _, e in imp.verify_all(self.root)}
        self.assertIn("draft-not-approved", codes)

    def test_a_committed_snapshot_of_a_draft_is_rejected_even_without_a_page(self):
        """The repo is public on GitHub, so a draft snapshot must never be committed."""
        self.write_snap(copy.deepcopy(FIXTURE))
        codes = {e["code"] for _, e in imp.verify_all(self.root)}
        self.assertIn("draft-snapshot-committed", codes)

    def test_a_draft_snapshot_with_an_approval_override_is_still_rejected_when_committed(self):
        snap = approved()
        snap["letterman"]["state"] = "DRAFT"
        snap["approval"]["allow_draft_state"] = True
        self.write_snap(snap)
        self.assertIn("draft-snapshot-committed", {e["code"] for _, e in imp.verify_all(self.root)})

    def test_a_published_snapshot_without_a_page_is_fine(self):
        self.write_snap(approved())
        self.assertEqual(imp.verify_all(self.root), [])

    def test_text_drift_is_detected(self):
        self.run_import(approved())
        page = self.root / al.PAGE_DIR / f"{SLUG}.html"
        page.write_text(page.read_text(encoding="utf-8").replace("free to attend", "FREE to attend!"), encoding="utf-8")
        self.assertIn("text-drift", {e["code"] for _, e in imp.verify_all(self.root)})

    def test_missing_seo_tags_are_detected(self):
        self.run_import(approved())
        page = self.root / al.PAGE_DIR / f"{SLUG}.html"
        page.write_text(re.sub(r'\s*<link rel="canonical"[^>]*>', "", page.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertIn("seo-tags", {e["code"] for _, e in imp.verify_all(self.root)})

    def test_snapshot_name_must_match_slug(self):
        snap = approved()
        (self.root / "content/letterman/other-name.json").write_text(json.dumps(snap), encoding="utf-8")
        self.assertIn("snapshot-name-mismatch", {e["code"] for _, e in imp.verify_all(self.root)})


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (REPO / al.TEMPLATE_PATH).read_text(encoding="utf-8")

    def test_template_placeholders_are_exactly_the_expected_set(self):
        self.assertEqual(set(re.findall(r"\{\{[A-Z_]+\}\}", self.template)),
                         {"{{TITLE}}", "{{DESCRIPTION}}", "{{ROBOTS_META}}", "{{SEO_TAGS}}", "{{DATE_DISPLAY}}",
                          "{{SUBTITLE}}", "{{IMAGE_BLOCK}}", "{{BODY}}"})

    def test_template_links_resolve_in_the_real_repo_and_use_no_forbidden_hosts(self):
        errors, _ = link_gate.check_links(self.template, "arlington/articles/new.html", REPO)
        self.assertEqual(errors, [])
        self.assertNotIn("arlington.dfwasocialbuzz.com", self.template)
        self.assertNotIn("https://dfwasocialbuzz.com", self.template)

    def test_real_repo_has_no_unapproved_snapshot_pages(self):
        self.assertEqual(imp.verify_all(REPO), [])


class CliTests(SiteCase):
    def test_cli_refuses_the_sample_fixture_with_actionable_messages(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = imp.main([str(REPO / "tests/fixtures/sample_festival/snapshot.json"), "--root", str(self.root)])
        out = buf.getvalue()
        self.assertEqual(rc, 1)
        self.assertIn("IMPORT REFUSED. Nothing was written.", out)
        self.assertIn("[draft-not-approved]", out)
        self.assertFalse((self.root / al.PAGE_DIR / f"{SLUG}.html").exists())

    def test_cli_dry_run_writes_nothing(self):
        import io
        from contextlib import redirect_stdout
        path = self.write_snap(approved())
        with redirect_stdout(io.StringIO()):
            rc = imp.main([str(path), "--root", str(self.root), "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.root / al.PAGE_DIR / f"{SLUG}.html").exists())
        self.assertEqual(self.hub_now(), self.hub_bytes)


if __name__ == "__main__":
    unittest.main()
