// Request parity test endpoint - logs exact outbound HTTP request
module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.GC_API_KEY;
  const { contactId, firstName, lastName, phone } = req.body;
  
  const url = `https://api.globalcontrol.io/api/ai/contacts/${contactId}`;
  const payload = {};
  if (firstName) payload.firstName = firstName;
  if (lastName) payload.lastName = lastName;
  if (phone) payload.phone = phone;
  
  const headers = {
    'X-API-KEY': apiKey ? `${apiKey.substring(0, 10)}...${apiKey.substring(apiKey.length-5)}` : 'MISSING',
    'Content-Type': 'application/json'
  };
  
  const bodyString = JSON.stringify(payload);
  
  // Log exact request details
  const requestLog = {
    timestamp: new Date().toISOString(),
    url: url,
    method: 'PUT',
    headers: headers,
    body: payload,
    bodyString: bodyString,
    bodyLength: bodyString.length,
    contactId: contactId
  };
  
  console.log('=== VERCEL REQUEST LOG ===');
  console.log(JSON.stringify(requestLog, null, 2));
  
  try {
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: bodyString
    });
    
    const responseText = await response.text();
    
    const responseLog = {
      status: response.status,
      statusText: response.statusText,
      responseBody: responseText.substring(0, 500)
    };
    
    console.log('=== VERCEL RESPONSE LOG ===');
    console.log(JSON.stringify(responseLog, null, 2));
    
    // Verify persistence
    const verifyRes = await fetch(url, {
      headers: { 'X-API-KEY': apiKey }
    });
    const verifyData = await verifyRes.json();
    
    const verifyLog = {
      persistedFirstName: verifyData.data?.firstName || null,
      persistedLastName: verifyData.data?.lastName || null,
      persistedPhone: verifyData.data?.phone || null
    };
    
    console.log('=== VERCEL VERIFY LOG ===');
    console.log(JSON.stringify(verifyLog, null, 2));
    
    return res.status(200).json({
      request: requestLog,
      response: responseLog,
      verify: verifyLog
    });
    
  } catch (error) {
    return res.status(500).json({
      error: error.message,
      request: requestLog
    });
  }
};
