"""Tests for scripts/link_gate.py and scripts/audit_backlinks.py (no network is used)."""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import article_lib  # noqa: E402
import audit_backlinks  # noqa: E402
import link_gate  # noqa: E402
import seo_lib  # noqa: E402


def codes(items):
    return {i["code"] for i in items}


class LinkGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "arlington" / "articles").mkdir(parents=True)
        (self.root / "arlington" / "index.html").write_text("hub", encoding="utf-8")
        (self.root / "arlington" / "articles" / "exists.html").write_text("x", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def gate(self, html):
        return link_gate.check_links(html, "arlington/articles/new.html", self.root)

    def test_valid_internal_links_pass(self):
        errors, _ = self.gate('<a href="/arlington/">hub</a><a href="/arlington/articles/exists.html">a</a><a href="exists.html">b</a>')
        self.assertEqual(errors, [])

    def test_broken_internal_link_blocks(self):
        errors, _ = self.gate('<a href="/arlington/articles/nope.html">x</a>')
        self.assertIn("broken-internal-link", codes(errors))

    def test_https_external_link_passes(self):
        errors, warnings = self.gate('<a href="https://example.com/page" target="_blank" rel="noopener noreferrer">Example site</a>')
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_http_external_is_a_warning_not_an_error(self):
        errors, warnings = self.gate('<a href="http://example.com/">Example</a>')
        self.assertEqual(errors, [])
        self.assertIn("insecure-http", codes(warnings))

    def test_unsafe_schemes_block(self):
        for href in ("javascript:alert(1)", "data:text/html,x", "vbscript:x", "file:///etc/passwd"):
            errors, _ = self.gate(f'<a href="{href}">x</a>')
            self.assertIn("unsafe-scheme", codes(errors), href)

    def test_arlington_subdomain_blocks(self):
        errors, _ = self.gate('<a href="https://arlington.dfwasocialbuzz.com/business">x</a>')
        self.assertIn("forbidden-host", codes(errors))

    def test_letterman_article_urls_block(self):
        for href in ("https://m.letterman.ai/a/some-slug", "https://dfwasocialbuzz.com/a/some-slug",
                     "https://www.dfwasocialbuzz.com/a/some-slug"):
            errors, _ = self.gate(f'<a href="{href}">x</a>')
            self.assertIn("letterman-article-url", codes(errors), href)

    def test_www_absolute_self_link_blocks_apex_is_allowed(self):
        errors, _ = self.gate('<a href="https://www.dfwasocialbuzz.com/arlington/">x</a>')
        self.assertIn("www-self-link", codes(errors))
        errors, _ = self.gate('<a href="https://dfwasocialbuzz.com/arlington/">x</a>')
        self.assertEqual(errors, [])

    def test_apex_absolute_link_to_missing_page_blocks(self):
        errors, _ = self.gate('<a href="https://dfwasocialbuzz.com/arlington/articles/missing.html">x</a>')
        self.assertIn("broken-internal-link", codes(errors))

    def test_malformed_urls_block(self):
        self.assertIn("malformed-url", codes(self.gate('<a href="https://nohost">x</a>')[0]))
        self.assertIn("malformed-url", codes(self.gate('<a href="https://exa mple.com">x</a>')[0]))
        self.assertIn("empty-href", codes(self.gate('<a href="">x</a>')[0]))

    def test_target_blank_requires_noopener(self):
        errors, _ = self.gate('<a href="https://example.com/" target="_blank">Example</a>')
        self.assertIn("target-blank-no-rel", codes(errors))

    def test_warnings_for_tracking_duplicates_and_generic_text(self):
        html = ('<a href="https://example.com/?utm_source=x">Example</a>'
                '<a href="https://example.com/?utm_source=x">click here</a>')
        errors, warnings = self.gate(html)
        self.assertEqual(errors, [])
        self.assertTrue({"tracking-params", "duplicate-external-link", "generic-link-text"} <= codes(warnings))

    def test_mailto_and_fragment_links_are_fine(self):
        errors, _ = self.gate('<a href="mailto:a@b.com">m</a><a href="#top">t</a>')
        self.assertEqual(errors, [])

    def test_reachability_is_warnings_only_and_uses_injected_opener(self):
        statuses = {"https://ok.example/": 200, "https://gone.example/": 404, "https://down.example/": 0}
        warnings = link_gate.check_reachable(list(statuses), opener=lambda url, timeout: statuses[url])
        self.assertEqual({w["ref"] for w in warnings}, {"https://gone.example/", "https://down.example/"})
        self.assertEqual(codes(warnings), {"unreachable-external-link"})


class CleanBodyTests(unittest.TestCase):
    def test_external_links_open_safely_internal_links_unchanged(self):
        out = article_lib.clean_body('<p><a href="https://example.com/x">Ext</a> and <a href="/arlington/">Hub</a></p><p>&nbsp;</p>')
        self.assertEqual(len(out), 1)
        self.assertIn('href="https://example.com/x" target="_blank" rel="noopener noreferrer"', out[0])
        self.assertIn('<a href="/arlington/">Hub</a>', out[0])

    def test_clean_body_output_passes_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arlington").mkdir()
            (root / "arlington" / "index.html").write_text("x", encoding="utf-8")
            out = "".join(article_lib.clean_body('<p><a href="https://example.com/x">Example</a> <a href="/arlington/">Hub</a></p>'))
            errors, _ = link_gate.check_links(out, "arlington/articles/new.html", root)
            self.assertEqual(errors, [])


class BacklinkAuditTests(unittest.TestCase):
    def test_inventory_groups_external_links_by_domain_and_ignores_own_hosts(self):
        cfg = seo_lib.load_config()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "arlington" / "articles").mkdir(parents=True)
            (root / "arlington" / "articles" / "a.html").write_text(
                '<a href="https://biz.example/x">1</a><a href="https://biz.example/y">2</a>'
                '<a href="https://dfwasocialbuzz.com/arlington/">own</a><a href="/arlington/">rel</a>', encoding="utf-8")
            (root / "arlington" / "articles" / "b.html").write_text('<a href="https://other.example/">3</a>', encoding="utf-8")
            inv = audit_backlinks.inventory(root, cfg)
            self.assertEqual(set(inv), {"biz.example", "other.example"})
            self.assertEqual(inv["biz.example"]["links"], 2)
            self.assertEqual(inv["biz.example"]["pages"], ["arlington/articles/a.html"])

    def test_audit_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(audit_backlinks.main(["--root", tmp]), 0)


if __name__ == "__main__":
    unittest.main()
