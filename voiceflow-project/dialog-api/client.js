/**
 * Voiceflow Dialog API Client for Resend AI Agent
 * Provides high-level methods for interacting with the agent via Dialog API
 */

const fetch = require('node-fetch');

class ResendAgentClient {
  constructor({ apiKey, projectId, versionId = 'production', baseUrl = 'https://api.voiceflow.com' }) {
    if (!apiKey) throw new Error('VOICEFLOW_API_KEY is required');
    if (!projectId) throw new Error('VOICEFLOW_PROJECT_ID is required');
    
    this.apiKey = apiKey;
    this.projectId = projectId;
    this.versionId = versionId;
    this.baseUrl = baseUrl;
    this.session = null;
  }

  async _request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`Voiceflow API ${response.status}: ${error.message || response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new dialog session
   */
  async createSession(userId, initialRequest = null) {
    const payload = {
      projectID: this.projectId,
      userID: userId,
      ...(initialRequest && { request: initialRequest })
    };

    const data = await this._request('/v2/dialogs', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    this.session = {
      sessionId: data.dialogID,
      state: data.state,
      trace: data.trace
    };

    return {
      sessionId: this.session.sessionId,
      messages: this._extractMessages(data),
      actions: this._extractActions(data)
    };
  }

  /**
   * Send a text message to the agent
   */
  async sendText(text, sessionId = null) {
    const id = sessionId || this.session?.sessionId;
    if (!id) throw new Error('No active session');

    const data = await this._request(`/v2/dialogs/${id}/requests`, {
      method: 'POST',
      body: JSON.stringify({
        request: { type: 'text', payload: text }
      })
    });

    return {
      sessionId: id,
      messages: this._extractMessages(data),
      actions: this._extractActions(data)
    };
  }

  /**
   * Send an intent with entities to the agent
   */
  async sendIntent(intent, entities = {}, sessionId = null) {
    const id = sessionId || this.session?.sessionId;
    if (!id) throw new Error('No active session');

    const data = await this._request(`/v2/dialogs/${id}/requests`, {
      method: 'POST',
      body: JSON.stringify({
        request: {
          type: 'intent',
          payload: {
            intent: { name: intent },
            entities
          }
        }
      })
    });

    return {
      sessionId: id,
      messages: this._extractMessages(data),
      actions: this._extractActions(data)
    };
  }

  /**
   * Send a choice/button selection
   */
  async sendChoice(value, label = value, sessionId = null) {
    const id = sessionId || this.session?.sessionId;
    if (!id) throw new Error('No active session');

    const data = await this._request(`/v2/dialogs/${id}/requests`, {
      method: 'POST',
      body: JSON.stringify({
        request: {
          type: 'choice',
          payload: { value, label }
        }
      })
    });

    return {
      sessionId: id,
      messages: this._extractMessages(data),
      actions: this._extractActions(data)
    };
  }

  /**
   * Send email via send_email intent
   */
  async sendEmail(sessionId, { to, from, subject, html, text, replyTo, tags, scheduledAt }) {
    return this.sendIntent('send_email', {
      to_email: to,
      from_email: from,
      email_subject: subject,
      html_content: html,
      text_content: text,
      reply_to: replyTo,
      email_tags: tags?.join(','),
      scheduled_at: scheduledAt
    }, sessionId);
  }

  /**
   * Check email status via check_email_status intent
   */
  async checkEmailStatus(sessionId, emailId) {
    return this.sendIntent('check_email_status', { email_id: emailId }, sessionId);
  }

  /**
   * List emails via list_emails intent
   */
  async listEmails(sessionId, { limit, fromDate, toDate, status } = {}) {
    return this.sendIntent('list_emails', {
      limit: limit?.toString(),
      from_date: fromDate,
      to_date: toDate,
      status
    }, sessionId);
  }

  /**
   * Verify domain via verify_domain intent
   */
  async verifyDomain(sessionId, domainName) {
    return this.sendIntent('verify_domain', { domain_name: domainName }, sessionId);
  }

  /**
   * Manage contact via manage_contacts intent
   */
  async manageContact(sessionId, { action, email, audienceId, firstName, lastName, unsubscribed }) {
    return this.sendIntent('manage_contacts', {
      action,
      contact_email: email,
      contact_audience_id: audienceId,
      contact_first_name: firstName,
      contact_last_name: lastName,
      contact_unsubscribed: unsubscribed?.toString()
    }, sessionId);
  }

  /**
   * Get help via help intent
   */
  async getHelp(sessionId) {
    return this.sendIntent('help', {}, sessionId);
  }

  /**
   * End the current session
   */
  async endSession(sessionId = null) {
    const id = sessionId || this.session?.sessionId;
    if (!id) return;

    try {
      await this._request(`/v2/dialogs/${id}`, { method: 'DELETE' });
      if (id === this.session?.sessionId) this.session = null;
    } catch (error) {
      console.warn('Failed to end session:', error.message);
    }
  }

  /**
   * Extract messages from dialog response
   */
  _extractMessages(data) {
    if (!data.trace) return [];
    return data.trace
      .filter(t => t.type === 'speak' || t.type === 'text')
      .map(t => ({
        type: t.type,
        content: t.payload?.message || t.payload?.text || JSON.stringify(t.payload)
      }));
  }

  /**
   * Extract actions from dialog response
   */
  _extractActions(data) {
    if (!data.trace) return [];
    return data.trace
      .filter(t => t.type === 'action' || t.type === 'function')
      .map(t => ({
        type: t.type,
        name: t.payload?.name || t.payload?.function,
        params: t.payload?.args || t.payload
      }));
  }
}

module.exports = { ResendAgentClient };
