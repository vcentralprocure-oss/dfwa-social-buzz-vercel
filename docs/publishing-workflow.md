# Publishing workflow (phases 1 and 2)

This describes the tooling on the feature branch `claude/publishing-pipeline-seo`. It does not change production. Merging, deploying, DNS, Cloudflare, and Vercel production settings each need separate approval.

## What runs on every pull request

`.github/workflows/site-checks.yml` runs:

1. `python -m unittest discover -s tests -v`: unit tests for the SEO tools, link gate, importer, and Vercel config.
2. `python scripts/generate_seo.py --check`: fails if `sitemap.xml` or `robots.txt` are out of date. Fix with `python scripts/generate_seo.py`, then commit the result.
3. `python scripts/validate_site.py`: fails only on **new** errors. Known pre-existing errors are in `scripts/validator_baseline.json` (a ratchet: it can shrink, it should not grow).
4. `python -m unittest tests.test_vercel_config`: keeps existing `vercel.json` redirects, rewrites, crons, function limits, and blocks any catch-all `/a/` redirect.
5. `python scripts/import_letterman_article.py --verify-all`: for every snapshot in `content/letterman/` that has a page, re-checks draft protection, canonical and Open Graph tags, the link gate, and that the page text still equals the approved Letterman text.

## Importing an approved Letterman article (phase 2)

The pipeline never contacts Letterman from CI and can never change a Letterman article's status. A Claude session reads the approved article through the Letterman connector and writes a committed **snapshot**.

### 1. Snapshot (`content/letterman/<slug>.json`)

```
letterman: id, state, url_path, title, description, summary_description, no_index,
           blocks[] (type, index, subTitle, html)
approval:  approved_by, approved_at, site_publish_date (YYYY-MM-DD), image_alt,
           quadrant, quadrant_evidence, manual_review, [allow_draft_state]
image:     file (arlington/images/articles/<slug>.<jpg|png|webp>), source_url
```

- The slug **is** Letterman's `urlPath`, exactly. A missing or ID-style slug is refused.
- The image is downloaded **into the repo** at `arlington/images/articles/<slug>.<ext>` so the page does not depend on Letterman storage.
- `approval` is the site approval record. Without it, nothing is imported.
- `quadrant` is one of `north`, `south`, `central`, `east`, `all`, chosen under `docs/arlington-quadrant-policy.md`. Anything other than `all` needs `quadrant_evidence`. Ambiguous locations use `all` with `manual_review: true`.

### 2. Import

```
python scripts/import_letterman_article.py content/letterman/<slug>.json --dry-run
python scripts/import_letterman_article.py content/letterman/<slug>.json
```

On success it writes `arlington/articles/<slug>.html` from `templates/arlington-article-page.html`, adds one card at the top of the Arlington hub, and regenerates `sitemap.xml` and `robots.txt`. On any error it prints `IMPORT REFUSED. Nothing was written.` with one actionable line per problem.

### 3. Then

Run the tests and `validate_site.py`, push the branch, inspect the Vercel preview, and ask for approval. Do not merge without it.

## Draft protection

An import is refused unless **all** of these hold:

- Letterman state is `PUBLISHED`. A complete approval record does **not** override a draft. `approval.allow_draft_state: true` exists only for local dry runs; **never commit** a snapshot for an unpublished article, because this repository is public on GitHub (see `docs/deployment-exposure.md`).
- The approval record has `approved_by`, `approved_at`, `site_publish_date`, `image_alt`, and `quadrant`.
- The slug is valid and no page with that slug exists. An existing page is never overwritten.

CI re-checks every committed snapshot: a snapshot whose state is not `PUBLISHED` fails with `draft-snapshot-committed`, and a snapshot that has a page must also pass the approval, tag, link and text checks.

## What the importer validates

| Area | Blocks the import | Only warns |
|---|---|---|
| Body | tags other than `p`, `strong`, `em`, `u`, `a`; attributes; text outside paragraphs; empty body | text tells readers to visit an "official page" but no link URLs were supplied |
| Text | page text must equal the approved text (empty spacer paragraphs are dropped) | headline block title differs from article title |
| Links | broken internal links; malformed or unsafe URLs; `arlington.dfwasocialbuzz.com`; Letterman `/a/` or `m.letterman.ai` URLs; apex (`dfwasocialbuzz.com`) absolute links | `http` links; tracking parameters; duplicate or generic links |
| Image | missing, empty, over 2 MB, wrong format, extension mismatch, wrong path | narrower than 1200 px; unknown dimensions |
| Metadata | missing description; excerpt over 150 characters (never truncated) | meta description over 160 characters |
| Hub | duplicate card; missing or repeated `archive-grid` anchor | |

External links in the body get `target="_blank" rel="noopener noreferrer"` automatically. Reachability of external links is **not** checked in CI. See `docs/backlink-audit.md`.

## Page, metadata, and hub rules

- **Page:** same header, CSS, and footer as the live Arlington articles. No related-articles block. Subscribe and business links are relative, never the `arlington.` subdomain or the apex.
- **Metadata (new pages only):** one canonical tag and one Open Graph set, on `https://www.dfwasocialbuzz.com`. Existing pages are never modified. Letterman keywords are not rendered, and no JSON-LD is added in this phase.
- **`noIndex` articles:** the page gets `noindex, nofollow` and no canonical or Open Graph tags, is excluded from the sitemap, and gets no hub card.
- **Hub card:** exactly one card at the top of the grid, using `summary_description` (or `description`). The hub file's line endings are preserved. The hub shows only the first six cards, so each new card pushes the oldest visible card out of view. The cap itself is unchanged.

## Not changed by this tooling

- DNS, Cloudflare, Vercel production settings, `vercel.json` routing, and `main`.
- Existing article pages, existing hub cards, and existing labels.
- Letterman articles and their statuses.

## Adding a hand-written page (phase 1 method, still available)

1. Create the page as a new file under `arlington/articles/`. It must not already be tracked by git.
2. `python scripts/generate_seo.py --tag-new-page arlington/articles/<slug>.html --meta meta.json`
3. `python scripts/generate_seo.py`, then `python scripts/validate_site.py`.
