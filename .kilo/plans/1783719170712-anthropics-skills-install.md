# 1783719170712-anthropics-skills-install.md

## Goal
Install all public skill files (`*.md` with YAML metadata) from Anthropic GitHub repositories into the Kilo system.

## Features
- Recursively search Anthropic organization repositories
- Identify markdown files with `skills:` YAML header
- Clone repositories securely
- Validate YAML format and metadata structure
- Add skills to system via Kilo's configuration workflow
- Generate migration manifest for version tracking
- Deploy update using cloud-agent validation loop

## Scope
- All public repositories under `github.com/orgs/anthropics`
- Markdown files ending with `.md`
- Files containing YAML frontmatter where `skills:` key exists
- Zero external dependencies required

## Detailed Task List
1. Identify Repositories
   - Search GitHub for Anthropic org repos (91 total)
   - Filter repositories containing `*.md` with `skills:` in YAML header

2. Clone Repositories
   - Use secure HTTPS cloning without credentials
   - Parallel fetch limited to 5 concurrent repositories

3. Extract Skills
   - Glob pattern: `**/*.md`
   - YAML validation via `/task cloud-agent` sanity checks
   - Path resolution: repository root → skill directory

4. Validate Skills
   - Verify YAML structure contains `name`, `description`, `version`
   - Confirm no secret leakage via `/grep` scan for `['"]{API,KEY,SECRET}`
   - Check compatibility with current Kilo version via `/task cloud-agent` lint

5. Upload Process
   - Create `.kilo/skills` directory if absent
   - Append each validated skill to `.kilo/skills` manifest
   - Update `.kilo/config` with latest skill registry entries
   - Run `/task cloud-agent` validation suite

6. Post-Deployment
   - Generate migration manifest listing added/updated skills
   - Run end-to-end test using `/task cloud-agent` functional guard
   - Notify user of successful installation via system log

## Risks & Mitigations
- **Dependency Conflicts**: Validate versions against existing skill registry before upload
- **Repository Rate Limits**: Cache repository clones to avoid repeated fetches
- **Schema Drift**: Enforce strict YAML schema validation using `/task cloud-agent` validator
- **Security Exposure**: Scan all cloned content for secrets before processing

## Dependencies
- `/task cloud-agent` for validation and installation
- `/skill cloud-agent` for skill-specific processing logic
- `/plan_exit` to finalize execution