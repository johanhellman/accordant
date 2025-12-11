# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Accept build arguments for Vite environment variables
# These allow flexible analytics configuration without hard-coding
ARG VITE_PLAUSIBLE_DOMAIN
ARG VITE_ANALYTICS_DOMAIN
ARG VITE_ANALYTICS_PROVIDER
ARG VITE_ANALYTICS_WEBSITE_ID
ARG VITE_API_BASE

# Set as environment variables for Vite build
ENV VITE_PLAUSIBLE_DOMAIN=${VITE_PLAUSIBLE_DOMAIN}
ENV VITE_ANALYTICS_DOMAIN=${VITE_ANALYTICS_DOMAIN}
ENV VITE_ANALYTICS_PROVIDER=${VITE_ANALYTICS_PROVIDER}
ENV VITE_ANALYTICS_WEBSITE_ID=${VITE_ANALYTICS_WEBSITE_ID}
ENV VITE_API_BASE=${VITE_API_BASE}

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend Runtime
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for build tools)
# Install media-types to ensure proper MIME type detection for static files
# This provides /etc/mime.types which Python's mimetypes module uses
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    media-types \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to cache layer
COPY pyproject.toml ./
# We can use pip to install from pyproject.toml (requires a compatible pip version or build tool)
# Or we can just use uv if strictly desired, but standard pip is easier for generic containers without extra tools.
# Let's use simple pip with the toml support or generate requirements. 
# Since we don't have a requirements.txt, we can use `pip install .` 
# But let's check if the project has a way to export requirements or just install via pip.
# Installing directly from pyproject.toml is supported in newer pip.
RUN pip install --upgrade pip && pip install .

# Copy backend code
COPY backend/ ./backend/
COPY docs/ ./docs/
COPY start.sh ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Copy Defaults for seeding
COPY data/defaults/ ./defaults_seed/
# Ensure data directory exists
RUN mkdir -p /app/data

# Copy Frontend Build from Stage 1
# We place it in /app/frontend/dist so backend can mount it
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set permissions
# Create a non-root user
RUN groupadd -r accordant && useradd -r -g accordant accordant \
    && chown -R accordant:accordant /app

# Switch to non-root user
USER accordant

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
# Tell backend where to find static files if we make it configurable (optional, but good practice)
ENV STATIC_DIR=/app/frontend/dist

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["./docker-entrypoint.sh"]
