/**
 * Voiceflow Function: manageTenants
 * Multi-tenant support: isolates each tenant's Resend API key and settings.
 *
 * Resend has no native multi-tenancy, so this meta-layer stores per-tenant
 * config and validates that operations stay scoped to a tenant. All mutations
 * are forwarded to the webhook for audit trail.
 *
 * Environment Variables Required:
 * - TENANT_STORE (optional JSON map; in production use a database)
 */

const fetch = require('node-fetch');
const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

// In-memory tenant store (replace with DB in production)
const tenantStore = new Map();

module.exports = async function manageTenants({
  action,                 // create | list | get | update | delete
  tenantId,
  name,
  resendApiKey,           // per-tenant Resend key
  plan = 'free',          // free | pro | enterprise
  settings = {}
}) {
  const valid = ['create', 'list', 'get', 'update', 'delete'];
  if (!valid.includes(action)) throw new Error(`Invalid action: ${action}`);

  const notify = (type, data) => fetch(BEECEPTOR_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Tenant-Event': type },
    body: JSON.stringify({ type, data, timestamp: new Date().toISOString() })
  }).catch(() => {});

  switch (action) {
    case 'create': {
      if (!name) throw new Error('name is required');
      if (!resendApiKey) throw new Error('resendApiKey is required');
      const id = tenantId || `tenant_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const tenant = { id, name, resendApiKey, plan, settings, createdAt: new Date().toISOString() };
      tenantStore.set(id, tenant);
      await notify('tenant.created', { id, name, plan });
      return { success: true, tenant: { ...tenant, resendApiKey: '***redacted***' }, message: `Tenant ${name} created` };
    }
    case 'list':
      return { success: true, tenants: Array.from(tenantStore.values()).map(t => ({ ...t, resendApiKey: '***redacted***' })), count: tenantStore.size };
    case 'get': {
      if (!tenantId) throw new Error('tenantId required');
      const t = tenantStore.get(tenantId);
      if (!t) throw new Error('Tenant not found');
      return { success: true, tenant: { ...t, resendApiKey: '***redacted***' } };
    }
    case 'update': {
      if (!tenantId) throw new Error('tenantId required');
      const t = tenantStore.get(tenantId);
      if (!t) throw new Error('Tenant not found');
      const updated = { ...t, ...(name && { name }), ...(resendApiKey && { resendApiKey }), ...(plan && { plan }), ...(settings && { settings }) };
      tenantStore.set(tenantId, updated);
      await notify('tenant.updated', { id: tenantId, name: updated.name });
      return { success: true, tenant: { ...updated, resendApiKey: '***redacted***' }, message: 'Tenant updated' };
    }
    case 'delete': {
      if (!tenantId) throw new Error('tenantId required');
      const ok = tenantStore.delete(tenantId);
      if (!ok) throw new Error('Tenant not found');
      await notify('tenant.deleted', { id: tenantId });
      return { success: true, message: `Tenant ${tenantId} deleted` };
    }
  }
};
