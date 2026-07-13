# Arlington Pulse Card Data Structure

## Source-of-Truth Mapping

Cards should ONLY contain these public-facing fields:

```
headline      → <h4> text (required)
date          → <div class="date"> text (required)  
quadrant      → data-quadrant attribute + badge class (required)
excerpt       → <p> teaser text (required)
url           → <a href> link (required)
status        → "live" | "coming-soon" (determines CTA)
```

## Internal OC Fields (NEVER in DOM)

These fields are for AI/content generation ONLY and must NEVER appear in public cards:

- `PUBLICATION:` - Internal metadata
- `AUDIENCE VOICE:` - AI prompt instruction
- `TOPIC:` - Source classification
- `SOURCE URL:` - Attribution tracking
- `WORD COUNT:` - AI constraint
- `FORMAT:` - AI instruction
- `TONE:` - AI instruction
- `DO NOT:` - AI constraint

## Card Template

### Live Article (has URL)
```html
<div class="issue-card" data-quadrant="[north|south|central|east|all]">
    <span class="quadrant-badge [quadrant]">[QUADRANT]</span>
    <h4>[Headline]</h4>
    <div class="date">[Month DD, YYYY]</div>
    <p>[Clean teaser excerpt - NO metadata]</p>
    <a href="/arlington/articles/[slug].html">Read Issue →</a>
</div>
```

### Coming Soon (no URL yet)
```html
<div class="issue-card" data-quadrant="[quadrant]">
    <span class="quadrant-badge [quadrant]">[QUADRANT]</span>
    <h4>[Headline]</h4>
    <div class="date">[Month DD, YYYY]</div>
    <p>[Clean teaser excerpt]</p>
    <span class="coming-soon">Article coming soon</span>
</div>
```

## Excerpt Generation Rules

1. **NEVER use raw brief text** (contains OC metadata)
2. **NEVER truncate mid-sentence**
3. **ALWAYS use quadrant-appropriate teasers**
4. **Maximum 150 characters**
5. **Must make sense to readers** (no internal codes)

### Quadrant Teaser Templates

| Quadrant | Teaser Examples |
|----------|-----------------|
| NORTH | "Entertainment District updates", "What's happening near Globe Life Field" |
| SOUTH | "South Arlington community news", "Updates for local families" |
| CENTRAL | "Downtown Arlington news", "UTA campus area updates" |
| EAST | "East Arlington happenings", "Division Street corridor news" |
| ALL | "Citywide Arlington news", "Updates affecting all residents" |

## Badge CSS Classes

```css
.quadrant-badge.north   { background: #3B82F6; }  /* Blue */
.quadrant-badge.south   { background: #22C55E; }  /* Green */
.quadrant-badge.central { background: #A855F7; }  /* Purple */
.quadrant-badge.east    { background: #F59E0B; }  /* Yellow */
.quadrant-badge.all     { background: #FF6B35; }  /* Orange */
```

## Pipeline Fix Applied

**File:** `~/.openclaw/skills/arlington-daily-pipeline/scripts/daily_pipeline.py`

**Changes:**
1. Separated `generate_brief()` (for AI) from `generate_excerpt()` (for public cards)
2. `generate_excerpt()` creates clean teasers from quadrant templates
3. Updated caller to use `generate_excerpt()` instead of truncating brief

**Result:** New cards will have clean excerpts, never raw OC metadata.
