// DEBUG ENDPOINT: Full GC request/response trace
// Use this to capture exactly what happens with GC

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const trace = {
    timestamp: new Date().toISOString(),
    steps: [],
    gc_api_key_present: false,
    gc_api_key_length: 0
  };

  try {
    const { email, first_name } = req.body;
    
    trace.steps.push({ step: 'start', email, first_name });

    const GC_API_KEY = process.env.GC_API_KEY;
    trace.gc_api_key_present = !!GC_API_KEY;
    trace.gc_api_key_length = GC_API_KEY ? GC_API_KEY.length : 0;

    if (!GC_API_KEY) {
      trace.steps.push({ step: 'error', message: 'GC_API_KEY not found in environment' });
      return res.status(500).json({ trace, error: 'GC_API_KEY not configured' });
    }

    // Step 1: Search for existing contact
    const searchUrl = `https://api.globalcontrol.io/api/ai/contacts/search?email=${encodeURIComponent(email)}`;
    trace.steps.push({ step: 'search_start', url: searchUrl });

    const searchResponse = await fetch(searchUrl, {
      method: 'GET',
      headers: {
        'X-API-KEY': GC_API_KEY,
        'Content-Type': 'application/json'
      }
    });

    const searchStatus = searchResponse.status;
    const searchStatusText = searchResponse.statusText;
    let searchData = null;
    let searchError = null;

    try {
      searchData = await searchResponse.json();
    } catch (e) {
      searchError = await searchResponse.text();
    }

    trace.steps.push({
      step: 'search_complete',
      status: searchStatus,
      statusText: searchStatusText,
      data: searchData,
      error: searchError
    });

    const contactExists = searchData && searchData.contacts && searchData.contacts.length > 0;
    const contactId = contactExists ? searchData.contacts[0].id : null;

    // Step 2: Create or Update
    const contactData = {
      email: email,
      firstName: first_name || 'Test',
      lastName: 'User',
      customFields: {
        debug_trace: true,
        trace_timestamp: trace.timestamp
      },
      tags: ['DEBUG_TRACE', 'GC_VERIFICATION_TEST']
    };

    const createUrl = contactId 
      ? `https://api.globalcontrol.io/api/ai/contacts/${contactId}`
      : 'https://api.globalcontrol.io/api/ai/contacts';
    
    const createMethod = contactId ? 'PUT' : 'POST';

    trace.steps.push({
      step: 'create_start',
      method: createMethod,
      url: createUrl,
      contactId: contactId,
      payload: contactData
    });

    const createResponse = await fetch(createUrl, {
      method: createMethod,
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': GC_API_KEY
      },
      body: JSON.stringify(contactData)
    });

    const createStatus = createResponse.status;
    const createStatusText = createResponse.statusText;
    let createData = null;
    let createError = null;

    try {
      createData = await createResponse.json();
    } catch (e) {
      createError = await createResponse.text();
    }

    trace.steps.push({
      step: 'create_complete',
      status: createStatus,
      statusText: createStatusText,
      data: createData,
      error: createError,
      ok: createResponse.ok
    });

    // Return full trace
    return res.status(200).json({
      trace,
      gc_create_status: createStatus,
      gc_create_ok: createResponse.ok,
      gc_create_data: createData,
      gc_create_error: createError,
      contact_id_from_search: contactId,
      contact_exists_before: contactExists
    });

  } catch (error) {
    trace.steps.push({ step: 'exception', error: error.message, stack: error.stack });
    return res.status(500).json({ trace, error: error.message });
  }
}
