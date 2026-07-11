/**
 * Voiceflow Function: getEmailStatus
 * Retrieves email delivery status from Resend API
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function getEmailStatus({ email_id }) {
  if (!email_id) {
    throw new Error('email_id is required');
  }

  // Validate UUID format
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(email_id)) {
    throw new Error('Invalid email_id format. Must be a valid UUID.');
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  try {
    const response = await fetch(`https://api.resend.com/emails/${email_id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Email not found');
      }
      const errorMessage = data.message || data.error || `HTTP ${response.status}`;
      throw new Error(`Resend API Error: ${errorMessage}`);
    }

    return {
      success: true,
      email_id: data.id,
      status: data.last_event,
      created_at: data.created_at,
      sent_at: data.sent_at,
      delivered_at: data.delivered_at,
      bounced_at: data.bounced_at,
      opened_at: data.opened_at,
      clicked_at: data.clicked_at,
      data
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
