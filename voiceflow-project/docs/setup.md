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
RESEND_WEBHOOK_SECRET=your_webhook_secret (optional)
```

## Step 3: Import Intents
Go to Intents section, create 7 intents from `intents.json`:
- `send_email` (entities: to_email, from_email, email_subject, html_content, text_content, reply_to, email_tags, content_type, scheduled_at)
- `check_email_status` (entities: email_id)
- `list_emails` (entities: limit, from_date, to_date, status)
- `verify_domain` (entities: domain_name)
- `manage_contacts` (entities: action, contact_email, contact_audience_id, contact_first_name, contact_last_name, contact_unsubscribed)
- `manage_templates` (entities: template_action, template_name, template_subject, template_html, template_text, template_variables, template_id, send_to, send_from, send_variables, update_field, update_value)
- `help` (no entities)
- `fallback` (no entities)

## Step 4: Import Entities
Go to Entities section, create 43 entities from `entities.json`:
- Email regex entities: to_email, from_email, reply_to, send_to, send_from, send_reply_to, contact_email
- UUID regex: email_id, contact_audience_id
- Domain regex: domain_name
- Template ID regex: template_id
- Custom: email_subject, html_content, text_content, email_tags, content_type, scheduled_at, limit, from_date, to_date, status, domain_name, action, contact_first_name, contact_last_name, contact_unsubscribed, template_action, template_name, template_subject, template_html, template_text, template_variables, send_tags, send_variables, update_field, update_value

## Step 5: Create Functions
Go to Functions section, create 6 functions:

### sendEmail
Copy code from `functions/sendEmail.js`

### getEmailStatus
Copy code from `functions/getEmailStatus.js`

### listEmails
Copy code from `functions/listEmails.js`

### verifyDomain
Copy code from `functions/verifyDomain.js`

### manageContacts
Copy code from `functions/manageContacts.js`

### manageTemplates
Copy code from `functions/manageTemplates.js`

## Step 6: Create Flows
Go to Flows section, create 9 flows:

1. **Main Flow** - from `flows/main.flow.json` (set as entry point)
2. **Send Email** - from `flows/send_email.json`
3. **Check Email Status** - from `flows/check_email_status.json`
4. **List Emails** - from `flows/list_emails.json`
5. **Verify Domain** - from `flows/verify_domain.json`
6. **Manage Contacts** - from `flows/manage_contacts.json`
7. **Manage Templates** - from `flows/manage_templates.json`
8. **Help** - from `flows/help.json`
9. **Fallback** - from `flows/fallback.json`

## Step 7: Connect Main Flow
1. Open Main Flow
2. Ensure intent step routes to correct sub-flows
3. Set Main Flow as entry point

## Step 8: Test in Preview
Click "Preview" and test:
- "Send email to test@example.com subject Test html <p>Hello</p>"
- "Check status of email 12345678-1234-1234-1234-123456789012"
- "List emails"
- "Verify domain example.com"
- "Add contact user@test.com to audience abc-def"
- "Create template welcome subject Welcome {{name}} html <h1>Hi {{name}}</h1>"
- "List templates"
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
3. Webhook will receive events and forward to Beeceptor for inspection

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

## Project Structure
```
voiceflow-project/
├── project.json              # Project configuration
├── intents.json              # 7 intent definitions
├── entities.json             # 43 entity definitions
├── functions/                # 6 Resend API functions
│   ├── sendEmail.js
│   ├── getEmailStatus.js
│   ├── listEmails.js
│   ├── verifyDomain.js
│   ├── manageContacts.js
│   └── manageTemplates.js
├── flows/                    # 9 Voiceflow flows
│   ├── main.flow.json
│   ├── send_email.json
│   ├── check_email_status.json
│   ├── list_emails.json
│   ├── verify_domain.json
│   ├── manage_contacts.json
│   ├── manage_templates.json
│   ├── help.json
│   └── fallback.json
└── dialog-api/               # Dialog API client & webhook handler
    ├── client.js
    ├── webhook.js
    └── test.js
```

## API Endpoints Used
| Function | Resend Endpoint | Method |
|----------|----------------|--------|
| sendEmail | /emails | POST |
| getEmailStatus | /emails/{id} | GET |
| listEmails | /emails | GET |
| verifyDomain | /domains | POST |
| manageContacts | /audiences/{id}/contacts | POST/PATCH |
| manageTemplates | Local storage + /emails | POST |

## Template System
Templates use `{{variable}}` syntax for placeholders:
- Create: `html: "<h1>Hello {{name}}!</h1>", variables: "name,company"`
- Send: `data: {"name": "John", "company": "Acme"}`
- Renders to: `<h1>Hello John!</h1>`

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
- [ ] Create template with variables
- [ ] List templates
- [ ] Send email from template
- [ ] View template details
- [ ] Update template
- [ ] Delete template
- [ ] Help command works
- [ ] Fallback triggers for unknown input

## Next Steps (Week 1)
- Day 2: Voiceflow Dialog API integration ✅
- Day 3: Email templates management ✅
- Day 4: Resend webhook handling (webhook.js)
- Day 5: Audience management
- Day 6: Batch email sending
- Day 7: Testing & retrospective
