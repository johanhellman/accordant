# Analytics Configuration Guide

This document explains how to configure Plausible Analytics for Accordant with flexible deployment options.

## Overview

Accordant supports optional Plausible Analytics integration via environment variables. This allows:

- **Flexible deployment**: Analytics can be enabled or disabled per deployment
- **No hard-coding**: Analytics domain is configurable, not hard-coded
- **Development-friendly**: Analytics disabled by default in development

## Configuration

### Environment Variables

Configure analytics via build-time environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VITE_PLAUSIBLE_DOMAIN` | Analytics server domain | (empty - disabled) | `analytics.accordant.eu` |
| `VITE_ANALYTICS_DOMAIN` | Domain to track | `window.location.hostname` | `accordant.eu` |

### Docker Compose Configuration

In `docker-compose.yml`, analytics configuration is passed as build arguments:

```yaml
accordant:
  build:
    context: ./accordant
    dockerfile: Dockerfile
    args:
      VITE_PLAUSIBLE_DOMAIN: ${PLAUSIBLE_DOMAIN:-analytics.accordant.eu}
      VITE_ANALYTICS_DOMAIN: ${ANALYTICS_DOMAIN:-accordant.eu}
```

### .env File Configuration

Add to your `.env` file:

```bash
# Plausible Analytics Configuration (Optional)
# Leave empty to disable analytics
PLAUSIBLE_DOMAIN=analytics.accordant.eu
ANALYTICS_DOMAIN=accordant.eu
```

**To disable analytics**: Simply don't set `PLAUSIBLE_DOMAIN` or set it to empty:

```bash
PLAUSIBLE_DOMAIN=
```

## How It Works

1. **Build Time**: Vite environment variables (`VITE_*`) are baked into the frontend build
2. **Runtime**: The analytics utility checks if `VITE_PLAUSIBLE_DOMAIN` is set
3. **Script Loading**: If configured, the Plausible script is dynamically injected into the page
4. **Tracking**: Analytics events are tracked automatically

## Implementation Details

### Analytics Utility

The analytics integration is implemented in `frontend/src/utils/analytics.js`:

- **`initAnalytics()`**: Initializes analytics on app load (called once)
- **`trackEvent(eventName, props)`**: Track custom events (if analytics enabled)

### Integration Points

- **App.jsx**: Calls `initAnalytics()` on component mount
- **Dockerfile**: Accepts build args and sets Vite env vars
- **docker-compose.yml**: Passes environment variables as build args

## Usage Examples

### Enable Analytics (Production)

```bash
# .env
PLAUSIBLE_DOMAIN=analytics.accordant.eu
ANALYTICS_DOMAIN=accordant.eu
```

Rebuild the Accordant image:

```bash
docker compose build accordant
docker compose up -d accordant
```

### Disable Analytics (Development)

```bash
# .env - Don't set PLAUSIBLE_DOMAIN or set to empty
PLAUSIBLE_DOMAIN=
```

Or simply omit the variable:

```bash
# .env - No PLAUSIBLE_DOMAIN variable
```

### Custom Analytics Domain

```bash
# .env
PLAUSIBLE_DOMAIN=analytics.example.com
ANALYTICS_DOMAIN=example.com
```

## Verification

### Check if Analytics is Enabled

1. **Browser Console**: Look for analytics initialization message:

   ```
   [Analytics] Initialized - Domain: accordant.eu, Script: https://analytics.accordant.eu/js/script.js
   ```

2. **Network Tab**: Check for script request to Plausible domain

3. **Plausible Dashboard**: Visit `https://analytics.accordant.eu` and verify events appear

### Debug Mode

In development mode (`import.meta.env.DEV`), the analytics utility logs:

- When analytics is disabled (if `VITE_PLAUSIBLE_DOMAIN` not set)
- When analytics is initialized (domain and script URL)
- Script loading errors (if any)

## Compatibility

This implementation follows Accordant's configuration patterns:

- ✅ Uses Vite environment variables (like `VITE_API_BASE`)
- ✅ Build-time configuration (no runtime config needed)
- ✅ Optional feature (gracefully disabled if not configured)
- ✅ No hard-coded domains or URLs

## Troubleshooting

### Analytics Not Loading

1. **Check build args**: Ensure `VITE_PLAUSIBLE_DOMAIN` is set during build
2. **Rebuild image**: Analytics config is baked at build time, not runtime
3. **Check console**: Look for error messages in browser console
4. **Verify domain**: Ensure Plausible domain is accessible and CORS-enabled

### Script Loading Errors

- Check network tab for failed script requests
- Verify Plausible domain is accessible: `curl https://analytics.accordant.eu/js/script.js`
- Check CORS configuration on Plausible server

### Events Not Appearing

- Verify `data-domain` attribute matches configured `VITE_ANALYTICS_DOMAIN`
- Check Plausible dashboard for site configuration
- Ensure Plausible is tracking the correct domain

## Related Documentation

- [Accordant Deployment Guide](DEPLOYMENT.md)
- [Accordant Plan](../../accordant_plan.md) - Analytics integration section
- [Plausible Documentation](https://plausible.io/docs)
