# DFWA Tracking System Implementation

## Commit: `5716645`

---

## ✅ Features Implemented

### 1. Separate Flows for Each CTA Type

| Flow | Modal ID | Purpose | Trigger Elements |
|------|----------|---------|------------------|
| **Subscribe** | `subscribe-quiz-modal` | Newsletter signup | `[data-cta="subscribe"]` |
| **Featured** | `featured-quiz-modal` | Business feature requests | `[data-cta="featured"]` |
| **Deals** | External link | Local deals page | `[data-cta="deals"]` (tracks click only) |

### 2. UTM Parameters (Auto-Generated)

Every Quizforma URL includes:

```
utm_source=dfwa
utm_medium=modal
utm_campaign={city}_pulse
utm_content={cta_type}
utm_term={placement}
```

**Example URL:**
```
https://app.quizforma.com/q/9sZIVo5jd461ltL?
  utm_source=dfwa&
  utm_medium=modal&
  utm_campaign=arlington_pulse&
  utm_content=subscribe&
  utm_term=top-bar
```

### 3. Tracked Events

| Event Name | When Fired | Properties |
|------------|------------|------------|
| `dfwa_modal_open` | Modal opens | cta_type, placement, flow, url |
| `dfwa_form_start` | Iframe loads | cta_type, placement, flow |
| `dfwa_form_submit` | Form submitted | flow, cta_type |
| `dfwa_form_success` | Submission confirmed | flow, cta_type, submission_id |
| `dfwa_form_error` | Iframe fails to load | cta_type, placement, flow |
| `dfwa_modal_close` | Modal closed | flow, started, submitted |
| `dfwa_fallback_click` | User clicks fallback link | cta_type, placement, flow |
| `dfwa_deals_click` | Deals link clicked | cta_type, placement, href |

### 4. Placement Tracking

CTA buttons use `data-placement` attributes:
- `top-bar` - Top action bar
- `footer` - Footer links
- `business-cta` - Business CTA section
- `sponsor-card` - Sponsor card (if applicable)

---

## 📊 Analytics Integration

### 1. Server-Side Tracking (Primary)
**Endpoint:** `POST /api/dfwa-track`

All events are captured server-side with:
- IP address
- User agent
- UTM parameters
- Session data
- Referrer

### 2. Google Analytics (gtag)
All events are sent to GA with:
- `event_category: 'dfwa_cta'`
- `event_label: {cta_type}`
- Custom dimensions: city, placement, flow

### 3. Console Debugging
Enable debug mode in browser console:
```javascript
DFWA.trackEvent('test_event', { test: true });
```

View current state:
```javascript
console.log(DFWA.modalState);
```

---

## 🧪 Quizforma UTM Verification

### Test Page
**URL:** https://dfwasocialbuzz.com/arlington/quizforma-utm-test.html

This page allows you to:
1. Open Quizforma with full UTM parameters
2. Load in iframe for testing
3. Verify UTM data appears in submissions

### Expected Behavior
✅ Quizforma should accept and store UTM parameters  
✅ UTM data appears in submission exports  
⚠️ If UTM params are stripped, implement server-side tracking

### Verification Steps
1. Visit the test page
2. Complete the form with test data
3. Check Quizforma admin panel → Submissions
4. Export to CSV and verify UTM columns exist

---

## 🔧 Technical Implementation

### File Structure
```
arlington/
├── index.html              # Main page with tracking system
└── quizforma-utm-test.html # UTM verification tool
```

### Key Functions

```javascript
// Build URL with UTM params
DFWA.buildQuizformaURL(ctaType, placement, extraParams);

// Track custom events
DFWA.trackEvent(eventName, properties);

// Access modal state
DFWA.modalState.subscribe.started  // boolean
DFWA.modalState.featured.submitted // boolean
```

### PostMessage Support
The system listens for messages from Quizforma (if supported):
- `quizforma_step_complete` - Track form progress
- `quizforma_submit` - Form submitted
- `quizforma_success` - Submission confirmed

---

## 🚀 Deployment Status

**Live URL:** https://dfwasocialbuzz.com/arlington/  
**Commit:** `5716645`  
**Branch:** `oc/arlington-gc-forms-20260622`

---

## ✅ Source of Truth: DFWA Server-Side Tracking

**We are NOT relying on Quizforma to store UTM data.**

Instead, we capture everything server-side via `/api/dfwa-track`:

| Data Point | Captured | Source |
|------------|----------|--------|
| UTM Source | ✅ | URL params |
| UTM Medium | ✅ | URL params |
| UTM Campaign | ✅ | URL params |
| UTM Content | ✅ | URL params |
| UTM Term | ✅ | URL params |
| IP Address | ✅ | Request headers |
| User Agent | ✅ | Request headers |
| Referrer | ✅ | Request headers |
| Timestamp | ✅ | Server clock |
| Session ID | ✅ | Client-generated |

### Test the Tracking
```bash
curl -X POST "https://dfwasocialbuzz.com/api/dfwa-track" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "dfwa_modal_open",
    "city": "arlington",
    "cta_type": "subscribe",
    "placement": "top-bar",
    "flow": "subscribe",
    "utm_params": {
      "utm_source": "dfwa",
      "utm_medium": "modal",
      "utm_campaign": "arlington_pulse",
      "utm_content": "subscribe",
      "utm_term": "top-bar"
    }
  }'
```

## Next Steps

1. **Database Integration**
   - Connect `dfwa-track.js` to Supabase/PostgreSQL
   - Store all tracking records

2. **Dashboard**
   - Build admin dashboard at `/admin/dfwa-analytics`
   - Show real-time conversion rates

3. **Expand to Other Cities**
   - Copy system to Dallas/Fort Worth pages
   - Update `CONFIG.city` value

4. **Webhook Integration**
   - Optional: Receive Quizforma submission webhooks
   - Match with tracking data for complete funnel
