// Debug endpoint to trace exactly what happens
module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.GC_API_KEY;
  const { email, contact_name, phone } = req.body;
  
  const evidence = {
    trace_id: `debug_${Date.now()}`,
    timestamp: new Date().toISOString(),
    input: {
      email,
      contact_name,
      phone
    }
  };

  // Step 1: Parse name
  const nameParts = (contact_name || '').split(' ');
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';
  
  evidence.parsed = {
    nameParts,
    firstName,
    lastName,
    phone
  };
  
  // Step 2: Build condition
  const condition = !!(firstName || lastName || phone);
  evidence.condition = {
    firstName_truthy: !!firstName,
    lastName_truthy: !!lastName,
    phone_truthy: !!phone,
    condition_result: condition
  };
  
  // Step 3: Create contact
  try {
    const createRes = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
      method: 'POST',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    const createData = await createRes.json();
    evidence.create = {
      status: createRes.status,
      contactId: createData.data?._id || null
    };
    
    const contactId = createData.data?._id;
    
    // Step 4: Attempt update
    if (contactId && condition) {
      const updatePayload = {};
      if (firstName) updatePayload.firstName = firstName;
      if (lastName) updatePayload.lastName = lastName;
      if (phone) updatePayload.phone = phone;
      
      evidence.update = {
        attempted: true,
        url: `https://api.globalcontrol.io/api/ai/contacts/${contactId}`,
        payload: updatePayload
      };
      
      try {
        const updateRes = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
          method: 'PUT',
          headers: {
            'X-API-KEY': apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updatePayload)
        });
        
        const updateData = await updateRes.json();
        evidence.update.result = {
          status: updateRes.status,
          statusText: updateRes.statusText,
          response: updateData
        };
      } catch (updateErr) {
        evidence.update.error = updateErr.message;
      }
    } else {
      evidence.update = {
        attempted: false,
        reason: contactId ? 'condition_false' : 'no_contact_id'
      };
    }
    
    // Step 5: Verify final state
    const verifyRes = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
      headers: { 'X-API-KEY': apiKey }
    });
    const verifyData = await verifyRes.json();
    
    evidence.final_state = {
      firstName: verifyData.data?.firstName || '',
      lastName: verifyData.data?.lastName || '',
      phone: verifyData.data?.phone || ''
    };
    
  } catch (err) {
    evidence.error = err.message;
  }
  
  return res.status(200).json(evidence);
};
