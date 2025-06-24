# Authentication Configuration Fix Summary

## Issue Identified

The "Authentication system not properly configured" error was caused by multiple configuration mismatches:

## Root Causes Found

1. **Wrong App Registration ID**: Static Web App was configured to use `713d0c7d-e0fb-4390-95e2-42019b52a656` but the correct App Registration is `61084964-08b8-49ea-b624-4859c4dc37de` (sutra-web-app)
2. **Missing Redirect URIs**: The App Registration had no redirect URIs configured
3. **Wrong Static Web App Name**: Scripts were targeting `sutra-static-web-app` but actual name is `sutra-web-hvyqgbrvnx4ii`

## Fixes Applied

### 1. App Registration Configuration

- **App ID**: `61084964-08b8-49ea-b624-4859c4dc37de`
- **Redirect URIs**:
  - `https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/login/aad/callback`
  - `https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/login/azureActiveDirectory/callback`
- **ID Tokens**: Enabled ✅
- **New Client Secret**: `[REDACTED - Stored in Azure Key Vault]`

### 2. Static Web App Configuration

- **Resource**: `sutra-web-hvyqgbrvnx4ii` in `sutra-rg`
- **VED_EXTERNAL_ID_CLIENT_ID**: `61084964-08b8-49ea-b624-4859c4dc37de` ✅
- **VED_EXTERNAL_ID_CLIENT_SECRET**: `[REDACTED - Stored in Azure Key Vault]` ✅
- **WEBSITE_AUTH_ENABLED**: `true` ✅

### 3. Azure Key Vault

- Secret `VED-EXTERNAL-ID-CLIENT-SECRET` updated with new value

## Testing Instructions

### 1. Wait for Propagation (2-3 minutes)

Configuration changes may take a few minutes to take effect.

### 2. Test Authentication

- **URL**: https://zealous-flower-04bbe021e.2.azurestaticapps.net
- **Sign In**: Click "Sign in with Microsoft"
- **Expected**: Should redirect to Microsoft login without errors

### 3. Direct Auth Test

- **Login URL**: https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/login/azureActiveDirectory
- **User Info**: https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/me

## Troubleshooting

If authentication still fails:

1. **Clear Browser Cache**: Clear cookies and cache for the site
2. **Incognito Mode**: Try in private/incognito browser window
3. **Check Console**: Open browser dev tools for JavaScript errors
4. **Wait Longer**: Configuration can take up to 5 minutes to propagate
5. **Verify URLs**: Ensure you're using the correct Static Web App URL

## Configuration Summary

| Component        | Setting               | Value                                  |
| ---------------- | --------------------- | -------------------------------------- |
| App Registration | Client ID             | `61084964-08b8-49ea-b624-4859c4dc37de` |
| App Registration | Display Name          | `sutra-web-app`                        |
| App Registration | ID Tokens             | Enabled                                |
| App Registration | Redirect URIs         | 2 URIs configured                      |
| Static Web App   | Name                  | `sutra-web-hvyqgbrvnx4ii`              |
| Static Web App   | Client ID Setting     | `VED_EXTERNAL_ID_CLIENT_ID`            |
| Static Web App   | Client Secret Setting | `VED_EXTERNAL_ID_CLIENT_SECRET`        |
| Tenant           | Domain                | `vedid.onmicrosoft.com`                |

## Validation Commands

```bash
# Check Static Web App settings
az staticwebapp appsettings list --name "sutra-web-hvyqgbrvnx4ii" --resource-group "sutra-rg"

# Check App Registration
az ad app show --id 61084964-08b8-49ea-b624-4859c4dc37de --query "{redirectUris:web.redirectUris,idTokens:web.implicitGrantSettings.enableIdTokenIssuance}"

# Test authentication endpoint
curl -I https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/login/azureActiveDirectory
```
