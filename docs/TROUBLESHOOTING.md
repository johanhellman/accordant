# Troubleshooting Guide

Common issues and solutions for Accordant LLM Council.

## Backend Issues

### API Key Not Found

**Error:** `OPENROUTER_API_KEY or LLM_API_KEY environment variable is required`

**Solution:**

- Ensure your `.env` file exists in the project root and contains `OPENROUTER_API_KEY=sk-or-v1-...`
- Verify: Check that `.env` is in the same directory as `pyproject.toml`
- Check file permissions: Ensure the `.env` file is readable

### Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**

- Run `uv sync` to install dependencies
- Use `uv run python -m backend.main` to start the backend (from project root)
- Alternative: Activate the virtual environment with `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)

### Port Already in Use

**Error:** `Address already in use` when starting backend

**Solution:**

- Either stop the process using port 8001:

  ```bash
  # Find process using port 8001
  lsof -ti:8001 | xargs kill -9
  ```

- Or set a different port via environment variable:

  ```bash
  PORT=8002 uv run python -m backend.main
  ```

- Don't forget to update the frontend API URL if you change the port

### Rate Limiting

**Symptom:** Requests fail with timeout or rate limit errors

**Solution:**

- Reduce `MAX_CONCURRENT_REQUESTS` in `.env` (try 2 or 1)
- Increase `LLM_REQUEST_TIMEOUT` if models are slow
- Check your OpenRouter account for rate limits and credits
- Consider upgrading your OpenRouter plan if you hit limits frequently

### Encryption Key Issues

**Error:** `Invalid token` or encryption-related errors

**Solution:**

- Ensure `ENCRYPTION_KEY` is set in `.env`
- Verify the key is valid Fernet format (32 url-safe base64-encoded bytes)
- If you've lost the key, you'll need to rotate it (see [SETUP.md](SETUP.md#key-rotation))

## Frontend Issues

### Port Already in Use

**Error:** Vite dev server can't start because port 5173 is in use

**Solution:**

- Vite will automatically try the next available port, or specify one:

  ```bash
  cd frontend
  npm run dev -- --port 5174
  ```

- Update `CORS_ORIGINS` in `.env` if you use a different port

### Dependencies Not Installing

**Error:** `npm install` fails

**Solution:**

- Ensure you have Node.js v18+ installed: `node --version`
- Try clearing cache:

  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

- Check npm version: `npm --version` (should be compatible with Node.js version)

### CORS Errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**

- Check your `CORS_ORIGINS` environment variable in `.env`
- Default is `http://localhost:5173,http://localhost:3000`
- If using a different frontend port, add it to `CORS_ORIGINS`
- Format: comma-separated or JSON array: `CORS_ORIGINS='["http://localhost:5174"]'`

### Network Errors (ERR_BLOCKED_BY_CLIENT)

**Error:** `Failed to load resource: net::ERR_BLOCKED_BY_CLIENT` or `TypeError: Failed to fetch` when registering/logging in

**Cause:**
- In production, the frontend was previously hardcoded to use `localhost:8001`, causing cross-origin requests to be blocked
- Browser extensions (ad blockers, privacy tools) may also block requests

**Solution:**

- **Production deployments:** The frontend now uses relative URLs by default (same origin as the backend). Ensure frontend and backend are served from the same domain.
- **Custom API URLs:** If you need a different API base URL, set `VITE_API_BASE` during build:
  ```bash
  VITE_API_BASE=https://api.yourdomain.com npm run build
  ```
- **Development:** For local development, the frontend defaults to relative URLs. If you need `http://localhost:8001`, set `VITE_API_BASE=http://localhost:8001` before running `npm run dev`
- **Browser extensions:** If errors persist, try disabling browser extensions or test in incognito mode

### API Routes Returning 404

**Error:** API endpoints like `/api/auth/me` return `404 Not Found` even though they exist in the backend

**Cause:**
- In FastAPI, routes are matched in the order they're defined
- If a catch-all route (like `/{full_path:path}` for SPA routing) is defined before API routes, it intercepts API requests
- This was a bug where the static file mounting and catch-all route were defined before API routes

**Solution:**

- **Fixed in code:** The catch-all route is now defined after all API routes in `backend/main.py`
- **If you're modifying routes:** Always define specific API routes before catch-all routes
- **Route order matters:** FastAPI matches routes top-to-bottom, so more specific routes must come before generic ones

**Example of correct route order:**
```python
# ✅ Correct: API routes first
@app.get("/api/auth/me")
async def get_current_user():
    ...

# Then catch-all at the end
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    ...
```

### Build Errors

**Error:** Frontend build fails or has TypeScript/ESLint errors

**Solution:**

- Run linting to see specific issues: `cd frontend && npm run lint`
- Auto-fix where possible: `cd frontend && npm run lint:fix`
- Check Node.js version compatibility
- Clear node_modules and reinstall (see above)

## Docker & Deployment Issues

### Stale Assets in Docker

**Problem:** Changes to frontend code (CSS/JS) are not reflected in the Docker container, even after restarting it.

**Cause:**
The `Dockerfile` usage a multi-stage build where the frontend is compiled **inside** the image construction phase. It does **not** mount your local `frontend/dist` directory (preventing host-container mismatches). Therefore, local changes or local builds are ignored by the running container until the image is rebuilt.

**Solution:**
You MUST rebuild the Docker image to pick up any frontend changes:

```bash
docker compose build --no-cache
docker compose up -d
```

### Rendering Artifacts (e.g. `/>`)

**Problem:** `/>` characters appear after text in the production build (port 8000) but not in the development server (port 5173).

**Cause:**
CSS syntax errors (e.g., missing braces, invalid nesting, or dangling properties) can cause the build tool (esbuild/Vite) to misinterpret the file structure, leading to corrupted assets in the production bundle.

**Solution:**

1. Run a local build to check for warnings:

   ```bash
   cd frontend
   npm run build
   ```

2. Look for warnings like `[esbuild css minify] Expected "}"` or `Unexpected token`.
3. Fix the syntax errors in your `.css` files.
4. Rebuild the Docker image (see above).

### Docker Port Conflicts

**Problem:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Cause:**
Another process (e.g., another Docker container, a dev server, or an IDE process) is using port 8000.

**Solution:**

1. Identify the blocking process:

   ```bash
   lsof -i :8000
   ```

2. Stop the conflicting process or container.
3. Alternatively, change the host port in `docker-compose.yml` to something available (e.g., 8081):

   ```yaml
   ports:
     - "8081:8000"
   ```

## General Issues

### Conversations Not Saving

**Symptom:** Conversations disappear after restart

**Solution:**

- Check that `data/conversations/` directory exists and is writable
- Verify file permissions: `ls -la data/conversations/`
- Check logs for file permission errors: `tail -f logs/llm_council.log`
- Ensure the application user has write permissions

### Models Not Responding

**Symptom:** All models fail or timeout

**Solution:**

1. Check your OpenRouter API key has sufficient credits
2. Verify model names are correct (check [OpenRouter models](https://openrouter.ai/models))
3. Increase `LLM_REQUEST_TIMEOUT` if models are slow
4. Check logs for specific error messages: `tail -f logs/llm_council.log`
5. Test API connectivity: `curl https://openrouter.ai/api/v1/models` (should return model list)

### Authentication Issues

**Error:** "Invalid credentials" or "Unauthorized"

**Solution:**

- Verify you're using the correct username/password
- Check that the user exists in `data/users.json`
- Ensure JWT tokens are being sent in requests (check browser Network tab)
- Clear browser cookies/localStorage and try again

### Organization/User Issues

**Error:** "Organization not found" or "User not in organization"

**Solution:**

- Verify organization exists in `data/organizations.json`
- Check user's `org_id` matches organization ID
- Ensure API key is configured for the organization (see [ADMIN_GUIDE.md](ADMIN_GUIDE.md))

### Logs Location

**Backend logs:**

- Default location: `logs/llm_council.log`
- Configure via `LOG_FILE` environment variable
- Check console output in the terminal where you started the backend

**Frontend logs:**

- Check browser DevTools Console (F12)
- Check Network tab for API call issues
- React DevTools extension recommended for component debugging

## Debugging Steps

### 1. Verify Environment Setup

```bash
# Check Python version
python --version  # Should be 3.10+

# Check Node.js version
node --version  # Should be v18+

# Check uv is installed
uv --version

# Check API key is set
grep OPENROUTER_API_KEY .env
```

### 2. Test Backend API

```bash
# Test health endpoint
curl http://localhost:8001/

# Should return: {"status":"ok"}

# Test with authentication (if configured)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/api/conversations
```

### 3. Check Logs

```bash
# Backend logs
tail -f logs/llm_council.log

# Or if LOG_FILE is different
tail -f $LOG_FILE

# Frontend: Check browser console (F12)
```

### 4. Verify Dependencies

```bash
# Backend dependencies
uv pip list

# Frontend dependencies
cd frontend && npm list --depth=0
```

### 5. Test Database/Storage

```bash
# Check data directory exists
ls -la data/

# Check conversations directory
ls -la data/conversations/

# Check users file (if exists)
cat data/users.json | jq .
```

## Getting Help

If you're still experiencing issues:

1. Check the [Developer Guide](DEVELOPER_GUIDE.md) for implementation details
2. Review [Architecture Decision Records](adr/ADR_INDEX.md) for design context
3. Check [API Documentation](api/API_SURFACE.md) for endpoint details
4. Review logs for specific error messages
5. Check OpenRouter status: <https://status.openrouter.ai/>

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Dependencies not installed | Run `uv sync` |
| `Address already in use` | Port conflict | Change port or kill existing process |
| `CORS policy` | Frontend origin not allowed | Update `CORS_ORIGINS` in `.env` |
| `Invalid token` | Encryption key issue | Check `ENCRYPTION_KEY` in `.env` |
| `Rate limit exceeded` | Too many requests | Reduce `MAX_CONCURRENT_REQUESTS` |
| `Timeout` | Model too slow | Increase `LLM_REQUEST_TIMEOUT` |
