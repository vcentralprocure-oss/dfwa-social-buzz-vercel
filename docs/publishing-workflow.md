# Publishing workflow (phase 1)

This describes the checks that exist on the feature branch. Phase 1 does not change production.

## What runs on every pull request

`.github/workflows/site-checks.yml` runs:

1. `python -m unittest discover -s tests -v`: unit tests for the SEO tools and Vercel config.
2. `python scripts/generate_seo.py --check`: fails if `sitemap.xml` or `robots.txt` are out of date. Fix with `python scripts/generate_seo.py`, then commit the result.
3. `python scripts/validate_site.py`: fails only on **new** errors. Known pre-existing errors are listed in `scripts/validator_baseline.json`. The baseline is a ratchet, so it can shrink but should not grow.
4. `python -m unittest tests.test_vercel_config`: keeps existing `vercel.json` redirects, rewrites, crons, and function limits.

## Adding a new article page (phase 1 method)

1. Create the page as a new file under `arlington/articles/`. It must not already be tracked by git.
2. Add canonical and Open Graph tags:
   ```
   python scripts/generate_seo.py --tag-new-page arlington/articles/<slug>.html --meta meta.json
   ```
   `meta.json` contains `title`, `description`, and optionally `image` (a repo path) and `published` (ISO date).
3. Run `python scripts/generate_seo.py` to update `sitemap.xml`.
4. Run `python scripts/validate_site.py` and fix any NEW errors.
5. Open a pull request. Vercel builds a preview automatically from the branch.

## Not in phase 1

- Changes to existing article pages, the hub, or the root homepage.
- JSON-LD schema.
- Production routing, DNS, Cloudflare, Vercel project settings, and merging to `main`. Each needs separate approval.
- The Letterman snapshot step and any automated Letterman import.
