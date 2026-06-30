# Link Audit Process

**Version:** 1.0  
**Last Updated:** 2026-06-29  
**Applies To:** Arlington Pulse, Dallas Current, Fort Worth Eco, and future publications

---

## Purpose

Standardized workflow for auditing "Read Issue" and other critical links across DFWA Social Buzz publications.

---

## Workflow

### Phase 1: Discovery & Report (AUTOMATED)

**Agent Actions:**
1. Crawl the site's "Latest Issues" cards (desktop + mobile views)
2. Catalog all "Read Issue →" links with: title, date, href, status code
3. Identify 404s and document mismatch patterns
4. Determine root cause (data vs template logic)
5. Generate comprehensive audit report

**Deliverables:**
- `LINK_AUDIT_REPORT.md` with findings
- `link-audit-results.json` (machine-readable)
- Before/after table of broken vs working URLs
- Root cause analysis

**STOP HERE. Do not proceed to Phase 2 without explicit approval.**

---

### Phase 2: Approval Gate (HUMAN REQUIRED)

**Agent Action:** Present report to Son and ask:

> "Link audit complete. Found [X] broken links causing 404s. 
> 
> **Options:**
> 1. **Remove broken cards** - Delete invalid HTML entries (fastest)
> 2. **Create missing articles** - Generate article files to match existing links
> 3. **Fix slug mapping** - Update hrefs to point to existing similar articles
> 
> Approve to proceed with fix, or specify alternative approach."

**Son Options:**
- Reply "Approve Option 1" → Proceed with removal
- Reply "Approve Option 2" → Create missing content
- Reply "Approve Option 3" → Remap URLs
- Reply "Hold" → Do nothing, keep report for later
- Specify custom approach

---

### Phase 3: Implementation (APPROVAL REQUIRED)

**Only proceed if explicitly approved.**

**Agent Actions:**
1. Create backup of original file(s)
2. Implement approved fix
3. Re-run audit to verify all links return 200
4. Document changes in report
5. Stage changes (git commit) or prepare PR

**Constraints (always honored):**
- No CSS changes
- No form changes  
- No card layout changes
- Only adjust data or URL-building logic
- Create backups before any modifications

---

### Phase 4: Production Deploy (APPROVAL REQUIRED)

**Agent Actions:**
1. Present verification results to Son
2. Request production deploy approval
3. Upon approval: deploy to production
4. Monitor 404 logs / GA4 for 24-48 hours
5. Report any anomalies

---

## Scripts & Tools

| Script | Purpose |
|--------|---------|
| `audit-links.js` | Crawl and catalog all links with status codes |
| `analyze-mismatch.js` | Deep analysis of broken link patterns |
| `fix-broken-links.js` | Apply fixes (only run with approval) |

---

## File Locations

```
dfwa-vercel/
├── arlington/index.html          # Arlington Pulse homepage
├── dallas/index.html             # Dallas Current homepage  
├── fort-worth/index.html         # Fort Worth Eco homepage
├── audit-links.js                # Link crawler
├── analyze-mismatch.js           # Root cause analyzer
├── fix-broken-links.js           # Fix implementation
└── .github/workflows/
    └── link-audit-process.md     # This file
```

---

## Checklist

### Pre-Audit
- [ ] Confirm site URL is accessible
- [ ] Verify local repo is up to date
- [ ] Check for existing audit artifacts

### Phase 1 (Report Only)
- [ ] Crawl desktop and mobile views
- [ ] Test all "Read Issue" links
- [ ] Document 404s with titles and URLs
- [ ] Analyze root cause
- [ ] Generate report
- [ ] **STOP - Wait for approval**

### Phase 2 (Approval)
- [ ] Present report to Son
- [ ] Get explicit approval for fix approach
- [ ] Document approval in chat/thread

### Phase 3 (Fix - If Approved)
- [ ] Create backup file
- [ ] Implement approved fix
- [ ] Re-run audit to verify
- [ ] Confirm 100% links return 200
- [ ] Stage/commit changes

### Phase 4 (Deploy - If Approved)
- [ ] Get production deploy approval
- [ ] Deploy to production
- [ ] Monitor 404 logs for 24-48 hours
- [ ] Report results

---

## Emergency Rollback

If issues arise post-deploy:

```bash
# Restore from backup
cp arlington/index.html.bak.linkfix arlington/index.html

# Or restore from git
git checkout arlington/index.html
```

---

*Process established 2026-06-29 after Arlington Pulse link audit*
