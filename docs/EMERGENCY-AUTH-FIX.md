# EMERGENCY AUTHENTICATION ENABLEMENT CHECKLIST

## 🚨 CRITICAL: Complete This Today

### **Step 1: Azure Portal Configuration (Manual - 10 minutes)**

1. **Open Azure Portal**: https://portal.azure.com
2. **Navigate to Static Web Apps**
3. **Find your app**: `sutra-web` or similar
4. **Click "Authentication"** in left menu
5. **Click "+ Add identity provider"**
6. **Select "Microsoft"** as provider
7. **Configure:**
   - App registration type: "Use existing app registration"
   - Client ID: `61084964-08b8-49ea-b624-4859c4dc37de`
   - Tenant ID: `vedid.onmicrosoft.com`
8. **Add redirect URI**: `https://your-app.azurestaticapps.net/.auth/login/azureActiveDirectory/callback`
9. **Enable ID tokens** in app registration
10. **Save** and **wait 5-10 minutes** for propagation

### **Step 2: Test Authentication**

```bash
# Test if authentication is enabled
curl -I https://salmon-pond-004adb91e.1.azurestaticapps.net/.auth/me

# Expected result after fix:
# HTTP/2 200 OK (authenticated user)
# HTTP/2 401 Unauthorized (not authenticated)
# NOT HTTP/2 404 Not Found (authentication disabled)
```

### **Step 3: Deploy Updated API Code**

Run deployment pipeline or manually deploy:

```bash
# Push latest code with migrated endpoints
git add .
git commit -m "Fix authentication: migrate all endpoints to Static Web Apps auth"
git push origin main
```

### **Step 4: Verification**

```bash
# Run comprehensive test
./scripts/comprehensive-auth-test.sh

# Expected improvement:
# - Authentication endpoints return 200/401 (not 404)
# - API endpoints return 401/403 (not 404)
# - Overall score improves from 75% to 90%+
```

---

## 🎯 SUCCESS CRITERIA

### **Immediate (Today)**

- [ ] ✅ Authentication endpoints return 200/401 (not 404)
- [ ] ✅ Users can initiate login flow
- [ ] ✅ API endpoints are deployed and protected

### **This Week**

- [ ] ✅ Complete user authentication flow works
- [ ] ✅ Role assignment functions correctly
- [ ] ✅ All API endpoints use new authentication
- [ ] ✅ Legacy JWT code removed from production

### **Production Ready**

- [ ] ✅ 95%+ test success rate
- [ ] ✅ All security vulnerabilities resolved
- [ ] ✅ Comprehensive monitoring in place
- [ ] ✅ User acceptance testing completed

---

## 📞 SUPPORT

**If authentication still doesn't work after Azure Portal changes:**

1. **Check App Registration**:

   - Verify redirect URIs match exactly
   - Ensure ID tokens are enabled
   - Check tenant configuration

2. **Environment Variables**:

   ```bash
   # Required in Static Web Apps configuration:
   VED_EXTERNAL_ID_CLIENT_ID=61084964-08b8-49ea-b624-4859c4dc37de
   VED_EXTERNAL_ID_CLIENT_SECRET=<from-key-vault>
   ```

3. **Contact Support**:
   - Azure Support for Static Web Apps issues
   - Check Azure Service Health dashboard
   - Review Azure Portal audit logs

**Emergency Contact**: Use scripts in `/scripts/` directory for automated diagnostics and fixes.
