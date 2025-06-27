# Local Development Authentication Guide

This guide explains how to use the new local development authentication system for Sutra.

## Overview

The local development authentication system provides a mock implementation of Azure Static Web Apps authentication that works seamlessly in local development while maintaining compatibility with production.

## Quick Start

1. **Start the development environment:**

   ```bash
   npm run dev        # Frontend on http://localhost:3003
   cd api && func start   # Backend on http://localhost:7071
   ```

2. **Set authentication mode:**

   ```bash
   # Edit .env.development or set environment variable
   export VITE_LOCAL_AUTH_MODE=admin  # or "user" or "anonymous"
   ```

3. **Access the application:**
   - Frontend: http://localhost:3003
   - Authentication will automatically use the configured mode

## Authentication Modes

### Admin Mode (Default)

```bash
VITE_LOCAL_AUTH_MODE=admin
```

- User: vedprakash.m@outlook.com
- Role: admin
- Access: All features including admin panel

### User Mode

```bash
VITE_LOCAL_AUTH_MODE=user
```

- User: user@example.com
- Role: user
- Access: Standard user features

### Anonymous Mode

```bash
VITE_LOCAL_AUTH_MODE=anonymous
```

- No authentication required
- Rate limited access (5 LLM calls/day)
- Restricted to GPT-3.5-turbo only

## Testing Authentication

### 1. Test Authentication Endpoint

```bash
curl http://localhost:3003/.auth/me | jq .
```

### 2. Test Role Assignment

```bash
curl http://localhost:3003/api/getroles | jq .
```

### 3. Test API Access

```bash
# Test prompt creation
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Hello"}' \
  http://localhost:3003/api/prompts | jq .

# Test collections
curl http://localhost:3003/api/collections | jq .
```

### 4. Test Anonymous APIs

```bash
# Get anonymous usage limits
curl http://localhost:3003/api/anonymous/llm/usage | jq .

# Create guest session
curl http://localhost:3003/api/guest/session | jq .
```

## Switching Authentication Modes

### Method 1: Environment Variable

```bash
# In terminal
export VITE_LOCAL_AUTH_MODE=admin
npm run dev

# Or in .env.development file
echo "VITE_LOCAL_AUTH_MODE=admin" > .env.development
```

### Method 2: Runtime Switching (Development)

The login button in development mode will prompt for auth mode selection.

### Method 3: Manual Override

In browser developer console:

```javascript
localStorage.setItem("vite_local_auth_mode", "admin");
window.location.reload();
```

## Architecture

### Components

1. **Local Auth Plugin** (`src/dev/localAuthPlugin.ts`)

   - Vite plugin that provides `/.auth/me` endpoint
   - Mimics Azure Static Web Apps authentication headers
   - Configurable via environment variables

2. **Enhanced AuthProvider** (`src/components/auth/AuthProvider.tsx`)

   - Environment detection (local vs production)
   - Fallback to `/api/getroles` for role assignment
   - Support for anonymous/guest users

3. **Vite Configuration** (`vite.config.ts`)
   - Proxy configuration for API requests
   - Mock authentication headers injection
   - Hot reload compatibility

### Authentication Flow

```
Local Development:
Browser → /.auth/me (mock) → AuthProvider → /api/getroles → Backend APIs

Production:
Browser → /.auth/me (Azure) → AuthProvider → /api/getroles → Backend APIs
```

## Troubleshooting

### Issue: Authentication not working

**Solution:** Check environment variables and restart dev server

```bash
echo $VITE_LOCAL_AUTH_MODE
npm run dev
```

### Issue: API requests failing

**Solution:** Verify backend is running and proxy configuration

```bash
curl http://localhost:7071/api/health
curl http://localhost:3003/api/health
```

### Issue: Role not recognized

**Solution:** Check role assignment API

```bash
curl http://localhost:3003/api/getroles
```

### Issue: Anonymous features not working

**Solution:** Test anonymous APIs directly

```bash
curl http://localhost:3003/api/anonymous/llm/usage
curl http://localhost:3003/api/guest/session
```

## Production Deployment

The authentication system automatically detects production environment and uses Azure Static Web Apps authentication. No code changes needed for deployment.

**Environment Detection:**

- Local: `hostname === 'localhost'` or `NODE_ENV === 'development'`
- Production: `hostname.includes('azurestaticapps.net')`

## Best Practices

1. **Always test with different auth modes** before deploying
2. **Use admin mode for testing admin features**
3. **Test anonymous mode for rate limiting**
4. **Verify role assignment in both environments**
5. **Check authentication headers in backend APIs**

## API Reference

### Authentication APIs

- `GET /.auth/me` - Current user info (mock in dev, real in prod)
- `GET /api/getroles` - User role assignment
- `POST /api/guest/session` - Create guest session
- `GET /api/anonymous/llm/usage` - Anonymous usage limits

### User Types

- **Authenticated Admin**: Full access, admin panel
- **Authenticated User**: Standard features
- **Guest User**: Limited session-based access
- **Anonymous User**: IP-based rate-limited access

## Security Notes

- Local auth is for development only
- Mock headers are automatically stripped in production
- Anonymous access is properly rate-limited
- Guest sessions expire after 24 hours
- All production authentication goes through Azure Static Web Apps
