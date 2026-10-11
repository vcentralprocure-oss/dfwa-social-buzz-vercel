"""Unit tests for scripts/seo_lib.py, scripts/generate_seo.py and scripts/validate_site.py.

Each test builds a small temporary site so results do not depend on the real repo.
Run with:  python -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import generate_seo  # noqa: E402
import seo_lib  # noqa: E402
import validate_site  # noqa: E402

CFG = {
    "canonical_host": "https://www.dfwasocialbuzz.com",
    "include_globs": [
        "index.html",
        "arlington/index.html",
        "arlington/articles/*.html",
    ],
    "exclude_globs": ["**/*.bak*", "**/*test*", "**/sample-template.html", "templates/**"],
}

PAGE_OK = """<!DOCTYPE html><html><head><title>T</title>
<meta name="description" content="d"></head><body><a href="/arlington/">hub</a></body></html>
"""


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class SiteFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(self.root, "index.html", PAGE_OK)
        write(self.root, "arlington/index.html", PAGE_OK)
        write(self.root, "arlington/articles/good.html", PAGE_OK)

    def tearDown(self):
        self._tmp.cleanup()


class PathAndUrlTests(unittest.TestCase):
    def test_page_paths(self):
        self.assertEqual(seo_lib.page_path("index.html"), "/")
        self.assertEqual(seo_lib.page_path("arlington/index.html"), "/arlington/")
        self.assertEqual(seo_lib.page_path("arlington/articles/a.html"), "/arlington/articles/a.html")

    def test_canonical_uses_www_host(self):
        cfg = seo_lib.load_config()
        self.assertEqual(cfg["canonical_host"], "https://www.dfwasocialbuzz.com")
        self.assertTrue(seo_lib.canonical_url(cfg, "arlington/articles/a.html").startswith("https://www.dfwasocialbuzz.com/"))

    def test_real_config_has_no_apex_or_subdomain_canonical(self):
        cfg = seo_lib.load_config()
        self.assertNotIn("arlington.dfwasocialbuzz.com", cfg["canonical_host"])
        self.assertNotEqual(cfg["canonical_host"], "https://dfwasocialbuzz.com")


class DiscoveryTests(SiteFixture):
    def test_include_and_exclude(self):
        write(self.root, "arlington/articles/x.html.bak", PAGE_OK)
        write(self.root, "arlington/articles/arlington-test-article.html", PAGE_OK)
        write(self.root, "arlington/articles/sample-template.html", PAGE_OK)
        rels = seo_lib.discover_pages(self.root, CFG)
        self.assertEqual(rels, ["arlington/articles/good.html", "arlington/index.html", "index.html"])

    def test_noindex_pages_are_excluded(self):
        write(self.root, "arlington/articles/private.html",
              '<html><head><meta name="robots" content="noindex, nofollow"></head></html>')
        rels = seo_lib.discover_pages(self.root, CFG)
        self.assertNotIn("arlington/articles/private.html", rels)

    def test_noindex_in_any_attribute_order(self):
        write(self.root, "arlington/articles/private2.html",
              '<html><head><meta content="noindex" name="robots"></head></html>')
        self.assertNotIn("arlington/articles/private2.html", seo_lib.discover_pages(self.root, CFG))


class SitemapAndRobotsTests(SiteFixture):
    def test_sitemap_lists_exactly_eligible_pages(self):
        write(self.root, "arlington/articles/hidden.html",
              '<html><head><meta name="robots" content="noindex"></head></html>')
        rels = seo_lib.discover_pages(self.root, CFG)
        xml_text = seo_lib.build_sitemap(CFG, rels)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [e.text for e in ET.fromstring(xml_text).findall("s:url/s:loc", ns)]
        self.assertEqual(len(locs), len(set(locs)))
        self.assertEqual(sorted(locs), sorted(seo_lib.canonical_url(CFG, r) for r in rels))
        self.assertFalse(any("hidden" in loc for loc in locs))

    def test_robots_has_one_sitemap_line_and_no_disallow(self):
        text = seo_lib.build_robots(CFG)
        self.assertEqual(text.count("Sitemap:"), 1)
        self.assertIn("Sitemap: https://www.dfwasocialbuzz.com/sitemap.xml", text)
        self.assertNotIn("Disallow", text)


class OpenGraphTagTests(unittest.TestCase):
    def setUp(self):
        self.meta = {
            "rel": "arlington/articles/new.html",
            "title": 'Sample "quoted" & title',
            "description": "Desc <b>x</b>",
            "image": "arlington/images/articles/new.jpg",
            "published": "2026-10-11",
        }

    def test_exactly_one_canonical_and_one_of_each_og(self):
        tags = seo_lib.render_seo_tags(CFG, self.meta)
        self.assertEqual(tags.count('rel="canonical"'), 1)
        for prop in ["og:type", "og:site_name", "og:title", "og:description", "og:url", "og:image", "article:published_time"]:
            self.assertEqual(tags.count(f'property="{prop}"'), 1, prop)

    def test_canonical_and_og_url_match(self):
        tags = seo_lib.render_seo_tags(CFG, self.meta)
        expected = "https://www.dfwasocialbuzz.com/arlington/articles/new.html"
        self.assertIn(f'<link rel="canonical" href="{expected}">', tags)
        self.assertIn(f'property="og:url" content="{expected}"', tags)

    def test_values_are_escaped(self):
        tags = seo_lib.render_seo_tags(CFG, self.meta)
        self.assertIn("&quot;quoted&quot;", tags)
        self.assertNotIn("<b>", tags)

    def test_image_is_absolute_on_canonical_host(self):
        tags = seo_lib.render_seo_tags(CFG, self.meta)
        self.assertIn('property="og:image" content="https://www.dfwasocialbuzz.com/arlington/images/articles/new.jpg"', tags)

    def test_optional_fields_omitted_when_absent(self):
        meta = {"rel": "arlington/articles/new.html", "title": "t", "description": "d"}
        tags = seo_lib.render_seo_tags(CFG, meta)
        self.assertNotIn("og:image", tags)
        self.assertNotIn("article:published_time", tags)


class TagNewPageTests(SiteFixture):
    def meta(self):
        return {"title": "New", "description": "New desc"}

    def test_tags_a_new_untracked_page(self):
        write(self.root, "arlington/articles/brand-new.html", PAGE_OK)
        generate_seo.tag_new_page(self.root, CFG, "arlington/articles/brand-new.html", self.meta(), tracked=set())
        text = (self.root / "arlington/articles/brand-new.html").read_text(encoding="utf-8")
        self.assertEqual(text.count('rel="canonical"'), 1)
        self.assertLess(text.index('rel="canonical"'), text.index("</head>"))

    def test_refuses_tracked_existing_page(self):
        with self.assertRaises(SystemExit):
            generate_seo.tag_new_page(self.root, CFG, "arlington/articles/good.html", self.meta(),
                                      tracked={"arlington/articles/good.html"})
        self.assertNotIn("canonical", (self.root / "arlington/articles/good.html").read_text(encoding="utf-8"))

    def test_refuses_page_that_already_has_canonical(self):
        write(self.root, "arlington/articles/dup.html",
              PAGE_OK.replace("</head>", '<link rel="canonical" href="https://x/">\n</head>'))
        with self.assertRaises(SystemExit):
            generate_seo.tag_new_page(self.root, CFG, "arlington/articles/dup.html", self.meta(), tracked=set())


class ValidatorTests(SiteFixture):
    def make_sitemap(self):
        rels = seo_lib.discover_pages(self.root, CFG)
        write(self.root, "sitemap.xml", seo_lib.build_sitemap(CFG, rels))

    def run_validate(self):
        return validate_site.validate(root=self.root, cfg=CFG)

    def test_clean_site_has_no_errors(self):
        self.make_sitemap()
        result = self.run_validate()
        self.assertEqual(result["errors"], [])

    def test_detects_broken_internal_link(self):
        self.make_sitemap()
        write(self.root, "arlington/articles/broken.html",
              PAGE_OK.replace("hub", '<a href="/arlington/articles/nope.html">x</a>'))
        self.make_sitemap()
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("broken-internal-link", types)

    def test_detects_missing_image(self):
        write(self.root, "arlington/articles/img.html",
              PAGE_OK.replace("hub", '<img src="/arlington/images/none.jpg">'))
        self.make_sitemap()
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("missing-image", types)

    def test_detects_bad_image_format(self):
        write(self.root, "arlington/images/x.txt", "not an image")
        write(self.root, "arlington/articles/bad-img.html",
              PAGE_OK.replace("hub", '<img src="/arlington/images/x.txt">'))
        self.make_sitemap()
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("image-bad-format", types)

    def test_detects_duplicate_canonical_tags_on_one_page(self):
        tag = '<link rel="canonical" href="https://www.dfwasocialbuzz.com/arlington/articles/good.html">'
        write(self.root, "arlington/articles/good.html", PAGE_OK.replace("</head>", tag + tag + "</head>"))
        self.make_sitemap()
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("duplicate-canonical-tag", types)

    def test_detects_duplicate_canonical_url_across_pages(self):
        tag = '<link rel="canonical" href="https://www.dfwasocialbuzz.com/arlington/articles/good.html">'
        write(self.root, "arlington/articles/good.html", PAGE_OK.replace("</head>", tag + "</head>"))
        write(self.root, "arlington/articles/copy.html", PAGE_OK.replace("</head>", tag + "</head>"))
        self.make_sitemap()
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("duplicate-canonical-url", types)

    def test_detects_eligible_page_missing_from_sitemap(self):
        self.make_sitemap()
        write(self.root, "arlington/articles/late.html", PAGE_OK)
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("eligible-page-missing-from-sitemap", types)

    def test_detects_sitemap_url_for_excluded_page(self):
        write(self.root, "arlington/articles/gone.html", PAGE_OK)
        self.make_sitemap()
        write(self.root, "arlington/articles/gone.html",
              '<html><head><meta name="robots" content="noindex"></head></html>')
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("sitemap-url-not-eligible", types)

    def test_detects_missing_sitemap(self):
        types = {e["type"] for e in self.run_validate()["errors"]}
        self.assertIn("missing-sitemap", types)

    def test_external_links_are_not_checked(self):
        self.make_sitemap()
        write(self.root, "arlington/articles/ext.html",
              PAGE_OK.replace("hub", '<a href="https://example.com/x">x</a><img src="https://example.com/a.jpg">'))
        self.make_sitemap()
        self.assertEqual(self.run_validate()["errors"], [])

    def test_ratchet_only_blocks_new_errors(self):
        self.make_sitemap()
        write(self.root, "arlington/articles/old.html", PAGE_OK.replace("hub", '<a href="/nope/">x</a>'))
        self.make_sitemap()
        result = self.run_validate()
        known = {validate_site.finding_key(e) for e in result["errors"]}
        self.assertTrue(known)
        self.assertEqual([e for e in result["errors"] if validate_site.finding_key(e) not in known], [])


class StaleOutputTests(SiteFixture):
    def test_check_mode_detects_stale_sitemap(self):
        write(self.root, "sitemap.xml", "<stale/>")
        write(self.root, "robots.txt", seo_lib.build_robots(CFG))
        self.assertEqual(generate_seo.check_outputs(self.root, CFG), 1)

    def test_check_mode_passes_when_current(self):
        generate_seo.write_outputs(self.root, CFG)
        self.assertEqual(generate_seo.check_outputs(self.root, CFG), 0)


if __name__ == "__main__":
    unittest.main()
