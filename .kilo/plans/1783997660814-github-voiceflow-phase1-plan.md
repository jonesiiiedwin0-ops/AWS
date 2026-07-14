# GitHub Agent on Voiceflow — Phase 1 Plan

## 1. Vision & Scope
- **Long-term vision:** A Voiceflow-built conversational/voice agent that can act across **everything on GitHub** (issues, PRs, code search, workflows, releases, etc.).
- **Phase 1 (this plan):** Ship a **monetizable MVP wedge** that proves the architecture and the willingness to pay. Later phases (2–1000) iteratively extend capabilities toward the full "everything on GitHub" vision.
- **Phase 1 wedge decision (delegated):** Freemium SaaS deployed on **web chat embed + Slack**, offering two high-value, low-risk capabilities: **Repo Q&A** and **Issue/PR triage + summarization**.

## 2. Goals (success metrics)
- **Activation:** % of signed-up users who connect ≥1 repo and complete ≥1 successful query within 7 days.
- **Paid conversion:** % of free users who upgrade to Pro within 30 days.
- **Cost guardrail:** Blended LLM + infra cost per active free user must stay below free-tier margin.

## 3. Architecture
| Layer | Responsibility |
|-------|----------------|
| **Voiceflow project** | Conversation design, NLU via AI steps, slots (`repo_id`, `intent`), GitHub OAuth handshake, calls backend through API/custom-action steps. |
| **Backend agent service** | Python **FastAPI** exposing `/ask` and `/triage`. GitHub REST/GraphQL client (rate-limit aware), provider-agnostic LLM wrapper for Q&A + summaries. |
| **Auth** | **GitHub OAuth App** → encrypted user access token stored keyed by `user_id`. |
| **Data** | Usage/quota tracking for freemium tiers (reuse **AWS DynamoDB** from the existing AWS MCP Server repo where sensible). |
| **Billing** | **Stripe** checkout. Free tier (1 repo, N queries/month, web only) vs Pro (unlimited repos, Slack, advanced triage, priority). |
| **LLM** | Provider-agnostic wrapper; prefer Voiceflow built-in AI steps to cut cost where possible, fall back to external LLM for GitHub-content-heavy tasks. Default provider TBD (see open decisions). |

## 4. Task List (ordered)
1. **Product spec + success metrics** — define activation and paid-conversion targets; write PRD for Phase 1 wedge.
2. **Scaffold Voiceflow project** — intents, auth handshake flow, slots (`repo_id`, `intent`), response templates, error handling.
3. **GitHub OAuth App + token storage** — register OAuth App, implement encrypted token persistence keyed by `user_id` (KMS/Secrets Manager).
4. **Backend agent service (FastAPI)** — implement `/ask` (repo Q&A) and `/triage` (issue/PR label/summarize/route), GitHub API client with retry + rate-limit handling, LLM wrapper.
5. **Wire Voiceflow ↔ backend** — API/custom-action steps call backend endpoints; pass OAuth token + repo context securely.
6. **Freemium quota + Stripe billing** — enforce per-tier usage limits; Stripe checkout + webhook for plan changes.
7. **Deploy + publish** — containerize backend (reuse AWS infra), deploy; publish web embed snippet and Slack app.
8. **Analytics + landing page** — instrument usage/conversion events; simple marketing page with embed.
9. **Validate** — dogfood on a public test repo; measure activation + first paying user.

## 5. Risks
- **GitHub API rate limits** — mitigate with token scoping, caching, and backoff.
- **LLM cost vs freemium margin** — cap tokens/query, cache embeddings, prefer Voiceflow AI steps.
- **Voiceflow custom-action latency** — keep backend responses fast; stream where possible.
- **OAuth token security/compliance** — encrypt at rest, least-privilege scopes, easy revoke.

## 6. Validation Plan
- Unit + integration tests for `/ask` and `/triage` (mock GitHub + LLM).
- Quota enforcement test (free tier hard stop at N queries).
- End-to-end test inside Voiceflow (web + Slack).
- Manual dogfood on a public repo; track activation + first paid conversion.

## 7. Open Decisions (resolve in implementation)
- LLM provider (start with one; keep wrapper provider-agnostic).
- Exact pricing tiers and free-query cap N.
- DB choice: DynamoDB (reuse existing AWS repo) vs managed Postgres.
- Whether to reuse the existing AWS MCP Server as the hosting/runtime base or stand up a separate service.
