# Voiceflow Project Setup Guide

## Prerequisites
- Voiceflow account (https://creator.voiceflow.com)
- Resend account with API key (https://resend.com/api-keys)

## Step 1: Create Voiceflow Project
1. Go to https://creator.voiceflow.com
2. Click "New Project"
3. Name: "Resend AI Agent"
4. Language: English (US)
5. Create project

## Step 2: Configure Environment Variables
In Voiceflow project settings → Environment Variables:
```
RESEND_API_KEY=re_your_actual_api_key_here
VOICEFLOW_API_KEY=vf_your_voiceflow_api_key
VOICEFLOW_PROJECT_ID=your_project_id
WEBHOOK_URL=https://wh34c025ff0874a90e2f.free.beeceptor.com/
```

## Step 3: Import Intents
1. Go to Intents section
2. Click "Import" or create manually from `intents.json`
3. Create 7 intents:
   - `send_email` (with entities: to_email, from_email, email_subject, html_content, text_content, reply_to, email_tags, content_type, scheduled_at)
   - `check_email_status` (entities: email_id)
   - `list_emails` (entities: limit, from_date, to_date, status)
   - `verify_domain` (entities: domain_name)
   - `manage_contacts` (entities: action, contact_audience_id, contact_email, contact_first_name, contact_last_name, contact_unsubscribed)
   - `help` (no entities)
   - `fallback` (no entities)

## Step 4: Import Entities
1. Go to Entities section
2. Create 17 entities from `entities.json`:
   - `to_email` (regex: email format)
   - `from_email` (regex: email format)
   - `email_subject` (custom)
   - `html_content` (custom)
   - `text_content` (custom)
   - `reply_to` (regex: email format)
   - `email_tags` (custom)
   - `content_type` (custom: html, text, both)
   - `scheduled_at` (datetime)
   - `email_id` (regex: UUID)
   - `limit` (number: 1-100)
   - `from_date` (datetime)
   - `to_date` (datetime)
   - `status` (custom: delivered, bounced, complained, sent)
   - `domain_name` (regex: domain format)
   - `action` (custom: add, update, unsubscribe)
   - `contact_audience_id` (regex: UUID)
   - `contact_email` (regex: email format)
   - `contact_first_name` (custom)
   - `contact_last_name` (custom)
   - `contact_unsubscribed` (boolean)

## Step 5: Create Functions
1. Go to Functions section
2. Create 5 functions, copy code from `/functions/*.js`:
   - `sendEmail` - paste `sendEmail.js`
   - `getEmailStatus` - paste `getEmailStatus.js`
   - `listEmails` - paste `listEmails.js`
   - `verifyDomain` - paste `verifyDomain.js`
   - `manageContacts` - paste `manageContacts.js`

## Step 6: Create Flows
1. Go to Flows section
2. Create 8 flows from JSON files:
   - `Main Flow` - from `main.flow.json`
   - `Send Email` - from `send_email.json`
   - `Check Email Status` - from `check_email_status.json`
   - `List Emails` - from `list_emails.json`
   - `Verify Domain` - from `verify_domain.json`
   - `Manage Contacts` - from `manage_contacts.json`
   - `Help` - from `help.json`
   - `Fallback` - from `fallback.json`

3. For each flow, recreate the nodes manually or use Voiceflow's import if available

## Step 7: Connect Main Flow
1. Open `Main Flow`
2. Ensure intent step routes to correct sub-flows
3. Set Main Flow as entry point

## Step 8: Test in Preview
1. Click "Preview" button
2. Test conversations:
   - "Send email to test@example.com subject Test html <p>Hello</p>"
   - "Check status of email 12345678-1234-1234-1234-123456789012"
   - "List emails"
   - "Verify domain example.com"
   - "Add contact user@test.com to audience abc-def"
   - "Help"
   - "Unknown command" (tests fallback)

## Step 9: Deploy
1. Click "Publish" → "Deploy"
2. Note the Dialog API endpoint
3. Test with Dialog API if needed

## Webhook Integration (Resend Events)
In Resend Dashboard → Webhooks:
1. Add webhook: `https://wh34c025ff0874a90e2f.free.beeceptor.com/`
2. Select events: email.sent, email.delivered, email.bounced, email.complained, email.opened, email.clicked
3. Webhook will receive events and can trigger Voiceflow Dialog API

## Dialog API Usage
```bash
curl -X POST https://api.voiceflow.com/v2/dialogs \
  -H "Authorization: Bearer ${VOICEFLOW_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "projectID": "'${VOICEFLOW_PROJECT_ID}'",
    "userID": "user123",
    "request": {"type": "text", "payload": "Send email to john@example.com subject Hello"}
  }'
```

## Troubleshooting
| Issue | Solution |
|-------|----------|
| "Authentication failed" | Check RESEND_API_KEY in environment variables |
| "Function not found" | Verify function names match exactly (case-sensitive) |
| "Entity not recognized" | Check entity names in intents match entity definitions |
| "Flow not triggered" | Verify intent training phrases and entity mapping |
| Network error | Check internet connectivity, Resend API status |

## Testing Checklist
- [ ] Send email with HTML content
- [ ] Send email with text content
- [ ] Send email with both HTML and text
- [ ] Send email with reply-to
- [ ] Send email with tags
- [ ] Send scheduled email
- [ ] Check status of delivered email
- [ ] Check status of bounced email
- [ ] List emails with no filters
- [ ] List emails with date filter
- [ ] List emails with status filter
- [ ] Verify new domain
- [ ] Add contact to audience
- [ ] Update contact
- [ ] Unsubscribe contact
- [ ] Help command works
- [ ] Fallback triggers for unknown input
