// QuizForma Webhook Handler
// Receives quiz submissions from QuizForma and syncs to Global Control
// Endpoint: POST /api/quizforma-webhook

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Webhook-Secret');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed', allowed: ['POST'] });
  }

  try {
    // Validate webhook secret if configured
    const webhookSecret = process.env.QUIZFORMA_WEBHOOK_SECRET;
    if (webhookSecret) {
      const providedSecret = req.headers['x-webhook-secret'];
      if (providedSecret !== webhookSecret) {
        console.error('Invalid webhook secret received');
        return res.status(401).json({ error: 'Unauthorized - Invalid webhook secret' });
      }
    }

    const GC_API_KEY = process.env.GC_API_KEY;
    if (!GC_API_KEY) {
      console.error('GC_API_KEY not configured');
      return res.status(500).json({ error: 'Server configuration error' });
    }

    // Parse the incoming QuizForma payload
    // QuizForma can send in multiple formats depending on configuration
    const payload = req.body;
    console.log('Received QuizForma webhook:', JSON.stringify(payload, null, 2));

    // Extract data from various possible QuizForma formats
    const {
      // Standard QuizForma fields
      email,
      name,
      firstName,
      lastName,
      quiz_id,
      quiz_title,
      quizId,
      quizTitle,
      submitted_at,
      submittedAt,
      answers,
      responses,
      result,
      score,
      // QSM (Quiz and Survey Master) format
      user_email,
      user_name,
      quiz_name,
      quiz_id: qsm_quiz_id,
      question_answers,
      total_score,
      total_points,
      // Generic form fields
      ...otherFields
    } = payload;

    // Normalize email
    const contactEmail = email || user_email || otherFields.email;
    if (!contactEmail) {
      return res.status(400).json({
        error: 'Email is required',
        message: 'No email found in webhook payload'
      });
    }

    // Normalize name fields
    let contactFirstName = firstName || otherFields.firstName;
    let contactLastName = lastName || otherFields.lastName;

    if (!contactFirstName && name) {
      const nameParts = name.trim().split(/\s+/);
      contactFirstName = nameParts[0];
      contactLastName = nameParts.slice(1).join(' ');
    }

    if (!contactFirstName && user_name) {
      const nameParts = user_name.trim().split(/\s+/);
      contactFirstName = nameParts[0];
      contactLastName = nameParts.slice(1).join(' ');
    }

    // Normalize quiz identifiers
    const normalizedQuizId = quiz_id || quizId || qsm_quiz_id || 'unknown-quiz';
    const normalizedQuizTitle = quiz_title || quizTitle || quiz_name || 'Quiz Submission';
    const normalizedSubmittedAt = submitted_at || submittedAt || new Date().toISOString();
    const normalizedScore = score || total_score || total_points || result?.score || null;

    // Normalize answers (handle various formats)
    let normalizedAnswers = {};
    if (answers && typeof answers === 'object') {
      normalizedAnswers = answers;
    } else if (responses && typeof responses === 'object') {
      normalizedAnswers = responses;
    } else if (question_answers && typeof question_answers === 'object') {
      normalizedAnswers = question_answers;
    } else {
      // Try to extract Q&A from otherFields
      Object.keys(otherFields).forEach(key => {
        if (key.startsWith('question_') || key.startsWith('answer_') || key.startsWith('q_')) {
          normalizedAnswers[key] = otherFields[key];
        }
      });
    }

    console.log('Normalized data:', {
      email: contactEmail,
      firstName: contactFirstName,
      lastName: contactLastName,
      quizId: normalizedQuizId,
      quizTitle: normalizedQuizTitle,
      score: normalizedScore,
      answersCount: Object.keys(normalizedAnswers).length
    });

    // Step 1: Search for existing contact by email
    let contactId = null;
    let isExistingContact = false;

    try {
      const searchResponse = await fetch(
        `https://api.globalcontrol.io/api/ai/contacts?search=${encodeURIComponent(contactEmail)}`,
        {
          method: 'GET',
          headers: {
            'X-API-KEY': GC_API_KEY
          }
        }
      );

      if (searchResponse.ok) {
        const searchResults = await searchResponse.json();
        if (Array.isArray(searchResults) && searchResults.length > 0) {
          // Find contact with matching email
          const existingContact = searchResults.find(c =>
            c.email?.toLowerCase() === contactEmail.toLowerCase()
          );
          if (existingContact) {
            contactId = existingContact._id || existingContact.id;
            isExistingContact = true;
            console.log('Found existing contact:', contactId);
          }
        }
      }
    } catch (searchError) {
      console.error('Error searching for contact:', searchError);
    }

    // Step 2: Create or update contact
    const customFields = {
      quiz_participation: 'true',
      last_quiz_id: normalizedQuizId,
      last_quiz_title: normalizedQuizTitle,
      last_quiz_date: normalizedSubmittedAt,
      quiz_source: 'QuizForma'
    };

    // Add score if available
    if (normalizedScore !== null) {
      customFields.last_quiz_score = String(normalizedScore);
    }

    // Extract specific answers for custom fields (configurable mapping)
    // These mappings can be customized based on quiz questions
    const answerMapping = {
      preferred_city: ['preferred_city', 'city', 'what_city', 'your_city', 'location'],
      audience_type: ['audience_type', 'role', 'user_type', 'i_am_a', 'reader_type'],
      content_preference: ['content_preference', 'interests', 'topics', 'what_interests_you'],
      business_name: ['business_name', 'company', 'business', 'company_name'],
      phone: ['phone', 'phone_number', 'contact_number']
    };

    // Map answers to custom fields
    Object.keys(answerMapping).forEach(fieldName => {
      const possibleKeys = answerMapping[fieldName];
      for (const key of possibleKeys) {
        if (normalizedAnswers[key]) {
          customFields[fieldName] = Array.isArray(normalizedAnswers[key])
            ? normalizedAnswers[key].join(', ')
            : String(normalizedAnswers[key]);
          break;
        }
      }
    });

    // Store all answers as JSON for reference
    customFields.quiz_answers_json = JSON.stringify(normalizedAnswers);

    let gcResponse;

    if (isExistingContact && contactId) {
      // Update existing contact
      console.log('Updating existing contact:', contactId);
      gcResponse = await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': GC_API_KEY
        },
        body: JSON.stringify({
          firstName: contactFirstName || '',
          lastName: contactLastName || '',
          customFields: customFields
        })
      });
    } else {
      // Create new contact
      console.log('Creating new contact');
      gcResponse = await fetch('https://api.globalcontrol.io/api/ai/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': GC_API_KEY
        },
        body: JSON.stringify({
          email: contactEmail,
          firstName: contactFirstName || '',
          lastName: contactLastName || '',
          customFields: customFields
        })
      });
    }

    if (!gcResponse.ok) {
      const errorText = await gcResponse.text();
      console.error('Global Control API error:', errorText);
      return res.status(500).json({
        error: 'Failed to sync contact to Global Control',
        details: errorText,
        retryable: true
      });
    }

    const gcData = await gcResponse.json();
    contactId = gcData._id || gcData.id || contactId;

    console.log('Contact synced successfully:', contactId);

    // Step 3: Apply tags based on quiz participation
    const tagsToApply = ['quiz-participant'];

    // Add quiz-specific tag
    const quizTagName = normalizedQuizId.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    tagsToApply.push(`quiz-${quizTagName}`);

    // Add segment tags based on answers
    if (customFields.audience_type) {
      const audienceTag = customFields.audience_type.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      tagsToApply.push(`audience-${audienceTag}`);
    }

    if (customFields.preferred_city) {
      const cityTag = customFields.preferred_city.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      tagsToApply.push(`city-${cityTag}`);
    }

    // Fire tags
    const tagResults = [];

    for (const tagName of tagsToApply) {
      try {
        // Get or create tag
        const tagListResponse = await fetch('https://api.globalcontrol.io/api/ai/tags', {
          method: 'GET',
          headers: { 'X-API-KEY': GC_API_KEY }
        });

        let tagId = null;
        if (tagListResponse.ok) {
          const tagData = await tagListResponse.json();
          // Handle both array response and object with tags property
          const tags = Array.isArray(tagData) ? tagData : (tagData.tags || []);
          const existingTag = tags.find(t => t.name === tagName);
          if (existingTag) {
            tagId = existingTag._id;
          }
        }

        // Create tag if it doesn't exist
        if (!tagId) {
          const createTagResponse = await fetch('https://api.globalcontrol.io/api/ai/tags', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify({ name: tagName })
          });

          if (createTagResponse.ok) {
            const newTag = await createTagResponse.json();
            tagId = newTag._id;
          }
        }

        // Fire tag on contact
        if (tagId) {
          const fireTagResponse = await fetch(`https://api.globalcontrol.io/api/ai/tags/fire-tag/${tagId}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-API-KEY': GC_API_KEY
            },
            body: JSON.stringify({ contactId: contactId })
          });

          tagResults.push({
            tag: tagName,
            tagId: tagId,
            success: fireTagResponse.ok,
            status: fireTagResponse.status
          });

          // If fire-tag wipes fields, re-apply them
          if (fireTagResponse.ok && isExistingContact) {
            await fetch(`https://api.globalcontrol.io/api/ai/contacts/${contactId}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': GC_API_KEY
              },
              body: JSON.stringify({
                firstName: contactFirstName || '',
                lastName: contactLastName || '',
                customFields: customFields
              })
            });
          }
        }
      } catch (tagError) {
        console.error(`Error processing tag ${tagName}:`, tagError);
        tagResults.push({
          tag: tagName,
          success: false,
          error: tagError.message
        });
      }
    }

    console.log('Tag processing complete:', tagResults);

    // Return success response
    return res.status(200).json({
      success: true,
      message: isExistingContact ? 'Contact updated with quiz data' : 'New contact created from quiz',
      contactId: contactId,
      email: contactEmail,
      quizId: normalizedQuizId,
      quizTitle: normalizedQuizTitle,
      isExistingContact: isExistingContact,
      tagsApplied: tagsToApply,
      tagResults: tagResults,
      customFields: customFields
    });

  } catch (error) {
    console.error('QuizForma webhook error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message,
      retryable: true
    });
  }
}
