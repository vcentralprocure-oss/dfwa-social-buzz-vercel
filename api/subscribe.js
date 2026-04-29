module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, first_name, city_interest, entry_point, offer_type } = req.body;

  if (!email) {
    return res.status(400).json({ error: 'Email required' });
  }

  // For now, just store locally and return success
  // Global Control integration can be added once API is verified
  
  console.log('New subscriber:', {
    email,
    first_name,
    city_interest,
    entry_point,
    offer_type,
    timestamp: new Date().toISOString()
  });

  // Build tags for response
  const tags = [];
  if (entry_point === 'homepage') tags.push('subscribed-homepage');
  if (city_interest === 'Arlington') tags.push('subscribed-arlington');
  if (city_interest === 'Dallas') tags.push('subscribed-dallas');
  if (city_interest === 'Fort Worth') tags.push('subscribed-fort-worth');
  if (offer_type === 'newsletter') tags.push('intent-reader');

  return res.status(200).json({ 
    success: true, 
    message: 'Subscribed successfully! Welcome to DFWA Social Buzz.',
    email: email,
    tags: tags
  });
};