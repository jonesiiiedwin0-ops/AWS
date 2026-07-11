/**
 * Voiceflow Function: manageContacts
 * Manages contacts in Resend audiences (add, update, unsubscribe)
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function manageContacts({ 
  action,           // 'add' | 'update' | 'unsubscribe'
  email, 
  audience_id,
  first_name,
  last_name,
  unsubscribed = false
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Validate email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email address format');
  }

  // Validate audience_id (UUID)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(audience_id)) {
    throw new Error('Invalid audience_id. Must be a valid UUID');
  }

  // Validate action
  const validActions = ['add', 'update', 'unsubscribe'];
  if (!validActions.includes(action)) {
    throw new Error(`Invalid action. Must be one of: ${validActions.join(', ')}`);
  }

  const contactData = {
    email,
    unsubscribed
  };

  if (first_name) contactData.first_name = first_name;
  if (last_name) contactData.last_name = last_name;

  let url = `https://api.resend.com/audiences/${audience_id}/contacts`;
  let method = 'POST';

  if (action === 'update' || action === 'unsubscribe') {
    url = `${url}/${email}`;
    method = 'PATCH';
  }

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(contactData)
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Audience or contact not found');
      }
      const errorMessage = data.message || data.error || `HTTP ${response.status}`;
      throw new Error(`Resend API Error: ${errorMessage}`);
    }

    const actionMessages = {
      add: 'Contact added successfully',
      update: 'Contact updated successfully',
      unsubscribe: 'Contact unsubscribed successfully'
    };

    return {
      success: true,
      message: actionMessages[action],
      contact: data,
      action
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
