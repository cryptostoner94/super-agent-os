# Architecture

Supreme AI Agent OS is structured around:

- Backend API: FastAPI
- Frontend: Streamlit first draft
- Provider Router: Grok/XAI → Gemini → Bedrock → OpenAI → extra fallbacks
- Agent Registry: Executive, Builder, Terminal, Researcher, Browser, Finance
- Runtime Executor: safe terminal execution with blocked destructive commands
- Artifact Factory: Markdown, HTML, XLSX, CSV
- Connector Status: capability-gated integrations
- Memory Store: local JSON state, designed to evolve into Supabase + vector memory

## Why this structure

It avoids mixing all logic into one file and gives a clean GitHub-ready base for iterative improvement.
