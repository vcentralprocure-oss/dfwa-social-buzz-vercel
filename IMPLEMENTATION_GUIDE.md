# DFWA Subscriber Intake - Implementation Files

## API Route for Vercel

Create `/api/subscribe.js` in your Vercel project:

```javascript
// /api/subscribe.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, first_name, city_interest, entry_point, offer_type, source_form_id } = req.body;

  // Validate
  if (!email) {
    return res.status(400).json({ error: 'Email required' });
  }

  // Determine tags
  const tags = [];
  if (entry_point === 'homepage') tags.push('subscribed-homepage');
  if (city_interest === 'Arlington') tags.push('subscribed-arlington');
  if (city_interest === 'Dallas') tags.push('subscribed-dallas');
  if (city_interest === 'Fort Worth') tags.push('subscribed-fort-worth');
  if (offer_type === 'deals') tags.push('subscribed-deals');
  if (offer_type === 'business') tags.push('subscribed-business');
  
  // Intent tags
  if (offer_type === 'newsletter') tags.push('intent-reader');
  if (offer_type === 'deals') tags.push('intent-deals');
  if (offer_type === 'business') tags.push('intent-business');

  try {
    // Send to Global Control
    const gcResponse = await fetch('https://api.globalcontrol.com/v1/subscribers', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GC_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        first_name,
        tags,
        custom_fields: {
          city_interest,
          entry_point,
          offer_type,
          source_form_id
        }
      })
    });

    if (!gcResponse.ok) {
      throw new Error('Global Control API error');
    }

    return res.status(200).json({ success: true, tags });
  } catch (error) {
    console.error('Subscribe error:', error);
    return res.status(500).json({ error: 'Subscription failed' });
  }
}
```

## Environment Variable

Add to Vercel:
```
GC_API_KEY=9dbd9c86b7ed48ab3b19d54c1ef5d761d2685e5d8ce63728fc475f47b0b44f09
```

## Form HTML (Example)

```html
<form action="/api/subscribe" method="POST">
  <input type="email" name="email" placeholder="Your email" required>
  <input type="hidden" name="city_interest" value="Arlington">
  <input type="hidden" name="entry_point" value="city_page">
  <input type="hidden" name="offer_type" value="newsletter">
  <button type="submit">Subscribe</button>
</form>
```

## Global Control Setup

1. Create tags: subscribed-homepage, subscribed-arlington, etc.
2. Create custom fields: city_interest, entry_point, offer_type
3. Create workflows for each nurture sequence
4. Connect SMTP for email delivery