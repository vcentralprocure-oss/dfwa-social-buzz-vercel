// Fixed Subscribe API Endpoint
// Uses same pattern as working business-form.js

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { email, city, source, first_name, last_name } = req.body;

    if (!email) {
      return res.status(400).json({ success: false, message: 'Email is required' });
    }

    const GC_API_KEY = process.env.GC_API_KEY;
    let gcSuccess = false;
    let gcError = null;

    if (GC_API_KEY) {
      try {
        // Build tags (same pattern as business form)
        const tags = [
          'lead:subscriber',
          'source:website',
          'source:subscribe-form',
          'SUBSCRIBE_FORM_ACTIVATED',
          `city:${city || 'Arlington'}`,
          'intent:newsletter',
          'interest:local-news'
        ];

        // Build contact data (same structure as business form)
        const contactData = {
          email: email,
          firstName: first_name || '',
          lastName: last_name || '',
          customFields: {
            city_interest: city || 'Arlington',
            subscriber_type: 'newsletter',
            source_form_id: 'form_subscribe',
            entry_point: source || 'website',
            subscription_date: new Date().toISOString()
          },
          tags: tags
        };

        console.log('Sending to Global Control:', JSON.stringify(contactData, null, 2));

        const gcResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': GC_API_KEY
          },
          body: JSON.stringify(contactData)
        });

        if (!gcResponse.ok) {
          const errorText = await gcResponse.text();
          console.error('Global Control API error:', errorText);
          gcError = errorText;
        } else {
          const gcData = await gcResponse.json();
          console.log('Global Control success:', gcData);
          gcSuccess = true;
        }
      } catch (error) {
        console.error('Global Control integration error:', error);
        gcError = error.message;
      }
    }

    // Only return success if GC actually succeeded
    if (gcSuccess) {
      return res.status(200).json({
        success: true,
        message: 'Successfully subscribed',
        gc_status: 'synced',
        email: email,
        city: city || 'Arlington'
      });
    } else {
      // GC failed - return honest error
      return res.status(500).json({
        success: false,
        message: 'Subscription failed. Please try again.',
        error: gcError || 'Global Control sync failed',
        retryable: true
      });
    }

  } catch (error) {
    console.error('Subscribe error:', error);
    return res.status(500).json({
      success: false,
      message: 'Subscription failed',
      error: error.message
    });
  }
}
