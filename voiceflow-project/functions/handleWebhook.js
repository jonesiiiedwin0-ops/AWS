/**
 * Voiceflow Function: handleWebhook
 * Processes Resend webhook events and optionally sends proactive notifications
 * 
 * Webhook URL: https://wh34c025ff0874a90e2f.free.beeceptor.com/
 * 
 * Events handled:
 * - email.sent
 * - email.delivered
 * - email.bounced
 * - email.complained
 * - email.opened
 * - email.clicked
 * - template.sent (custom event from manageTemplates)
 * 
 * Environment Variables:
 * - VOICEFLOW_API_KEY: For proactive notifications
 * - VOICEFLOW_PROJECT_ID: For proactive notifications
 * - VOICEFLOW_BASE_URL: (optional) Default: https://general-runtime.voiceflow.com
 */

const fetch = require('node-fetch');

const VOICEFLOW_BASE_URL = process.env.VOICEFLOW_BASE_URL || 'https://general-runtime.voiceflow.com';
const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

module.exports = async function handleWebhook({ 
  eventType,      // 'email.sent', 'email.delivered', etc.
  eventData,      // Event payload from Resend
  notifyUser = false,    // Send proactive notification
  userId = null,         // User ID for notification
  voiceflowApiKey = process.env.VOICEFLOW_API_KEY,
  voiceflowProjectId = process.env.VOICEFLOW_PROJECT_ID
}) {
  // Validate event type
  const validEvents = [
    'email.sent', 'email.delivered', 'email.bounced',
    'email.complained', 'email.opened', 'email.clicked',
    'template.sent'
  ];
  
  if (!validEvents.includes(eventType)) {
    throw new Error(`Invalid eventType. Must be one of: ${validEvents.join(', ')}`);
  }

  // Forward to Beeceptor for inspection/debugging
  try {
    await fetch(BEECEPTOR_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Resend-Event': eventType,
        'X-Processed-By': 'resend-voiceflow-agent'
      },
      body: JSON.stringify({
        type: eventType,
        data: eventData,
        receivedAt: new Date().toISOString()
      })
    });
  } catch (error) {
    console.warn('Failed to forward to Beeceptor:', error.message);
  }

  // Process event and generate response
  let response = { success: true, eventType, processed: true };

  switch (eventType) {
    case 'email.sent':
      response = {
        ...response,
        message: `Email sent to ${eventData.to?.join(', ') || 'recipient'}`,
        emailId: eventData.email_id,
        subject: eventData.subject,
        timestamp: eventData.created_at
      };
      break;

    case 'email.delivered':
      response = {
        ...response,
        message: `Email delivered to ${eventData.to?.join(', ') || 'recipient'}`,
        emailId: eventData.email_id,
        deliveredAt: eventData.delivered_at
      };
      break;

    case 'email.bounced':
      response = {
        ...response,
        message: `Email bounced: ${eventData.bounce_type} bounce to ${eventData.to?.join(', ')}`,
        emailId: eventData.email_id,
        bounceType: eventData.bounce_type,
        bouncedAt: eventData.bounced_at,
        actionRequired: true
      };
      break;

    case 'email.complained':
      response = {
        ...response,
        message: `Spam complaint received for email to ${eventData.to?.join(', ')}`,
        emailId: eventData.email_id,
        complainedAt: eventData.complained_at,
        actionRequired: true
      };
      break;

    case 'email.opened':
      response = {
        ...response,
        message: `Email opened by ${eventData.to?.join(', ')}`,
        emailId: eventData.email_id,
        openedAt: eventData.opened_at
      };
      break;

    case 'email.clicked':
      response = {
        ...response,
        message: `Link clicked in email to ${eventData.to?.join(', ')}: ${eventData.url}`,
        emailId: eventData.email_id,
        url: eventData.url,
        clickedAt: eventData.clicked_at
      };
      break;

    case 'template.sent':
      response = {
        ...response,
        message: `Template "${eventData.templateName}" sent to ${eventData.to?.join(', ')}`,
        templateId: eventData.templateId,
        templateName: eventData.templateName,
        emailId: eventData.emailId,
        timestamp: eventData.timestamp
      };
      break;
  }

  // Send proactive notification if requested
  if (notifyUser && userId && voiceflowApiKey && voiceflowProjectId) {
    try {
      const notificationMessage = `📧 Resend Event: ${response.message}`;
      
      await fetch(`${VOICEFLOW_BASE_URL}/v1/projects/${voiceflowProjectId}/dialogs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${voiceflowApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userID: userId,
          platform: 'webhook',
          request: {
            type: 'text',
            payload: notificationMessage
          }
        })
      });
      response.notificationSent = true;
    } catch (error) {
      console.error('Failed to send proactive notification:', error.message);
      response.notificationSent = false;
      response.notificationError = error.message;
    }
  }

  return response;
};
