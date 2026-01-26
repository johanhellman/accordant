# Accordant - XMarkDigest Application

**Access**: https://accordant.eu

## Overview

Accordant (based on XMarkDigest) is a personal knowledge engine that syncs, categorizes, and analyzes information from various sources, starting with X (Twitter) bookmarks. The system continuously syncs new bookmarks in the background, detects changes, and uses AI to analyze and categorize content.

**Source Repository**: [johanhellman/XMarkDigest](https://github.com/johanhellman/XMarkDigest) (private)

## Key Features

- **Secure Authentication**: Seamless "Login with X" integration using OAuth 2.0 (Authorization Code Flow with PKCE)
- **Smart Sync Engine**: 
  - Quick Sync (optimized for daily usage)
  - Date-Limited Sync (sync only bookmarks newer than a specific date)
  - Deep Sync (full historical sync)
  - Rate limit resilience with automatic re-queuing
- **AI-Powered Categorization**: Content-aware analysis using LLMs (Claude Sonnet, GPT-4o, Llama) with intelligent auto-tagging
- **Premium Insights Dashboard**: User persona generation, weekly digests, deep dives, and trend visualization

## Technology Stack

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, Zustand, React Query
- **Backend**: Next.js API Routes, PostgreSQL, Prisma ORM
- **Async Processing**: Redis, BullMQ (for robust job queues)
- **AI Infrastructure**: LiteLLM, OpenRouter for unified model access

## Architecture

- **Container Names**: 
  - `ai-stack_accordant_web` (Next.js web application)
  - `ai-stack_accordant_worker` (Background job processor)
  - `ai-stack_accordant_redis` (Redis for job queues)
- **Port**: 3000 (Next.js production port)
- **Domain**: `accordant.eu`
- **Networks**: `frontend` (Traefik), `internal` (database and Redis access)
- **Health Endpoint**: `/api/health` (checks database and Redis connectivity)

## Dependencies

- **PostgreSQL**: Via `ai-stack_db` (app-specific database user: `accordant`)
- **Redis**: Internal Redis container for job queues
- **No external services required**: LiteLLM and Qdrant are optional (for future phases)

## Deployment

### Prerequisites

- Infrastructure running and healthy
- Networks (`ai-stack_frontend`, `ai-stack_internal`) exist
- DNS configured: `accordant.eu` → server IP
- Database user and database created (see Database Setup below)

### Initial Setup

1. **Copy environment file**:
   ```bash
   cd /root/apps/accordant
   cp .env.example .env
   chmod 600 .env
   ```

2. **Generate secure passwords and secrets**:
   ```bash
   # Generate database password
   openssl rand -base64 32
   
   # Generate NextAuth secret
   openssl rand -base64 32
   
   # Generate encryption key (64-character hex string)
   openssl rand -hex 32
   ```

3. **Edit `.env` file** with actual values:
   ```bash
   # IMPORTANT: Define password BEFORE DATABASE_URL (variable expansion dependency)
   ACCORDANT_DB_PASSWORD="<generated-password-from-step-2>"
   DATABASE_URL=postgresql://accordant:${ACCORDANT_DB_PASSWORD}@ai-stack_db:5432/accordant?sslmode=require
   
   # Set security metadata
   SECURITY_OWNER=<your-name>
   SECURITY_CONTACT=<your-email>
   
   # Set NextAuth secret (from step 2)
   NEXTAUTH_SECRET="<generated-secret>"
   
   # Set encryption key (from step 2)
   ENCRYPTION_KEY="<generated-hex-string>"
   
   # Set domain
   DOMAIN_NAME=accordant.eu
   NEXTAUTH_URL=https://accordant.eu
   
   # Set X (Twitter) OAuth credentials
   X_CLIENT_ID=<your-x-client-id>
   X_CLIENT_SECRET=<your-x-client-secret>
   X_CALLBACK_URL=https://accordant.eu/api/auth/callback/twitter
   
   # Set LLM API key
   LLM_API_KEY=sk-or-v1-...
   LLM_BASE_URL=https://openrouter.ai/api/v1
   LLM_DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514
   
   # Set email configuration (if using Resend)
   RESEND_API_KEY=re_...
   EMAIL_FROM=onboarding@resend.dev
   ```

4. **Database Setup**:
   ```bash
   # Connect to PostgreSQL
   docker exec -it ai-stack_db psql -U llmproxy -d postgres
   ```
   
   Then run (use the same password from `.env`):
   ```sql
   -- Create app-specific database user
   CREATE USER accordant WITH PASSWORD 'same-password-as-in-env';
   
   -- Create database
   CREATE DATABASE accordant OWNER accordant;
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE accordant TO accordant;
   ```
   
   Verify connectivity:
   ```bash
   docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT current_database(), current_user;"
   ```

5. **Validate compose file**:
   ```bash
   /root/ai-stack/scripts/validation/validate-app-compose.sh \
     /root/apps/accordant/docker-compose.yml
   ```

6. **Verify Docker Compose config**:
   ```bash
   cd /root/apps/accordant
   docker compose config
   ```

7. **Deploy**:
   ```bash
   cd /root/apps/accordant
   docker compose up -d --build
   ```

8. **Run database migrations**:
   ```bash
   # Push Prisma schema to database
   docker compose exec web pnpm --filter database push
   ```

9. **Verify services are running**:
   ```bash
   docker compose ps
   # Should show web, worker, and redis as "Up" and healthy
   ```

### Post-Deployment

1. **Verify Container Status**:
   ```bash
   docker compose ps
   # Should show web, worker, and redis as "Up" and healthy
   ```

2. **Check Logs**:
   ```bash
   docker compose logs -f web
   docker compose logs -f worker
   docker compose logs -f redis
   ```

3. **Verify Health Endpoint**:
   ```bash
   curl https://accordant.eu/api/health
   # Should return: {"status":"ok","timestamp":"..."}
   ```

4. **Access Application**:
   - Navigate to: https://accordant.eu
   - Complete initial setup/onboarding

5. **Verify Monitoring** (if monitoring stack is running):
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.service=="accordant")'
   
   # Check Blackbox probes
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="blackbox_apps") | select(.labels.instance | contains("accordant"))'
   ```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Key Variables**:
- `DATABASE_URL`: PostgreSQL connection string (app-specific user)
- `NEXTAUTH_URL`: Public URL where app is accessible
- `NEXTAUTH_SECRET`: Authentication secret (generate with `openssl rand -base64 32`)
- `ENCRYPTION_KEY`: 64-character hex string (generate with `openssl rand -hex 32`)
- `X_CLIENT_ID`, `X_CLIENT_SECRET`: X (Twitter) OAuth credentials
- `LLM_API_KEY`: OpenRouter API key
- `REDIS_HOST`, `REDIS_PORT`: Redis connection (via internal network)
- `PORT`: Application port (default: 3000)

### Database Configuration

Accordant uses an **app-specific database user** following [ADR-0014](../../ai-stack/docs/adr/ADR-0014-database-strategy.md):

- **Database User**: `accordant` (created during setup)
- **Database Name**: `accordant` (or any name you choose)
- **Connection**: Via `internal` network to `ai-stack_db:5432`
- **SSL**: Required (`sslmode=require`)

### Redis Configuration

Redis is provided by the infrastructure layer:

- **Container**: `ai-stack_redis` (managed in infrastructure)
- **Network**: `internal`
- **Connection**: `redis://ai-stack_redis:6379`
- **Usage**: BullMQ job queues
- **Data Isolation**: Uses Redis database 0 (default) with BullMQ namespacing

## Updates

### Update Accordant

```bash
cd /root/apps/accordant

# Update submodule (source repository)
git submodule update --remote xmarkdigest

# Rebuild and restart
docker compose build
docker compose up -d

# Run migrations if schema changed
docker compose exec web pnpm --filter database push
```

### Update Configuration

1. Edit `.env` file with new values
2. Restart services:
   ```bash
   docker compose restart web worker redis
   ```

## Monitoring

### Health Checks

- **Health endpoint**: `https://accordant.eu/api/health`
- **Internal health**: `http://localhost:3000/api/health` (from within container)
- **Health check**: Configured in docker-compose.yml for all services

### Metrics

- **Metrics endpoint**: Not available (uses container metrics via cAdvisor)
- **Prometheus**: Automatically scrapes container metrics via auto-discovery
  - Targets: `ai-stack_accordant_web:3000`, `ai-stack_accordant_worker`, `ai-stack_accordant_redis`
  - Service labels: `accordant`, `accordant-worker`, `accordant-redis`
  - Environment: `production`
- **Grafana**: Generic container metrics dashboard shows accordant data
- **Auto-Discovery**: Configured - no manual Prometheus config needed

### Monitoring Verification

After deployment, verify monitoring is working:

1. **Prometheus Targets**:
   ```bash
   # Check if accordant services appear in targets
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.service | startswith("accordant"))'
   ```
   Expected: Targets should be UP and scraping metrics

2. **Blackbox Probes**:
   ```bash
   # Check Blackbox probe status
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="blackbox_apps") | select(.labels.instance | contains("accordant"))'
   ```
   Expected: Probes should be UP and returning 200 status

3. **Logs in Loki**:
   ```bash
   # Query logs for accordant
   curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
     --data-urlencode 'query={container_name=~"ai-stack_accordant.*"}' \
     --data-urlencode 'limit=10'
   ```
   Expected: Logs should be visible in Loki

### Logs

```bash
# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f redis

# View last 100 lines
docker compose logs --tail=100 web
```

## Troubleshooting

### Application Not Starting

1. **Check container status**:
   ```bash
   docker compose ps
   ```

2. **Check logs**:
   ```bash
   docker compose logs web
   docker compose logs worker
   ```

3. **Check health endpoint** (if web container is running):
   ```bash
   curl http://localhost:3000/api/health
   ```

4. **Verify database connection**:
   ```bash
   docker compose exec web pnpm --filter database push
   ```

5. **Check Docker Compose config**:
   ```bash
   docker compose config
   ```

### Cannot Access Application

1. **Check Traefik routing**:
   ```bash
   docker logs ai-stack_traefik | grep accordant
   ```

2. **Verify DNS**:
   ```bash
   dig accordant.eu
   nslookup accordant.eu
   ```

3. **Check SSL certificate**:
   ```bash
   curl -I https://accordant.eu
   ```

### Database Connection Issues

1. **Verify database exists**:
   ```bash
   docker exec ai-stack_db psql -U llmproxy -d postgres -c "\l accordant"
   ```

2. **Check database user**:
   ```bash
   docker exec ai-stack_db psql -U llmproxy -d postgres -c "\du accordant"
   ```

3. **Test connection with app user**:
   ```bash
   docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT current_database(), current_user;"
   ```

4. **Verify .env file**:
   ```bash
   # Check that password is set (don't display it)
   grep -q "ACCORDANT_DB_PASSWORD=" .env && echo "Password is set" || echo "Password missing"
   
   # Verify DATABASE_URL uses variable expansion
   grep "DATABASE_URL.*ACCORDANT_DB_PASSWORD" .env
   ```

5. **Check variable ordering**:
   - Ensure `ACCORDANT_DB_PASSWORD` is defined **before** `DATABASE_URL` in `.env`
   - `DATABASE_URL` uses `${ACCORDANT_DB_PASSWORD}` variable expansion

### Redis Connection Issues

1. **Check Redis container status**:
   ```bash
   docker compose ps redis
   ```

2. **Check Redis logs**:
   ```bash
   docker compose logs redis
   ```

3. **Test Redis connection from web container**:
   ```bash
   docker compose exec web node -e "const redis = require('redis'); const client = redis.createClient({url: 'redis://accordant_redis:6379'}); client.connect().then(() => {console.log('Connected'); client.quit();})"
   ```

### Migration Issues

1. **Check Prisma schema**:
   ```bash
   docker compose exec web cat xmarkdigest/packages/database/prisma/schema.prisma
   ```

2. **Run migrations manually**:
   ```bash
   docker compose exec web pnpm --filter database push
   ```

## Security

### Security Requirements

- ✅ No Docker socket access
- ✅ Container hardening (`no-new-privileges`, `cap_drop: ALL`)
- ✅ Resource limits enforced
- ✅ Network isolation (frontend + internal only)
- ✅ Secrets in `env_file` with proper permissions
- ✅ Security labels on containers and volumes
- ✅ App-specific database user (principle of least privilege)

### Secrets Management

- Store secrets in `.env` file with `chmod 600` permissions
- Never commit `.env` files to version control
- Generate secure passwords: `openssl rand -base64 32`
- Generate encryption keys: `openssl rand -hex 32`
- Rotate secrets periodically

## Backup

### Backup Accordant Data

```bash
# Backup database
docker exec ai-stack_db pg_dump -U accordant accordant > accordant-backup-$(date +%Y%m%d).sql

# Backup Redis data (if needed)
docker run --rm \
  -v accordant_redis_data:/data:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/accordant-redis-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Accordant Data

```bash
# Restore database
cat accordant-backup-YYYYMMDD.sql | docker exec -i ai-stack_db psql -U accordant accordant

# Restore Redis data
docker run --rm \
  -v accordant_redis_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/accordant-redis-YYYYMMDD.tar.gz"
```

## App Wrapper Pattern

Accordant uses the **app wrapper pattern** to keep the source repository (`XMarkDigest`) independent:

- **Source Repository**: `/root/apps/accordant/xmarkdigest/` (git submodule)
  - Contains application source code
  - Dockerfile and source code remain unchanged
  - Can be deployed independently elsewhere

- **App Wrapper**: `/root/apps/accordant/`
  - Contains deployment configuration (`docker-compose.yml`)
  - Infrastructure details (Traefik, monitoring, security)
  - Environment configuration (`.env`, `.env.example`)
  - Deployment documentation (this README)

**Benefits**:
- Source repository remains clean and independent
- Infrastructure details stay in app wrapper
- Can update deployment config without touching source
- Follows separation of concerns

## Related Documentation

- [Adding New Apps: Quick Reference](../../ai-stack/docs/ADDING_NEW_APPS.md) - Official guide for adding apps
- [ADR-0014: Database Strategy](../../ai-stack/docs/adr/ADR-0014-database-strategy.md) - Database user strategy
- [Multi-App Architecture](../../ai-stack/docs/MULTI_APP_ARCHITECTURE.md) - Complete architecture documentation
- [XMarkDigest Source Repository](https://github.com/johanhellman/XMarkDigest) - Source code (private)

## Support

For issues:
1. Check logs: `docker compose logs web worker redis`
2. Check health endpoint: `curl https://accordant.eu/api/health`
3. Review [Troubleshooting](#troubleshooting) section above
4. Check source repository documentation in `xmarkdigest/README.md`
