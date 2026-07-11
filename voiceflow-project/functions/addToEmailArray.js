/**
 * Voiceflow Function: addToEmailArray
 * Helper to add email objects to a JSON array string
 * Used by send_batch flow
 */

module.exports = async function addToEmailArray({ 
  emailsJson, 
  to, 
  from, 
  subject, 
  html, 
  text, 
  replyTo, 
  tags 
}) {
  let emails = [];
  try {
    emails = JSON.parse(emailsJson || '[]');
  } catch (e) {
    emails = [];
  }

  const emailObj = {
    to,
    from,
    subject,
    html,
    text,
    ...(replyTo && { replyTo }),
    ...(tags && { tags: tags.split(',').map(t => t.trim()) })
  };

  emails.push(emailObj);

  return {
    emailsJson: JSON.stringify(emails)
  };
};
