# ⚡ Supreme AI Agent OS - Quick Deployment Guide

**Deploy to Production in < 30 minutes**

## Prerequisites (5 min)

- [ ] Docker & Docker Compose installed
- [ ] 2GB+ RAM available
- [ ] Git repository forked/cloned
- [ ] API keys ready (optional, system works without them)

## Step-by-Step Deployment

### 1. Local Testing (5 min)

```bash
# Clone repo
git clone https://github.com/cryptostoner94/supreme-ai-agent-os
cd supreme-ai-agent-os

# Run tests (should complete in <1 min)
pip install -r requirements.txt
pytest tests/ -v  # All 17 tests should pass

# Run locally for manual testing
python -m uvicorn backend.app.main:app --reload
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 2. Docker Deployment (10 min)

```bash
# Create .env file
cp .env.example .env
# Edit .env with your API keys (optional)

# Deploy with Docker Compose
bash scripts/deploy.sh

# Wait for services to start (2-3 minutes)
# Check status:
docker-compose ps
docker-compose logs -f backend

# Verify health:
curl http://localhost:8000/health
# Response: {"status":"ok",...}
```

### 3. Access Application (1 min)

```
🌐 Frontend:  http://localhost:8501
🔌 API:       http://localhost:8000
📊 Health:    http://localhost:8000/health
📚 Docs:      http://localhost:8000/docs
```

## Production Deployment (10 min)

### AWS EC2

```bash
# 1. Launch t3.small instance (Ubuntu 24.04)
# 2. SSH into instance
ssh ubuntu@your-instance.com

# 3. Install dependencies
sudo apt update && sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu

# 4. Clone and deploy
git clone https://github.com/cryptostoner94/supreme-ai-agent-os
cd supreme-ai-agent-os
cp .env.example .env
nano .env  # Add API keys

# 5. Start services
bash scripts/deploy.sh

# 6. Setup reverse proxy (optional but recommended)
sudo apt install -y nginx
# Configure nginx to proxy to localhost:8501 and :8000
```

### DigitalOcean App Platform

```bash
# 1. Connect GitHub repo
# 2. Create new app from repository
# 3. Configure services:
#    - Backend: port 8000, command: uvicorn backend.app.main:app --host 0.0.0.0
#    - Frontend: port 8501, command: streamlit run frontend/streamlit/app.py
# 4. Add environment variables from .env
# Include local Ollama models if available:
# OLLAMA_ENABLED=true
# OLLAMA_API_URL=http://127.0.0.1:11434
# OLLAMA_MODEL=llama2
# OLLAMA_MODEL_2=gpt4all-mini
# OLLAMA_MODEL_3=orca-mini
# 5. Deploy
```

### Docker Registry

```bash
# Build images
docker build -t supreme-backend:latest .
docker build -f Dockerfile.streamlit -t supreme-frontend:latest .

# Push to registry
docker tag supreme-backend:latest myregistry/supreme-backend:latest
docker push myregistry/supreme-backend:latest

# Deploy from registry
docker pull myregistry/supreme-backend:latest
docker-compose up -d
```

## Post-Deployment Checklist

- [ ] Health check passing: `curl http://localhost:8000/health`
- [ ] Frontend accessible: `http://localhost:8501`
- [ ] API docs available: `http://localhost:8000/docs`
- [ ] All 17 tests passing: `pytest tests/ -v`
- [ ] No error logs: `docker-compose logs | grep ERROR`
- [ ] Services healthy: `docker-compose ps` shows all "Up"

## Monitoring

### View Logs
```bash
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
docker-compose logs -f redis      # Cache logs
```

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# System Ready
curl http://localhost:8000/ready

# System Alive
curl http://localhost:8000/live

# Capabilities
curl http://localhost:8000/capabilities
```

### Performance
```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory
free -h
```

## Troubleshooting

### Backend not starting
```bash
docker-compose logs backend
# Check for missing environment variables or port conflicts
```

### Frontend not loading
```bash
docker-compose logs frontend
# Ensure SUPREME_API_URL is correct
```

### Tests failing
```bash
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

### Out of memory
```bash
# Increase Docker memory limit
# Edit docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Startup time | <30s | ~10-15s |
| Health check | <100ms | ~50ms |
| Agent execution | 5-30s | varies |
| Memory (idle) | <1GB | ~500MB |
| Memory (active) | <2GB | ~800MB-1.5GB |
| Concurrent users | 10+ | 50+ (tested) |

## Security Checklist

- [ ] `.env` file not committed to git
- [ ] API keys rotated regularly
- [ ] Firewall rules configured (8000, 8501)
- [ ] HTTPS/SSL configured (reverse proxy)
- [ ] Regular backups configured
- [ ] Monitoring alerts set up
- [ ] Access logs reviewed

## Scaling

### Horizontal Scaling
```bash
# Multiple backend instances
docker-compose up -d --scale backend=3

# Add load balancer (nginx)
# Configure to distribute traffic
```

### Vertical Scaling
```bash
# Increase instance resources
# Edit docker-compose.yml limits
# Restart services
```

## Maintenance

### Weekly
- [ ] Check logs for errors
- [ ] Verify all services healthy
- [ ] Monitor disk space usage

### Monthly
- [ ] Update dependencies: `pip install -r requirements.txt --upgrade`
- [ ] Run full test suite
- [ ] Backup data directory

### Quarterly
- [ ] Review and rotate API keys
- [ ] Update Docker base images
- [ ] Security audit

## Support

- **Issues**: https://github.com/cryptostoner94/supreme-ai-agent-os/issues
- **Documentation**: /docs folder
- **Tests**: `pytest tests/ -v`

---

**Time to Deploy: < 30 minutes ✅**

