// Contact Form API Endpoint
// Creates/updates contacts in Global Control with CONTACT FORM tags

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { name, email, subject, message, source_host, source_page } = req.body;

    if (!name || !email || !message) {
      return res.status(400).json({ success: false, message: 'Missing required fields' });
    }

    const GC_API_KEY = process.env.GC_API_KEY;
    let contactId = null;
    let existingTags = [];

    // Search for existing contact
    if (GC_API_KEY) {
      try {
        const searchResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/search?email=${encodeURIComponent(email)}`, {
          headers: { 'X-API-KEY': GC_API_KEY, 'Content-Type': 'application/json' }
        });
        if (searchResponse.ok) {
          const searchData = await searchResponse.json();
          if (searchData.contacts?.length > 0) {
            contactId = searchData.contacts[0].id;
            existingTags = searchData.contacts[0].tags || [];
          }
        }
      } catch (e) { console.error('Search error:', e); }
    }

    // Build tags - CONTACT FORM specific
    const newTags = ['CONTACT FORM', 'lead:general', 'source:website', 'source:contact-page'];
    if (subject?.toLowerCase().includes('business')) newTags.push('intent:business-inquiry');
    if (subject?.toLowerCase().includes('partnership')) newTags.push('intent:partnership');
    
    const mergedTags = [...new Set([...existingTags, ...newTags])];

    const contactData = {
      email,
      firstName: name.split(' ')[0],
      lastName: name.split(' ').slice(1).join(' '),
      customFields: {
        contact_form_subject: subject || '',
        contact_form_message: message,
        contact_form_source: source_host || 'unknown',
        contact_form_page: source_page || '',
        contact_form_date: new Date().toISOString(),
        form_type: 'contact_form'
      },
      tags: mergedTags
    };

    if (GC_API_KEY) {
      try {
        const url = contactId 
          ? `https://api.globalcontrol.io/api/ai/contacts/${contactId}`
          : 'https://api.globalcontrol.io/api/ai/contacts';
        
        const gcResponse = await fetch(url, {
          method: contactId ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json', 'X-API-KEY': GC_API_KEY },
          body: JSON.stringify(contactData)
        });

        const gcData = await gcResponse.json();
        
        // Check for GC error in response body (GC returns HTTP 200 with error body)
        if (gcData.type === 'error' || gcData.error || !gcResponse.ok) {
          const errorMessage = gcData.error?.message || gcData.message || 'Unknown GC error';
          console.error('GC API error:', errorMessage, gcData);
          return res.status(500).json({
            success: false,
            message: 'Failed to send message. Please try again.',
            error: 'Global Control sync failed',
            gc_error: errorMessage
          });
        }
      } catch (e) { console.error('GC error:', e); }
    }

    // Only return success if GC_API_KEY is configured and request was attempted
    if (!GC_API_KEY) {
      return res.status(500).json({
        success: false,
        message: 'Configuration error. Please try again later.'
      });
    }

    // Final verification: gcData must exist and not be an error
    if (!gcData || gcData.type === 'error' || gcData.error) {
      return res.status(500).json({
        success: false,
        message: 'Failed to send message. Please try again.',
        error: 'Global Control sync failed'
      });
    }

    return res.status(200).json({ success: true, message: 'Message sent' });

  } catch (error) {
    console.error('Contact form error:', error);
    return res.status(500).json({ success: false, message: 'Server error' });
  }
}
