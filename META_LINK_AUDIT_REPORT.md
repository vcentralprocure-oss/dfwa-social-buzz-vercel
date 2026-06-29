# Meta Links Audit Report - Arlington Pulse

**Date:** 2026-06-29  
**Auditor:** OpenClaw Agent  
**Scope:** Open Graph, Twitter Cards, JSON-LD structured data URLs  
**Status:** ⚠️ **ISSUES FOUND - AWAITING APPROVAL TO FIX**

---

## Executive Summary

**Problem:** Meta URLs (og:url, JSON-LD @id) in article pages are missing the `/arlington/` path prefix, causing 404s when accessed via social platforms or search engines.

**Root Cause:** The `add-article-schema.js` script generates incorrect URLs at line 157.

**Impact:** 1 confirmed file affected, potentially more if script is reused.

**Fix:** Update URL generation to include `/arlington/` prefix.

---

## Detailed Findings

### 1. URL Pattern Analysis

| URL Type | Current (Broken) | Correct (Working) |
|----------|------------------|-------------------|
| File Path | `/arlington/articles/FILE.html` | `/arlington/articles/FILE.html` |
| Meta URL | `https://arlington.dfwasocialbuzz.com/articles/FILE.html` ❌ | `https://arlington.dfwasocialbuzz.com/arlington/articles/FILE.html` ✅ |

### 2. Root Cause Location

**File:** `arlington/add-article-schema.js`  
**Line:** 157  
**Current Code:**
```javascript
metadata.url = `https://arlington.dfwasocialbuzz.com/articles/${fileName}`;
```

**Should Be:**
```javascript
metadata.url = `https://arlington.dfwasocialbuzz.com/arlington/articles/${fileName}`;
```

### 3. Affected Files

| File | og:url Status | JSON-LD Status |
|------|---------------|----------------|
| `5-local-arlington-gems-summer-2026.html` | ❌ Missing /arlington/ | ❌ Missing /arlington/ |

**Note:** Only 1 file currently has schema data. Other 53 files don't have JSON-LD yet, so they're not affected until schema is added.

### 4. Where URLs Are Generated

| Location | Purpose | Issue |
|----------|---------|-------|
| `add-article-schema.js:157` | Schema generation script | Missing `/arlington/` in URL template |
| `article-schema-template.html:95` | Documentation comment | Incorrect example URL |

---

## Proposed Fix

### Option 1: Fix the Script (Recommended)

Update `add-article-schema.js` line 157 to generate correct URLs.

**Pros:**
- Fixes root cause
- Prevents future issues
- Minimal code change

**Cons:**
- Requires regenerating schema for affected file

### Option 2: Fix Individual File

Manually update the meta URLs in `5-local-arlington-gems-summer-2026.html`.

**Pros:**
- Immediate fix
- No script changes needed

**Cons:**
- Doesn't fix root cause
- Issue will recur when script is used again

### Option 3: Fix Both

Fix the script AND update the affected file.

**Pros:**
- Fixes current issue
- Prevents future issues
- Most comprehensive

**Cons:**
- Slightly more work

---

## Recommended Approach: Option 3 (Fix Both)

### Step 1: Fix the Script

**File:** `arlington/add-article-schema.js`  
**Change:** Line 157

```diff
- metadata.url = `https://arlington.dfwasocialbuzz.com/articles/${fileName}`;
+ metadata.url = `https://arlington.dfwasocialbuzz.com/arlington/articles/${fileName}`;
```

### Step 2: Fix the Affected File

**File:** `arlington/articles/5-local-arlington-gems-summer-2026.html`

**Changes needed:**
1. Line 13: Update `og:url`
2. Line 46: Update JSON-LD `@id`

```diff
- <meta property="og:url" content="https://arlington.dfwasocialbuzz.com/articles/5-local-arlington-gems-summer-2026.html">
+ <meta property="og:url" content="https://arlington.dfwasocialbuzz.com/arlington/articles/5-local-arlington-gems-summer-2026.html">
```

```diff
- "@id": "https://arlington.dfwasocialbuzz.com/articles/5-local-arlington-gems-summer-2026.html"
+ "@id": "https://arlington.dfwasocialbuzz.com/arlington/articles/5-local-arlington-gems-summer-2026.html"
```

---

## Before/After Table

| # | Element | Before (404) | After (200) |
|---|---------|--------------|-------------|
| 1 | og:url | `https://arlington.dfwasocialbuzz.com/articles/5-local-arlington-gems-summer-2026.html` | `https://arlington.dfwasocialbuzz.com/arlington/articles/5-local-arlington-gems-summer-2026.html` |
| 2 | JSON-LD @id | `https://arlington.dfwasocialbuzz.com/articles/5-local-arlington-gems-summer-2026.html` | `https://arlington.dfwasocialbuzz.com/arlington/articles/5-local-arlington-gems-summer-2026.html` |

---

## Verification Plan

After fix:
1. Re-run `audit-meta-links.js` to confirm 0 issues
2. Verify URLs return 200 (not 404)
3. Check that social preview URLs work correctly

---

## Files to Modify

| File | Lines | Change Type |
|------|-------|-------------|
| `arlington/add-article-schema.js` | 157 | URL template fix |
| `arlington/articles/5-local-arlington-gems-summer-2026.html` | 13, 46 | Meta URL updates |

---

## Guardrails Honored

- ✅ No CSS changes
- ✅ No form changes
- ✅ No layout changes
- ✅ Only URL data corrections
- ✅ Minimal, targeted fixes

---

## Approval Requested

**Son, please approve one of the following:**

1. **"Approve Option 1"** - Fix the script only (prevents future issues)
2. **"Approve Option 2"** - Fix the affected file only (immediate fix)
3. **"Approve Option 3"** - Fix both script and file (recommended)
4. **"Hold"** - Do nothing, keep report for later

Or specify a custom approach.

---

*Report generated by OpenClaw Agent on 2026-06-29*
