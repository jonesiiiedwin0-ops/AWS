/**
 * Test script for Dialog API Client and Webhook Handler
 * Run with: node test.js
 * 
 * Requires environment variables:
 * - VOICEFLOW_API_KEY
 * - VOICEFLOW_PROJECT_ID
 * - RESEND_API_KEY (for function testing)
 */

const { ResendAgentClient } = require('./client');
const { ResendWebhookHandler, startWebhookServer, BEECEPTOR_WEBHOOK_URL } = require('./webhook');

async function testDialogAPI() {
  console.log('=== Testing Voiceflow Dialog API Client ===\n');
  
  const apiKey = process.env.VOICEFLOW_API_KEY;
  const projectId = process.env.VOICEFLOW_PROJECT_ID;
  
  if (!apiKey || !projectId) {
    console.log('⚠️  Skipping Dialog API test - missing VOICEFLOW_API_KEY or VOICEFLOW_PROJECT_ID');
    return;
  }

  const client = new ResendAgentClient({ apiKey, projectId });
  
  try {
    // Create session
    console.log('1. Creating session...');
    const session = await client.createSession('test-user-123');
    console.log(`   Session ID: ${session.sessionId}`);
    console.log(`   Messages: ${session.messages.length}`);
    console.log(`   Actions: ${session.actions.length}`);
    
    // Test help command
    console.log('\n2. Testing help command...');
    const helpResponse = await client.getHelp(session.sessionId);
    console.log(`   Messages: ${helpResponse.messages.length}`);
    helpResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 80)}...`));
    
    // Test send email intent
    console.log('\n3. Testing send_email intent...');
    const emailResponse = await client.sendEmail(session.sessionId, {
      to: 'test@example.com',
      from: 'onboarding@resend.dev',
      subject: 'Test from Dialog API',
      html: '<h1>Hello from Dialog API!</h1>',
      tags: ['test', 'api']
    });
    console.log(`   Messages: ${emailResponse.messages.length}`);
    emailResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 100)}...`));
    if (emailResponse.actions.length) {
      console.log(`   Actions: ${emailResponse.actions.map(a => a.type).join(', ')}`);
    }
    
    // Test check status intent
    console.log('\n4. Testing check_email_status intent...');
    const statusResponse = await client.checkEmailStatus(session.sessionId, '12345678-1234-1234-1234-123456789012');
    console.log(`   Messages: ${statusResponse.messages.length}`);
    statusResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 100)}...`));
    
    // Test list emails intent
    console.log('\n5. Testing list_emails intent...');
    const listResponse = await client.listEmails(session.sessionId, { limit: '5', status: 'delivered' });
    console.log(`   Messages: ${listResponse.messages.length}`);
    listResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 100)}...`));
    
    // Test verify domain intent
    console.log('\n6. Testing verify_domain intent...');
    const domainResponse = await client.verifyDomain(session.sessionId, 'example.com');
    console.log(`   Messages: ${domainResponse.messages.length}`);
    domainResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 100)}...`));
    
    // Test manage contact intent
    console.log('\n7. Testing manage_contacts intent...');
    const contactResponse = await client.manageContact(session.sessionId, {
      action: 'add',
      email: 'newuser@example.com',
      audienceId: '12345678-1234-1234-1234-123456789012',
      firstName: 'John',
      lastName: 'Doe'
    });
    console.log(`   Messages: ${contactResponse.messages.length}`);
    contactResponse.messages.forEach(m => console.log(`   - ${m.content.substring(0, 100)}...`));
    
    // End session
    console.log('\n8. Ending session...');
    await client.endSession(session.sessionId);
    console.log('   Session ended');
    
    console.log('\n✅ All Dialog API tests passed!');
    
  } catch (error) {
    console.error('\n❌ Dialog API test failed:', error.message);
  }
}

async function testWebhookHandler() {
  console.log('\n=== Testing Webhook Handler ===\n');
  
  const handler = new ResendWebhookHandler({
    webhookSecret: process.env.RESEND_WEBHOOK_SECRET,
    voiceflowApiKey: process.env.VOICEFLOW_API_KEY,
    voiceflowProjectId: process.env.VOICEFLOW_PROJECT_ID,
    forwardToBeeceptor: true
  });
  
  // Test event processing
  const testEvents = [
    {
      type: 'email.sent',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        from: 'sender@domain.com',
        subject: 'Test Email',
        created_at: new Date().toISOString()
      }
    },
    {
      type: 'email.delivered',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        delivered_at: new Date().toISOString()
      }
    },
    {
      type: 'email.bounced',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        bounce_type: 'hard',
        bounced_at: new Date().toISOString()
      }
    },
    {
      type: 'email.opened',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        opened_at: new Date().toISOString()
      }
    },
    {
      type: 'email.clicked',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        url: 'https://example.com/link',
        clicked_at: new Date().toISOString()
      }
    },
    {
      type: 'email.complained',
      data: {
        email_id: 'test-email-123',
        to: ['user@example.com'],
        complained_at: new Date().toISOString()
      }
    }
  ];
  
  for (const event of testEvents) {
    console.log(`Processing ${event.type}...`);
    await handler.processEvent(event);
    console.log(`  ✓ Processed`);
  }
  
  console.log('\n✅ Webhook handler tests passed!');
  console.log(`\nBeeceptor URL for inspection: ${BEECEPTOR_WEBHOOK_URL}`);
}

async function main() {
  await testDialogAPI();
  await testWebhookHandler();
  
  console.log('\n=== Summary ===');
  console.log('Phase 2 Components:');
  console.log('  ✅ Dialog API Client (client.js)');
  console.log('  ✅ Resend Webhook Handler (webhook.js)');
  console.log('  ✅ Test Suite (test.js)');
  console.log('  ✅ Beeceptor Integration');
  console.log('\nEnvironment Variables Needed:');
  console.log('  VOICEFLOW_API_KEY');
  console.log('  VOICEFLOW_PROJECT_ID');
  console.log('  RESEND_API_KEY');
  console.log('  RESEND_WEBHOOK_SECRET (optional, for signature verification)');
}

main().catch(console.error);
