// Business Form API Endpoint for Vercel
// A2P/TCPA Compliant - Handles SMS consent separately

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
      // Business contact fields
      first_name,
      last_name,
      business_name,
      email,
      phone,
      website,
      city_interest,
      interests,
      message,
      
      // Consent fields
      contact_consent,
      sms_consent,
      consent_timestamp,
      consent_language_version,
      
      // Attribution fields
      city,
      intent,
      source_host,
      source_page,
      source_path,
      button_location,
      referrer,
      submission_timestamp,
      ip_address,
      user_agent,
      
      // Legacy fields
      entry_point,
      source_form_id
    } = req.body;

    // Validate required fields
    if (!first_name || !last_name || !business_name || !email || !contact_consent) {
      return res.status(400).json({ 
        success: false, 
        message: 'Missing required fields. Please fill in all required fields and agree to be contacted.' 
      });
    }

    // Get client IP if not provided
    const clientIp = ip_address || req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';
    const clientUserAgent = user_agent || req.headers['user-agent'] || 'unknown';
    const timestamp = submission_timestamp || new Date().toISOString();

    // Build submission log with full compliance data
    const submissionLog = {
      // Contact info
      first_name,
      last_name,
      business_name,
      email,
      phone: phone || '',
      website: website || '',
      city_interest: city_interest || 'unknown',
      interests: interests || [],
      message: message || '',
      
      // Consent data (A2P/TCPA compliant)
      contact_consent: contact_consent === 'on' || contact_consent === true,
      sms_consent: sms_consent === 'on' || sms_consent === true,
      consent_timestamp: consent_timestamp || timestamp,
      consent_language_version: consent_language_version || 'v1.0-tcpa-a2p',
      
      // Attribution
      city: city || city_interest || 'unknown',
      intent: intent || 'get_featured',
      source_host: source_host || 'unknown',
      source_page: source_page || '',
      source_path: source_path || '/',
      button_location: button_location || 'unknown',
      referrer: referrer || '',
      
      // Technical metadata
      submission_timestamp: timestamp,
      ip_address: clientIp,
      user_agent: clientUserAgent,
      submitted_at: new Date().toISOString()
    };

    console.log('Business form submission (A2P/TCPA compliant):', submissionLog);

    // Global Control API Integration
    const GC_API_KEY = process.env.GC_API_KEY;
    
    if (GC_API_KEY) {
      try {
        // Build tags array
        const tags = [
          'lead:business',
          'source:website',
          'source:business-form',
          'BUSINESS_FORMS_ACTIVATED',
          `city:${city || city_interest || 'unknown'}`,
          `source_host:${source_host || 'unknown'}`,
          `intent:${intent || 'get_featured'}`
        ];
        
        // Add SMS consent tag if opted in
        if (sms_consent === 'on' || sms_consent === true) {
          tags.push('sms:consented');
          tags.push('a2p:opted-in');
        } else {
          tags.push('sms:not-consented');
        }
        
        // Create contact in Global Control
        const contactData = {
          email: email,
          firstName: first_name,
          lastName: last_name,
          phone: phone || '',
          customFields: {
            // Business info
            business_name: business_name,
            city_interest: city_interest || 'unknown',
            website: website || '',
            interests: Array.isArray(interests) ? interests.join(', ') : (interests || ''),
            message: message || '',
            
            // Consent data (A2P/TCPA)
            contact_consent: contact_consent === 'on' || contact_consent === true,
            sms_consent: sms_consent === 'on' || sms_consent === true,
            consent_timestamp: consent_timestamp || timestamp,
            consent_language_version: consent_language_version || 'v1.0-tcpa-a2p',
            
            // Attribution
            attribution_city: city || city_interest || 'unknown',
            attribution_intent: intent || 'get_featured',
            attribution_source_host: source_host || 'unknown',
            attribution_source_page: source_page || '',
            attribution_source_path: source_path || '/',
            attribution_button_location: button_location || 'unknown',
            attribution_referrer: referrer || '',
            
            // Technical
            submission_timestamp: timestamp,
            ip_address: clientIp,
            user_agent: clientUserAgent,
            
            // Legacy
            entry_point: entry_point || 'business_page',
            form_type: 'business_feature',
            source_form_id: source_form_id || 'form_business'
          },
          tags: tags
        };

        const gcResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': GC_API_KEY
          },
          body: JSON.stringify(contactData)
        });

        if (!gcResponse.ok) {
          console.error('Global Control API error:', await gcResponse.text());
        } else {
          console.log('Successfully sent to Global Control');
        }
      } catch (gcError) {
        console.error('Global Control integration error:', gcError);
        // Continue even if GC fails - don't block form submission
      }
    }

    return res.status(200).json({
      success: true,
      message: 'Form submitted successfully',
      sms_consented: sms_consent === 'on' || sms_consent === true
    });

  } catch (error) {
    console.error('Business form error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error. Please try again.'
    });
  }
}
