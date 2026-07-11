/**
 * Voiceflow Function: voiceIntegration
 * Handles voice-specific interactions for Voiceflow Voice
 * 
 * Environment Variables Required:
 * - VOICEFLOW_API_KEY: For proactive voice notifications
 * - VOICEFLOW_PROJECT_ID: For proactive voice notifications
 */

const fetch = require('node-fetch');

module.exports = async function voiceIntegration({ 
  action,           // 'speak', 'listen', 'transfer', 'hangup', 'notify'
  text,             // Text to speak (for 'speak')
  voice = 'alloy',  // Voice: alloy, echo, fable, onyx, nova, shimmer
  language = 'en-US',
  sessionId,        // Voice session ID
  userId,           // User ID for proactive notifications
  message           // Message for proactive notification
}) {
  const voiceflowApiKey = process.env.VOICEFLOW_API_KEY;
  const voiceflowProjectId = process.env.VOICEFLOW_PROJECT_ID;
  const voiceflowBaseUrl = process.env.VOICEFLOW_BASE_URL || 'https://general-runtime.voiceflow.com';

  const validActions = ['speak', 'listen', 'transfer', 'hangup', 'notify', 'dtmf'];
  if (!validActions.includes(action)) {
    throw new Error(`Invalid action. Must be one of: ${validActions.join(', ')}`);
  }

  try {
    switch (action) {
      case 'speak': {
        if (!text) throw new Error('text is required for speak action');
        
        // Return SSML for voice synthesis
        return {
          success: true,
          action: 'speak',
          ssml: `<speak><voice name="${voice}">${escapeXml(text)}</voice></speak>`,
          text
        };
      }

      case 'listen': {
        return {
          success: true,
          action: 'listen',
          language,
          maxDuration: 10,
          silenceTimeout: 3
        };
      }

      case 'dtmf': {
        return {
          success: true,
          action: 'dtmf',
          maxDigits: 10,
          timeout: 5,
          finishOnKey: '#'
        };
      }

      case 'transfer': {
        if (!sessionId) throw new Error('sessionId is required for transfer');
        
        // Transfer to human agent or another number
        return {
          success: true,
          action: 'transfer',
          sessionId,
          message: 'Transferring you to an agent...'
        };
      }

      case 'hangup': {
        return {
          success: true,
          action: 'hangup',
          message: 'Goodbye!'
        };
      }

      case 'notify': {
        // Send proactive voice notification
        if (!userId || !message) {
          throw new Error('userId and message are required for notify');
        }
        if (!voiceflowApiKey || !voiceflowProjectId) {
          throw new Error('VOICEFLOW_API_KEY and VOICEFLOW_PROJECT_ID required for notifications');
        }

        const response = await fetch(`${voiceflowBaseUrl}/v1/projects/${voiceflowProjectId}/dialogs`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${voiceflowApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            userID: userId,
            platform: 'voice',
            request: {
              type: 'text',
              payload: message
            }
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(`Voiceflow API Error: ${data.message || response.status}`);
        }

        return {
          success: true,
          action: 'notify',
          dialogId: data.dialogID,
          message: 'Voice notification sent'
        };
      }

      default:
        throw new Error(`Action ${action} not implemented`);
    }
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Voiceflow API');
    }
    throw error;
  }
};

function escapeXml(text) {
  return text
    .replace(/&/g, '&')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/"/g, '"')
    .replace(/'/g, '&apos;');
}
