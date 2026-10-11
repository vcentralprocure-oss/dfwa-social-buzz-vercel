"""Regression tests for the deployment-exposure safeguards.

Background: this project serves the repository root as static files, so any tracked file
is publicly reachable unless /.vercelignore excludes it from the deployment. These tests
keep Letterman snapshots, approval records, fixtures, tooling and internal docs private,
without touching any file that is public today. The live check against a real preview is
scripts/check_deployment_exposure.py (network); these tests need no network.
"""

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import check_deployment_exposure as ex  # noqa: E402
import import_letterman_article as imp  # noqa: E402

TRACKED = ex.tracked_files(REPO)
RULES = ex.load_rules(REPO)

# Paths that must stay public: they are public on production today or are needed by it.
MUST_STAY_PUBLIC_PREFIXES = (
    "api/", "data/", "arlington/", "dallas/", "fort-worth/", "fortworth/", "business/", "contact/",
    "deals/", "privacy-policy/", "terms-and-conditions/", "public/", "backups/", "lib/",
)
MUST_STAY_PUBLIC_FILES = {
    "index.html", "vercel.json", "package.json", "logo.jpg", "robots.txt", "sitemap.xml",
    "templates/article-template.html", "docs/arlington-quadrant-policy.md",
    "CLAUDE.md", "TRANSITION_CONTROL_LOG.md", ".gitignore",
}
INTERNAL_PREFIXES = (".github/", "scripts/", "tests/", "content/")
INTERNAL_FILES = {"templates/arlington-article-page.html", ".vercelignore", ".gitattributes"}


class MatcherTests(unittest.TestCase):
    def ignored(self, text, path):
        return ex.is_ignored(path, ex.parse_rules(text))

    def test_directory_rule_excludes_everything_below_it(self):
        self.assertTrue(self.ignored("/content/\n", "content/letterman/a.json"))
        self.assertTrue(self.ignored("/content/\n", "content/deep/er/x.md"))
        self.assertFalse(self.ignored("/content/\n", "contentx/a.json"))
        self.assertFalse(self.ignored("/content/\n", "arlington/content/a.json"))

    def test_exact_file_rule(self):
        self.assertTrue(self.ignored("/templates/a.html\n", "templates/a.html"))
        self.assertFalse(self.ignored("/templates/a.html\n", "templates/b.html"))

    def test_glob_and_negation(self):
        rules = "/docs/*\n!/docs/keep.md\n"
        self.assertTrue(self.ignored(rules, "docs/other.md"))
        self.assertFalse(self.ignored(rules, "docs/keep.md"))
        self.assertTrue(self.ignored(rules, "docs/sub/nested.md"))

    def test_last_matching_rule_wins(self):
        self.assertFalse(self.ignored("/x.txt\n!/x.txt\n", "x.txt"))
        self.assertTrue(self.ignored("!/x.txt\n/x.txt\n", "x.txt"))

    def test_a_file_inside_an_excluded_directory_cannot_be_reincluded(self):
        self.assertTrue(self.ignored("/a/\n!/a/x.txt\n", "a/x.txt"))

    def test_comments_and_blank_lines_are_ignored(self):
        self.assertTrue(self.ignored("# comment\n\n/x/\n", "x/y"))


class RealRulesTests(unittest.TestCase):
    def test_every_tracked_internal_path_is_excluded(self):
        missed = [p for p in TRACKED
                  if (p.startswith(INTERNAL_PREFIXES) or p in INTERNAL_FILES) and not ex.is_ignored(p, RULES)]
        self.assertEqual(missed, [], f"internal files would be PUBLIC: {missed}")

    def test_new_internal_docs_are_excluded_but_the_public_policy_is_kept(self):
        for doc in ("docs/seo-routing.md", "docs/publishing-workflow.md", "docs/backlink-audit.md",
                    "docs/deployment-exposure.md", "docs/any-future-doc.md"):
            self.assertTrue(ex.is_ignored(doc, RULES), doc)
        self.assertFalse(ex.is_ignored("docs/arlington-quadrant-policy.md", RULES))

    def test_nothing_that_is_public_today_is_excluded(self):
        wrongly = [p for p in TRACKED
                   if ex.is_ignored(p, RULES)
                   and (p in MUST_STAY_PUBLIC_FILES or p.startswith(MUST_STAY_PUBLIC_PREFIXES))]
        self.assertEqual(wrongly, [], f"existing public files would be removed: {wrongly}")

    def test_excluded_set_is_exactly_the_internal_set(self):
        for p in ex.internal_files(REPO, RULES, TRACKED):
            self.assertTrue(p.startswith(INTERNAL_PREFIXES) or p in INTERNAL_FILES
                            or (p.startswith("docs/") and p != "docs/arlington-quadrant-policy.md"), p)

    def test_future_snapshots_and_approval_records_cannot_become_public(self):
        for future in ("content/letterman/some-new-article.json",
                       "content/letterman/some-new-article.approval.json",
                       "content/letterman/drafts/x.json",
                       "content/drafts/unapproved.md",
                       "content/anything/at/all.txt"):
            self.assertTrue(ex.is_ignored(future, RULES), future)

    def test_future_tooling_and_fixtures_cannot_become_public(self):
        for future in ("scripts/new_tool.py", "tests/fixtures/another/snapshot.json", "tests/test_new.py",
                       ".github/workflows/new.yml"):
            self.assertTrue(ex.is_ignored(future, RULES), future)

    def test_removing_the_content_rule_would_be_caught(self):
        weakened = ex.parse_rules(re.sub(r"(?m)^/content/\n", "", (REPO / ".vercelignore").read_text(encoding="utf-8")))
        self.assertFalse(ex.is_ignored("content/letterman/x.json", weakened))
        missed = [p for p in TRACKED if p.startswith("content/") and not ex.is_ignored(p, weakened)]
        self.assertTrue(missed, "the coverage test would not notice a missing /content/ rule")

    def test_vercelignore_is_lf_only_so_no_pattern_ends_in_a_carriage_return(self):
        """A CRLF file would leave a stray \\r on every pattern and could silently match nothing."""
        self.assertNotIn(b"\r", (REPO / ".vercelignore").read_bytes())
        attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
        self.assertRegex(attrs, r"(?m)^\.vercelignore\s+text\s+eol=lf\s*$")
        import subprocess
        blob = subprocess.run(["git", "cat-file", "-p", ":.vercelignore"], cwd=REPO, capture_output=True)
        self.assertEqual(blob.returncode, 0, "the file must be tracked")
        self.assertNotIn(b"\r", blob.stdout, "the committed blob must be LF-only")
        attr = subprocess.run(["git", "check-attr", "eol", ".vercelignore"], cwd=REPO, capture_output=True, text=True)
        self.assertIn("eol: lf", attr.stdout)

    def test_api_and_data_are_never_excluded(self):
        for p in ("api/subscribe.js", "api/update-articles.js", "data/articles-metadata.json"):
            self.assertFalse(ex.is_ignored(p, RULES), p)


class CanaryAndFixtureTests(unittest.TestCase):
    def test_canary_exists_is_tracked_and_excluded(self):
        self.assertIn(ex.CANARY, TRACKED)
        self.assertTrue(ex.is_ignored(ex.CANARY, RULES))

    def test_canary_is_not_mistaken_for_a_snapshot(self):
        self.assertFalse(ex.CANARY.endswith(".json"))
        self.assertEqual(imp.verify_all(REPO), [])

    # SHA-256 of normalized paragraphs/strings from a real, unpublished draft. Only hashes are stored:
    # the repo is public, so the draft text (and its name) must never appear here in clear text.
    BANNED_FRAGMENT_HASHES = frozenset([
        "02300c94509f79367f11ce6d875125f977ee80d5173036f18e129c5ad0420d05",
        "0cec806848de957b406078f409f10d960e46b6243610c92aa35dee9c41d394e2",
        "17c32b75fafb1fd4cd2b3cc70df4f90540ecf379b2e57c08d3893afe1a7fd575",
        "197978452185b48910e13aa8c25402ee7f7dcc50d155c9d482b16449ad0c0140",
        "1b214c5c0273ce7299c1ae92442484589bd1588f9cc83c01ac2183fccda04aa7",
        "1f5425a4898ff201a4e9f9d3ad4e11b7d70fa34bdc1ef5981919a1286e6b7a84",
        "354068448a97d1778fb77a3f36db4ebac11c2f20e9597a44dc89ed2d08f50b21",
        "37f938e5c10d9a04fdca86f6318dae93aff61e96fd95966d78c74c744dbbbf52",
        "3e2ae50a4cc1f91d7489f98e6e47f2063414c4d80cf50636f1d00ae50168f55c",
        "4db422fc725011fab55306d8cf5d3f8a25c86c26e68404f30b75fdeef7429122",
        "60a9cb9cbcfb723f694847a605dbbee231a64b1abfec5615007a34c228c8d124",
        "68fdf11508229bcc44d818669b740dc814321f367022fe5e953691977bbeeb1a",
        "69c1ae2403b17cd62b855adcd7852bf39e2ff7362341722c9b827140509be6d4",
        "6d9312365ee91b25b92a95cdc0327469b446cf4b6c0fa385683dc99c00e391b1",
        "886bf8cf85774597516efefaefab7591fed0b04ceb480e930f04c534dc143c6e",
        "8b62fe8c4584002c0a34e0fef970dae1094e4c69417e316c14a75c4a17c81039",
        "a0e627d9eec5de4c593e2c702d31010391c90d20b38d59e4af49999cba958b4d",
        "b045cdac8194226d7cb031b47c216a8b3c7c36d42d764607f49681a08885ebf8",
        "b5a355338034917c58261ee308b4a7fd5c981f5ea12ecf259f12dfdab4bc5b48",
        "b762bedc85395996f108a838b1f3c06bac315f46ff08ce0d744061b40fa427b0",
        "b7c2e0a00ea3f96bc77f0c5e64d46cd7474a23d0da6404e4eea91eefc9834daa",
        "ba1c403f7c0a7ba522e90c67a4dd0f7abce80a314b57b338f2ab973490829142",
        "c13898f559bc62359078d103047a665619d5960582c17b8943f163ecabf2f666",
        "c2f8f8e066652662dae50f57bcfe5ebff9bac88ad369af1550495ba82cc8ae45",
        "d1a1748a3abfd3ad26510160b639d920207df2da31d7a666db8159874d19149f",
        "d4e04fcce99d91480dc90eb06d17519e72dc1afa4944062febe4718e1ff4e5dc",
        "fa9b6a5a70e7c318752599513b9022400ce369ea05584a07e05ffff237188da1",
    ])

    @staticmethod
    def fragment_hashes(text):
        """SHA-256 of each normalized paragraph or JSON string of at least 20 characters."""
        import hashlib
        import html
        import json
        try:
            obj = json.loads(text)
        except ValueError:
            obj = None
        strings = []

        def walk(o):
            if isinstance(o, str):
                strings.append(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        if obj is not None:
            walk(obj)
        else:
            strings.append(text)
        out = set()
        for s in strings:
            for part in re.split(r"</p>|\n", s):
                t = re.sub(r"<[^>]+>", " ", part)
                t = " ".join(html.unescape(t).replace("\xa0", " ").split()).lower()
                if len(t) >= 20:
                    out.add(hashlib.sha256(t.encode("utf-8")).hexdigest())
        return out

    def test_fixtures_and_content_contain_no_real_draft_text(self):
        offenders = []
        for p in TRACKED:
            if p.startswith(("tests/", "content/", "docs/", "scripts/")):
                text = (REPO / p).read_text(encoding="utf-8", errors="replace")
                if self.fragment_hashes(text) & self.BANNED_FRAGMENT_HASHES:
                    offenders.append(p)
        self.assertEqual(offenders, [], f"real draft text found in: {offenders}")

    def test_the_fragment_detector_catches_copied_text_despite_case_and_spacing(self):
        sample = "This is an invented sentence that stands in for a real draft paragraph."
        original = self.fragment_hashes("<p>" + sample + "</p><p>&nbsp;</p>")
        self.assertEqual(len(original), 1)
        reformatted = "<p>  THIS is an   invented sentence that stands in for a real draft paragraph. </p>"
        self.assertEqual(self.fragment_hashes(reformatted), original)
        other = self.fragment_hashes("<p>Completely different text here, long enough to count.</p>")
        self.assertFalse(other & original)
        self.assertFalse(self.fragment_hashes("<p>too short</p>"))

    def test_the_fixture_is_clearly_synthetic(self):
        text = (REPO / "tests/fixtures/sample_festival/snapshot.json").read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC TEST FIXTURE", text)
        self.assertIn("example.invalid", text)


class ProbeLogicTests(unittest.TestCase):
    """check_deployment() with a fake fetcher: no network."""

    BASE = "https://preview.example"

    def run_check(self, handler):
        return ex.check_deployment(self.BASE, REPO, fetcher=lambda url: handler(url.replace(self.BASE, "")),
                                   tracked=TRACKED, rules=RULES)

    @staticmethod
    def healthy(path):
        if path in ("/", "") or path in ex.PUBLIC_ROUTES:
            return 200
        if path.startswith("/api/"):
            return 405
        return 404

    def test_healthy_deployment_passes(self):
        result = self.run_check(self.healthy)
        self.assertTrue(ex.report_ok(result), result)
        self.assertGreater(result["internal_checked"], 15)

    def test_any_exposed_internal_file_fails(self):
        def leaky(path):
            return 200 if path == "/content/letterman/EXPOSURE_CANARY.txt" else self.healthy(path)
        result = self.run_check(leaky)
        self.assertFalse(ex.report_ok(result))
        self.assertEqual([p for p, _ in result["exposed"]], ["content/letterman/EXPOSURE_CANARY.txt"])

    def test_a_leaked_snapshot_under_content_is_detected(self):
        tracked = TRACKED + ["content/letterman/new-article.json"]
        result = ex.check_deployment(self.BASE, REPO, tracked=tracked, rules=RULES,
                                     fetcher=lambda u: 200 if u.endswith("new-article.json") else self.healthy(u.replace(self.BASE, "")))
        self.assertIn("content/letterman/new-article.json", [p for p, _ in result["exposed"]])

    def test_a_404_on_a_few_files_does_not_prove_the_rest_are_private(self):
        def partial(path):
            return 200 if path.startswith("/tests/") and path.endswith("test_seo_tools.py") else self.healthy(path)
        result = self.run_check(partial)
        self.assertEqual([p for p, _ in result["exposed"]], ["tests/test_seo_tools.py"])

    def test_unreachable_site_is_not_reported_as_safe(self):
        result = self.run_check(lambda path: 0)
        self.assertFalse(ex.report_ok(result))
        self.assertTrue(result["unverified"])

    def test_redirects_are_not_followed_and_are_not_exposure(self):
        def redirecting(path):
            return 308 if path.startswith("/scripts/") else self.healthy(path)
        self.assertEqual(self.run_check(redirecting)["exposed"], [])

    def test_missing_public_route_or_api_function_is_a_problem(self):
        broken_public = self.run_check(lambda p: 404 if p == "/arlington/" else self.healthy(p))
        self.assertTrue(any("/arlington/" in x for x in broken_public["problems"]))
        broken_api = self.run_check(lambda p: 404 if p == "/api/subscribe" else self.healthy(p))
        self.assertTrue(any("/api/subscribe" in x for x in broken_api["problems"]))

    def test_missing_canary_exclusion_is_a_problem(self):
        no_rules = ex.parse_rules("/scripts/\n")
        result = ex.check_deployment(self.BASE, REPO, tracked=TRACKED, rules=no_rules,
                                     fetcher=lambda u: self.healthy(u.replace(self.BASE, "")))
        self.assertTrue(any("canary" in x for x in result["problems"]))


class TlsContextTests(unittest.TestCase):
    def test_verification_stays_on_and_only_the_strict_flag_is_relaxed(self):
        import ssl
        ctx = ex.ssl_context()
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)
        self.assertFalse(ctx.verify_flags & ssl.VERIFY_X509_STRICT)


class WorkflowTests(unittest.TestCase):
    def test_preview_workflow_runs_the_exposure_check_against_the_deployment_url(self):
        wf = (REPO / ".github/workflows/deployment-exposure.yml").read_text(encoding="utf-8")
        self.assertIn("deployment_status", wf)
        self.assertIn("scripts/check_deployment_exposure.py", wf)
        self.assertIn("target_url", wf)
        self.assertIn("Preview", wf)


if __name__ == "__main__":
    unittest.main()
