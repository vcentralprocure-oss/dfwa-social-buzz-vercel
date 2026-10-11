# SEO routing, canonical host, and indexing

Status: **phase 1 (feature branch only).** Production canonicalization and indexing are **blocked** until the public domains are verified to serve the Vercel site. Do not treat the generated sitemap as production-ready before then.

## Canonical host

- Intended canonical host: `https://www.dfwasocialbuzz.com` (set in `scripts/seo_config.json`).
- The apex `https://dfwasocialbuzz.com` must redirect to `www` (single hop). Not yet verified.
- Nothing publishes on `arlington.dfwasocialbuzz.com`. Existing repo links to that subdomain (87 files) are a separate content cleanup, not changed here.

## Current verified state (as of this branch)

| Host | Observed | Expected |
|---|---|---|
| `www.dfwasocialbuzz.com/` | 200, legacy Apache page | Vercel site |
| `www.dfwasocialbuzz.com/arlington/` | 404 | 200 |
| `dfwasocialbuzz.com/` | 200, legacy Apache page | 308 to `www` |
| `dfwa-social-buzz-vercel.vercel.app/arlington/` | 200 (Vercel) | 200 |

The Vercel project `dfwa-social-buzz-vercel` has `www.dfwasocialbuzz.com` attached. The project `dfwa-vercel` has the apex attached. Cloudflare DNS currently sends both public hosts to the legacy server. Fixing that is outside the repo.

## `/a/<slug>` links from Letterman

- Letterman article links are `https://dfwasocialbuzz.com/a/<urlPath>` (or `/a/<id>` when no slug is set).
- **There is no `/a/` redirect in `vercel.json`.** A blanket `/a/:slug` redirect was tested on a preview and removed, because:
  - none of Letterman's 23 Arlington articles had a matching `/arlington/articles/<slug>.html`, so every `/a/<slug>` ended in a 404;
  - a permanent redirect is cached by browsers and CDNs, so a wrong mapping persists;
  - `m.letterman.ai/a/<slug>` redirects to `dfwasocialbuzz.com/a/<slug>`, so a fallback to Letterman's shared domain would loop;
  - a catch-all cannot be validated against a list of real pages.
- **Future behavior:** add an explicit redirect only for a verified pair: the Letterman article is published and not noindex, and its page already exists in the repo. The destination must be the absolute canonical URL (`https://www.dfwasocialbuzz.com/arlington/articles/<slug>.html`). Use a temporary (307) redirect while verifying, then permanent.
- `tests/test_vercel_config.py` enforces this: it fails on any catch-all `/a/` pattern, on any redirect that would catch an unknown `/a/` slug, and on any explicit `/a/` redirect whose destination page does not exist or is not on the canonical host.
- Only after the public domains are verified to serve the Vercel site should any `/a/` redirect be considered for production.

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
