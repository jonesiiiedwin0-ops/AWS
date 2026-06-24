# Strategy: How AWS MCP Server Becomes a Top-Tier (100k★+) Open-Source Project

> A long-range, honest roadmap. Star counts are a *lagging indicator* of real
> value — they follow utility, trust, and distribution. This document outlines
> what has to be true for that to happen, in priority order.

---

## 0. The honest starting point

This repository now ships a **real MCP server** with working, read-only tools
for Amazon S3, EC2, Lambda, and CloudWatch — built on the official `mcp` SDK and
covered by a `moto`-backed test suite that needs no AWS account. That is the first install of
the "ship something real" principle below: a narrow, genuinely useful slice that
beats vaporware. Everything else assumes we keep earning attention with
substance — more services, sharper safety rails, and shorter time-to-value —
rather than marketing.

Repos that have crossed 100k stars (e.g. `freeCodeCamp`, `vscode`,
`tensorflow`, `kubernetes`, `ollama`) share a pattern: **a sharp problem, a
gentle on-ramp, relentless reliability, and a community that compounds.** We
copy the pattern, not the marketing.

---

## 1. Pillars that have to be true

### Pillar 1 — Solve one painful problem exceptionally well
- **Wedge:** "Give any MCP-capable AI client safe, read-first access to a real
  AWS account in under 5 minutes." Narrow beats broad.
- Resist the urge to support all 200+ AWS services on day one. Ship S3, EC2,
  Lambda, CloudWatch, Cost Explorer — the five people actually ask an AI about.
- Be *measurably* better: latency, safety rails, and a setup that genuinely
  takes minutes.

### Pillar 2 — Time-to-first-success under 5 minutes
- `pipx install` / `uvx` / Docker one-liner that works with zero code.
- A guided `--setup` flow that validates AWS credentials and prints exactly
  which IAM permissions are missing.
- A read-only demo mode against a public/sample account so people can try it
  with no risk.

### Pillar 3 — Trust and safety as a feature, not a footnote
- **Read-only by default.** Mutating actions require an explicit opt-in flag
  and per-action confirmation. This is the #1 reason teams will adopt an
  AI↔cloud bridge.
- Least-privilege IAM policy generator shipped in-repo.
- Audit logging of every call. No silent writes, ever.
- Published threat model + a security policy with a real disclosure path.

### Pillar 4 — Reliability you can stake production on
- >90% test coverage, contract tests against `moto`/LocalStack so CI needs no
  real AWS account.
- Semantic-versioned releases, a changelog, and a deprecation policy.
- Green CI badge that means something: lint, type-check, tests, and a security
  scan on every PR.

### Pillar 5 — Documentation as a first-class product
- A docs site (not just a README): quickstart, per-service guides, recipes,
  and an API reference generated from code.
- Every feature ships with a runnable example.
- "Cookbook" of real tasks: *"ask Claude to find your largest S3 buckets and
  estimate their monthly cost."*

### Pillar 6 — Distribution and community compounding
- Listed in the official MCP server registries and "awesome-mcp" lists.
- One-click configs for the popular MCP clients (Claude Desktop, IDE
  extensions, etc.).
- Good-first-issue funnel, fast PR review SLA, visible roadmap, and
  contributor recognition.

---

## 2. Phased roadmap

| Phase | Goal | Definition of done | Star horizon* |
|------:|------|--------------------|--------------:|
| **0. Foundation** ✅ | Real, installable skeleton + clean repo | Working server stub, CI, tests, contributor docs | 0–100 |
| **1. MVP** 🚧 | 5 services, read-only, <5-min setup | Real MCP server with live S3 + EC2 + Lambda + CloudWatch read-only tools (moto-tested); Cost Explorer next; demo video | 100–1k |
| **2. Trust** | Safety rails + audit + IAM generator | Threat model published; mutating ops gated; security policy | 1k–5k |
| **3. Reach** | Docs site + registry listings + client configs | Listed in MCP registries; docs site live; 20+ recipes | 5k–25k |
| **4. Depth** | 25+ services, plugins, performance | Plugin API; benchmarks published; enterprise auth (SSO/roles) | 25k–60k |
| **5. Platform** | Ecosystem + governance | Third-party extensions; stable 1.0; governance model | 60k–100k+ |

\* *Star ranges are illustrative motivation, not promises. Stars follow value.*

---

## 3. What "outshine" actually requires (the unglamorous truths)

1. **Consistency over heroics.** Weekly releases for a year beat one viral
   launch. The compounding curve is built from steady, boring reliability.
2. **Reduce time-to-value, repeatedly.** Every friction point you remove is
   worth more than any feature you add.
3. **Earn trust before asking for adoption.** For a tool that touches a
   production cloud account, "safe by default" *is* the product.
4. **Make contributing effortless.** 100k-star repos are built by thousands of
   hands; the maintainers' real job is removing friction for contributors.
5. **Tell true stories.** Show real tasks solved end-to-end. Demos that work
   beat adjectives in a README.
6. **Measure and publish.** Latency, coverage, and adoption numbers — in the
   open — convert skeptics.

---

## 4. Anti-goals (how popular repos quietly die)

- Feature sprawl that outruns test coverage.
- A README that promises more than the code delivers (we are correcting exactly
  this today).
- Breaking changes without a deprecation path.
- Ignored issues and stale PRs.
- Treating security as something to add "later."

---

## 5. Leading metrics to watch (not stars)

- Time-to-first-successful-call (target: < 5 min, p90).
- Weekly active installs / `pip` downloads.
- Median issue first-response time (target: < 48h).
- Median PR review time (target: < 72h).
- Test coverage (target: > 90%) and CI pass rate.
- Docs page views → install conversion.

Stars are the scoreboard. These are the game.
