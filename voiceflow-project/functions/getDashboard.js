/**
 * Voiceflow Function: getDashboard
 * Advanced analytics dashboard: aggregates email stats + tenant/workspace
 * context into a structured dashboard payload and forwards to the webhook.
 *
 * Environment Variables Required:
 * - RESEND_API_KEY
 */

const fetch = require('node-fetch');
const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

module.exports = async function getDashboard({
  period = '7d',
  tenantId,
  workspaceId
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error('RESEND_API_KEY environment variable not set');

  const periodMs = { '1d': 864e5, '7d': 6048e5, '30d': 2592e6, '90d': 7776e6 }[period] || 6048e5;
  const createdAfter = new Date(Date.now() - periodMs).toISOString();

  const response = await fetch(`https://api.resend.com/emails?limit=100&created_after=${encodeURIComponent(createdAfter)}`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`Resend API Error: ${data.message || response.status}`);

  const emails = data.data || [];
  const byStatus = {}, byDay = {}, byDomain = {};
  let sent = 0, delivered = 0, bounced = 0, complained = 0;

  for (const e of emails) {
    const s = e.last_event || 'sent';
    byStatus[s] = (byStatus[s] || 0) + 1;
    if (s === 'sent') sent++;
    if (s === 'delivered') delivered++;
    if (s === 'bounced') bounced++;
    if (s === 'complained') complained++;
    const day = new Date(e.created_at).toISOString().split('T')[0];
    byDay[day] = (byDay[day] || 0) + 1;
    const dom = (e.to && e.to[0] && e.to[0].split('@')[1]) || 'unknown';
    byDomain[dom] = (byDomain[dom] || 0) + 1;
  }

  const total = emails.length;
  const dashboard = {
    period,
    tenantId: tenantId || null,
    workspaceId: workspaceId || null,
    total,
    sent, delivered, bounced, complained,
    deliveryRate: total ? ((delivered / total) * 100).toFixed(1) : '0.0',
    bounceRate: total ? ((bounced / total) * 100).toFixed(1) : '0.0',
    complaintRate: total ? ((complained / total) * 100).toFixed(1) : '0.0',
    byStatus, byDay, topDomains: Object.entries(byDomain).sort((a, b) => b[1] - a[1]).slice(0, 5)
  };

  await fetch(BEECEPTOR_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Dashboard-Event': 'dashboard.viewed' },
    body: JSON.stringify({ type: 'dashboard.viewed', data: dashboard, timestamp: new Date().toISOString() })
  }).catch(() => {});

  return { success: true, dashboard };
};
