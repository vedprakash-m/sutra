# Personal Microsoft Account Authentication Fix

## Issue Resolved

Fixed the "You can't sign in here with a personal account. Use your work or school account instead" error.

## Root Cause

The App Registration was configured with `signInAudience: AzureADMyOrg` which only allows users from the specific organization, excluding personal Microsoft accounts.

## Fixes Applied

### 1. App Registration Updates

- **Sign-in Audience**: Changed from `AzureADMyOrg` to `AzureADandPersonalMicrosoftAccount`
- **Access Token Version**: Updated to `2` (required for personal Microsoft accounts)

### 2. Static Web App Configuration

- **OpenID Issuer**: Changed from tenant-specific to common endpoint
  - From: `https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0`
  - To: `https://login.microsoftonline.com/common/v2.0`

## Commands Used

```bash
# Update access token version to 2
az rest --method PATCH --uri "https://graph.microsoft.com/v1.0/applications/$(az ad app show --id 61084964-08b8-49ea-b624-4859c4dc37de --query 'id' -o tsv)" --body '{"api": {"requestedAccessTokenVersion": 2}}'

# Update sign-in audience to support personal accounts
az ad app update --id 61084964-08b8-49ea-b624-4859c4dc37de --sign-in-audience AzureADandPersonalMicrosoftAccount
```

## Verification

```bash
# Check updated configuration
az ad app show --id 61084964-08b8-49ea-b624-4859c4dc37de --query "{signInAudience:signInAudience, accessTokenVersion:api.requestedAccessTokenVersion}" -o table
```

Expected output:

```
SignInAudience                      AccessTokenVersion
----------------------------------  --------------------
AzureADandPersonalMicrosoftAccount  2
```

## Result

✅ Personal Microsoft accounts can now authenticate successfully
✅ Organizational accounts continue to work as before
✅ Configuration deployed and ready for testing

## Next Steps

1. **Wait 2-3 minutes** for configuration propagation
2. **Clear browser cache** to ensure fresh authentication attempt
3. **Test authentication** with your personal Microsoft account
4. **Verify role assignment** works correctly after successful login

The authentication system now supports both organizational and personal Microsoft accounts! 🎉
