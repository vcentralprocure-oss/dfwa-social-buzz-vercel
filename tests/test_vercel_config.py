"""Checks that vercel.json stays valid and keeps every existing route on main.

The expected redirects and rewrites below are the ones on origin/main as of this
branch. Adding a route is allowed; removing or changing one fails this test.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

EXISTING_REDIRECTS = {
    ("/privacy", "/privacy-policy/", True),
    ("/terms", "/terms-and-conditions/", True),
}
EXISTING_REWRITE_SOURCES = {
    "/api/quizforma-webhook",
    "/api/quizforma-test",
    "/arlington/articles/:slug",
    "/dallas/articles/:slug",
    "/fortworth/articles/:slug",
    "/arlington/:path*",
    "/dallas/:path*",
    "/fortworth/:path*",
    "/privacy-policy",
    "/privacy-policy/",
    "/terms-and-conditions",
    "/terms-and-conditions/",
    "/articles/:path*",
}


CANONICAL_HOST = "https://www.dfwasocialbuzz.com"


def source_to_regex(source):
    """Approximate Vercel source matching: ':name' = one path segment, ':name*' = rest."""
    out = []
    for part in re.split(r"(:\w+\*?)", source):
        if re.fullmatch(r":\w+\*", part):
            out.append(".*")
        elif re.fullmatch(r":\w+", part):
            out.append("[^/]+")
        else:
            out.append(re.escape(part))
    return re.compile("^" + "".join(out) + "$")


class VercelConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((REPO / "vercel.json").read_text(encoding="utf-8"))

    def a_redirects(self):
        return [r for r in self.cfg.get("redirects", []) if r["source"].startswith("/a/")]

    def test_no_catch_all_redirect_under_a(self):
        """A pattern like /a/:slug would send unknown slugs to nonexistent pages."""
        for r in self.a_redirects():
            self.assertNotRegex(r["source"], r"[:*(]",
                                f"catch-all /a/ redirect is not allowed: {r['source']}")

    def test_unknown_a_slug_is_not_redirected(self):
        probe = "/a/this-slug-does-not-exist-xyz"
        for r in self.cfg.get("redirects", []):
            self.assertIsNone(source_to_regex(r["source"]).match(probe),
                              f"redirect {r['source']} would catch unknown /a/ slugs")

    def test_any_explicit_a_redirect_targets_an_existing_page_on_canonical_host(self):
        """Vacuous today (no /a/ redirects). Guards future explicit pairs."""
        for r in self.a_redirects():
            dest = r["destination"]
            self.assertTrue(dest.startswith(CANONICAL_HOST + "/arlington/articles/"),
                            f"destination must be absolute on the canonical host: {dest}")
            rel = dest[len(CANONICAL_HOST) + 1:]
            self.assertTrue((REPO / rel).is_file(), f"destination page does not exist: {rel}")

    def test_existing_redirects_preserved(self):
        got = {(r["source"], r["destination"], r.get("permanent", False)) for r in self.cfg.get("redirects", [])}
        self.assertTrue(EXISTING_REDIRECTS <= got, f"missing: {EXISTING_REDIRECTS - got}")

    def test_existing_rewrites_preserved(self):
        got = {r["source"] for r in self.cfg.get("rewrites", [])}
        self.assertTrue(EXISTING_REWRITE_SOURCES <= got, f"missing: {EXISTING_REWRITE_SOURCES - got}")

    def test_existing_crons_and_functions_preserved(self):
        self.assertEqual(self.cfg["crons"][0]["path"], "/api/update-articles")
        self.assertEqual(self.cfg["functions"]["api/*.js"]["maxDuration"], 30)


class SourceMatcherTests(unittest.TestCase):
    """The route matcher used above must itself be correct, or the tests pass vacuously."""

    def test_named_segment_matches_one_segment_only(self):
        rx = source_to_regex("/a/:slug")
        self.assertTrue(rx.match("/a/some-slug"))
        self.assertFalse(rx.match("/a/some/slug"))
        self.assertFalse(rx.match("/a/"))

    def test_wildcard_segment_matches_rest(self):
        rx = source_to_regex("/arlington/:path*")
        self.assertTrue(rx.match("/arlington/articles/x.html"))

    def test_literal_source_matches_exactly(self):
        rx = source_to_regex("/privacy")
        self.assertTrue(rx.match("/privacy"))
        self.assertFalse(rx.match("/privacy-policy"))


if __name__ == "__main__":
    unittest.main()
