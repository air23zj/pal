# Production Deployment Guide

This guide covers deploying PAL to production environments.

## 🚀 Quick Production Setup

### 1. Environment Configuration

```bash
# Copy and configure environment
cp .env.example .env
nano .env  # Edit with production values

# Key production settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=postgresql://user:pass@host:5432/pal_prod
```

### 2. Database Setup

```bash
# For PostgreSQL
createdb pal_prod
psql pal_prod < schema.sql

# Or use migrations
cd backend && alembic upgrade head
```

### 3. Build and Deploy

```bash
# Using Docker
docker-compose -f docker-compose.prod.yml up -d

# Or using the build system
make build-prod
make deploy
```

## 🔧 Production Configuration

### Required Environment Variables

```bash
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=your-256-bit-secret-key

# Database (PostgreSQL required for production)
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis (required for production)
REDIS_URL=redis://host:6379/0

# Vector Database
QDRANT_URL=http://qdrant-host:6333

# API Keys (secure storage required)
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
```

### Security Considerations

- ✅ **API Keys**: Store in secure secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- ✅ **Database**: Use connection pooling and SSL
- ✅ **Redis**: Enable authentication and SSL
- ✅ **Qdrant**: Configure authentication and network isolation
- ✅ **Logs**: Implement log aggregation (ELK stack, CloudWatch, etc.)
- ✅ **Monitoring**: Set up health checks and alerts

### Performance Optimization

```bash
# Worker configuration
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker

# Connection limits
MAX_CONNECTIONS=1000
CONNECTION_TIMEOUT=30

# Cache settings
CACHE_TTL_SECONDS=1800  # 30 minutes
REDIS_MAX_CONNECTIONS=20
```

## 🐳 Docker Production Setup

### Multi-stage Dockerfile

The production Dockerfile includes:
- Multi-stage build for smaller images
- Non-root user for security
- Health checks
- Optimized dependencies

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  pal-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - openai_api_key
      - serpapi_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  pal-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com

secrets:
  openai_api_key:
    environment: "OPENAI_API_KEY"
  serpapi_key:
    environment: "SERPAPI_API_KEY"
```

## ☁️ Cloud Deployment Options

### AWS

```bash
# ECS/Fargate
aws ecs create-service --cluster pal-prod --service-name pal-backend --task-definition pal-backend:1

# Elastic Beanstalk
eb create pal-prod-env

# Lambda (serverless)
# Use the lambda deployment guide
```

### Google Cloud

```bash
# Cloud Run
gcloud run deploy pal-backend --source . --platform managed

# GKE
kubectl apply -f k8s/
```

### Railway/Render/Vercel

```bash
# Railway
railway up

# Render
render deploy
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Application health
GET /api/health

# Database connectivity
GET /api/health/db

# External services
GET /api/health/services
```

### Logging

```bash
# Structured logging
LOG_FORMAT=json
LOG_LEVEL=WARNING

# Log aggregation
# Send to CloudWatch, DataDog, or ELK stack
```

### Metrics

```bash
# Key metrics to monitor:
# - Response time (p95 < 500ms)
# - Error rate (< 1%)
# - Database connection pool usage
# - Redis memory usage
# - LLM API rate limits
# - Search API usage
```

## 🔧 Maintenance

### Database Backups

```bash
# Daily backups
pg_dump pal_prod > backup_$(date +%Y%m%d).sql

# Automated with cron
0 2 * * * pg_dump pal_prod | gzip > /backups/pal_$(date +%Y%m%d).sql.gz
```

### Updates

```bash
# Rolling updates
docker-compose up -d --no-deps backend

# Zero-downtime deployment
kubectl set image deployment/pal-backend pal-backend=new-version
```

### Scaling

```bash
# Horizontal scaling
docker-compose up -d --scale backend=3

# Auto-scaling based on CPU/memory
# Configure in your cloud provider
```

## 🚨 Troubleshooting

### Common Issues

1. **Memory Issues**
   ```bash
   # Increase container memory
   docker-compose.yml: deploy.resources.limits.memory: 2G
   ```

2. **Rate Limiting**
   ```bash
   # Configure API rate limits
   SEARCH_REQUESTS_PER_MINUTE=100
   ```

3. **Database Connection Pool**
   ```bash
   # Adjust pool settings
   SQLALCHEMY_POOL_SIZE=20
   SQLALCHEMY_MAX_OVERFLOW=30
   ```

### Performance Tuning

```bash
# Database indexes
CREATE INDEX CONCURRENTLY idx_brief_user_date ON briefs(user_id, created_at);

# Query optimization
EXPLAIN ANALYZE SELECT * FROM briefs WHERE user_id = $1;

# Caching strategy
REDIS_CACHE_TTL=3600
```

## 📚 Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/topics/memory-optimization)
- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)