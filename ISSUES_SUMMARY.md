# XMarkDigest Deployment Issues - Quick Summary

**Full Details**: See `XMARKDIGEST_DEPLOYMENT_ISSUES.md`

## Critical Issues (Blocks Deployment)

### 1. Prisma SSL Configuration
- **Problem**: Prisma ignores `sslmode=require` in DATABASE_URL, tries non-SSL connection
- **Error**: `pg_hba.conf rejects connection ... no encryption`
- **Fix Needed**: Verify Prisma SSL connection string format, add SSL config to schema if needed

## High Priority Issues

### 2. Corepack Not Available
- **Problem**: `node:25-slim` doesn't include corepack
- **Error**: `/bin/sh: 1: corepack: not found`
- **Fix**: Install corepack explicitly or use `npm install -g pnpm@latest`

### 3. Worker Permission Issues
- **Problem**: Worker can't create `/app/apps/worker/uploads` directory
- **Error**: `EACCES: permission denied, mkdir '/app/apps/worker/uploads'`
- **Fix**: Create directory in Dockerfile before switching to non-root user

### 4. Self-Signed Certificate Handling
- **Problem**: Prisma rejects self-signed SSL certificates
- **Error**: `self-signed certificate in certificate chain`
- **Fix**: Support `sslmode=prefer` or document certificate acceptance

## Medium Priority Issues

### 5. Redis Connection Timing
- **Problem**: Services connect to Redis before it's ready
- **Error**: `getaddrinfo EAI_AGAIN accordant_redis`
- **Fix**: Add health check dependencies or retry logic

### 6. Health Check Design
- **Problem**: Health check fails if database/Redis unavailable
- **Impact**: Docker health checks fail even when web server works
- **Fix**: Implement tiered health checks (liveness vs readiness)

## Files to Update

1. **Dockerfile**
   - Fix corepack installation (line 5)
   - Fix worker permissions (Stage 4)

2. **apps/web/app/api/health/route.ts**
   - Consider tiered health checks

3. **docker-compose.prod.yml**
   - Add health check dependencies

4. **.env.example**
   - Document SSL connection string options
   - Document Redis connection configuration

5. **Prisma Configuration**
   - Verify SSL connection string format
   - Add SSL configuration if needed

## Quick Fixes Applied (Temporary)

These fixes were applied in the app wrapper but should be fixed in source:

1. Changed `RUN corepack enable` → `RUN npm install -g pnpm@latest`
2. Added `RUN mkdir -p /app/apps/worker/uploads && chown -R worker:nodejs /app` before `USER worker`
3. Adjusted Redis security settings in docker-compose.yml

## Testing Checklist

- [ ] Dockerfile builds with `node:25-slim`
- [ ] Worker container starts and can create uploads directory
- [ ] Database connection works with `sslmode=require`
- [ ] Database connection works with self-signed certificates
- [ ] Redis connection handles startup timing
- [ ] Health check endpoint design is appropriate
- [ ] All environment variables documented
