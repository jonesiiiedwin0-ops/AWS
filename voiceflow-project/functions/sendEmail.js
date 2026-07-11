/**
 * Voiceflow Function: sendEmail
 * Sends transactional or marketing emails via Resend API
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function sendEmail({ 
  to,                    // string or string[] - required
  from,                  // string - required (verified domain)
  subject,               // string - required
  html,                  // string - optional (required if no text)
  text,                  // string - optional (required if no html)
  reply_to,              // string - optional
  tags,                  // object[] - optional [{name: 'tag', value: 'value'}]
  headers,               // object - optional custom headers
  scheduled_at           // string - optional ISO 8601 timestamp
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Validate required fields
  if (!from) throw new Error('from email is required');
  if (!subject) throw new Error('subject is required');
  if (!to) throw new Error('to email is required');
  if (!html && !text) throw new Error('Either html or text content is required');

  // Validate email format for 'from'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(from)) {
    throw new Error('Invalid from email format');
  }

  // Validate 'to' - can be string or array
  const recipients = Array.isArray(to) ? to : [to];
  for (const recipient of recipients) {
    if (!emailRegex.test(recipient)) {
      throw new Error(`Invalid recipient email: ${recipient}`);
    }
  }

  // Validate reply_to if provided
  if (reply_to && !emailRegex.test(reply_to)) {
    throw new Error('Invalid reply_to email format');
  }

  // Validate tags if provided
  if (tags) {
    if (!Array.isArray(tags)) {
      throw new Error('tags must be an array of objects with name and value');
    }
    for (const tag of tags) {
      if (!tag.name || !tag.value) {
        throw new Error('Each tag must have name and value properties');
      }
    }
  }

  // Validate scheduled_at if provided
  if (scheduled_at) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;
    if (!dateRegex.test(scheduled_at)) {
      throw new Error('scheduled_at must be in ISO 8601 format (e.g., 2024-12-31T23:59:59Z)');
    }
    const scheduledDate = new Date(scheduled_at);
    const now = new Date();
    if (scheduledDate <= now) {
      throw new Error('scheduled_at must be in the future');
    }
  }

  // Build request body
  const body = {
    from,
    to: recipients,
    subject
  };

  if (html) body.html = html;
  if (text) body.text = text;
  if (reply_to) body.reply_to = reply_to;
  if (tags) body.tags = tags;
  if (headers) body.headers = headers;
  if (scheduled_at) body.scheduled_at = scheduled_at;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.message || data.error || `HTTP ${response.status}`;
      throw new Error(`Resend API Error: ${errorMessage}`);
    }

    return {
      success: true,
      email_id: data.id,
      message: 'Email sent successfully'
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
