// Minimal test endpoint for debugging
module.exports = async function handler(req, res) {
  const apiKey = process.env.GC_API_KEY;
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { contactId, firstName, lastName, phone } = req.body;
  
  if (!contactId) {
    return res.status(400).json({ error: 'contactId required' });
  }

  const updatePayload = {};
  if (firstName) updatePayload.firstName = firstName;
  if (lastName) updatePayload.lastName = lastName;
  if (phone) updatePayload.phone = phone;

  console.log('DEBUG UPDATE:', {
    contactId,
    updatePayload,
    apiKeyPresent: !!apiKey
  });

  try {
    const updateResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
      method: 'PUT',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updatePayload)
    });

    const responseText = await updateResponse.text();
    
    console.log('DEBUG UPDATE RESPONSE:', {
      status: updateResponse.status,
      statusText: updateResponse.statusText,
      body: responseText
    });

    return res.status(200).json({
      success: updateResponse.ok,
      status: updateResponse.status,
      response: responseText
    });
  } catch (error) {
    console.log('DEBUG UPDATE ERROR:', error.message);
    return res.status(500).json({ error: error.message });
  }
};
