/**
 * Voiceflow Function: sendBatch
 * Sends multiple emails in batch via Resend API
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 * 
 * Webhook URL: https://wh34c025ff0874a90e2f.free.beeceptor.com/
 */

const fetch = require('node-fetch');

const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

module.exports = async function sendBatch({ 
  emails,           // Required: Array of email objects
  batchName,        // Optional: Name for this batch
  webhookUrl        // Optional: Custom webhook for completion notification
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  if (!emails || !Array.isArray(emails) || emails.length === 0) {
    throw new Error('emails array is required and must not be empty');
  }

  if (emails.length > 1000) {
    throw new Error('Batch size cannot exceed 1000 emails');
  }

  // Validate each email
  for (let i = 0; i < emails.length; i++) {
    const email = emails[i];
    if (!email.to) throw new Error(`Email ${i}: 'to' is required`);
    if (!email.from) throw new Error(`Email ${i}: 'from' is required`);
    if (!email.subject) throw new Error(`Email ${i}: 'subject' is required`);
    if (!email.html && !email.text) throw new Error(`Email ${i}: 'html' or 'text' is required`);
  }

  const results = {
    success: [],
    failed: [],
    total: emails.length
  };

  // Send emails sequentially
  for (const email of emails) {
    try {
      const response = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          from: email.from,
          to: Array.isArray(email.to) ? email.to : [email.to],
          subject: email.subject,
          html: email.html,
          text: email.text,
          reply_to: email.replyTo,
          tags: email.tags?.map(t => ({ name: t })) || [],
          headers: email.headers,
          scheduled_at: email.scheduledAt
        })
      });

      const data = await response.json();

      if (!response.ok) {
        results.failed.push({
          email: email.to,
          error: data.message || data.error || `HTTP ${response.status}`
        });
      } else {
        results.success.push({
          emailId: data.id,
          to: email.to,
          subject: email.subject
        });

        // Forward to Beeceptor webhook
        try {
          await fetch(BEECEPTOR_WEBHOOK_URL, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Resend-Event': 'email.sent',
              'X-Batch-Name': batchName || 'batch',
              'X-Processed-By': 'resend-voiceflow-agent'
            },
            body: JSON.stringify({
              type: 'email.sent',
              data: {
                email_id: data.id,
                to: email.to,
                from: email.from,
                subject: email.subject,
                batch_name: batchName
              },
              timestamp: new Date().toISOString()
            })
          });
        } catch (webhookError) {
          console.warn('Failed to forward to webhook:', webhookError.message);
        }
      }
    } catch (error) {
      results.failed.push({
        email: email.to,
        error: error.message
      });
    }
  }

  // Send batch completion webhook if provided
  if (webhookUrl) {
    try {
      await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'batch.completed',
          batchName: batchName || 'batch',
          results,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.warn('Failed to send batch completion webhook:', error.message);
    }
  }

  return {
    success: results.failed.length === 0,
    results,
    message: `Batch completed: ${results.success.length} sent, ${results.failed.length} failed`
  };
};
