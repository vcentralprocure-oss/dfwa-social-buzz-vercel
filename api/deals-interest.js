// Deals Interest API Endpoint
// Handles lead capture with additive tagging for Global Control

export default async function handler(req, res) {
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

  try {
    const {
      first_name,
      email,
      cities,
      consent,
      source_host,
      source_page,
      source_path,
      intent,
      button_location,
      referrer,
      submission_timestamp
    } = req.body;

    // Validate required fields
    if (!first_name || !email || !cities || cities.length === 0 || !consent) {
      return res.status(400).json({ 
        success: false, 
        message: 'Please fill in all required fields and select at least one city.' 
      });
    }

    const GC_API_KEY = process.env.GC_API_KEY;
    let contactId = null;
    let existingTags = [];
    let isNewContact = false;

    // Step 1: Check if contact already exists
    if (GC_API_KEY) {
      try {
        const searchResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/search?email=${encodeURIComponent(email)}`, {
          method: 'GET',
          headers: {
            'X-API-KEY': GC_API_KEY,
            'Content-Type': 'application/json'
          }
        });

        if (searchResponse.ok) {
          const searchData = await searchResponse.json();
          if (searchData.contacts && searchData.contacts.length > 0) {
            contactId = searchData.contacts[0].id;
            existingTags = searchData.contacts[0].tags || [];
            console.log(`Found existing contact: ${contactId} with tags:`, existingTags);
          }
        }
      } catch (searchError) {
        console.error('Error searching for contact:', searchError);
      }
    }

    // Step 2: Build new tags (additive approach)
    const newTags = ['DEALS INTEREST'];
    
    // Add city-specific tags
    cities.forEach(city => {
      const cityTag = `DEALS - ${city.toUpperCase().replace('-', ' ')}`;
      if (!newTags.includes(cityTag)) {
        newTags.push(cityTag);
      }
    });

    // Step 3: Merge with existing tags (additive, not replacement)
    const mergedTags = [...new Set([...existingTags, ...newTags])];
    
    console.log('Tag merge:', {
      existing: existingTags,
      new: newTags,
      merged: mergedTags
    });

    // Step 4: Create or update contact
    if (GC_API_KEY) {
      const contactData = {
        email: email,
        firstName: first_name,
        lastName: '',
        customFields: {
          // Source attribution
          source_host: source_host || 'unknown',
          source_page: source_page || '',
          source_path: source_path || '/',
          intent: intent || 'local_deals',
          button_location: button_location || 'local-deals-cta',
          referrer: referrer || '',
          submission_timestamp: submission_timestamp || new Date().toISOString(),
          // Deals specific
          deals_interest_cities: cities.join(', '),
          consent: consent,
          form_type: 'deals_interest'
        },
        tags: mergedTags
      };

      try {
        let gcResponse;
        
        if (contactId) {
          // UPDATE existing contact
          console.log(`Updating existing contact: ${contactId}`);
          gcResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify(contactData)
          });
          isNewContact = false;
        } else {
          // CREATE new contact
          console.log('Creating new contact');
          gcResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify(contactData)
          });
          isNewContact = true;
        }

        const gcData = await gcResponse.json();
        
        // Check for GC error in response body (GC returns HTTP 200 with error body)
        if (gcData.type === 'error' || gcData.error || !gcResponse.ok) {
          const errorMessage = gcData.error?.message || gcData.message || 'Unknown GC error';
          console.error('Global Control API error:', errorMessage, gcData);
          return res.status(500).json({
            success: false,
            message: 'Failed to save subscription. Please try again.',
            error: 'Global Control sync failed',
            gc_error: errorMessage
          });
        }
        
        console.log(`Successfully ${isNewContact ? 'created' : 'updated'} contact in Global Control:`, gcData.id || contactId);
      } catch (gcError) {
        console.error('Global Control integration error:', gcError);
      }
    }

    // Log submission
    const submissionLog = {
      first_name,
      email,
      cities,
      isNewContact,
      mergedTags,
      source_host: source_host || 'unknown',
      timestamp: submission_timestamp || new Date().toISOString()
    };
    
    console.log('Deals interest submission:', submissionLog);

    // Only return success if we actually created/updated in GC
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
        message: 'Failed to save subscription. Please try again.',
        error: 'Global Control sync failed'
      });
    }

    return res.status(200).json({
      success: true,
      message: 'Successfully subscribed to local deals',
      isNewContact,
      cities: cities
    });

  } catch (error) {
    console.error('Deals form error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error. Please try again.'
    });
  }
}
