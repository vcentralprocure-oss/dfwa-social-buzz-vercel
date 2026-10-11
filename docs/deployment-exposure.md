# Deployment exposure: keeping internal files private

## The problem

This Vercel project serves the **repository root as static files** (`vercel.json` sets `"outputDirectory": "."`). Without an exclusion, every tracked file is a public URL. That includes dot-folders: before this fix, `/.github/workflows/site-checks.yml` returned 200 on a preview.

For the publishing pipeline this matters because Letterman snapshots, approval records, test fixtures, tooling, and internal docs all live in the repo. A merge would otherwise publish them, including unpublished draft text.

## The fix

`/.vercelignore` excludes the pipeline's internal paths from every deployment:

| Excluded | Why |
|---|---|
| `/.github/` | CI workflows |
| `/scripts/`, `/tests/` | Tooling, tests, and fixtures |
| `/content/` | Letterman snapshots and approval records. The **whole directory** is excluded, so a snapshot added in the future can never become public |
| `/templates/arlington-article-page.html` | Importer template |
| `/docs/*` except `docs/arlington-quadrant-policy.md` | Internal docs; the quadrant policy is already public and stays public |

It is deliberately narrow. It does **not** touch `api/` (functions), `data/` (read at runtime by `api/update-articles.js`), the site pages, `vercel.json`, or any file that was public before this change. Other existing public files (for example `CLAUDE.md`, `backups/`, audit reports) are a separate cleanup that needs its own approval.

Defense in depth: the test fixture is synthetic text, not a real draft, so a future exclusion failure cannot publish unpublished copy.

## How it is verified

1. **Offline tests (`tests/test_deployment_exposure.py`, run in CI):**
   - every tracked internal file is covered by `.vercelignore`;
   - nothing public today is excluded;
   - future snapshots, approval records, tooling, and fixtures are covered;
   - removing the `/content/` rule would be noticed;
   - fixtures and `content/` contain no real draft text.
2. **Live check (`scripts/check_deployment_exposure.py <URL>`):** requests every tracked internal file, the canary, public routes, and an API route from a deployed site **without following redirects**. Any 2xx on an internal file fails. A site that cannot be reached is **not** reported as safe. A 404 on one file is not treated as proof for the rest.
3. **Automatic:** `.github/workflows/deployment-exposure.yml` runs the live check against each Vercel **Preview** deployment (`deployment_status` event). It is read-only.

The canary `content/letterman/EXPOSURE_CANARY.txt` must always return 404 on a deployed site. It is not a `*.json` file, so the importer ignores it.

## If the check fails

Treat any "EXPOSED" line as an incident: do not merge, and do not promote the deployment. Fix `.vercelignore`, redeploy the preview, and rerun the check.

## Adding new internal files

Put them under `scripts/`, `tests/`, `content/`, or `docs/` and they are excluded automatically. If a new top-level folder must stay private, add it to `.vercelignore` and to the lists in `tests/test_deployment_exposure.py`.
