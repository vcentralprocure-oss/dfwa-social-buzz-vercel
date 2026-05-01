// Minimal working version - inline everything
module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.GC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'API key not configured' });
  }

  const { email, contact_name, phone, city_interest, source_form_id } = req.body;
  
  if (!email) {
    return res.status(400).json({ error: 'Email is required' });
  }

  try {
    // Step 1: Create contact
    const createResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
      method: 'POST',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    const createResult = await createResponse.json();
    
    if (!createResponse.ok) {
      throw new Error(`Create failed: ${JSON.stringify(createResult)}`);
    }
    
    const contactId = createResult.data._id;

    // Step 2: IMMEDIATELY update with name/phone
    const nameParts = (contact_name || '').split(' ');
    const updatePayload = {
      firstName: nameParts[0] || '',
      lastName: nameParts.slice(1).join(' ') || '',
      phone: phone || ''
    };

    const updateResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
      method: 'PUT',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updatePayload)
    });

    const updateResult = await updateResponse.json();

    // Step 3: Apply tags
    const tags = ['subscribed-business', 'intent-business', 'prospect-lead'];
    if (city_interest && city_interest !== 'general') {
      tags.push(`interest-${city_interest}`);
    }

    for (const tagName of tags) {
      try {
        // Get tag ID
        const tagsResponse = await fetch('https://api.globalcontrol.io/api/ai/tags', {
          headers: { 'X-API-KEY': apiKey }
        });
        const tagsResult = await tagsResponse.json();
        const allTags = tagsResult.data || tagsResult;
        const tag = allTags.find(t => t.name === tagName);
        
        if (tag) {
          await fetch(`https://api.globalcontrol.io/api/ai/tags/fire-tag/${tag._id}`, {
            method: 'POST',
            headers: {
              'X-API-KEY': apiKey,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
          });
        }
      } catch (e) {
        console.log('Tag error:', e.message);
      }
    }

    return res.status(200).json({
      success: true,
      contactId: contactId,
      updateStatus: updateResponse.ok,
      updateResult: updateResult
    });

  } catch (error) {
    return res.status(500).json({
      error: error.message
    });
  }
};
