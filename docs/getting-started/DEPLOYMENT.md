# Deployment Guide

Production deployment guide for Accordant LLM Council, including security considerations, configuration, and deployment options.

## Production Deployment Considerations

When deploying to production, ensure the following security and configuration settings are properly configured.

## Security Configuration

### CORS Configuration

**⚠️ Important:** Default CORS settings are permissive for local development. For production, you **must** configure restrictive CORS settings.

**Environment Variables:**

```bash
# Required: Specify exact allowed origins (comma-separated or JSON array)
# Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# Or JSON: CORS_ORIGINS='["https://yourdomain.com","https://www.yourdomain.com"]'
CORS_ORIGINS=https://yourdomain.com

# Optional: Restrict HTTP methods (default: "*" allows all)
# Example: CORS_METHODS=GET,POST,OPTIONS
CORS_METHODS=GET,POST,OPTIONS

# Optional: Restrict allowed headers (default: "*" allows all)
# Example: CORS_HEADERS=Content-Type,Authorization
CORS_HEADERS=Content-Type,Authorization

# Optional: Allow credentials (default: "true")
# Set to "false" if you don't need cookies/auth headers
CORS_CREDENTIALS=true
```

**Security Best Practices:**

- **Never use `*` for `CORS_ORIGINS` in production** - Always specify exact domain(s)
- Use HTTPS in production - CORS with credentials requires HTTPS
- Restrict `CORS_METHODS` to only what your frontend needs
- Restrict `CORS_HEADERS` to only necessary headers

### File System Security

**Path Validation:**

- The application validates file paths to prevent directory traversal attacks
- Environment variables for file paths (`LOG_DIR`, `LOG_FILE`, `PERSONALITIES_FILE`) are validated
- All paths are resolved to absolute paths and checked against allowed directories

**File Permissions:**

- Ensure `data/conversations/` directory has proper write permissions
- Log directories should be writable by the application user
- Consider using a database for production instead of JSON files for better scalability
- Use a dedicated user account with minimal privileges

**Example permissions:**

```bash
# Create dedicated user
sudo useradd -r -s /bin/false accordant

# Set ownership
sudo chown -R accordant:accordant /opt/accordant

# Set directory permissions
chmod 750 /opt/accordant
chmod 700 /opt/accordant/data
```

### Secrets Management

**Never commit secrets to version control!**

**Recommended approaches:**

- Use environment variables from your deployment platform
- Use secret management systems:
  - AWS Secrets Manager
  - HashiCorp Vault
  - Google Secret Manager
  - Azure Key Vault
- Use `.env` files only for local development (ensure `.env` is in `.gitignore`)

**Critical secrets:**

- `OPENROUTER_API_KEY` - Your LLM API key
- `ENCRYPTION_KEY` - Fernet key for encrypting stored credentials
- Database credentials (if using a database)
- JWT secret (if configured)

## Example Production Configuration

**Production `.env`:**

```bash
# API Configuration
OPENROUTER_API_KEY=sk-or-v1-...

# Encryption
ENCRYPTION_KEY=your-secure-fernet-key

# CORS - Production Settings
CORS_ORIGINS=https://yourdomain.com
CORS_METHODS=GET,POST,OPTIONS
CORS_HEADERS=Content-Type,Authorization
CORS_CREDENTIALS=true

# Performance Settings
MAX_CONCURRENT_REQUESTS=4
LLM_REQUEST_TIMEOUT=180.0
LLM_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/accordant
LOG_FILE=/var/log/accordant/accordant.log

# Server
PORT=8001
```

## Deployment Options

### Option 1: Docker (Recommended)

**Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY data ./data

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8001

# Run application
CMD ["uv", "run", "python", "-m", "backend.main"]
```

**Build and run:**

```bash
# Build image
docker build -t accordant .

# Run container
docker run -d \
  --name accordant \
  -p 8001:8001 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  accordant
```

**Docker Compose:**

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Option 2: Systemd Service

**Service file:** `/etc/systemd/system/accordant.service`

```ini
[Unit]
Description=Accordant LLM Council API
After=network.target

[Service]
Type=simple
User=accordant
Group=accordant
WorkingDirectory=/opt/accordant
Environment="PATH=/opt/accordant/.venv/bin"
EnvironmentFile=/opt/accordant/.env
ExecStart=/opt/accordant/.venv/bin/python -m backend.main
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/accordant/data /var/log/accordant

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable accordant
sudo systemctl start accordant
sudo systemctl status accordant
```

### Option 3: Reverse Proxy (nginx)

**nginx configuration:** `/etc/nginx/sites-available/accordant`

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Frontend static files
    location / {
        root /var/www/accordant/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/accordant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 4: Cloud Platforms

#### AWS (EC2 + ECS)

- Use ECS Fargate for containerized deployment
- Use Secrets Manager for API keys
- Use CloudWatch for logging
- Use Application Load Balancer for HTTPS termination

#### Google Cloud Platform

- Use Cloud Run for serverless deployment
- Use Secret Manager for API keys
- Use Cloud Logging for logs
- Use Cloud Load Balancing for HTTPS

#### Azure

- Use App Service or Container Instances
- Use Key Vault for secrets
- Use Application Insights for monitoring
- Use Application Gateway for HTTPS

## Environment Variables for Production

See [SETUP.md](SETUP.md#environment-variables-reference) for all available environment variables. Key production considerations:

- **API Keys:** Use secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.)
- **CORS:** Configure restrictive settings (see above)
- **Logging:** Set appropriate log levels and retention policies
- **Performance:** Tune `MAX_CONCURRENT_REQUESTS` based on your rate limits
- **File Paths:** Use absolute paths and ensure proper permissions
- **HTTPS:** Always use HTTPS in production (use reverse proxy or load balancer)
- **Frontend API Base URL:** By default, the frontend uses relative URLs (same origin). For custom configurations, set `VITE_API_BASE` during frontend build (e.g., `VITE_API_BASE=https://api.yourdomain.com npm run build`)

## Monitoring and Logging

### Logging

Configure centralized logging:

```bash
# Use structured logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/accordant
LOG_FILE=/var/log/accordant/accordant.log

# Or send to syslog
# Configure in logging_config.py
```

### Monitoring

Consider monitoring:

- API response times
- Error rates
- Rate limit hits
- Disk usage (for JSON storage)
- Memory usage
- CPU usage

**Recommended tools:**

- Prometheus + Grafana
- Datadog
- New Relic
- CloudWatch (AWS)
- Application Insights (Azure)

### Health Checks

The application provides a health endpoint:

```bash
curl http://localhost:8001/
# Returns: {"status":"ok"}
```

Use this for:

- Load balancer health checks
- Container orchestration health checks
- Monitoring system checks

## Backup and Recovery

### Data Backup

**Critical data to backup:**

- `data/conversations/` - User conversations
- `data/users.json` - User accounts
- `data/organizations.json` - Organization data
- `.env` or secrets - API keys and encryption keys

**Backup strategy:**

- Regular automated backups (daily recommended)
- Store backups in separate location
- Test restore procedures regularly
- Encrypt backups containing sensitive data

**Example backup script:**

```bash
#!/bin/bash
BACKUP_DIR="/backups/accordant"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/accordant_$DATE.tar.gz" \
  data/ \
  .env

# Keep only last 30 days
find "$BACKUP_DIR" -name "accordant_*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery

1. **Document recovery procedures**
2. **Test restore from backups**
3. **Keep encryption keys secure** (if lost, encrypted data is unrecoverable)
4. **Document all environment variables**
5. **Keep deployment scripts version-controlled**

## Scaling Considerations

### Horizontal Scaling

- Use load balancer to distribute traffic
- Ensure shared storage (database or shared filesystem)
- Use sticky sessions if needed (for WebSocket connections)
- Consider stateless design where possible

### Vertical Scaling

- Increase `MAX_CONCURRENT_REQUESTS` for more powerful servers
- Monitor CPU and memory usage
- Consider database migration for better performance

### Database Migration

For production at scale, consider migrating from JSON files to a database:

- **PostgreSQL** - Recommended for relational data
- **MongoDB** - Good for document storage
- **SQLite** - Simple option for small deployments

See [ADR-003](../adr/ADR-003-json-file-storage.md) for current storage architecture.

## Security Checklist

- [ ] CORS configured with specific origins (not `*`)
- [ ] HTTPS enabled (via reverse proxy or load balancer)
- [ ] Secrets stored in secure secret management system
- [ ] File permissions set correctly
- [ ] Application runs as non-root user
- [ ] Logging configured and monitored
- [ ] Regular security updates applied
- [ ] Firewall rules configured
- [ ] Rate limiting configured (if needed)
- [ ] Backup strategy in place
- [ ] Encryption keys backed up securely
- [ ] Health checks configured
- [ ] Monitoring and alerting set up

## Next Steps

- Review [SETUP.md](SETUP.md) for configuration details
- Review [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for admin features
- Review [SECURITY.md](../SECURITY.md) for security best practices
- Test deployment in staging environment first
