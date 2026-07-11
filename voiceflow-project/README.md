# Resend AI Agent - Voiceflow Project

## Overview
Voiceflow agent for sending and managing transactional/marketing emails via Resend API.

## Project Structure
```
voiceflow-project/
├── project.json           # Project configuration
├── intents.json           # Intent definitions
├── entities.json          # Entity definitions
├── flows/
│   ├── main.flow.json         # Entry point
│   ├── send_email.json        # Send email flow
│   ├── check_email_status.json # Check delivery status
│   ├── list_emails.json       # List emails with filters
│   ├── verify_domain.json     # Domain verification
│   ├── manage_contacts.json   # Audience contact management
│   ├── help.json              # Help command
│   └── fallback.json          # Fallback handler
├── functions/
│   ├── sendEmail.js           # POST /emails
│   ├── getEmailStatus.js      # GET /emails/{id}
│   ├── listEmails.js          # GET /emails
│   ├── verifyDomain.js        # POST /domains
│   └── manageContacts.js      # POST/PATCH /audiences/{id}/contacts
└── docs/
    └── setup.md               # Setup instructions
```

## Quick Start

### 1. Create Voiceflow Project
- Go to https://creator.voiceflow.com
- Create new project: "Resend AI Agent"
- Import the project structure

### 2. Configure Environment Variables
In Voiceflow project settings, add:
```
RESEND_API_KEY=re_your_api_key_here
```
Get API key from https://resend.com/api-keys

### 3. Import Functions
Copy each function file to Voiceflow Functions section:
- `functions/sendEmail.js`
- `functions/getEmailStatus.js`
- `functions/listEmails.js`
- `functions/verifyDomain.js`
- `functions/manageContacts.js`

### 4. Import Intents & Entities
- Copy `intents.json` to Intents
- Copy `entities.json` to Entities

### 5. Import Flows
Copy each flow file to Flows section.

### 6. Test
- Use Voiceflow Preview
- Test with: "Send email to test@example.com subject Test html <p>Hello</p>"

## Webhook Integration
Webhook endpoint: `https://wh34c025ff0874a90e2f.free.beeceptor.com/`
- Configure in Resend dashboard for email events
- Can trigger Voiceflow Dialog API for proactive notifications

## API Endpoints Used
| Function | Resend Endpoint | Method |
|----------|-----------------|--------|
| sendEmail | /emails | POST |
| getEmailStatus | /emails/{id} | GET |
| listEmails | /emails | GET |
| verifyDomain | /domains | POST |
| manageContacts | /audiences/{id}/contacts | POST/PATCH |

## Example Conversations

### Send Email
```
User: Send email to john@example.com subject Welcome html <h1>Hello!</h1>
Agent: From email? (optional)
User: onboarding@myapp.com
Agent: Send email to john@example.com with subject 'Welcome'?
User: Yes
Agent: ✅ Email sent! Email ID: abc123-def456
```

### Check Status
```
User: Check status of email abc123-def456
Agent: 📧 Email Status: abc123-def456
Status: delivered
Created: 2024-01-15T10:30:00Z
Sent: 2024-01-15T10:30:01Z
Delivered: 2024-01-15T10:30:02Z
```

### Verify Domain
```
User: Verify domain example.com
Agent: ✅ Domain verification initiated!
Add these DNS records:
TXT | _resend.example.com | resend-verification=abc123
MX  | @                   | 10 feedback-smtp.us-east-1.amazonses.com
```

## Error Handling
- Invalid API key → "Authentication failed"
- Network error → "Unable to connect to Resend API"
- Invalid email → "Invalid email format"
- Rate limited → "Too many requests, please wait"

## Next Steps (Week 1)
- Day 2: Voiceflow Dialog API integration
- Day 3: Email templates management
- Day 4: Resend webhook handling
- Day 5: Audience management
- Day 6: Batch email sending
- Day 7: Testing & retrospective
