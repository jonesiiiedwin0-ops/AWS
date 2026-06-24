# Security Policy

Security is a first-class feature of this project, not an afterthought. This
server can touch real cloud accounts, so we take reports seriously.

## Supported versions

The project is in early development (`0.x`). Security fixes are applied to the
latest release on the `main` branch.

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Instead, report privately via GitHub's
[private vulnerability reporting](https://github.com/jonesiiiedwin0-ops/AWS/security/advisories/new)
(Security → Report a vulnerability).

Please include:
- A description of the issue and its impact.
- Steps to reproduce or a proof of concept.
- Any suggested remediation.

We aim to acknowledge reports within **72 hours** and to provide a remediation
timeline after triage.

## Security design principles

- **Read-only by default.** Mutating actions require explicit opt-in.
- **Least privilege.** Use scoped IAM policies; never run with admin creds.
- **No secrets in the repo.** Credentials are loaded from the environment and
  `.env` is git-ignored.
- **Auditability.** Calls are logged so actions can be reviewed.
