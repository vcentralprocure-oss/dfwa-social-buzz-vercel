export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, first_name, city_interest, entry_point, offer_type, source_form_id, source_url } = req.body;

  if (!email) {
    return res.status(400).json({ error: 'Email required' });
  }

  // Build tags
  const tags = [];
  
  // Source tags
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
    // Global Control API
    const GC_API_KEY = process.env.GC_API_KEY;
    
    if (!GC_API_KEY) {
      console.error('GC_API_KEY not set');
      return res.status(500).json({ error: 'Server configuration error' });
    }

    const gcResponse = await fetch('https://api.globalcontrol.io/v1/subscribers', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GC_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        first_name: first_name || '',
        tags,
        custom_fields: {
          city_interest: city_interest || 'general',
          entry_point: entry_point || 'unknown',
          offer_type: offer_type || 'newsletter',
          source_form_id: source_form_id || '',
          source_url: source_url || '',
          subscribed_at: new Date().toISOString()
        }
      })
    });

    if (!gcResponse.ok) {
      const errorText = await gcResponse.text();
      console.error('Global Control error:', errorText);
      throw new Error('Global Control API error');
    }

    const gcData = await gcResponse.json();

    return res.status(200).json({ 
      success: true, 
      subscriber_id: gcData.id,
      tags,
      message: 'Subscribed successfully'
    });

  } catch (error) {
    console.error('Subscribe error:', error);
    return res.status(500).json({ error: 'Subscription failed. Please try again.' });
  }
}