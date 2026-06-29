# QuizForma → Global Control Integration Guide

## Overview
This integration automatically syncs QuizForma quiz submissions to Global Control CRM, enabling lead qualification, segmentation, and automated follow-up based on quiz answers.

## Endpoints

### Live Webhook Endpoint
```
POST https://dfwa-vercel.vercel.app/api/quizforma-webhook
```

### Test Endpoint
```
POST https://dfwa-vercel.vercel.app/api/quizforma-test
```
Use this to validate your payload structure before going live.

## Setup Instructions

### 1. QuizForma Webhook Configuration

#### Option A: Native Webhooks (if available in your QuizForma plan)
1. Go to QuizForma → Quiz Settings → Integrations
2. Enable "Send results to URL" or Webhooks
3. Set the callback URL to:
   ```
   https://dfwa-vercel.vercel.app/api/quizforma-webhook
   ```
4. Configure payload format as JSON
5. Include all relevant fields (see Payload Format below)
6. Add webhook secret if supported (set in environment variables)

#### Option B: Zapier/Make Integration
1. Create a new Zap/Make scenario
2. Trigger: "Quiz completion in QuizForma"
3. Action: Webhooks → POST
4. URL: `https://dfwa-vercel.vercel.app/api/quizforma-webhook`
5. Payload Type: JSON
6. Map quiz fields to the payload structure below

### 2. Environment Variables

Add to your Vercel project:
```
GC_API_KEY=your_global_control_api_key
QUIZFORMA_WEBHOOK_SECRET=your_optional_secret_for_validation
```

### 3. Payload Format

The endpoint accepts various formats. Here's the standard format:

```json
{
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "quiz_id": "arlington-subscribe-v1",
  "quiz_title": "Arlington Pulse Subscribe Quiz",
  "submitted_at": "2026-06-28T23:00:00Z",
  "answers": {
    "preferred_city": "Arlington",
    "audience_type": "Reader",
    "content_preference": "Local News, Events"
  },
  "score": 85
}
```

### 4. Data Mapping

| QuizForma Field | Global Control Field | Notes |
|----------------|---------------------|-------|
| email | Contact email | Required |
| firstName/name | firstName | Auto-extracted from full name |
| lastName | lastName | Auto-extracted from full name |
| quiz_id | last_quiz_id | Custom field |
| quiz_title | last_quiz_title | Custom field |
| submitted_at | last_quiz_date | Custom field |
| answers.preferred_city | preferred_city | Custom field |
| answers.audience_type | audience_type | Custom field |
| answers.content_preference | interest_segments | Custom field |
| score | last_quiz_score | Custom field |
| all answers | quiz_answers_json | Stored as JSON |

### 5. Tags Applied

The following tags are automatically applied in Global Control:

| Tag | Condition |
|-----|-----------|
| `quiz-participant` | All quiz submissions |
| `quiz-{quiz-id}` | Quiz-specific tag (e.g., `quiz-arlington-subscribe-v1`) |
| `audience-{type}` | Based on audience_type answer |
| `city-{city}` | Based on preferred_city answer |

## Testing

### Step 1: Test Payload Structure
```bash
curl -X POST https://dfwa-vercel.vercel.app/api/quizforma-test \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User",
    "quiz_id": "arlington-subscribe-v1",
    "quiz_title": "Arlington Pulse Subscribe Quiz",
    "answers": {
      "preferred_city": "Arlington",
      "audience_type": "Reader"
    }
  }'
```

### Step 2: Test Live Integration
```bash
curl -X POST https://dfwa-vercel.vercel.app/api/quizforma-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User",
    "quiz_id": "arlington-subscribe-v1",
    "quiz_title": "Arlington Pulse Subscribe Quiz",
    "answers": {
      "preferred_city": "Arlington",
      "audience_type": "Reader",
      "content_preference": "Local News"
    },
    "score": 90
  }'
```

### Step 3: Verify in Global Control
1. Log into Global Control dashboard
2. Search for the test email
3. Verify contact was created/updated
4. Check custom fields for quiz data
5. Confirm tags were applied

## Quiz Naming Convention

For consistency, use these standardized identifiers:

| Quiz | quiz_id | quiz_title |
|------|---------|------------|
| Arlington Subscribe | `arlington-subscribe-v1` | `Arlington Pulse Subscribe Quiz` |
| Dallas Subscribe | `dallas-subscribe-v1` | `Dallas Current Subscribe Quiz` |
| Fort Worth Subscribe | `fortworth-subscribe-v1` | `Fort Worth Eco Subscribe Quiz` |

## Troubleshooting

### Webhook Not Firing
- Check QuizForma webhook settings are saved
- Verify webhook URL is correct (no typos)
- Test with the test endpoint first

### Contact Not Created
- Verify `GC_API_KEY` environment variable is set
- Check Vercel function logs for errors
- Ensure email field is present in payload

### Tags Not Applied
- Known issue: Global Control's `fire-tag` endpoint may wipe name fields
- The integration automatically re-applies fields after tagging
- Check Global Control dashboard for tag presence

### Duplicate Contacts
- Integration searches by email before creating
- Existing contacts are updated, not duplicated
- Check email normalization (case sensitivity)

## Security

- Webhook secret validation supported (optional)
- API keys stored in environment variables only
- No sensitive data logged
- CORS configured for cross-origin requests

## Option C: API Polling (No Native Webhooks)

If QuizForma doesn't offer webhooks in your plan, you can use API polling as a fallback:

### API Polling Approach

**Status:** ⚠️ Partial - QuizForma API endpoints for responses are not fully functional

**Discovery:**
- ✅ `GET /quiz/get` - Lists quizzes (WORKS)
- ❌ `GET /quiz/{id}/responses` - Returns 404
- ❌ `GET /responses` - Returns 404
- ❌ `GET /quiz/get/{id}` - Returns 404

**Finding:** The QuizForma API only exposes quiz listing. Response/submission endpoints documented in the skill don't exist or have different URLs.

**Recommendation:** 
1. Check if QuizForma has a **Zapier** or **Make** integration (these often work even without native webhooks)
2. Contact QuizForma support to ask about response API endpoints
3. As a last resort, manually export quiz responses and POST them to the webhook endpoint

### Manual Export Workaround

If no automation is available, you can:
1. Export quiz responses from QuizForma dashboard (CSV)
2. Use a simple script to POST each row to the webhook:

```bash
# Example: POST a single quiz response
curl -X POST https://dfwa-vercel.vercel.app/api/quizforma-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "quiz_id": "arlington-subscribe-v1",
    "quiz_title": "Arlington Pulse Subscribe Quiz",
    "answers": {
      "preferred_city": "Arlington",
      "audience_type": "Reader"
    }
  }'
```

---

## API Discovery Log

**Date:** 2026-06-29  
**Tester:** OpenClaw  
**API Key:** Valid (returns quiz list)  
**Base URL:** `https://api.quizforma.com/api/ai`

**Working Endpoints:**
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/quiz/get` | GET | ✅ 200 | Returns paginated quiz list |

**Non-Working Endpoints:**
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/quiz/get/{id}` | GET | ❌ 404 | Quiz details |
| `/quiz/{id}/responses` | GET | ❌ 404 | Quiz submissions |
| `/responses` | GET | ❌ 404 | All responses |

**Conclusion:** The QuizForma API appears to be partially implemented or requires different authentication/endpoint structure for responses.

---

## Support

For issues or questions:
1. Check Vercel function logs
2. Verify Global Control API key permissions
3. Test with `/api/quizforma-test` endpoint
4. Review payload format matches expected structure
5. Contact QuizForma support about response API access

---

# JSON-LD Schema Implementation (AI Booster Replacement)

Since DFWA Social Buzz is not on WordPress, we've replicated the AI Booster plugin's schema generation functionality directly in the codebase.

## Schema Types Implemented

| Schema Type | Purpose | Location |
|-------------|---------|----------|
| `NewsMediaOrganization` | Identifies the publisher | All pages |
| `WebSite` | Site structure + search | All pages |
| `WebPage` | Page-level metadata | City homepages |
| `NewsArticle` | Article structured data | Article pages |
| `BreadcrumbList` | Navigation breadcrumbs | All pages |
| `LocalBusiness` | Business listings | Business pages |

## Files Created

| File | Purpose |
|------|---------|
| `arlington/schema.html` | Static schema include for Arlington homepage |
| `arlington/schema-generator.js` | JavaScript schema generation utilities |
| `arlington/schema-config.json` | Site/city configuration |
| `arlington/article-schema-template.html` | Template for article schemas |
| `arlington/add-article-schema.js` | Node.js script to add schema to existing articles |

## Usage

### For New Articles

Copy the template from `article-schema-template.html` and customize:
- `ARTICLE_URL` - Full article URL
- `ARTICLE_HEADLINE` - Article title
- `ARTICLE_DESCRIPTION` - Brief summary
- `ARTICLE_IMAGE_URL` - Featured image (1200x630)
- `AUTHOR_NAME` - Author name
- `datePublished` - ISO 8601 date

### For Existing Articles

Run the script to auto-add schema:
```bash
cd /root/.openclaw/workspace/dfwa-vercel/arlington
node add-article-schema.js articles/my-article.html
```

With custom values:
```bash
node add-article-schema.js articles/my-article.html \
  --headline="Custom Headline" \
  --date="2024-06-15" \
  --author="John Doe"
```

## Validation

Test your schemas with Google's tools:
- [Rich Results Test](https://search.google.com/test/rich-results)
- [Schema Markup Validator](https://validator.schema.org/)

## Schema Structure

### NewsMediaOrganization
```json
{
  "@context": "https://schema.org",
  "@type": "NewsMediaOrganization",
  "name": "DFWA Social Buzz",
  "url": "https://dfwasocialbuzz.com",
  "logo": {...},
  "sameAs": [social profiles],
  "foundingDate": "2024"
}
```

### NewsArticle
```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Article Title",
  "description": "Article summary",
  "url": "https://arlington.dfwasocialbuzz.com/articles/...",
  "image": {...},
  "datePublished": "2024-01-15T10:00:00-06:00",
  "author": {"@type": "Person", "name": "Author"},
  "publisher": {"@id": "https://dfwasocialbuzz.com/#organization"}
}
```
