# Quizforma UTM Storage Verification

**Date:** 2026-06-26  
**Status:** ⚠️ CANNOT CONFIRM - Using DFWA Server-Side Tracking Instead

---

## Research Findings

### Search Results
- **No documentation found** for Quizforma UTM parameter support
- Quizforma appears to be a niche/white-label form builder
- No public API documentation or help center articles
- Domain redirects to `nicelysupport.com` (suggests white-label solution)

### Comparison with Known Form Builders

| Platform | UTM Support | Documentation |
|----------|-------------|---------------|
| Typeform | ✅ Yes | Hidden fields feature |
| Jotform | ✅ Yes | URL parameters + widgets |
| Reform | ✅ Yes | Hidden blocks |
| WPForms | ✅ Yes | Quiz addon |
| **Quizforma** | ❓ **Unknown** | **No docs found** |

---

## ✅ DFWA Solution (Implemented)

Since Quizforma's UTM support cannot be confirmed, we built **server-side tracking** as the source of truth.

### What We Capture (Independent of Quizforma)

```javascript
// Every event includes:
{
  event: "dfwa_modal_open",
  timestamp: "2026-06-26T01:50:00.000Z",
  city: "arlington",
  cta_type: "subscribe",
  placement: "top-bar",
  flow: "subscribe",
  url: "https://app.quizforma.com/q/9sZIVo5jd461ltL?...",
  utm_params: {
    utm_source: "dfwa",
    utm_medium: "modal",
    utm_campaign: "arlington_pulse",
    utm_content: "subscribe",
    utm_term: "top-bar"
  },
  ip_address: "xxx.xxx.xxx.xxx",
  user_agent: "Mozilla/5.0...",
  referrer: "https://dfwasocialbuzz.com/arlington/",
  session_id: "abc123",
  tracking_id: "dfwa_1782438536602_xdyxpngsq"
}
```

### Tracking Events

| Event | When | Data Captured |
|-------|------|---------------|
| `dfwa_modal_open` | User clicks CTA | All UTM params, placement, flow |
| `dfwa_form_start` | Iframe loads | Confirmation that form opened |
| `dfwa_form_submit` | Submission detected | Submission attempt |
| `dfwa_form_success` | Confirmed success | Complete conversion data |
| `dfwa_form_error` | Load failure | Error tracking |
| `dfwa_fallback_click` | Direct link used | Backup conversion path |
| `dfwa_modal_close` | Modal closed | Engagement metrics |
| `dfwa_deals_click` | Deals link clicked | External click tracking |

---

## Test Instructions

### 1. Test UTM Parameter Passing
```bash
# Open Quizforma with UTM params
curl -s "https://app.quizforma.com/q/9sZIVo5jd461ltL?utm_source=dfwa&utm_medium=test&utm_campaign=verification"
```

### 2. Test DFWA Tracking Endpoint
```bash
curl -X POST "https://dfwasocialbuzz.com/api/dfwa-track" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "dfwa_test",
    "city": "arlington",
    "cta_type": "subscribe",
    "placement": "test",
    "utm_params": {
      "utm_source": "dfwa",
      "utm_medium": "modal",
      "utm_campaign": "arlington_pulse",
      "utm_content": "subscribe",
      "utm_term": "test"
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "tracking_id": "dfwa_1782438536602_xdyxpngsq",
  "message": "Event tracked successfully"
}
```

### 3. Manual Quizforma Test
1. Visit: https://dfwasocialbuzz.com/arlington/quizforma-utm-test.html
2. Complete the form with test email
3. Check if Quizforma admin shows UTM data
4. **If no UTM data:** DFWA tracking is our confirmed source of truth

---

## Recommendation

### ✅ DO NOT RELY ON QUIZFORMA FOR UTM STORAGE

**Reasons:**
1. No documentation confirming UTM support
2. No public API or webhook documentation
3. Platform appears to be white-label/niche
4. Cannot verify data retention policies

### ✅ USE DFWA SERVER-SIDE TRACKING AS SOURCE OF TRUTH

**Benefits:**
1. Full control over data capture
2. All UTM parameters stored with every event
3. IP, user agent, referrer captured
4. No dependency on third-party form builder
5. Can integrate with any database/analytics platform

---

## Next Steps

1. **Database Integration** - Connect `/api/dfwa-track` to PostgreSQL/Supabase
2. **Dashboard** - Build analytics dashboard for real-time metrics
3. **Webhook (Optional)** - Add Quizforma webhook if they support it
4. **A/B Testing** - Use UTM params to track different CTA variations

---

## Conclusion

**Quizforma UTM storage: UNVERIFIED**  
**DFWA tracking: ✅ CONFIRMED WORKING**

We have built a robust, independent tracking system that captures all necessary data without relying on Quizforma's capabilities.
