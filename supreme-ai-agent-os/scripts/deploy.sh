#!/bin/bash
set -e

# Supreme AI Agent OS - Production Deployment Script
# Deploys application using Docker Compose with health checks

echo "🚀 Supreme AI Agent OS - Deployment Script"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker available${NC}"
echo -e "${GREEN}✓ Docker Compose available${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found, creating from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env created from .env.example${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

# Pull latest images
echo -e "${YELLOW}📥 Pulling latest images...${NC}"
docker-compose pull || true

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose build --no-cache 2>&1 | grep -E "^Successfully|Step|ERROR" || true

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 5

# Check backend health
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec supreme-backend curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    echo -e "${YELLOW}⏳ Backend starting... ($((attempt+1))/$max_attempts)${NC}"
    sleep 1
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    docker-compose logs backend
    exit 1
fi

# Display service information
echo -e "${GREEN}=========================================="
echo -e "✓ Deployment Complete!${NC}"
echo -e "${GREEN}=========================================="
echo ""
echo -e "🌐 Frontend:  ${YELLOW}http://localhost:8501${NC}"
echo -e "🔌 API:       ${YELLOW}http://localhost:8000${NC}"
echo -e "📊 Health:    ${YELLOW}http://localhost:8000/health${NC}"
echo -e "📚 Docs:      ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo ""

