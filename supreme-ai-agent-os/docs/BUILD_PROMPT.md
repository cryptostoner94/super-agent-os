# Master Prompt for OpenHands / Cline / AI Coding Agent

You are taking over this repository: `supreme-ai-agent-os`.

Objective:
Transform this first-draft repo into a production-grade, Manus-inspired, self-hosted Supreme AI Agent OS.

Hard rules:
1. Do not delete working functionality.
2. Preserve `.env` values. Never commit real secrets.
3. Modules must be capability-gated: if required key is missing, hide/lock module.
4. Every backend route must be tested.
5. Every file edit must be committed to Git.
6. Terminal execution must remain guarded with blocked dangerous commands.
7. Do not fake external actions. If an API key or OAuth token is missing, show the module as locked.
8. Prefer simple reliable architecture over overcomplicated frameworks.

Provider priority:
1. XAI/Grok
2. Gemini
3. Amazon Bedrock
4. OpenAI
5. Groq/OpenRouter/Together/Fireworks fallback when configured

Build targets:
- Multi-agent orchestration
- Project workspaces
- Memory
- Connector manager
- Browser automation adapter
- Artifact generation
- Scheduled task engine
- Telegram control
- GitHub operator
- Data Lab
- Remote terminal execution
- Audit logs
- Enterprise-style settings

Current repo already includes:
- FastAPI backend
- Streamlit frontend
- Provider router
- Terminal execution guard
- Agent registry
- Skill registry
- Artifact factory
- Library/state store
- Docs and scripts

Immediate tasks:
1. Run `bash scripts/install.sh`
2. Run `bash scripts/run.sh`
3. Run `bash scripts/healthcheck.sh`
4. Run `pytest`
5. Fix any runtime errors.
6. Improve UI to be Manus/Raycast-style.
7. Add project workspace model.
8. Add persistent task run logs.
9. Add GitHub push automation.
10. Add Telegram command bridge if TELEGRAM_BOT_TOKEN exists.
11. Add Browserless Playwright adapter if BROWSERLESS_API_KEY exists.
12. Add Supabase persistence if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY exist.
13. Keep the repo deployable on EC2.

Final output expected:
- Working repo
- Passing tests
- Updated README
- Updated docs
- Clear deployment command
- No committed secrets
