/**
 * Voiceflow Function: manageAudiences
 * Manages audiences in Resend
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function manageAudiences({ 
  action,           // 'create' | 'list' | 'get' | 'update' | 'delete'
  audienceId,
  name,
  description
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  const validActions = ['create', 'list', 'get', 'update', 'delete'];
  if (!validActions.includes(action)) {
    throw new Error(`Invalid action. Must be one of: ${validActions.join(', ')}`);
  }

  try {
    switch (action) {
      case 'create': {
        if (!name) throw new Error('name is required for create');
        
        const response = await fetch('https://api.resend.com/audiences', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name, ...(description && { description }) })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(`Resend API Error: ${data.message || data.error || response.status}`);
        }

        return { success: true, data };
      }

      case 'list': {
        const response = await fetch('https://api.resend.com/audiences', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(`Resend API Error: ${data.message || data.error || response.status}`);
        }

        return { success: true, data: data.data || data };
      }

      case 'get': {
        if (!audienceId) throw new Error('audienceId is required for get');
        
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(audienceId)) {
          throw new Error('Invalid audienceId format. Must be a valid UUID.');
        }

        const response = await fetch(`https://api.resend.com/audiences/${audienceId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (!response.ok) {
          if (response.status === 404) throw new Error('Audience not found');
          throw new Error(`Resend API Error: ${data.message || data.error || response.status}`);
        }

        return { success: true, data };
      }

      case 'update': {
        if (!audienceId) throw new Error('audienceId is required for update');
        if (!name && !description) throw new Error('name or description is required for update');
        
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(audienceId)) {
          throw new Error('Invalid audienceId format. Must be a valid UUID.');
        }

        const updateData = {};
        if (name) updateData.name = name;
        if (description) updateData.description = description;

        const response = await fetch(`https://api.resend.com/audiences/${audienceId}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updateData)
        });

        const data = await response.json();

        if (!response.ok) {
          if (response.status === 404) throw new Error('Audience not found');
          throw new Error(`Resend API Error: ${data.message || data.error || response.status}`);
        }

        return { success: true, data };
      }

      case 'delete': {
        if (!audienceId) throw new Error('audienceId is required for delete');
        
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(audienceId)) {
          throw new Error('Invalid audienceId format. Must be a valid UUID.');
        }

        const response = await fetch(`https://api.resend.com/audiences/${audienceId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (!response.ok) {
          if (response.status === 404) throw new Error('Audience not found');
          throw new Error(`Resend API Error: ${data.message || data.error || response.status}`);
        }

        return { success: true, data };
      }
    }
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
