/**
 * Voiceflow Function: manageWhiteLabel
 * White-label settings: brand name, logo, primary color, custom footer.
 * Stored per workspace and forwarded to the webhook for audit.
 *
 * Environment Variables Required: none (uses in-memory store)
 */

const fetch = require('node-fetch');
const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

const whiteLabelStore = new Map();

module.exports = async function manageWhiteLabel({
  action,            // get | set | delete
  workspaceId,
  brandName,
  logoUrl,
  primaryColor,
  footerText
}) {
  const valid = ['get', 'set', 'delete'];
  if (!valid.includes(action)) throw new Error(`Invalid action: ${action}`);
  if (!workspaceId) throw new Error('workspaceId is required');

  const notify = (type, data) => fetch(BEECEPTOR_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Whitelabel-Event': type },
    body: JSON.stringify({ type, data, timestamp: new Date().toISOString() })
  }).catch(() => {});

  switch (action) {
    case 'get':
      return { success: true, settings: whiteLabelStore.get(workspaceId) || null };
    case 'set': {
      const current = whiteLabelStore.get(workspaceId) || {};
      const updated = {
        ...current,
        ...(brandName && { brandName }),
        ...(logoUrl && { logoUrl }),
        ...(primaryColor && { primaryColor }),
        ...(footerText && { footerText }),
        updatedAt: new Date().toISOString()
      };
      whiteLabelStore.set(workspaceId, updated);
      await notify('whitelabel.updated', { workspaceId, settings: updated });
      return { success: true, settings: updated, message: `White-label updated for ${workspaceId}` };
    }
    case 'delete':
      whiteLabelStore.delete(workspaceId);
      await notify('whitelabel.deleted', { workspaceId });
      return { success: true, message: `White-label reset for ${workspaceId}` };
  }
};
