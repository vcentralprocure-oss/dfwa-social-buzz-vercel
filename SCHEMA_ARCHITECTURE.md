# JSON-LD Schema Architecture

## Overview
Centralized, template-based schema generation for DFWA Social Buzz. No runtime DOM manipulation - schemas are generated at build time or injected safely via dedicated script tags.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DATA SOURCE (Letterman, CMS, Sheets)                       │
│  ↓                                                          │
│  Cron/OpenClaw Task (every 6 hours)                         │
│  ↓                                                          │
│  data/articles-metadata.json                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  BUILD PROCESS                                              │
│  lib/build-schemas.js                                       │
│  ↓                                                          │
│  Reads templates/article-template.html                      │
│  ↓                                                          │
│  Replaces {{VARS}} and <!-- SCHEMA_PLACEHOLDER -->          │
│  ↓                                                          │
│  Generates: arlington/articles/*.html                       │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
dfwa-vercel/
├── lib/
│   ├── schema-helpers.js       # Core schema generation functions
│   ├── build-schemas.js        # Build-time script
│   └── runtime-schema.js       # Client-side fallback (optional)
├── data/
│   └── articles-metadata.json  # Article data (updated by cron)
├── templates/
│   └── article-template.html   # HTML template with placeholders
├── api/
│   └── update-articles.js      # Cron endpoint for data updates
└── arlington/
    └── articles/               # Generated HTML files
```

## Schema Helpers (lib/schema-helpers.js)

Centralized functions for generating schema objects:

```javascript
const {
  getOrganizationSchema,    // NewsMediaOrganization
  getWebSiteSchema,         // WebSite + SearchAction
  getWebPageSchema,         // WebPage for cities
  getArticleSchema,         // NewsArticle
  getBreadcrumbSchema,      // BreadcrumbList
  getPageSchemas,           // Get all schemas for a page type
  renderSchemaScripts,      // Convert to HTML script tags
  validateSchema            // Basic validation
} = require('./lib/schema-helpers');

// Usage in template/build
const articleSchema = getArticleSchema({
  headline: 'Article Title',
  description: 'Article description',
  url: 'https://arlington.dfwasocialbuzz.com/articles/...',
  image: 'https://...',
  datePublished: '2024-06-29T10:00:00-06:00',
  author: 'Author Name',
  cityKey: 'arlington'
});

const html = renderSchemaScripts([articleSchema]);
// Returns: <script type="application/ld+json">{...}</script>
```

## Build Process

### 1. Update Article Data (Cron)
```javascript
// POST /api/update-articles (runs every 6 hours)
// Fetches from Letterman/CMS → updates data/articles-metadata.json
```

### 2. Build HTML Files
```bash
# Local development
node lib/build-schemas.js

# This reads:
# - data/articles-metadata.json
# - templates/article-template.html
#
# And generates:
# - arlington/articles/*.html (with embedded schemas)
```

### 3. Deploy
```bash
vercel --prod
# or git push (triggers Vercel build)
```

## Template System

### Placeholders
Templates use `{{VARIABLE}}` syntax:

```html
<title>{{TITLE}} | Arlington Pulse</title>
<meta name="description" content="{{DESCRIPTION}}">
<!-- SCHEMA_PLACEHOLDER -->
```

### Schema Placeholder
The `<!-- SCHEMA_PLACEHOLDER -->` comment is replaced with:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  ...
}
</script>
```

## Data Format (articles-metadata.json)

```json
{
  "lastUpdated": "2024-06-29T03:30:00Z",
  "articles": [
    {
      "headline": "Article Title",
      "description": "Article description",
      "url": "https://arlington.dfwasocialbuzz.com/articles/slug.html",
      "slug": "slug.html",
      "image": "https://...",
      "datePublished": "2024-06-29T10:00:00-06:00",
      "dateModified": "2024-06-29T10:00:00-06:00",
      "author": "Author Name",
      "cityKey": "arlington",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

## Cron Configuration

Vercel runs the update every 6 hours:

```json
{
  "crons": [
    {
      "path": "/api/update-articles",
      "schedule": "0 */6 * * *"
    }
  ]
}
```

## Runtime Fallback (Optional)

If build-time generation isn't possible, use `lib/runtime-schema.js`:

```html
<head>
  <!-- Other head content -->
  <script src="/lib/runtime-schema.js"></script>
</head>
```

This script:
- Only touches `<head>` to add script tags
- Reads meta tags for article data
- Injects schemas after DOM is ready
- Does NOT modify forms, links, CSS, or layout

## Validation

Always validate before deploying:

```bash
# Test schema generation
node -e "
const { getArticleSchema, validateSchema } = require('./lib/schema-helpers');
const schema = getArticleSchema({
  headline: 'Test Article',
  description: 'Test description',
  url: 'https://example.com/article.html',
  datePublished: '2024-06-29T10:00:00-06:00'
});
console.log(validateSchema(schema));
"
```

Online tools:
- [Rich Results Test](https://search.google.com/test/rich-results)
- [Schema Validator](https://validator.schema.org/)

## Guardrails

1. **Schema is data, not code**
   - Uses `<script type="application/ld+json">` (not executable JS)
   - Cannot interfere with existing scripts

2. **Build-time generation**
   - No runtime DOM manipulation of content
   - Schemas embedded at build time

3. **Validation**
   - All schemas validated before injection
   - Errors logged, bad schemas skipped

4. **Feature flag**
   - Set `SCHEMA_ENABLED=false` to disable
   - Schemas won't be generated/injected

## Adding a New Article

### Option 1: Add to Metadata (Recommended)
```bash
# Edit data/articles-metadata.json
# Add article object
# Run build
node lib/build-schemas.js
# Deploy
git add -A && git commit -m "Add new article" && git push
```

### Option 2: Wait for Cron
```bash
# Article added to source (Letterman/CMS)
# Cron automatically updates data/articles-metadata.json
# Next build will include new article
```

## Troubleshooting

### Schemas not appearing
1. Check `data/articles-metadata.json` exists
2. Verify article has required fields (headline, url, datePublished)
3. Run `node lib/build-schemas.js` manually
4. Check for validation errors in console

### Invalid schema errors
1. Test with `validateSchema()` function
2. Check all required fields are present
3. Validate JSON at https://validator.schema.org/

### Cron not running
1. Check Vercel dashboard → Cron Jobs
2. Verify `CRON_SECRET` env var if set
3. Check function logs for errors
