# Letterman → Vercel Sync Workflow

## Overview
This workflow allows Letterman to manage content while Vercel hosts better-designed pages.

## How It Works

### 1. Content Creation (Letterman)
- Create and publish articles in Letterman dashboard
- Articles automatically get URLs like:
  - `https://m.letterman.ai/a/article-slug`

### 2. Article Sync (Manual or Automated)
**Option A: Manual (Recommended for now)**
```bash
# When new article published in Letterman:
# 1. Copy article headline, date, excerpt
# 2. Add to Vercel page HTML
# 3. Link to Letterman full article
# 4. Deploy to Vercel
```

**Option B: Automated (Future)**
- Script pulls articles from Letterman API
- Updates HTML templates
- Auto-deploys to Vercel

### 3. Visitor Experience
1. Visitor lands on Vercel page (better design)
2. Sees article preview cards
3. Clicks "Read More" → goes to Letterman (full content)
4. Letterman tracks engagement, delivers content

## Current Setup

### Vercel Pages (Presentation Layer)
- **Root:** https://dfwa-social-buzz-vercel-9krkzz6cz.vercel.app/
- **Arlington:** /arlington/
- **Dallas:** /dallas/
- **Fort Worth:** /fort-worth/

### Letterman Publications (Content Layer)
- **Arlington Pulse:** ID 69ee9d94a166af267eb5e972
- **Dallas Current:** ID 69ee9da5a166af267eb5e999
- **Fort Worth Echo:** ID 69ee9da6a166af267eb5e99e

## Recommended Workflow

### For Each New Article:

1. **Create in Letterman**
   - Write full article
   - Add images
   - Publish
   - Copy the article URL

2. **Update Vercel Page**
   - Add article card to city page
   - Include: headline, date, excerpt
   - Link to Letterman full article
   - Keep Vercel design/styling

3. **Deploy**
   - Commit changes
   - Push to GitHub
   - Vercel auto-deploys

### Example Article Card HTML:
```html
<div class="issue-card">
    <h4>Article Headline</h4>
    <div class="date">April 29, 2026</div>
    <p>Short excerpt from article...</p>
    <a href="https://m.letterman.ai/a/article-slug" target="_blank">Read Issue →</a>
</div>
```

## Benefits

| Letterman | Vercel |
|-----------|--------|
| Content management | Better design control |
| Newsletter delivery | Custom branding |
| Subscriber management | SEO optimization |
| Analytics | Performance |

## Next Steps

1. **Test the workflow:**
   - Publish new article in Letterman
   - Add to Vercel page manually
   - Verify links work

2. **Optional automation:**
   - Build API integration script
   - Schedule regular syncs
   - Auto-update pages

## Files

- `sync-letterman.sh` - Future automation script
- `/arlington/index.html` - Arlington hub page
- `/dallas/index.html` - Dallas hub page
- `/fort-worth/index.html` - Fort Worth hub page

## Questions?

This is a hybrid approach that gives you:
- ✅ Letterman's content management
- ✅ Vercel's design flexibility
- ✅ Simple manual workflow (for now)
- ✅ Option to automate later