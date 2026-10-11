"""Check that a DEPLOYED site does not expose internal files (read-only HTTP GETs).

Usage:
  python scripts/check_deployment_exposure.py https://<preview-host>   # probe a deployment
  python scripts/check_deployment_exposure.py --offline                # rule coverage only

How it works:
  1. Reads the exclusion rules from /.vercelignore (gitignore syntax).
  2. Lists every git-tracked file those rules exclude (the "internal files").
  3. Requests each one from the deployed site WITHOUT following redirects. Any 2xx
     response means the file is public: that is an exposure.
  4. Requests the canary (content/letterman/EXPOSURE_CANARY.txt) and a few public
     routes and API routes to confirm the deployment is otherwise healthy.

A 404 alone is not treated as proof that nothing leaks: the check covers every tracked
internal file individually, and it fails if the network is unreachable (status 0).
"""

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANARY = "content/letterman/EXPOSURE_CANARY.txt"
PUBLIC_ROUTES = ["/", "/arlington/", "/robots.txt", "/sitemap.xml", "/privacy-policy/",
                 "/docs/arlington-quadrant-policy.md"]
API_ROUTES = ["/api/subscribe"]  # a GET reaches the function (405), so it must not be 404 or 5xx


# ------------------------------------------------------------------ rules (.gitignore subset)

class Rule:
    def __init__(self, raw):
        self.raw = raw
        self.negate = raw.startswith("!")
        body = raw[1:] if self.negate else raw
        self.dir_only = body.endswith("/")
        body = body.rstrip("/")
        self.anchored = body.startswith("/") or "/" in body
        body = body.lstrip("/")
        self.regex = re.compile("^" + self._translate(body) + "$")

    @staticmethod
    def _translate(pattern):
        out, i = [], 0
        while i < len(pattern):
            c = pattern[i]
            if pattern.startswith("**", i):
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c))
            i += 1
        return "".join(out)

    def matches(self, path, is_dir):
        if self.dir_only and not is_dir:
            return False
        if self.anchored:
            return bool(self.regex.match(path))
        return bool(self.regex.match(path.rsplit("/", 1)[-1]))


def parse_rules(text):
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rules.append(Rule(line))
    return rules


def is_ignored(path, rules):
    """Gitignore semantics: the last matching rule wins, and a file inside an
    excluded directory cannot be re-included."""
    parts = path.split("/")
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        is_dir = i < len(parts)
        state = None
        for rule in rules:
            if rule.matches(sub, is_dir):
                state = not rule.negate
        if is_dir and state:
            return True
        if not is_dir:
            return bool(state)
    return False


def tracked_files(root):
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def load_rules(root):
    return parse_rules((Path(root) / ".vercelignore").read_text(encoding="utf-8"))


def internal_files(root, rules=None, tracked=None):
    rules = rules if rules is not None else load_rules(root)
    tracked = tracked if tracked is not None else tracked_files(root)
    return sorted(p for p in tracked if is_ignored(p, rules))


# ------------------------------------------------------------------ probing

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_status(url, timeout=20):
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "DFWASocialBuzz-exposure-check/1.0"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def _url(base, path):
    return base.rstrip("/") + "/" + urllib.parse.quote(path.lstrip("/"), safe="/")


def check_deployment(base_url, root=ROOT, fetcher=fetch_status, tracked=None, rules=None):
    root = Path(root)
    internal = internal_files(root, rules, tracked)
    result = {"internal_checked": len(internal), "exposed": [], "unverified": [], "problems": []}
    if CANARY not in internal:
        result["problems"].append(f"canary {CANARY} is missing or not excluded by .vercelignore")
    for path in internal:
        status = fetcher(_url(base_url, path))
        if 200 <= status < 300:
            result["exposed"].append((path, status))
        elif status == 0:
            result["unverified"].append(path)
    for route in PUBLIC_ROUTES:
        status = fetcher(_url(base_url, route) if route != "/" else base_url.rstrip("/") + "/")
        if not 200 <= status < 300:
            result["problems"].append(f"public route {route} returned {status}")
    for route in API_ROUTES:
        status = fetcher(_url(base_url, route))
        if status == 404 or status == 0 or status >= 500:
            result["problems"].append(f"API route {route} returned {status}; the function may be missing")
    return result


def report_ok(result):
    return not (result["exposed"] or result["unverified"] or result["problems"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_url", nargs="?")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--offline", action="store_true", help="list rule coverage without any network access")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.offline or not args.base_url:
        files = internal_files(root)
        print(f"{len(files)} tracked internal files are excluded by .vercelignore:")
        for f in files:
            print(f"  {f}")
        return 0 if CANARY in files else 1
    result = check_deployment(args.base_url, root)
    print(f"probed {result['internal_checked']} internal files on {args.base_url}")
    for path, status in result["exposed"]:
        print(f"  EXPOSED ({status}): /{path}")
    for path in result["unverified"]:
        print(f"  COULD NOT VERIFY (no response): /{path}")
    for problem in result["problems"]:
        print(f"  PROBLEM: {problem}")
    if report_ok(result):
        print("OK: no internal file is reachable, and the public and API routes respond")
        return 0
    print("FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
