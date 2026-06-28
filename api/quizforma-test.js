// Test endpoint for QuizForma webhook integration
// Use this to verify the webhook is working before connecting QuizForma

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  // GET request returns test form and documentation
  if (req.method === 'GET') {
    return res.status(200).json({
      message: 'QuizForma Webhook Test Endpoint',
      description: 'Use this endpoint to test QuizForma webhook integration before going live',
      liveEndpoint: '/api/quizforma-webhook',
      testEndpoint: '/api/quizforma-test',
      documentation: {
        acceptedFormats: [
          'QuizForma native webhook',
          'QSM (Quiz and Survey Master) webhook',
          'Zapier/Make webhook POST',
          'Generic JSON POST'
        ],
        requiredFields: ['email'],
        optionalFields: [
          'name / firstName / lastName',
          'quiz_id / quizId',
          'quiz_title / quizTitle',
          'submitted_at / submittedAt',
          'answers / responses / question_answers',
          'score / result'
        ]
      },
      examplePayload: {
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        quiz_id: 'arlington-subscribe-v1',
        quiz_title: 'Arlington Pulse Subscribe Quiz',
        submitted_at: '2026-06-28T23:00:00Z',
        answers: {
          preferred_city: 'Arlington',
          audience_type: 'Reader',
          content_preference: 'Local News, Events'
        },
        score: 85
      },
      testInstructions: [
        'Send a POST request to this endpoint with your test payload',
        'Verify the response shows success: true',
        'Check Global Control dashboard for the test contact',
        'Once verified, update QuizForma to use the live endpoint: /api/quizforma-webhook'
      ]
    });
  }

  // POST request simulates a QuizForma webhook
  if (req.method === 'POST') {
    try {
      const payload = req.body;
      console.log('Test webhook received:', JSON.stringify(payload, null, 2));

      // Validate minimum required field
      if (!payload.email && !payload.user_email) {
        return res.status(400).json({
          success: false,
          error: 'Missing required field: email',
          message: 'QuizForma webhook must include an email address'
        });
      }

      // Simulate processing (don't actually call Global Control in test mode)
      const normalizedData = {
        email: payload.email || payload.user_email,
        name: payload.name || payload.user_name,
        quizId: payload.quiz_id || payload.quizId || 'test-quiz',
        quizTitle: payload.quiz_title || payload.quizTitle || 'Test Quiz',
        answers: payload.answers || payload.responses || payload.question_answers || {},
        score: payload.score || payload.total_score || null
      };

      return res.status(200).json({
        success: true,
        mode: 'TEST',
        message: 'Test payload received and validated',
        receivedPayload: payload,
        normalizedData: normalizedData,
        nextSteps: [
          'Payload structure looks good!',
          'To go live, POST to /api/quizforma-webhook instead',
          'Make sure GC_API_KEY is configured in environment variables'
        ]
      });

    } catch (error) {
      return res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
