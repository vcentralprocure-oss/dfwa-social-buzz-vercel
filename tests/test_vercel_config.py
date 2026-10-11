"""Checks that vercel.json stays valid and keeps every existing route on main.

The expected redirects and rewrites below are the ones on origin/main as of this
branch. Adding a route is allowed; removing or changing one fails this test.
"""

import json
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


class VercelConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((REPO / "vercel.json").read_text(encoding="utf-8"))

    def test_existing_redirects_preserved(self):
        got = {(r["source"], r["destination"], r.get("permanent", False)) for r in self.cfg.get("redirects", [])}
        self.assertTrue(EXISTING_REDIRECTS <= got, f"missing: {EXISTING_REDIRECTS - got}")

    def test_existing_rewrites_preserved(self):
        got = {r["source"] for r in self.cfg.get("rewrites", [])}
        self.assertTrue(EXISTING_REWRITE_SOURCES <= got, f"missing: {EXISTING_REWRITE_SOURCES - got}")

    def test_existing_crons_and_functions_preserved(self):
        self.assertEqual(self.cfg["crons"][0]["path"], "/api/update-articles")
        self.assertEqual(self.cfg["functions"]["api/*.js"]["maxDuration"], 30)


if __name__ == "__main__":
    unittest.main()
