# ⚡ Super Agent OS

**Enterprise-Grade Self-Hosted Super AI Agent Operating System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-v1.45-red.svg)](https://streamlit.io/)

## 🎯 Overview

Super Agent OS is a production-ready, enterprise-grade autonomous agent operating system designed for businesses and teams that need intelligent automation, multi-provider AI orchestration, and complete data sovereignty.

### 🌟 Key Features

- **🤖 Multi-Agent System** - Executive, Technical, Creative, and Domain-Specific Agents
- **🧠 Provider Agnostic** - Grok/XAI → Gemini → Amazon Bedrock → OpenAI (with fallbacks)
- **🔌 50+ Integrations** - GitHub, Slack, Notion, Airtable, Stripe, Google Workspace, and more
- **🛡️ Data Sovereignty** - Self-hosted, no data leaves your infrastructure
- **📊 Enterprise Dashboard** - Real-time monitoring, logs, and capabilities
- **🚀 Production Ready** - Health checks, graceful shutdown, comprehensive logging
- **⚙️ Skill Registry** - Extensible skill system for custom capabilities
- **📦 Artifact Factory** - Generate Markdown, HTML, CSV, XLSX, PDF documents
- **🔐 Security First** - Non-root execution, CORS controls, request validation
- **🎨 Modern UI** - Beautiful Streamlit interface with dark mode and animations

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Architecture](#-architecture)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Contributing](#-contributing)

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/cryptostoner94/super-agent-os.git
cd super-agent-os

# Create environment
cp .env.example .env
nano .env  # Add your API keys

# Install dependencies
bash scripts/install.sh

# Run locally
bash scripts/run.sh
```

### Docker Deployment (Recommended)

```bash
# Build and start
bash scripts/deploy.sh

# Access
# Frontend: http://localhost:8501
# API:      http://localhost:8000
```

## ⚙️ Configuration

### Environment Variables

```env
# Core Settings
SUPREME_APP_NAME=Super Agent OS
SUPREME_WORKSPACE_DIR=./data
SUPREME_ALLOW_TERMINAL=false
SUPREME_API_URL=http://127.0.0.1:8000
SUPREME_PUBLIC_URL=http://127.0.0.1:8501

# LLM Providers
OLLAMA_ENABLED=true
OLLAMA_API_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama2
OLLAMA_MODEL_2=gpt4all-mini
OLLAMA_MODEL_3=orca-mini
XAI_API_KEY=your_xai_key
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Search Providers
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key

# Integrations
GITHUB_TOKEN=your_github_token
SLACK_CLIENT_ID=your_slack_id
SLACK_CLIENT_SECRET=your_slack_secret

# AWS Services
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│        Streamlit Frontend (Port 8501)            │
├─────────────────────────────────────────────────┤
│                                                  │
│    FastAPI Backend (Port 8000)                 │
│  ├─ Agent Orchestration                         │
│  ├─ Skill Registry                              │
│  ├─ Provider Router                             │
│  ├─ Memory/State Management                     │
│  └─ Connector Gateway                           │
│                                                  │
├─────────────────────────────────────────────────┤
│                                                  │
│    External Services                            │
│  ├─ LLM Providers (Grok, Gemini, OpenAI)       │
│  ├─ Search Services (Tavily, Serper)           │
│  └─ Integrations (GitHub, Slack, etc.)         │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 📦 Deployment

### Production Checklist

- [ ] API keys configured in `.env`
- [ ] Docker installed and running
- [ ] Firewall rules configured (8000, 8501 ports)
- [ ] SSL/TLS reverse proxy configured (nginx/Caddy)
- [ ] Backup strategy in place
- [ ] Monitoring and logging setup

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Server Deployment

```bash
# SSH into server
ssh user@server.ip

# Clone and setup
git clone https://github.com/cryptostoner94/super-agent-os.git
cd super-agent-os
cp .env.example .env
# Edit .env with production values
nano .env

# Install and run
bash scripts/install.sh
bash scripts/run.sh
```

## 📡 API Documentation

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "service": "Super Agent OS",
  "version": "1.0.0",
  "timestamp": "2024-06-03 12:00:00"
}
```

### Run Agent

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this data",
    "agent_id": "executive",
    "raw_data": "your data here"
  }'
```

### Create Artifact

```bash
curl -X POST http://localhost:8000/artifact/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Report",
    "format": "markdown",
    "content": "# Title\n\nContent here"
  }'
```

### Interactive API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestHealth -v

# Run performance tests
pytest tests/ -v -m performance
```

## 📊 Monitoring

### Health Probes

- **Startup Probe**: `/health` - Full system check
- **Readiness Probe**: `/ready` - Ready to accept traffic
- **Liveness Probe**: `/live` - Process alive check

### Logs

```bash
# View backend logs
docker-compose logs backend

# View frontend logs
docker-compose logs frontend

# Real-time logs
docker-compose logs -f
```

## 🔒 Security

- Non-root container execution
- CORS protection
- Request validation (Pydantic)
- SQL injection prevention
- XSS protection
- CSRF tokens (when applicable)
- Rate limiting ready
- API key management in environment

## 🛠️ Development

### Project Structure

```
super-agent-os/
├── backend/
│   └── app/
│       ├── agents/          # Agent implementations
│       ├── api/             # API schemas and routes
│       ├── artifacts/       # Artifact generation
│       ├── connectors/      # External integrations
│       ├── core/            # Configuration
│       ├── memory/          # State management
│       ├── providers/       # LLM provider routing
│       ├── skills/          # Skill registry
│       ├── runtime/         # Command execution
│       └── main.py          # FastAPI application
├── frontend/
│   └── streamlit/
│       └── app.py           # Streamlit UI
├── tests/
│   └── test_api.py          # Comprehensive tests
├── scripts/
│   ├── deploy.sh            # Production deployment
│   ├── install.sh           # Dependency installation
│   ├── run.sh               # Local development
│   ├── auto-commit.sh       # Git auto-commit
│   └── healthcheck.sh       # Health verification
└── docs/                    # Documentation
```

### Adding a Skill

```python
# skills/custom_skill.py
def my_skill(param: str) -> str:
    """Custom skill implementation"""
    return f"Processed: {param}"

# Register in skills/registry.py
SKILLS = [
    {"name": "my_skill", "desc": "My custom skill"}
]
```

### Adding an Integration

1. Create connector in `connectors/`
2. Add environment variable to `.env.example`
3. Register in `core/config.py`
4. Implement gateway in `providers/router.py`

## 📈 Performance

- Response time: <100ms (health checks)
- Agent execution: 5-30s (varies by task)
- Concurrent requests: 100+
- Memory footprint: ~500MB baseline
- CPU: Minimal when idle

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] GraphQL API
- [ ] Multi-user authentication
- [ ] Advanced analytics dashboard
- [ ] Agent marketplace
- [ ] Training/fine-tuning capabilities
- [ ] Mobile app support
- [ ] Enterprise SSO integration

## 📞 Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/cryptostoner94/super-agent-os/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cryptostoner94/super-agent-os/discussions)

## 🙏 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Streamlit](https://streamlit.io/) - Python app framework for data projects
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

---

**Made with ❤️ by [Cryptostoner94](https://github.com/cryptostoner94)**

⭐ Star this repo if you find it useful!
