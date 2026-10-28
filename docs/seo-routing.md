# SEO routing, canonical host, and indexing

Status: **phase 1 (feature branch only).** This tooling does not change production. Merging, deploying, DNS, and hosting settings each need separate approval.

## Canonical host

- Canonical host: `https://dfwasocialbuzz.com` (the apex), set in `scripts/seo_config.json`.
- This matches the pages already on `main`: 10 `og:url` values and 16 structured-data URLs use the apex, and none use `www`. Article URLs end in `.html`.
- Publication subdomains such as `arlington.dfwasocialbuzz.com` are never used. Existing repo links to that subdomain (87 files) are a separate content cleanup, not changed here.
- Redirecting `www` to the apex is a hosting setting, not a repository change, and is outside this tooling.

## Hosting observations

An earlier version of this document listed observed responses for the public hostnames. Those observations were taken from a machine with a local hosts-file override and were not valid for the public, so they have been removed. Check the live hosts directly before relying on any hosting claim.

## `/a/<slug>` links from Letterman

- Letterman article links are `https://dfwasocialbuzz.com/a/<urlPath>` (or `/a/<id>` when no slug is set).
- **There is no `/a/` redirect in `vercel.json`.** A blanket `/a/:slug` redirect was tested on a preview and removed, because:
  - none of Letterman's 23 Arlington articles had a matching `/arlington/articles/<slug>.html`, so every `/a/<slug>` ended in a 404;
  - a permanent redirect is cached by browsers and CDNs, so a wrong mapping persists;
  - `m.letterman.ai/a/<slug>` redirects to `dfwasocialbuzz.com/a/<slug>`, so a fallback to Letterman's shared domain would loop;
  - a catch-all cannot be validated against a list of real pages.
- **Future behavior:** add an explicit redirect only for a verified pair: the Letterman article is published and not noindex, and its page already exists in the repo. The destination must be the absolute canonical URL (`https://dfwasocialbuzz.com/arlington/articles/<slug>.html`). Use a temporary (307) redirect while verifying, then permanent.
- `tests/test_vercel_config.py` enforces this: it fails on any catch-all `/a/` pattern, on any redirect that would catch an unknown `/a/` slug, and on any explicit `/a/` redirect whose destination page does not exist or is not on the canonical host.
- Any `/a/` redirect needs its own approval and is not part of this tooling.

## Sitemap and robots

- `sitemap.xml` and `robots.txt` are generated from the real pages by `scripts/generate_seo.py`.
- Included: root, `arlington/`, `arlington/articles/`, `contact/`, `deals/`, `business/`, `privacy-policy/`, `terms-and-conditions/`.
- Excluded: any file matching `scripts/seo_config.json` exclude globs (backups, test and sample pages, templates), and any page with a noindex robots meta tag.
- Dallas, Fort Worth, and `fortworth/` are not included, because those hubs are marked "Coming Soon" and are not part of the Arlington publishing scope.
- `robots.txt` contains no Disallow rules (there were none on `main`), and one `Sitemap:` line.
- CI fails if the committed files are stale (`--check`).

## Canonical and Open Graph tags

- Added **only to new pages** through `scripts/generate_seo.py --tag-new-page`, which refuses any file git already tracks.
- Existing pages are not modified in phase 1. 14 existing pages already carry `og:title`, which is left unchanged.
- Canonical URL = the page's route on the canonical host. OG image = absolute URL on the canonical host.

## Serpsling and schema

- Not used for schema or canonical handling. Letterman does not expose schema. Website JSON-LD is a later phase.
