/**
 * Voiceflow Function: verifyDomain
 * Creates and verifies a sending domain in Resend
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function verifyDomain({ domain }) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Validate domain format
  const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
  if (!domainRegex.test(domain)) {
    throw new Error('Invalid domain format. Example: example.com');
  }

  try {
    const response = await fetch('https://api.resend.com/domains', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: domain })
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.message || data.error || `HTTP ${response.status}`;
      throw new Error(`Resend API Error: ${errorMessage}`);
    }

    // Format DNS records for user-friendly display
    const dnsRecords = data.records.map(record => ({
      type: record.type,
      name: record.name,
      value: record.value,
      priority: record.priority,
      verified: record.verified
    }));

    return {
      success: true,
      domain: data.name,
      id: data.id,
      status: data.status,
      region: data.region,
      created_at: data.created_at,
      dns_records: dnsRecords,
      instructions: `To verify your domain, add these DNS records to your domain provider (e.g., GoDaddy, Cloudflare, Route53):`
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
