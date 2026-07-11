/**
 * Voiceflow Function: getAnalytics
 * Calculates email analytics from Resend data
 * 
 * Note: Resend doesn't have a native analytics endpoint, so this 
 * fetches emails and computes statistics client-side
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

module.exports = async function getAnalytics({ 
  period = '7d',     // '1d', '7d', '30d', '90d'
  groupBy = 'day',   // 'hour', 'day', 'week'
  limit = 1000
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Calculate date range
  const now = new Date();
  const periodMs = {
    '1d': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000,
    '90d': 90 * 24 * 60 * 60 * 1000
  }[period] || 7 * 24 * 60 * 60 * 1000;

  const startDate = new Date(now.getTime() - periodMs);
  const createdAfter = startDate.toISOString();

  try {
    // Fetch emails (paginated)
    let allEmails = [];
    let hasMore = true;
    let cursor = null;
    let fetched = 0;

    while (hasMore && fetched < limit) {
      const params = new URLSearchParams({
        limit: Math.min(100, limit - fetched).toString(),
        created_after: createdAfter
      });
      if (cursor) params.append('after', cursor);

      const response = await fetch(`https://api.resend.com/emails?${params.toString()}`, {
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

      const emails = data.data || [];
      allEmails = allEmails.concat(emails);
      fetched += emails.length;
      hasMore = data.has_more || false;
      cursor = data.next_cursor || null;
    }

    // Compute statistics
    const stats = computeStats(allEmails, groupBy, period);

    return {
      success: true,
      period,
      groupBy,
      stats
    };

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};

function computeStats(emails, groupBy, period) {
  const stats = {
    total: emails.length,
    sent: 0,
    delivered: 0,
    bounced: 0,
    complained: 0,
    byStatus: {},
    byDomain: {},
    byDay: {},
    byHour: {}
  };

  // Status counts
  const statusMap = {
    'sent': 'sent',
    'delivered': 'delivered',
    'bounced': 'bounced',
    'complained': 'complained'
  };

  for (const email of emails) {
    const status = email.last_event || 'sent';
    stats[statusMap[status] || 'sent']++;

    // By status
    stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

    // By domain (from recipient)
    if (email.to && email.to.length > 0) {
      const domain = email.to[0].split('@')[1] || 'unknown';
      stats.byDomain[domain] = (stats.byDomain[domain] || 0) + 1;
    }

    // Time grouping
    const createdAt = new Date(email.created_at);
    
    if (groupBy === 'day' || groupBy === 'week') {
      const dayKey = createdAt.toISOString().split('T')[0];
      stats.byDay[dayKey] = (stats.byDay[dayKey] || 0) + 1;
    }
    
    if (groupBy === 'hour') {
      const hourKey = createdAt.toISOString().substring(0, 13) + ':00';
      stats.byHour[hourKey] = (stats.byHour[hourKey] || 0) + 1;
    }
  }

  // Calculate rates
  stats.deliveryRate = stats.total > 0 ? ((stats.delivered / stats.total) * 100).toFixed(1) : '0.0';
  stats.bounceRate = stats.total > 0 ? ((stats.bounced / stats.total) * 100).toFixed(1) : '0.0';
  stats.complaintRate = stats.total > 0 ? ((stats.complained / stats.total) * 100).toFixed(1) : '0.0';

  // Sort byDay
  const sortedByDay = {};
  Object.keys(stats.byDay).sort().forEach(key => {
    sortedByDay[key] = stats.byDay[key];
  });
  stats.byDay = sortedByDay;

  // Sort byHour
  const sortedByHour = {};
  Object.keys(stats.byHour).sort().forEach(key => {
    sortedByHour[key] = stats.byHour[key];
  });
  stats.byHour = sortedByHour;

  // Top domains
  const sortedDomains = Object.entries(stats.byDomain)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .reduce((obj, [key, val]) => { obj[key] = val; return obj; }, {});
  stats.byDomain = sortedDomains;

  return stats;
}
