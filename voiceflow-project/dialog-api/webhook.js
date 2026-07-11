/**
 * Resend Webhook Handler for Voiceflow Agent
 * Receives Resend webhook events and can trigger Voiceflow Dialog API
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
 */

const crypto = require('crypto');
const fetch = require('node-fetch');

const WEBHOOK_SECRET = process.env.RESEND_WEBHOOK_SECRET; // Set in Resend dashboard
const VOICEFLOW_API_KEY = process.env.VOICEFLOW_API_KEY;
const VOICEFLOW_PROJECT_ID = process.env.VOICEFLOW_PROJECT_ID;
const VOICEFLOW_BASE_URL = process.env.VOICEFLOW_BASE_URL || 'https://general-runtime.voiceflow.com';
const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

class ResendWebhookHandler {
  constructor(config = {}) {
    this.webhookSecret = config.webhookSecret || WEBHOOK_SECRET;
    this.voiceflowApiKey = config.voiceflowApiKey || VOICEFLOW_API_KEY;
    this.voiceflowProjectId = config.voiceflowProjectId || VOICEFLOW_PROJECT_ID;
    this.voiceflowBaseUrl = config.voiceflowBaseUrl || VOICEFLOW_BASE_URL;
    this.forwardToBeeceptor = config.forwardToBeeceptor !== false;
  }

  /**
   * Verify webhook signature from Resend
   */
  verifySignature(payload, signature) {
    if (!this.webhookSecret) {
      console.warn('Webhook secret not configured, skipping verification');
      return true;
    }

    const expectedSignature = crypto
      .createHmac('sha256', this.webhookSecret)
      .update(payload, 'utf8')
      .digest('hex');

    const providedSignature = signature.replace('sha256=', '');
    
    return crypto.timingSafeEqual(
      Buffer.from(expectedSignature),
      Buffer.from(providedSignature)
    );
  }

  /**
   * Forward webhook to Beeceptor for inspection
   */
  async forwardToBeeceptor(event) {
    try {
      await fetch(BEECEPTOR_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Resend-Event': event.type,
          'X-Forwarded-By': 'resend-voiceflow-agent'
        },
        body: JSON.stringify(event)
      });
    } catch (error) {
      console.error('Failed to forward to Beeceptor:', error.message);
    }
  }

  /**
   * Process incoming webhook event
   */
  async handleWebhook(req, res) {
    const signature = req.headers['resend-signature'] || req.headers['x-resend-signature'];
    const rawBody = req.rawBody || JSON.stringify(req.body);

    // Verify signature
    if (!this.verifySignature(rawBody, signature)) {
      console.error('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = req.body;
    console.log(`Received Resend webhook: ${event.type}`, event.data?.email_id);

    // Forward to Beeceptor for debugging
    if (this.forwardToBeeceptor) {
      await this.forwardToBeeceptor(event);
    }

    // Process event based on type
    try {
      await this.processEvent(event);
      res.json({ success: true });
    } catch (error) {
      console.error('Webhook processing error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  /**
   * Process specific event types
   */
  async processEvent(event) {
    const { type, data } = event;

    switch (type) {
      case 'email.sent':
        await this.handleEmailSent(data);
        break;
      case 'email.delivered':
        await this.handleEmailDelivered(data);
        break;
      case 'email.bounced':
        await this.handleEmailBounced(data);
        break;
      case 'email.complained':
        await this.handleEmailComplained(data);
        break;
      case 'email.opened':
        await this.handleEmailOpened(data);
        break;
      case 'email.clicked':
        await this.handleEmailClicked(data);
        break;
      default:
        console.log(`Unhandled event type: ${type}`);
    }
  }

  /**
   * Handle email.sent event
   */
  async handleEmailSent(data) {
    console.log(`Email sent: ${data.email_id} to ${data.to}`);
    // Could trigger proactive notification via Voiceflow
    // await this.notifyUser(data.to, `Email sent: ${data.subject}`);
  }

  /**
   * Handle email.delivered event
   */
  async handleEmailDelivered(data) {
    console.log(`Email delivered: ${data.email_id} to ${data.to}`);
    // Could notify user or update tracking
  }

  /**
   * Handle email.bounced event
   */
  async handleEmailBounced(data) {
    console.log(`Email bounced: ${data.email_id} to ${data.to} - ${data.bounce_type}`);
    // Could trigger proactive notification about bounce
  }

  /**
   * Handle email.complained event
   */
  async handleEmailComplained(data) {
    console.log(`Email complained: ${data.email_id} to ${data.to}`);
    // Could auto-unsubscribe contact
  }

  /**
   * Handle email.opened event
   */
  async handleEmailOpened(data) {
    console.log(`Email opened: ${data.email_id} by ${data.to}`);
  }

  /**
   * Handle email.clicked event
   */
  async handleEmailClicked(data) {
    console.log(`Email clicked: ${data.email_id} by ${data.to} - ${data.url}`);
  }

  /**
   * Send proactive notification via Voiceflow Dialog API
   */
  async notifyUser(userId, message) {
    if (!this.voiceflowApiKey || !this.voiceflowProjectId) {
      console.warn('Voiceflow credentials not configured, skipping notification');
      return;
    }

    try {
      const url = `${this.voiceflowBaseUrl}/v1/projects/${this.voiceflowProjectId}/dialogs`;
      
      await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.voiceflowApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userID: userId,
          platform: 'webhook',
          request: {
            type: 'text',
            payload: message
          }
        })
      });
    } catch (error) {
      console.error('Failed to send proactive notification:', error.message);
    }
  }
}

/**
 * Express.js middleware for webhook
 */
function createWebhookMiddleware(handler) {
  return async (req, res, next) => {
    // Capture raw body for signature verification
    let data = '';
    req.setEncoding('utf8');
    req.on('data', chunk => { data += chunk; });
    req.on('end', () => {
      req.rawBody = data;
      try {
        req.body = JSON.parse(data);
      } catch {
        req.body = {};
      }
      handler.handleWebhook(req, res).catch(next);
    });
  };
}

/**
 * Standalone webhook server (for testing)
 */
async function startWebhookServer(port = 3000, config = {}) {
  const express = require('express');
  const app = express();
  
  const handler = new ResendWebhookHandler(config);
  
  app.use(express.json({ verify: (req, res, buf) => { req.rawBody = buf; } }));
  app.post('/webhook/resend', createWebhookMiddleware(handler));
  app.get('/health', (req, res) => res.json({ status: 'ok' }));

  app.listen(port, () => {
    console.log(`Resend webhook server listening on port ${port}`);
    console.log(`Webhook endpoint: http://localhost:${port}/webhook/resend`);
    console.log(`Beeceptor forwarding: ${BEECEPTOR_WEBHOOK_URL}`);
  });

  return app;
}

module.exports = {
  ResendWebhookHandler,
  createWebhookMiddleware,
  startWebhookServer,
  BEECEPTOR_WEBHOOK_URL
};
