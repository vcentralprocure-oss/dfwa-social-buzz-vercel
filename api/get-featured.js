// Arlington Pulse Get Featured API Endpoint
// Creates advertiser lead contact in Global Control

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { firstName, lastName, email, phone, businessName, city } = req.body;

    if (!email) {
      return res.status(400).json({ success: false, message: 'Email is required' });
    }

    const GC_API_KEY = process.env.GC_API_KEY;
    
    if (!GC_API_KEY) {
      return res.status(500).json({
        success: false,
        message: 'Server configuration error',
        error: 'GC_API_KEY not configured'
      });
    }

    // Step 1: Create contact in Global Control
    const contactData = {
      email: email,
      firstName: firstName || '',
      lastName: lastName || '',
      phone: phone || '',
      customFields: {
        business_name: businessName || '',
        city: city || 'Arlington',
        lead_type: 'advertiser',
        source_form_id: 'arlington_get_featured',
        entry_point: 'arlington_pulse_homepage',
        submission_date: new Date().toISOString(),
        interest: 'advertising'
      }
    };

    console.log('Creating advertiser lead in Global Control:', JSON.stringify(contactData, null, 2));

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
      console.error('Global Control API error (create contact):', errorText);
      return res.status(500).json({
        success: false,
        message: 'Failed to create contact',
        error: errorText,
        retryable: true
      });
    }

    const gcData = await gcResponse.json();
    const contactId = gcData._id || gcData.id;
    
    console.log('Advertiser lead created:', contactId);

    // Step 2: Fire tags on the contact
    const tagsToApply = ['arlington-advertiser', 'arlington-get-featured'];

    // Fire each tag
    const tagResults = [];
    for (const tagName of tagsToApply) {
      try {
        // First, get or create the tag
        const tagResponse = await fetch('https://api.globalcontrol.io/api/ai/tags', {
          method: 'GET',
          headers: {
            'X-API-KEY': GC_API_KEY
          }
        });

        let tagId = null;
        if (tagResponse.ok) {
          const tags = await tagResponse.json();
          const existingTag = tags.find(t => t.name === tagName);
          if (existingTag) {
            tagId = existingTag._id;
          }
        }

        // If tag doesn't exist, create it
        if (!tagId) {
          const createTagResponse = await fetch('https://api.globalcontrol.io/api/ai/tags', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify({ name: tagName })
          });

          if (createTagResponse.ok) {
            const newTag = await createTagResponse.json();
            tagId = newTag._id;
          }
        }

        // Fire the tag on the contact
        if (tagId) {
          const fireTagResponse = await fetch(`https://api.globalcontrol.io/api/ai/tags/fire-tag/${tagId}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify({ contactId: contactId })
          });

          tagResults.push({
            tag: tagName,
            success: fireTagResponse.ok,
            status: fireTagResponse.status
          });
        }
      } catch (tagError) {
        console.error(`Error firing tag ${tagName}:`, tagError);
        tagResults.push({
          tag: tagName,
          success: false,
          error: tagError.message
        });
      }
    }

    console.log('Tag results:', tagResults);

    return res.status(200).json({
      success: true,
      message: 'Successfully submitted',
      contactId: contactId,
      email: email,
      businessName: businessName,
      tagsApplied: tagsToApply,
      tagResults: tagResults
    });

  } catch (error) {
    console.error('Get Featured error:', error);
    return res.status(500).json({
      success: false,
      message: 'Submission failed',
      error: error.message,
      retryable: true
    });
  }
}
