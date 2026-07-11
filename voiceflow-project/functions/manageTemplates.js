/**
 * Voiceflow Function: manageTemplates
 * Manages email templates in Resend (create, list, get, update, delete)
 * 
 * Note: Resend doesn't have a native templates API yet, so this manages
 * templates locally and can sync with the webhook for tracking
 * 
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

// In-memory template store (replace with database in production)
const templateStore = new Map();

module.exports = async function manageTemplates({ 
  action,           // 'create' | 'list' | 'get' | 'update' | 'delete' | 'send'
  templateId,
  name,
  subject,
  htmlContent,
  textContent,
  variables = [],
  to,
  from,
  replyTo,
  tags,
  data = {}        // Variable values for rendering
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('RESEND_API_KEY environment variable not set');
  }

  // Validate action
  const validActions = ['create', 'list', 'get', 'update', 'delete', 'send'];
  if (!validActions.includes(action)) {
    throw new Error(`Invalid action. Must be one of: ${validActions.join(', ')}`);
  }

  try {
    switch (action) {
      case 'create': {
        if (!name || !subject || (!htmlContent && !textContent)) {
          throw new Error('name, subject, and htmlContent/textContent are required for create');
        }
        
        const id = `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const template = {
          id,
          name,
          subject,
          htmlContent,
          textContent,
          variables: Array.isArray(variables) ? variables : variables.split(',').map(v => v.trim()),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        
        templateStore.set(id, template);
        
        return { success: true, template };
      }

      case 'list': {
        const templates = Array.from(templateStore.values())
          .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        
        return { 
          success: true, 
          templates,
          count: templates.length 
        };
      }

      case 'get': {
        if (!templateId) throw new Error('templateId is required for get');
        const template = templateStore.get(templateId);
        if (!template) throw new Error('Template not found');
        
        return { success: true, template };
      }

      case 'update': {
        if (!templateId) throw new Error('templateId is required for update');
        const template = templateStore.get(templateId);
        if (!template) throw new Error('Template not found');
        
        const updated = {
          ...template,
          ...(name && { name }),
          ...(subject && { subject }),
          ...(htmlContent && { htmlContent }),
          ...(textContent && { textContent }),
          ...(variables && { variables: Array.isArray(variables) ? variables : variables.split(',').map(v => v.trim()) }),
          updatedAt: new Date().toISOString()
        };
        
        templateStore.set(templateId, updated);
        return { success: true, template: updated };
      }

      case 'delete': {
        if (!templateId) throw new Error('templateId is required for delete');
        const deleted = templateStore.delete(templateId);
        if (!deleted) throw new Error('Template not found');
        
        return { success: true, message: 'Template deleted' };
      }

      case 'send': {
        if (!templateId) throw new Error('templateId is required for send');
        if (!to) throw new Error('to is required for send');
        if (!from) throw new Error('from is required for send');
        
        const template = templateStore.get(templateId);
        if (!template) throw new Error('Template not found');
        
        // Render template with variable data
        const render = (content) => {
          if (!content) return content;
          return content.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] !== undefined ? data[key] : match;
          });
        };
        
        const html = render(template.htmlContent);
        const text = render(template.textContent);
        const subject = render(template.subject);
        
        // Send via Resend API
        const response = await fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            from,
            to: Array.isArray(to) ? to : [to],
            subject,
            html,
            text,
            reply_to: replyTo,
            tags: tags?.map(t => ({ name: t })) || []
          })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(`Resend API Error: ${result.message || result.error || response.status}`);
        }
        
        // Log to webhook for tracking
        await fetch('https://wh34c025ff0874a90e2f.free.beeceptor.com/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'template.sent',
            templateId,
            templateName: template.name,
            emailId: result.id,
            to,
            timestamp: new Date().toISOString()
          })
        }).catch(() => {}); // Don't fail on webhook error
        
        return { 
          success: true, 
          emailId: result.id,
          message: 'Email sent from template',
          templateName: template.name
        };
      }
    }
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Resend API');
    }
    throw error;
  }
};
