# XMarkDigest Deployment Issues - For Source Repository

This document outlines all issues encountered during deployment of XMarkDigest as an app wrapper in the ai-stack infrastructure. These issues should be addressed in the XMarkDigest source repository.

**Date**: 2026-01-26  
**Deployment Environment**: Docker Compose with PostgreSQL, Redis, Traefik  
**Repository**: https://github.com/johanhellman/XMarkDigest

---

## 1. Dockerfile Build Issues

### 1.1 Corepack Not Available in node:25-slim

**Issue**: The Dockerfile uses `RUN corepack enable` but `corepack` is not available in the `node:25-slim` base image.

**Error**:
```
/bin/sh: 1: corepack: not found
```

**Location**: `Dockerfile` line 5

**Current Code**:
```dockerfile
FROM node:25-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
```

**Workaround Applied**: Changed to `RUN npm install -g pnpm@latest`

**Recommended Fix**: 
- Option 1: Use `node:25` (full image) instead of `node:25-slim` if corepack is required
- Option 2: Install corepack explicitly: `RUN npm install -g corepack && corepack enable`
- Option 3: Install pnpm directly: `RUN npm install -g pnpm@latest` (current workaround)

**Priority**: High - Blocks builds in some environments

---

### 1.2 Worker Container Permission Issues

**Issue**: The worker container fails to start because it cannot create the `/app/apps/worker/uploads` directory due to permission restrictions.

**Error**:
```
Error: EACCES: permission denied, mkdir '/app/apps/worker/uploads'
```

**Location**: `Dockerfile` worker stage (Stage 4)

**Root Cause**: The directory is created after switching to the non-root `worker` user, but the user doesn't have write permissions to create directories.

**Current Code**:
```dockerfile
FROM node:25-slim AS worker
RUN apt-get update && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 worker

# Files are copied here
COPY --from=builder /app/apps/worker ./apps/worker
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER worker  # Switched to non-root user
WORKDIR /app/apps/worker
CMD ["node", "dist/index.js"]
```

**Workaround Applied**: Created directory and set permissions before switching user:
```dockerfile
RUN mkdir -p /app/apps/worker/uploads && chown -R worker:nodejs /app
# ... copy files ...
RUN chown -R worker:nodejs /app/apps/worker/uploads
USER worker
```

**Recommended Fix**: 
- Create the uploads directory in the Dockerfile before switching to the worker user
- Ensure proper ownership is set: `RUN mkdir -p /app/apps/worker/uploads && chown -R worker:nodejs /app/apps/worker/uploads`
- Consider using a volume mount for uploads directory if persistence is needed

**Priority**: High - Blocks worker container from starting

---

## 2. Database Connection Issues

### 2.1 Prisma SSL Configuration Not Respected

**Issue**: Prisma is not respecting the `sslmode=require` parameter in the `DATABASE_URL` connection string, attempting to connect without SSL and being rejected by PostgreSQL.

**Error**:
```
Raw query failed. Code: `28000`. Message: `pg_hba.conf rejects connection for host "172.19.0.25", user "accordant", database "accordant", no encryption`
```

**Connection String Format**:
```
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

**Root Cause**: 
- Prisma may not be parsing the `sslmode` parameter correctly
- The connection string format may need to be different for Prisma
- Prisma might require explicit SSL configuration in the Prisma schema or environment

**Investigation Needed**:
1. Check if Prisma supports `sslmode` parameter in connection strings
2. Verify if Prisma requires SSL configuration in `schema.prisma`
3. Check if connection string needs to be formatted differently (e.g., `?ssl=true` instead of `?sslmode=require`)

**Recommended Fix**:
- Document the correct connection string format for Prisma with SSL
- Add SSL configuration options to Prisma schema if needed
- Consider adding environment variable for SSL mode that Prisma can use
- Update documentation with SSL connection requirements

**Priority**: Critical - Blocks database connectivity in production environments requiring SSL

**References**:
- Prisma SSL documentation: https://www.prisma.io/docs/concepts/database-connectors/postgresql#connection-strings
- PostgreSQL SSL modes: https://www.postgresql.org/docs/current/libpq-ssl.html

---

### 2.2 Self-Signed Certificate Handling

**Issue**: When SSL is enabled, Prisma fails with self-signed certificate errors even when `sslmode=require` is used.

**Error**:
```
Error opening a TLS connection: self-signed certificate in certificate chain
```

**Root Cause**: Prisma/Node.js PostgreSQL driver is validating SSL certificates and rejecting self-signed certificates.

**Recommended Fix**:
- Add support for `sslmode=prefer` (tries SSL, falls back to non-SSL if unavailable)
- Document how to configure Prisma to accept self-signed certificates
- Consider adding `?sslmode=prefer` as a fallback option
- Add environment variable to control SSL strictness: `DATABASE_SSL_MODE=require|prefer|disable`

**Priority**: High - Affects deployments with self-signed certificates

---

## 3. Redis Connection Issues

### 3.1 Service Name Resolution Timing

**Issue**: The web and worker services sometimes fail to connect to Redis during startup, getting `EAI_AGAIN` errors (DNS resolution failure).

**Error**:
```
Error: getaddrinfo EAI_AGAIN accordant_redis
  errno: -3001,
  code: 'EAI_AGAIN',
  syscall: 'getaddrinfo',
  hostname: 'accordant_redis'
```

**Root Cause**: 
- Services are trying to connect to Redis before it's fully ready
- Docker Compose `depends_on` doesn't wait for Redis to be ready, only for it to start
- No retry logic in the application code

**Current Configuration**:
```yaml
depends_on:
  - redis
```

**Recommended Fix**:
1. **Add health check dependency** (Docker Compose v2.1+):
   ```yaml
   depends_on:
     redis:
       condition: service_healthy
   ```

2. **Implement retry logic in application code**:
   - Add exponential backoff retry for Redis connections
   - Add connection pooling with retry on failure
   - Log connection attempts for debugging

3. **Add startup delay or wait script**:
   - Wait for Redis to be ready before starting application
   - Use a health check script that pings Redis before proceeding

**Priority**: Medium - Causes temporary connection errors but usually resolves

**Location**: 
- Redis connection code in web service
- Redis connection code in worker service
- Docker Compose configuration

---

### 3.2 Redis Connection Configuration

**Issue**: The application uses `REDIS_HOST` and `REDIS_PORT` environment variables, but the connection URL format may not be consistent.

**Current Environment Variables**:
- `REDIS_HOST=accordant_redis`
- `REDIS_PORT=6379`
- `REDIS_URL=redis://accordant_redis:6379` (optional)

**Recommended Fix**:
- Standardize on either `REDIS_URL` or separate `REDIS_HOST`/`REDIS_PORT` variables
- Document which format is preferred
- Ensure consistent usage across web and worker services
- Add validation to ensure Redis connection parameters are set

**Priority**: Low - Works but could be more consistent

---

## 4. Health Check Endpoint Issues

### 4.1 Health Check Fails When Database/Redis Unavailable

**Issue**: The `/api/health` endpoint returns 503 (Service Unavailable) when either the database or Redis connection fails, even if the web server itself is running.

**Current Behavior**:
- Health check requires both database AND Redis to be healthy
- Returns 503 if either service is unavailable
- This causes Docker health checks to fail even if the web server is functional

**Location**: `apps/web/app/api/health/route.ts`

**Recommended Fix**:
- Consider implementing a tiered health check:
  - **Liveness**: Web server is running (always returns 200)
  - **Readiness**: Database and Redis are available (returns 503 if unavailable)
- Or add separate endpoints:
  - `/api/health` - Basic health (web server)
  - `/api/health/ready` - Full readiness (database + Redis)
- Document which endpoint should be used for Docker health checks vs. load balancer checks

**Priority**: Medium - Affects deployment orchestration and monitoring

---

## 5. Environment Variable Documentation

### 5.1 Missing SSL Configuration Documentation

**Issue**: The `.env.example` file doesn't document SSL connection string options for PostgreSQL.

**Current State**: `.env.example` shows:
```
DATABASE_URL="postgresql://user:pass@localhost:5432/bookmark_analyzer"
```

**Recommended Fix**: Add documentation for SSL modes:
```bash
# Database Connection
# SSL Modes: disable, allow, prefer, require, verify-ca, verify-full
# For production with SSL: use ?sslmode=require
# For self-signed certificates: use ?sslmode=prefer
DATABASE_URL="postgresql://user:pass@localhost:5432/bookmark_analyzer?sslmode=require"
```

**Priority**: Medium - Would help users configure SSL correctly

---

### 5.2 Redis Connection Documentation

**Issue**: The `.env.example` shows Redis configuration but doesn't explain the relationship between `REDIS_HOST`, `REDIS_PORT`, and `REDIS_URL`.

**Recommended Fix**: Add comments explaining:
- When to use `REDIS_URL` vs separate variables
- Docker Compose service name vs. hostname
- Connection string format

**Priority**: Low - Documentation improvement

---

## 6. Docker Compose Production Configuration

### 6.1 Missing Health Check Dependencies

**Issue**: The `docker-compose.prod.yml` uses `depends_on` but doesn't wait for services to be healthy.

**Current Configuration**:
```yaml
depends_on:
  - redis
```

**Recommended Fix**: Use health check conditions:
```yaml
depends_on:
  redis:
    condition: service_healthy
```

**Priority**: Medium - Improves startup reliability

---

### 6.2 Redis Container Security Configuration

**Issue**: The production Docker Compose doesn't specify security hardening for Redis container.

**Recommended Fix**: Add security configuration similar to web/worker:
```yaml
redis:
  security_opt:
    - no-new-privileges:true
  # Note: Redis may need some capabilities to run
  # Consider minimal cap_drop or specific cap_add if needed
```

**Priority**: Low - Security best practice

---

## 7. Build and Development Issues

### 7.1 Node.js Version Requirement

**Issue**: The `package.json` specifies `"node": ">=25"` but Node.js 25 may not be widely available yet.

**Current Requirement**: `engines.node >= 25`

**Recommended Fix**:
- Consider supporting Node.js 20 LTS as minimum
- Test compatibility with Node.js 20, 22, and 25
- Document which Node.js versions are tested and supported

**Priority**: Low - Compatibility consideration

---

## 8. Monitoring and Observability

### 8.1 Missing Metrics Endpoint

**Issue**: The application doesn't expose a `/metrics` endpoint for Prometheus scraping, even though the deployment expects it.

**Current State**: Monitoring labels expect `/metrics` endpoint but it doesn't exist.

**Recommended Fix**:
- Add Prometheus metrics endpoint at `/metrics`
- Or document that metrics are not available and update monitoring configuration
- Consider using a metrics library like `prom-client` for Node.js

**Priority**: Low - Nice to have for production monitoring

---

## Summary of Priorities

### Critical (Blocks Deployment)
1. **Database SSL Configuration** - Prisma not respecting `sslmode=require` parameter

### High (Significant Impact)
1. **Corepack Availability** - Build fails in node:25-slim
2. **Worker Permissions** - Worker container cannot start
3. **Self-Signed Certificate Handling** - SSL connection fails with self-signed certs

### Medium (Affects Reliability)
1. **Redis Connection Timing** - Services connect before Redis is ready
2. **Health Check Design** - Fails when dependencies unavailable
3. **Docker Compose Health Dependencies** - Services don't wait for dependencies to be healthy

### Low (Documentation/Polish)
1. **Environment Variable Documentation** - Missing SSL/Redis connection docs
2. **Redis Security Configuration** - Missing in production compose
3. **Node.js Version Support** - Consider LTS versions
4. **Metrics Endpoint** - Missing Prometheus metrics

---

## Testing Recommendations

When fixing these issues, please test:

1. **Build**: Verify Dockerfile builds successfully with `node:25-slim`
2. **Database**: Test with both SSL and non-SSL PostgreSQL connections
3. **Redis**: Test connection with service name resolution (Docker Compose)
4. **Health Checks**: Verify health endpoint behavior with unavailable dependencies
5. **Worker**: Verify worker can create required directories and start successfully
6. **Startup**: Test service startup order and dependency waiting

---

## Deployment Environment Details

- **Infrastructure**: Docker Compose with external networks
- **Database**: PostgreSQL 16.11 with SSL required
- **Redis**: Redis 7-alpine in Docker container
- **Reverse Proxy**: Traefik with Let's Encrypt
- **Networks**: `frontend` (Traefik), `internal` (database/Redis)
- **Security**: Container hardening with `no-new-privileges` and `cap_drop: ALL`

---

## Contact

For questions about these issues or the deployment environment, please refer to the app wrapper repository or deployment documentation.

**App Wrapper Location**: `/root/apps/accordant`  
**Source Repository**: https://github.com/johanhellman/XMarkDigest
