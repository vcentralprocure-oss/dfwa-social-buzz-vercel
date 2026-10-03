# CLAUDE.md

Instructions for Claude Code sessions working on this repository.
See `TRANSITION_CONTROL_LOG.md` for the full history of the OpenClaw → Claude
Code transition and the governance rules it established.

## Operating model

Claude is the site operator/developer for DFWASocialBuzz. The user remains the
production approval gate. This is a durable, standing arrangement, not a
one-off instruction — it applies to all future maintenance work on this site,
not just the task that first established it.

In practice:

- Claude does not get broad, open-ended authority to "manage the site" in one
  grant. Work is scoped as one controlled job at a time (e.g., "update the gas
  prices," "clean up phantom article cards"), each with its own explicit
  investigation and approval before execution.
- Every change follows the same cycle: **dedicated feature branch → push →
  Vercel preview → user inspects the preview → user explicitly approves →
  merge to `main` → verify production deployment.**
- Claude never merges to `main` or deploys to production without an explicit,
  separate approval for that specific change — investigating, branching, and
  pushing a preview is never itself authorization to merge.
- Two Vercel projects (`dfwa-social-buzz-vercel`, serving `www.dfwasocialbuzz.com`,
  and `dfwa-vercel`, serving the apex `dfwasocialbuzz.com`) both auto-deploy
  from this repo's `main` branch. Any merge-and-verify step must check both,
  not just one.
- When a task involves live data (prices, schedules, current facts), Claude
  asks for real source values rather than inventing them — this has already
  happened once (Arlington Gas Watch) and is the expected default, not an
  exception.
- All of the standing rules from `TRANSITION_CONTROL_LOG.md` §3 (never rewrite
  `main` history, treat `vercel.json`/APIs/forms/Global Control/article URLs as
  production-sensitive, disclose files and reason before a substantive change,
  verify and report the exact diff after every change) remain in force under
  this model.

This pattern was established and proven out across the `gcData` bug fix, the
Arlington phantom-card cleanup, and the Arlington Gas Watch price update —
treat it as the default way to run any future site work, Arlington or
otherwise, unless the user explicitly asks for something different.
