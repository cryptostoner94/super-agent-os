# Supreme AI Agent OS

A GitHub-ready first-draft repository for a Manus-inspired, self-hosted Super AI Agent workspace.

This repository is designed to run on an EC2/VPS server and provide:

- FastAPI backend
- Streamlit web workspace
- Provider router with fallback order: **Grok/XAI → Gemini → Amazon Bedrock → OpenAI**
- Support for extra providers already seen in your `.env`: Groq, OpenRouter, Together, Fireworks
- Capability-gated modules: modules appear only when required `.env` keys exist
- Safe remote terminal execution
- Agent registry
- Skills registry
- Artifact factory: Markdown, HTML, CSV, XLSX, DOCX, PDF fallback where available
- Library/state storage
- Logs and health checks
- GitHub-ready structure
- Deployment scripts

## Important honesty note

This is a strong working first-draft repo scaffold and runtime foundation. It is not a full commercial Manus clone. Real Gmail, Drive, Calendar, Skyvern, OpenClaw, Slack, and GitHub actions require valid keys/OAuth setup and provider-specific permissions.

## Quick Start on EC2

```bash
unzip supreme-ai-agent-os.zip
cd supreme-ai-agent-os
cp .env.example .env
nano .env
bash scripts/install.sh
bash scripts/run.sh
```

Open:

```text
http://YOUR_SERVER_IP:8501
```

API:

```text
http://YOUR_SERVER_IP:8000/health
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial Supreme AI Agent OS repo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/supreme-ai-agent-os.git
git push -u origin main
```

## Updating after changes

```bash
bash scripts/git_push_update.sh "describe your change"
```
