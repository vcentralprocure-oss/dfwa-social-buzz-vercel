# Backlink audit (optional, non-blocking)

`scripts/audit_backlinks.py` is a **separate, optional** review tool. It is not part of CI and not part of the publishing gate. It always exits 0.

## What it does

- Lists every external domain the eligible site pages link to, with link counts and the pages that carry them.
- With `--check`, tests whether each external URL is reachable and reports failures as **warnings** for an editor to review. Live checks are never run in CI, because business sites time out or block automated requests and would make releases flaky.

```
python scripts/audit_backlinks.py            # offline inventory
python scripts/audit_backlinks.py --json
python scripts/audit_backlinks.py --check    # also test reachability (network)
```

## How it differs from the publishing gate

| | Publishing link gate (`scripts/link_gate.py`) | Backlink audit |
|---|---|---|
| Runs | On every import and in CI | On demand |
| Scope | The new article's body | All eligible pages |
| Blocks a release | **Yes**: broken internal links, malformed or unsafe URLs, forbidden hosts, apex self-links, `target="_blank"` without `rel` | **Never** |
| Warns | `http` links, tracking parameters, duplicates, generic link text | Unreachable external links |
| Network | No | Only with `--check` |

## Suggested use

Run the audit before a larger content change, or monthly, and review the unreachable list by hand. Fixing a business link is a content change and needs its own approval.
