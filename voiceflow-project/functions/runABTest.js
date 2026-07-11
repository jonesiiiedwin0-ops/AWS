/**
 * Voiceflow Function: runABTest
 * Sends variant A / variant B emails to two audience segments and tracks results.
 *
 * Resend does not have a native A/B test API, so we split recipients and
 * send each variant, then forward each send event to the webhook for tracking.
 *
 * Environment Variables Required:
 * - RESEND_API_KEY: Your Resend API key
 */

const fetch = require('node-fetch');

const BEECEPTOR_WEBHOOK_URL = 'https://wh34c025ff0874a90e2f.free.beeceptor.com/';

module.exports = async function runABTest({
  subjectA,
  htmlA,
  textA,
  subjectB,
  htmlB,
  textB,
  from,
  recipientsA = [],   // array of emails for variant A
  recipientsB = [],   // array of emails for variant B
  tags = [],
  testName = 'untitled_ab_test'
}) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error('RESEND_API_KEY environment variable not set');

  if (!subjectA || !subjectB) throw new Error('subjectA and subjectB are required');
  if (!htmlA && !textA) throw new Error('htmlA or textA required for variant A');
  if (!htmlB && !textB) throw new Error('htmlB or textB required for variant B');
  if (!from) throw new Error('from address is required');
  if (!Array.isArray(recipientsA) || recipientsA.length === 0) throw new Error('recipientsA array required');
  if (!Array.isArray(recipientsB) || recipientsB.length === 0) throw new Error('recipientsB array required');

  const result = {
    testName,
    variantA: { sent: 0, recipients: recipientsA.length, emailIds: [] },
    variantB: { sent: 0, recipients: recipientsB.length, emailIds: [] },
    errors: []
  };

  const sendVariant = async (subject, html, text, recipients, variantKey) => {
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
            tags: [...tags, 'ab_test', testName, variantKey].map(t => ({ name: t }))
          })
        });
        const data = await resp.json();
        if (!resp.ok) {
          result.errors.push({ to, error: data.message || resp.status });
          continue;
        }
        result[variantKey].sent++;
        result[variantKey].emailIds.push(data.id);

        // Forward to webhook for tracking
        await fetch(BEECEPTOR_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Resend-Event': 'email.sent', 'X-AB-Test': testName, 'X-Variant': variantKey },
          body: JSON.stringify({
            type: 'email.sent',
            data: { email_id: data.id, to, subject, variant: variantKey, ab_test: testName },
            timestamp: new Date().toISOString()
          })
        }).catch(() => {});
      } catch (e) {
        result.errors.push({ to, error: e.message });
      }
    }
  };

  await sendVariant(subjectA, htmlA, textA, recipientsA, 'variantA');
  await sendVariant(subjectB, htmlB, textB, recipientsB, 'variantB');

  // Notify webhook that the A/B test has launched
  await fetch(BEECEPTOR_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Resend-Event': 'ab_test.launched' },
    body: JSON.stringify({
      type: 'ab_test.launched',
      data: result,
      timestamp: new Date().toISOString()
    })
  }).catch(() => {});

  result.success = result.errors.length === 0;
  result.message = `A/B test "${testName}" launched: A sent ${result.variantA.sent}/${result.variantA.recipients}, B sent ${result.variantB.sent}/${result.variantB.recipients}`;
  return result;
};
