/**
 * Voiceflow Function: scheduleCampaign
 * Schedules a campaign (one or many emails) for future delivery via Resend's
 * `scheduled_at` field. Tracks scheduling via the webhook.
 *
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

module.exports = async function scheduleCampaign({
  campaignName = 'untitled_campaign',
  from,
  subject,
  html,
  text,
  recipients = [],         // array of email strings
  replyTo,
  tags = [],
  scheduledAt              // ISO 8601 datetime in the future
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error('RESEND_API_KEY environment variable not set');

  if (!from) throw new Error('from address is required');
  if (!subject) throw new Error('subject is required');
  if (!html && !text) throw new Error('html or text content is required');
  if (!Array.isArray(recipients) || recipients.length === 0) throw new Error('recipients array required');
  if (!scheduledAt) throw new Error('scheduledAt (ISO 8601) is required');

  const date = new Date(scheduledAt);
  if (isNaN(date.getTime())) throw new Error('scheduledAt must be a valid ISO 8601 datetime');
  if (date.getTime() <= Date.now()) throw new Error('scheduledAt must be in the future');

  const result = { campaignName, scheduledAt, scheduled: 0, total: recipients.length, emailIds: [], errors: [] };

  for (const to of recipients) {
    try {
      const resp = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from,
          to: [to],
          subject,
          html,
          text,
          reply_to: replyTo,
          scheduled_at: date.toISOString(),
          tags: [...tags, 'campaign', campaignName].map(t => ({ name: t }))
        })
      });
      const data = await resp.json();
      if (!resp.ok) {
        result.errors.push({ to, error: data.message || resp.status });
        continue;
      }
      result.scheduled++;
      result.emailIds.push(data.id);

      await fetch(BEECEPTOR_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Resend-Event': 'campaign.scheduled' },
        body: JSON.stringify({
          type: 'campaign.scheduled',
          data: { email_id: data.id, to, campaign: campaignName, scheduled_at: date.toISOString() },
          timestamp: new Date().toISOString()
        })
      }).catch(() => {});
    } catch (e) {
      result.errors.push({ to, error: e.message });
    }
  }

  result.success = result.errors.length === 0;
  result.message = `Campaign "${campaignName}" scheduled: ${result.scheduled}/${result.total} emails queued for ${scheduledAt}`;
  return result;
};
