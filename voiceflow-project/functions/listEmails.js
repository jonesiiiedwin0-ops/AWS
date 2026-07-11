/**
 * Voiceflow Function: listEmails
 * Lists sent emails with optional filters
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function listEmails({ 
  from, 
  to, 
  created_after, 
  created_before, 
  status, 
  limit = 10 
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Validate limit
  if (limit < 1 || limit > 100) {
    throw new Error('limit must be between 1 and 100');
  }

  // Validate date formats if provided
  const dateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;
  if (created_after && !dateRegex.test(created_after)) {
    throw new Error('created_after must be in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)');
  }
  if (created_before && !dateRegex.test(created_before)) {
    throw new Error('created_before must be in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)');
  }

  // Validate status if provided
  const validStatuses = ['sent', 'delivered', 'bounced', 'complained'];
  if (status && !validStatuses.includes(status)) {
    throw new Error(`Invalid status. Must be one of: ${validStatuses.join(', ')}`);
  }

  // Build query parameters
  const params = new URLSearchParams({
    limit: limit.toString()
  });
  
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (created_after) params.append('created_after', created_after);
  if (created_before) params.append('created_before', created_before);
  if (status) params.append('status', status);

  try {
    const response = await fetch(`https://api.resend.com/emails?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.message || data.error || `HTTP ${response.status}`;
      throw new Error(`Resend API Error: ${errorMessage}`);
    }

    return {
      success: true,
      emails: data.data || [],
      has_more: data.has_more || false,
      total_count: data.total_count || 0
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
