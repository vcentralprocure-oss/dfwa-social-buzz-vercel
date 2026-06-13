// DEBUG ENDPOINT: Test alternate GC endpoint paths
// Isolates whether the endpoint URL is the issue

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

    const minimalPayload = {
      email: email,
      firstName: first_name || 'Test',
      lastName: 'User'
    };

    // TEST 1: Current endpoint (api/ai/contacts)
    const endpoints = [
      {
        name: 'current_api_ai',
        url: 'https://api.globalcontrol.io/api/ai/contacts'
      },
      {
        name: 'api_v1',
        url: 'https://api.globalcontrol.io/api/v1/contacts'
      },
      {
        name: 'api_v2',
        url: 'https://api.globalcontrol.io/api/v2/contacts'
      },
      {
        name: 'root_contacts',
        url: 'https://api.globalcontrol.io/contacts'
      },
      {
        name: 'globalcontrol_io',
        url: 'https://globalcontrol.io/api/ai/contacts'
      }
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint.url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': GC_API_KEY
          },
          body: JSON.stringify(minimalPayload)
        });

        let data = null;
        let error = null;

        try {
          data = await response.json();
        } catch (e) {
          error = await response.text();
        }

        results.tests.push({
          endpoint: endpoint.name,
          url: endpoint.url,
          status: response.status,
          statusText: response.statusText,
          ok: response.ok,
          data: data,
          error: error,
          appears_successful: data && !data.error && data.type !== 'error'
        });
      } catch (fetchError) {
        results.tests.push({
          endpoint: endpoint.name,
          url: endpoint.url,
          fetch_error: fetchError.message
        });
      }
    }

    // Find any successful endpoint
    const successful = results.tests.find(t => t.appears_successful);
    
    results.conclusion = {
      any_endpoint_worked: !!successful,
      working_endpoint: successful ? successful.url : null,
      recommendation: successful 
        ? `Use endpoint: ${successful.url}`
        : 'All endpoints failed - likely API key permissions or workspace issue'
    };

    return res.status(200).json(results);

  } catch (error) {
    return res.status(500).json({
      error: error.message,
      results
    });
  }
}
