# Security Guide

## Threat Model

This is a multi-agent OS with browser automation and terminal execution.
The attack surface includes: prompt injection, SSRF, command injection, credential leakage.

## Terminal Execution Safety

- Allowlist enforced in `backend/app/runtime/executor.py`
- No arbitrary shell access via API
- Command timeout enforced (default 10s)
- Output size capped
- Audit trail in SQLite memory

## Browser Automation Safety

- Domain allowlist should be configured before production use
- Never store raw credentials in browser session snapshots
- Session state files encrypted at rest (TODO: implement at-rest encryption)
- Screenshots stored locally; clear sensitive screenshots periodically
- No unreviewed JS execution in production mode

## API Security

- CORS: set `ALLOWED_ORIGINS` in production (currently `*` — change this)
- Rate limiting: not implemented — add via nginx/reverse proxy in production
- Auth: no user auth in current version — add API key or OAuth before public exposure
- Secrets: load from env vars only; never log env values

## Credentials Handling

- All credentials loaded from `.env` or environment only
- `.env` is gitignored
- Never commit `.env` — only `.env.example` with blank values
- Bounty platform credentials scoped to env vars; not stored in DB

## Guardrails

- Soul quality gate rejects low-quality or potentially harmful outputs
- Warden agent reviews high-value/dangerous operations
- Approval gate UI for high-risk tasks
- `GUARDRAILS_STRICT=true` enables strict mode

## Production Checklist

- [ ] Change CORS `allow_origins` from `["*"]` to your domain
- [ ] Add API authentication (e.g., API key header or OAuth)
- [ ] Set up nginx reverse proxy with rate limiting
- [ ] Enable HTTPS (Render/Railway handle this automatically)
- [ ] Set `SUPREME_ALLOW_TERMINAL=false` if terminal is not needed
- [ ] Rotate `STRIPE_SECRET_KEY` and other sensitive keys regularly
- [ ] Review and tighten terminal allowlist for your use case
- [ ] Store browser session state in encrypted form
- [ ] Set up log monitoring (the `/logs` endpoint exposes events)
