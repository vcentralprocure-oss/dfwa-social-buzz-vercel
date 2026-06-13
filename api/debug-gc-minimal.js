// DEBUG ENDPOINT: Minimal payload test for GC
// Tests with only core fields to isolate payload structure issues

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const results = {
    timestamp: new Date().toISOString(),
    tests: []
  };

  try {
    const { email, first_name } = req.body;
    const GC_API_KEY = process.env.GC_API_KEY;

    if (!GC_API_KEY) {
      return res.status(500).json({ error: 'GC_API_KEY not configured' });
    }

    // TEST 1: Minimal payload (core fields only)
    const minimalPayload = {
      email: email,
      firstName: first_name || 'Test',
      lastName: 'User'
    };

    results.tests.push({
      test_name: 'minimal_payload',
      payload: minimalPayload
    });

    const minimalResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': GC_API_KEY
      },
      body: JSON.stringify(minimalPayload)
    });

    const minimalData = await minimalResponse.json();

    results.tests[0].response = {
      status: minimalResponse.status,
      statusText: minimalResponse.statusText,
      ok: minimalResponse.ok,
      data: minimalData
    };

    // TEST 2: With customFields only (no tags)
    const customFieldsPayload = {
      email: email,
      firstName: first_name || 'Test',
      lastName: 'User',
      customFields: {
        test_field: 'test_value'
      }
    };

    results.tests.push({
      test_name: 'with_customFields_only',
      payload: customFieldsPayload
    });

    const cfResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': GC_API_KEY
      },
      body: JSON.stringify(customFieldsPayload)
    });

    const cfData = await cfResponse.json();

    results.tests[1].response = {
      status: cfResponse.status,
      statusText: cfResponse.statusText,
      ok: cfResponse.ok,
      data: cfData
    };

    // TEST 3: With tags only (no customFields)
    const tagsPayload = {
      email: email + '.tags', // Different email to avoid conflict
      firstName: first_name || 'Test',
      lastName: 'User',
      tags: ['TEST_TAG']
    };

    results.tests.push({
      test_name: 'with_tags_only',
      payload: { ...tagsPayload, email: tagsPayload.email }
    });

    const tagsResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': GC_API_KEY
      },
      body: JSON.stringify(tagsPayload)
    });

    const tagsData = await tagsResponse.json();

    results.tests[2].response = {
      status: tagsResponse.status,
      statusText: tagsResponse.statusText,
      ok: tagsResponse.ok,
      data: tagsData
    };

    // Determine which payload structure works
    const minimalSuccess = minimalData && !minimalData.error && minimalData.type !== 'error';
    const cfSuccess = cfData && !cfData.error && cfData.type !== 'error';
    const tagsSuccess = tagsData && !tagsData.error && tagsData.type !== 'error';

    results.conclusion = {
      minimal_payload_works: minimalSuccess,
      customFields_works: cfSuccess,
      tags_works: tagsSuccess,
      recommendation: minimalSuccess 
        ? 'Use minimal payload (email, firstName, lastName only)'
        : cfSuccess 
          ? 'Use payload with customFields but no tags'
          : tagsSuccess
            ? 'Use payload with tags but no customFields'
            : 'All payload structures failed - check endpoint or API key permissions'
    };

    return res.status(200).json(results);

  } catch (error) {
    return res.status(500).json({
      error: error.message,
      stack: error.stack,
      results
    });
  }
}
